-- 03_metrics.sql — monthly metrics for the series figures (built by src/analysis.py).
-- Grain: town × flat_type × month · town = '(all)' rows are the Singapore pooled series.
--   n           = transactions in the month
--   med_ppsm    = median price/m² that month (display series)
--   mean_ppsm   = mean price/m² (feeds decomposition checks)
--   n_3m        = transactions, trailing 3 months
--   r3_med_ppsm = rolling 3-month median — median of the trailing 3 monthly medians
-- Window: full history, months up to and including 2026-09
-- (2026-10 is partial — see docs/data_audit.md).

CREATE OR REPLACE TABLE town_month_metrics AS
WITH monthly AS (
    SELECT
        coalesce(town, '(all)') AS town,
        flat_type,
        sale_month,
        count(*)              AS n,
        median(price_per_sqm) AS med_ppsm,
        avg(price_per_sqm)    AS mean_ppsm
    FROM sales
    WHERE sale_month <= DATE '2026-09-01'
    GROUP BY GROUPING SETS ((town, flat_type, sale_month), (flat_type, sale_month))
)
SELECT
    town,
    flat_type,
    sale_month,
    n,
    med_ppsm,
    mean_ppsm,
    sum(n) OVER w           AS n_3m,
    median(med_ppsm) OVER w AS r3_med_ppsm
FROM monthly
WINDOW w AS (
    PARTITION BY town, flat_type
    ORDER BY sale_month
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
);
