# Sensitivity — 4-room Q3-2026 vs Q3-2025 decomposition

Same shift-share method as the headline, re-run under wider windows and with an analytic restriction to the towns meeting the display threshold (weights re-normalized). The headline calculation itself retains all 26 towns.
Reproduce: `python src/analysis.py` → `outputs/sensitivity.csv`. Method: [`sql/04_yoy.sql`](../sql/04_yoy.sql).

| variant | towns | total Δ vs level | rate | mix | interaction |
|---|---|---|---|---|---|
| q3 (base) | 26 | −0.57% | −53.3 | −0.7 | +13.3 |
| q3 · thr25 | 23 | −0.33% | −38.5 | +2.3 | +13.0 |
| 6m Apr–Sep | 26 | −0.02% | −37.5 | +25.1 | +11.3 |
| 6m Apr–Sep · thr25 | 24 | −0.03% | −37.7 | +24.2 | +11.1 |
| 12m Oct–Sep | 26 | +0.99% | +31.8 | +25.6 | +12.4 |
| 12m Oct–Sep · thr25 | 25 | +0.97% | +30.5 | +25.9 | +12.5 |

Rate / mix / interaction in S$/m², 4-room, transaction-weighted by town; total Δ expressed against **each variant’s own period-0 level** (S$7,169/m² for the base quarter; S$7,076/m² for the base twelve-month window). `thr25` = towns with ≥25 four-room transactions in each compared period (the display threshold — see [`data_audit.md`](data_audit.md)).

**What holds across all variants**

- The total per-m² move stays small — from −0.6% to +1.0%. No window turns the headline into a big rise or fall.
- Within-town movement (rate) carries the sign of the total at every horizon; town-mix is ≈0 at the one-quarter horizon.
- Mix is ≈0 at the quarter horizon but turns materially positive beyond it — **+25.1 S$/m² at six months** and **+25.6 over the year** (≈+0.36% of the respective period-0 levels). It offsets most of the **negative** rate at six months but **adds to the positive rate** at twelve months, under either threshold.
- Applying the threshold changes magnitudes materially but preserves the sign **within each window**, not across windows: dropping the three below-threshold towns lifts the Q3 total from −40.6 to −23.3 S$/m² (rate −53.3 → −38.5; total −0.57% → −0.33%). Central Area alone contributes −16.4 S$/m² to the base rate with 23 sales per quarter; the threshold variant removes it along with Marine Parade and Bukit Timah and re-normalizes the remaining town weights.

**Where the sensitivity bites**

- **The sign is not stable across windows:** the base total is −0.567% at three months, −0.016% at six months and **+0.987% at twelve months**; the rate term also turns positive at twelve months. This is not evidence of a sustained decline.
- A single quarter is noisy; over 6 months the total flattens to ≈0 because a positive mix contribution starts to offset the negative rate contribution. Component *shares* of a near-zero total are meaningless by construction (six-month rate ÷ total ≈ +3,300%) — read components in S$/m², as above.

Figures and the memo use the Q3 base variant; this file is a window/threshold sensitivity check, not a claim of sign robustness. “Rate” is a town-average price/m² change, not a like-for-like flat-price change: block, model, storey and lease composition remain inside it.
