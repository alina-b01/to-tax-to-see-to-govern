"""Abolition of direct mayoral elections: Tables 3, 4, B2, B3, B4, C1 and Figure 3 data.

Usage: python municipal.py [main|timing|robustness|horizons|heterogeneity|conditional|cohorts|all]
"""
import sys

import numpy as np
import pandas as pd

from common import (B, CITY_OUTCOMES, SEED, StaggeredDiD, bootstrap, city_panel, read, save, summary)

Y18, Y24 = range(2010, 2019), range(2010, 2025)
NEED, JKH = "mun_heat_need_share", "mun_jkh_exp_share"


def run_single(P, y, years, spec, **kw):
    m = StaggeredDiD(P, y, years, **kw)
    d = bootstrap({"x": m})["x"]
    return summary(spec, y, m, d), d, m


def main():
    rows, dyn = [], []
    for spec, coding, last in [("corrected_2018", "corrected", 2018), ("original_2018", "original", 2018),
                               ("decision_2018", "decision", 2018), ("corrected_2024", "corrected", 2024)]:
        P = city_panel(coding, last)
        for y in CITY_OUTCOMES:
            r, d, m = run_single(P, y, range(2010, last + 1), spec)
            rows.append(r)
            if spec == "corrected_2018" and y in (NEED, JKH):
                for e, v in m.estimate()[2].items():
                    dyn.append(dict(outcome=y, e=e, att=v, se=d[f"e{e}"].std()))
    save(pd.DataFrame(rows), "table3_municipal_did.csv")
    save(pd.DataFrame(dyn), "figure3_event_study.csv")


def conditional():
    P = city_panel("corrected", 2018)
    base = read("city_panel_bdpmo.csv", dtype={"oktmo_stable": str}).query("year == 2010").set_index("oktmo_stable")
    P["x_lnpop"] = P.oktmo_stable.map(np.log(base.mun_population))
    P["x_need10"] = P.oktmo_stable.map(base.mun_heat_need_share)
    P["x_jkh10"] = P.oktmo_stable.map(base.mun_jkh_exp_share)
    X = ["x_lnpop", "x_need10", "x_jkh10"]
    keep = P.groupby("city_id")[X].first().dropna().index
    rows = []
    for y in (NEED, JKH):
        models = {"regression_adjusted": StaggeredDiD(P, y, Y18, X=X),
                  "unadjusted_same_sample": StaggeredDiD(P[P.city_id.isin(keep)], y, Y18)}
        dr = bootstrap(models)
        rows += [summary(k, y, m, dr[k]) for k, m in models.items()]
    save(pd.DataFrame(rows), "table3_conditional_did.csv")


def timing():
    Pd, Po, Pc = city_panel("decision"), city_panel("original"), city_panel("corrected")
    T = read("mayors_treatment_v2.csv").set_index("city_id")
    lag = T.year_transition_v2 - T.bbr_cancel_year
    rows = []
    for y in (JKH, NEED):
        ids = {k: set(P.dropna(subset=[y]).city_id) for k, P in (("d", Pd), ("o", Po), ("c", Pc))}
        common = ids["d"] & ids["o"] & ids["c"]
        models = {"decision_all": StaggeredDiD(Pd, y, Y18),
                  "decision_common": StaggeredDiD(Pd[Pd.city_id.isin(common)], y, Y18),
                  "original_common": StaggeredDiD(Po[Po.city_id.isin(common)], y, Y18),
                  "corrected_common": StaggeredDiD(Pc[Pc.city_id.isin(common)], y, Y18),
                  "corrected_all": StaggeredDiD(Pc, y, Y18)}
        dr = bootstrap(models)
        rows += [summary(k, y, m, dr[k]) for k, m in models.items()]
        rows.append(dict(spec="diff_decision_minus_corrected_common", outcome=y,
                         att=models["decision_common"].estimate()[0] - models["corrected_common"].estimate()[0],
                         se=(dr["decision_common"].att - dr["corrected_common"].att).std(), n_cities=len(common)))
        pair = ids["d"] & ids["c"]
        gd = Pd.groupby("city_id").g.first().reindex(list(pair))
        gc = Pc.groupby("city_id").g.first().reindex(list(pair))
        td, tc = gd.notna() & (gd <= 2018), gc.notna() & (gc <= 2018)
        fixed = set(gd.index[td == tc])
        for name, S in (("fixed", fixed), ("fixed_no_negative_lag", {c for c in fixed if not lag.get(c, 0) < 0})):
            models = {"decision": StaggeredDiD(Pd[Pd.city_id.isin(S)], y, Y18),
                      "corrected": StaggeredDiD(Pc[Pc.city_id.isin(S)], y, Y18)}
            dr = bootstrap(models)
            for k, m in models.items():
                r = summary(f"{name}_{k}", y, m, dr[k])
                r["n_treated"] = int((td & tc)[list(S)].sum())
                rows.append(r)
            rows.append(dict(spec=f"{name}_diff", outcome=y, n_cities=len(S),
                             att=models["decision"].estimate()[0] - models["corrected"].estimate()[0],
                             se=(dr["decision"].att - dr["corrected"].att).std()))
    save(pd.DataFrame(rows), "table4_timing.csv")


