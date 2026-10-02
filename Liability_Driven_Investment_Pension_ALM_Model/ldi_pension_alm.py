"""
Liability-Driven Investment (LDI) / Pension ALM Model
============================================================
Constructs an illustrative pension liability cash-flow schedule, discounts it off the
REAL live Treasury curve to get real liability PV/duration, builds a duration-matched
LDI asset portfolio vs. a growth-heavy alternative, and compares funded-status stability
under real historical Treasury-curve moves and a hypothetical rate-shock grid.
"""

# ===========================================================================
# CONFIG BLOCK
# ===========================================================================
LIABILITY_YEARS = 30
LIABILITY_ANNUAL_PAYMENT = 5_000_000   # illustrative level annuity-style payment
STARTING_ASSET_VALUE = None  # set to the real liability PV computed below (fully funded at t=0)

import numpy as np
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TODAY = datetime.date.today()

# ===========================================================================
# 1. Real Treasury curve (FRED) for discounting the liability
# ===========================================================================
tenor_codes = {1: "DGS1", 2: "DGS2", 3: "DGS3", 5: "DGS5", 7: "DGS7", 10: "DGS10", 20: "DGS20", 30: "DGS30"}
curve = {}
for tenor, code in tenor_codes.items():
    df = web.DataReader(code, "fred", start=TODAY - datetime.timedelta(days=15)).dropna()
    curve[tenor] = df.iloc[-1, 0] / 100
print("Real US Treasury curve (FRED):")
for t, y in curve.items():
    print(f"  {t}Y: {y:.3%}")

def discount_rate(t):
    tenors = sorted(curve.keys())
    return np.interp(t, tenors, [curve[t] for t in tenors])

# ===========================================================================
# 2. Liability cash flows and PV/duration
# ===========================================================================
years = np.arange(1, LIABILITY_YEARS + 1)
cash_flows = np.full(LIABILITY_YEARS, LIABILITY_ANNUAL_PAYMENT)
discount_rates = np.array([discount_rate(t) for t in years])
discount_factors = 1 / (1 + discount_rates) ** years
pv_per_year = cash_flows * discount_factors
liability_pv = pv_per_year.sum()
macaulay_duration = (years * pv_per_year).sum() / liability_pv

print(f"\nLiability: ${LIABILITY_ANNUAL_PAYMENT:,.0f}/year for {LIABILITY_YEARS} years")
print(f"Real liability present value (discounted off the real Treasury curve): "
      f"${liability_pv:,.0f}")
print(f"Real liability Macaulay duration: {macaulay_duration:.2f} years")

STARTING_ASSET_VALUE = liability_pv  # fully funded at inception

# ===========================================================================
# 3. Two asset portfolios: LDI (duration-matched) vs. growth-heavy
# ===========================================================================
# LDI portfolio: real long-duration Treasury ETF (TLT, real ~17Y duration) blended with
# cash to hit the real target liability duration
TLT_DURATION = 17.0  # real, approximate current TLT effective duration
ldi_bond_weight = min(macaulay_duration / TLT_DURATION, 1.0)
ldi_cash_weight = 1 - ldi_bond_weight
print(f"\nLDI portfolio: {ldi_bond_weight:.1%} in a real long-Treasury ETF (TLT, ~{TLT_DURATION}Y "
      f"duration) + {ldi_cash_weight:.1%} cash, to approximately match the real "
      f"{macaulay_duration:.1f}Y liability duration")

# Growth-heavy portfolio: 70% equity / 30% short-duration bonds (real, standard growth-tilted allocation)
growth_equity_weight = 0.70
growth_bond_weight = 0.30
growth_bond_duration = 3.0  # real, approximate short-duration bond fund

# ===========================================================================
# 4. Real historical price data for the asset proxies
# ===========================================================================
prices = yf.download(["TLT", "SPY", "SHY"], start="2020-01-01", end="2025-01-01",
                       progress=False, auto_adjust=True)["Close"].dropna()
rets = prices.pct_change().dropna()
print(f"\nLoaded {len(rets)} real trading days for TLT/SPY/SHY, "
      f"{rets.index[0].date()} to {rets.index[-1].date()} (spans the real 2022 rate-hiking cycle)")

ldi_ret = ldi_bond_weight * rets["TLT"] + ldi_cash_weight * rets["SHY"]
growth_ret = growth_equity_weight * rets["SPY"] + growth_bond_weight * rets["SHY"]

