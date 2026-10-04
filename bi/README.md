# Power BI page — 4-room resale, Q3 2026 vs Q3 2025

Screenshot: [`reports/figures/bi_page.png`](../reports/figures/bi_page.png) — the page built in Power BI Desktop (free) from `outputs/town_4room_yoy.csv` (26 towns, one row per town). A finding strip — three KPI cards: **26 towns** in the comparison · **3,270 resales · +7.0%** (Q3 2026 vs Q3 2025; computed from 3,057 prior-quarter-year sales) · **−1.64%** median of the 26 towns' changes (distinct from the national headline — it's the median across towns, not a national figure) — sits above four visuals. The footer carries the source line, the national decomposition totals (rate −53.3 · mix −0.7 · interaction +13.3 · total −40.6 S$/m²), and a pointer to the full town table — the on-page table scrolls, so the PNG is an overview of all 26 towns, not the whole list.

1. **Clustered bar** — median price/m² by town, Q3 2025 vs Q3 2026 (`med_ppsm_2025q3` / `med_ppsm_2026q3`)
2. **Clustered column** — shift-share components by town (`rate_effect`, `mix_effect`, `interaction`)
3. **Scatter** — transactions vs price change (`n_t1` × `med_pct_change`), one dot per town
4. **Table** — `town`, `n_t0`, `n_t1`, `med_ppsm_2026q3`, `med_pct_change`, `rate_effect`, `mix_effect` — town-level detail with **no totals row**: medians are not additive (a sum of town medians is meaningless), and the additive totals live in the memo and the charts.

Both theme renders ship: [`bi_page.png`](../reports/figures/bi_page.png) (light) and [`bi_page-dark.png`](../reports/figures/bi_page-dark.png) (dark) — the repo README swaps them with `<picture>`, so dark-theme visitors see the ink version.

**Rebuild:** the editable, cache-free Power BI project is committed at [`source/hdb-resale-mart.pbip`](source/hdb-resale-mart.pbip). Run the repo pipeline first. In `source/hdb-resale-mart.SemanticModel/definition/tables/town_4room_yoy.tmdl`, replace `REPLACE_WITH_ABSOLUTE_PATH_TO_OUTPUTS/town_4room_yoy.csv` with your checkout's absolute CSV path, then open the `.pbip` in Power BI Desktop and refresh. No personal machine path or cached data is shipped in the source. The release `.pbix` includes its imported snapshot; before refreshing on another machine, use Transform data → Data source settings → Change Source to select your CSV. Export a new `.pbix` using Desktop File → Save as → Power BI file (not a programmatic conversion).

**Notes**

- The resale callout uses `Resales KPI`: `SUM(n_t1)` and `(SUM(n_t1) − SUM(n_t0)) / SUM(n_t0)` in the current filter context, rounded to one decimal percent. A zero/blank prior count shows `YoY unavailable`. `Resales Alt Text` reuses that measure, names both Q3 windows, gives the prior count, and distinguishes count growth from price change; there is no literal `+7%`.
- Run `python bi/check_report.py` for the source regression check; add `--pbix <release-file.pbix>` to inspect the exported report bindings and ZIP integrity. These checks complement, not replace, opening and rendering the artifact in Desktop.
- The `.pbix` is a binary and is not committed — it ships via [Releases](https://github.com/faizsaifulnizam/hdb-resale-mart/releases) (open it to refresh data via Home → Refresh after re-running `python src/analysis.py`).
- Chart legends and table headers use plain-English labels ("Q3 2025", "Rate (S$/m²)", "Sales, Q3 2025", …) rather than auto-generated "Sum of med_ppsm…" field names.
- This page shows all 26 towns — the ≥25-transactions display threshold applies to the matplotlib figures only.
- Medians are the display metric; the shift-share decomposition uses means (medians are not additive — see the decision memo).
