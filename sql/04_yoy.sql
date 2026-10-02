-- 04_yoy.sql — headline table: 4-room, Q3 2026 vs Q3 2025 (same quarter a year earlier).
-- Built by src/analysis.py. Writes: outputs/town_4room_yoy.csv.
--
-- Shift-share decomposition (transaction-weighted; spec 01 §4):
--   p = town mean price/m² in a quarter; w = town share of 4-room transactions
--   total = Σ w1·p1 − Σ w0·p0 · rate = Σ w0·(p1−p0) · mix = Σ (w1−w0)·p0 · interaction = Σ (w1−w0)·(p1−p0)
--   Means feed the decomposition (medians are not additive) · medians are kept for display.
--
-- Build constants (data pull 2026-10-02; keep in sync with src/analysis.py):
--   t0 = 2025-07-01 → 2025-09-30 · t1 = 2026-07-01 → 2026-09-30

CREATE OR REPLACE TABLE yoy_4room AS
WITH base AS (
    SELECT
        town,
        CASE
            WHEN sale_date BETWEEN DATE '2026-07-01' AND DATE '2026-09-30' THEN 1
            WHEN sale_date BETWEEN DATE '2025-07-01' AND DATE '2025-09-30' THEN 0
        END AS period,
        resale_price / floor_area_sqm AS ppsm
    FROM sales
    WHERE flat_type = '4 ROOM'
      AND sale_date BETWEEN DATE '2025-07-01' AND DATE '2026-09-30'
),
agg AS (
    SELECT town, period,
           count(*)     AS n,
           avg(ppsm)    AS mean_ppsm,
           median(ppsm) AS med_ppsm
    FROM base
    WHERE period IS NOT NULL
    GROUP BY town, period
),
piv AS (
    SELECT town,
           max(CASE WHEN period = 0 THEN n END)         AS n_t0,
           max(CASE WHEN period = 1 THEN n END)         AS n_t1,
           max(CASE WHEN period = 0 THEN mean_ppsm END) AS mean_t0,
           max(CASE WHEN period = 1 THEN mean_ppsm END) AS mean_t1,
           max(CASE WHEN period = 0 THEN med_ppsm END)  AS med_t0,
           max(CASE WHEN period = 1 THEN med_ppsm END)  AS med_t1
    FROM agg
    GROUP BY town
),
w AS (
    SELECT *,
           n_t0 / sum(n_t0) OVER () AS w_t0,
           n_t1 / sum(n_t1) OVER () AS w_t1
    FROM piv
)
SELECT * FROM w;

-- Export (rounded for display; national totals = sums of the contribution columns).
COPY (
    SELECT
        town,
        n_t0,
        n_t1,
        round(med_t0, 2)  AS med_ppsm_2025q3,
        round(med_t1, 2)  AS med_ppsm_2026q3,
        round(100 * (med_t1 / med_t0 - 1), 2) AS med_pct_change,
        round(mean_t0, 2) AS mean_ppsm_2025q3,
        round(mean_t1, 2) AS mean_ppsm_2026q3,
        round(w_t0, 4)    AS share_2025q3,
        round(w_t1, 4)    AS share_2026q3,
        round(w_t0 * (mean_t1 - mean_t0), 2)          AS rate_effect,
        round((w_t1 - w_t0) * mean_t0, 2)             AS mix_effect,
        round((w_t1 - w_t0) * (mean_t1 - mean_t0), 2) AS interaction
    FROM yoy_4room
    ORDER BY n_t1 DESC
) TO 'outputs/town_4room_yoy.csv' (HEADER);
