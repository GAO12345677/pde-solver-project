from __future__ import annotations

import math
from typing import Dict

import numpy as np

from services.market_data import align_close_returns, fetch_pair_history, fetch_risk_free_rate, fetch_stock_snapshot


def estimate_stock_inputs(symbol: str, lookback_days: int = 252) -> Dict[str, object]:
    snapshot = fetch_stock_snapshot(symbol, lookback_days)
    closes = np.asarray(snapshot["closes"], dtype=float)
    log_returns = np.diff(np.log(closes))
    historical_volatility = float(np.std(log_returns, ddof=1) * math.sqrt(252)) if len(log_returns) > 1 else 0.0
    drift = float(np.mean(log_returns) * 252) if len(log_returns) > 0 else 0.0
    risk_free = fetch_risk_free_rate()
    return {
        "symbol": snapshot["symbol"],
        "spot": snapshot["spot"],
        "historical_volatility": historical_volatility,
        "drift": drift,
        "risk_free_rate": risk_free["annual_rate"],
        "history_preview": snapshot["history_preview"],
        "data_source": "yfinance",
    }


def estimate_pair_inputs(symbol1: str, symbol2: str, lookback_days: int = 252) -> Dict[str, object]:
    pair = fetch_pair_history(symbol1, symbol2, lookback_days)
    left_returns, right_returns = align_close_returns(symbol1, symbol2, lookback_days)
    correlation = float(np.corrcoef(left_returns.to_numpy(), right_returns.to_numpy())[0, 1])
    return {
        "symbol1": pair["symbol1"]["symbol"],
        "symbol2": pair["symbol2"]["symbol"],
        "spot1": pair["symbol1"]["spot"],
        "spot2": pair["symbol2"]["spot"],
        "historical_volatility1": estimate_stock_inputs(symbol1, lookback_days)["historical_volatility"],
        "historical_volatility2": estimate_stock_inputs(symbol2, lookback_days)["historical_volatility"],
        "correlation": correlation,
        "data_source": "yfinance",
    }
