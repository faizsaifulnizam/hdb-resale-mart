# Power BI page — 4-room resale, Q3 2026 vs Q3 2025

Screenshot: [`reports/figures/bi_page.png`](../reports/figures/bi_page.png) — the page built in Power BI Desktop (free) from `outputs/town_4room_yoy.csv`
(26 towns, one row per town). Four visuals:

1. **Clustered bar** — median price/m² by town, Q3 2025 vs Q3 2026 (`med_ppsm_2025q3` / `med_ppsm_2026q3`)
2. **Clustered column** — shift-share components by town (`rate_effect`, `mix_effect`, `interaction`)
3. **Scatter** — transactions vs price change (`n_t1` × `med_pct_change`), one dot per town
4. **Table** — `town`, `n_t0`, `n_t1`, `med_ppsm_2026q3`, `med_pct_change`, `rate_effect`, `mix_effect`

**Rebuild:** open Power BI Desktop → Get data → Text/CSV → `outputs/town_4room_yoy.csv` → build the four visuals above. (Built 2026-10-02 on Power BI Desktop v2.158.1177.0.)

**Notes**

- The `.pbix` is a binary and is not committed; keep it locally and refresh via Home → Refresh after re-running `python src/analysis.py`.
- This page shows all 26 towns — the ≥25-transactions display threshold applies to the matplotlib figures only.
- Medians are the display metric; the shift-share decomposition uses means (medians are not additive — see the decision memo).
