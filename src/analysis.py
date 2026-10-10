"""S2 analysis runner — dims -> metrics -> 4-room YoY + shift-share decomposition -> sensitivity.

Run: python src/analysis.py   (from the repo root; reads data/processed/sales.parquet)
Receipts printed:
  1. dims + metrics row counts
  2. hand-checks: 3 town-month medians/rolling medians recomputed independently (stdlib statistics)
  3. decomposition assert: rate + mix + interaction == total (epsilon 1e-9) + headline coverage
  4. sensitivity table (window + threshold variants) -> outputs/sensitivity.csv
Validation runs BEFORE any output file is written; a failing run leaves existing outputs untouched.
Writes: outputs/town_4room_yoy.csv (via sql/04) · outputs/sensitivity.csv
"""
import csv
import os
import statistics as st
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
PARQUET = (ROOT / "data/processed/sales.parquet").as_posix()
OUT = ROOT / "outputs"

# Headline periods (keep in sync with sql/04_yoy.sql).
P0 = ("2025-07-01", "2025-09-30")  # t0: Q3 2025
P1 = ("2026-07-01", "2026-09-30")  # t1: Q3 2026

HAND_CHECKS = [
    ("SENGKANG", "4 ROOM", "2026-09-01"),
    ("TAMPINES", "4 ROOM", "2024-12-01"),
    ("PUNGGOL", "4 ROOM", "2025-03-01"),
]


def q(con, sql):
    return con.sql(sql).fetchall()


def validate_sales(con):
    """Every staged row must retain staging's finite, positive DOUBLE quotient.

    Exact equality is intentional: staging stores the quotient verbatim, not a
    rounded estimate. No component is silently repaired or ignored.
    """
    invalid = con.execute("""SELECT count(*) FROM sales WHERE
        resale_price IS NULL OR NOT isfinite(resale_price) OR resale_price <= 0
        OR floor_area_sqm IS NULL OR NOT isfinite(floor_area_sqm) OR floor_area_sqm <= 0
        OR price_per_sqm IS NULL OR NOT isfinite(price_per_sqm) OR price_per_sqm <= 0
        OR NOT isfinite(resale_price / floor_area_sqm)
        OR price_per_sqm != resale_price / floor_area_sqm""").fetchone()[0]
    if invalid:
        raise ValueError(f'numeric sales contract: {invalid} nonfinite, invalid or inconsistent rows')


def run_script(con, path):
    if Path(path).name in ('02_dims.sql', '03_metrics.sql', '04_yoy.sql'):
        validate_sales(con)
    # Strip comment tails per line first, then split statements on ';'
    # (safe here: no '--' inside string literals in this repo's SQL).
    text = "\n".join(l.split("--", 1)[0] for l in Path(path).read_text(encoding="utf-8").splitlines())
    for stmt in text.split(";"):
        if stmt.strip():
            con.execute(stmt)


def prev_months(month, k):
    """['yyyy-mm-01', ...] — the k months ending at `month` (inclusive), ascending."""
    y, m = int(month[:4]), int(month[5:7])
    out = []
    for d in range(k - 1, -1, -1):
        mm, yy = m - d, y
        while mm <= 0:
            mm += 12
            yy -= 1
        out.append(f"{yy:04d}-{mm:02d}-01")
    return out


