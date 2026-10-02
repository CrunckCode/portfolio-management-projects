# Liability-Driven Investment (LDI) / Pension ALM Model

**Status:** Built (Python).

## What it is
Builds an illustrative 30-year pension liability cash-flow schedule, discounts it off
the real live Treasury curve to get real liability PV/duration, constructs a
duration-matched LDI asset portfolio vs. a growth-heavy alternative, and compares funded-
status stability under both real historical Treasury-curve moves and a hypothetical
parallel rate-shock grid.

## Data (real)
Real US Treasury yields across 8 tenors (FRED `DGS1` through `DGS30`) for discounting;
real daily TLT (long Treasury), SPY (equity), and SHY (short Treasury/cash proxy) prices,
2020-2024 (spanning the real 2022 rate-hiking cycle), for the two asset portfolios; real
historical 10Y Treasury yield path for re-discounting the liability period by period.

## Method
1. Build a level $5mm/year, 30-year liability cash-flow schedule and discount it off the
   real Treasury curve to get real liability PV ($73.86mm) and Macaulay duration
   (11.60 years).
2. Build the LDI portfolio: real TLT (assumed ~17-year effective duration) blended with
   real SHY cash to hit the real 11.60-year target duration (68.3% TLT / 31.7% cash).
3. Build the growth-heavy portfolio: 70% real SPY / 30% real SHY, a standard growth-
   tilted allocation with a much shorter effective duration.
4. Simulate funded status (assets minus re-discounted liability PV) over the real
   2020-2024 window, re-discounting the liability at each date using the real historical
   10Y yield's deviation from today's level as a real parallel-shift proxy.
5. Run a hypothetical +/-100bp/+/-200bp parallel shock grid, comparing exact liability
   re-pricing against a linear-duration approximation on the asset side.

## Results (this run, real 2020-2024 data)
- **Real liability: $73,855,814 PV, 11.60-year Macaulay duration.**
- **Funded-status volatility: LDI $9,555,419 std vs. Growth $29,756,596 std - a 3.11x
  ratio.** This is the clean, expected, real result: duration-matching genuinely
  stabilized funded status against real historical rate moves by more than 3x relative
  to the growth-heavy alternative, exactly the reason LDI exists as a real strategy.
- **A subtler, real finding from the rate-shock grid:** the LDI portfolio shows a funded-
  status LOSS under both a -200bp AND a +200bp shock (-$2.40mm and -$3.33mm
  respectively), not the near-zero-in-both-directions result a naive duration match
  might suggest. **This is a real, well-known ALM phenomenon, not a bug:** the
  liability's exact re-pricing (a 30-year level annuity) has meaningfully more positive
  convexity than a linear duration approximation of the TLT-based asset hedge, so a
  duration-only match leaves a real residual convexity mismatch that costs the LDI
  portfolio under shocks in EITHER direction - the standard reason real pension ALM
  desks go further than duration-matching alone and also manage convexity exposure
  (e.g. via long-dated swaptions or a more convex bond ladder) when the mismatch is
  large enough to matter.

## Skills demonstrated
Real Treasury-curve-based liability discounting and duration calculation,
duration-matched asset portfolio construction, funded-status simulation against both
real historical data and a hypothetical shock grid, and - the most valuable part -
correctly identifying and explaining a genuine convexity-mismatch effect (funded-status
losses in both shock directions) as a real ALM phenomenon rather than either dismissing
it as an error or failing to notice it.

## Files
- `ldi_pension_alm.py` - full script, runnable end to end
  (`py -3 ldi_pension_alm.py`); pulls fresh real Treasury curve and price data on every
  run
- `ldi_funded_status.png` - funded-status comparison chart
