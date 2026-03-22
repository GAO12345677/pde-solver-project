# Quick Start

## 1. What This Project Supports

Numerical PDE demos currently include:

- `heat1d`
- `heat2d`
- `heat3d`
- `wave1d`
- `wave2d`
- `wave3d`
- `poisson1d`
- `poisson3d`
- `poisson2d_nonlinear`

3D algorithm support:

- `heat3d`: `fdm`, `fvm`, `fem`
- `wave3d`: `fdm`, `fem`, `spectral`
- `poisson3d`: `fdm`, `fem`, `bem`

Finance practice support:

- `Stocks`:
  - A-share live stock snapshot
  - A-share pair correlation analysis
  - Shanghai market-session label
  - latest quote timestamp
  - recent close trend
  - dual-price trend and rolling correlation
  - `HV20 / HV60 / HV252`
  - stock-path simulation
  - terminal distribution
  - mean / std / percentile summary
  - live-market parameter estimation for `spot` and historical volatility
- `Options 1D`:
  - Black-Scholes price curve
  - payoff curve
  - Greeks summary
  - model-vs-market comparison
  - 50ETF / 300ETF option market snapshot with expiry and strike selectors
  - HS300 / SSE50 / CSI1000 index-option snapshot
  - option Greeks and theoretical-value comparison
- `Options 2D`:
  - two-asset basket-style approximate surface
  - correlation input
  - 2D heatmap

## 2. Environment

Recommended:

- Windows 10/11
- Python 3.10+
- Node.js 18+

## 3. Install

Backend:

```powershell
pip install -r requirements.txt
```

Note:

- `requirements.txt` uses `nvidia-ml-py` for NVIDIA hardware detection. If you still have the old `pynvml` package installed, uninstalling it will remove the deprecation warning shown by PyTorch.

Frontend:

```powershell
cd static
npm install
cd ..
```

## 4. Build Frontend

```powershell
cd static
npm run build
cd ..
```

## 5. Start the App

```powershell
python main.py
```

Or with the project venv:

```powershell
.\.venv\Scripts\python.exe main.py
```

## 6. Open the App

- frontend: [http://127.0.0.1:8001/app/](http://127.0.0.1:8001/app/)
- finance page: [http://127.0.0.1:8001/app/#finance](http://127.0.0.1:8001/app/#finance)
- swagger: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- health: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

## 7. Run Tests

Recommended one-command entry:

```powershell
.\run_tests.ps1
```

Targeted backend verification:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_heat3d_api.py tests\test_poisson3d_api.py tests\test_websocket_api.py -q
```

Finance backend verification:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_finance_api.py -q
```

Frontend build verification:

```powershell
cd static
npm run build
```

Frontend page test:

```powershell
cd static
npm run test -- --run SolvePage
```

Finance page test:

```powershell
cd static
npm run test -- --run FinancePage
```

## 8. Live Finance Endpoints

- `GET /finance/ashare/stock/000001`
- `GET /finance/ashare/pair?symbol1=000001&symbol2=600519`
- `POST /finance/ashare/etf_option`
- `GET /finance/market/stock/{symbol}`
- `GET /finance/market/pair?symbol1=AAPL&symbol2=MSFT`
- `POST /finance/options/compare_market`
- `POST /finance/stocks/simulate`
- `POST /finance/options/black_scholes_1d`
- `POST /finance/options/black_scholes_2d`

The Finance page now separates:

- `model price`: value produced by the Black-Scholes model
- `market price`: observed option-chain quote
- `implied volatility`: volatility backed out from the market quote
- `pricing gap`: `model price - market price`

Reliability note:

- these values are for learning and analysis
- they are not investment advice
- A-share quotes should be read together with market-session status and quote timestamps
- live quotes, rates, and approximations can differ from exchange-quality data

## 9. Finance API Examples

Stock simulation:

```json
{
  "initial_price": 100,
  "drift": 0.08,
  "volatility": 0.2,
  "horizon": 1.0,
  "steps": 252,
  "paths": 2000
}
```

Black-Scholes 1D:

```json
{
  "spot": 100,
  "strike": 105,
  "maturity": 0.5,
  "volatility": 0.25,
  "rate": 0.02
}
```

Black-Scholes 2D:

```json
{
  "spot1": 100,
  "spot2": 95,
  "strike": 100,
  "maturity": 0.5,
  "volatility1": 0.25,
  "volatility2": 0.22,
  "rate": 0.02,
  "correlation": 0.3,
  "grid_size": 16
}
```

Market comparison:

```json
{
  "symbol": "AAPL",
  "option_type": "call",
  "maturity_years": 0.25,
  "use_market_iv": true
}
```

## 10. Example 3D Solve Payload

```json
{
  "equation_type": "poisson3d",
  "algorithm_key": "fem",
  "nx": 9,
  "ny": 9,
  "nz": 9,
  "Lx": 1.0,
  "Ly": 1.0,
  "Lz": 1.0,
  "bc_type": "dirichlet",
  "left_bc": 0.0,
  "right_bc": 0.0
}
```
