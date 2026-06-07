# PDE Solver Project

This project is a course-oriented PDE solving platform that combines:

- parameterized numerical solvers
- feature extraction and algorithm selection
- natural-language problem parsing
- API and frontend demo pages
- a finance practice module for stock dynamics and option pricing

It is designed for demos, reports, and system integration experiments rather than production scientific computing.

## 3D Capability Matrix

Current 3D support:

- `heat3d`: `fdm`, `fvm`, `fem`
- `wave3d`: `fdm`, `fem`, `spectral`
- `poisson3d`: `fdm`, `fem`, `bem`

Notes:

- `heat3d` uses zero-Dirichlet manufactured-solution baselines.
- `wave3d` now includes FDM, FEM, and spectral manufactured-solution baselines.
- `poisson3d` includes teaching-style FEM and BEM baselines in addition to FDM.

## Main Features

- FastAPI backend with Swagger docs
- React + Vite frontend
- algorithm recommendation strategies:
  - `static_rf`
  - `static_xgb`
  - `dynamic_rl`
  - `mlp_nn`
  - `gnn_selector`
- direct equation solving and natural-language auto-solve flows
- benchmark and evaluation utilities
- finance practice pages:
  - `Stocks`: path simulation, terminal distribution, and risk summary
  - `A-Shares`: live A-share snapshot, market-session status, recent close trend, and historical volatility
  - `Options 1D`: Black-Scholes price curve, payoff curve, and Greeks
  - `Options 2D`: two-asset basket-style price surface with correlation input

## Finance Module

The finance module is positioned as an application extension, not a replacement for the thesis mainline.

It is meant to show that the platform can be extended from physical PDE cases into financial modeling demos.

Current finance support:

- frontend page: [http://127.0.0.1:8001/app/#finance](http://127.0.0.1:8001/app/#finance)
- `Stocks`:
  - geometric-Brownian-motion baseline
  - A-share live analysis with market-session awareness
  - A-share pair analysis with correlation, dual-price trend, and rolling correlation
  - sample paths
  - terminal-price histogram
  - summary statistics
- `Options 1D`:
  - Black-Scholes 1D call/put pricing
  - payoff visualization
  - Greeks: `delta`, `gamma`, `theta`, `vega`, `rho`
  - A-share `50ETF` / `300ETF` option snapshots with expiry and strike selectors
  - A-share index-option snapshots for `HS300`, `SSE50`, and `CSI1000`
  - Greeks and theory-vs-market reference
- `Options 2D`:
  - two-asset basket-style approximate surface
  - asset correlation control
  - 2D heatmap visualization

Finance API endpoints:

- `POST /finance/stocks/simulate`
- `POST /finance/options/black_scholes_1d`
- `POST /finance/options/black_scholes_2d`
- `GET /finance/ashare/stock/{symbol}`
- `GET /finance/ashare/pair`
- `POST /finance/ashare/etf_option`
- `POST /finance/ashare/index_option`
- `GET /finance/market/stock/{symbol}`
- `GET /finance/market/pair`
- `POST /finance/options/compare_market`

Live market-data comparison support:

- A-share stock snapshot with:
  - Shanghai-time market clock
  - last trade date
  - quote timestamp
  - `HV20 / HV60 / HV252`
- latest stock `spot` fetched from market history
- historical volatility estimated from log returns
- risk-free proxy rate fetched for pricing inputs
- option-chain snapshot lookup for market comparison
- side-by-side display of:
  - `model price`
  - `market price`
  - `implied volatility`
  - `pricing gap`

Reliability note:

- this is a model-based analysis workflow built on a prototype market-data source
- A-share quotes are constrained by exchange trading sessions and should be interpreted together with their timestamps
- it is useful for demos, learning, and comparison experiments
- it is not investment advice and should not be presented as a production trading engine

## Quick Start

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

GPU note:

- The project now declares `nvidia-ml-py` instead of the deprecated `pynvml` package name for NVIDIA hardware detection.

Install frontend dependencies:

```powershell
cd static
npm install
npm run build
cd ..
```

Start the project:

```powershell
python main.py
```

If you use the project virtual environment:

```powershell
.\.venv\Scripts\python.exe main.py
```

Open:

- frontend: [http://127.0.0.1:8001/app/](http://127.0.0.1:8001/app/)
- swagger: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- health: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

## Testing

Run the standard project checks:

```powershell
.\run_tests.ps1
```

Run targeted 3D API tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_heat3d_api.py tests\test_poisson3d_api.py tests\test_websocket_api.py -q
```

Run targeted finance API tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_finance_api.py -q
```

Run frontend finance page tests:

```powershell
cd static
npm run test -- --run FinancePage
```

Run the frontend build:

```powershell
cd static
npm run build
```

## Open Source Statement

This repository is released under the [MIT License](LICENSE) as the public code artifact for academic citation and reproducibility.

If you refer to this project in a paper, cite the GitHub repository:

- repository: [https://github.com/GAO12345677/pde-solver-project](https://github.com/GAO12345677/pde-solver-project)
- citation metadata: [CITATION.cff](CITATION.cff)

## Documentation

- quick usage guide: [QUICKSTART.md](QUICKSTART.md)
- API guide: [docs/API_GUIDE.md](docs/API_GUIDE.md)
- submission notes: [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md)
