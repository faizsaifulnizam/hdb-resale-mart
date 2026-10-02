# hdb-resale-mart

> **Answer:** 4-room resale price per m² **slipped 1.3%** in Q3 2026 vs a year earlier — national median S$6,647 → **S$6,559/m²** — and the move decomposes almost entirely into **within-town pricing** (rate −53.3 S$/m²) rather than a change in which towns sold (mix −0.7, ≈ 0). A slight dip; a rate story; one quarter.

**Status:** built 2026-10-02. Part of a six-repo series on Singapore's public data.

## Key numbers (all reproducible)

- **Headline:** national 4-room median price/m² 6,647 → 6,559 (−1.32%), Q3 2026 vs Q3 2025.
- **16 of 23** shown towns lower; range **Queenstown +10.9% → Bukit Batok −6.3%** (towns need ≥25 sales in each compared quarter to appear in headline charts; all 26 are in the CSV).
- **Shift-share** (transaction-weighted, means): total −40.6 S$/m² = rate **−53.3** + mix **−0.7** + interaction **+13.3**.
- **Robust across windows** (totals −0.6% … +1.0%): [`docs/sensitivity.md`](docs/sensitivity.md).

![4-room median price/m² by town — Q3 2026 vs Q3 2025](reports/figures/f1_town_dumbbell.png)

*Also in `reports/figures/`: rolling medians (`f2`), town-mix drift (`f3`), the rate/mix waterfall (`f4`) — plus the Power BI page [`bi/bi_page.png`](bi/bi_page.png) and the half-page [`docs/decision_memo.md`](docs/decision_memo.md).*

## The question

HDB resale prices are usually reported as a single index. But any move in that index can come from two very different places: flats getting more expensive per square metre, or the mix of transactions shifting (more sales in pricier towns, more larger flats). This repo separates the two for 4-room flats, transaction by transaction, since 2017.

## The data

- **HDB resale flat prices** (registration date, Jan-2017 onwards) — [data.gov.sg](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view), 241,822 rows × 11 columns at the 2026-10-02 pull (town, flat type, floor area, storey range, remaining lease, price).
- Licence: Singapore Open Data Licence (© Housing & Development Board). A script downloads the file into `data/raw/` (gitignored); the raw file is never edited.
- Cite note carried from HDB: prices are indicative; transactions between relatives and part-share sales are excluded.

## Method (short)

- DuckDB throughout; one row = one registered resale. [`sql/01_staging.sql`](sql/01_staging.sql) cleans (month → date, storey band → midpoint), [`sql/05_checks.sql`](sql/05_checks.sql) validates — 7/7 checks pass, 0 exclusions; [`docs/data_audit.md`](docs/data_audit.md) profiles the file.
- Town-month medians + 3-month rolling medians ([`sql/03_metrics.sql`](sql/03_metrics.sql)); headline table + shift-share decomposition ([`sql/04_yoy.sql`](sql/04_yoy.sql)) → [`outputs/town_4room_yoy.csv`](outputs/town_4room_yoy.csv).
- Figures are code-generated ([`src/figures.py`](src/figures.py)); the Power BI page is in [`bi/`](bi/README.md).

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

*Part of a six-repo series on Singapore's public data.* **The others:** [card-book-quality](https://github.com/faizsaifulnizam/card-book-quality) · [coe-quota-premium](https://github.com/faizsaifulnizam/coe-quota-premium) · [retail-sales-split](https://github.com/faizsaifulnizam/retail-sales-split) · [coe-category-break](https://github.com/faizsaifulnizam/coe-category-break) · [hdb-lease-slope](https://github.com/faizsaifulnizam/hdb-lease-slope)
