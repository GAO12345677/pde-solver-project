from fastapi.testclient import TestClient
import pandas as pd

import main
from api import routes
from services import ashare_market_data


def test_finance_stock_simulation_endpoint() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/finance/stocks/simulate",
        json={
            "initial_price": 100,
            "drift": 0.08,
            "volatility": 0.2,
            "horizon": 1.0,
            "steps": 120,
            "paths": 500,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["inputs"]["paths"] == 500
    assert len(payload["data"]["sample_path_data"]) == 121
    assert len(payload["data"]["terminal_histogram"]) == 12
    assert payload["data"]["summary"]["max"] >= payload["data"]["summary"]["min"]


def test_finance_black_scholes_endpoint() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/finance/options/black_scholes_1d",
        json={
            "spot": 100,
            "strike": 105,
            "maturity": 0.5,
            "volatility": 0.25,
            "rate": 0.02,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]["curve"]) == 40
    assert payload["data"]["summary"]["callAtSpot"] >= 0.0
    assert payload["data"]["summary"]["putAtSpot"] >= 0.0
    assert "greeks" in payload["data"]["summary"]
    assert "call" in payload["data"]["summary"]["greeks"]
    assert "delta" in payload["data"]["summary"]["greeks"]["call"]


def test_finance_black_scholes_2d_endpoint() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/finance/options/black_scholes_2d",
        json={
            "spot1": 100,
            "spot2": 95,
            "strike": 100,
            "maturity": 0.5,
            "volatility1": 0.25,
            "volatility2": 0.22,
            "rate": 0.02,
            "correlation": 0.3,
            "grid_size": 12,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["inputs"]["grid_size"] == 12
    assert len(payload["data"]["x_values"]) == 12
    assert len(payload["data"]["y_values"]) == 12
    assert len(payload["data"]["surface"]) == 144
    assert payload["data"]["summary"]["surfaceMax"] >= payload["data"]["summary"]["surfaceMin"]


def test_finance_market_stock_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "estimate_stock_inputs",
        lambda symbol, lookback_days=252: {
            "symbol": symbol.upper(),
            "spot": 123.45,
            "historical_volatility": 0.28,
            "drift": 0.11,
            "risk_free_rate": 0.021,
            "history_preview": [{"date": "2026-03-20", "close": 123.45}],
            "data_source": "yfinance",
        },
    )
    client = TestClient(main.app)
    response = client.get("/finance/market/stock/MSFT")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["spot"] == 123.45
    assert payload["data"]["historical_volatility"] == 0.28


def test_finance_compare_market_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "compare_option_with_market",
        lambda **kwargs: {
            "symbol": "MSFT",
            "spot": 123.45,
            "expiry": "2026-06-19",
            "strike": 125.0,
            "option_type": "call",
            "market_price": 6.2,
            "model_price": 5.8,
            "implied_volatility": 0.31,
            "risk_free_rate": 0.021,
            "pricing_gap": -0.4,
            "contract_symbol": "MSFT260619C00125000",
            "notes": ["demo"],
        },
    )
    client = TestClient(main.app)
    response = client.post(
        "/finance/options/compare_market",
        json={"symbol": "MSFT", "option_type": "call"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["model_price"] == 5.8
    assert payload["data"]["market_price"] == 6.2
    assert payload["data"]["implied_volatility"] == 0.31


def test_finance_ashare_stock_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_ashare_stock_analysis",
        lambda symbol, lookback_days=252, force_history_only=False: {
            "symbol": "000001.SZ",
            "raw_symbol": "000001",
            "name": "平安银行",
            "latest_price": 10.77,
            "latest_close": 10.88,
            "open": 10.87,
            "high": 10.94,
            "low": 10.76,
            "prev_close": 10.88,
            "average_price": 10.84,
            "change_percent": -1.01,
            "change_amount": -0.11,
            "volume": 834083.0,
            "amount": 903819000.0,
            "quote_timestamp": "15:30:01",
            "latest_trade_date": "2026-03-20",
            "market_clock": {
                "timezone": "Asia/Shanghai",
                "local_time": "2026-03-22 10:00:00",
                "is_trading_day": False,
                "market_open": False,
                "phase": "closed_non_trading_day",
                "phase_label": "Closed 非交易日",
            },
            "volatility": {"hv20": 0.18, "hv60": 0.22, "hv252": 0.25},
            "annualized_drift": 0.06,
            "history_preview": [{"date": "2026-03-20", "close": 10.88}],
            "data_source": "akshare",
            "notes": ["demo"],
        },
    )
    client = TestClient(main.app)
    response = client.get("/finance/ashare/stock/000001")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["symbol"] == "000001.SZ"
    assert payload["data"]["name"] == "平安银行"
    assert payload["data"]["volatility"]["hv252"] == 0.25


def test_finance_ashare_pair_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_ashare_pair_analysis",
        lambda symbol1, symbol2, lookback_days=252: {
            "symbol1": "000001.SZ",
            "symbol2": "600519.SH",
            "name1": "平安银行",
            "name2": "贵州茅台",
            "latest_price1": 10.77,
            "latest_price2": 1520.0,
            "correlation": 0.36,
            "hv252_1": 0.25,
            "hv252_2": 0.31,
            "pair_history": [
                {"date": "2026-03-19", "close1": 10.9, "close2": 1518.0},
                {"date": "2026-03-20", "close1": 10.88, "close2": 1520.0},
            ],
            "rolling_correlation": [
                {"date": "2026-03-20", "correlation": 0.41},
            ],
            "data_source": "akshare",
        },
    )
    client = TestClient(main.app)
    response = client.get("/finance/ashare/pair?symbol1=000001&symbol2=600519")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["correlation"] == 0.36
    assert payload["data"]["pair_history"][0]["close1"] == 10.9
    assert payload["data"]["rolling_correlation"][0]["correlation"] == 0.41


