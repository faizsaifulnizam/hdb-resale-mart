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
- Mix turns materially positive only over the full year (+25.6 S$/m², ≈+0.36%), under either threshold.
- The display threshold shifts magnitudes by a few S$/m² — signs and story unchanged.

**Where the sensitivity bites**

- A single quarter is noisy; over 6 months the total flattens to ≈0 because a positive mix contribution starts to offset the negative rate contribution.

Figures and the memo use the Q3 base variant; both may cite this file as the robustness check.
