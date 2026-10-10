-- 04_yoy.sql — headline table: 4-room, Q3 2026 vs Q3 2025 (same quarter a year earlier).
-- Built by src/analysis.py and src/figures.py. Read-only relation; export in sql/04_export.sql.
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
