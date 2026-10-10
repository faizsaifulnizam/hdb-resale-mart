import unittest
from pathlib import Path
import duckdb
from src.analysis import run_script

class TieChecks(unittest.TestCase):
    def test_finite_inputs_with_overflowing_aggregate_rejected(self):
        from src.analysis import decomposition
        with duckdb.connect() as con:
            con.execute('CREATE TABLE sales(town VARCHAR, flat_type VARCHAR, sale_date DATE, sale_month DATE, price_per_sqm DOUBLE, resale_price DOUBLE, floor_area_sqm DOUBLE)')
            con.execute("INSERT INTO sales SELECT 'A','4 ROOM', DATE '2025-07-01', DATE '2025-07-01', 1e308, 1e308, 1.0 FROM range(4)")
            con.execute("INSERT INTO sales SELECT 'A','4 ROOM', DATE '2026-07-01', DATE '2026-07-01', 1e308, 1e308, 1.0 FROM range(4)")
            with self.assertRaisesRegex(ValueError, 'nonfinite decomposition'):
                decomposition(con, ('2025-07-01','2025-07-31'), ('2026-07-01','2026-07-31'))

    def test_percentage_overflow_rejected(self):
        from src.analysis import decomposition
        with duckdb.connect() as con:
            con.execute('CREATE TABLE sales(town VARCHAR, flat_type VARCHAR, sale_date DATE, sale_month DATE, price_per_sqm DOUBLE, resale_price DOUBLE, floor_area_sqm DOUBLE)')
            con.execute("INSERT INTO sales VALUES ('A','4 ROOM',DATE '2025-07-01',DATE '2025-07-01',1e-300,1e-300,1.0), ('A','4 ROOM',DATE '2026-07-01',DATE '2026-07-01',1e300,1e300,1.0)")
            with self.assertRaisesRegex(ValueError, 'nonfinite percentage change'):
                decomposition(con, ('2025-07-01','2025-07-31'), ('2026-07-01','2026-07-31'))

    def test_all_comparison_months_required(self):
        from src.analysis import decomposition
        with duckdb.connect() as con:
            con.execute("CREATE TABLE complete AS SELECT 'A' AS town, '4 ROOM' AS flat_type, m::DATE AS sale_date, m::DATE AS sale_month, 5000.0 AS price_per_sqm FROM generate_series(DATE '2024-10-01',DATE '2026-09-01',INTERVAL 1 MONTH) AS t(m)")
            months = [r[0] for r in con.sql('SELECT sale_month FROM complete').fetchall()]
            for month in months:
                with self.subTest(month=month):
                    con.execute('CREATE OR REPLACE TABLE sales AS SELECT * FROM complete WHERE sale_month != ?', [month])
                    with self.assertRaisesRegex(ValueError, 'incomplete national calendar'):
                        decomposition(con, ('2024-10-01','2025-09-30'), ('2025-10-01','2026-09-30'))

    def test_export_tied_volume_orders_by_town(self):
        with duckdb.connect() as con:
            con.execute('CREATE TABLE yoy_4room(town VARCHAR,n_t0 INT,n_t1 INT,med_t0 DOUBLE,med_t1 DOUBLE,mean_t0 DOUBLE,mean_t1 DOUBLE,w_t0 DOUBLE,w_t1 DOUBLE)')
            con.execute("INSERT INTO yoy_4room VALUES ('Z',30,30,5000,5100,5000,5100,.5,.5),('A',30,30,5000,5100,5000,5100,.5,.5)")
            run_script(con, Path(__file__).resolve().parents[1] / 'sql/04_export.sql')
            self.assertEqual(con.sql('SELECT town FROM town_4room_export').fetchall(), [('A',),('Z',)])
