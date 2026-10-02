# Power BI page — 4-room resale, Q3 2026 vs Q3 2025

Screenshot: [`reports/figures/bi_page.png`](../reports/figures/bi_page.png) — the page built in Power BI Desktop (free) from `outputs/town_4room_yoy.csv` (26 towns, one row per town). A finding strip (title + 26 towns · 3,270 transactions · -1.64% median town change) sits above four visuals:

1. **Clustered bar** — median price/m² by town, Q3 2025 vs Q3 2026 (`med_ppsm_2025q3` / `med_ppsm_2026q3`)
2. **Clustered column** — shift-share components by town (`rate_effect`, `mix_effect`, `interaction`)
3. **Scatter** — transactions vs price change (`n_t1` × `med_pct_change`), one dot per town
4. **Table** — `town`, `n_t0`, `n_t1`, `med_ppsm_2026q3`, `med_pct_change`, `rate_effect`, `mix_effect`

**Rebuild:** the page is maintained as a Power BI project (`.pbip` — report + semantic model as text files) in my workspace; the committed PNG is its latest rendering. Rebuilding from the CSV alone: Power BI Desktop → Get data → Text/CSV → `outputs/town_4room_yoy.csv` → recreate the fields above. (Original build 2026-10-02 on Power BI Desktop v2.158.1177.0; refreshed 2026-10-03.)

**Notes**

- The `.pbix` is a binary and is not committed — it ships via [Releases](https://github.com/faizsaifulnizam/hdb-resale-mart/releases) (open it to refresh data via Home → Refresh after re-running `python src/analysis.py`).
- This page shows all 26 towns — the ≥25-transactions display threshold applies to the matplotlib figures only.
- Medians are the display metric; the shift-share decomposition uses means (medians are not additive — see the decision memo).
