"""Smoke tests for the committed artifacts — stdlib only, no network.

Run (repo root):  python tests/smoke_test.py
In CI:            same command, on every push + PR (.github/workflows/ci.yml)

These do NOT re-run the pipeline (that needs the raw download); they check the
repo's committed outputs and figures are present, parse, and keep their
expected shape. Regenerating the outputs should still keep these green.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOWN_CSV = ROOT / "outputs" / "town_4room_yoy.csv"
SENS_CSV = ROOT / "outputs" / "sensitivity.csv"

TOWN_REQUIRED_COLS = {
    "town", "n_t0", "n_t1",
    "med_ppsm_2025q3", "med_ppsm_2026q3", "med_pct_change",
}
SENS_REQUIRED_COLS = {
    "variant", "towns", "level_t0", "total_delta", "total_pct",
    "rate", "mix", "interaction",
}
EXPECTED_FIGURES = [
    "f1_town_dumbbell.png", "f1_town_dumbbell-dark.png",
    "f2_rolling_median.png", "f2_rolling_median-dark.png",
    "f3_mix_drift.png", "f3_mix_drift-dark.png",
    "f4_waterfall.png", "f4_waterfall-dark.png",
    "bi_page.png", "bi_page-dark.png",
]

MIN_FIGURE_BYTES = 5000


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_town_csv() -> None:
    rows = _load_csv(TOWN_CSV)
    assert rows, f"{TOWN_CSV.name} has no data rows"
    missing = TOWN_REQUIRED_COLS - set(rows[0].keys())
    assert not missing, f"{TOWN_CSV.name} missing columns: {sorted(missing)}"
    towns = {r["town"] for r in rows}
    assert {"QUEENSTOWN", "TAMPINES"} <= towns, "expected towns missing"
    assert len(rows) >= 20, f"only {len(rows)} towns — expected the full set"
    for r in rows:
        assert float(r["med_ppsm_2025q3"]) > 1000
        assert float(r["med_ppsm_2026q3"]) > 1000
        assert int(r["n_t0"]) >= 1 and int(r["n_t1"]) >= 1


def test_sensitivity_csv() -> None:
    rows = _load_csv(SENS_CSV)
    assert rows, f"{SENS_CSV.name} has no data rows"
    missing = SENS_REQUIRED_COLS - set(rows[0].keys())
    assert not missing, f"{SENS_CSV.name} missing columns: {sorted(missing)}"
    assert len(rows) >= 4, f"only {len(rows)} variants row(s) — expected 6"
    assert rows[0]["variant"].startswith("q3"), "base variant should be first"
    for r in rows:
        float(r["total_pct"])
        float(r["rate"])
        float(r["mix"])
        float(r["interaction"])


def test_figures_present() -> None:
    fig_dir = ROOT / "reports" / "figures"
    missing = [n for n in EXPECTED_FIGURES if not (fig_dir / n).is_file()]
    assert not missing, f"missing figures: {missing}"
    small = [n for n in EXPECTED_FIGURES if (fig_dir / n).stat().st_size < MIN_FIGURE_BYTES]
    assert not small, f"suspiciously small figures: {small}"


def main() -> int:
    checks = [test_town_csv, test_sensitivity_csv, test_figures_present]
    failed = 0
    for fn in checks:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 — report, don't crash the runner
            failed += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    print(f"{len(checks) - failed}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