def robustness():
    P = city_panel("corrected", 2018)
    A = read("mayors_appointed_panel.csv").sort_values(["city_id", "year"])
    A["prev"] = A.groupby("city_id").appointed.shift()
    reversals = set(A[(A.year >= 2005) & (A.prev == 1) & (A.appointed == 0)].city_id)
    samples = {"no_reversals": P[~P.city_id.isin(reversals)], "capitals": P[P.capitol == 1],
               "cohorts_2014_2018": P[P.g.isna() | (P.g >= 2014)]}
    rows = [run_single(Q, y, Y18, k)[0] for k, Q in samples.items() for y in CITY_OUTCOMES[:4]]
    save(pd.DataFrame(rows), "tableB3_municipal_robustness.csv")


def horizons():
    P = city_panel("corrected", 2018)
    g = P.groupby("city_id").g.first()
    specs = {"all_cohorts_e0_3": (None, 3), "cohorts_2011_2017_e0_1": (set(g.index[g <= 2017]), 1),
             "cohorts_2011_2015_e0_3": (set(g.index[g <= 2015]), 3),
             "cohorts_2012_2015_e0_3": (set(g.index[(g >= 2012) & (g <= 2015)]), 3)}
    rows = [run_single(P, y, Y18, k, treated=ids, emax=em)[0] for y in (NEED, JKH) for k, (ids, em) in specs.items()]
    save(pd.DataFrame(rows), "tableB4_horizons.csv")


def capital_ownership():
    T = read("mayors_treatment_v2.csv", dtype={"region_code": str})
    S = T[T.in_h2_sample & ~(T.year_transition <= 2010) & (T.capitol == 1)].copy()
    S["region_code"] = S.region_code.str.zfill(2)
    e = read("emiss_heat_long.csv", dtype={"region_code": str})
    c = e[(e.level == "capital") & (e.variable == "heat_len_km") & (e.year == 2019)].pivot_table(
        index="region_code", columns="ownership", values="value")
    c.index = c.index.astype(str).str.zfill(2)
    c["mun_share"] = 100 * c["municipal"] / c["all"]
    return S.merge(c[["all", "mun_share"]], left_on="region_code", right_index=True, how="left")[["city", "region_code", "all", "mun_share"]]


def heterogeneity():
    P = city_panel("corrected", 2018)
    own = capital_ownership()
    share = dict(zip(own.city, own.mun_share))
    pz = set(read("price_zones_heat.csv", dtype=str).oktmo_stable.dropna())
    s = P.groupby("city_id").first()
    groups = {"capitals_municipal_gt50": set(s.index[s.city.map(share) > 50]),
              "capitals_municipal_le50": set(s.index[s.city.map(share) <= 50]),
              "price_zone": set(s.index[s.oktmo_stable.isin(pz)]), "no_price_zone": set(s.index[~s.oktmo_stable.isin(pz)])}
    rows = []
    for y in (NEED, JKH):
        models = {k: StaggeredDiD(P, y, Y18, treated=ids) for k, ids in groups.items()}
        dr = bootstrap(models)
        rows += [summary(k, y, m, dr[k]) for k, m in models.items()]
        for a, b in (("capitals_municipal_gt50", "capitals_municipal_le50"), ("no_price_zone", "price_zone")):
            rows.append(dict(spec=f"diff_{a}_minus_{b}", outcome=y, att=models[a].estimate()[0] - models[b].estimate()[0],
                             se=(dr[a].att - dr[b].att).std()))
    save(pd.DataFrame(rows), "tableC1_heterogeneity.csv")
    save(own, "capital_ownership_2019.csv")


def cohorts():
    P = city_panel("corrected", 2018)
    rows, cells_out = [], []
    for y in (NEED, JKH):
        m = StaggeredDiD(P, y, Y18)
        c = m.cells(np.ones(len(m.G)))
        post = c[(c.e >= 0) & (c.e <= 3)]
        w = post.groupby("g").n_treated.sum() / post.n_treated.sum()
        s = P.dropna(subset=[y]).groupby("city_id").g.first()
        for g, n in s.value_counts(dropna=False).sort_index().items():
            rows.append(dict(outcome=y, cohort="never_by_2018" if pd.isna(g) else int(g), n_cities=int(n),
                             weight=None if pd.isna(g) else float(w.get(g, 0)),
                             not_yet_treated_end_of_year=None if pd.isna(g) else int((s.isna() | (s > g)).sum())))
        cells_out.append(c.assign(outcome=y))
    save(pd.DataFrame(rows), "tableB2_cohorts.csv")
    save(pd.concat(cells_out), "att_cells_corrected_2018.csv")


SECTIONS = {"main": main, "timing": timing, "robustness": robustness, "horizons": horizons,
            "heterogeneity": heterogeneity, "conditional": conditional, "cohorts": cohorts}

if __name__ == "__main__":
    todo = sys.argv[1:] or ["all"]
    for name in (SECTIONS if todo == ["all"] else todo):
        SECTIONS[name]()
        print("done:", name)
