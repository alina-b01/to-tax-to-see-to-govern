"""Fiscal structure and heat-network outcomes across regions: Table 2, Table B1, text statistics."""
import warnings

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

from common import read, save

warnings.filterwarnings("ignore")
LAGGED = ["trans_share", "dot_equal_share", "discretionary_share", "subsidies_share", "subventions_share",
          "fed_tax_share", "ln_grp_pc_real", "heat_loss_pct", "ln_real_heat_price", "jkh_targeted_tr_share",
          "trans_nonjkh_share"]
OUTCOMES = ["heat_loss_pct", "heat_need_share_emiss", "heat_replaced_share_emiss", "communal_exp_share"]
DECOMP = ["dot_equal_share", "discretionary_share", "subsidies_share", "subventions_share"]
CTRL = "ln_grp_pc_real_l1"


def panel():
    P = read("panel_h1.csv", dtype={"region_code": str}).replace([np.inf, -np.inf], np.nan).sort_values(["region_code", "year"])
    g = P.groupby("region_code")
    for x in LAGGED:
        for k in (1, 2):
            P[f"{x}_l{k}"] = g[x].shift(k)
            P[f"{x}_f{k}"] = g[x].shift(-k)
    P["may_x_post"] = P.edu_health_emp_share_2011 * (P.year >= 2013)
    for y in range(2011, 2024):
        P[f"mining_x_{y}"] = P.mining_share_gva_2010 * (P.year == y)
    return P


def fit(P, y, xs, extra=(), sample=None, label=""):
    d = (P if sample is None else P[sample]).dropna(subset=[y, *xs, *extra]).set_index(["region_code", "year"])
    r = PanelOLS(d[y], d[list(xs) + list(extra)], entity_effects=True, time_effects=True,
                 drop_absorbed=True, check_rank=False).fit(cov_type="clustered", cluster_entity=True)
    out = []
    for x in xs:
        if x == CTRL or x not in r.params.index:
            continue
        sd = (d[x] - d.groupby(level=0)[x].transform("mean")).std()
        out.append(dict(model=label, outcome=y, regressor=x, coef=r.params[x], se=r.std_errors[x], p=r.pvalues[x],
                        n=int(r.nobs), clusters=int(d.index.get_level_values(0).nunique()), sd_within_x=sd,
                        effect_1sd=r.params[x] * sd, ci_1sd_lo=(r.params[x] - 1.96 * r.std_errors[x]) * sd,
                        ci_1sd_hi=(r.params[x] + 1.96 * r.std_errors[x]) * sd))
    return out


def main():
    P = panel()
    shocks = ["may_x_post"] + [c for c in P.columns if c.startswith("mining_x_")]
    big = P.region_code.isin(["77", "78", "72"]) | (P.mining_share_gva_2010 > 20)
    early = P.year <= 2019
    hdd = P.hdd.notna()

    t2 = []
    for y in OUTCOMES:
        for x in ("trans_share_l1", "fed_tax_share_l1"):
            t2 += fit(P, y, [x, CTRL], label="baseline")
    save(pd.DataFrame(t2), "table2_regional.csv")

    b1 = []
    loss, repl = "heat_loss_pct", "heat_replaced_share_emiss"
    for y, cols in ((loss, ("trans_share", "fed_tax_share", "discretionary_share")), (repl, ("fed_tax_share",))):
        for x in cols:
            if x == "discretionary_share":
                b1 += [r for r in fit(P, y, [f"{v}_l1" for v in DECOMP] + [CTRL], label="baseline") if r["regressor"] == "discretionary_share_l1"]
                b1 += [r for r in fit(P, y, [f"{v}_l1" for v in DECOMP] + [CTRL], extra=shocks, label="shocks") if r["regressor"] == "discretionary_share_l1"]
                b1 += [r for r in fit(P, y, [f"{v}_l2" for v in DECOMP] + [CTRL], label="lag2") if r["regressor"] == "discretionary_share_l2"]
            else:
                b1 += fit(P, y, [f"{x}_l1", CTRL], label="baseline")
                b1 += fit(P, y, [f"{x}_l1", CTRL], extra=shocks, label="shocks")
                b1 += fit(P, y, [f"{x}_l2", CTRL], label="lag2")
                b1 += fit(P, y, [f"{x}_l1", CTRL, "hdd"], sample=hdd, label="hdd")
            b1 += [r for r in fit(P, y, [f"{x}_f1", f"{x}_l1", CTRL], label="lead") if r["regressor"].endswith("_f1")]
        joint = ["trans_share_l1", "discretionary_share_l1", "fed_tax_share_l1", CTRL] if y == loss else ["trans_share_l1", "fed_tax_share_l1", CTRL]
        b1 += fit(P, y, joint, sample=early, label="2010_2019_joint")
        if y == loss:
            b1 += fit(P, y, joint, sample=~big, label="excl_large_resource_joint")
        b1 += fit(P, y, ["trans_share_l1", "fed_tax_share_l1", "ln_real_heat_price_l1", CTRL], label="tariff_joint")
    save(pd.DataFrame(b1), "tableB1_regional_robustness.csv")

    tx = []
    for y in (loss, "communal_exp_share", repl):
        tx += fit(P, y, [f"{v}_l1" for v in DECOMP] + [CTRL], label="transfer_decomposition")
    for y in (loss, "heat_need_share_emiss", repl):
        tx += fit(P, y, ["ln_real_heat_price_l1", CTRL], label="tariff_only")
    tx += fit(P, "communal_exp_share", ["jkh_infra_tr_share", "urban_env_tr_share", "state_corp_tr_share", "trans_nonjkh_share", CTRL], label="targeted_transfers_contemporaneous")
    for y in (loss, repl, "communal_exp_share"):
        tx += fit(P, y, ["jkh_targeted_tr_share_l1", "trans_nonjkh_share_l1", CTRL], label="targeted_transfers_lag")
    for x in ("discretionary_share", "dot_equal_share", "trans_share"):
        tx += fit(P, loss, [f"{x}_f2", f"{x}_f1", x, f"{x}_l1", f"{x}_l2", CTRL], label="distributed_lags")
        tx += fit(P, x, ["heat_loss_pct_l1", "heat_loss_pct_l2", CTRL], label="reverse")
        tx += fit(P, x, ["heat_loss_pct_l1", "heat_loss_pct_l2", CTRL], sample=early, label="reverse_2010_2019")
    tx += fit(P, "jkh_targeted_tr_share", ["heat_loss_pct_l1", "heat_loss_pct_l2", CTRL], label="reverse")
    save(pd.DataFrame(tx), "regional_text_statistics.csv")


if __name__ == "__main__":
    main()
    print("done: regional")
