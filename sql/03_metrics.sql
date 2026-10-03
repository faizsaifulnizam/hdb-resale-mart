-- 03_metrics.sql — monthly metrics for the series figures (built by src/analysis.py).
-- Grain: town × flat_type × month · town = '(all)' rows are the Singapore pooled series.
--   n           = transactions in the month
--   med_ppsm    = median price/m² that month (display series)
--   mean_ppsm   = mean price/m² (feeds decomposition checks)
--   n_3m        = transactions in the trailing 3 CALENDAR months (missing months contribute 0)
--   r3_med_ppsm = rolling 3-month median — median of the last 3 monthly medians in the
--                 calendar window (missing months contribute no median)
-- Window: full history, months up to and including 2026-09
-- (2026-10 is partial — see docs/data_audit.md).
-- The frame is calendar-aware (RANGE over months), not row-count based: a town-month with
-- gaps must not reach back further than three calendar months.

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
    RANGE BETWEEN INTERVAL 2 MONTH PRECEDING AND CURRENT ROW
);
