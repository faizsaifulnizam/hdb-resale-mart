"""Build the processed dataset: raw CSV -> staging (sql/01) -> checks (sql/05) -> parquet.

Run: python src/build_dataset.py
Receipts printed: in/out counts, exclusion breakdown, check results. Exit 1 if any check fails.

Order matters: every check runs BEFORE the parquet is produced, and the file is written
to a temp path then atomically replaced — a failing run never touches the existing output.
"""
import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
STAGING = ROOT / "sql/01_staging.sql"
CHECKS = ROOT / "sql/05_checks.sql"
OUT_DIR = ROOT / "data/processed"
RAW = (ROOT / "data/raw/hdb-resale-prices-2017-onwards.csv").as_posix()

# Exclusion rules — must mirror the WHERE clause in sql/01. A row is excluded if ANY rule matches.
RULES = [
    ("price null or <= 0", "resale_price IS NULL OR resale_price <= 0"),
    ("area null or <= 0", "floor_area_sqm IS NULL OR floor_area_sqm <= 0"),
    ("bad month", "try_strptime(month, '%Y-%m') IS NULL"),
    ("no lease text", "remaining_lease IS NULL"),
]
ANY_RULE = "NOT (" + " AND ".join(f"NOT ({expr})" for _, expr in RULES) + ")"


def q(con, sql):
    return con.sql(sql).fetchall()


def main():
    os.chdir(ROOT)  # sql/01 references data/raw relatively
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    from download import inspect_csv
    inspect_csv(RAW, ROOT / 'data/raw/pull_manifest.json')
    con.read_csv(RAW).create_view('raw_rows')
    raw_n = q(con, 'SELECT count(*) FROM raw_rows')[0][0]
    invalid = q(con, "SELECT count(*) FROM raw_rows WHERE "
                "NOT isfinite(resale_price) OR NOT isfinite(floor_area_sqm) "
                "OR (floor_area_sqm > 0 AND NOT isfinite(resale_price / floor_area_sqm))")[0][0]
    if invalid:
        print('checks failed — nonfinite input; parquet NOT written (existing file left untouched)')
        sys.exit(1)
    con.execute(STAGING.read_text(encoding="utf-8"))
    from analysis import validate_sales
    try:
        validate_sales(con)
    except ValueError as exc:
        print(f'checks failed — {exc}; parquet NOT written (existing file left untouched)')
        sys.exit(1)
    out_n = q(con, "SELECT count(*) FROM sales")[0][0]
    excl_any = q(con, f"SELECT count(*) FROM raw_rows WHERE {ANY_RULE}")[0][0]
    print(f"raw rows:    {raw_n}")
    print(f"staged rows: {out_n}")
    print(f"excluded:    {raw_n - out_n}  ({100 * (raw_n - out_n) / raw_n:.3f}%)")
    print("exclusion rules (per-rule counts; a row may match more than one):")
    for rule, expr in RULES:
        k = q(con, f"SELECT count(*) FROM raw_rows WHERE {expr}")[0][0]
        print(f"    rule [{rule}]: {k}")
    ok_recon = (out_n + excl_any) == raw_n
    print(f"    [{'PASS' if ok_recon else 'FAIL'}] retained + excluded == raw ({out_n} + {excl_any} vs {raw_n})")

    print("checks:")
    failed = not ok_recon
    for name, v in con.execute(CHECKS.read_text(encoding="utf-8")).fetchall():
        status = "PASS" if v == 0 else "FAIL"
        print(f"    [{status}] {name}  (violations: {v})")
        if v:
            failed = True

    if failed:
        print("checks failed — parquet NOT written (existing file left untouched)")
        sys.exit(1)

    pq = OUT_DIR / "sales.parquet"
    tmp = OUT_DIR / "sales.parquet.tmp"
    con.sql('SELECT * FROM sales').write_parquet(tmp.as_posix())
    os.replace(tmp, pq)
    print(f"wrote: {pq.as_posix()}  ({pq.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
