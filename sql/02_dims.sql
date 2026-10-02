-- 02_dims.sql — light dimension views (views only, built by src/analysis.py).

CREATE OR REPLACE VIEW dim_town AS
SELECT DISTINCT town FROM sales;

CREATE OR REPLACE VIEW dim_flat_type AS
SELECT flat_type, count(*) AS n_transactions
FROM sales
GROUP BY flat_type;
