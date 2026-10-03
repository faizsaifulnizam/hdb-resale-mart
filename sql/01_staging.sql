-- 01_staging.sql — raw CSV -> cleaned sales table.
-- Reads:  data/raw/hdb-resale-prices-2017-onwards.csv (never modified)
-- Writes: table `sales`; parquet copy handled by src/build_dataset.py.
-- Every exclusion rule below is mirrored in the WHERE clause and counted by src/build_dataset.py
-- (retained + excluded must reconcile to the raw row count). Bad months (e.g. '2026-13') are
-- excluded via try_strptime, not by crashing the strict parser.

CREATE OR REPLACE TABLE sales AS
SELECT
    CAST(TRY_STRPTIME(month, '%Y-%m') AS DATE)                          AS sale_date,
    date_trunc('month', CAST(TRY_STRPTIME(month, '%Y-%m') AS DATE))     AS sale_month,
    town,
    flat_type,
    block,
    street_name,
    TRY_CAST(regexp_extract(storey_range, '^([0-9]+)', 1) AS INTEGER)   AS storey_low,
    TRY_CAST(regexp_extract(storey_range, 'TO ([0-9]+)$', 1) AS INTEGER) AS storey_high,
    (TRY_CAST(regexp_extract(storey_range, '^([0-9]+)', 1) AS INTEGER)
     + TRY_CAST(regexp_extract(storey_range, 'TO ([0-9]+)$', 1) AS INTEGER)) / 2.0 AS storey_mid,
    floor_area_sqm,
    flat_model,
    TRY_CAST(lease_commence_date AS INTEGER)                            AS lease_commence_year,
    (TRY_CAST(regexp_extract(remaining_lease, '^([0-9]+) year', 1) AS INTEGER)
     + COALESCE(TRY_CAST(regexp_extract(remaining_lease, '([0-9]+) month', 1) AS INTEGER), 0) / 12.0) AS remaining_lease_years,
    resale_price,
    resale_price / NULLIF(floor_area_sqm, 0)                        AS price_per_sqm
FROM read_csv_auto('data/raw/hdb-resale-prices-2017-onwards.csv')
WHERE resale_price IS NOT NULL
  AND resale_price > 0
  AND floor_area_sqm IS NOT NULL
  AND floor_area_sqm > 0
  AND TRY_STRPTIME(month, '%Y-%m') IS NOT NULL
  AND remaining_lease IS NOT NULL;
