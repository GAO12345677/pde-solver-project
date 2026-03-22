from __future__ import annotations

import concurrent.futures
import math
from datetime import datetime, time
from functools import lru_cache
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

try:
    import akshare as ak
except Exception:  # noqa: BLE001
    ak = None

try:
    import baostock as bs
except Exception:  # noqa: BLE001
    bs = None


ASIA_SHANGHAI = ZoneInfo("Asia/Shanghai")
LIVE_QUOTE_TIMEOUT_S = 6.0


class AShareMarketDataError(RuntimeError):
    pass


def fetch_ashare_stock_analysis(symbol: str, lookback_days: int = 252, force_history_only: bool = False) -> Dict[str, Any]:
    _ensure_akshare()
    normalized = normalize_ashare_symbol(symbol)
    raw_symbol = normalized["raw_symbol"]
    display_symbol = normalized["display_symbol"]
    history_df = _fetch_daily_history(raw_symbol, lookback_days)
    history_source = history_df.attrs.get("history_source", "unknown")

    close_series = history_df["close"].astype(float)
    latest_close = float(close_series.iloc[-1])
    history_preview = history_df.tail(30)[["date", "close"]].to_dict(orient="records")
    log_returns = np.diff(np.log(close_series.to_numpy()))
    annualized_drift = float(np.mean(log_returns) * 252) if len(log_returns) else 0.0

    quote_map: Dict[str, Any] = {}
    info_map: Dict[str, Any] = {}
    realtime_available = False
    fallback_reason: str | None = None

    if force_history_only:
        fallback_reason = "Manual history-only mode selected."
    else:
        try:
            quote_df = _call_with_timeout(ak.stock_bid_ask_em, timeout_s=LIVE_QUOTE_TIMEOUT_S, symbol=raw_symbol)
            if quote_df.empty:
                fallback_reason = f"No live A-share quote data available for {display_symbol}."
            else:
                quote_map = _frame_to_mapping(quote_df, "item", "value")
                realtime_available = True
        except Exception as exc:  # noqa: BLE001
            fallback_reason = str(exc)

        try:
            info_df = _call_with_timeout(ak.stock_individual_info_em, timeout_s=LIVE_QUOTE_TIMEOUT_S, symbol=raw_symbol)
            info_map = _frame_to_mapping(info_df, "item", "value") if not info_df.empty else {}
        except Exception:  # noqa: BLE001
            info_map = {}

    market_clock = get_ashare_market_clock()
    latest_trade_date = str(history_df["date"].iloc[-1])
    quote_timestamp = _string_or_none(quote_map.get("?????"))
    prev_close = _float_or_none(quote_map.get("???")) or (float(close_series.iloc[-2]) if len(close_series) >= 2 else latest_close)
    change_amount = _float_or_none(quote_map.get("???"))
    if change_amount is None:
        change_amount = latest_close - prev_close
    change_percent = _float_or_none(quote_map.get("???"))
    if change_percent is None:
        change_percent = (change_amount / prev_close * 100.0) if prev_close else 0.0

    notes = [
        "A-share quotes are constrained by exchange trading sessions and may reflect the latest available tick or the latest completed session.",
        "Outside trading hours, latest price should be interpreted together with market status and quote timestamp.",
        "This module is for research and analysis, not investment advice.",
    ]
    if not market_clock["is_trading_day"]:
        notes.append("Current date is not an A-share trading day, so prices should be treated as latest available market data.")
    elif not market_clock["market_open"]:
        notes.append("Market is currently not in a continuous trading session, so quotes may lag the next active session.")
    if not realtime_available:
        notes.append("Live quote source is temporarily unavailable, so the panel has fallen back to daily-history mode.")
        notes.append("Fallback mode uses the latest daily close and recent history to keep volatility and trend analysis available.")
        if force_history_only:
            notes.append("History-only mode was selected manually, so the panel skipped real-time quote fetching on purpose.")
        if fallback_reason:
            notes.append(f"Fallback reason: {fallback_reason}")

    return {
        "symbol": display_symbol,
        "raw_symbol": raw_symbol,
        "name": _string_or_none(info_map.get("???????")) or display_symbol,
        "latest_price": _float_or_none(quote_map.get("????")) or latest_close,
        "latest_close": latest_close,
        "open": _float_or_none(quote_map.get("???")),
        "high": _float_or_none(quote_map.get("????")),
        "low": _float_or_none(quote_map.get("????")),
        "prev_close": prev_close,
        "average_price": _float_or_none(quote_map.get("???")),
        "change_percent": change_percent,
        "change_amount": change_amount,
        "volume": _float_or_none(quote_map.get("???")),
        "amount": _float_or_none(quote_map.get("???")),
        "quote_timestamp": quote_timestamp or latest_trade_date,
        "latest_trade_date": latest_trade_date,
        "market_clock": market_clock,
        "volatility": {
            "hv20": _annualized_volatility(close_series, 20),
            "hv60": _annualized_volatility(close_series, 60),
            "hv252": _annualized_volatility(close_series, 252),
        },
        "annualized_drift": annualized_drift,
        "history_preview": history_preview,
        "data_source": "akshare" if realtime_available else f"{history_source}_history_fallback",
        "realtime_available": realtime_available,
        "notes": notes,
    }


