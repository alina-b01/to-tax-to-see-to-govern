"""Shared paths, data loaders and the staggered difference-in-differences estimator."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TABLES = os.path.join(ROOT, "output", "tables")
FIGURES = os.path.join(ROOT, "output", "figures")
B, SEED = 1999, 1
EMIN, EMAX = -4, 3
CITY_OUTCOMES = ["mun_heat_need_share", "mun_jkh_exp_share", "roads_local_substandard_share",
                 "mun_roads_exp_share", "report_jump_heat"]


def read(name, **kw):
    return pd.read_csv(os.path.join(DATA, name), **kw)


def save(df, name):
    os.makedirs(TABLES, exist_ok=True)
    df.to_csv(os.path.join(TABLES, name), index=False)
    return df


def city_data():
    W = read("city_panel_bdpmo.csv", dtype={"oktmo_stable": str}).sort_values(["oktmo_stable", "year"])
    d = W.groupby("oktmo_stable").mun_heat_need_share.diff()
    W["report_jump_heat"] = (d.abs() > 20).astype(float).where(d.notna())
    return W


def city_panel(coding="corrected", last_year=2018):
    """City-year panel with treatment cohort g.

    coding: 'corrected' (manual check of 2019-2024), 'original' (Reuter et al.)
    or 'decision' (date of the legal decision to cancel direct elections).
    """
    W = city_data()
    if coding == "corrected":
        T = read("mayors_treatment_v2.csv", dtype={"oktmo_stable": str, "region_code": str})
        T = T[T.in_h2_sample & ~(T.year_transition <= 2010)].copy()
        T["g"] = T.year_transition_v2
        T.loc[T.g > last_year, "g"] = np.nan
    else:
        T = read("mayors_treatment.csv", dtype={"oktmo_stable": str, "region_code": str})
        T = T[T.in_h2_sample]
        if coding == "decision":
            T = T[T.bbr_cancel_year.notna() | T.year_transition.isna()]
        T = T.assign(g=T["year_transition" if coding == "original" else "bbr_cancel_year"])
        T = T[~(T.g <= 2010)]
    P = T[["city_id", "city", "oktmo_stable", "region_code", "g", "capitol"]].merge(
        W[W.year.between(2010, last_year)], on="oktmo_stable", how="left", suffixes=("", "_w"))
    P = P.dropna(subset=["year"])
    P["year"] = P.year.astype(int)
    return P


class StaggeredDiD:
    """Callaway-Sant'Anna ATT(g,t) with base period g-1 and not-yet-treated controls.

    Cluster bootstrap by region is implemented through city multiplicity weights,
    which reproduces resampling regions with replacement exactly.
    """

    def __init__(self, P, y, years, treated=None, X=None, emax=EMAX):
        g = P.groupby("city_id").g.first()
        self.ids = g.index.values
        self.G = g.values.astype(float)
        self.region = P.groupby("city_id").region_code.first().reindex(g.index).values
        self.years = list(years)
        self.Y = P.pivot_table(index="city_id", columns="year", values=y).reindex(index=g.index, columns=self.years).values.astype(float)
        self.tr_ok = np.ones(len(g), bool) if treated is None else np.isin(self.ids, list(treated))
        self.X = None if X is None else P.groupby("city_id")[X].first().reindex(g.index).values.astype(float)
        self.regs = pd.Series(self.region).dropna().unique()
        self.emax = emax

    def cells(self, w):
        out, yi = [], {t: i for i, t in enumerate(self.years)}
        for g in np.unique(self.G[~np.isnan(self.G)]):
            base = int(g) - 1
            if base not in yi:
                continue
            tr = (self.G == g) & self.tr_ok
            for t in self.years:
                if t == base:
                    continue
                ctrl = np.isnan(self.G) | (self.G > max(t, base))
                d = self.Y[:, yi[t]] - self.Y[:, yi[base]]
                v = ~np.isnan(d) & (w > 0)
                if self.X is not None:
                    v &= ~np.isnan(self.X).any(1)
                mt, mc = tr & v, ctrl & v
                ntr, nct = w[mt].sum(), w[mc].sum()
                if ntr == 0:
                    continue
                if self.X is None:
                    if nct < 3:
                        continue
                    att = (w[mt] * d[mt]).sum() / ntr - (w[mc] * d[mc]).sum() / nct
                else:
                    if nct < self.X.shape[1] + 4:
                        continue
                    sw = np.sqrt(w[mc])
                    Zc = np.c_[np.ones(mc.sum()), self.X[mc]]
                    beta = np.linalg.lstsq(Zc * sw[:, None], d[mc] * sw, rcond=None)[0]
                    att = (w[mt] * (d[mt] - np.c_[np.ones(mt.sum()), self.X[mt]] @ beta)).sum() / ntr
                out.append((g, t, t - g, att, ntr, nct))
        return pd.DataFrame(out, columns=["g", "t", "e", "att", "n_treated", "n_control"])

    def aggregate(self, c):
        if c.empty:
            return np.nan, np.nan, {}
        c = c[(c.e >= EMIN) & (c.e <= self.emax)]
        dyn = {int(k): np.average(d.att, weights=d.n_treated) for k, d in c.groupby("e")}
        post, pre = c[c.e >= 0], c[c.e <= -2]
        ov = np.average(post.att, weights=post.n_treated) if len(post) else np.nan
        pr = np.average(pre.att, weights=pre.n_treated) if len(pre) else np.nan
        return ov, pr, dyn

    def estimate(self, w=None):
        return self.aggregate(self.cells(np.ones(len(self.G)) if w is None else w))

    def n_cities(self):
        has = ~np.isnan(self.Y).all(1)
        return int(has.sum()), int((has & ~np.isnan(self.G) & self.tr_ok).sum())


def bootstrap(models, B=B, seed=SEED):
    """Joint region bootstrap for a dict of StaggeredDiD models (common draws)."""
    rng = np.random.default_rng(seed)
    regs = sorted(set().union(*[set(m.regs) for m in models.values()]))
    draws = {k: [] for k in models}
    for _ in range(B):
        cnt = pd.Series(rng.choice(regs, size=len(regs), replace=True)).value_counts()
        for k, m in models.items():
            ov, pr, dyn = m.estimate(pd.Series(m.region).map(cnt).fillna(0).values.astype(float))
            draws[k].append(dict(att=ov, pre=pr, **{f"e{e}": v for e, v in dyn.items()}))
    return {k: pd.DataFrame(v) for k, v in draws.items()}


def summary(spec, outcome, model, draws):
    att, pre, _ = model.estimate()
    n, nt = model.n_cities()
    return dict(spec=spec, outcome=outcome, att=att, se=draws.att.std(),
                ci_lo_pct=np.nanpercentile(draws.att, 2.5), ci_hi_pct=np.nanpercentile(draws.att, 97.5),
                pre=pre, pre_se=draws.pre.std(), n_cities=n, n_treated=nt, B=int(draws.att.notna().sum()))
