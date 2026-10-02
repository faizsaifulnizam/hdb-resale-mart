-- 01_staging.sql — raw CSV -> cleaned sales table.
-- Reads:  data/raw/hdb-resale-prices-2017-onwards.csv (never modified)
-- Writes: table `sales`; parquet copy handled by src/build_dataset.py.
-- Every exclusion below is counted and printed by src/build_dataset.py.

CREATE OR REPLACE TABLE sales AS
SELECT
    CAST(strptime(month, '%Y-%m') AS DATE)                          AS sale_date,
    date_trunc('month', CAST(strptime(month, '%Y-%m') AS DATE))     AS sale_month,
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
WHERE resale_price > 0
  AND floor_area_sqm > 0
  AND regexp_matches(month, '^[0-9]{4}-[0-9]{2}$')
  AND remaining_lease IS NOT NULL;
