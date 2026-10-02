-- 05_checks.sql — validation queries for the staged `sales` table.
-- Each row: one check. src/build_dataset.py runs this and asserts all violations = 0.

SELECT 'price > 0'            AS check_name, count(*) AS violations FROM sales WHERE resale_price <= 0
UNION ALL SELECT 'area > 0',           count(*) FROM sales WHERE floor_area_sqm <= 0
UNION ALL SELECT 'date in range',      count(*) FROM sales WHERE sale_date < DATE '2017-01-01' OR sale_date > CURRENT_DATE
UNION ALL SELECT 'town not null',      count(*) FROM sales WHERE town IS NULL OR town = ''
UNION ALL SELECT 'flat_type not null', count(*) FROM sales WHERE flat_type IS NULL OR flat_type = ''
UNION ALL SELECT 'price/m2 sane',      count(*) FROM sales WHERE price_per_sqm IS NULL OR price_per_sqm <= 0
UNION ALL SELECT 'lease years sane',   count(*) FROM sales WHERE remaining_lease_years IS NULL OR remaining_lease_years < 0 OR remaining_lease_years > 99;
