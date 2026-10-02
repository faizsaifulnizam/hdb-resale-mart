"""Build the processed dataset: raw CSV -> staging (sql/01) -> checks (sql/05) -> parquet.

Run: python src/build_dataset.py
Receipts printed: in/out counts, exclusion breakdown, check results. Exit 1 if any check fails.
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


def q(con, sql):
    return con.sql(sql).fetchall()


def main():
    os.chdir(ROOT)  # sql/01 references data/raw relatively
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    raw_n = q(con, f"SELECT count(*) FROM read_csv_auto('{RAW}')")[0][0]
    con.execute(STAGING.read_text(encoding="utf-8"))
    out_n = q(con, "SELECT count(*) FROM sales")[0][0]
    print(f"raw rows:    {raw_n}")
    print(f"staged rows: {out_n}")
    print(f"excluded:    {raw_n - out_n}  ({100 * (raw_n - out_n) / raw_n:.3f}%)")

    for rule, expr in [
        ("price <= 0", "resale_price <= 0"),
        ("area <= 0", "floor_area_sqm <= 0"),
        ("bad month", "NOT regexp_matches(month, '^[0-9]{4}-[0-9]{2}$')"),
        ("no lease text", "remaining_lease IS NULL"),
    ]:
        k = q(con, f"SELECT count(*) FROM read_csv_auto('{RAW}') WHERE {expr}")[0][0]
        print(f"    rule [{rule}]: {k}")

    pq = OUT_DIR / "sales.parquet"
    con.sql(f"COPY sales TO '{pq.as_posix()}' (FORMAT PARQUET)")
    print(f"wrote: {pq.as_posix()}  ({pq.stat().st_size} bytes)")

    print("checks:")
    failed = False
    for name, v in con.execute(CHECKS.read_text(encoding="utf-8")).fetchall():
        status = "PASS" if v == 0 else "FAIL"
        print(f"    [{status}] {name}  (violations: {v})")
        if v:
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
