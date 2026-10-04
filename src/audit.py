"""Data audit — profiles the raw HDB resale CSV (read-only).

Run: python src/audit.py
Numbers from this run feed docs/data_audit.md.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = (ROOT / "data/raw/hdb-resale-prices-2017-onwards.csv").as_posix()


def q(con, sql):
    return con.sql(sql).fetchall()


def main():
    con = duckdb.connect()
    con.execute(f"CREATE OR REPLACE VIEW raw AS SELECT * FROM read_csv_auto('{RAW}')")

    print("rows:", q(con, "SELECT count(*) FROM raw")[0][0])
    cols = [r[0] for r in q(con, "DESCRIBE raw")]
    print("cols:", len(cols), cols)

    print()
    print("nulls per column (only columns with nulls):")
    for c in cols:
        k = q(con, f'SELECT count(*) FROM raw WHERE "{c}" IS NULL')[0][0]
        if k:
            print(" ", c, k)

    print()
    print("month range:", q(con, "SELECT min(month), max(month) FROM raw")[0])

    print()
    print("towns:", q(con, "SELECT count(DISTINCT town) FROM raw")[0][0])
    for name, cnt in q(con, "SELECT town, count(*) FROM raw GROUP BY 1 ORDER BY 2"):
        print(f"  {name}: {cnt}")

    print()
    print("flat types:")
    for name, cnt in q(con, "SELECT flat_type, count(*) FROM raw GROUP BY 1 ORDER BY 2"):
        print(f"  {name}: {cnt}")

    print()
    print("price range:", q(con, "SELECT min(resale_price), max(resale_price) FROM raw")[0])
    print("area range:", q(con, "SELECT min(floor_area_sqm), max(floor_area_sqm) FROM raw")[0])
    print("price/sqm percentiles [0.1, 1, 50, 99, 99.9]:",
          q(con, "SELECT quantile_cont(resale_price / nullif(floor_area_sqm, 0), [0.001, 0.01, 0.5, 0.99, 0.999]) FROM raw")[0])

    print()
    print("storey_range OK / total:",
          q(con, "SELECT sum(CASE WHEN regexp_matches(storey_range, '^[0-9]+ TO [0-9]+$') THEN 1 ELSE 0 END), count(*) FROM raw")[0])
    print("remaining_lease OK / total:",
          q(con, "SELECT sum(CASE WHEN regexp_matches(remaining_lease, '^[0-9]+ years?( [0-9]+ months?)?$') THEN 1 ELSE 0 END), count(*) FROM raw")[0])
    print("lease text samples:", q(con, "SELECT DISTINCT remaining_lease FROM raw LIMIT 8")[:8])

    print()
    d = q(con, "SELECT sum(c - 1) FROM (SELECT *, count(*) AS c FROM raw GROUP BY ALL) WHERE c > 1")[0][0]
    print("duplicate rows (extra copies):", d or 0)

    print()
    print("structural checks:")
    for name, expr in [
        ("price <= 0", "resale_price <= 0"),
        ("area <= 0", "floor_area_sqm <= 0"),
        ("unparseable month", "NOT regexp_matches(month, '^[0-9]{4}-[0-9]{2}$')"),
    ]:
        k = q(con, f"SELECT count(*) FROM raw WHERE {expr}")[0][0]
        print(f"  {name}: {k}")

    print()
    print("town transaction counts since 2023-01 (threshold check):")
    rows = q(con, "SELECT town, count(*) FROM raw WHERE month >= '2023-01' GROUP BY 1 ORDER BY 2")
    for name, cnt in rows:
        print(f"  {name}: {cnt}")
    print("towns < 20 txns:", sum(1 for _, c in rows if c < 20),
          "| towns < 50 txns:", sum(1 for _, c in rows if c < 50))

    print()
    print("4-room rows total:", q(con, "SELECT count(*) FROM raw WHERE flat_type = '4 ROOM'")[0][0],
          "| since 2023-01:", q(con, "SELECT count(*) FROM raw WHERE flat_type = '4 ROOM' AND month >= '2023-01'")[0][0])


if __name__ == "__main__":
    main()