def fetch_ashare_pair_analysis(symbol1: str, symbol2: str, lookback_days: int = 252) -> Dict[str, Any]:
    left = fetch_ashare_stock_analysis(symbol1, lookback_days)
    right = fetch_ashare_stock_analysis(symbol2, lookback_days)
    left_returns, right_returns = _aligned_log_returns(left["raw_symbol"], right["raw_symbol"], lookback_days)
    correlation = float(np.corrcoef(left_returns.to_numpy(), right_returns.to_numpy())[0, 1])
    pair_history = _build_pair_history(left["raw_symbol"], right["raw_symbol"], lookback_days)
    rolling_correlation = _build_rolling_correlation(pair_history, window=20)

    return {
        "symbol1": left["symbol"],
        "symbol2": right["symbol"],
        "name1": left["name"],
        "name2": right["name"],
        "latest_price1": left["latest_price"],
        "latest_price2": right["latest_price"],
        "correlation": correlation,
        "hv252_1": left["volatility"]["hv252"],
        "hv252_2": right["volatility"]["hv252"],
        "pair_history": pair_history.tail(30).to_dict(orient="records"),
        "rolling_correlation": rolling_correlation,
        "data_source": "akshare",
    }


def get_ashare_market_clock(now: datetime | None = None) -> Dict[str, Any]:
    current = now.astimezone(ASIA_SHANGHAI) if now else datetime.now(ASIA_SHANGHAI)
    trade_dates = _trade_dates()
    today = current.date()
    current_time = current.time()
    is_trading_day = today in trade_dates

    if not is_trading_day:
        phase = "closed_non_trading_day"
        label = "Closed 非交易日"
        market_open = False
    elif current_time < time(9, 15):
        phase = "pre_open"
        label = "Pre-open 开盘前"
        market_open = False
    elif current_time < time(9, 25):
        phase = "opening_auction"
        label = "Opening auction 开盘集合竞价"
        market_open = True
    elif current_time < time(9, 30):
        phase = "auction_buffer"
        label = "Auction buffer 集合竞价缓冲"
        market_open = False
    elif current_time < time(11, 30):
        phase = "continuous_am"
        label = "Continuous trading AM 上午连续竞价"
        market_open = True
    elif current_time < time(13, 0):
        phase = "lunch_break"
        label = "Lunch break 午间休市"
        market_open = False
    elif current_time < time(14, 57):
        phase = "continuous_pm"
        label = "Continuous trading PM 下午连续竞价"
        market_open = True
    elif current_time <= time(15, 0):
        phase = "closing_auction"
        label = "Closing auction 收盘集合竞价"
        market_open = True
    else:
        phase = "after_close"
        label = "After close 收盘后"
        market_open = False

    return {
        "timezone": "Asia/Shanghai",
        "local_time": current.strftime("%Y-%m-%d %H:%M:%S"),
        "is_trading_day": is_trading_day,
        "market_open": market_open,
        "phase": phase,
        "phase_label": label,
    }


