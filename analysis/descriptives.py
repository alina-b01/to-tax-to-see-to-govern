"""Descriptive statistics: Table 1, Figure 1 series and measurement statistics (sections 3.3, 4.3, 4.4)."""
import numpy as np
import pandas as pd

from common import city_panel, read, save
from municipal import capital_ownership

REGIONAL = ["heat_loss_pct", "heat_need_share_emiss", "heat_replaced_share_emiss", "communal_exp_share",
            "trans_share", "fed_tax_share", "ln_grp_pc_real"]
CITY = ["mun_heat_need_share", "mun_jkh_exp_share", "roads_local_substandard_share", "mun_roads_exp_share", "report_jump_heat"]


def table(d, cols, unit, block):
    rows = []
    for c in cols:
        x = d[[unit, c]].dropna()
        rows.append(dict(block=block, variable=c, n=len(x), mean=x[c].mean(), sd=x[c].std(),
                         sd_within=(x[c] - x.groupby(unit)[c].transform("mean")).std(), median=x[c].median()))
    return rows


def twoway_sd(d, c, it=50):
    x = d[["region_code", "year", c]].dropna().copy()
    for _ in range(it):
        x[c] -= x.groupby("region_code")[c].transform("mean")
        x[c] -= x.groupby("year")[c].transform("mean")
    return x[c].std()


def main():
    P = read("panel_h1.csv", dtype={"region_code": str})
    C = city_panel("corrected", 2018)
    save(pd.DataFrame(table(P, REGIONAL, "region_code", "regions_2010_2023") + table(C, CITY, "city_id", "cities_2010_2018")),
         "table1_descriptives.csv")
    save(P.groupby("year")[["fed_tax_share", "trans_share", "heat_loss_pct", "heat_need_share_emiss",
                            "heat_replaced_share_emiss", "net_municipal_share"]].median().reset_index(), "figure1_medians.csv")

    s = []
    add = lambda k, v: s.append(dict(statistic=k, value=v))
    for c in ("heat_loss_pct", "heat_need_share_emiss"):
        add(f"sd_within_twoway_{c}", twoway_sd(P, c))
    y23 = P[P.year == 2023]
    add("spearman_2023_loss_need", y23[["heat_loss_pct", "heat_need_share_emiss"]].corr("spearman").iloc[0, 1])
    for yr in (2019, 2023):
        d = P[P.year == yr]
        add(f"spearman_{yr}_need_replaced", d[["heat_need_share_emiss", "heat_replaced_share_emiss"]].corr("spearman").iloc[0, 1])
    v = ["heat_loss_pct", "heat_need_share_emiss", "heat_replaced_share_emiss"]
    q = P[["region_code", "year"] + v].dropna()
    for c in v:
        q[c] = q[c] - q.groupby("region_code")[c].transform("mean") - q.groupby("year")[c].transform("mean") + q[c].mean()
    w = q[v].corr()
    add("within_corr_loss_need", w.loc[v[0], v[1]]); add("within_corr_need_replaced", w.loc[v[1], v[2]]); add("within_corr_loss_replaced", w.loc[v[0], v[2]])
    inc = P.pivot(index="region_code", columns="year", values="heat_loss_pct").diff(axis=1)
    for yr in range(2011, 2024):
        add(f"share_regions_heat_loss_increase_{yr}", (inc[yr] > 0).mean())
    for yr in (2019, 2020, 2023):
        add(f"median_municipal_network_share_{yr}", P.loc[P.year == yr, "net_municipal_share"].median())

    e = read("emiss_heat_long.csv", dtype={"region_code": str})
    cap = e[(e.level == "capital") & (e.ownership == "all")].pivot_table(index=["name", "year"], columns="variable", values="value").reset_index()
    cap["need_emiss"] = 100 * cap.heat_need_replace_km / cap.heat_len_km
    T = read("mayors_treatment_v2.csv", dtype={"oktmo_stable": str})
    W = read("city_panel_bdpmo.csv", dtype={"oktmo_stable": str})
    m = cap.merge(T[["city", "oktmo_stable"]].drop_duplicates(), left_on="name", right_on="city").merge(
        W[["oktmo_stable", "year", "mun_heat_need_share"]], on=["oktmo_stable", "year"]).dropna(subset=["need_emiss", "mun_heat_need_share"])
    diff = (m.need_emiss - m.mun_heat_need_share).abs()
    add("emiss_vs_bdpmo_capitals_n", len(m)); add("emiss_vs_bdpmo_capitals_corr", m[["need_emiss", "mun_heat_need_share"]].corr().iloc[0, 1])
    add("emiss_vs_bdpmo_median_abs_diff", diff.median()); add("emiss_vs_bdpmo_share_diff_gt10", (diff > 10).mean()); add("emiss_vs_bdpmo_share_diff_gt20", (diff > 20).mean())

    own = capital_ownership()
    add("capitals_in_sample", len(own)); add("capitals_with_municipal_length", own.mun_share.notna().sum())
    add("capitals_municipal_share_median", own.mun_share.median()); add("capitals_municipal_share_min", own.mun_share.min())
    add("capitals_municipal_share_max", own.mun_share.max()); add("capitals_municipal_share_lt1", (own.mun_share < 1).sum())
    add("capitals_municipal_share_gt50", (own.mun_share > 50).sum())
    pz = set(read("price_zones_heat.csv", dtype=str).oktmo_stable.dropna())
    S = T[T.in_h2_sample & ~(T.year_transition <= 2010)]
    add("cities_in_sample", len(S)); add("cities_in_price_zones", S.oktmo_stable.isin(pz).sum())
    save(pd.DataFrame(s), "descriptive_statistics.csv")


if __name__ == "__main__":
    main()
    print("done: descriptives")
