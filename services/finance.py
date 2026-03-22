from __future__ import annotations

import math
from typing import Dict, List

from services.market_data import fetch_option_market_snapshot, fetch_risk_free_rate, fetch_stock_snapshot


def simulate_stock_dynamics(
    *,
    initial_price: float,
    drift: float,
    volatility: float,
    horizon: float,
    steps: int,
    paths: int,
) -> Dict[str, object]:
    steps = _clamp_integer(steps, 10, 600)
    paths = _clamp_integer(paths, 50, 5000)
    initial_price = max(float(initial_price), 1.0)
    drift = float(drift)
    volatility = max(float(volatility), 1e-4)
    horizon = max(float(horizon), 0.05)
    dt = horizon / steps

    seed = 20260322

    def random_uniform() -> float:
        nonlocal seed
        seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
        return seed / 4294967296.0

    def random_normal() -> float:
        u1 = max(random_uniform(), 1e-12)
        u2 = random_uniform()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

    visible_paths = min(paths, 6)
    path_store: List[List[float]] = [[initial_price] * (steps + 1) for _ in range(visible_paths)]
    terminal_prices: List[float] = []

    for path_index in range(paths):
        price = initial_price
        for step_index in range(1, steps + 1):
            shock = random_normal()
            price *= math.exp((drift - 0.5 * volatility * volatility) * dt + volatility * math.sqrt(dt) * shock)
            if path_index < visible_paths:
                path_store[path_index][step_index] = price
        terminal_prices.append(price)

    sample_path_data: List[Dict[str, float | int]] = []
    for step_index in range(steps + 1):
        row: Dict[str, float | int] = {"step": step_index}
        for path_index, path in enumerate(path_store):
            row[f"Path {path_index + 1}"] = path[step_index]
        sample_path_data.append(row)

    summary = _build_summary(terminal_prices)
    terminal_histogram = _build_histogram(terminal_prices, 12)
    return {
        "inputs": {
            "initial_price": initial_price,
            "drift": drift,
            "volatility": volatility,
            "horizon": horizon,
            "steps": steps,
            "paths": paths,
        },
        "sample_path_data": sample_path_data,
        "terminal_histogram": terminal_histogram,
        "summary": summary,
    }


def price_black_scholes_1d(
    *,
    spot: float,
    strike: float,
    maturity: float,
    volatility: float,
    rate: float,
) -> Dict[str, object]:
    spot = max(float(spot), 1.0)
    strike = max(float(strike), 1.0)
    maturity = max(float(maturity), 0.01)
    volatility = max(float(volatility), 1e-4)
    rate = float(rate)

    start = max(spot * 0.4, strike * 0.4, 10.0)
    end = max(spot * 1.8, strike * 1.8, start + 10.0)
    curve = []
    for index in range(40):
        current_spot = start + ((end - start) * index) / 39.0
        priced = _black_scholes(current_spot, strike, maturity, rate, volatility)
        curve.append(
            {
                "spot": round(current_spot, 2),
                "callPrice": priced["call"],
                "putPrice": priced["put"],
                "callPayoff": max(current_spot - strike, 0.0),
                "putPayoff": max(strike - current_spot, 0.0),
            }
        )

    at_spot = _black_scholes(spot, strike, maturity, rate, volatility)
    greeks = _black_scholes_greeks(spot, strike, maturity, rate, volatility)
    intrinsic_call = max(spot - strike, 0.0)
    intrinsic_put = max(strike - spot, 0.0)

    return {
        "inputs": {
            "spot": spot,
            "strike": strike,
            "maturity": maturity,
            "volatility": volatility,
            "rate": rate,
        },
        "curve": curve,
        "summary": {
            "callAtSpot": at_spot["call"],
            "putAtSpot": at_spot["put"],
            "intrinsicCall": intrinsic_call,
            "intrinsicPut": intrinsic_put,
            "timeValueCall": max(at_spot["call"] - intrinsic_call, 0.0),
            "timeValuePut": max(at_spot["put"] - intrinsic_put, 0.0),
            "greeks": greeks,
        },
    }