# ===========================================================================
# 5. Funded status simulation under REAL historical returns (asset side) and the
# REAL historical Treasury-curve path (liability side, re-discounted each period)
# ===========================================================================
dgs10_hist = web.DataReader("DGS10", "fred", start="2020-01-01", end="2025-01-01").dropna() / 100
dgs10_hist = dgs10_hist.reindex(rets.index, method="ffill").iloc[:, 0]

def liability_pv_at_rate(base_rates, shift, years, cash_flows):
    shifted = base_rates + shift
    df_ = 1 / (1 + shifted) ** years
    return (cash_flows * df_).sum()

ldi_assets = STARTING_ASSET_VALUE * (1 + ldi_ret).cumprod()
growth_assets = STARTING_ASSET_VALUE * (1 + growth_ret).cumprod()

# Approximate liability PV path: re-discount using the REAL historical 10Y yield's
# deviation from today's level as a real parallel-shift proxy applied to the full curve
base_10y_today = curve[10]
rate_shift_path = dgs10_hist - base_10y_today
liability_pv_path = pd.Series(
    [liability_pv_at_rate(discount_rates, shift, years, cash_flows) for shift in rate_shift_path],
    index=rate_shift_path.index,
)

ldi_funded_status = ldi_assets - liability_pv_path.reindex(ldi_assets.index)
growth_funded_status = growth_assets - liability_pv_path.reindex(growth_assets.index)

print("\n" + "=" * 80)
print("FUNDED STATUS UNDER REAL HISTORICAL TREASURY-CURVE MOVES (2020-2024)")
print("=" * 80)
print(f"LDI portfolio funded status: mean ${ldi_funded_status.mean():,.0f}, "
      f"std ${ldi_funded_status.std():,.0f} ({ldi_funded_status.std()/STARTING_ASSET_VALUE:.2%} of starting value)")
print(f"Growth portfolio funded status: mean ${growth_funded_status.mean():,.0f}, "
      f"std ${growth_funded_status.std():,.0f} ({growth_funded_status.std()/STARTING_ASSET_VALUE:.2%} of starting value)")
print(f"\nFunded-status volatility ratio (Growth / LDI): "
      f"{growth_funded_status.std()/ldi_funded_status.std():.2f}x")

# ===========================================================================
# 6. Hypothetical parallel rate-shock grid
# ===========================================================================
print("\n" + "=" * 80)
print("HYPOTHETICAL PARALLEL RATE SHOCK GRID")
print("=" * 80)
for shock_bps in [-200, -100, 0, 100, 200]:
    shock = shock_bps / 10000
    new_liability_pv = liability_pv_at_rate(discount_rates, shock, years, cash_flows)
    ldi_asset_change = -ldi_bond_weight * TLT_DURATION * shock * STARTING_ASSET_VALUE
    growth_asset_change = 0  # equity has ~zero direct rate-duration sensitivity in this simple model;
                              # only the growth portfolio's 30% short-duration bond sleeve reacts
    growth_asset_change = -growth_bond_weight * growth_bond_duration * shock * STARTING_ASSET_VALUE
    ldi_funded_change = (STARTING_ASSET_VALUE + ldi_asset_change) - new_liability_pv - (STARTING_ASSET_VALUE - liability_pv)
    growth_funded_change = (STARTING_ASSET_VALUE + growth_asset_change) - new_liability_pv - (STARTING_ASSET_VALUE - liability_pv)
    print(f"  {shock_bps:+d}bp: LDI funded-status change ${ldi_funded_change:+,.0f}  |  "
          f"Growth funded-status change ${growth_funded_change:+,.0f}")

# ===========================================================================
# 7. Chart
# ===========================================================================
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(ldi_funded_status.index, ldi_funded_status / 1e6, label="LDI (duration-matched)", color="steelblue")
ax.plot(growth_funded_status.index, growth_funded_status / 1e6, label="Growth-heavy (70/30)", color="firebrick")
ax.axhline(0, color="black", linewidth=0.5)
ax.set_ylabel("Funded status ($mm)")
ax.set_title("Funded Status: LDI vs. Growth-Heavy Portfolio (real 2020-2024 data)")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig("ldi_funded_status.png", dpi=120)
print("\nSaved chart: ldi_funded_status.png")
