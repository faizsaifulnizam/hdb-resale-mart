# hdb-resale-mart

> **After 2023, did 4-room HDB resale prices rise because flats became more expensive per square metre — or because the mix of towns and flat sizes sold changed?**

**Status:** scaffolded — question, data and approach are locked; analysis, figures and reproduce steps pending. Part of a six-repo series on Singapore's public data.

## The question

HDB resale prices are usually reported as a single index. But any move in that index can come from two very different places: flats getting more expensive per square metre, or the mix of transactions shifting (more sales in pricier towns, more larger flats). This repo separates the two for 4-room flats, transaction by transaction, since 2017.

## The data

- **HDB resale flat prices** (registration date, Jan-2017 onwards) — [data.gov.sg](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view), ~240,000 rows, 11 columns including town, flat type, floor area, storey range and remaining lease.
- Licence: Singapore Open Data Licence (© Housing & Development Board). A script downloads the file into `data/raw/` (gitignored); the raw file is never edited.
- Cite note carried from HDB: prices are indicative; transactions between relatives and part-share sales are excluded.

## Planned approach

- Load into DuckDB; one row = one registered resale.
- Build price per m²; town-month medians and 3-month rolling medians via SQL window functions.
- Mix vs rate: hold flat type fixed (4-room) and split the price move into a within-town price effect and a town-share (mix) effect.
- Four-visual Power BI page (screenshot committed); one query a reviewer can run and match to `outputs/town_4room_yoy.csv`.
- One-page decision memo: what moved, why, and what a buyer should not conclude.

## Done when

A stranger can clone the repo, run the download and SQL, and match the number in the memo. The README leads with the answer; raw data and credentials are not in git.

## Out of scope

A price predictor, block-level maps, dbt/Snowflake (a BigQuery sandbox is optional and never used as the archive).

## Licence

Code: MIT. Data: Singapore Open Data Licence — © Housing & Development Board, via data.gov.sg. This is an independent, unofficial analysis.

---

*Part of a six-repo series on Singapore's public data.* **The others:** [card-book-quality](https://github.com/faizsaifulnizam/card-book-quality) · [coe-quota-premium](https://github.com/faizsaifulnizam/coe-quota-premium) · [retail-sales-split](https://github.com/faizsaifulnizam/retail-sales-split) · [coe-category-break](https://github.com/faizsaifulnizam/coe-category-break) · [hdb-lease-slope](https://github.com/faizsaifulnizam/hdb-lease-slope)