def price_black_scholes_2d(
    *,
    spot1: float,
    spot2: float,
    strike: float,
    maturity: float,
    volatility1: float,
    volatility2: float,
    rate: float,
    correlation: float,
    grid_size: int,
) -> Dict[str, object]:
    spot1 = max(float(spot1), 1.0)
    spot2 = max(float(spot2), 1.0)
    strike = max(float(strike), 1.0)
    maturity = max(float(maturity), 0.01)
    volatility1 = max(float(volatility1), 1e-4)
    volatility2 = max(float(volatility2), 1e-4)
    rate = float(rate)
    correlation = max(min(float(correlation), 0.999), -0.999)
    grid_size = _clamp_integer(grid_size, 8, 32)

    effective_vol = math.sqrt(
        (volatility1 * volatility1 + volatility2 * volatility2 + 2.0 * correlation * volatility1 * volatility2) / 4.0
    )

    s1_start = max(min(spot1, strike) * 0.4, 10.0)
    s1_end = max(max(spot1, strike) * 1.8, s1_start + 10.0)
    s2_start = max(min(spot2, strike) * 0.4, 10.0)
    s2_end = max(max(spot2, strike) * 1.8, s2_start + 10.0)

    surface: List[float] = []
    x_values: List[float] = []
    y_values: List[float] = []

    for iy in range(grid_size):
        s2_value = s2_start + ((s2_end - s2_start) * iy) / max(grid_size - 1, 1)
        y_values.append(round(s2_value, 2))
    for ix in range(grid_size):
        s1_value = s1_start + ((s1_end - s1_start) * ix) / max(grid_size - 1, 1)
        x_values.append(round(s1_value, 2))

    for s2_value in y_values:
        for s1_value in x_values:
            basket_spot = 0.5 * (s1_value + s2_value)
            priced = _black_scholes(basket_spot, strike, maturity, rate, effective_vol)
            surface.append(priced["call"])

    current_basket = 0.5 * (spot1 + spot2)
    current_price = _black_scholes(current_basket, strike, maturity, rate, effective_vol)["call"]

    return {
        "inputs": {
            "spot1": spot1,
            "spot2": spot2,
            "strike": strike,
            "maturity": maturity,
            "volatility1": volatility1,
            "volatility2": volatility2,
            "rate": rate,
            "correlation": correlation,
            "grid_size": grid_size,
        },
        "surface": surface,
        "x_values": x_values,
        "y_values": y_values,
        "summary": {
            "effectiveVolatility": effective_vol,
            "basketSpot": current_basket,
            "callAtCurrentPair": current_price,
            "surfaceMin": min(surface),
            "surfaceMax": max(surface),
        },
    }


def compare_option_with_market(
    *,
    symbol: str,
    expiry: str | None,
    strike: float | None,
    option_type: str,
    maturity_years: float | None = None,
    use_market_iv: bool = True,
) -> Dict[str, object]:
    stock = fetch_stock_snapshot(symbol, 252)
    market = fetch_option_market_snapshot(symbol, expiry=expiry, strike=strike, option_type=option_type)
    quote = market["quote"]
    risk_free = fetch_risk_free_rate()
    maturity = max(float(maturity_years or 0.25), 0.01)
    implied_volatility = quote.get("implied_volatility") or 0.25
    model_volatility = implied_volatility if use_market_iv else 0.25

    model_prices = _black_scholes(
        stock["spot"],
        float(quote["strike"]),
        maturity,
        float(risk_free["annual_rate"]),
        float(model_volatility),
    )
    market_price = float(quote["midpoint"])
    model_price = model_prices["call" if option_type.lower() == "call" else "put"]
    pricing_gap = model_price - market_price

    return {
        "symbol": symbol.upper(),
        "spot": stock["spot"],
        "expiry": quote["expiry"],
        "strike": quote["strike"],
        "option_type": option_type.lower(),
        "market_price": market_price,
        "model_price": model_price,
        "implied_volatility": implied_volatility,
        "risk_free_rate": risk_free["annual_rate"],
        "pricing_gap": pricing_gap,
        "contract_symbol": quote["symbol"],
        "notes": [
            "Model price is based on Black-Scholes style assumptions.",
            "Market price is taken from the option-chain snapshot midpoint when available.",
            "This result is for learning and analysis only, not investment advice.",
        ],
    }


