# Data audit — HDB resale prices (raw pull 2026-10-02)

Read-only profile of `data/raw/hdb-resale-prices-2017-onwards.csv` — 241,823 lines incl. header (241,822 transaction rows × 11 columns), pulled 2026-10-02 from data.gov.sg `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`. Numbers produced by `src/audit.py`.

## Profile

- **Coverage:** 2017-01 → 2026-10 (registration month). **2026-10 is partial (113 rows) — excluded from all trend/quarter reads**; analysis window ends 2026-09. Recent months can revise upward as registrations complete.
- **Nulls:** none in any column.
- **Parseability:** `storey_range` 241,822/241,822 OK · `remaining_lease` 241,822/241,822 OK ("60 years 10 months" style).
- **Exact-duplicate copies:** 318 (0.13%) — **kept, documented**; they are indistinguishable from repeat registrations, not silently dropped.
- **Towns:** 26 — smallest BUKIT TIMAH (588 total), largest SENGKANG (19,554). All towns ≥ 208 transactions since 2023-01.
- **Flat types:** 4 ROOM 102,785 · 5 ROOM 59,153 · 3 ROOM 57,394 · EXECUTIVE 17,224 · 2 ROOM 5,088 · MULTI-GENERATION 90 · 1 ROOM 88.
- **Ranges:** price 140,000 → 1,728,000 · area 31.0 → 366.7 m² · price/m² p0.1–p99.9: 2,785 → 13,698 (median 5,325). Tails are real (small flats carry high S$/m²); no impossible values.
- **Structural:** price ≤ 0: 0 · area ≤ 0: 0 · unparseable month: 0.

## Proposed rules — Faiz calls #2 / #3 *(proposed 2026-10-02 — confirm at next checkpoint)*

1. **Window (#2):** long view **2023-01 → 2026-09**; headline = latest complete quarter **(2026 Q3, Jul–Sep) vs same quarter a year earlier (2025 Q3)**, 4-room flats.
2. **Tiny-town display threshold (#3):** a town appears in headline charts only with **≥ 25 four-room transactions in each compared quarter**; below that it stays in `outputs/town_4room_yoy.csv` with a flag. Effect: drops **BUKIT TIMAH (5/4), MARINE PARADE (7/7), CENTRAL AREA (23/23)**; all others ≥ 38. (Central Area sits just under the line — noted, can revisit.)
3. **Outlier rule:** **none applied** — data is structurally clean; winsorising would hide real small-flat high-S$/m² cases. Documented instead.

## Exclusion ledger (staging)

| rule | rows excluded |
|---|---|
| price ≤ 0 | 0 |
| floor area ≤ 0 | 0 |
| unparseable month | 0 |
| missing lease text | 0 |
| **total: in → staged** | **241,822 → 241,822 (0.000%)** |

Validation (`sql/05_checks.sql` via `src/build_dataset.py`): **7/7 PASS** (price>0 · area>0 · date range · town · flat_type · price/m² · lease years).

## Notes carried into the build

- `storey_mid` and `remaining_lease_years` are derived at staging (`sql/01_staging.sql`); every exclusion is counted by `src/build_dataset.py`.
- 4-room focus: 102,785 rows total · 42,882 since 2023-01.
- Registration dating means the newest months move — the memo and README carry this caveat.
