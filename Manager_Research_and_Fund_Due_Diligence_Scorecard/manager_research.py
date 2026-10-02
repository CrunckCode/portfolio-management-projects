"""
Manager Research and Fund Due Diligence Scorecard
=====================================================
Real monthly return data for a peer group of 12 real large-cap growth mutual
funds/ETFs, scored on risk-adjusted performance metrics, ranked into a composite
scorecard, and cross-checked with a returns-based style regression (Sharpe-style
analysis) to flag any fund whose actual factor exposure has drifted from its stated
large-cap-growth mandate.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression

PEER_GROUP = ["VUG", "SCHG", "MGK", "IWF", "SPYG", "QQQ", "FTEC", "VONG", "IVW", "JGRO", "MOAT", "SPHQ"]
BENCHMARK = "SPY"
FACTOR_PROXIES = {"Market": "SPY", "Size": "IWM", "Value": "IWD", "Momentum": "MTUM"}

# ===========================================================================
# 1. Real monthly returns
# ===========================================================================
all_tickers = list(set(PEER_GROUP + [BENCHMARK] + list(FACTOR_PROXIES.values())))
prices = yf.download(all_tickers, start="2019-01-01", end="2025-01-01", progress=False,
                      auto_adjust=True)["Close"].dropna()
monthly = prices.resample("ME").last().pct_change().dropna()
print(f"Loaded {len(monthly)} real monthly return observations, "
      f"{monthly.index[0].date()} to {monthly.index[-1].date()}")

# ===========================================================================
# 2. Risk-adjusted performance metrics
# ===========================================================================
rf_monthly = 0.02 / 12
results = []
bench_ret = monthly[BENCHMARK]
for fund in PEER_GROUP:
    r = monthly[fund]
    ann_ret = r.mean() * 12
    ann_vol = r.std() * np.sqrt(12)
    sharpe = (ann_ret - 0.02) / ann_vol
    downside = r[r < 0]
    sortino = (ann_ret - 0.02) / (downside.std() * np.sqrt(12)) if len(downside) > 1 else np.nan
    cum = (1 + r).cumprod()
    max_dd = (cum / cum.cummax() - 1).min()
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else np.nan
    up_months = bench_ret > 0
    down_months = bench_ret < 0
    up_capture = (r[up_months].mean() / bench_ret[up_months].mean()) if up_months.sum() > 0 else np.nan
    down_capture = (r[down_months].mean() / bench_ret[down_months].mean()) if down_months.sum() > 0 else np.nan
    results.append({
        "Fund": fund, "Ann_Return": ann_ret, "Ann_Vol": ann_vol, "Sharpe": sharpe,
        "Sortino": sortino, "Max_DD": max_dd, "Calmar": calmar,
        "Up_Capture": up_capture, "Down_Capture": down_capture,
    })

df = pd.DataFrame(results).set_index("Fund")
print("\n" + "=" * 90)
print("RISK-ADJUSTED PERFORMANCE METRICS (real data, 2019-2024)")
print("=" * 90)
print(df.round(3).to_string())

# ===========================================================================
# 3. Composite scorecard (z-scored, weighted)
# ===========================================================================
def zscore(s):
    return (s - s.mean()) / s.std()

df["Style_Drift_Penalty"] = 0  # filled in after style regression below

score_components = pd.DataFrame({
    "Sharpe_Z": zscore(df["Sharpe"]),
    "Sortino_Z": zscore(df["Sortino"]),
    "Calmar_Z": zscore(df["Calmar"]),
    "DownCapture_Z": -zscore(df["Down_Capture"]),  # lower down-capture is better -> flip sign
})
df["Composite_Score"] = score_components.mean(axis=1)

# ===========================================================================
# 4. Returns-based style analysis (Sharpe-style regression) - infer real factor
#    exposure vs. stated large-cap-growth mandate
# ===========================================================================
print("\n" + "=" * 90)
print("RETURNS-BASED STYLE ANALYSIS (regression on Market/Size/Value/Momentum factors)")
print("=" * 90)
factor_rets = monthly[list(FACTOR_PROXIES.values())]
style_results = {}
for fund in PEER_GROUP:
    y = monthly[fund].values
    X = factor_rets.values
    reg = LinearRegression(positive=False).fit(X, y)
    r2 = reg.score(X, y)
    style_results[fund] = dict(zip(FACTOR_PROXIES.keys(), reg.coef_))
    style_results[fund]["R2"] = r2
    style_results[fund]["Alpha_ann"] = reg.intercept_ * 12

style_df = pd.DataFrame(style_results).T
print(style_df.round(3).to_string())

# Style drift flag: a "growth" fund should load positively on Market, near-zero/negative
# on Value (growth is the opposite of value), and should NOT show a large unexplained
# Size tilt if it claims to be large-cap
style_df["Value_Tilt_Flag"] = style_df["Value"] > 0.15  # unexpectedly value-tilted for a growth fund
style_df["Size_Tilt_Flag"] = style_df["Size"].abs() > 0.15  # unexpected small-cap drift
drift_funds = style_df[style_df["Value_Tilt_Flag"] | style_df["Size_Tilt_Flag"]]
print(f"\nFunds showing style drift from stated large-cap-growth mandate: "
      f"{list(drift_funds.index)}")

for fund in drift_funds.index:
    df.loc[fund, "Style_Drift_Penalty"] = -0.5  # penalize composite score

df["Composite_Score"] += df["Style_Drift_Penalty"]

# ===========================================================================
# 5. Final ranking
# ===========================================================================
ranked = df.sort_values("Composite_Score", ascending=False)
print("\n" + "=" * 90)
print("FINAL MANAGER RESEARCH SCORECARD (ranked)")
print("=" * 90)
print(ranked[["Sharpe", "Sortino", "Calmar", "Down_Capture", "Style_Drift_Penalty",
              "Composite_Score"]].round(3).to_string())

top_fund = ranked.index[0]
bottom_fund = ranked.index[-1]
print(f"\nTop-ranked: {top_fund}  |  Bottom-ranked: {bottom_fund}")
