# Replication package
#### Author: Alina Bikaeva *(alinab@uchicago.edu)*
#### The University of Chicago Harris School of Public Policy

**To Tax, to See, to Govern: State Capacity and the Limits of Centralization in Russia** (working paper, October 2026). An early short version appeared in the Chicago Policy Review (2026) as “The Gluttonous Leviathan: How Russia's Digital Extraction Disguises Physical Decay”.

The package reproduces every table, figure and number in the paper and its online appendix from the included data. Raw source files (Treasury and FNS archives, Rosstat and EMISS downloads, BDPMO extracts, NOAA station files) are not redistributed; the scripts that construct the included data from them are available from the author on request.

## Online appendix

This repository serves as the online appendix to the paper:

- **Appendix A** (data and replication): this README, `data/codebook.csv` and `docs/mayor_coding_2019_2024.xlsx`.
- **Appendix B** (additional tables): Tables B1–B4 in `output/tables/` (`tableB1_regional_robustness.csv`, `tableB2_cohorts.csv`, `tableB3_municipal_robustness.csv`, `tableB4_horizons.csv`).
- **Appendix C** (exploratory test of H2c): Table C1 in `output/tables/tableC1_heterogeneity.csv`, with ownership shares in `capital_ownership_2019.csv`.

## Layout

```
analysis/   scripts that produce all results (run from this folder)
config/     budget classification codes used in data construction
data/       all datasets used by analysis/, plus codebook.csv
docs/       manual verification of mayoral selection methods, 2019-2024 (English; city names in Russian)
output/     tables/ (CSV) and figures/ (PNG) written by analysis/
```

## Running

Python 3.10+; `pip install -r requirements.txt`. Then

```
./run_all.sh
```

Runtime is about 12 minutes on one CPU, almost all of it in `municipal.py` (1,999 bootstrap draws per specification). Sections can be run separately: `python municipal.py main timing robustness horizons heterogeneity conditional cohorts`. `figures.py` reads outputs of `descriptives.py` and `municipal.py`.

## Outputs

Numbering below follows the full version of the paper. In the abridged version (writing sample), Figure 2 corresponds to Figure 3 here (`figures/figure3_event_study.png`) and Table 4 corresponds to Table 5 here (`tables/table5_reporting_jumps.csv`). Table 4 here (timing) is summarized in the text of section 6.5 of the abridged version, and Figure 2 here (binscatter) appears only in the full version. Tables 1–3, Figure 1 and Appendices B–C are numbered the same in both versions.

| Paper | Script | File in output/ |
|---|---|---|
| Table 1 | descriptives.py | tables/table1_descriptives.csv |
| Sections 3.3, 4.3, 4.4 (measure agreement, ownership, price zones) | descriptives.py | tables/descriptive_statistics.csv |
| Figure 1 | descriptives.py, figures.py | tables/figure1_medians.csv, figures/figure1_trends.png |
| Table 2, Figure 2 | regional.py, figures.py | tables/table2_regional.csv, figures/figure2_binscatter.png |
| Sections 6.2-6.4 (decomposition, tariffs, targeted transfers, lags, reverse models) | regional.py | tables/regional_text_statistics.csv |
| Table 3 | municipal.py main, conditional | tables/table3_municipal_did.csv, tables/table3_conditional_did.csv |
| Figure 3 | municipal.py main, figures.py | tables/figure3_event_study.csv, figures/figure3_event_study.png |
| Table 4 | municipal.py timing | tables/table4_timing.csv |
| Table 5, Novotroitsk example | reporting.py | tables/table5_reporting_jumps.csv, tables/reporting_jump_events.csv, tables/example_novotroitsk.csv |
| Table B1 | regional.py | tables/tableB1_regional_robustness.csv |
| Table B2, control counts in 5.2 | municipal.py cohorts | tables/tableB2_cohorts.csv, tables/att_cells_corrected_2018.csv |
| Table B3 | municipal.py robustness | tables/tableB3_municipal_robustness.csv |
| Table B4 | municipal.py horizons | tables/tableB4_horizons.csv |
| Table C1 | municipal.py heterogeneity | tables/tableC1_heterogeneity.csv, tables/capital_ownership_2019.csv |

## Data

Variables of the analysis datasets are documented in `data/codebook.csv`.

Analysis datasets:

| File | Content |
|---|---|
| panel_h1.csv | Regional panel: 80 territorial units, 2010-2023 (Arkhangelsk and Tyumen oblasts include their autonomous okrugs; Crimea and Sevastopol excluded). Money in 2010 prices where indicated. |
| city_panel_bdpmo.csv | Urban okrugs, 2006-2025, from the Municipal Indicators Database (BDPMO): heat networks, local budgets (to 2020), roads, population. |
| mayors_treatment_v2.csv | Mayoral selection timing by city; `year_transition_v2` is the corrected coding used in the paper. |
| mayors_treatment.csv | Original coding (`year_transition`) and decision dates (`bbr_cancel_year`). |
| mayors_appointed_panel.csv | City-year indicator of an appointed head, 1990-2018 (used to identify reversals). |
| emiss_heat_long.csv | EMISS heat-network series for regions and administrative centers, by ownership. |
| price_zones_heat.csv | Municipalities assigned to heat price zones, 2018-2023 (Ministry of Energy report for 2023, table 67). |

Remaining files in `data/` are intermediate inputs used to construct the analysis datasets.

Sources: Federal Treasury reports on consolidated regional budgets (form 0503317); FNS form 1-NM; Rosstat, Regions of Russia and housing statistics; EMISS; the Municipal Indicators Database (BDPMO) via tochno.st; NOAA GHCN-Daily; CPI by region (Rosstat); Ministry of Energy; mayoral selection data from Reuter et al. (2016) and Buckley, Reuter, Rochlitz and Aisin (2021, Harvard Dataverse, doi:10.7910/DVN/XD2KRJ); decision dates from Beazer, Buckley and Reuter (2026).

## Data construction

The data-construction scripts are not included in this repository and are available from the author on request.

Two steps were done by hand and are not scripted: combining the regional heat-supply series into `heat_region_combined_long.csv` (from the other `heat_*` files, preferring the latest statistical edition), and the city-level mayor coding (`mayors_*.csv`), built from the replication data cited above and verified manually for 2019-2024 as documented in `docs/mayor_coding_2019_2024.xlsx`.

## Notes

- Municipal estimates: Callaway and Sant'Anna (2021) group-time ATTs with base year g−1 and not-yet-treated controls, averaged over event years 0-3 with cohort-size weights. Standard errors come from a region cluster bootstrap (1,999 draws, seed 1), implemented with city multiplicity weights; this is equivalent to resampling regions with replacement. Earlier working versions reported 2.28 instead of 2.14 for one standard error (corrected coding, 2010-2024, networks); the difference was Monte Carlo noise from 499 draws.
- The conditional DiD (regression adjustment on 2010 characteristics) is exploratory, not the doubly robust estimator; because its bootstrap distribution is heavy-tailed, the paper reports percentile intervals (`ci_lo_pct`, `ci_hi_pct`).
- Ownership (2019) and price zones are measured after most transitions; Table C1 is descriptive.
- No formal sensitivity analysis for violations of parallel trends (Rambachan and Roth, 2023) is included.
