"""
Portfolio Rebalancing and Tax-Aware Trade Optimization Tool
================================================================
Drift-band rebalancing (not calendar-based) simulated over REAL historical daily returns
for a 4-asset model portfolio, with a minimum-trade trade-list generator and a tax-lot-aware
sell-selection rule (loss-harvest first, avoid short-term gains) compared against a naive
full-rebalance-to-target approach.
"""
import numpy as np
import pandas as pd
import yfinance as yf

TICKERS = ["SPY", "TLT", "GLD", "VNQ"]
TARGET = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.10, "VNQ": 0.10}
BAND = 0.05  # rebalance when any asset drifts +/-5 percentage points from target

# ===========================================================================
# 1. Real daily returns to drive portfolio drift
# ===========================================================================
prices = yf.download(TICKERS, start="2020-01-01", end="2025-01-01", progress=False,
                      auto_adjust=True)["Close"].dropna()
rets = prices.pct_change().dropna()
print(f"Loaded {len(prices)} real trading days, {prices.index[0].date()} to "
      f"{prices.index[-1].date()}")

PORTFOLIO_VALUE_START = 5_000_000  # $5M account

# ===========================================================================
# 2. Simulate drift, trigger rebalance when a band is breached
# ===========================================================================
weights = pd.Series(TARGET).reindex(TICKERS)
holdings_value = weights * PORTFOLIO_VALUE_START
rebalance_dates = []
turnover_naive_total = 0
turnover_bandaware_total = 0

for date, r in rets.iterrows():
    holdings_value = holdings_value * (1 + r)
    total = holdings_value.sum()
    current_weights = holdings_value / total
    drift = current_weights - weights
    if (drift.abs() > BAND).any():
        rebalance_dates.append((date, current_weights.copy(), total))
        target_value = weights * total
        trades = target_value - holdings_value
        turnover_bandaware_total += trades.abs().sum()
        holdings_value = target_value.copy()

print(f"\nBand-based (drift > {BAND:.0%}) rebalancing triggered on {len(rebalance_dates)} "
      f"real dates over {len(rets)} trading days:")
for date, w, total in rebalance_dates:
    print(f"  {date.date()}: portfolio value ${total:,.0f}, weights before rebal: "
          + ", ".join(f"{t}={w[t]:.1%}" for t in TICKERS))

# ===========================================================================
# 3. Compare to naive monthly full-rebalance-to-target (calendar-based)
# ===========================================================================
holdings_naive = weights * PORTFOLIO_VALUE_START
monthly_dates = rets.resample("ME").apply(lambda x: x.index[-1] if len(x) else None).dropna()
prev_date = rets.index[0]
for date in rets.index:
    r = rets.loc[date]
    holdings_naive = holdings_naive * (1 + r)
    if date in monthly_dates.values:
        total = holdings_naive.sum()
        target_value = weights * total
        turnover_naive_total += (target_value - holdings_naive).abs().sum()
        holdings_naive = target_value.copy()

print(f"\nTotal turnover (band-based, {len(rebalance_dates)} events): "
      f"${turnover_bandaware_total:,.0f}")
print(f"Total turnover (naive monthly full-rebalance, ~60 events): "
      f"${turnover_naive_total:,.0f}")
print(f"Turnover reduction from band-based vs. naive monthly: "
      f"{(1 - turnover_bandaware_total/turnover_naive_total):.1%}")

# ===========================================================================
# 4. Tax-lot-aware sell selection (constructed lot data - real brokerage lot
#    data isn't publicly accessible, so this section is illustrative)
# ===========================================================================
print("\n" + "=" * 70)
print("TAX-LOT-AWARE SELL SELECTION (constructed lot data, illustrative)")
print("=" * 70)
np.random.seed(3)
lots = []
lot_id = 0
for t in TICKERS:
    for _ in range(6):
        purchase_date = pd.Timestamp("2020-01-01") + pd.Timedelta(days=int(np.random.uniform(0, 1700)))
        shares = np.random.randint(500, 3000)
        cost_basis_price = prices[t].asof(purchase_date)
        lots.append({"lot_id": lot_id, "ticker": t, "purchase_date": purchase_date,
                     "shares": shares, "cost_basis": cost_basis_price})
        lot_id += 1
lots_df = pd.DataFrame(lots)

current_prices = prices.iloc[-1]
today = prices.index[-1]
lots_df["current_price"] = lots_df["ticker"].map(current_prices)
lots_df["unrealized_pnl_per_share"] = lots_df["current_price"] - lots_df["cost_basis"]
lots_df["holding_days"] = (today - lots_df["purchase_date"]).dt.days
lots_df["long_term"] = lots_df["holding_days"] > 365
lots_df["total_unrealized_pnl"] = lots_df["unrealized_pnl_per_share"] * lots_df["shares"]

def select_lots_to_sell(ticker, shares_to_sell, lots_df):
    """Tax-aware: sell losses first (any holding period), then long-term gains,
    avoid short-term gains last."""
    candidates = lots_df[lots_df["ticker"] == ticker].copy()
    losses = candidates[candidates["unrealized_pnl_per_share"] < 0].sort_values("unrealized_pnl_per_share")
    # Within each gain bucket, sell the highest-cost-basis (smallest-gain) lots first -
    # specific-identification / HIFO logic to minimize realized taxable gain
    lt_gains = candidates[(candidates["unrealized_pnl_per_share"] >= 0) & candidates["long_term"]] \
        .sort_values("unrealized_pnl_per_share")
    st_gains = candidates[(candidates["unrealized_pnl_per_share"] >= 0) & ~candidates["long_term"]] \
        .sort_values("unrealized_pnl_per_share")
    ordered = pd.concat([losses, lt_gains, st_gains])
    selected, remaining = [], shares_to_sell
    for _, lot in ordered.iterrows():
        take = min(lot["shares"], remaining)
        selected.append((lot["lot_id"], take, lot["unrealized_pnl_per_share"] * take, lot["long_term"]))
        remaining -= take
        if remaining <= 0:
            break
    return selected

# Example: need to trim SPY by 5000 shares in a rebalance
example_ticker = "SPY"
example_shares = 3000
selection = select_lots_to_sell(example_ticker, example_shares, lots_df)
print(f"Trimming {example_shares} shares of {example_ticker} - tax-aware lot selection:")
realized_gain_taxaware = 0
for lot_id, shares_sold, pnl, is_lt in selection:
    realized_gain_taxaware += pnl
    print(f"  Lot #{lot_id}: sell {shares_sold} shares, realized P&L ${pnl:,.0f} "
          f"({'long-term' if is_lt else 'short-term'})")

# Naive FIFO comparison
fifo_lots = lots_df[lots_df["ticker"] == example_ticker].sort_values("purchase_date")
remaining, realized_gain_fifo = example_shares, 0
for _, lot in fifo_lots.iterrows():
    take = min(lot["shares"], remaining)
    realized_gain_fifo += lot["unrealized_pnl_per_share"] * take
    remaining -= take
    if remaining <= 0:
        break

print(f"\nRealized gain, tax-aware selection: ${realized_gain_taxaware:,.0f}")
print(f"Realized gain, naive FIFO selection: ${realized_gain_fifo:,.0f}")
print(f"Tax-aware selection reduces realized taxable gain by: "
      f"${realized_gain_fifo - realized_gain_taxaware:,.0f}")
