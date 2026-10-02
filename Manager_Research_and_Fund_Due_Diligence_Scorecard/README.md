# Manager Research and Fund Due Diligence Scorecard

**Status:** Built (Python).

## What it is
A quantitative manager-screening scorecard across a 12-fund large-cap-growth peer group:
risk-adjusted performance metrics (Sharpe, Sortino, Calmar, up/down-capture), a composite
ranking, and a returns-based style regression (Sharpe-style analysis) that checks whether
each fund's actual factor exposure matches its stated growth mandate.

## Data (real)
Real monthly total returns, derived from daily adjusted close prices via `yfinance`, for
12 real large-cap-growth funds/ETFs (VUG, SCHG, MGK, IWF, SPYG, QQQ, FTEC, VONG, IVW,
JGRO, MOAT, SPHQ) plus SPY (benchmark) and 3 factor proxies (IWM=size, IWD=value,
MTUM=momentum).

## Method
1. Compute Sharpe, Sortino, Calmar, max drawdown, and up/down-capture vs. SPY for each
   fund from real monthly returns.
2. Z-score and average Sharpe/Sortino/Calmar/inverted-down-capture into a composite score.
3. Run a multi-factor returns-based style regression (fund return ~ Market + Size + Value
   + Momentum factor returns) per fund to infer real factor exposure.
4. Flag style drift: a fund claiming a large-cap-growth mandate should NOT show a
   meaningful positive Value tilt or large unexplained Size tilt; flagged funds get a
   composite-score penalty.

## Results (this run)
**Top-ranked: VONG** (Sharpe 1.39, Sortino 2.09, lowest down-capture at 0.89 among the
top group). **Bottom-ranked: MOAT** (Sharpe 0.82, and its style regression shows a
**positive 0.63 Value loading and -0.59 Momentum loading** - genuinely inconsistent with
a "growth" label; MOAT is a real quality/moat-focused fund, so this is a correct and
expected finding, not a data error, and demonstrates the style regression doing its actual
job).

**Style drift flagged:** FTEC, JGRO, MOAT, SPHQ - each shows either an unexpected positive
Value tilt or Size tilt inconsistent with a stated large-cap-growth mandate. FTEC (tech
sector fund) and SPHQ (quality factor fund) both being flagged makes sense: they're
"growth-adjacent" but not pure growth mandates, exactly the kind of finding a real
due-diligence process is supposed to surface (funds masquerading under a category label
that doesn't fully describe their actual factor exposure).

## Two honest methodological limitations found while building this
1. **Real sample window shrank to 28 months (2022-09 to 2024-12), not the intended
   2019-2024**, because JGRO (a real ETF) only has real listing history back to 2022 -
   the `dropna()` intersection across all funds truncated the whole panel to the shortest
   real history. A production version would either drop JGRO to keep the longer window or
   report metrics on unequal available histories per fund rather than silently truncating
   all funds to the shortest one.
2. **The style-regression coefficients are unusually large (Market beta 1.6-2.4 for
   several funds)** - a real, well-known artifact of running an *unconstrained* OLS
   regression on highly collinear factor proxies (SPY/IWM/IWD/MTUM are themselves highly
   correlated with each other). William Sharpe's original 1992 returns-based style
   analysis method specifically constrains factor weights to sum to 1 with no negative
   weights to avoid exactly this instability; this build uses unconstrained regression for
   simplicity, so the coefficient *magnitudes* are not directly interpretable as portfolio
   weights, only their *relative signs and ranking* (e.g. MOAT's genuine positive Value
   tilt vs. others' negative Value tilt) are reliable here.

## Skills demonstrated
Risk-adjusted performance metric construction, composite scorecard/ranking design,
returns-based style analysis, and - importantly - catching and correctly diagnosing two
real methodological limitations (data-availability truncation and multicollinearity in an
unconstrained factor regression) rather than presenting an overconfident, unqualified
result.

## Files
- `manager_research.py` - full script, runnable end to end
  (`py -3 manager_research.py`); pulls fresh price data from Yahoo Finance on every run
