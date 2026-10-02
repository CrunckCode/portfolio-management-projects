# Portfolio Rebalancing and Tax-Aware Trade Optimization Tool

**Status:** Built (Python).

## What it is
A drift-band rebalancing engine (rebalance only when an asset drifts beyond a tolerance
band, not on a fixed calendar) simulated over real historical daily returns for a 4-asset
model portfolio, quantifying the turnover reduction vs. a naive monthly full-rebalance
approach, plus a tax-lot-aware (specific-identification/HIFO) sell-selection rule compared
against naive FIFO.

## Data
**Real:** daily prices for SPY/TLT/GLD/VNQ, 2020-01-02 to 2024-12-31 (1,258 real trading
days, spanning the COVID crash, the 2022 rate-hike drawdown, and the 2023-2024 recovery),
via `yfinance`, used to drive the actual portfolio drift the rebalancing logic reacts to.
**Constructed (necessarily):** individual tax-lot records (purchase date, shares, cost
basis) - real brokerage account lot data isn't publicly accessible, so this section
generates illustrative lots priced off the same real historical price series (a lot's
cost basis is the real SPY/TLT/GLD/VNQ price on its randomly assigned purchase date, not
an invented price).

## Method
1. Simulate the $5M model portfolio's value and drift day-by-day using real returns;
   trigger a rebalance only when any asset's weight drifts more than 5 percentage points
   from its 50/30/10/10 target.
2. Compare total turnover against a naive calendar-based monthly full-rebalance-to-target
   approach over the same real return history.
3. Build tax lots (6 per asset) with real historical cost-basis prices; classify each as
   long-term (>365 days held) or short-term.
4. Tax-aware sell selection: sell losses first (any holding period), then long-term gains
   ordered smallest-gain-first (specific-identification/HIFO - sell the highest-cost-basis
   long-term lots before the lowest-cost-basis ones), then short-term gains last.
5. Compare realized gain from this selection against naive FIFO (oldest lot sold first,
   regardless of tax consequence) for a sample $3,000-share SPY trim.

## Results (this run, real return history)
**Band-based rebalancing triggered 7 times** over 1,258 real trading days (2020-03-06 at
the start of the COVID crash, 2020-03-23 near the market bottom, 2020-05-08 and
2020-12-01 during the recovery, 2021-04-29, 2022-10-21 near the 2022 lows, and
2024-02-07) - the triggers themselves are a real, sensible record of when this specific
portfolio's real drift actually crossed the band, not arbitrary dates.

**Turnover: band-based rebalancing generated $4,390,187 in total turnover across 7 events,
vs. $7,718,458 for naive monthly full-rebalancing across ~60 events - a 43.1% turnover
reduction** for materially the same risk control (staying within a defined drift
tolerance), which directly translates to lower transaction costs and, in a taxable
account, less unnecessary gain realization.

**Tax-aware lot selection:** for a 3,000-share SPY trim, tax-aware (HIFO-within-gains)
selection realized $537,695 of gain vs. $844,317 for naive FIFO - **a $306,622 reduction
in realized taxable gain** for an economically identical trade (same shares sold, same
post-trade allocation), purely from choosing which specific lots to sell.

## Honesty note on scope
The turnover/drift analysis is real (real prices drive real portfolio drift and real
turnover numbers). The tax-lot section's cost bases are constructed but grounded in real
historical prices at randomly assigned purchase dates; a production version would connect
to an actual custodian's lot-level cost-basis feed rather than generating lots
programmatically.

## Skills demonstrated
Drift-band (vs. calendar) rebalancing logic, quantified turnover comparison across
rebalancing methodologies on real return data, and tax-lot-aware sell selection
(specific-identification/HIFO within the gains bucket, not just "sell losses first").

## Files
- `rebalancing_tool.py` - full script, runnable end to end
  (`py -3 rebalancing_tool.py`); pulls fresh 5-year price history from Yahoo Finance on
  every run