def test_fetch_ashare_stock_analysis_falls_back_to_daily_history(monkeypatch) -> None:
    class FakeAk:
        @staticmethod
        def stock_bid_ask_em(symbol: str):
            raise ConnectionError("live quote disconnected")

        @staticmethod
        def stock_individual_info_em(symbol: str):
            return pd.DataFrame(columns=["item", "value"])

    def fake_daily_history(raw_symbol: str, lookback_days: int):
        frame = pd.DataFrame(
            {
                "date": ["2026-03-19", "2026-03-20"],
                "close": [10.5, 10.8],
            }
        )
        frame.attrs["history_source"] = "baostock"
        return frame

    monkeypatch.setattr(ashare_market_data, "ak", FakeAk())
    monkeypatch.setattr(ashare_market_data, "_ensure_akshare", lambda: None)
    monkeypatch.setattr(ashare_market_data, "_fetch_daily_history", fake_daily_history)
    monkeypatch.setattr(
        ashare_market_data,
        "get_ashare_market_clock",
        lambda now=None: {
            "timezone": "Asia/Shanghai",
            "local_time": "2026-03-22 10:00:00",
            "is_trading_day": False,
            "market_open": False,
            "phase": "closed_non_trading_day",
            "phase_label": "Closed",
        },
    )

    result = ashare_market_data.fetch_ashare_stock_analysis("000001", 252)
    assert result["latest_price"] == 10.8
    assert result["prev_close"] == 10.5
    assert result["quote_timestamp"] == "2026-03-20"
    assert result["data_source"] == "baostock_history_fallback"
    assert result["realtime_available"] is False
    assert any("fallen back to daily-history mode" in note for note in result["notes"])


def test_finance_ashare_stock_endpoint_accepts_history_only_flag(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_fetch(symbol: str, lookback_days: int = 252, force_history_only: bool = False):
        captured["symbol"] = symbol
        captured["lookback_days"] = lookback_days
        captured["force_history_only"] = force_history_only
        return {
            "symbol": "000001.SZ",
            "raw_symbol": "000001",
            "name": "示例股票",
            "latest_price": 10.8,
            "latest_close": 10.8,
            "open": None,
            "high": None,
            "low": None,
            "prev_close": 10.5,
            "average_price": None,
            "change_percent": 2.86,
            "change_amount": 0.3,
            "volume": None,
            "amount": None,
            "quote_timestamp": "2026-03-20",
            "latest_trade_date": "2026-03-20",
            "market_clock": {
                "timezone": "Asia/Shanghai",
                "local_time": "2026-03-22 10:00:00",
                "is_trading_day": False,
                "market_open": False,
                "phase": "closed_non_trading_day",
                "phase_label": "Closed",
            },
            "volatility": {"hv20": 0.18, "hv60": 0.22, "hv252": 0.25},
            "annualized_drift": 0.06,
            "history_preview": [{"date": "2026-03-20", "close": 10.8}],
            "data_source": "baostock_history_fallback",
            "realtime_available": False,
            "notes": ["demo"],
        }

    monkeypatch.setattr(routes, "fetch_ashare_stock_analysis", fake_fetch)
    client = TestClient(main.app)
    response = client.get("/finance/ashare/stock/000001?lookback_days=120&force_history_only=true")
    assert response.status_code == 200
    assert captured == {"symbol": "000001", "lookback_days": 120, "force_history_only": True}


def test_finance_ashare_pair_endpoint_handles_data_source_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_ashare_pair_analysis",
        lambda *args, **kwargs: (_ for _ in ()).throw(routes.AShareMarketDataError("remote disconnected")),
    )
    client = TestClient(main.app)
    response = client.get("/finance/ashare/pair?symbol1=000001&symbol2=600519")
    assert response.status_code == 503
    payload = response.json()
    assert payload["message"]["success"] is False
    assert payload["message"]["error"]["code"] == "ASHARE_PAIR_UNAVAILABLE"
    assert payload["message"]["error"]["details"]["message"] == "remote disconnected"


