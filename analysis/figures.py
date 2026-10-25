"""Figures 1-3. Requires outputs of descriptives.py and municipal.py."""
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import FIGURES, TABLES, read

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
BLUE = "#1f4e79"


def figure1():
    m = pd.read_csv(os.path.join(TABLES, "figure1_medians.csv"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.8))
    a.plot(m.year, m.fed_tax_share, "o-", label="Taxes from the territory → federal budget, %")
    a.plot(m.year, m.trans_share, "s-", label="Transfers in regional revenues, %")
    a.set_title("A. Fiscal structure (median across 80 regions)", fontsize=11); a.legend(fontsize=8.5); a.grid(alpha=0.3)
    b.plot(m.year, m.heat_loss_pct, "o-", color="#b22222")
    b.set_title("B. Heat losses in networks, % (median)", fontsize=11); b.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "figure1_trends.png"), dpi=200); plt.close()


def figure2():
    P = read("panel_h1.csv", dtype={"region_code": str}).sort_values(["region_code", "year"]).copy()
    for v in ("trans_share", "fed_tax_share", "ln_grp_pc_real"):
        P[v + "_l1"] = P.groupby("region_code")[v].shift()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    for ax, (x, xl, ttl) in zip(axes, [("trans_share_l1", "Transfers share, t−1 (residual), p.p.", "A. Transfers share"),
                                       ("fed_tax_share_l1", "Share of taxes to the federal budget, t−1 (residual), p.p.", "B. Share of taxes to the federal budget")]):
        d = P[["region_code", "year", "heat_loss_pct", x, "ln_grp_pc_real_l1"]].dropna().copy()
        cols = ["heat_loss_pct", x, "ln_grp_pc_real_l1"]
        for _ in range(200):
            for c in cols:
                d[c] -= d.groupby("region_code")[c].transform("mean")
                d[c] -= d.groupby("year")[c].transform("mean")
        g = d[["ln_grp_pc_real_l1"]].values
        res = lambda v: v - g @ np.linalg.lstsq(g, v, rcond=None)[0]
        ry, rx = res(d.heat_loss_pct.values), res(d[x].values)
        beta = rx @ ry / (rx @ rx)
        bins = pd.qcut(rx, 20, labels=False)
        bx, by = pd.Series(rx).groupby(bins).mean(), pd.Series(ry).groupby(bins).mean()
        ax.scatter(bx, by, s=22, color=BLUE, zorder=3)
        xs = np.linspace(bx.min(), bx.max(), 50); ax.plot(xs, beta * xs, color="#7f7f7f", lw=1.6)
        ax.axhline(0, color="black", lw=0.6); ax.grid(alpha=0.3)
        ax.set_title(ttl, fontsize=11); ax.set_xlabel(xl, fontsize=9.5); ax.set_ylabel("Heat losses, % (residual)", fontsize=9.5)
        ax.text(0.03, 0.95, f"β = {beta:.4f}".replace("-", "−") + f"\nN = {len(d)}", transform=ax.transAxes,
                va="top", fontsize=9.5, bbox=dict(fc="white", ec="0.8", lw=0.6))
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "figure2_binscatter.png"), dpi=200); plt.close()


def figure3():
    es = pd.read_csv(os.path.join(TABLES, "figure3_event_study.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    for ax, (y, ttl) in zip(axes, [("mun_heat_need_share", "A. Heating networks in need of replacement"), ("mun_jkh_exp_share", "B. Share of communal spending")]):
        s = es[es.outcome == y].sort_values("e")
        for part in (s[s.e < 0], s[s.e >= 0]):
            ax.errorbar(part.e, part.att, yerr=1.96 * part.se, fmt="o-", color=BLUE, capsize=3, lw=1.4, ms=5)
        ax.plot([-1], [0], marker="o", mfc="white", mec=BLUE, ms=6, ls="none")
        ax.axhline(0, color="0.4", lw=0.8); ax.axvline(-0.5, color="0.6", ls="--", lw=0.9)
        ax.set_xticks(range(-4, 4)); ax.grid(alpha=0.25); ax.set_title(ttl, fontsize=11)
        ax.set_xlabel("Years relative to the transition"); ax.set_ylabel("ATT, p.p. (95% interval)", fontsize=9.5)
    plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "figure3_event_study.png"), dpi=200); plt.close()


if __name__ == "__main__":
    os.makedirs(FIGURES, exist_ok=True)
    figure1(); figure2(); figure3()
    print("done: figures")
