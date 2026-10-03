"""S3 figures — code-generated, series style, light + dark (theme-adaptive). Run: python src/figures.py (from the repo root).

Produces (reports/figures/), each as a light/dark pair for `<picture>` theme-adaptive README embeds:
  f1_town_dumbbell[-dark].png  — 4-room median price/m² by town, Q3 2026 vs Q3 2025 (threshold applied)
  f2_rolling_median[-dark].png — rolling 3-month median, Singapore + Tampines + Sengkang (2023–2026)
  f3_mix_drift[-dark].png      — share of quarterly 4-room registrations, top 6 towns + other
  f4_waterfall[-dark].png      — shift-share bridge: rate / mix / interaction / total
Reads the parquet via DuckDB; re-runs sql/03 + sql/04 so figures always match the SQL.
"""
import sys
from datetime import date
from pathlib import Path

import json

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.style import use_series_style  # noqa: E402

use_series_style()

import duckdb  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402

from src.analysis import P0, P1, decomposition, run_script  # noqa: E402

PARQUET = (ROOT / "data/processed/sales.parquet").as_posix()
FIGDIR = ROOT / "reports/figures"
FT = "4 ROOM"

# Palette pairs — the dark set adapts the series hues for the ink surface (same roles, same semantics).
LIGHT = dict(ink="#14293D", petrol="#22607B", burnt="#C0552B", teal="#2E7D6B",
             violet="#8A6EAF", brass="#B9975B", muted="#5C6B79", light="#C9C6BF",
             edge="white", suffix="")
DARK = dict(ink="#E7E3DC", petrol="#4C93B5", burnt="#D97E4F", teal="#45A08B",
            violet="#A78FC8", brass="#D4B87A", muted="#8B98A5", light="#435D73",
            edge="#14293D", suffix="-dark")
T = LIGHT  # active palette; switched by main() per pass


def use_palette(p):
    """Switch the active figure palette (module-level)."""
    global T
    T = p


MANIFEST = ROOT / "data/raw/pull_manifest.json"


def _source_date():
    """Pull date from the raw-data manifest (falls back to the last known manual pull)."""
    try:
        ts = json.loads(MANIFEST.read_text(encoding="utf-8")).get("retrieved_at", "")
        return ts[:10] or None
    except Exception:
        return None


SRC = f"Source: HDB resale registrations via data.gov.sg (© HDB), pulled {_source_date() or '2026-10-02'}"


def q(con, sql):
    return con.sql(sql).fetchall()


def foot(fig, text):
    fig.tight_layout(rect=(0, 0.075, 1, 1))
    fig.text(0.01, 0.015, text, fontsize=7.5, color=T["muted"])


def save(fig, name):
    p = FIGDIR / name.replace(".png", T["suffix"] + ".png")
    fig.savefig(p)
    plt.close(fig)
    print(f"wrote {p.as_posix()}  ({p.stat().st_size} bytes)")


