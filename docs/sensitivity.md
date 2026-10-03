# Sensitivity — 4-room Q3-2026 vs Q3-2025 decomposition

Same shift-share method as the headline, re-run under wider windows and the display threshold.
Reproduce: `python src/analysis.py` → `outputs/sensitivity.csv`. Method: [`sql/04_yoy.sql`](../sql/04_yoy.sql).

| variant | towns | total Δ vs level | rate | mix | interaction |
|---|---|---|---|---|---|
| q3 (base) | 26 | −0.57% | −53.3 | −0.7 | +13.3 |
| q3 · thr25 | 23 | −0.33% | −38.5 | +2.3 | +13.0 |
| 6m Apr–Sep | 26 | −0.02% | −37.5 | +25.1 | +11.3 |
| 6m Apr–Sep · thr25 | 24 | −0.03% | −37.7 | +24.2 | +11.1 |
| 12m Oct–Sep | 26 | +0.99% | +31.8 | +25.6 | +12.4 |
| 12m Oct–Sep · thr25 | 25 | +0.97% | +30.5 | +25.9 | +12.5 |

Rate / mix / interaction in S$/m², 4-room, transaction-weighted by town; total Δ expressed against the period-0 level (~S$7,169/m²). `thr25` = towns with ≥25 four-room transactions in each compared period (the display threshold — see [`data_audit.md`](data_audit.md)).

**What holds across all variants**

- The total per-m² move stays small — from −0.6% to +1.0%. No window turns the headline into a big rise or fall.
- Within-town movement (rate) carries the sign of the total at every horizon; town-mix is ≈0 at the one-quarter horizon.
- Mix is ≈0 at the quarter horizon but turns materially positive beyond it — **+25.1 S$/m² at six months** and **+25.6 over the year** (≈+0.36% of the period-0 level) — offsetting most of the rate contribution there, under either threshold.
- The display threshold moves magnitudes materially, not direction: dropping the three below-threshold towns lifts the Q3 total from −40.6 to −23.3 S$/m² (rate −53.3 → −38.5; total −0.57% → −0.33%).

**Where the sensitivity bites**

- A single quarter is noisy; over 6 months the total flattens to ≈0 because a positive mix contribution starts to offset the negative rate contribution. Component *shares* of a near-zero total are meaningless by construction (six-month rate ÷ total ≈ +3,300%) — read components in S$/m², as above.

Figures and the memo use the Q3 base variant; both may cite this file as the robustness check.
