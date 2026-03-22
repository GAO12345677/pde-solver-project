from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


class MarketDataError(RuntimeError):
    pass


@dataclass
class OptionQuote:
    symbol: str
    expiry: str
    strike: float
    option_type: str
    bid: float
    ask: float
    last_price: float
    midpoint: float
    implied_volatility: float | None
    volume: int | None
    open_interest: int | None


def fetch_stock_snapshot(symbol: str, lookback_days: int = 252) -> Dict[str, Any]:
    ticker = _ticker(symbol)
    history = ticker.history(period="18mo", auto_adjust=False)
    if history.empty:
        raise MarketDataError(f"No history available for symbol {symbol}.")

    close = history["Close"].dropna()
    if close.empty:
        raise MarketDataError(f"No close prices available for symbol {symbol}.")

    latest_close = float(close.iloc[-1])
    recent = close.tail(max(int(lookback_days), 30))
    preview = [
        {
            "date": index.strftime("%Y-%m-%d"),
            "close": float(value),
        }
        for index, value in recent.tail(30).items()
    ]

    return {
        "symbol": symbol.upper(),
        "spot": latest_close,
        "currency": _safe_info_value(ticker, "currency"),
        "exchange": _safe_info_value(ticker, "exchange"),
        "history_preview": preview,
        "closes": recent.reset_index(drop=True).tolist(),
    }


def fetch_pair_history(symbol1: str, symbol2: str, lookback_days: int = 252) -> Dict[str, Any]:
    left = fetch_stock_snapshot(symbol1, lookback_days)
    right = fetch_stock_snapshot(symbol2, lookback_days)
    return {
        "symbol1": left,
        "symbol2": right,
    }


def fetch_option_market_snapshot(
    symbol: str,
    *,
    expiry: str | None = None,
    strike: float | None = None,
    option_type: str = "call",
) -> Dict[str, Any]:
    ticker = _ticker(symbol)
    expiries = list(ticker.options or [])
    if not expiries:
        raise MarketDataError(f"No option expiries available for symbol {symbol}.")

    selected_expiry = expiry if expiry in expiries else expiries[0]
    chain = ticker.option_chain(selected_expiry)
    frame = chain.calls if option_type.lower() == "call" else chain.puts
    if frame is None or frame.empty:
        raise MarketDataError(f"No {option_type} option chain available for {symbol} on {selected_expiry}.")

    if strike is None:
        spot = float(fetch_stock_snapshot(symbol)["spot"])
        selected_row = frame.iloc[(frame["strike"] - spot).abs().argsort().iloc[0]]
    else:
        selected_row = frame.iloc[(frame["strike"] - float(strike)).abs().argsort().iloc[0]]

    bid = _to_float(selected_row.get("bid"))
    ask = _to_float(selected_row.get("ask"))
    last_price = _to_float(selected_row.get("lastPrice"))
    midpoint = _choose_midpoint(bid, ask, last_price)
    quote = OptionQuote(
        symbol=str(selected_row.get("contractSymbol", "")),
        expiry=selected_expiry,
        strike=float(selected_row.get("strike")),
        option_type=option_type.lower(),
        bid=bid,
        ask=ask,
        last_price=last_price,
        midpoint=midpoint,
        implied_volatility=_to_optional_float(selected_row.get("impliedVolatility")),
        volume=_to_optional_int(selected_row.get("volume")),
        open_interest=_to_optional_int(selected_row.get("openInterest")),
    )

    return {
        "underlying": symbol.upper(),
        "available_expiries": expiries,
        "quote": quote.__dict__,
    }


def fetch_risk_free_rate() -> Dict[str, Any]:
    ticker = _ticker("^IRX")
    history = ticker.history(period="1mo", auto_adjust=False)
    if history.empty or history["Close"].dropna().empty:
        # fallback fixed demo rate if live quote is unavailable
        return {"symbol": "^IRX", "annual_rate": 0.02, "source": "fallback_demo_rate"}

    latest_close = float(history["Close"].dropna().iloc[-1])
    # ^IRX is quoted roughly in percent terms
    return {"symbol": "^IRX", "annual_rate": latest_close / 100.0, "source": "yfinance_^IRX"}


def align_close_returns(symbol1: str, symbol2: str, lookback_days: int = 252) -> Tuple[pd.Series, pd.Series]:
    left = _ticker(symbol1).history(period="18mo", auto_adjust=False)["Close"].dropna()
    right = _ticker(symbol2).history(period="18mo", auto_adjust=False)["Close"].dropna()
    if left.empty or right.empty:
        raise MarketDataError("Not enough price history to compute correlation.")

    joined = pd.concat([left.rename("left"), right.rename("right")], axis=1, join="inner").dropna().tail(max(int(lookback_days), 30))
    if len(joined) < 10:
        raise MarketDataError("Not enough overlapping observations to compute correlation.")

    log_returns = pd.DataFrame(
        {
            "left": np.log(joined["left"] / joined["left"].shift(1)),
            "right": np.log(joined["right"] / joined["right"].shift(1)),
        }
    ).dropna()
    return log_returns["left"], log_returns["right"]


def _ticker(symbol: str):
    try:
        return yf.Ticker(symbol)
    except Exception as exc:  # noqa: BLE001
        raise MarketDataError(f"Failed to create market-data ticker for {symbol}: {exc}") from exc


def _safe_info_value(ticker: Any, key: str) -> Any:
    try:
        info = getattr(ticker, "fast_info", None) or getattr(ticker, "info", None) or {}
        return info.get(key)
    except Exception:  # noqa: BLE001
        return None


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return 0.0


def _to_optional_float(value: Any) -> float | None:
    try:
        converted = float(value)
        return converted if pd.notna(converted) else None
    except Exception:  # noqa: BLE001
        return None


def _to_optional_int(value: Any) -> int | None:
    try:
        converted = int(value)
        return converted
    except Exception:  # noqa: BLE001
        return None


def _choose_midpoint(bid: float, ask: float, last_price: float) -> float:
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    if last_price > 0:
        return last_price
    if bid > 0:
        return bid
    if ask > 0:
        return ask
    return 0.0
