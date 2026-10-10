"""Real producer CLI regressions; isolated files, generated data, no network.

Run: python -m unittest discover -s tests -p 'test_pipeline.py' -v
"""
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import statistics as st

import duckdb

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("month,town,flat_type,block,street_name,storey_range,floor_area_sqm,"
          "flat_model,lease_commence_date,remaining_lease,resale_price").split(",")


def sale(**changes):
    row = dict(zip(FIELDS, ["2025-07", "SENGKANG", "4 ROOM", "101", "TEST ROAD",
                           "04 TO 06", "100", "Model A", "2000", "73 years 02 months", "500000"]))
    row.update(changes)
    return row


def fixture_rows():
    """Two years, changing town shares/rates, skewed prices and a small town."""
    rows = []
    for year in (2024, 2025, 2026):
        for month in range(1, 13):
            if not "2024-10" <= f"{year}-{month:02}" <= "2026-09":
                continue
            for i, town in enumerate(("SENGKANG", "TAMPINES", "PUNGGOL", "CENTRAL AREA")):
                n = 1 if i == 3 else 10 + 2 * i + (year == 2026) * (i + 1)
                for k in range(n):
                    area = 80 + 10 * (k % 3)
                    ppsm = 4000 + i * 1500 + month * 20 + (year - 2024) * (200 - i * 100) + k * k * 10
                    rows.append(sale(month=f"{year}-{month:02}", town=town, block=str(100 + k),
                                     floor_area_sqm=str(area), resale_price=str(area * ppsm)))
    # Non-headline flats must not enter the national 4-room calculation.
    rows.extend(sale(month=f"{year}-09", flat_type="3 ROOM", resale_price="9999999")
                for year in (2025, 2026))
    return rows


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hdb-pipeline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("src", "sql", "assets"):
            shutil.copytree(ROOT / directory, self.root / directory,
                            ignore=shutil.ignore_patterns("__pycache__"))
        for directory in ("data/raw", "data/processed", "outputs"):
            (self.root / directory).mkdir(parents=True)
        self.raw = self.root / "data/raw/hdb-resale-prices-2017-onwards.csv"
        self.parquet = self.root / "data/processed/sales.parquet"

    def write_raw(self, rows):
        with self.raw.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def run_cli(self, name):
        return subprocess.run([sys.executable, str(self.root / "src" / name)],
                              cwd=self.root.parent, capture_output=True, text=True,
                              encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                              timeout=60)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def seed_outputs(self):
        for name in ("town_4room_yoy.csv", "sensitivity.csv"):
            (self.root / "outputs" / name).write_bytes(b"old CSV sentinel\n")

    def assert_validation_failure(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation failed — output files NOT written", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        for name in ("town_4room_yoy.csv", "sensitivity.csv"):
            self.assertEqual((self.root / "outputs" / name).read_bytes(), b"old CSV sentinel\n")

    def test_missing_headline_window_fails_cleanly(self):
        fixtures = [[sale(month="2017-01")]]
        for missing_year in ("2025", "2026"):
            fixtures.append([r for r in fixture_rows()
                             if not (r["month"].startswith(missing_year) and r["month"][5:] in ("07", "08", "09"))])
        for rows in fixtures:
            with self.subTest(rows=len(rows)):
                self.write_raw(rows)
                self.assert_success(self.run_cli("build_dataset.py"))
                self.seed_outputs()
                self.assert_validation_failure(self.run_cli("analysis.py"))

    def test_disjoint_headline_towns_fail_cleanly(self):
        rows = fixture_rows()
        for r in rows:
            if r["month"] in ("2025-07", "2025-08", "2025-09"):
                r["town"] = "OLD " + r["town"]
        self.write_raw(rows)
        self.assert_success(self.run_cli("build_dataset.py"))
        self.seed_outputs()
        self.assert_validation_failure(self.run_cli("analysis.py"))

    def test_missing_threshold_comparison_preserves_both_csvs(self):
        self.write_raw([r for r in fixture_rows() if r["block"] == "100" or r["flat_type"] != "4 ROOM"])
        self.assert_success(self.run_cli("build_dataset.py"))
        self.seed_outputs()
        result = self.run_cli("analysis.py")
        self.assertIn("[PASS] headline coverage: 4/4", result.stdout)
        for town in ("SENGKANG", "TAMPINES", "PUNGGOL"):
            self.assertIn(f"[PASS] {town}", result.stdout)
        self.assert_validation_failure(result)

    def test_generated_pipeline_matches_independent_raw_statistics(self):
        rows = fixture_rows()
        # One calendar gap exercises RANGE rather than a three-row rolling window.
        rows = [r for r in rows if (r["town"], r["month"]) != ("PUNGGOL", "2025-02")]
        rejected = [sale(resale_price="0"), sale(floor_area_sqm="0"), sale(month="2026-13"),
                    sale(remaining_lease=""), sale(resale_price="0", floor_area_sqm="0")]
        self.write_raw(rows + rejected)
        staged = self.run_cli("build_dataset.py")
        self.assert_success(staged)
        self.assertIn(f"staged rows: {len(rows)}", staged.stdout)
        self.assertIn("excluded:    5", staged.stdout)
        analyzed = self.run_cli("analysis.py")
        self.assert_success(analyzed)
        self.assertIn("RESULT: ALL CHECKS PASS", analyzed.stdout)

        def values(a, b):
            groups = {}
            for r in rows:
                if r["flat_type"] == "4 ROOM" and a <= r["month"] <= b:
                    groups.setdefault(r["town"], []).append(float(r["resale_price"]) / float(r["floor_area_sqm"]))
            return groups

        def load_csv(name):
            with (self.root / "outputs" / name).open(encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))

        before, after = values("2025-07", "2025-09"), values("2026-07", "2026-09")
        table = load_csv("town_4room_yoy.csv")
        self.assertEqual({r["town"] for r in table}, set(before) | set(after))
        for r in table:
            town = r["town"]
            x, y = before[town], after[town]
            w0, w1 = len(x) / sum(map(len, before.values())), len(y) / sum(map(len, after.values()))
            p0, p1 = st.mean(x), st.mean(y)
            expected = {
                "med_ppsm_2025q3": (st.median(x), 2), "med_ppsm_2026q3": (st.median(y), 2),
                "med_pct_change": (100 * (st.median(y) / st.median(x) - 1), 2),
                "mean_ppsm_2025q3": (p0, 2), "mean_ppsm_2026q3": (p1, 2),
                "share_2025q3": (w0, 4), "share_2026q3": (w1, 4),
                "rate_effect": (w0 * (p1 - p0), 2), "mix_effect": ((w1 - w0) * p0, 2),
                "interaction": ((w1 - w0) * (p1 - p0), 2),
            }
            self.assertEqual((int(r["n_t0"]), int(r["n_t1"])), (len(x), len(y)))
            for column, (value, digits) in expected.items():
                with self.subTest(town=town, column=column):
                    self.assertAlmostEqual(float(r[column]), round(value, digits), places=digits)
        med0 = st.median([v for group in before.values() for v in group])
        med1 = st.median([v for group in after.values() for v in group])
        self.assertIn(f"national 4-room median price/m2: {med0:.0f} -> {med1:.0f} "
                      f"({100 * (med1 / med0 - 1):+.2f}%)", analyzed.stdout)

        sensitivity = load_csv("sensitivity.csv")
        windows = [("q3", "2025-07", "2025-09", "2026-07", "2026-09"),
                   ("6m", "2025-04", "2025-09", "2026-04", "2026-09"),
                   ("12m", "2024-10", "2025-09", "2025-10", "2026-09")]
        self.assertEqual(len(sensitivity), 6)
        for index, (_, a, b, c, d) in enumerate(windows):
            for threshold in (0, 25):
                x, y = values(a, b), values(c, d)
                towns = {t for t in x.keys() & y.keys() if len(x[t]) >= threshold and len(y[t]) >= threshold}
                pooled0 = [v for t in towns for v in x[t]]
                pooled1 = [v for t in towns for v in y[t]]
                rate = mix = inter = 0.0
                for t in towns:
                    p0, p1 = st.mean(x[t]), st.mean(y[t])
                    w0, w1 = len(x[t]) / len(pooled0), len(y[t]) / len(pooled1)
                    rate += w0 * (p1 - p0)
                    mix += (w1 - w0) * p0
                    inter += (w1 - w0) * (p1 - p0)
                total = st.mean(pooled1) - st.mean(pooled0)
                self.assertAlmostEqual(rate + mix + inter, total, places=8)
                r = sensitivity[index * 2 + (threshold > 0)]
                self.assertEqual(int(r["towns"]), len(towns))
                self.assertEqual(int(r["towns_dropped"]), len(x.keys() | y.keys()) - len(towns))
                for column, expected in (("level_t0", st.mean(pooled0)), ("total_delta", total),
                                         ("rate", rate), ("mix", mix), ("interaction", inter)):
                    self.assertAlmostEqual(float(r[column]), round(expected, 2), places=2)
                self.assertAlmostEqual(float(r["total_pct"]), round(100 * total / st.mean(pooled0), 3), places=3)
                self.assertAlmostEqual(sum(float(r[k]) for k in ("rate", "mix", "interaction")),
                                       float(r["total_delta"]), delta=0.021)

        # Read the real processed output, run the same metrics producer as analysis/figures,
        # and independently recompute the calendar-aware median-of-monthly-medians.
        from src.analysis import run_script
        with duckdb.connect() as con:
            con.read_parquet(self.parquet.as_posix()).create_view("sales")
            self.assertEqual(con.sql("SELECT count(*) FROM sales").fetchone()[0], len(rows))
            run_script(con, self.root / "sql/03_metrics.sql")
            for town, month in (("SENGKANG", "2026-09"), ("TAMPINES", "2024-12"), ("PUNGGOL", "2025-03")):
                months = [f"{month[:4]}-{m:02}" for m in range(int(month[5:]) - 2, int(month[5:]) + 1)]
                monthly = [values(m, m).get(town, []) for m in months]
                actual = con.execute("SELECT med_ppsm, r3_med_ppsm, n, n_3m FROM town_month_metrics "
                                     "WHERE town = ? AND flat_type = '4 ROOM' AND sale_month = CAST(? AS DATE)", [town, month + "-01"]).fetchone()
                self.assertAlmostEqual(actual[0], st.median(monthly[-1]))
                self.assertAlmostEqual(actual[1], st.median([st.median(v) for v in monthly if v]))
                self.assertEqual((actual[2], actual[3]), (len(monthly[-1]), sum(map(len, monthly))))

    def test_csvs_use_lf_and_repeat_identically(self):
        self.write_raw(fixture_rows())
        self.assert_success(self.run_cli("build_dataset.py"))
        self.assert_success(self.run_cli("analysis.py"))
        paths = [self.root / "outputs" / name for name in ("town_4room_yoy.csv", "sensitivity.csv")]
        first = [p.read_bytes() for p in paths]
        for path, data in zip(paths, first):
            with self.subTest(path=path.name):
                self.assertNotIn(b"\r", data)
                self.assertTrue(data.endswith(b"\n"))
        self.assert_success(self.run_cli("analysis.py"))
        self.assertEqual(first, [p.read_bytes() for p in paths])

    def test_every_window_rejects_missing_national_month(self):
        for month in ('2025-04', '2026-08', '2024-10'):
            with self.subTest(month=month):
                self.write_raw([r for r in fixture_rows() if r['month'] != month])
                self.assert_success(self.run_cli('build_dataset.py'))
                self.seed_outputs()
                self.assert_validation_failure(self.run_cli('analysis.py'))

    def test_direct_parquet_nonfinite_sensitivity_preserves_outputs(self):
        for month in ('2025-04-01', '2025-07-01', '2026-07-01'):
            with self.subTest(month=month):
                self.write_raw(fixture_rows())
                self.assert_success(self.run_cli('build_dataset.py'))
                with duckdb.connect() as con:
                    con.read_parquet(str(self.parquet)).create_view('original')
                    con.execute("CREATE TABLE altered AS SELECT * REPLACE (CASE WHEN sale_month = CAST(? AS DATE) THEN 'NaN'::DOUBLE ELSE price_per_sqm END AS price_per_sqm) FROM original", [month])
                    con.sql('SELECT * FROM altered').write_parquet(str(self.parquet))
                self.seed_outputs()
                self.assert_validation_failure(self.run_cli('analysis.py'))

    def test_raw_nonfinite_preserves_parquet(self):
        for column in ('resale_price', 'floor_area_sqm'):
            for value in ('NaN', 'Infinity', '-Infinity'):
                with self.subTest(column=column, value=value):
                    self.write_raw(fixture_rows() + [sale(**{column: value})])
                    self.parquet.write_bytes(b'previous generation')
                    result = self.run_cli('build_dataset.py')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.parquet.read_bytes(), b'previous generation')

    def test_duplicate_header_preserves_parquet(self):
        self.raw.write_text(','.join(FIELDS + ['resale_price']) + '\n' + ','.join(sale().values()) + ',500000\n')
        self.parquet.write_bytes(b'previous generation')
        result = self.run_cli('build_dataset.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.parquet.read_bytes(), b'previous generation')

    def test_apostrophe_checkout_all_dataset_consumers(self):
        renamed = self.root.with_name(self.root.name + "-O'Brien-é")
        self.root.rename(renamed)
        self.addCleanup(shutil.rmtree, renamed)
        self.root = renamed
        self.raw = self.root / 'data/raw/hdb-resale-prices-2017-onwards.csv'
        self.parquet = self.root / 'data/processed/sales.parquet'
        self.write_raw(fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        self.assert_success(self.run_cli('analysis.py'))
        self.assert_success(self.run_cli('audit.py'))
        self.assert_success(self.run_cli('figures.py'))

    def test_figures_do_not_publish_analysis_csvs(self):
        self.write_raw(fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        self.seed_outputs()
        result = self.run_cli('figures.py')
        self.assert_success(result)
        for name in ('town_4room_yoy.csv', 'sensitivity.csv'):
            self.assertEqual((self.root / 'outputs' / name).read_bytes(), b'old CSV sentinel\n')

    def test_sensitivity_requires_full_town_coverage_without_threshold(self):
        rows = fixture_rows()
        for row in rows:
            if row['month'] == '2025-04': row['town'] = 'ONLY PRIOR'
        self.write_raw(rows)
        self.assert_success(self.run_cli('build_dataset.py'))
        self.seed_outputs()
        self.assert_validation_failure(self.run_cli('analysis.py'))

    def test_builder_rejects_stale_manifest(self):
        import json
        self.write_raw(fixture_rows())
        (self.raw.parent / 'pull_manifest.json').write_text(json.dumps({'sha256':'0'*64}))
        self.parquet.write_bytes(b'previous generation')
        self.assertNotEqual(self.run_cli('build_dataset.py').returncode, 0)
        self.assertEqual(self.parquet.read_bytes(), b'previous generation')

    def test_empty_staging_preserves_parquet(self):
        for changes in ({"resale_price": "0"}, {"floor_area_sqm": "0"},
                        {"month": "2026-13"}, {"remaining_lease": ""}):
            with self.subTest(changes=changes):
                self.write_raw([sale(**changes)])
                self.parquet.write_bytes(b"old parquet sentinel")
                result = self.run_cli("build_dataset.py")
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("checks failed", result.stdout)
                self.assertIn("staged rows: 0", result.stdout)
                self.assertEqual(self.parquet.read_bytes(), b"old parquet sentinel")
                self.assertFalse(self.parquet.with_suffix(".parquet.tmp").exists())

    def test_audit_counts_identical_extra_copies(self):
        a, b, c = sale(), sale(block="102"), sale(block="103", street_name="")
        for rows, expected in [([a, b, c], 0), ([a, a, a, b, c, c], 3), ([a], 0)]:
            with self.subTest(expected=expected, rows=len(rows)):
                self.write_raw(rows)
                result = self.run_cli("audit.py")
                self.assert_success(result)
                self.assertIn(f"duplicate rows (extra copies): {expected}\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