def decomposition(con, p0, p1, min_n=0):
    """National shift-share totals for two periods (4-room, by town).

    Towns must have transactions in BOTH periods (min_n filters small towns on top).
    Returns coverage counts; raises on an empty comparison instead of reporting zeros.
    """
    for period in (p0, p1):
        months = prev_months(period[1][:7] + '-01',
                             (int(period[1][:4]) - int(period[0][:4])) * 12
                             + int(period[1][5:7]) - int(period[0][5:7]) + 1)
        observed = {str(r[0])[:10] for r in con.execute(
            "SELECT DISTINCT sale_month FROM sales WHERE flat_type = '4 ROOM' "
            "AND sale_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)", period).fetchall()}
        if set(months) != observed:
            raise ValueError(f'incomplete national calendar: {period}; missing {sorted(set(months) - observed)}')
        invalid = con.execute(
            "SELECT count(*) FROM sales WHERE flat_type = '4 ROOM' "
            "AND sale_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE) "
            "AND (price_per_sqm IS NULL OR NOT isfinite(price_per_sqm) OR price_per_sqm <= 0)", period).fetchone()[0]
        if invalid:
            raise ValueError(f'nonfinite or invalid price_per_sqm: {period}')
    validate_sales(con)
    sql = f"""
    WITH base AS (
        SELECT town,
               CASE WHEN sale_date BETWEEN DATE '{p1[0]}' AND DATE '{p1[1]}' THEN 1
                    WHEN sale_date BETWEEN DATE '{p0[0]}' AND DATE '{p0[1]}' THEN 0 END AS period,
               price_per_sqm AS ppsm
        FROM sales
        WHERE flat_type = '4 ROOM'
          AND sale_date BETWEEN DATE '{p0[0]}' AND DATE '{p1[1]}'
    ),
    agg AS (
        SELECT town, period, count(*) AS n, avg(ppsm) AS mean_ppsm
        FROM base WHERE period IS NOT NULL GROUP BY town, period
    ),
    piv AS (
        SELECT town,
               max(CASE WHEN period = 0 THEN n END) AS n_t0,
               max(CASE WHEN period = 1 THEN n END) AS n_t1,
               max(CASE WHEN period = 0 THEN mean_ppsm END) AS p_t0,
               max(CASE WHEN period = 1 THEN mean_ppsm END) AS p_t1
        FROM agg GROUP BY town
    ),
    w AS (
        SELECT *,
               n_t0 / sum(n_t0) OVER () AS w_t0,
               n_t1 / sum(n_t1) OVER () AS w_t1
        FROM piv
        WHERE n_t0 >= {min_n} AND n_t1 >= {min_n}
    )
    SELECT sum(w_t0 * p_t0)                    AS level_t0,
           sum(w_t1 * p_t1) - sum(w_t0 * p_t0) AS total,
           sum(w_t0 * (p_t1 - p_t0))           AS rate,
           sum((w_t1 - w_t0) * p_t0)           AS mix,
           sum((w_t1 - w_t0) * (p_t1 - p_t0))  AS inter,
           count(*)                            AS towns,
           (SELECT count(*) FROM piv)          AS towns_total
    FROM w
    """
    row = q(con, sql)[0]
    towns, towns_total = int(row[5]), int(row[6])
    if towns == 0:
        raise ValueError(
            f"no towns with transactions in both periods ({p0[0]}..{p0[1]} vs {p1[0]}..{p1[1]}) — "
            "refusing to report a national comparison")
    if min_n == 0 and towns != towns_total:
        raise ValueError('incomplete town coverage; not a national comparison')
    import math
    vals = [float(v) if v is not None else math.nan for v in row[:5]]
    if not all(math.isfinite(v) for v in vals) or vals[0] <= 0:
        raise ValueError('nonfinite decomposition or invalid baseline')
    if not math.isfinite(100 * (vals[1] / vals[0])):
        raise ValueError('nonfinite percentage change')
    if abs(sum(vals[2:]) - vals[1]) > 1e-9 * max(1.0, abs(vals[1])):
        raise ValueError('decomposition identity failed')
    return dict(zip(["level_t0", "total", "rate", "mix", "inter"], vals)) | {
        "towns": towns, "towns_total": towns_total, "towns_dropped": towns_total - towns}


def validate_headline_export(con, d):
    """Gate the actual unrounded export against the independent decomposition."""
    import math
    rows = q(con, 'SELECT * FROM town_4room_unrounded')
    if len(rows) != d['towns'] or not rows:
        raise ValueError('headline export: incomplete town coverage')
    for row in rows:
        if any(v is None or not math.isfinite(v) for v in row[1:]):
            raise ValueError('headline export: nonfinite numeric value')
        if any(row[i] <= 0 for i in (1, 2, 3, 4, 6, 7, 8, 9)):
            raise ValueError('headline export: invalid count, price or share')
    level0 = math.fsum(r[8] * r[6] for r in rows)
    level1 = math.fsum(r[9] * r[7] for r in rows)
    actual = {'level_t0': level0, 'total': level1 - level0,
              'rate': math.fsum(r[10] for r in rows),
              'mix': math.fsum(r[11] for r in rows),
              'inter': math.fsum(r[12] for r in rows)}
    if any(not math.isclose(actual[k], d[k], rel_tol=1e-9, abs_tol=1e-9) for k in actual):
        raise ValueError('headline export: unrounded decomposition mismatch')
    if any(not math.isclose(math.fsum(r[i] for r in rows), 1.0, abs_tol=1e-9)
           for i in (8, 9)):
        raise ValueError('headline export: invalid national shares')


