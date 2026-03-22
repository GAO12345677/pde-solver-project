# Real Finance Integration Todo

This checklist upgrades the finance module from parameter demos to market-data-driven analysis.

## Phase 1 - Market Data Layer

- [x] Install a no-key prototype provider for live market data (`yfinance`).
- [x] Add a market-data service layer under `services/market_data.py`.
- [x] Fetch stock history and latest price (`spot`).
- [x] Fetch option expiries and option-chain snapshots.
- [x] Fetch a risk-free proxy rate for model pricing.

## Phase 2 - Parameter Estimation

- [x] Add `services/finance_features.py`.
- [x] Estimate historical volatility from log returns.
- [x] Estimate correlation between two assets from aligned returns.
- [x] Expose stock/pair estimation endpoints.

## Phase 3 - Model vs Market Comparison

- [x] Add an option comparison endpoint that returns:
  - model price
  - market price
  - implied volatility
  - pricing gap
- [x] Support sensible defaults when expiry or strike are omitted.
- [x] Add transparent notes when a value is approximated.

## Phase 4 - Frontend Integration

- [x] Add market-data input controls on the Finance page.
- [x] Show:
  - latest spot
  - historical volatility
  - risk-free rate
  - implied volatility
  - model price
  - market price
  - pricing gap
- [x] Add a clear disclaimer block:
  - model-based estimate
  - not investment advice
  - for learning and analysis only

## Phase 5 - Validation

- [x] Add backend tests with mocked market-data responses.
- [x] Add frontend tests for the market-comparison flow.
- [x] Update README and QUICKSTART with live-data notes.
