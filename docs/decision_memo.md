# Decision memo — 4-room resale prices, Q3 2026 vs Q3 2025

**Data:** HDB resale registrations (data.gov.sg, pulled 2026-10-02) · 4-room flats · window 2023-01 → 2026-09.
**Headline:** the national median price per m² dipped **−1.3% year-on-year** (S$6,647 → S$6,559, Q3 2026 vs Q3 2025); the decomposition runs on **means** (**−0.6%**) — medians are not additive, and both bases point the same way. The move is **within-town**, not a change in which towns sold.

## What moved

- 16 of 23 towns shown were lower; the range runs from **Queenstown +10.9%** to **Bukit Batok −6.3%** (≥25 sales in each compared quarter — the display rule; all 26 towns are in `outputs/town_4room_yoy.csv`).
- In level terms the move is small: −S$40.6/m² on the quarterly mean (≈ −0.6%).

## Rate vs mix (the core)

Transaction-weighted shift-share on quarterly means:

| component | S$/m² | read |
|---|---|---|
| rate (within-town) | **−53.3** | dominates the move |
| mix (town weights) | **−0.7** | nets to ≈ zero |
| interaction | +13.3 | the overlap term (weight shifts × price moves); reported, not folded in |
| **total** | **−40.6** | mean level 7,168.5 → 7,127.9 |

Mix nets to ≈ zero *because share gains and losses cancel each other*: Bukit Batok gained volume (134 → 189 sales) while its own median eased 6.3%; Queenstown gained volume *and* rose 10.9%. Across towns these effects offset almost exactly. So the per-m² move is a **rate story** at this horizon.

Method note: medians are shown; means feed the split because medians are not additive — stated rather than hidden. Robustness is in [`sensitivity.md`](sensitivity.md): direction holds across 3-, 6- and 12-month windows and with/without the small-town threshold, but the component mix is window-dependent — mix is ≈0 at the quarter, then +25.1 / +25.6 S$/m² at six and twelve months, offsetting much of the rate contribution — and the threshold moves magnitudes (Q3 total −40.6 → −23.3 S$/m²), not direction.

## What a buyer should NOT conclude

- **Not "the market is falling."** This is one quarter; the 12-month window reads +1.0%. The signal is the *composition* of the move (rate ≫ mix), not its sign.
- **Not "my town moved like the headline."** Towns diverged by ~17 percentage points (−6.3% to +10.9%).
- **Not "prices now."** These are *registration* dates; the newest month can still revise upward as registrations complete.

## What this file cannot say

Why the rate moved — interest rates, BTO supply, grants and cooling measures are context, not tested here. Storey range is observed (staged as a midpoint) but not adjusted for; exact storey, flat condition and renovation value are unobserved. Related-party and part-share sales are excluded by HDB. And a single quarter is noisy — read the direction against `sensitivity.md`, not one print.

*How it was built, step by step — choices, validation, limits → [Method, in the README](../README.md#method).*