def check_cell(con, town, flat_type, month):
    got = q(con, f"""SELECT med_ppsm, r3_med_ppsm, n FROM town_month_metrics
                     WHERE town = '{town}' AND flat_type = '{flat_type}' AND sale_month = DATE '{month}'""")
    if not got:
        print(f"   [FAIL] {town} {flat_type} {month[:7]}: no metrics row")
        return False
    med_got, r3_got, n_got = got[0]
    meds = []
    for m in prev_months(month, 3):
        vals = [r[0] for r in q(con, f"""SELECT price_per_sqm FROM sales
                                         WHERE town = '{town}' AND flat_type = '{flat_type}' AND sale_month = DATE '{m}'""")]
        meds.append(st.median(vals) if vals else None)
    med_ind = meds[-1]
    avail = [v for v in meds if v is not None]
    r3_ind = st.median(avail) if avail else None
    ok = abs(med_got - med_ind) < 1e-6 and abs(r3_got - r3_ind) < 1e-6
    print(f"   [{'PASS' if ok else 'FAIL'}] {town} {flat_type} {month[:7]}: "
          f"med {med_got:.2f} vs {med_ind:.2f} · r3 {r3_got:.2f} vs {r3_ind:.2f} · n={n_got}")
    return ok


def main():
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.read_parquet(PARQUET).create_view('sales')
    try:
        validate_sales(con)
    except ValueError as exc:
        print(f'[FAIL] {exc}')
        print('validation failed — output files NOT written (existing outputs left untouched)')
        sys.exit(1)
    failed = False

    print("== dims (sql/02) ==")
    run_script(con, ROOT / "sql/02_dims.sql")
    print("towns:", q(con, "SELECT count(*) FROM dim_town")[0][0])
    for name, n in q(con, "SELECT flat_type, n_transactions FROM dim_flat_type ORDER BY n_transactions DESC"):
        print(f"   {name}: {n}")

    print()
    print("== metrics (sql/03): town-month medians + rolling ==")
    run_script(con, ROOT / "sql/03_metrics.sql")
    print("town_month_metrics rows:", q(con, "SELECT count(*) FROM town_month_metrics")[0][0])
    print("hand-checks (independent recompute, stdlib statistics):")
    for town, ft, m in HAND_CHECKS:
        failed |= not check_cell(con, town, ft, m)

    print()
    print("== validation (runs BEFORE any file is written) ==")
    nat_med = q(con, f"""SELECT median(price_per_sqm) FILTER (WHERE sale_date BETWEEN DATE '{P1[0]}' AND DATE '{P1[1]}'),
                                median(price_per_sqm) FILTER (WHERE sale_date BETWEEN DATE '{P0[0]}' AND DATE '{P0[1]}')
                         FROM sales WHERE flat_type = '4 ROOM'
                           AND sale_date BETWEEN DATE '{P0[0]}' AND DATE '{P1[1]}'""")[0]
    if any(v is None for v in nat_med):
        print("[FAIL] headline requires 4-room transactions in both quarters")
        print("validation failed — output files NOT written (existing outputs left untouched)")
        sys.exit(1)
    print(f"national 4-room median price/m2: {nat_med[1]:.0f} -> {nat_med[0]:.0f} "
          f"({100 * (nat_med[0] / nat_med[1] - 1):+.2f}%)")

    try:
        d = decomposition(con, P0, P1)
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        print("validation failed — output files NOT written (existing outputs left untouched)")
        sys.exit(1)
    print(f"national decomposition (means): level t0 {d['level_t0']:.2f} | "
          f"total {d['total']:+.2f} | rate {d['rate']:+.2f} | mix {d['mix']:+.2f} | "
          f"interaction {d['inter']:+.2f} S$/m2 | towns {d['towns']}/{d['towns_total']}")
    eps = 1e-9 * max(1.0, abs(d["total"]))
    ok1 = abs(d["rate"] + d["mix"] + d["inter"] - d["total"]) <= eps
    print(f"   [{'PASS' if ok1 else 'FAIL'}] rate + mix + interaction == total (eps {eps:.1e})")
    nat = q(con, f"""SELECT avg(price_per_sqm) FILTER (WHERE sale_date BETWEEN DATE '{P1[0]}' AND DATE '{P1[1]}')
                          - avg(price_per_sqm) FILTER (WHERE sale_date BETWEEN DATE '{P0[0]}' AND DATE '{P0[1]}')
                     FROM sales WHERE flat_type = '4 ROOM'
                       AND sale_date BETWEEN DATE '{P0[0]}' AND DATE '{P1[1]}'""")[0][0]
    ok2 = abs(float(nat) - d["total"]) < 1e-6
    print(f"   [{'PASS' if ok2 else 'FAIL'}] total == direct mean difference ({float(nat):+.4f})")
    ok3 = d["towns"] == d["towns_total"]
    print(f"   [{'PASS' if ok3 else 'FAIL'}] headline coverage: {d['towns']}/{d['towns_total']} towns in both quarters"
          + ("" if ok3 else f" — {d['towns_dropped']} dropped; not a national comparison"))
    failed |= not (ok1 and ok2 and ok3)

    if failed:
        print()
        print("validation failed — output files NOT written (existing outputs left untouched)")
        sys.exit(1)

    print()
    print("== sensitivity (C5): windows + threshold variants ==")
    variants = [
        ("q3 (base)", P0, P1, 0),
        ("q3_thr25", P0, P1, 25),
        ("6m_apr-sep", ("2025-04-01", "2025-09-30"), ("2026-04-01", "2026-09-30"), 0),
        ("6m_apr-sep_thr25", ("2025-04-01", "2025-09-30"), ("2026-04-01", "2026-09-30"), 25),
        ("12m_oct-sep", ("2024-10-01", "2025-09-30"), ("2025-10-01", "2026-09-30"), 0),
        ("12m_oct-sep_thr25", ("2024-10-01", "2025-09-30"), ("2025-10-01", "2026-09-30"), 25),
    ]
    srows = []
    for label, a, b, mn in variants:
        try:
            d = decomposition(con, a, b, mn)
        except ValueError as exc:
            print(f"[FAIL] {label}: {exc}")
            print("validation failed — output files NOT written (existing outputs left untouched)")
            sys.exit(1)
        pct = 100 * (d["total"] / d["level_t0"])
        srows.append({
            "variant": label,
            "towns": d["towns"],
            "towns_dropped": d["towns_dropped"],
            "level_t0": round(d["level_t0"], 2),
            "total_delta": round(d["total"], 2),
            "total_pct": round(pct, 3),
            "rate": round(d["rate"], 2),
            "mix": round(d["mix"], 2),
            "interaction": round(d["inter"], 2),
        })
        drop = f" ({d['towns_dropped']} dropped)" if d["towns_dropped"] else ""
        print(f"   {label:<20} towns {d['towns']:>2}{drop} · total {pct:+.2f}% · "
              f"rate {d['rate']:+.1f} / mix {d['mix']:+.1f} / inter {d['inter']:+.1f} S$/m2")
    print()
    print("== headline table (sql/04): 4-room Q3-2026 vs Q3-2025 ==")
    run_script(con, ROOT / "sql/04_yoy.sql")
    print("towns in table:", q(con, "SELECT count(*) FROM yoy_4room")[0][0])
    csv_path = OUT / "town_4room_yoy.csv"
    run_script(con, ROOT / 'sql/04_export.sql')
    try:
        validate_headline_export(con, decomposition(con, P0, P1))
    except ValueError as exc:
        print(f'[FAIL] {exc}')
        print('validation failed — output files NOT written (existing outputs left untouched)')
        sys.exit(1)
    town_part = csv_path.with_suffix('.csv.part')
    con.sql('SELECT * FROM town_4room_export').write_csv(town_part.as_posix(), header=True)
    print("top 6 towns (by Q3-2026 volume):")
    for r in q(con, """SELECT town, n_t0, n_t1, round(med_t0), round(med_t1),
                              round(100 * (med_t1 / med_t0 - 1), 1)
                       FROM yoy_4room ORDER BY n_t1 DESC LIMIT 6"""):
        print(f"   {r[0]:<15} n {r[1]}->{r[2]} · median {r[3]}->{r[4]} S$/m2 ({r[5]:+.1f}%)")

    sens_path = OUT / "sensitivity.csv"
    sens_part = sens_path.with_suffix('.csv.part')
    with sens_part.open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(srows[0].keys()), lineterminator="\n")
        wcsv.writeheader()
        wcsv.writerows(srows)
    if __package__:
        from .promotion import promote
    else:
        from promotion import promote
    promote([(town_part, csv_path), (sens_part, sens_path)])
    print("wrote:", csv_path.as_posix(), f"({csv_path.stat().st_size} bytes)")
    print("wrote:", sens_path.as_posix(), f"({sens_path.stat().st_size} bytes)")

    print()
    print("RESULT: ALL CHECKS PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