def normalize_ashare_symbol(symbol: str) -> Dict[str, str]:
    candidate = (symbol or "").strip().upper()
    if not candidate:
        raise AShareMarketDataError("A-share symbol cannot be empty.")

    raw_symbol = candidate.split(".")[0]
    if not raw_symbol.isdigit() or len(raw_symbol) != 6:
        raise AShareMarketDataError("A-share symbol must be a 6-digit code such as 000001 or 600519.")

    if raw_symbol.startswith(("6", "9")):
        market = "SH"
    elif raw_symbol.startswith(("0", "2", "3")):
        market = "SZ"
    elif raw_symbol.startswith(("4", "8")):
        market = "BJ"
    else:
        market = "UNKNOWN"

    return {
        "raw_symbol": raw_symbol,
        "display_symbol": f"{raw_symbol}.{market}" if market != "UNKNOWN" else raw_symbol,
    }


def _to_baostock_symbol(raw_symbol: str) -> str:
    if raw_symbol.startswith(("6", "9")):
        return f"sh.{raw_symbol}"
    if raw_symbol.startswith(("0", "2", "3")):
        return f"sz.{raw_symbol}"
    if raw_symbol.startswith(("4", "8")):
        return f"bj.{raw_symbol}"
    raise AShareMarketDataError(f"Unsupported A-share market prefix for {raw_symbol}.")


def _fetch_daily_history(raw_symbol: str, lookback_days: int) -> pd.DataFrame:
    if bs is not None:
        try:
            return _fetch_daily_history_baostock(raw_symbol, lookback_days)
        except Exception:  # noqa: BLE001
            pass

    start = datetime.now(ASIA_SHANGHAI) - pd.Timedelta(days=max(lookback_days * 2, 180))
    end = datetime.now(ASIA_SHANGHAI) + pd.Timedelta(days=1)
    history_df = ak.stock_zh_a_hist(
        symbol=raw_symbol,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="",
    )
    if history_df.empty:
        raise AShareMarketDataError(f"No A-share daily history available for {raw_symbol}.")

    renamed = history_df.rename(
        columns={
            "日期": "date",
            "收盘": "close",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "change_percent",
            "涨跌额": "change_amount",
        }
    )
    renamed["date"] = pd.to_datetime(renamed["date"]).dt.strftime("%Y-%m-%d")
    result = renamed.tail(max(lookback_days, 60)).reset_index(drop=True)
    result.attrs["history_source"] = "akshare"
    return result


def _fetch_daily_history_baostock(raw_symbol: str, lookback_days: int) -> pd.DataFrame:
    start = datetime.now(ASIA_SHANGHAI) - pd.Timedelta(days=max(lookback_days * 2, 180))
    end = datetime.now(ASIA_SHANGHAI) + pd.Timedelta(days=1)
    bs_code = _to_baostock_symbol(raw_symbol)

    login_result = bs.login()
    if getattr(login_result, "error_code", "0") != "0":
        raise AShareMarketDataError(f"baostock login failed for {raw_symbol}: {getattr(login_result, 'error_msg', '')}")

    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
            frequency="d",
            adjustflag="3",
        )
        if getattr(rs, "error_code", "0") != "0":
            raise AShareMarketDataError(f"baostock history query failed for {raw_symbol}: {getattr(rs, 'error_msg', '')}")

        rows: List[list[str]] = []
        while rs.next():
            rows.append(rs.get_row_data())
    finally:
        bs.logout()

    if not rows:
        raise AShareMarketDataError(f"No baostock daily history available for {raw_symbol}.")

    history_df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume", "amount", "change_percent"])
    for column in ["open", "high", "low", "close", "volume", "amount", "change_percent"]:
        history_df[column] = pd.to_numeric(history_df[column], errors="coerce")
    history_df["change_amount"] = history_df["close"].diff()
    history_df["date"] = pd.to_datetime(history_df["date"]).dt.strftime("%Y-%m-%d")
    result = history_df.tail(max(lookback_days, 60)).reset_index(drop=True)
    result.attrs["history_source"] = "baostock"
    return result


def _aligned_log_returns(raw_symbol1: str, raw_symbol2: str, lookback_days: int) -> Tuple[pd.Series, pd.Series]:
    merged = _build_pair_history(raw_symbol1, raw_symbol2, lookback_days)
    if len(merged) < 10:
        raise AShareMarketDataError("Not enough overlapping A-share observations to compute correlation.")

    returns = pd.DataFrame(
        {
            "left": np.log(merged["close1"] / merged["close1"].shift(1)),
            "right": np.log(merged["close2"] / merged["close2"].shift(1)),
        }
    ).dropna()
    return returns["left"], returns["right"]


