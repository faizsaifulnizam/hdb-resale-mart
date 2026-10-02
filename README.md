<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner.svg">
  <img src="assets/banner.svg" width="100%" alt="hdb-resale-mart — a six-repo series on Singapore's public data">
</picture>

# hdb-resale-mart

[![license: MIT](https://img.shields.io/badge/license-MIT-22607B.svg)](LICENSE) ![Python 3.12](https://img.shields.io/badge/Python-3.12-2E7D6B.svg) ![DuckDB](https://img.shields.io/badge/analytics-DuckDB-C0552B.svg) [![data: data.gov.sg](https://img.shields.io/badge/data-data.gov.sg-14293D.svg)](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) [![Power BI page](https://img.shields.io/badge/Power%20BI-page%20included-8A6EAF.svg)](bi/README.md)

> **Answer:** 4-room resale price per m² dipped in Q3 2026 vs a year earlier: **−1.3%** on the headline median (S$6,647 → **S$6,559/m²**) and **−0.6%** on the mean basis used for the decomposition — both point the same way (the split needs means because medians are not additive). The move is **within-town, not mix**: rate −53.3 S$/m² vs mix −0.7, interaction +13.3 reported separately. A small dip; a rate story; one quarter.

**Status:** built 2026-10-02. Part of a six-repo series on Singapore's public data.

## Key numbers (all reproducible)

- **Headline:** national 4-room median price/m² 6,647 → 6,559 (**−1.32%**, medians) · **−0.57%** on the mean basis that the split uses; Q3 2026 vs Q3 2025.
- **16 of 23** shown towns lower; range **Queenstown +10.9% → Bukit Batok −6.3%** (towns need ≥25 sales in each compared quarter to appear in headline charts; all 26 are in the CSV).
- **Shift-share** (transaction-weighted, means): total −40.6 S$/m² = rate **−53.3** + mix **−0.7** + interaction **+13.3** (the overlap term — town-weight shifts coinciding with town-price moves; reported, not folded in).
- **Robust across windows** (totals −0.6% … +1.0%): [`docs/sensitivity.md`](docs/sensitivity.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="reports/figures/f1_town_dumbbell-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="reports/figures/f1_town_dumbbell.png">
  <img src="reports/figures/f1_town_dumbbell.png" width="100%" alt="4-room median price/m² by town — Q3 2026 vs Q3 2025">
</picture>

### More views

| | |
|---|---|
| <a href="reports/figures/f2_rolling_median.png"><picture><source media="(prefers-color-scheme: dark)" srcset="reports/figures/f2_rolling_median-dark.png"><source media="(prefers-color-scheme: light)" srcset="reports/figures/f2_rolling_median.png"><img src="reports/figures/f2_rolling_median.png" alt="3-month rolling medians of town price/m²"></picture></a> | <a href="reports/figures/f3_mix_drift.png"><picture><source media="(prefers-color-scheme: dark)" srcset="reports/figures/f3_mix_drift-dark.png"><source media="(prefers-color-scheme: light)" srcset="reports/figures/f3_mix_drift.png"><img src="reports/figures/f3_mix_drift.png" alt="Town-mix drift over the sample"></picture></a> |
| <a href="reports/figures/f4_waterfall.png"><picture><source media="(prefers-color-scheme: dark)" srcset="reports/figures/f4_waterfall-dark.png"><source media="(prefers-color-scheme: light)" srcset="reports/figures/f4_waterfall.png"><img src="reports/figures/f4_waterfall.png" alt="Rate/mix waterfall of the national move"></picture></a> | <a href="reports/figures/bi_page.png"><picture><source media="(prefers-color-scheme: dark)" srcset="reports/figures/bi_page-dark.png"><source media="(prefers-color-scheme: light)" srcset="reports/figures/bi_page.png"><img src="reports/figures/bi_page.png" alt="The Power BI page for this dataset"></picture></a> |

*Rolling medians (`f2`), town-mix drift (`f3`), the rate/mix waterfall (`f4`), and the Power BI page (`bi_page`) — full size in [`reports/figures/`](reports/figures/) · half-page write-up in [`docs/decision_memo.md`](docs/decision_memo.md).*

## The question

HDB resale prices are usually reported as a single index. But any move in that index can come from two very different places: flats getting more expensive per square metre, or the mix of transactions shifting (more sales in pricier towns, more larger flats). This repo separates the two for 4-room flats, transaction by transaction, since 2017.

## The data

- **HDB resale flat prices** (registration date, Jan-2017 onwards) — [data.gov.sg](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view), 241,822 rows × 11 columns at the 2026-10-02 pull (town, flat type, floor area, storey range, remaining lease, price).
- Licence: Singapore Open Data Licence (© Housing & Development Board). A script downloads the file into `data/raw/` (gitignored); the raw file is never edited.
- Cite note carried from HDB: prices are indicative; transactions between relatives and part-share sales are excluded.

## Method (short)

DuckDB throughout; one row = one registered resale. The pipeline, end to end:

1. **Pull** — scripted from data.gov.sg into `data/raw/` (never edited): [`src/download.py`](src/download.py)
2. **Audit** — profile, then rules set *before* analysis: [`docs/data_audit.md`](docs/data_audit.md)
3. **Stage** — parse & clean; every exclusion counted: [`sql/01_staging.sql`](sql/01_staging.sql)
4. **Check** — 7 assertions, fail loudly: [`sql/05_checks.sql`](sql/05_checks.sql) — 7/7 pass, 0 exclusions
5. **Measure** — town×type×month medians + rolling 3-month medians: [`sql/03_metrics.sql`](sql/03_metrics.sql)
6. **Decompose** — headline table + shift-share (rate / mix / interaction): [`sql/04_yoy.sql`](sql/04_yoy.sql) → [`outputs/town_4room_yoy.csv`](outputs/town_4room_yoy.csv)
7. **Stress** — window + threshold variants: [`docs/sensitivity.md`](docs/sensitivity.md)
8. **Draw · write · present** — figures are code, light + dark ([`src/figures.py`](src/figures.py)); then the memo ([`docs/decision_memo.md`](docs/decision_memo.md)) and the Power BI page ([`bi/`](bi/README.md))

Why each choice was made — why quarters, why medians to display but means to split, why the ≥25 display rule, what was validated — is written out in **[`docs/method.md`](docs/method.md)**.

## Reproduce

```bash
git clone https://github.com/faizsaifulnizam/hdb-resale-mart && cd hdb-resale-mart
uv venv .venv --python 3.12          # or: python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt   # or: pip install -r requirements.txt

python src/download.py       # raw CSV → data/raw/ (gitignored)
python src/build_dataset.py  # staging + 7 checks → data/processed/sales.parquet
python src/analysis.py       # medians, YoY, decomposition, sensitivity → outputs/
python src/figures.py        # re-renders reports/figures/
```

Then check `outputs/town_4room_yoy.csv`: Queenstown reads 10,666.67 → 11,833.33, and the national medians match the headline above. Data as of the 2026-10-02 pull — a later re-pull can move the newest months.

## Caveats

- Registrations, not listings; the newest months can revise upward as registrations complete.
- Medians are the display metric; the decomposition uses transaction-weighted means (medians are not additive — see the memo).
- Display threshold: towns with <25 sales in a compared quarter stay in the CSV but are dropped from headline charts (3 towns at this build).
- Descriptive only — no forecast, no causal claim. Context (interest rates, BTO supply, grants) is out of scope.

## Out of scope

A price predictor, block-level maps, dbt/Snowflake (a BigQuery sandbox is optional and never used as the archive).

## Licence

Code: MIT. Data: Singapore Open Data Licence — © Housing & Development Board, via data.gov.sg. This is an independent, unofficial analysis.

---

*Part of a six-repo series on Singapore's public data — the other five repos go live as they're built:* **card-book-quality · coe-quota-premium · retail-sales-split · coe-category-break · hdb-lease-slope**
