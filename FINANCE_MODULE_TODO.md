# Finance Module Todo

This roadmap keeps the thesis mainline focused on `heat / wave / poisson` while adding finance as a separate practice module.

## Positioning

- Main thesis line: PDE solving, algorithm selection, and result analysis for physical equations.
- New application module: `Finance`
- Finance submodules:
  - `Stocks`: stock dynamics and stochastic process visualization
  - `Options`: option pricing and Black-Scholes style PDE demos

## Phase 1 - Module Shell

- [x] Define the Finance module scope and split it into `Stocks` and `Options`.
- [ ] Add a top-level `Finance` entry to the frontend navigation.
- [ ] Create a Finance landing page with bilingual explanations.
- [ ] Explain how the finance module relates to the existing PDE platform.

Deliverable:
- Users can open a dedicated finance page from the main app.

## Phase 2 - Stocks First Version

- [ ] Add a `Stocks` panel with the following inputs:
  - initial price
  - expected drift
  - volatility
  - horizon
  - time steps
  - number of Monte Carlo paths
- [ ] Implement a simple stock-path simulator.
- [ ] Display:
  - sample paths
  - terminal-price summary
  - mean / standard deviation
  - short Chinese explanations for each metric
- [ ] Add frontend tests for the stocks panel.

Deliverable:
- A beginner-friendly stock dynamics demo that does not require prior option knowledge.

## Phase 3 - Options First Version

- [ ] Add an `Options` panel with bilingual teaching notes.
- [ ] Introduce the meaning of:
  - strike price
  - maturity
  - volatility
  - risk-free rate
- [ ] Implement a first `Black-Scholes 1D` demo path.
- [ ] Show:
  - price curve
  - payoff intuition
  - parameter summary
- [ ] Add frontend tests for the options panel.

Deliverable:
- A clean entry-level option-pricing demo for academic presentation.

## Phase 4 - Backend Integration

- [ ] Add finance-specific backend routes under `/finance/...`.
- [ ] Move local demo logic into backend services when the API shape stabilizes.
- [ ] Add backend tests for stocks and options endpoints.
- [ ] Add route docs to README / QUICKSTART.

Deliverable:
- Frontend finance panels use real backend APIs instead of only local mock/demo logic.

## Phase 5 - Research-Grade Extension

- [ ] Stocks:
  - joint two-stock simulation
  - correlation input
  - 2D distribution heatmap
- [ ] Options:
  - `Black-Scholes 2D`
  - method comparison
  - Greeks summary
- [ ] Add benchmark and runtime comparison cards.
- [ ] Add links from finance results back to the main benchmark page.

Deliverable:
- Finance becomes a strong application case without replacing the thesis core.

## Recommended Execution Order

1. Finish Phase 1 first.
2. Build the first `Stocks` demo.
3. Add the first `Options` demo.
4. Stabilize API contracts.
5. Expand into 2D and benchmark comparisons.
