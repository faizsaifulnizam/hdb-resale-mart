"""Exercise staged corruption through real producer CLIs; no network or GUI."""
import unittest
import duckdb
from tests import test_pipeline as fixtures


class NumericContractTest(unittest.TestCase):
    setUp = fixtures.PipelineTest.setUp
    write_raw = fixtures.PipelineTest.write_raw
    run_cli = fixtures.PipelineTest.run_cli
    assert_success = fixtures.PipelineTest.assert_success
    def test_independent_components_rejected_before_publication(self):
        self.write_raw(fixtures.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        original = self.parquet.read_bytes()
        paths = [self.root / 'outputs' / n for n in ('town_4room_yoy.csv', 'sensitivity.csv')]
        paths += [self.root / folder / (name + suffix + '.png')
                  for folder in ('reports/figures', 'docs/img')
                  for name in ('f1_town_dumbbell', 'f2_rolling_median', 'f3_mix_drift', 'f4_waterfall')
                  for suffix in ('', '-dark')]
        for p in paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(('previous:' + p.name).encode())
        prior = [p.read_bytes() for p in paths]
        for column in ('resale_price', 'floor_area_sqm', 'price_per_sqm'):
            for expression in ("'NaN'::DOUBLE", "'Infinity'::DOUBLE", "'-Infinity'::DOUBLE", column + ' * 1.01'):
                # Include a non-headline flat to prove validation is not window/type scoped.
                for predicate in ("sale_month=DATE '2026-07-01'", "flat_type='3 ROOM'"):
                    with self.subTest(column=column, expression=expression, predicate=predicate):
                        self.parquet.write_bytes(original)
                        with duckdb.connect() as con:
                            con.read_parquet(str(self.parquet)).create_view('original')
                            con.execute(f'CREATE TABLE altered AS SELECT * REPLACE(CASE WHEN {predicate} THEN {expression} ELSE {column} END AS {column}) FROM original')
                            con.sql('SELECT * FROM altered').write_parquet(str(self.parquet))
                        for cli in ('analysis.py', 'figures.py'):
                            result = self.run_cli(cli)
                            self.assertNotEqual(result.returncode, 0, cli + result.stdout + result.stderr)
                            self.assertIn('numeric sales contract', result.stdout + result.stderr)
                            self.assertEqual(prior, [p.read_bytes() for p in paths])


    def test_unrounded_headline_rejected_before_either_csv_is_replaced(self):
        self.write_raw(fixtures.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        sql = self.root / 'sql/04_yoy.sql'
        original = sql.read_text(encoding='utf-8')
        paths = [self.root / 'outputs' / n for n in ('town_4room_yoy.csv', 'sensitivity.csv')]
        for p in paths:
            p.write_bytes(b'prior complete generation')
        # Corrupt the actual SQL producer AFTER its valid input boundary. The
        # finite drift disappears under CSV rounding; gate unrounded values.
        for change in ("mean_t1 = 'NaN'::DOUBLE", 'mean_t1 = mean_t1 + 0.0001'):
            with self.subTest(change=change):
                sql.write_text(original + '\nUPDATE yoy_4room SET ' + change + " WHERE town='CENTRAL AREA';\n", encoding='utf-8')
                result = self.run_cli('analysis.py')
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('headline export', result.stdout + result.stderr)
                self.assertEqual([p.read_bytes() for p in paths], [b'prior complete generation'] * 2)


    def test_direct_decomposition_rejects_primitive_drift(self):
        from src.analysis import decomposition, P0, P1
        self.write_raw(fixtures.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        with duckdb.connect() as con:
            con.read_parquet(str(self.parquet)).create_view('original')
            con.execute('CREATE TABLE sales AS SELECT * REPLACE(resale_price * 1.01 AS resale_price) FROM original')
            with self.assertRaisesRegex(ValueError, 'numeric sales contract'):
                decomposition(con, P0, P1)

    def test_builder_rejects_inconsistent_staging_preserves_parquet(self):
        self.write_raw(fixtures.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        prior = self.parquet.read_bytes()
        sql = self.root / 'sql/01_staging.sql'
        sql.write_text(sql.read_text() + '\nUPDATE sales SET price_per_sqm = price_per_sqm + 1;\n')
        result = self.run_cli('build_dataset.py')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('numeric sales contract', result.stdout + result.stderr)
        self.assertEqual(prior, self.parquet.read_bytes())

    def test_raw_audit_rejects_nonfinite_input(self):
        for column in ('resale_price', 'floor_area_sqm'):
            with self.subTest(column=column):
                self.write_raw(fixtures.fixture_rows() + [fixtures.sale(**{column: 'NaN'})])
                result = self.run_cli('audit.py')
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_figures_reject_unrounded_headline_drift(self):
        self.write_raw(fixtures.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        paths = [self.root / folder / (name + suffix + '.png')
                 for folder in ('reports/figures', 'docs/img')
                 for name in ('f1_town_dumbbell', 'f2_rolling_median', 'f3_mix_drift', 'f4_waterfall')
                 for suffix in ('', '-dark')]
        for p in paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'previous figures')
        sql = self.root / 'sql/04_yoy.sql'
        sql.write_text(sql.read_text() + "\nUPDATE yoy_4room SET mean_t1 = mean_t1 + 0.0001 WHERE town='CENTRAL AREA';\n")
        result = self.run_cli('figures.py')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('headline export', result.stdout + result.stderr)
        self.assertEqual([p.read_bytes() for p in paths], [b'previous figures'] * len(paths))


if __name__ == '__main__':
    unittest.main()