def fig1_dumbbell(con):
    rows = q(con, f"""SELECT town, n_t0, n_t1, med_t0, med_t1 FROM yoy_4room
                      WHERE n_t0 >= 25 AND n_t1 >= 25 ORDER BY med_t1""")
    towns = [r[0] for r in rows]
    n_down = sum(1 for r in rows if r[4] < r[3])
    lo = min(min(r[3], r[4]) for r in rows)
    hi = max(max(r[3], r[4]) for r in rows)

    fig, ax = plt.subplots(figsize=(8, 9))
    ys = range(len(rows))
    margin = (hi - lo) * 0.03
    for y, (town, n0, n1, m0, m1) in zip(ys, rows):
        up = m1 >= m0
        ax.plot([m0, m1], [y, y], color=T["light"], lw=1.3, zorder=1)
        ax.scatter([m0], [y], s=26, color=T["muted"], zorder=2, edgecolors=T["edge"], linewidths=0.8)
        ax.scatter([m1], [y], s=36, color=(T["teal"] if up else T["burnt"]), zorder=3, edgecolors=T["edge"], linewidths=0.8)
        pct = 100 * (m1 / m0 - 1)
        pct_txt = "(0.0%)" if abs(pct) < 0.05 else f"({pct:+.1f}%)"
        ax.text(max(m0, m1) + margin, y, f"{m1:,.0f} {pct_txt}", va="center", fontsize=8, color=T["ink"])
    ax.set_yticks(list(ys))
    ax.set_yticklabels(towns)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlim(lo - 380, hi + 1450)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(6))
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    ax.set_xlabel("median price S$/m²")
    ax.set_title(f"4-room resale price per m² — Q3 2026 vs Q3 2025: lower in {n_down} of {len(rows)} towns", fontsize=12)
    ax.scatter([], [], s=26, color=T["muted"], label="Q3 2025")
    ax.scatter([], [], s=36, color=T["teal"], label="Q3 2026 — higher")
    ax.scatter([], [], s=36, color=T["burnt"], label="Q3 2026 — lower")
    ax.legend()
    foot(fig, f"4-room · towns with ≥25 transactions in each quarter (3 excluded) · {SRC}")
    print(f"F1: {len(rows)} towns shown · lower in {n_down}")
    save(fig, "f1_town_dumbbell.png")