def _black_scholes(spot: float, strike: float, maturity: float, rate: float, volatility: float) -> Dict[str, float]:
    sqrt_t = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility * volatility) * maturity) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    nd1 = _normal_cdf(d1)
    nd2 = _normal_cdf(d2)
    discounted_strike = strike * math.exp(-rate * maturity)

    call = spot * nd1 - discounted_strike * nd2
    put = discounted_strike * _normal_cdf(-d2) - spot * _normal_cdf(-d1)
    return {"call": call, "put": put}


def _black_scholes_greeks(spot: float, strike: float, maturity: float, rate: float, volatility: float) -> Dict[str, Dict[str, float]]:
    sqrt_t = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility * volatility) * maturity) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    pdf_d1 = _normal_pdf(d1)
    nd1 = _normal_cdf(d1)
    nd2 = _normal_cdf(d2)

    gamma = pdf_d1 / (spot * volatility * sqrt_t)
    vega = spot * pdf_d1 * sqrt_t
    call_theta = -(spot * pdf_d1 * volatility) / (2.0 * sqrt_t) - rate * strike * math.exp(-rate * maturity) * nd2
    put_theta = -(spot * pdf_d1 * volatility) / (2.0 * sqrt_t) + rate * strike * math.exp(-rate * maturity) * _normal_cdf(-d2)
    call_rho = strike * maturity * math.exp(-rate * maturity) * nd2
    put_rho = -strike * maturity * math.exp(-rate * maturity) * _normal_cdf(-d2)

    return {
        "call": {
            "delta": nd1,
            "gamma": gamma,
            "theta": call_theta,
            "vega": vega,
            "rho": call_rho,
        },
        "put": {
            "delta": nd1 - 1.0,
            "gamma": gamma,
            "theta": put_theta,
            "vega": vega,
            "rho": put_rho,
        },
    }


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _build_summary(values: List[float]) -> Dict[str, float]:
    sorted_values = sorted(values)
    mean = sum(sorted_values) / len(sorted_values)
    variance = sum((value - mean) ** 2 for value in sorted_values) / len(sorted_values)
    return {
        "min": sorted_values[0],
        "max": sorted_values[-1],
        "mean": mean,
        "std": math.sqrt(variance),
        "p05": _percentile(sorted_values, 0.05),
        "median": _percentile(sorted_values, 0.5),
        "p95": _percentile(sorted_values, 0.95),
    }


def _build_histogram(values: List[float], bins: int) -> List[Dict[str, float | int | str]]:
    min_value = min(values)
    max_value = max(values)
    width = max((max_value - min_value) / bins, 1e-6)
    counts = [0] * bins
    for value in values:
        index = min(int((value - min_value) / width), bins - 1)
        counts[index] += 1

    histogram = []
    for index, count in enumerate(counts):
        start = min_value + index * width
        end = start + width
        histogram.append({"bin": f"{start:.0f}-{end:.0f}", "count": count})
    return histogram


def _percentile(sorted_values: List[float], ratio: float) -> float:
    index = ratio * (len(sorted_values) - 1)
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return sorted_values[lower]
    weight = index - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _clamp_integer(value: int, min_value: int, max_value: int) -> int:
    return min(max(int(round(value)), min_value), max_value)