def test_finance_ashare_pair_endpoint_handles_generic_upstream_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_ashare_pair_analysis",
        lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError("remote closed connection")),
    )
    client = TestClient(main.app)
    response = client.get("/finance/ashare/pair?symbol1=000001&symbol2=600519")
    assert response.status_code == 503
    payload = response.json()
    assert payload["message"]["success"] is False
    assert payload["message"]["error"]["code"] == "ASHARE_PAIR_UPSTREAM_ERROR"
    assert payload["message"]["error"]["details"]["message"] == "remote closed connection"


def test_finance_ashare_etf_option_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_etf_option_snapshot",
        lambda **kwargs: {
            "underlying": "510050",
            "underlying_name": "上证50ETF",
            "underlying_price": 2.957,
            "underlying_prev_close": 2.993,
            "underlying_open": 2.99,
            "underlying_high": 3.001,
            "underlying_low": 2.955,
            "underlying_quote_time": "15:00:03",
            "option_type": "call",
            "contract_code": "10009633",
            "trading_code": "510050C2603A02700",
            "contract_name": "50ETF购3月2630A",
            "expiry": "20260325",
            "strike": 2.63,
            "latest_price": 0.33,
            "bid": 0.327,
            "ask": 0.33,
            "midpoint": 0.3285,
            "change_percent": -9.76,
            "open_interest": 1007,
            "volume": 141,
            "quote_time": "2026-03-20 14:53:37",
            "delta": 1.0,
            "gamma": 0.0,
            "theta": -0.1051,
            "vega": 0.0,
            "implied_volatility": 0.5124,
            "theoretical_value": 0.3284,
            "pricing_gap": 0.0016,
            "moneyness": 0.327,
            "data_source": "akshare_sse_option",
            "notes": ["demo"],
        },
    )
    client = TestClient(main.app)
    response = client.post("/finance/ashare/etf_option", json={"underlying": "510050", "option_type": "call"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["contract_code"] == "10009633"
    assert payload["data"]["underlying_name"] == "上证50ETF"
    assert payload["data"]["implied_volatility"] == 0.5124
def test_finance_ashare_index_option_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_index_option_snapshot",
        lambda **kwargs: {
            "market": "hs300",
            "market_name": "HS300 Index Option",
            "available_months": ["io2604", "io2605"],
            "available_strikes": [3800.0, 3850.0, 3900.0],
            "contract_month": "io2604",
            "option_type": "call",
            "contract_code": "IO2604-C-3900",
            "strike": 3900.0,
            "latest_price": 112.5,
            "bid": 111.8,
            "ask": 113.2,
            "midpoint": 112.5,
            "open_interest": 1245.0,
            "change_amount": 8.2,
            "data_source": "akshare_hs300_index_option",
            "notes": ["demo"],
        },
    )
    client = TestClient(main.app)
    response = client.post("/finance/ashare/index_option", json={"market": "hs300", "option_type": "call"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["market"] == "hs300"
    assert payload["data"]["contract_code"] == "IO2604-C-3900"
    assert payload["data"]["available_months"] == ["io2604", "io2605"]


def test_finance_ashare_index_option_endpoint_handles_data_source_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "fetch_index_option_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(routes.AShareOptionError("upstream unavailable")),
    )
    client = TestClient(main.app)
    response = client.post("/finance/ashare/index_option", json={"market": "hs300", "option_type": "call"})
    assert response.status_code == 503
    payload = response.json()
    assert payload["message"]["success"] is False
    assert payload["message"]["error"]["code"] == "ASHARE_INDEX_OPTION_UNAVAILABLE"
    assert payload["message"]["error"]["details"]["message"] == "upstream unavailable"
