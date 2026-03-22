from __future__ import annotations

from typing import Any, Dict

import pandas as pd

try:
    import akshare as ak
except Exception:  # noqa: BLE001
    ak = None


class AShareOptionError(RuntimeError):
    pass


UNDERLYING_CONFIG = {
    "510050": {"name": "50ETF", "sina_symbol": "sh510050"},
    "510300": {"name": "300ETF", "sina_symbol": "sh510300"},
}

INDEX_OPTION_CONFIG = {
    "hs300": {
        "name": "HS300 Index Option",
        "list_fn": "option_cffex_hs300_list_sina",
        "spot_fn": "option_cffex_hs300_spot_sina",
    },
    "sz50": {
        "name": "SSE50 Index Option",
        "list_fn": "option_cffex_sz50_list_sina",
        "spot_fn": "option_cffex_sz50_spot_sina",
    },
    "zz1000": {
        "name": "CSI1000 Index Option",
        "list_fn": "option_cffex_zz1000_list_sina",
        "spot_fn": "option_cffex_zz1000_spot_sina",
    },
}


def fetch_etf_option_snapshot(
    *,
    underlying: str = "510050",
    option_type: str = "call",
    expiry: str | None = None,
    strike: float | None = None,
    contract_code: str | None = None,
) -> Dict[str, Any]:
    _ensure_akshare()
    option_type = _normalize_option_type(option_type)
    if underlying not in UNDERLYING_CONFIG:
        raise AShareOptionError("underlying must be one of: 510050, 510300.")

    contracts = ak.option_current_day_sse()
    if contracts.empty:
        raise AShareOptionError("No current SSE ETF option contracts are available.")

    filtered = contracts[contracts["标的券名称及代码"].astype(str).str.contains(underlying, na=False)].copy()
    type_label = "认购" if option_type == "call" else "认沽"
    filtered = filtered[filtered["类型"].astype(str) == type_label].copy()
    if filtered.empty:
        raise AShareOptionError(f"No {type_label} contracts available for {UNDERLYING_CONFIG[underlying]['name']}.")

    underlying_snapshot = _frame_to_mapping(ak.option_sse_underlying_spot_price_sina(symbol=UNDERLYING_CONFIG[underlying]["sina_symbol"]))
    underlying_price = _to_float(underlying_snapshot.get("最近成交价"))
    if underlying_price <= 0:
        raise AShareOptionError(f"Could not fetch a valid underlying price for {UNDERLYING_CONFIG[underlying]['name']}.")

    selected = _select_etf_contract(
        contracts=filtered,
        underlying_price=underlying_price,
        expiry=expiry,
        strike=strike,
        contract_code=contract_code,
    )
    contract_code_value = str(selected["合约编码"])
    quote = _frame_to_mapping(ak.option_sse_spot_price_sina(symbol=contract_code_value))
    greeks = _frame_to_mapping(ak.option_sse_greeks_sina(symbol=contract_code_value))

    bid = _to_float(quote.get("买价"))
    ask = _to_float(quote.get("卖价"))
    latest_price = _to_float(quote.get("最新价"))
    midpoint = _choose_midpoint(bid, ask, latest_price)
    theoretical_value = _to_float(greeks.get("理论价值"))

    return {
        "underlying": underlying,
        "available_expiries": _collect_expiries(filtered),
        "available_strikes": _collect_strikes(filtered, expiry=expiry),
        "underlying_name": _string_or_default(underlying_snapshot.get("证券简称"), UNDERLYING_CONFIG[underlying]["name"]),
        "underlying_price": underlying_price,
        "underlying_prev_close": _to_float(underlying_snapshot.get("昨日收盘价")),
        "underlying_open": _to_float(underlying_snapshot.get("今日开盘价")),
        "underlying_high": _to_float(underlying_snapshot.get("最高成交价")),
        "underlying_low": _to_float(underlying_snapshot.get("最低成交价")),
        "underlying_quote_time": _string_or_default(underlying_snapshot.get("行情时间"), ""),
        "option_type": option_type,
        "contract_code": contract_code_value,
        "trading_code": str(selected["合约交易代码"]),
        "contract_name": str(selected["合约简称"]),
        "expiry": str(selected["到期日"]),
        "strike": _to_float(selected["行权价"]),
        "latest_price": latest_price,
        "bid": bid,
        "ask": ask,
        "midpoint": midpoint,
        "change_percent": _to_float(quote.get("涨幅")),
        "open_interest": _to_float(quote.get("持仓量")),
        "volume": _to_float(quote.get("成交量")),
        "quote_time": _string_or_default(quote.get("行情时间"), ""),
        "delta": _to_float(greeks.get("Delta")),
        "gamma": _to_float(greeks.get("Gamma")),
        "theta": _to_float(greeks.get("Theta")),
        "vega": _to_float(greeks.get("Vega")),
        "implied_volatility": _to_float(greeks.get("隐含波动率")),
        "theoretical_value": theoretical_value,
        "pricing_gap": latest_price - theoretical_value,
        "moneyness": underlying_price - _to_float(selected["行权价"]),
        "data_source": "akshare_sse_option",
        "notes": [
            "This panel focuses on domestic ETF option market snapshots rather than full execution or strategy automation.",
            "Latest price, midpoint, implied volatility, and theoretical value should be interpreted together.",
            "This module is for learning and analysis, not investment advice.",
        ],
    }


