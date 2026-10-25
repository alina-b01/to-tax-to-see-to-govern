# Replication package
#### Author: Alina Bikaeva *(alinab@uchicago.edu)*
#### The University of Chicago. Harris School of Public Policy

**To Tax, to See, to Govern: State Capacity and the Limits of Centralization in Russia** (working paper, October 2026). An early short version appeared in the Chicago Policy Review (2026) as “The Gluttonous Leviathan: How Russia's Digital Extraction Disguises Physical Decay”.

The package reproduces every table, figure and number in the paper and its online appendix from the included data. Raw source files (Treasury and FNS archives, Rosstat and EMISS downloads, BDPMO extracts, NOAA station files) are not redistributed; the scripts in `build/` document how the included data were constructed from them.

## Layout

```
analysis/   scripts that produce all results (run from this folder)
build/      data construction from raw sources
config/     budget classification codes used by build/parse_roskazna.py and build/parse_kbk.py
data/       all datasets used by analysis/ and build/, plus codebook.csv
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

Remaining files in `data/` are intermediate inputs of `build/`.

Sources: Federal Treasury reports on consolidated regional budgets (form 0503317); FNS form 1-NM; Rosstat, Regions of Russia and housing statistics; EMISS; the Municipal Indicators Database (BDPMO) via tochno.st; NOAA GHCN-Daily; CPI by region (Rosstat); Ministry of Energy; mayoral selection data from Reuter et al. (2016) and Buckley, Reuter, Rochlitz and Aisin (2021, Harvard Dataverse, doi:10.7910/DVN/XD2KRJ); decision dates from Beazer, Buckley and Reuter (2026).

## Data construction

Order of `build/` steps: `parse_roskazna.py` → `extract_transfer_lines.py` → `build_jkh_transfers.py`; `parse_fns_1nm.py`; `parse_rr_text.py`, `deflate.py`; `hdd_ghcn.py`; `parse_emiss_heat.py`; `build_heat_from_uploads.py`, `parse_minenergo_appendix.py`; `build_elections.py`; then `build_panel_h1.py` → `add_emiss_to_panel.py` → `add_climate_prices.py`. The city panel is built by `filter_tochno_budgets.py` → `build_city_panel.py` (raw BDPMO files in `$BDPMO_DIR`). `regions.py` and `parse_region_table.py` are shared helpers.

Two steps were done by hand and are not scripted: combining the regional heat-supply series into `heat_region_combined_long.csv` (from the other `heat_*` files, preferring the latest statistical edition), and the city-level mayor coding (`mayors_*.csv`), built from the replication data cited above and verified manually for 2019-2024 as documented in `docs/mayor_coding_2019_2024.xlsx`.

## Notes

- Municipal estimates: Callaway and Sant'Anna (2021) group-time ATTs with base year g−1 and not-yet-treated controls, averaged over event years 0-3 with cohort-size weights. Standard errors come from a region cluster bootstrap (1,999 draws, seed 1), implemented with city multiplicity weights; this is equivalent to resampling regions with replacement. Earlier working versions reported 2.28 instead of 2.14 for one standard error (corrected coding, 2010-2024, networks); the difference was Monte Carlo noise from 499 draws.
- The conditional DiD (regression adjustment on 2010 characteristics) is exploratory, not the doubly robust estimator; because its bootstrap distribution is heavy-tailed, the paper reports percentile intervals (`ci_lo_pct`, `ci_hi_pct`).
- Figures carry English labels, matching the English version of the paper.
- Ownership (2019) and price zones are measured after most transitions; Table C1 is descriptive.
- No formal sensitivity analysis for violations of parallel trends (Rambachan and Roth, 2023) is included.