def fig2_rolling(con):
    series = [("(all)", "Singapore (all towns)", T["ink"], 2.4), ("TAMPINES", "Tampines", T["petrol"], 1.9), ("SENGKANG", "Sengkang", T["burnt"], 1.9)]
    fig, ax = plt.subplots()
    last = None
    for town, label, color, lw in series:
        rows = q(con, f"""SELECT sale_month, r3_med_ppsm FROM town_month_metrics
                          WHERE town = '{town}' AND flat_type = '{FT}'
                            AND sale_month >= DATE '2023-01-01' AND r3_med_ppsm IS NOT NULL
                          ORDER BY sale_month""")
        xs = [r[0] for r in rows]
        ys = [float(r[1]) for r in rows]
        ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round")
        ax.annotate(label, (xs[-1], ys[-1]), xytext=(7, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=color, fontweight="semibold")
        last = xs[-1]
    ax.set_xlim(date(2023, 1, 1), date(2027, 3, 1))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.set_ylabel("S$/m² (rolling 3-month median)")
    ax.set_title("Rolling 3-month median of the last 3 monthly medians\n4-room resale price per m²")
    foot(fig, f"Monthly medians · Tampines (mature) · Sengkang (non-mature) · {SRC}")
    print("F2: series plotted —", ", ".join(s[1] for s in series))
    save(fig, "f2_rolling_median.png")


def fig3_mix(con):
    rows = q(con, f"""SELECT town, sale_month, n FROM town_month_metrics
                      WHERE flat_type = '{FT}' AND town <> '(all)' AND sale_month >= DATE '2023-01-01'
                      ORDER BY sale_month""")
    totals = {}
    for town, _, n in rows:
        totals[town] = totals.get(town, 0) + n
    top6 = [t for t, _ in sorted(totals.items(), key=lambda kv: -kv[1])][:6]

    quarters = []
    seen = set()
    for _, m, _n in rows:
        qt = date(m.year, 3 * ((m.month - 1) // 3) + 1, 1)
        if qt not in seen:
            seen.add(qt)
            quarters.append(qt)
    quarters.sort()
    qidx = {qt: i for i, qt in enumerate(quarters)}
    grid = {t: [0] * len(quarters) for t in top6}
    grid["OTHER"] = [0] * len(quarters)
    qtot = [0] * len(quarters)
    for town, m, n in rows:
        qt = date(m.year, 3 * ((m.month - 1) // 3) + 1, 1)
        i = qidx[qt]
        qtot[i] += n
        if town in grid:
            grid[town][i] += n
        else:
            grid["OTHER"][i] += n
    order = list(top6) + ["OTHER"]
    palette = {}
    pool = [T["teal"], T["violet"], T["brass"], T["muted"]]
    for t in order:
        if t == "TAMPINES":
            palette[t] = T["petrol"]
        elif t == "SENGKANG":
            palette[t] = T["burnt"]
        elif t == "OTHER":
            palette[t] = T["light"]
        else:
            palette[t] = pool.pop(0)
    shares = [[grid[t][i] / qtot[i] for i in range(len(quarters))] for t in order]

    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    ax.stackplot(quarters, *shares, labels=order, colors=[palette[t] for t in order], edgecolor=T["edge"], lw=0.4)
    ax.set_ylim(0, 1)
    ax.set_xlim(quarters[0], quarters[-1])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    ax.grid(False)
    ax.set_ylabel("share of 4-room registrations")
    ax.set_title("Four-room sales mix by town — top 6 and the rest (quarterly share)")
    handles, labels_ = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels_[::-1], loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.075, 0.83, 1))
    fig.text(0.01, 0.015, f"Share of quarterly registrations · 2023 Q1 – 2026 Q3 · {SRC}", fontsize=7.5, color=T["muted"])
    print("F3: top towns —", ", ".join(top6))
    save(fig, "f3_mix_drift.png")


def fig4_waterfall(con, d):
    labels = ["Rate\n(within towns)", "Mix\n(town shares)", "Interaction", "Total"]
    deltas = [("rate", d["rate"], T["burnt"]), ("mix", d["mix"], T["burnt"]), ("inter", d["inter"], T["teal"])]

    fig, ax = plt.subplots()
    cum = 0.0
    xs = [0, 1, 2, 3]
    for i, (key, val, color) in enumerate(deltas):
        ax.bar(xs[i], abs(val), bottom=min(cum, cum + val), color=color, width=0.6, zorder=3)
        ax.annotate(f"{val:+.1f}", (xs[i], cum + val), xytext=(0, 8 if val > 0 else -14),
                    textcoords="offset points", ha="center",
                    va=("bottom" if val > 0 else "top"), fontsize=9, color=T["ink"])
        if i < len(deltas) - 1:
            ax.plot([xs[i] + 0.3, xs[i + 1] - 0.3], [cum + val, cum + val], color=T["light"], lw=0.9, ls="--", zorder=2)
        cum += val
    ax.bar(xs[3], abs(d["total"]), bottom=min(0, d["total"]), color=T["ink"], width=0.6, zorder=3)
    ax.annotate(f"{d['total']:+.1f}", (xs[3], d["total"]), xytext=(0, -14),
                textcoords="offset points", ha="center", va="top", fontsize=9, color=T["ink"])
    ax.axhline(0, color=T["muted"], lw=0.9, zorder=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylim(min(cum, d["total"]) - 28, 34)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.set_ylabel("S$/m² contribution")
    ax.set_title(f"Rate, not mix — the {d['total']:+.1f} S$/m² move decomposes within towns")
    foot(fig, f"Shift-share on quarterly means · level {d['level_t0']:,.1f} → {d['level_t0'] + d['total']:,.1f} S$/m² · {SRC}")
    print(f"F4: rate {d['rate']:+.2f} · mix {d['mix']:+.2f} · inter {d['inter']:+.2f} · total {d['total']:+.2f}")
    save(fig, "f4_waterfall.png")


def main():
    import os

    os.chdir(ROOT)
    FIGDIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE OR REPLACE VIEW sales AS SELECT * FROM read_parquet('{PARQUET}')")
    run_script(con, ROOT / "sql/03_metrics.sql")
    run_script(con, ROOT / "sql/04_yoy.sql")
    d = decomposition(con, P0, P1)
    for palette in (LIGHT, DARK):
        use_palette(palette)
        use_series_style(dark=(palette is DARK))
        print(f"-- rendering {'dark' if palette['suffix'] else 'light'} set --")
        fig1_dumbbell(con)
        fig2_rolling(con)
        fig3_mix(con)
        fig4_waterfall(con, d)
    print("figures done — light + dark")


if __name__ == "__main__":
    main()
