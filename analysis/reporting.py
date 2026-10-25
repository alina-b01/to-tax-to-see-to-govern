"""Large year-to-year changes in the reported share of networks in need of replacement: Table 5."""
import numpy as np
import pandas as pd

from common import read, save


def main():
    T = read("mayors_treatment_v2.csv", dtype={"oktmo_stable": str})
    S = T[T.in_h2_sample & ~(T.year_transition <= 2010)]
    W = read("city_panel_bdpmo.csv", dtype={"oktmo_stable": str})
    W = W[W.oktmo_stable.isin(S.oktmo_stable)].set_index(["oktmo_stable", "year"]).sort_index()
    sh, L, N = (W[c].unstack() for c in ("mun_heat_need_share", "mun_heat_len_m", "mun_heat_need_m"))
    ev = []
    for o in sh.index:
        r = sh.loc[o]
        for t in range(2010, 2019):
            a, b = r.get(t - 1, np.nan), r.get(t, np.nan)
            if np.isnan(a) or np.isnan(b) or abs(b - a) <= 20:
                continue
            d = b - a
            back = [-(r.get(t + k, np.nan) - b) * np.sign(d) for k in (1, 2)]
            ev.append(dict(oktmo_stable=o, year=t, jump=d, length_change=L.loc[o, t] / L.loc[o, t - 1] - 1,
                           need_ratio=N.loc[o, t] / N.loc[o, t - 1] if N.loc[o, t - 1] > 0 else np.nan,
                           reversal_2y=any(x >= 0.5 * abs(d) for x in back if not np.isnan(x)),
                           reversal_by_2018=any(x >= 0.5 * abs(d) for k, x in zip((1, 2), back) if not np.isnan(x) and t + k <= 2018)))
    E = pd.DataFrame(ev)
    changes = sh.loc[:, 2009:2018].diff(axis=1).loc[:, 2010:2018].stack().dropna()
    lc = E.length_change.abs() * 100
    stable = E[lc < 5]
    rows = [("annual_changes", len(changes)), ("jumps_gt20pp", len(E)), ("jump_share", len(E) / len(changes)),
            ("cities_with_jump", E.oktmo_stable.nunique()), ("cities", sh.shape[0]),
            ("length_change_lt5", (lc < 5).sum()), ("length_change_5_20", ((lc >= 5) & (lc <= 20)).sum()), ("length_change_gt20", (lc > 20).sum()),
            ("stable_length_need_ratio_gt2_or_lt05", ((stable.need_ratio > 2) | (stable.need_ratio < 0.5)).mean()),
            ("jumps_up", (E.jump > 0).mean()), ("reversal_within_2y", E.reversal_2y.mean()), ("reversal_within_2y_by_2018", E.reversal_by_2018.mean())]
    save(pd.DataFrame(rows, columns=["statistic", "value"]), "table5_reporting_jumps.csv")
    save(E, "reporting_jump_events.csv")
    nv = "53720000"
    save(pd.DataFrame({"year": range(2010, 2015), "length_km": L.loc[nv, 2010:2014].values / 1000,
                       "need_km": N.loc[nv, 2010:2014].values / 1000, "need_share": sh.loc[nv, 2010:2014].values}), "example_novotroitsk.csv")


if __name__ == "__main__":
    main()
    print("done: reporting")
