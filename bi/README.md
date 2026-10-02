# Power BI page — 4-room resale, Q3 2026 vs Q3 2025

Screenshot: [`reports/figures/bi_page.png`](../reports/figures/bi_page.png) — the page built in Power BI Desktop (free) from `outputs/town_4room_yoy.csv` (26 towns, one row per town). A finding strip — three KPI cards: **26 towns** in the comparison · **3,270 resales** (Q3 2026 vs Q3 2025, +7%) · **−1.64%** median town change — sits above four visuals:

1. **Clustered bar** — median price/m² by town, Q3 2025 vs Q3 2026 (`med_ppsm_2025q3` / `med_ppsm_2026q3`)
2. **Clustered column** — shift-share components by town (`rate_effect`, `mix_effect`, `interaction`)
3. **Scatter** — transactions vs price change (`n_t1` × `med_pct_change`), one dot per town
4. **Table** — `town`, `n_t0`, `n_t1`, `med_ppsm_2026q3`, `med_pct_change`, `rate_effect`, `mix_effect`

Both theme renders ship: [`bi_page.png`](../reports/figures/bi_page.png) (light) and [`bi_page-dark.png`](../reports/figures/bi_page-dark.png) (dark) — the repo README swaps them with `<picture>`, so dark-theme visitors see the ink version.

**Rebuild:** the page is maintained as a Power BI project (`.pbip` — report + semantic model as text files) in my workspace; the committed PNG is its latest rendering. Rebuilding from the CSV alone: Power BI Desktop → Get data → Text/CSV → `outputs/town_4room_yoy.csv` → recreate the fields above. (Original build 2026-10-02 on Power BI Desktop v2.158.1177.0; refreshed 2026-10-03; series-styled the same day — Source Serif 4 / Inter, petrol-led palette, header band + rule, registered as a theme in the project.)

**Notes**

- The `.pbix` is a binary and is not committed — it ships via [Releases](https://github.com/faizsaifulnizam/hdb-resale-mart/releases) (open it to refresh data via Home → Refresh after re-running `python src/analysis.py`).
- This page shows all 26 towns — the ≥25-transactions display threshold applies to the matplotlib figures only.
- Medians are the display metric; the shift-share decomposition uses means (medians are not additive — see the decision memo).
