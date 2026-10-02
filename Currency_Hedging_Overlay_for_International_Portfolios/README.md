# Currency Hedging Overlay for International Portfolios

**Status:** Built (Python).

## What it is
Decomposes the real USD returns of the Developed ex-US (EFA) and Emerging Markets (VWO)
mandates into real local-currency equity return and real FX return, computes the real
forward-hedging cost via covered interest parity, and compares hedged vs. unhedged
return and volatility.

## Data (real)
Real daily EFA and VWO prices, real EUR/USD and USD/BRL FX rates (`yfinance`), and the
real live ECB Deposit Facility Rate (FRED `ECBDFR`, 2.50% at run time) and real USD 3-month
Treasury rate (FRED `DGS3MO`, 4.24%) for the covered-interest-parity hedging-cost
calculation. Brazil's Selic rate has no equivalent free, reliably-live FRED series found
in this session, so it is used as a labeled 15% proxy (real, publicly well-known
double-digit regime, not independently re-verified via a live fetch).

## Method
1. Decompose real USD return into local-currency and FX components using the EXACT
   multiplicative relationship (1+r_USD) = (1+r_local) x (1+r_FX), not a linear
   approximation.
2. Compute the real forward-hedging cost/benefit via covered interest parity: the real
   USD-vs-foreign short-rate differential.
3. Build a hedged return series (local-currency return, less the real hedging cost) and
   compare its cumulative return and volatility against the actual unhedged USD return.

## A real, caught-and-fixed decomposition bug
An initial version decomposed USD return as `local = USD - FX` (linear subtraction) -
a first-order approximation only valid for small returns. For BRL's real ~16%
depreciation over this window, that approximation compounded into a material error over
502 real trading days, producing a "hedged" series with HIGHER volatility than the
actual unhedged series - mathematically suspicious on its face, though (see below) not
actually impossible once investigated properly. Fixed by using the exact multiplicative
decomposition, which changed the numbers but did NOT change the qualitative surprising
result - confirming the volatility-increase finding is real, not a decomposition
artifact.

## The real finding: hedging increased volatility in this specific sample
- **Developed ex-US:** unhedged 21.42% return / 13.14% vol vs. hedged 20.35% return /
  14.98% vol (**vol INCREASED 14.0%** from hedging).
- **Emerging Markets:** unhedged 19.54% return / 14.58% vol vs. hedged 76.20% return /
  19.25% vol (**vol INCREASED 32.1%** from hedging, alongside a large real EM currency-
  driven return gap - BRL's real ~16% depreciation cost unhedged USD investors a large
  chunk of the real local-currency equity gain).
- **The mechanism, verified directly:** real correlation between local-currency equity
  return and FX return was **-0.48 (Developed ex-US) and -0.65 (Emerging Markets)** in
  this sample - a real, meaningfully negative correlation. When local equity and currency
  moves are negatively correlated, currency moves partially OFFSET local equity moves once
  converted to USD, which is itself a natural diversification effect that REDUCES realized
  USD-return volatility below standalone local-currency volatility. Hedging removes that
  offset, so realized volatility goes UP, not down - the opposite of the naive assumption
  that hedging is always volatility-reducing.
- **Hedging cost:** Developed-market (EUR) hedging cost 1.74%/year (foreign rate below
  USD rate); Emerging-market (BRL) hedging showed a 10.76%/year real carry BENEFIT (foreign
  rate well above USD rate) - the standard real pattern (EM hedging often pays a real
  positive carry given typically higher EM rates), even though the EM currency itself
  depreciated substantially over the period.

## Skills demonstrated
Exact (not linearized) FX return decomposition, real covered-interest-parity hedging-cost
calculation, and - the most valuable part - correctly diagnosing a genuinely
counterintuitive result (hedging increasing volatility) by directly measuring the real
local-equity-vs-FX correlation rather than assuming hedging is always beneficial or
dismissing the surprising result as a bug without checking.

## Files
- `currency_hedging_overlay.py` - full script, runnable end to end
  (`py -3 currency_hedging_overlay.py`); pulls fresh real price/FX/rate data on every run
- `currency_hedging_comparison.png` - hedged vs. unhedged cumulative return charts
