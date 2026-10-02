# Portfolio Management Projects

5 Python projects on portfolio management. Each folder has the code, any output charts or data files, and a README covering what it does, the data, the method, results and honest limitations.

All projects use real public market, rate or filing data wherever possible, built with AI assistance (Claude Code) as a build-and-learn exercise and checked against known results. Each README states what was real, what was synthetic and what the model cannot do.

| Project | What it does |
|---|---|
| [Currency Hedging Overlay for International Portfolios](Currency_Hedging_Overlay_for_International_Portfolios) | Decomposes the real USD returns of the Developed ex-US (EFA) and Emerging Markets (VWO) mandates into real local-currency equity return and real FX return, computes the real forward-hedging cost via covered interest parity, and compares hedged vs. |
| [Liability-Driven Investment (LDI) / Pension ALM Model](Liability_Driven_Investment_Pension_ALM_Model) | Builds an illustrative 30-year pension liability cash-flow schedule, discounts it off the real live Treasury curve to get real liability PV/duration, constructs a duration-matched LDI asset portfolio vs. |
| [Manager Research and Fund Due Diligence Scorecard](Manager_Research_and_Fund_Due_Diligence_Scorecard) | A quantitative manager-screening scorecard across a 12-fund large-cap-growth peer group: risk-adjusted performance metrics (Sharpe, Sortino, Calmar, up/down-capture), a composite ranking, and a returns-based style regression (Sharpe-style analysis) that checks whether each fund's actual factor exposure matches its stated growth mandate. |
| [Multi-Asset Risk Parity and Factor-Based Allocation Engine](Multi_Asset_Risk_Parity_and_Factor_Based_Allocation_Engine) | A risk-parity (equal risk contribution) portfolio optimizer across 5 real asset-class proxies, compared against a mean-variance-optimal portfolio and a 60/40 benchmark, plus a cross-asset momentum/low-vol factor tilt layered on top of the risk-parity base - backtested on 10 years of real daily data with explicit focus on three real historical drawdown periods. |
| [Portfolio Rebalancing and Tax-Aware Trade Optimization Tool](Portfolio_Rebalancing_and_Tax_Aware_Trade_Optimization_Tool) | A drift-band rebalancing engine (rebalance only when an asset drifts beyond a tolerance band, not on a fixed calendar) simulated over real historical daily returns for a 4-asset model portfolio, quantifying the turnover reduction vs. |
