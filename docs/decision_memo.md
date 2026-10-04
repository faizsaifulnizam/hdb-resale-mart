# Decision memo — 4-room resale prices, Q3 2026 vs Q3 2025

**Data:** HDB resale registrations (data.gov.sg, historical 2026-10-02 snapshot; manifest time is a file-mtime proxy) · 4-room flats · window 2023-01 → 2026-09.
**Headline:** the national median price per m² dipped **−1.3% year-on-year** (S$6,647 → S$6,559, Q3 2026 vs Q3 2025); the decomposition runs on **means** (**−0.6%**) — medians are not additive, and both bases point the same way. Town-share mix nets to ≈0, but the rate term still includes within-town sales composition: **Central Area contributes −16.4 of the −53.3 S$/m² rate** with 23 sales per quarter. Cantonment Road Type S1 sales fall from 15 to 8; this coincidence does not establish like-for-like price changes.

## What moved

- 16 of 23 towns shown were lower; the range runs from **Queenstown +10.9%** to **Bukit Batok −6.3%** (≥25 sales in each compared quarter — the display rule; all 26 towns are in `outputs/town_4room_yoy.csv`).
- In level terms the move is small: −S$40.6/m² on the quarterly mean (≈ −0.6%).

## Rate vs mix (the core)

Transaction-weighted shift-share on quarterly means:

| component | S$/m² | read |
|---|---|---|
| rate (town-average price/m²) | **−53.3** | includes within-town composition; not matched-flat prices |
| mix (town weights) | **−0.7** | nets to ≈ zero |
| interaction | +13.3 | the overlap term (weight shifts × price moves); reported, not folded in |
| **total** | **−40.6** | mean level 7,168.5 → 7,127.9 |

The **town-weight** term nets to ≈ zero because its positive and negative contributions cancel: for example, Bukit Batok contributes +93.0 and Queenstown +106.0 S$/m² to mix, while Sengkang contributes −72.2 and Clementi −83.7. These are weighted **mean** contributions, not contributions to the national median. Near-zero net town mix does not mean the same kinds of flats sold within each town.

**Central Area shows why that distinction matters.** It contributes −16.4 S$/m², or **30.9% of the −53.3 rate term**, despite only 23 four-room sales in each quarter. Its raw median falls from S$14,481.7 to S$8,947.4/m², alongside Cantonment Road Type S1 sales falling from 15 to 8 (also 15 → 8 sales at ≥S$12,000/m²). This documents a composition change coinciding with the price move, not a causal decomposition of block/model effects. Central Area remains in the national calculation but is suppressed on the town chart. Restricting the split to all towns with ≥25 sales per quarter, with town weights re-normalized, moves the Q3 rate to **−38.5** and the total to **−23.3 S$/m²**.

Method note: medians are shown; means feed the split because medians are not additive. The trend chart uses the median of the last three monthly medians, not the median of pooled sales in those months. [`Sensitivity`](sensitivity.md) shows small totals, **not a stable sign**: Q3 −0.567%, six months −0.016%, twelve months **+0.987%**. Mix is ≈0 at the quarter, +25.1 S$/m² at six months (offsetting much of the negative rate), and +25.6 at twelve months (**adding to** a positive +31.8 rate). Applying the threshold preserves the sign within each window, while changing the magnitudes.

## What a buyer should NOT conclude

- **Not "the market is falling."** This is one quarter; the 12-month window reads +1.0%. The quarterly town-share split is descriptive; the rate term still includes within-town composition, and its sign also turns positive over twelve months.
- **Not "my town moved like the headline."** Towns diverged by ~17 percentage points (−6.3% to +10.9%).
- **Not "prices now."** These are *registration* dates; the newest month can still revise upward as registrations complete.

## What this file cannot say

Why the rate moved — interest rates, BTO supply, grants and cooling measures are context, not tested here. Storey range is observed (staged as a midpoint) but not adjusted for; exact storey, flat condition and renovation value are unobserved. Related-party and part-share sales are excluded by HDB. Floor area is the only attribute normalized for; block, lease and model are not held fixed. A single quarter is noisy — read all windows in `sensitivity.md`, not one print.

*How it was built, step by step — choices, validation, limits → [Method, in the README](../README.md#method).*