def _build_pair_history(raw_symbol1: str, raw_symbol2: str, lookback_days: int) -> pd.DataFrame:
    left = _fetch_daily_history(raw_symbol1, lookback_days)[["date", "close"]].rename(columns={"close": "close1"})
    right = _fetch_daily_history(raw_symbol2, lookback_days)[["date", "close"]].rename(columns={"close": "close2"})
    return left.merge(right, on="date", how="inner").tail(max(lookback_days, 60)).reset_index(drop=True)


def _build_rolling_correlation(pair_history: pd.DataFrame, window: int = 20) -> List[Dict[str, Any]]:
    if len(pair_history) < window + 1:
        return []

    returns = pd.DataFrame(
        {
            "date": pair_history["date"],
            "left": np.log(pair_history["close1"] / pair_history["close1"].shift(1)),
            "right": np.log(pair_history["close2"] / pair_history["close2"].shift(1)),
        }
    ).dropna()
    if len(returns) < window:
        return []

    rows: List[Dict[str, Any]] = []
    for index in range(window - 1, len(returns)):
        window_frame = returns.iloc[index - window + 1 : index + 1]
        corr = float(np.corrcoef(window_frame["left"].to_numpy(), window_frame["right"].to_numpy())[0, 1])
        rows.append({"date": str(returns.iloc[index]["date"]), "correlation": corr})
    return rows[-30:]


@lru_cache(maxsize=1)
def _trade_dates() -> set:
    if bs is not None:
        try:
            login_result = bs.login()
            if getattr(login_result, "error_code", "0") == "0":
                try:
                    start = (datetime.now(ASIA_SHANGHAI) - pd.Timedelta(days=366)).strftime("%Y-%m-%d")
                    end = (datetime.now(ASIA_SHANGHAI) + pd.Timedelta(days=30)).strftime("%Y-%m-%d")
                    rs = bs.query_trade_dates(start_date=start, end_date=end)
                    if getattr(rs, "error_code", "0") == "0":
                        rows = []
                        while rs.next():
                            rows.append(rs.get_row_data())
                        if rows:
                            frame = pd.DataFrame(rows, columns=["calendar_date", "is_trading_day"])
                            frame = frame[frame["is_trading_day"] == "1"]
                            return set(pd.to_datetime(frame["calendar_date"]).dt.date.tolist())
                finally:
                    bs.logout()
        except Exception:  # noqa: BLE001
            pass

    if ak is not None:
        try:
            trade_dates_df = ak.tool_trade_date_hist_sina()
            if not trade_dates_df.empty:
                return set(pd.to_datetime(trade_dates_df["trade_date"]).dt.date.tolist())
        except Exception:  # noqa: BLE001
            pass

    # Final fallback: weekdays only. Less precise on holidays, but avoids blocking the whole panel.
    today = datetime.now(ASIA_SHANGHAI).date()
    return {
        (pd.Timestamp(today) + pd.Timedelta(days=offset)).date()
        for offset in range(-366, 31)
        if (pd.Timestamp(today) + pd.Timedelta(days=offset)).weekday() < 5
    }


def _annualized_volatility(close_series: pd.Series, window: int) -> float | None:
    if len(close_series) < window + 1:
        return None
    returns = np.diff(np.log(close_series.tail(window + 1).to_numpy()))
    if len(returns) < 2:
        return None
    return float(np.std(returns, ddof=1) * math.sqrt(252))


def _frame_to_mapping(frame: pd.DataFrame, key_col: str, value_col: str) -> Dict[str, Any]:
    mapping: Dict[str, Any] = {}
    if key_col not in frame.columns or value_col not in frame.columns:
        return mapping
    for _, row in frame[[key_col, value_col]].iterrows():
        mapping[str(row[key_col])] = row[value_col]
    return mapping


def _float_or_none(value: Any) -> float | None:
    try:
        converted = float(value)
        return converted if np.isfinite(converted) else None
    except Exception:  # noqa: BLE001
        return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    converted = str(value).strip()
    return converted or None


def _call_with_timeout(func, *, timeout_s: float, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, **kwargs)
        try:
            return future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError as exc:
            raise TimeoutError(f"Timed out after {timeout_s:.0f}s while fetching live A-share data.") from exc


def _ensure_akshare() -> None:
    if ak is None:
        raise AShareMarketDataError("akshare is not installed. Install it to enable A-share market data.")