def fetch_index_option_snapshot(
    *,
    market: str = "hs300",
    option_type: str = "call",
    contract_month: str | None = None,
    strike: float | None = None,
) -> Dict[str, Any]:
    _ensure_akshare()
    option_type = _normalize_option_type(option_type)
    if market not in INDEX_OPTION_CONFIG:
        raise AShareOptionError("market must be one of: hs300, sz50, zz1000.")

    config = INDEX_OPTION_CONFIG[market]
    list_fn = getattr(ak, config["list_fn"])
    spot_fn = getattr(ak, config["spot_fn"])

    contract_groups = list_fn()
    if not contract_groups:
        raise AShareOptionError(f"No index-option contract groups available for {config['name']}.")

    root_label = next(iter(contract_groups.keys()))
    contract_months = contract_groups[root_label]
    selected_month = contract_month if contract_month in contract_months else contract_months[0]
    spot_frame = spot_fn(symbol=selected_month)
    if spot_frame.empty:
        raise AShareOptionError(f"No spot rows available for index-option month {selected_month}.")

    prefix = "看涨合约" if option_type == "call" else "看跌合约"
    code_col = f"{prefix}-标识"
    bid_col = f"{prefix}-买价"
    last_col = f"{prefix}-最新价"
    ask_col = f"{prefix}-卖价"
    hold_col = f"{prefix}-持仓量"
    change_col = f"{prefix}-涨跌"

    filtered = spot_frame.copy()
    if strike is None:
        filtered["distance"] = (filtered["行权价"].astype(float) - filtered["行权价"].astype(float).median()).abs()
        selected_row = filtered.sort_values(by=["distance", "行权价"]).iloc[0]
    else:
        filtered["distance"] = (filtered["行权价"].astype(float) - float(strike)).abs()
        selected_row = filtered.sort_values(by=["distance"]).iloc[0]

    bid = _to_float(selected_row[bid_col])
    ask = _to_float(selected_row[ask_col])
    latest_price = _to_float(selected_row[last_col])

    return {
        "market": market,
        "market_name": config["name"],
        "available_months": contract_months,
        "available_strikes": sorted(spot_frame["行权价"].astype(float).tolist()),
        "contract_month": selected_month,
        "option_type": option_type,
        "contract_code": str(selected_row[code_col]),
        "strike": _to_float(selected_row["行权价"]),
        "latest_price": latest_price,
        "bid": bid,
        "ask": ask,
        "midpoint": _choose_midpoint(bid, ask, latest_price),
        "open_interest": _to_float(selected_row[hold_col]),
        "change_amount": _to_float(selected_row[change_col]),
        "data_source": f"akshare_{market}_index_option",
        "notes": [
            "This is a domestic index-option snapshot panel based on CFFEX contract-month quotes.",
            "Rows are organized by strike within a selected contract month, and the panel currently surfaces one representative contract at a time.",
            "This module is for learning and analysis, not investment advice.",
        ],
    }


def _select_etf_contract(
    *,
    contracts: pd.DataFrame,
    underlying_price: float,
    expiry: str | None,
    strike: float | None,
    contract_code: str | None,
) -> pd.Series:
    filtered = contracts.copy()
    if contract_code:
        exact = filtered[filtered["合约编码"].astype(str) == str(contract_code)]
        if exact.empty:
            raise AShareOptionError(f"Contract code {contract_code} was not found.")
        return exact.iloc[0]

    filtered["strike_value"] = filtered["行权价"].astype(float)
    if expiry:
        normalized_expiry = str(expiry).replace("-", "")
        if len(normalized_expiry) == 6:
            filtered = filtered[filtered["到期日"].astype(str).str.startswith(normalized_expiry)]
        else:
            filtered = filtered[filtered["到期日"].astype(str) == normalized_expiry]
        if filtered.empty:
            raise AShareOptionError(f"No contracts found for expiry {expiry}.")

    filtered = filtered.sort_values(by=["到期日", "strike_value"]).reset_index(drop=True)
    if strike is None:
        filtered["distance"] = (filtered["strike_value"] - underlying_price).abs()
        return filtered.sort_values(by=["到期日", "distance", "strike_value"]).iloc[0]

    filtered["distance"] = (filtered["strike_value"] - float(strike)).abs()
    return filtered.sort_values(by=["distance", "到期日"]).iloc[0]


def _collect_expiries(contracts: pd.DataFrame) -> list[str]:
    return sorted({str(value) for value in contracts["到期日"].astype(str).tolist()})


def _collect_strikes(contracts: pd.DataFrame, expiry: str | None) -> list[float]:
    filtered = contracts.copy()
    if expiry:
        normalized_expiry = str(expiry).replace("-", "")
        if len(normalized_expiry) == 6:
            filtered = filtered[filtered["到期日"].astype(str).str.startswith(normalized_expiry)]
        else:
            filtered = filtered[filtered["到期日"].astype(str) == normalized_expiry]
    return sorted({float(value) for value in filtered["行权价"].astype(float).tolist()})


def _frame_to_mapping(frame: pd.DataFrame) -> Dict[str, Any]:
    mapping: Dict[str, Any] = {}
    if frame.empty or "字段" not in frame.columns or "值" not in frame.columns:
        return mapping
    for _, row in frame.iterrows():
        mapping[str(row["字段"]).strip()] = row["值"]
    return mapping


def _normalize_option_type(option_type: str) -> str:
    normalized = (option_type or "").strip().lower()
    if normalized not in {"call", "put"}:
        raise AShareOptionError("option_type must be 'call' or 'put'.")
    return normalized


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return 0.0


def _string_or_default(value: Any, default: str) -> str:
    if value is None:
        return default
    converted = str(value).strip()
    return converted or default


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


def _ensure_akshare() -> None:
    if ak is None:
        raise AShareOptionError("akshare is not installed. Install it to enable A-share derivatives.")
