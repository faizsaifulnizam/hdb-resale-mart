# Method — how the answer was built, and why each choice was made

Reviewer's fast path: this file → [`sql/04_yoy.sql`](../sql/04_yoy.sql) (the core) → [`outputs/town_4room_yoy.csv`](../outputs/town_4room_yoy.csv). Every number quoted here comes from that CSV or [`decision_memo.md`](decision_memo.md).

## 1 · The question, made computable

National stats report a *single* price index. The question here is what moved inside it: **did 4-room flats get more expensive per m² (rate), or did the mix of towns sold change (mix)?**

Making that answerable needs three moves:

- a like-for-like comparison window → **Q3 2026 vs Q3 2025** — same quarter a year earlier; quarters absorb month noise, same-quarter kills seasonality;
- a size-independent price → **price per m²** (`resale_price ÷ floor_area_sqm`), **4-room** flats only;
- a decomposition that splits the total per-m² move into within-town vs mix parts → **shift-share** (§4).

## 2 · Data and provenance

- Source: data.gov.sg dataset `d_8b84c4ee58e3cfc0ece0d773c8ca6abc` (HDB resale flat prices), pulled **2026-10-02** by [`src/download.py`](../src/download.py) (initiate → poll → signed URL). The raw file is never edited and is gitignored — re-run the script to refetch.
- Shape: **241,822 rows × 11 columns**, registrations 2017-01 → 2026-10. **2026-10 is partial (113 rows) → excluded from all reads**; the analysis window ends 2026-09.
- First contact is an audit, not code: [`data_audit.md`](data_audit.md) profiles nulls, duplicates (318 kept, documented), ranges — and sets the *rules* (window, display threshold, no outlier rule) **before** any analysis.

## 3 · The pipeline

| # | Step | Where |
|---|------|-------|
| 1 | Pull → `data/raw/` (scripted; never manual) | [`src/download.py`](../src/download.py) |
| 2 | Audit → profile + rules | [`data_audit.md`](data_audit.md) |
| 3 | Stage → parse & clean; every exclusion counted | [`sql/01_staging.sql`](../sql/01_staging.sql) |
| 4 | Check → 7 assertions, fail loudly | [`sql/05_checks.sql`](../sql/05_checks.sql) |
| 5 | Measure → town×type×month medians + rolling 3-month medians | [`sql/03_metrics.sql`](../sql/03_metrics.sql) |
| 6 | Decompose → headline table + shift-share | [`sql/04_yoy.sql`](../sql/04_yoy.sql) |
| 7 | Stress → windows × threshold | [`sensitivity.md`](sensitivity.md) |
| 8 | Draw → figures are code, series style | [`src/figures.py`](../src/figures.py) |
| 9 | Communicate → memo · dashboard · README | [`decision_memo.md`](decision_memo.md) · [`bi/`](../bi/README.md) |

SQL does the analytics (CTEs, window functions); Python is glue and figures. Every number has **one home** — `outputs/town_4room_yoy.csv` — and one wording; the memo, README and dashboard are cross-checked against it.

## 4 · The decomposition (the core, in words)

Shift-share on quarterly town **means** (p), weighted by each town's share of 4-room transactions (w):

```text
total       = Σ w₁·p₁ − Σ w₀·p₀     the mean price-level move
            = Σ w₀·(p₁ − p₀)        rate         — within-town price moves
            + Σ (w₁ − w₀)·p₀        mix          — where the transactions went
            + Σ (w₁ − w₀)·(p₁ − p₀) interaction  — moves × weight shifts, together
```

- **Rate** answers "same towns, new prices"; **mix** answers "different towns, old prices"; **interaction** is both at once — it is **reported on its own, not folded into either side** (a deliberate choice; it keeps the other two readable).
- This build: rate **−53.3**, mix **−0.7**, interaction **+13.3** S$/m² → the per-m² move is a **rate story**. Mix nets to ≈0 because town gains and losses offset — Bukit Batok gained volume while easing, Queenstown gained volume while rising ([`decision_memo.md`](decision_memo.md)).
- **Why means inside the split:** medians are not additive — median(A+B) ≠ median(A) + median(B) — so the identity above only holds on means. Medians remain the *display* metric because they resist tails. Stated rather than hidden.
- The code **asserts the identity** `rate + mix + interaction == total` (ε = 1e-9) — [`src/analysis.py`](../src/analysis.py).

## 5 · Rules chosen, and why

| Rule | Choice | Why |
|------|--------|-----|
| Comparison | Q3 2026 vs Q3 2025 | like-for-like; seasonality-free |
| Display threshold | ≥ 25 sales in **each** compared quarter | tiny-town medians are noise; drops 3 towns from headline charts (Bukit Timah 5/4, Marine Parade 7/7, Central Area 23/23) — they stay in the CSV; display rule only |
| Outliers | none applied | data is structurally clean; the tails are real small-flat high-S$/m² cases; winsorising would hide them |
| Trend window | 2023-01 → 2026-09 | post-cooling-measures era; long enough to see the mix drift |

## 6 · Validation — receipts, not claims

- **7/7 checks** pass on the staged table; **0 exclusions** beyond the documented window/type filters ([`sql/05_checks.sql`](../sql/05_checks.sql)).
- **Independent recompute:** 3 town-month medians + rolling medians recomputed in plain Python stdlib (no pandas/DuckDB), matched.
- **Identity assert** on the decomposition (above).
- **Sensitivity:** the read — small move, rate carries the sign, mix ≈0 at the one-quarter horizon — holds across 3/6/12-month windows and with/without the threshold ([`sensitivity.md`](sensitivity.md)).
- **Stranger-rerun:** fresh clone → the four README commands → pipeline runs end-to-end and reproduces the committed outputs for the same pull (a later re-pull can move the newest months — HDB registrations revise).

## 7 · Limits — what this cannot say

Registrations revise upward as they complete; the analysis is descriptive — no forecast, no causal claim; interest rates, BTO supply and grants are context, untested here; flat condition, storey and renovation value are unobserved; one quarter is noisy — read it against [`sensitivity.md`](sensitivity.md).

## 8 · Principles this repo follows

1. **One question per repo** — the method serves the question, not the reverse.
2. **Audit before analysis** — rules come from the data's profile, not habit.
3. **SQL first** — the analysis lives in `.sql`; Python glues and draws.
4. **Nothing hand-edited** — raw data immutable; cleaning, figures and every number regenerate from code.
5. **Limits are part of the deliverable.**
