# A-Share Finance Roadmap

This checklist tracks the A-share expansion under the `Finance` module.

## Phase 1 - A-share stock analysis

- [x] Add an A-share market-data service based on `akshare`.
- [x] Normalize 6-digit A-share stock codes and expose display symbols such as `000001.SZ`.
- [x] Add exchange-session awareness for Shanghai time.
- [x] Expose `GET /finance/ashare/stock/{symbol}`.
- [x] Show latest quote, last trade date, quote timestamp, and market status on the Finance page.
- [x] Show annualized drift and `HV20 / HV60 / HV252`.
- [x] Add a recent-close trend chart and reliability notes.
- [x] Add backend and frontend tests.

## Phase 2 - A-share pair analysis

- [x] Expose `GET /finance/ashare/pair`.
- [x] Add a frontend pair-comparison panel.
- [x] Show rolling correlation and dual-price trend comparison.

## Phase 3 - A-share options and ETFs

- [x] Choose the first domestic derivative target:
  - ETF options
  - index options
- [x] Add a first ETF-options panel based on `50ETF` snapshots.
- [x] Separate `latest price`, `theoretical value`, `implied volatility`, and `pricing gap`.
- [x] Add quote-time and underlying-time labels for option snapshots.
- [x] Add expiry and strike selectors to the frontend.
- [x] Add index options as the second domestic derivative target.

## Phase 4 - stronger realism

- [ ] Add provider abstraction so `akshare` can be swapped with `Tushare Pro`.
- [ ] Add local caching and request backoff.
- [ ] Distinguish `latest traded price`, `latest close`, and delayed snapshot values more explicitly.
- [ ] Add a dedicated comparison page for historical model-vs-market tracking.
