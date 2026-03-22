"""API routes (service interface layer).

This module defines the **four core endpoints** requested:
- /extract_feature
- /select_algorithm
- /solve_equation
- /evaluate_result

Key requirements satisfied:
- FastAPI based
- Unified response format: status/success/error/data
- GET/POST supported
- JSON or Form input supported (auto-detected by request Content-Type)
- Parameter validation + explicit exception handling with actionable messages
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, Optional
import inspect
import json
import os

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from algorithm.selector import AlgorithmSelector, AlgorithmSelectionError, concat_features
from config.constants import BoundaryCondition, RequirementLevel
from feature.extractor import (
    DomainFeatureExtractor,
    FeatureExtractionError,
    HardwareFeatureExtractor,
    PhysicsFeatureExtractor,
)
from feedback.evaluator import FeedbackError, ModelOptimizer, ResultEvaluator
from services.ashare_market_data import AShareMarketDataError, fetch_ashare_pair_analysis, fetch_ashare_stock_analysis
from services.ashare_option_data import AShareOptionError, fetch_etf_option_snapshot, fetch_index_option_snapshot
from services.finance import compare_option_with_market, price_black_scholes_1d, price_black_scholes_2d, simulate_stock_dynamics
from services.finance_features import estimate_pair_inputs, estimate_stock_inputs
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    SolverError,
    get_solver,
    solve_heat3d_fdm,
    solve_heat3d_fem,
    solve_heat3d_fvm,
    solve_heat2d_fdm,
    solve_heat2d_fem,
    solve_heat2d_fvm,
    solve_poisson3d_bem,
    solve_poisson3d_fdm,
    solve_poisson3d_fem,
    solve_poisson2d_nonlinear,
    Wave1DParams,
    solve_wave2d_fdm,
    solve_wave2d_fem,
    solve_wave2d_spectral,
    solve_wave1d_fem,
    solve_wave1d,
    solve_wave3d_fdm,
    solve_wave3d_fem,
    solve_wave3d_spectral,
    solve_wave1d_spectral,
    solve_wave1d_spectral_v2,
)
from nlp.baidu_parser import GLOBAL_BAIDU_KEY_STORE, PDEQuestionBaiduParser
from api.llm.llm_factory import LLMFactory
from api.llm.llm_config_manager import LLMConfigManager
from api.llm.universal_parser import PDEQuestionUniversalParser
from api.llm.llm_base import BaseParser
from pydantic import BaseModel
from test_case.benchmark_algorithms import build_report, save_report


router = APIRouter()

SUPPORTED_EQUATIONS = {
    "heat1d": {
        "name": "1D Heat Equation",
        "algorithms": ["fdm", "fvm", "fem", "spectral", "pinn"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前是最完整、最稳定的一维热传导示例，已经接通 FDM/FVM/FEM/Spectral/PINN 多条求解链路。",
    },
    "wave1d": {
        "name": "1D Wave Equation",
        "algorithms": ["fdm", "fem", "spectral"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前稳定支持一维波动方程的 FDM、FEM 和 Spectral 方法，适合做算法对比与教学演示。",
    },
    "poisson1d": {
        "name": "1D Poisson Equation",
        "algorithms": ["fdm", "fem", "spectral", "bem"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持零 Dirichlet 边界下的一维 Poisson 教学基线，可比较 FDM/FEM/Spectral/BEM。",
    },
    "heat2d": {
        "name": "2D Heat Equation",
        "algorithms": ["fdm", "fvm", "fem"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持二维热传导方程的 FDM/FVM/FEM 基线，适合展示二维温度场与算法性能差异。",
    },
    "heat3d": {
        "name": "3D Heat Equation",
        "algorithms": ["fdm", "fvm", "fem"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持零 Dirichlet 边界下的三维热传导 FDM/FVM/FEM 基线，可结合切片结果查看 3D 温度场。",
    },
    "wave2d": {
        "name": "2D Wave Equation",
        "algorithms": ["fdm", "fem", "spectral"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持二维波动方程的 FDM/FEM/Spectral 基线，主要演示边界条件下的波传播与算法差异。",
    },
    "wave3d": {
        "name": "3D Wave Equation",
        "algorithms": ["fdm", "fem", "spectral"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持零 Dirichlet 边界下的三维波动 FDM/FEM/Spectral 基线，可用于 3D 波场切片展示。",
    },
    "poisson2d_nonlinear": {
        "name": "2D Nonlinear Poisson Equation",
        "algorithms": ["fdm"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前是二维非线性 Poisson 的演示型 manufactured-solution 基线，用于说明非线性问题的基本流程。",
    },
    "poisson3d": {
        "name": "3D Poisson Equation",
        "algorithms": ["fdm", "fem", "bem"],
        "strategies": ["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"],
        "note": "当前支持零 Dirichlet 边界下的三维 Poisson FDM/FEM/BEM 教学基线，适合比较体方法与边界方法。",
    },
}

class ParseQuestionIn(BaseModel):
    question: str
    model_name: Optional[str] = "baidu" # Default to baidu for backward compatibility

class AutoSolveIn(BaseModel):
    question: str
    parser_model: Optional[str] = "baidu" # Default to baidu for backward compatibility
    return_full_solution: Optional[bool] = False


class StockSimulationIn(BaseModel):
    initial_price: float = 100.0
    drift: float = 0.08
    volatility: float = 0.2
    horizon: float = 1.0
    steps: int = 252
    paths: int = 2000


class BlackScholes1DIn(BaseModel):
    spot: float = 100.0
    strike: float = 105.0
    maturity: float = 0.5
    volatility: float = 0.25
    rate: float = 0.02


class BlackScholes2DIn(BaseModel):
    spot1: float = 100.0
    spot2: float = 95.0
    strike: float = 100.0
    maturity: float = 0.5
    volatility1: float = 0.25
    volatility2: float = 0.22
    rate: float = 0.02
    correlation: float = 0.3
    grid_size: int = 16


class StockEstimateQuery(BaseModel):
    symbol: str
    lookback_days: int = 252


class PairEstimateQuery(BaseModel):
    symbol1: str
    symbol2: str
    lookback_days: int = 252


class OptionCompareIn(BaseModel):
    symbol: str
    expiry: Optional[str] = None
    strike: Optional[float] = None
    option_type: str = "call"
    maturity_years: Optional[float] = None
    use_market_iv: bool = True


class AShareETFOptionIn(BaseModel):
    underlying: str = "510050"
    option_type: str = "call"
    expiry: Optional[str] = None
    strike: Optional[float] = None
    contract_code: Optional[str] = None


class AShareIndexOptionIn(BaseModel):
    market: str = "hs300"
    option_type: str = "call"
    contract_month: Optional[str] = None
    strike: Optional[float] = None

async def _get_parser_instance(model_name: str) -> BaseParser:
    # Try to create LLM-based parser
    try:
        import api.llm.llm_models  # noqa: F401  # register LLMs lazily to avoid global import side effects

        llm_config_manager = LLMConfigManager()
        llm_config = llm_config_manager.get_model_config(model_name)

        # If config exists, try to create LLM instance
        if llm_config and llm_config.get('api_key'):
            llm_instance = LLMFactory.create_llm(
                model_name=llm_config.get('model_name', model_name),
                api_key=str(llm_config.get('api_key', '')).strip(),
                base_url=llm_config.get('base_url')
            )
            if llm_config.get("model_id"):
                setattr(llm_instance, "model_id", llm_config.get("model_id"))
            return PDEQuestionUniversalParser(llm_instance)
    except Exception as e:
        # Log the error but don't fail, fallback to Baidu parser
        print(f"Error creating LLM-based parser for {model_name}: {e}")

    # Fallback to Baidu parser
    return PDEQuestionBaiduParser()

# Singletons for the service process.
selector = AlgorithmSelector(model_dir="model")
evaluator = ResultEvaluator()
optimizer = ModelOptimizer(model_dir="model", feedback_dir="result")


def _score_to_level(score: float) -> str:
    """Map numeric score [0,1] to high/medium/low for existing feature pipeline."""
    s = float(score)
    if s >= 0.92:
        return "high"
    if s >= 0.85:
        return "medium"
    return "low"


def _resource_to_budget(score: float) -> float:
    """Ensure resource budget in (0,1]."""
    s = float(score)
    if s <= 0:
        return 0.7
    if s > 1:
        return 1.0
    return s


_PDE_POSITIVE_HINTS = (
    "pde",
    "偏微分",
    "热传导",
    "热方程",
    "波动方程",
    "泊松方程",
    "poisson",
    "wave equation",
    "heat equation",
    "heat1d",
    "wave1d",
    "u_t",
    "u_tt",
    "u_xx",
    "u_x",
    "边界条件",
    "初始条件",
    "dirichlet",
    "neumann",
)

_NON_PDE_HINTS = (
    "质量",
    "受力",
    "牛顿",
    "加速度",
    "末速度",
    "位移",
    "动摩擦",
    "摩擦因数",
    "水平面",
    "自由落体",
    "小车",
    "斜面",
)


def _validate_parsed_problem(question: str, parsed: Dict[str, Any]) -> Optional[str]:
    q = (question or "").strip().lower()
    physics_params = parsed.get("physics_params", {}) if isinstance(parsed.get("physics_params"), dict) else {}
    equation_type = str(physics_params.get("equation_type", "")).strip().lower()
    problem_size = physics_params.get("problem_size", None)

    has_pde_hint = any(token in q for token in _PDE_POSITIVE_HINTS)
    has_non_pde_hint = any(token in question for token in _NON_PDE_HINTS)

    if has_non_pde_hint and not has_pde_hint:
        return "这道题看起来不是偏微分方程题，而是普通力学/物理应用题，当前自动求解器不支持。"

    if equation_type not in ("heat1d", "heat2d", "heat3d", "wave1d", "wave2d", "wave3d", "poisson1d", "poisson3d", "poisson2d_nonlinear"):
        return "当前仅支持 heat1d、heat2d、heat3d、wave1d、wave2d、wave3d、poisson1d、poisson3d 和 poisson2d_nonlinear。"

    try:
        if int(problem_size) <= 0:
            return "题目未能解析出有效的 PDE 网格规模或自由度，当前自动求解器不支持继续求解。"
    except Exception:
        return "题目未能解析出有效的 PDE 网格规模或自由度，当前自动求解器不支持继续求解。"

    return None


def _repair_fallback_parsed_problem(question: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(parsed, dict):
        return parsed
    text = (question or "").lower()
    physics_params = parsed.get("physics_params")
    if not isinstance(physics_params, dict):
        physics_params = {}
        parsed["physics_params"] = physics_params

    is_3d = ("3d" in text) or ("三维" in text) or ("^3" in text) or ("立方体" in text)

    if ("poisson" in text or "泊松" in text) and is_3d:
        physics_params["equation_type"] = "poisson3d"
        physics_params["dimension"] = 3
        physics_params["linear"] = True
        physics_params["stationary"] = True
        physics_params["boundary_condition"] = physics_params.get("boundary_condition", "dirichlet")
        physics_params["problem_size"] = max(int(physics_params.get("problem_size", 21 * 21 * 21)), 21 * 21 * 21)
    elif ("heat" in text or "热传导" in text or "热方程" in text) and is_3d:
        physics_params["equation_type"] = "heat3d"
        physics_params["dimension"] = 3
        physics_params["linear"] = True
        physics_params["stationary"] = False
        physics_params["boundary_condition"] = physics_params.get("boundary_condition", "dirichlet")
        physics_params["problem_size"] = max(int(physics_params.get("problem_size", 11 * 11 * 11)), 11 * 11 * 11)
    elif ("wave" in text or "波动" in text) and is_3d:
        physics_params["equation_type"] = "wave3d"
        physics_params["dimension"] = 3
        physics_params["linear"] = True
        physics_params["stationary"] = False
        physics_params["boundary_condition"] = physics_params.get("boundary_condition", "dirichlet")
        physics_params["problem_size"] = max(int(physics_params.get("problem_size", 15 * 15 * 15)), 15 * 15 * 15)

    return parsed


def _preview_list(values: list[float], head: int = 50, tail: int = 50) -> Dict[str, Any]:
    """Return a small preview + stats to keep Swagger responsive."""
    n = len(values)
    if n == 0:
        return {"count": 0, "head": [], "tail": [], "stats": None}
    arr = np.asarray(values, dtype=float)
    stats = {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
    }
    return {
        "count": n,
        "head": values[: min(head, n)],
        "tail": values[max(0, n - tail) :],
        "stats": stats,
    }


def _validate_zero_dirichlet_3d(
    *,
    eq_type: str,
    bc_type: BoundaryCondition,
    left_bc: float,
    right_bc: float,
) -> Optional[Dict[str, Any]]:
    if bc_type != BoundaryCondition.DIRICHLET:
        return _err(f"{eq_type} currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
    if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
        return _err(f"{eq_type} currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")
    return None


def _pack_3d_steady_result(
    *,
    eq_type: str,
    algorithm_key: str,
    shape: list[int],
    solution: np.ndarray,
    solve_info: Dict[str, Any],
    return_full: bool,
) -> Dict[str, Any]:
    sol_list = solution.reshape(-1).tolist()
    data = {
        "shape": shape,
        "equation_type": eq_type,
        "recommended_algorithm": algorithm_key,
        "executed_algorithm": solve_info.get("algorithm", algorithm_key),
        "solve_info": solve_info,
        "solution_preview": _preview_list(sol_list),
    }
    if return_full:
        data["solution"] = sol_list
    return data


def _pack_3d_transient_result(
    *,
    eq_type: str,
    algorithm_key: str,
    shape: list[int],
    solution: np.ndarray,
    info_pack: Dict[str, Any],
    return_full: bool,
) -> Dict[str, Any]:
    sol_list = solution.reshape(-1).tolist()
    data = {
        "shape": shape,
        "equation_type": eq_type,
        "recommended_algorithm": algorithm_key,
        "executed_algorithm": info_pack["solve_info"]["algorithm"],
        "solve_info": info_pack["solve_info"],
        "validation": info_pack["validation"],
        "solution_preview": _preview_list(sol_list),
    }
    if return_full:
        data["solution"] = sol_list
    return data


def _solve_poisson3d_case(
    *,
    algorithm_key: str,
    nx: int,
    ny: int,
    nz: int,
    Lx: float,
    Ly: float,
    Lz: float,
    return_full: bool,
) -> Dict[str, Any]:
    if algorithm_key == "fem":
        sol3d, info = solve_poisson3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
    elif algorithm_key == "bem":
        sol3d, info = solve_poisson3d_bem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
    else:
        sol3d, info = solve_poisson3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
    return _pack_3d_steady_result(
        eq_type="poisson3d",
        algorithm_key=algorithm_key,
        shape=[nz, ny, nx],
        solution=sol3d,
        solve_info=info,
        return_full=return_full,
    )


def _solve_heat3d_case(
    *,
    algorithm_key: str,
    nx: int,
    ny: int,
    nz: int,
    Lx: float,
    Ly: float,
    Lz: float,
    k: float,
    t_span: tuple[float, float],
    nt: int,
    return_full: bool,
) -> Dict[str, Any]:
    if algorithm_key == "fvm":
        sol3d, info_pack = solve_heat3d_fvm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=t_span, nt=nt)
    elif algorithm_key == "fem":
        sol3d, info_pack = solve_heat3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=t_span, nt=nt)
    else:
        sol3d, info_pack = solve_heat3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=t_span, nt=nt)
    return _pack_3d_transient_result(
        eq_type="heat3d",
        algorithm_key=algorithm_key,
        shape=[nz, ny, nx],
        solution=sol3d,
        info_pack=info_pack,
        return_full=return_full,
    )


def _solve_wave3d_case(
    *,
    algorithm_key: str,
    nx: int,
    ny: int,
    nz: int,
    Lx: float,
    Ly: float,
    Lz: float,
    c: float,
    t_span: tuple[float, float],
    nt: int,
    return_full: bool,
) -> Dict[str, Any]:
    if algorithm_key == "fem":
        sol3d, info_pack = solve_wave3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=t_span, nt=nt)
    elif algorithm_key == "spectral":
        sol3d, info_pack = solve_wave3d_spectral(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=t_span, nt=nt)
    else:
        sol3d, info_pack = solve_wave3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=t_span, nt=nt)
    return _pack_3d_transient_result(
        eq_type="wave3d",
        algorithm_key=algorithm_key,
        shape=[nz, ny, nx],
        solution=sol3d,
        info_pack=info_pack,
        return_full=return_full,
    )


def _ok(data: Any) -> Dict[str, Any]:
    return {"status": "ok", "success": True, "error": None, "data": data}


def _err(message: str, *, code: str = "BAD_REQUEST", details: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "data": None,
    }


@router.get("/supported_equations")
async def supported_equations() -> Dict[str, Any]:
    return _ok({"equations": SUPPORTED_EQUATIONS})


@router.get("/benchmark/latest")
async def benchmark_latest() -> Dict[str, Any]:
    benchmark_dir = "benchmark"
    latest_path: Optional[str] = None
    if os.path.isdir(benchmark_dir):
        files = [
            os.path.join(benchmark_dir, name)
            for name in os.listdir(benchmark_dir)
            if name.startswith("benchmark_") and name.endswith(".json")
        ]
        if files:
            latest_path = max(files, key=os.path.getmtime)

    if latest_path is None:
        report = build_report()
        latest_path = save_report(report, output_dir=benchmark_dir)
    else:
        with open(latest_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    return _ok({"report": report, "path": latest_path})


@router.post("/finance/stocks/simulate")
async def finance_simulate_stocks(payload: StockSimulationIn) -> Dict[str, Any]:
    data = simulate_stock_dynamics(
        initial_price=payload.initial_price,
        drift=payload.drift,
        volatility=payload.volatility,
        horizon=payload.horizon,
        steps=payload.steps,
        paths=payload.paths,
    )
    return _ok(data)


@router.post("/finance/options/black_scholes_1d")
async def finance_black_scholes_1d(payload: BlackScholes1DIn) -> Dict[str, Any]:
    data = price_black_scholes_1d(
        spot=payload.spot,
        strike=payload.strike,
        maturity=payload.maturity,
        volatility=payload.volatility,
        rate=payload.rate,
    )
    return _ok(data)


@router.post("/finance/options/black_scholes_2d")
async def finance_black_scholes_2d(payload: BlackScholes2DIn) -> Dict[str, Any]:
    data = price_black_scholes_2d(
        spot1=payload.spot1,
        spot2=payload.spot2,
        strike=payload.strike,
        maturity=payload.maturity,
        volatility1=payload.volatility1,
        volatility2=payload.volatility2,
        rate=payload.rate,
        correlation=payload.correlation,
        grid_size=payload.grid_size,
    )
    return _ok(data)


@router.get("/finance/market/stock/{symbol}")
async def finance_market_stock(symbol: str, lookback_days: int = 252) -> Dict[str, Any]:
    data = estimate_stock_inputs(symbol, lookback_days)
    return _ok(data)


@router.get("/finance/market/pair")
async def finance_market_pair(symbol1: str, symbol2: str, lookback_days: int = 252) -> Dict[str, Any]:
    data = estimate_pair_inputs(symbol1, symbol2, lookback_days)
    return _ok(data)


@router.post("/finance/options/compare_market")
async def finance_option_compare_market(payload: OptionCompareIn) -> Dict[str, Any]:
    data = compare_option_with_market(
        symbol=payload.symbol,
        expiry=payload.expiry,
        strike=payload.strike,
        option_type=payload.option_type,
        maturity_years=payload.maturity_years,
        use_market_iv=payload.use_market_iv,
    )
    return _ok(data)


@router.get("/finance/ashare/stock/{symbol}")
async def finance_ashare_stock(symbol: str, lookback_days: int = 252, force_history_only: bool = False) -> Dict[str, Any]:
    try:
        data = fetch_ashare_stock_analysis(symbol, lookback_days, force_history_only=force_history_only)
        return _ok(data)
    except AShareMarketDataError as exc:
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股数据源暂时不可用，可能是免费行情源断连、限流或当前网络链路不稳定，请稍后重试。",
                code="ASHARE_DATA_UNAVAILABLE",
                details={"source": "akshare", "message": str(exc)},
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股实时数据抓取失败，当前免费数据源连接不稳定，请稍后重试。",
                code="ASHARE_DATA_UPSTREAM_ERROR",
                details={"source": "akshare", "message": str(exc), "symbol": symbol},
            ),
        ) from exc


@router.get("/finance/ashare/pair")
async def finance_ashare_pair(symbol1: str, symbol2: str, lookback_days: int = 252) -> Dict[str, Any]:
    try:
        data = fetch_ashare_pair_analysis(symbol1, symbol2, lookback_days)
        return _ok(data)
    except AShareMarketDataError as exc:
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股双股票数据抓取失败，通常是上游免费数据源断连或短时不可用，请稍后重试。",
                code="ASHARE_PAIR_UNAVAILABLE",
                details={"source": "akshare", "symbol1": symbol1, "symbol2": symbol2, "message": str(exc)},
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股双股票联动数据抓取失败，当前免费数据源连接不稳定，请稍后重试。",
                code="ASHARE_PAIR_UPSTREAM_ERROR",
                details={"source": "akshare", "symbol1": symbol1, "symbol2": symbol2, "message": str(exc)},
            ),
        ) from exc


@router.post("/finance/ashare/etf_option")
async def finance_ashare_etf_option(payload: AShareETFOptionIn) -> Dict[str, Any]:
    try:
        data = fetch_etf_option_snapshot(
            underlying=payload.underlying,
            option_type=payload.option_type,
            expiry=payload.expiry,
            strike=payload.strike,
            contract_code=payload.contract_code,
        )
        return _ok(data)
    except AShareOptionError as exc:
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股ETF期权数据源暂时不可用，请稍后重试。",
                code="ASHARE_ETF_OPTION_UNAVAILABLE",
                details={"source": "akshare", "underlying": payload.underlying, "message": str(exc)},
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股ETF期权数据抓取失败，当前免费数据源连接不稳定，请稍后重试。",
                code="ASHARE_ETF_OPTION_UPSTREAM_ERROR",
                details={"source": "akshare", "underlying": payload.underlying, "message": str(exc)},
            ),
        ) from exc


@router.post("/finance/ashare/index_option")
async def finance_ashare_index_option(payload: AShareIndexOptionIn) -> Dict[str, Any]:
    try:
        data = fetch_index_option_snapshot(
            market=payload.market,
            option_type=payload.option_type,
            contract_month=payload.contract_month,
            strike=payload.strike,
        )
        return _ok(data)
    except AShareOptionError as exc:
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股股指期权数据源暂时不可用，请稍后重试。",
                code="ASHARE_INDEX_OPTION_UNAVAILABLE",
                details={"source": "akshare", "market": payload.market, "message": str(exc)},
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=_err(
                "A股股指期权数据抓取失败，当前免费数据源连接不稳定，请稍后重试。",
                code="ASHARE_INDEX_OPTION_UPSTREAM_ERROR",
                details={"source": "akshare", "market": payload.market, "message": str(exc)},
            ),
        ) from exc


async def _read_payload(request: Request) -> Dict[str, Any]:
    """Read payload from JSON or form; for GET use query params."""
    if request.method.upper() == "GET":
        return dict(request.query_params)
    ctype = (request.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            body = await request.json()
            if isinstance(body, dict):
                return body
            raise ValueError("JSON body must be an object.")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}") from e
    # Default: form/multipart
    try:
        form = await request.form()
        return dict(form)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"表单解析失败: {e}") from e


def _parse_requirement_level(x: Any, field: str) -> RequirementLevel:
    try:
        if isinstance(x, RequirementLevel):
            return x
        return RequirementLevel(str(x).strip().lower())
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"{field} 必须是 high/medium/low。") from e


def _to_float(x: Any, field: str) -> float:
    try:
        return float(x)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"{field} 必须是数值。") from e


def _to_int(x: Any, field: str) -> int:
    try:
        return int(float(x))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"{field} 必须是整数。") from e


@router.api_route("/extract_feature", methods=["GET", "POST"])
async def extract_feature(request: Request) -> Dict[str, Any]:
    """Feature extraction endpoint.

    Input:
    - physics: structured params. Minimal required keys:
      - equation_type: "heat1d", "wave1d" or "poisson2d_nonlinear"
      - (for heat1d/wave1d) dimension/linearity/stationarity/boundary_condition/problem_size or inferable keys
    - domain: accuracy/realtime/resource_budget
    Output:
    - normalized physics/hardware/domain vectors
    - concatenated 13-dim vector (x13)
    """
    payload = await _read_payload(request)
    try:
        eq_type = str(payload.get("equation_type", "heat1d")).strip().lower()

        # Physics features (normalized)
        if eq_type in ("heat1d", "poisson1d"):
            nx = _to_int(payload.get("nx", 101), "nx")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 1,
                    "linearity": 0,
                    "stationarity": 0 if eq_type == "poisson1d" else 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx,
                }
            )
        elif eq_type == "heat2d":
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny,
                }
            )
        elif eq_type == "heat3d":
            nx = _to_int(payload.get("nx", 11), "nx")
            ny = _to_int(payload.get("ny", 11), "ny")
            nz = _to_int(payload.get("nz", 11), "nz")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 3,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny * nz,
                }
            )
        elif eq_type == "wave1d":
            nx = _to_int(payload.get("nx", 101), "nx")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 1,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx,
                }
            )
        elif eq_type == "wave2d":
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny,
                }
            )
        elif eq_type == "wave3d":
            nx = _to_int(payload.get("nx", 15), "nx")
            ny = _to_int(payload.get("ny", 15), "ny")
            nz = _to_int(payload.get("nz", 15), "nz")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 3,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny * nz,
                }
            )
        elif eq_type == "poisson2d_nonlinear":
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 1,
                    "stationarity": 0,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny,
                }
            )
        elif eq_type == "poisson3d":
            nx = _to_int(payload.get("nx", 21), "nx")
            ny = _to_int(payload.get("ny", 21), "ny")
            nz = _to_int(payload.get("nz", 21), "nz")
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 3,
                    "linearity": 0,
                    "stationarity": 0,
                    "boundary_condition": str(payload.get("boundary_condition", "dirichlet")),
                    "problem_size": nx * ny * nz,
                }
            )
        else:
            return _err("equation_type 必须是 heat1d、heat2d、heat3d、wave1d、wave2d、wave3d、poisson1d、poisson3d 或 poisson2d_nonlinear。", code="INVALID_EQUATION_TYPE")

        physics_vec = PhysicsFeatureExtractor.normalize(physics_out["vector"])

        # Hardware features (normalized)
        hw_raw = HardwareFeatureExtractor.extract()
        hw_vec = HardwareFeatureExtractor.normalize(hw_raw["vector"])

        # Domain features (normalized)
        acc = _parse_requirement_level(payload.get("accuracy", "medium"), "accuracy")
        rt = _parse_requirement_level(payload.get("realtime", "medium"), "realtime")
        rb = payload.get("resource_budget", 0.75)
        domain_out = DomainFeatureExtractor.extract_from_params({"accuracy": acc, "realtime": rt, "resource_budget": rb})
        domain_vec = DomainFeatureExtractor.normalize(domain_out["vector"])

        x13 = concat_features(physics_vec, hw_vec, domain_vec)

        return _ok(
            {
                "equation_type": eq_type,
                "physics": physics_vec.tolist(),
                "hardware": hw_vec.tolist(),
                "domain": domain_vec.tolist(),
                "x13": x13.tolist(),
                "hardware_extra": {"gpu_name": hw_raw.get("gpu_name")},
            }
        )
    except FeatureExtractionError as e:
        return _err(str(e), code="FEATURE_EXTRACTION_ERROR")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        return _err(f"特征提取失败: {e}", code="INTERNAL_ERROR")


@router.api_route("/select_algorithm", methods=["GET", "POST"])
async def select_algorithm(request: Request) -> Dict[str, Any]:
    """Algorithm recommendation endpoint (M: F×H×D→A)."""
    payload = await _read_payload(request)
    try:
        strategy = str(payload.get("strategy", "static_rf")).strip().lower()
        if strategy not in ("static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"):
            return _err("strategy 必须是 static_rf/static_xgb/dynamic_rl/mlp_nn/gnn_selector。", code="INVALID_STRATEGY")

        physics = np.array(payload.get("physics", []), dtype=float)
        hardware = np.array(payload.get("hardware", []), dtype=float)
        domain = np.array(payload.get("domain", []), dtype=float)

        # Auto-load/train to keep the service "no extra config" runnable.
        if strategy in ("static_rf", "static_xgb", "mlp_nn", "gnn_selector"):
            selector._load_or_train_static(strategy)  # type: ignore[attr-defined]
        else:
            if selector.rl_agent is None:
                selector.train_dynamic(episodes=120)  # small default for quick runnable service
                selector.save_dynamic()

        # DEBUG_BREAKPOINT_API_SELECT: set breakpoint here.
        out = selector.select(physics=physics, hardware=hardware, domain=domain, strategy=strategy)  # type: ignore[arg-type]
        return _ok(out)
    except AlgorithmSelectionError as e:
        return _err(str(e), code="ALGORITHM_SELECTION_ERROR")
    except Exception as e:  # noqa: BLE001
        return _err(f"算法推荐失败: {e}", code="INTERNAL_ERROR")


@router.api_route("/solve_equation", methods=["GET", "POST"])
async def solve_equation(request: Request) -> Dict[str, Any]:
    """Equation solving endpoint."""
    payload = await _read_payload(request)
    try:
        eq_type = str(payload.get("equation_type", "heat1d")).strip().lower()
        algorithm_key = str(payload.get("algorithm_key", "")).strip().lower()
        if algorithm_key not in ("fdm", "fvm", "fem", "spectral", "pinn", "bem"):
            return _err("algorithm_key 必须是 fdm/fvm/fem/spectral。", code="INVALID_ALGORITHM_KEY")

        # Default: do NOT return huge solution arrays in Swagger.
        return_full = str(payload.get("return_full_solution", "false")).strip().lower() in ("1", "true", "yes")

        # DEBUG_BREAKPOINT_API_SOLVE: set breakpoint here.
        if eq_type == "poisson3d":
            if algorithm_key not in ("fdm", "fem", "bem"):
                return _err("poisson3d currently only supports FDM/FEM/BEM.", code="UNSUPPORTED_ALGORITHM")
            nx = _to_int(payload.get("nx", 21), "nx")
            ny = _to_int(payload.get("ny", 21), "ny")
            nz = _to_int(payload.get("nz", 21), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            bc_error = _validate_zero_dirichlet_3d(eq_type=eq_type, bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            return _ok(
                _solve_poisson3d_case(
                    algorithm_key=algorithm_key,
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    return_full=True,
                )
            )

        if eq_type == "heat3d":
            if algorithm_key not in ("fdm", "fvm", "fem"):
                return _err("heat3d currently only supports FDM/FVM/FEM.", code="UNSUPPORTED_ALGORITHM")
            k = _to_float(payload.get("k", 1.0), "k")
            nx = _to_int(payload.get("nx", 11), "nx")
            ny = _to_int(payload.get("ny", 11), "ny")
            nz = _to_int(payload.get("nz", 11), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.02), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            bc_error = _validate_zero_dirichlet_3d(eq_type=eq_type, bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            return _ok(
                _solve_heat3d_case(
                    algorithm_key=algorithm_key,
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    k=k,
                    t_span=(t0, t1),
                    nt=nt,
                    return_full=True,
                )
            )

        if eq_type == "wave3d":
            if algorithm_key not in ("fdm", "fem", "spectral"):
                return _err("wave3d currently only supports FDM/FEM/spectral.", code="UNSUPPORTED_ALGORITHM")
            c = _to_float(payload.get("c", 1.0), "c")
            nx = _to_int(payload.get("nx", 15), "nx")
            ny = _to_int(payload.get("ny", 15), "ny")
            nz = _to_int(payload.get("nz", 15), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.15), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            bc_error = _validate_zero_dirichlet_3d(eq_type=eq_type, bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            return _ok(
                _solve_wave3d_case(
                    algorithm_key=algorithm_key,
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    c=c,
                    t_span=(t0, t1),
                    nt=nt,
                    return_full=True,
                )
            )

        if eq_type == "poisson1d":
            if algorithm_key in ("fvm", "pinn"):
                return _err("poisson1d 当前尚未实现 FVM。", code="UNSUPPORTED_ALGORITHM")
            L = _to_float(payload.get("L", 1.0), "L")
            nx = _to_int(payload.get("nx", 101), "nx")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("poisson1d 当前仅支持 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            params = Heat1DParams(k=1.0, L=L, nx=nx, t_span=(0.0, 0.0), enforce_nonnegativity=False)
            bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)

            def initial_fn(x: np.ndarray) -> np.ndarray:
                return np.zeros_like(x, dtype=float)

            def source_fn(x: np.ndarray, t: float) -> np.ndarray:
                return (math.pi ** 2) * np.sin(math.pi * x / float(L))

            solver = get_solver(algorithm_key)
            sol, info, validation = solver.solve(params=params, bc=bc, initial=initial_fn, source=source_fn)
            sol_list = sol.tolist()
            data = {
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "poisson3d":
            if algorithm_key not in ("fdm", "fem", "bem"):
                return _err("poisson3d 当前仅支持 FDM/FEM/BEM。", code="UNSUPPORTED_ALGORITHM")
            nx = _to_int(payload.get("nx", 21), "nx")
            ny = _to_int(payload.get("ny", 21), "ny")
            nz = _to_int(payload.get("nz", 21), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("poisson3d 当前仅支持 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("poisson3d 当前要求零 Dirichlet 边界。", code="INVALID_BOUNDARY_VALUE")
            if algorithm_key == "fem":
                sol3d, info = solve_poisson3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            elif algorithm_key == "bem":
                sol3d, info = solve_poisson3d_bem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            else:
                sol3d, info = solve_poisson3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.get("algorithm", algorithm_key),
                "solve_info": info,
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "heat1d":
            k = _to_float(payload.get("k", 1.0), "k")
            L = _to_float(payload.get("L", 1.0), "L")
            nx = _to_int(payload.get("nx", 101), "nx")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.1), "t1")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            enforce_nonneg = str(payload.get("enforce_nonnegativity", "true")).strip().lower() not in ("0", "false", "no")

            params = Heat1DParams(k=k, L=L, nx=nx, t_span=(t0, t1), enforce_nonnegativity=enforce_nonneg)
            if bc_type == BoundaryCondition.DIRICHLET:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            elif bc_type == BoundaryCondition.NEUMANN:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            else:
                bc = BoundarySpec(
                    bc_type=bc_type,
                    left_mixed=(1.0, 1.0, lambda t: left_bc),
                    right_mixed=(1.0, 1.0, lambda t: right_bc),
                )

            initial_kind = str(payload.get("initial", "sine_nonnegative")).strip().lower()

            def initial_fn(x: np.ndarray) -> np.ndarray:
                if initial_kind == "constant":
                    return np.full_like(x, 1.0, dtype=float)
                return np.maximum(0.0, np.sin(np.pi * x / float(L)))

            solver = get_solver(algorithm_key)
            sol, info, validation = solver.solve(params=params, bc=bc, initial=initial_fn)
            sol_list = sol.tolist()
            data = {
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "heat3d":
            if algorithm_key not in ("fdm", "fvm", "fem"):
                return _err("heat3d currently only supports FDM/FVM/FEM.", code="UNSUPPORTED_ALGORITHM")
            k = _to_float(payload.get("k", 1.0), "k")
            nx = _to_int(payload.get("nx", 11), "nx")
            ny = _to_int(payload.get("ny", 11), "ny")
            nz = _to_int(payload.get("nz", 11), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.02), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("heat3d currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("heat3d currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")

            if algorithm_key == "fvm":
                sol3d, info_pack = solve_heat3d_fvm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "fem":
                sol3d, info_pack = solve_heat3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(t0, t1), nt=nt)
            else:
                sol3d, info_pack = solve_heat3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(t0, t1), nt=nt)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "wave3d":
            if algorithm_key not in ("fdm", "fem", "spectral"):
                return _err("wave3d currently only supports FDM/FEM/spectral.", code="UNSUPPORTED_ALGORITHM")
            c = _to_float(payload.get("c", 1.0), "c")
            nx = _to_int(payload.get("nx", 15), "nx")
            ny = _to_int(payload.get("ny", 15), "ny")
            nz = _to_int(payload.get("nz", 15), "nz")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            Lz = _to_float(payload.get("Lz", payload.get("L", 1.0)), "Lz")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.15), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("wave3d currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("wave3d currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")
            if algorithm_key == "fem":
                sol3d, info_pack = solve_wave3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "spectral":
                sol3d, info_pack = solve_wave3d_spectral(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(t0, t1), nt=nt)
            else:
                sol3d, info_pack = solve_wave3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(t0, t1), nt=nt)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "heat2d":
            if algorithm_key not in ("fdm", "fvm", "fem"):
                return _err("heat2d 当前仅支持 FDM/FVM/FEM。", code="UNSUPPORTED_ALGORITHM")
            k = _to_float(payload.get("k", 1.0), "k")
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.05), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("heat2d 当前仅支持零 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("heat2d 当前要求零 Dirichlet 边界。", code="INVALID_BOUNDARY_VALUE")

            if algorithm_key == "fvm":
                sol2d, info_pack = solve_heat2d_fvm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "fem":
                sol2d, info_pack = solve_heat2d_fem(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            else:
                sol2d, info_pack = solve_heat2d_fdm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            sol_list = sol2d.reshape(-1).tolist()
            data = {
                "shape": [ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "wave2d":
            if algorithm_key not in ("fdm", "fem", "spectral"):
                return _err("wave2d currently only supports FDM/FEM/spectral.", code="UNSUPPORTED_ALGORITHM")
            c = _to_float(payload.get("c", 1.0), "c")
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            Lx = _to_float(payload.get("Lx", payload.get("L", 1.0)), "Lx")
            Ly = _to_float(payload.get("Ly", payload.get("L", 1.0)), "Ly")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.2), "t1")
            nt = _to_int(payload.get("nt", 200), "nt")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("wave2d currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("wave2d currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")

            if algorithm_key == "fem":
                sol2d, info_pack = solve_wave2d_fem(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "spectral":
                sol2d, info_pack = solve_wave2d_spectral(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1))
            else:
                sol2d, info_pack = solve_wave2d_fdm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1), nt=nt)
            sol_list = sol2d.reshape(-1).tolist()
            data = {
                "shape": [ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        # Canonical wave1d fallback rule: only spectral with non-Dirichlet BC falls back to FDM.
        if eq_type == "wave1d":
            if algorithm_key == "fvm":
                return _err("wave1d 当前尚未实现 FVM。", code="UNSUPPORTED_ALGORITHM")
            c = _to_float(payload.get("c", 1.0), "c")
            L = _to_float(payload.get("L", 1.0), "L")
            nx = _to_int(payload.get("nx", 101), "nx")
            nt = _to_int(payload.get("nt", 200), "nt")
            t0 = _to_float(payload.get("t0", 0.0), "t0")
            t1 = _to_float(payload.get("t1", 0.5), "t1")
            bc_type = BoundaryCondition(str(payload.get("bc_type", "dirichlet")).strip().lower())
            left_bc = _to_float(payload.get("left_bc", 0.0), "left_bc")
            right_bc = _to_float(payload.get("right_bc", 0.0), "right_bc")

            params = Wave1DParams(c=c, L=L, nx=nx, t_span=(t0, t1), nt=nt)
            if bc_type == BoundaryCondition.DIRICHLET:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            elif bc_type == BoundaryCondition.NEUMANN:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            else:
                return _err("wave1d 当前仅支持 Dirichlet 或 Neumann 边界。", code="INVALID_BOUNDARY_TYPE")

            initial_kind = str(payload.get("initial", "sine")).strip().lower()
            velocity_value = _to_float(payload.get("initial_velocity", 0.0), "initial_velocity")

            def initial_fn(x: np.ndarray) -> np.ndarray:
                if initial_kind == "constant":
                    return np.full_like(x, 1.0, dtype=float)
                return np.sin(np.pi * x / float(L))

            def velocity_fn(x: np.ndarray) -> np.ndarray:
                return np.full_like(x, velocity_value, dtype=float)

            if algorithm_key == "spectral":
                sol, info, validation = solve_wave1d_spectral_v2(
                    params=params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            elif algorithm_key == "fem":
                sol, info, validation = solve_wave1d_fem(
                    params=params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            else:
                sol, info, validation = solve_wave1d(
                    params=params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            sol_list = sol.tolist()
            data = {
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        if eq_type == "poisson2d_nonlinear":
            if algorithm_key == "fvm":
                return _err("poisson2d_nonlinear 当前尚未实现 FVM。", code="UNSUPPORTED_ALGORITHM")
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            Lx = _to_float(payload.get("Lx", 1.0), "Lx")
            Ly = _to_float(payload.get("Ly", 1.0), "Ly")
            tol = _to_float(payload.get("tol", 1e-6), "tol")
            max_iter = _to_int(payload.get("max_iter", 200), "max_iter")
            sol2d, info = solve_poisson2d_nonlinear(nx=nx, ny=ny, Lx=Lx, Ly=Ly, tol=tol, max_iter=max_iter)
            sol_list = sol2d.reshape(-1).tolist()
            data = {
                "shape": [ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.get("algorithm", algorithm_key) if isinstance(info, dict) else algorithm_key,
                "solve_info": info,
                "solution_preview": _preview_list(sol_list),
                "solution": sol_list,
            }
            return _ok(data)

        return _err("equation_type 必须是 heat1d、heat2d、heat3d、wave1d、wave2d、wave3d、poisson1d、poisson3d 或 poisson2d_nonlinear。", code="INVALID_EQUATION_TYPE")
    except (SolverError, ValueError) as e:
        return _err(str(e), code="SOLVER_ERROR")
    except Exception as e:  # noqa: BLE001
        return _err(f"求解失败: {e}", code="INTERNAL_ERROR")


@router.api_route("/evaluate_result", methods=["GET", "POST"])
async def evaluate_result(request: Request) -> Dict[str, Any]:
    """Result evaluation + model optimization feedback endpoint."""
    payload = await _read_payload(request)
    try:
        # Required inputs
        solution = np.array(payload.get("solution", []), dtype=float).reshape(-1)
        solve_info = payload.get("solve_info", {})
        if not isinstance(solve_info, dict):
            return _err("solve_info 必须是对象(dict)。", code="INVALID_SOLVE_INFO")

        acc = _parse_requirement_level(payload.get("accuracy", "medium"), "accuracy")
        rt = _parse_requirement_level(payload.get("realtime", "medium"), "realtime")
        rb = payload.get("resource_budget", 0.75)

        validation = payload.get("validation", None)

        # Evaluate
        # DEBUG_BREAKPOINT_API_EVAL: set breakpoint here.
        report = evaluator.evaluate(
            solution=solution,
            solve_info=solve_info,
            domain_requirements={"accuracy": acc, "realtime": rt, "resource_budget": rb},
            validation=validation if isinstance(validation, dict) else None,
        )
        report_path = evaluator.save_report(report, result_dir="result")

        # Optimization feedback (optional but recommended)
        x13 = payload.get("x13", None)
        selected_algorithm = str(payload.get("selected_algorithm", solve_info.get("algorithm", ""))).strip().lower()
        opt_status: Dict[str, Any] = {"skipped": True}
        if x13 is not None:
            x13_arr = np.array(x13, dtype=float).reshape(-1)
            sample_path = optimizer.append_training_sample(x13=x13_arr, algorithm_key=selected_algorithm)
            retrain_strategy = str(payload.get("retrain_strategy", "static_rf")).strip().lower()
            train_info = optimizer.retrain_static_with_feedback(strategy=retrain_strategy)
            opt_status = {"skipped": False, "feedback_saved_to": sample_path, "retrained": train_info}

        return _ok({"report": report, "saved_to": report_path, "optimizer": opt_status})
    except (FeedbackError, AlgorithmSelectionError, AlgorithmSelectionError) as e:
        return _err(str(e), code="FEEDBACK_ERROR")
    except Exception as e:  # noqa: BLE001
        return _err(f"评估失败: {e}", code="INTERNAL_ERROR")


@router.api_route("/api/parse_question", methods=["POST"])
async def api_parse_question(request_body: ParseQuestionIn) -> Dict[str, Any]:
    """Test endpoint: parse question only (no solve)."""
    try:
        question = request_body.question
        model_name = request_body.model_name
        if not question:
            return _err("question 不能为空。", code="INVALID_PARAM")

        # DEBUG_BREAKPOINT_PARSE_QUESTION: set breakpoint here.
        pde_question_parser = await _get_parser_instance(model_name)
        if inspect.iscoroutinefunction(pde_question_parser.parse):
            parsed = await pde_question_parser.parse(question)
        else:
            parsed = pde_question_parser.parse(question)
        validation_error = _validate_parsed_problem(question, parsed)
        if validation_error:
            return _err(
                validation_error,
                code="UNSUPPORTED_QUESTION",
                details={"parsed": parsed},
            )
        msg = (
            "当前使用大模型智能解析。"
            if parsed.get("parser_mode") not in (None, "rule_based")
            else "当前使用规则解析（未配置 Key 或大模型解析失败后自动降级）。"
        )
        return _ok({"message": msg, "parsed": parsed, "key_configured": LLMConfigManager().is_llm_configured(model_name)})
    except Exception as e:  # noqa: BLE001
        return _err(str(e), code="PARSE_ERROR")


@router.api_route("/api/auto_solve", methods=["POST"])
async def api_auto_solve(request_body: AutoSolveIn) -> Dict[str, Any]:
    """Full pipeline: natural language -> JSON -> features -> selection -> solve -> evaluate."""
    try:
        question = request_body.question
        parser_model = request_body.parser_model
        return_full = request_body.return_full_solution
        if not question:
            return _err("question 不能为空。", code="INVALID_PARAM")

        pde_question_parser = await _get_parser_instance(parser_model)
        parsed = {} # Initialize parsed to an empty dictionary
        try:
            if inspect.iscoroutinefunction(pde_question_parser.parse):
                parsed = await pde_question_parser.parse(question)
            else:
                parsed = pde_question_parser.parse(question)
        except Exception as parse_e:
            print(f"Error during parsing with {parser_model} parser: {parse_e}")
            try:
                fallback_parser = PDEQuestionBaiduParser()
                parsed = fallback_parser.parse(question)
                if isinstance(parsed, dict):
                    parsed["parser_mode"] = "rule_based_fallback"
                    parsed["parser_error"] = str(parse_e)
                    parsed = _repair_fallback_parsed_problem(question, parsed)
            except Exception:
                return _err(f"解析失败: {parse_e}", code="PARSE_ERROR")
        parsed = _repair_fallback_parsed_problem(question, parsed)
        validation_error = _validate_parsed_problem(question, parsed)
        if validation_error:
            return _err(
                validation_error,
                code="UNSUPPORTED_QUESTION",
                details={"parsed": parsed},
            )

        physics_params = parsed.get("physics_params", {}) if isinstance(parsed.get("physics_params"), dict) else {}
        domain_demand = parsed.get("domain_demand", {}) if isinstance(parsed.get("domain_demand"), dict) else {}

        # 2) Convert domain demand numeric -> feature pipeline inputs
        acc_level = _score_to_level(float(domain_demand.get("accuracy", 0.9)))
        rt_level = _score_to_level(float(domain_demand.get("realtime", 0.8)))
        rb = _resource_to_budget(float(domain_demand.get("resource_budget", 0.7)))

        eq_type = str(physics_params.get("equation_type", "heat1d")).strip().lower()
        dim = int(physics_params.get("dimension", 1))
        linear = bool(physics_params.get("linear", True))
        stationary = bool(physics_params.get("stationary", True))
        if eq_type == "wave1d":
            stationary = False

        # 3) Feature extraction (reuse existing endpoint logic)
        feature_payload: Dict[str, Any] = {
            "equation_type": eq_type if eq_type in ("heat1d", "wave1d", "wave2d", "wave3d", "poisson1d", "poisson3d", "heat2d", "heat3d", "poisson2d_nonlinear") else "heat1d",
            "accuracy": acc_level,
            "realtime": rt_level,
            "resource_budget": rb,
            "boundary_condition": str(physics_params.get("boundary_condition", "dirichlet")),
        }
        if feature_payload["equation_type"] in ("heat1d", "wave1d", "poisson1d"):
            feature_payload["nx"] = int(physics_params.get("problem_size", 101))
        elif feature_payload["equation_type"] in ("poisson3d", "heat3d", "wave3d"):
            n = round(int(physics_params.get("problem_size", 21 * 21 * 21)) ** (1.0 / 3.0))
            feature_payload["nx"] = max(5, n)
            feature_payload["ny"] = max(5, n)
            feature_payload["nz"] = max(5, n)
        elif feature_payload["equation_type"] in ("heat2d", "wave2d"):
            n = int(math.sqrt(int(physics_params.get("problem_size", 41 * 41))))
            feature_payload["nx"] = max(5, n)
            feature_payload["ny"] = max(5, n)
        else:
            # For 2D demo we assume square grid
            n = int(math.sqrt(int(physics_params.get("problem_size", 41 * 41))))
            feature_payload["nx"] = max(5, n)
            feature_payload["ny"] = max(5, n)

        # Call internal logic directly (same as /extract_feature)
        # DEBUG_BREAKPOINT_AUTO_SOLVE_FEATURE: set breakpoint here.
        # physics
        if feature_payload["equation_type"] in ("heat1d", "wave1d", "poisson1d"):
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 1,
                    "linearity": 0,
                    "stationarity": 1 if not stationary else 0,  # extractor uses 0=steady,1=unsteady
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]),
                }
            )
        elif feature_payload["equation_type"] == "heat2d":
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]) * int(feature_payload["ny"]),
                }
            )
        elif feature_payload["equation_type"] == "wave2d":
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 0,
                    "stationarity": 1,
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]) * int(feature_payload["ny"]),
                }
            )
        elif feature_payload["equation_type"] in ("poisson3d", "heat3d", "wave3d"):
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 3,
                    "linearity": 0,
                    "stationarity": 0 if feature_payload["equation_type"] == "poisson3d" else 1,
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]) * int(feature_payload["ny"]) * int(feature_payload["nz"]),
                }
            )
        else:
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 1 if not linear else 0,
                    "stationarity": 0,
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]) * int(feature_payload["ny"]),
                }
            )
        physics_vec = PhysicsFeatureExtractor.normalize(physics_out["vector"])

        hw_raw = HardwareFeatureExtractor.extract()
        hw_vec = HardwareFeatureExtractor.normalize(hw_raw["vector"])

        domain_out = DomainFeatureExtractor.extract_from_params(
            {"accuracy": acc_level, "realtime": rt_level, "resource_budget": rb}
        )
        domain_vec = DomainFeatureExtractor.normalize(domain_out["vector"])

        x13 = concat_features(physics_vec, hw_vec, domain_vec)

        extracted = {
            "equation_type": feature_payload["equation_type"],
            "physics": physics_vec.tolist(),
            "hardware": hw_vec.tolist(),
            "domain": domain_vec.tolist(),
            "x13": x13.tolist(),
            "hardware_extra": {"gpu_name": hw_raw.get("gpu_name")},
        }

        # 4) Algorithm selection
        strategy = "dynamic_rl" if (feature_payload["equation_type"] not in ("heat1d", "wave1d", "heat2d") or not stationary) else "static_rf"
        if feature_payload["equation_type"] in ("heat1d", "poisson1d"):
            strategy = "static_rf"
        elif feature_payload["equation_type"] in ("heat2d", "wave2d", "wave3d"):
            strategy = "gnn_selector"
        elif feature_payload["equation_type"] == "wave1d":
            strategy = "mlp_nn"

        # DEBUG_BREAKPOINT_AUTO_SOLVE_SELECT: set breakpoint here.
        if strategy in ("static_rf", "static_xgb", "mlp_nn", "gnn_selector"):
            selector._load_or_train_static(strategy)  # type: ignore[attr-defined]
        else:
            if selector.rl_agent is None:
                selector.train_dynamic(episodes=120)
                selector.save_dynamic()

        selection = selector.select(physics=physics_vec, hardware=hw_vec, domain=domain_vec, strategy=strategy)  # type: ignore[arg-type]
        if False:
            original_key = selection["algorithm_key"]
            original_name = selection.get("algorithm_name", original_key)
            selection["algorithm_key"] = "spectral"
            selection["algorithm_name"] = "有限差分法 (FDM)"
            selection["selected_algorithm"] = "spectral"
            selection["reason"] = (
                f"{selection['reason']} 当前 wave1d 数值求解器仅实现 FDM，"
                f"因此将推荐结果从 {original_name}({original_key}) 回退到 fdm 执行。"
            )
            selection["rationale"] = selection["reason"]

        if False:
            boundary_name = str(physics_params.get("bc_type", physics_params.get("boundary_condition", "dirichlet"))).strip().lower()
            if boundary_name != "dirichlet" and selection["algorithm_key"] in ("fem", "spectral"):
                original_key = selection["algorithm_key"]
                selection["algorithm_key"] = "spectral"
                selection["algorithm_name"] = "有限差分法 (FDM)"
                selection["selected_algorithm"] = "spectral"
                selection["reason"] = (
                    f"{selection['reason']} 当前 wave1d 的 {original_key} 实现仅支持 Dirichlet 边界，"
                    "因此自动回退到 fdm 执行。"
                )
                selection["rationale"] = selection["reason"]

        if eq_type == "wave1d":
            boundary_name = str(physics_params.get("bc_type", physics_params.get("boundary_condition", "dirichlet"))).strip().lower()
            corrected_selection = selector.select(
                physics=physics_vec,
                hardware=hw_vec,
                domain=domain_vec,
                strategy=strategy,
            )  # type: ignore[arg-type]
            if boundary_name != "dirichlet" and corrected_selection["algorithm_key"] == "spectral":
                corrected_selection["algorithm_key"] = "fdm"
                corrected_selection["algorithm_name"] = "有限差分法 (FDM)"
                corrected_selection["selected_algorithm"] = "fdm"
                corrected_selection["reason"] = (
                    f"{corrected_selection['reason']} 当前 wave1d 的 spectral 实现仅支持 Dirichlet 边界，"
                    "因此自动回退到 fdm 执行。"
                )
                corrected_selection["rationale"] = corrected_selection["reason"]
            selection = corrected_selection
        elif eq_type == "wave2d" and selection["algorithm_key"] not in ("fdm", "fem", "spectral"):
            original_key = selection["algorithm_key"]
            selection["algorithm_key"] = "fdm"
            selection["algorithm_name"] = "有限差分法 (FDM)"
            selection["selected_algorithm"] = "fdm"
            selection["reason"] = (
                f"{selection['reason']} 当前 {eq_type} 只实现了 FDM，"
                f"因此将推荐结果从 {original_key} 回退到 fdm 执行。"
            )
            selection["rationale"] = selection["reason"]
        elif eq_type == "wave3d" and selection["algorithm_key"] not in ("fdm", "fem", "spectral"):
            original_key = selection["algorithm_key"]
            selection["algorithm_key"] = "spectral"
            selection["algorithm_name"] = "Spectral Method"
            selection["selected_algorithm"] = "spectral"
            selection["reason"] = (
                f"{selection['reason']} ?? wave3d ??? FDM/FEM/spectral?"
                f"???????? {original_key} ??? spectral ???"
            )
            selection["rationale"] = selection["reason"]
        elif eq_type == "heat3d" and selection["algorithm_key"] not in ("fdm", "fvm", "fem"):
            original_key = selection["algorithm_key"]
            selection["algorithm_key"] = "fdm"
            selection["algorithm_name"] = "有限差分法(FDM)"
            selection["selected_algorithm"] = "fdm"
            selection["reason"] = (
                f"{selection['reason']} 当前 heat3d 已实现 fdm/fvm/fem，"
                f"但自动选择器返回的 {original_key} 尚未接入该方程，因此回退到 fdm 执行。"
            )
            selection["rationale"] = selection["reason"]
        elif eq_type == "poisson3d" and selection["algorithm_key"] not in ("fdm", "fem", "bem"):
            original_key = selection["algorithm_key"]
            selection["algorithm_key"] = "fdm"
            selection["algorithm_name"] = "鏈夐檺宸垎娉?(FDM)"
            selection["selected_algorithm"] = "fdm"
            selection["reason"] = (
                f"{selection['reason']} 当前 poisson3d 仅实现了 FDM，"
                f"因此将推荐结果从 {original_key} 回退到 fdm 执行。"
            )
            selection["rationale"] = selection["reason"]

        # 5) Solve equation
        # DEBUG_BREAKPOINT_AUTO_SOLVE_SOLVE: set breakpoint here.
        if extracted["equation_type"] == "poisson3d":
            nx = int(feature_payload.get("nx", 21))
            ny = int(feature_payload.get("ny", 21))
            nz = int(feature_payload.get("nz", 21))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            bc_error = _validate_zero_dirichlet_3d(eq_type=extracted["equation_type"], bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            solved = _solve_poisson3d_case(
                algorithm_key=selection["algorithm_key"],
                nx=nx,
                ny=ny,
                nz=nz,
                Lx=Lx,
                Ly=Ly,
                Lz=Lz,
                return_full=True,
            )
            sol_list = solved.get("solution", [])
            if not return_full:
                solved.pop("solution", None)
        elif extracted["equation_type"] == "heat3d":
            nx = int(feature_payload.get("nx", 11))
            ny = int(feature_payload.get("ny", 11))
            nz = int(feature_payload.get("nz", 11))
            k = float(physics_params.get("k", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            bc_error = _validate_zero_dirichlet_3d(eq_type=extracted["equation_type"], bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            t_span = (0.0, 0.0) if stationary else (0.0, 0.02)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                dz = Lz / max(nz - 1, 1)
                stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))
            solved = _solve_heat3d_case(
                algorithm_key=selection["algorithm_key"],
                nx=nx,
                ny=ny,
                nz=nz,
                Lx=Lx,
                Ly=Ly,
                Lz=Lz,
                k=k,
                t_span=t_span,
                nt=nt,
                return_full=True,
            )
            sol_list = solved.get("solution", [])
            if not return_full:
                solved.pop("solution", None)
        elif extracted["equation_type"] == "wave3d":
            nx = int(feature_payload.get("nx", 15))
            ny = int(feature_payload.get("ny", 15))
            nz = int(feature_payload.get("nz", 15))
            c = float(physics_params.get("c", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            bc_error = _validate_zero_dirichlet_3d(eq_type=extracted["equation_type"], bc_type=bc_type, left_bc=left_bc, right_bc=right_bc)
            if bc_error is not None:
                return bc_error
            t_span = (0.0, 0.0) if stationary else (0.0, 0.15)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                dz = Lz / max(nz - 1, 1)
                stability_limit = 1.0 / (c * math.sqrt((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))
            solved = _solve_wave3d_case(
                algorithm_key=selection["algorithm_key"],
                nx=nx,
                ny=ny,
                nz=nz,
                Lx=Lx,
                Ly=Ly,
                Lz=Lz,
                c=c,
                t_span=t_span,
                nt=nt,
                return_full=True,
            )
            sol_list = solved.get("solution", [])
            if not return_full:
                solved.pop("solution", None)
        elif extracted["equation_type"] == "poisson1d":
            nx = int(feature_payload.get("nx", 101))
            L = float(physics_params.get("L", 1.0))
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("poisson1d 当前仅支持 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            params = Heat1DParams(k=1.0, L=L, nx=nx, t_span=(0.0, 0.0), enforce_nonnegativity=False)
            bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)

            def initial_poisson(x: np.ndarray) -> np.ndarray:
                return np.zeros_like(x, dtype=float)

            def poisson_source(x: np.ndarray, t: float) -> np.ndarray:
                return (math.pi ** 2) * np.sin(math.pi * x / float(L))

            solver = get_solver(selection["algorithm_key"])
            sol, info, validation = solver.solve(params=params, bc=bc, initial=initial_poisson, source=poisson_source)
            sol_list = sol.tolist()
            solved = {
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "poisson3d":
            nx = int(feature_payload.get("nx", 21))
            ny = int(feature_payload.get("ny", 21))
            nz = int(feature_payload.get("nz", 21))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("poisson3d 当前仅支持 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("poisson3d 当前要求零 Dirichlet 边界。", code="INVALID_BOUNDARY_VALUE")

            if selection["algorithm_key"] == "fem":
                sol3d, info = solve_poisson3d_fem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            elif selection["algorithm_key"] == "bem":
                sol3d, info = solve_poisson3d_bem(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            else:
                sol3d, info = solve_poisson3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            sol_list = sol3d.reshape(-1).tolist()
            solved = {
                "shape": [nz, ny, nx],
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info.get("algorithm", selection["algorithm_key"]),
                "solve_info": info,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "heat1d":
            nx = int(feature_payload.get("nx", 101))
            k = float(physics_params.get("k", 1.0))
            L = float(physics_params.get("L", 1.0))
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            params = Heat1DParams(
                k=k,
                L=L,
                nx=nx,
                t_span=(0.0, 0.0) if stationary else (0.0, 0.05),
                enforce_nonnegativity=True,
            )
            if bc_type == BoundaryCondition.DIRICHLET:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            elif bc_type == BoundaryCondition.NEUMANN:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            else:
                bc = BoundarySpec(
                    bc_type=bc_type,
                    left_mixed=(1.0, 1.0, lambda t: left_bc),
                    right_mixed=(1.0, 1.0, lambda t: right_bc),
                )

            def initial_fn(x: np.ndarray) -> np.ndarray:
                return np.maximum(0.0, np.sin(np.pi * x / float(L)))

            solver = get_solver(selection["algorithm_key"])
            sol, info, validation = solver.solve(params=params, bc=bc, initial=initial_fn)
            sol_list = sol.tolist()
            solved = {
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "heat3d":
            nx = int(feature_payload.get("nx", 11))
            ny = int(feature_payload.get("ny", 11))
            nz = int(feature_payload.get("nz", 11))
            k = float(physics_params.get("k", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("heat3d currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("heat3d currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")
            t_span = (0.0, 0.0) if stationary else (0.0, 0.02)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                dz = Lz / max(nz - 1, 1)
                stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))

            if selection["algorithm_key"] == "fvm":
                sol3d, info_pack = solve_heat3d_fvm(
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            elif selection["algorithm_key"] == "fem":
                sol3d, info_pack = solve_heat3d_fem(
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            else:
                sol3d, info_pack = solve_heat3d_fdm(
                    nx=nx,
                    ny=ny,
                    nz=nz,
                    Lx=Lx,
                    Ly=Ly,
                    Lz=Lz,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            sol_list = sol3d.reshape(-1).tolist()
            solved = {
                "shape": [nz, ny, nx],
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "wave3d":
            nx = int(feature_payload.get("nx", 15))
            ny = int(feature_payload.get("ny", 15))
            nz = int(feature_payload.get("nz", 15))
            c = float(physics_params.get("c", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            Lz = float(physics_params.get("Lz", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("wave3d currently only supports zero Dirichlet boundaries.", code="INVALID_BOUNDARY_TYPE")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("wave3d currently requires zero Dirichlet boundaries.", code="INVALID_BOUNDARY_VALUE")
            t_span = (0.0, 0.0) if stationary else (0.0, 0.15)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                dz = Lz / max(nz - 1, 1)
                stability_limit = 1.0 / (c * math.sqrt((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))
            solved = _solve_wave3d_case(
                algorithm_key=selection["algorithm_key"],
                nx=nx,
                ny=ny,
                nz=nz,
                Lx=Lx,
                Ly=Ly,
                Lz=Lz,
                c=c,
                t_span=t_span,
                nt=nt,
                return_full=return_full,
            )
        elif extracted["equation_type"] == "heat2d":
            nx = int(feature_payload.get("nx", 41))
            ny = int(feature_payload.get("ny", 41))
            k = float(physics_params.get("k", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("heat2d 当前仅支持零 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("heat2d 当前要求零 Dirichlet 边界。", code="INVALID_BOUNDARY_VALUE")
            t_span = (0.0, 0.0) if stationary else (0.0, 0.05)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))

            if selection["algorithm_key"] == "fvm":
                sol2d, info_pack = solve_heat2d_fvm(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            elif selection["algorithm_key"] == "fem":
                sol2d, info_pack = solve_heat2d_fem(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            else:
                sol2d, info_pack = solve_heat2d_fdm(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    k=k,
                    t_span=t_span,
                    nt=nt,
                )
            sol_list = sol2d.reshape(-1).tolist()
            solved = {
                "shape": [ny, nx],
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "wave2d":
            nx = int(feature_payload.get("nx", 41))
            ny = int(feature_payload.get("ny", 41))
            c = float(physics_params.get("c", 1.0))
            Lx = float(physics_params.get("Lx", physics_params.get("L", 1.0)))
            Ly = float(physics_params.get("Ly", physics_params.get("L", 1.0)))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                return _err("wave2d 当前仅支持零 Dirichlet 边界。", code="INVALID_BOUNDARY_TYPE")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                return _err("wave2d 当前要求零 Dirichlet 边界。", code="INVALID_BOUNDARY_VALUE")

            t_span = (0.0, 0.0) if stationary else (0.0, 0.2)
            t0_val, t1_val = t_span
            if t1_val > t0_val:
                dx = Lx / max(nx - 1, 1)
                dy = Ly / max(ny - 1, 1)
                stability_limit = 1.0 / (c * math.sqrt((1.0 / dx**2) + (1.0 / dy**2)))
                nt = max(nt, int(math.ceil((t1_val - t0_val) / stability_limit)))

            if selection["algorithm_key"] == "fem":
                sol2d, info_pack = solve_wave2d_fem(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    c=c,
                    t_span=t_span,
                    nt=nt,
                )
            elif selection["algorithm_key"] == "spectral":
                sol2d, info_pack = solve_wave2d_spectral(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    c=c,
                    t_span=t_span,
                )
            else:
                sol2d, info_pack = solve_wave2d_fdm(
                    nx=nx,
                    ny=ny,
                    Lx=Lx,
                    Ly=Ly,
                    c=c,
                    t_span=t_span,
                    nt=nt,
                )
            sol_list = sol2d.reshape(-1).tolist()
            solved = {
                "shape": [ny, nx],
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        elif extracted["equation_type"] == "wave1d":
            nx = int(feature_payload.get("nx", 101))
            c = float(physics_params.get("c", 1.0))
            L = float(physics_params.get("L", 1.0))
            left_bc = float(physics_params.get("left_bc", 0.0))
            right_bc = float(physics_params.get("right_bc", 0.0))
            nt = int(physics_params.get("nt", 200))
            bc_type = BoundaryCondition(str(physics_params.get("bc_type", "dirichlet")).strip().lower())
            if bc_type == BoundaryCondition.MIXED:
                return _err("wave1d 当前仅支持 Dirichlet 或 Neumann 边界。", code="INVALID_BOUNDARY_TYPE")

            wave_params = Wave1DParams(
                c=c,
                L=L,
                nx=nx,
                t_span=(0.0, 0.0) if stationary else (0.0, 0.5),
                nt=nt,
            )
            bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)

            def initial_wave(x: np.ndarray) -> np.ndarray:
                return np.sin(np.pi * x / float(L))

            def velocity_wave(x: np.ndarray) -> np.ndarray:
                return np.zeros_like(x, dtype=float)

            if selection["algorithm_key"] == "spectral":
                sol, info, validation = solve_wave1d_spectral_v2(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_wave,
                    initial_velocity=velocity_wave,
                )
            elif selection["algorithm_key"] == "fem":
                sol, info, validation = solve_wave1d_fem(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_wave,
                    initial_velocity=velocity_wave,
                )
            else:
                sol, info, validation = solve_wave1d(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_wave,
                    initial_velocity=velocity_wave,
                )
            sol_list = sol.tolist()
            solved = {
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list
        else:
            # Note: our current 2D solver is steady manufactured-solution demo.
            sol2d, info = solve_poisson2d_nonlinear(nx=int(feature_payload["nx"]), ny=int(feature_payload["ny"]))
            sol_list = sol2d.reshape(-1).tolist()
            solved = {
                "shape": [int(feature_payload["ny"]), int(feature_payload["nx"])],
                "equation_type": extracted["equation_type"],
                "recommended_algorithm": selection["algorithm_key"],
                "executed_algorithm": info.get("algorithm", selection["algorithm_key"]) if isinstance(info, dict) else selection["algorithm_key"],
                "solve_info": info,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                solved["solution"] = sol_list

        # 6) Evaluate + optimize
        # DEBUG_BREAKPOINT_AUTO_SOLVE_EVAL: set breakpoint here.
        # Evaluate uses full solution; if we didn't include it in response, compute from preview source.
        solution_for_eval = np.array(
            (sol_list if "sol_list" in locals() else solved.get("solution", [])), dtype=float
        ).reshape(-1)
        report = evaluator.evaluate(
            solution=solution_for_eval,
            solve_info=solved["solve_info"],
            domain_requirements={"accuracy": _parse_requirement_level(acc_level, "accuracy"), "realtime": _parse_requirement_level(rt_level, "realtime"), "resource_budget": rb},
            validation=solved.get("validation") if isinstance(solved.get("validation"), dict) else None,
        )
        report_path = evaluator.save_report(report, result_dir="result")

        opt_status: Dict[str, Any] = {"skipped": False}
        try:
            sample_path = optimizer.append_training_sample(x13=np.array(x13, dtype=float), algorithm_key=selection["algorithm_key"])
            train_info = optimizer.retrain_static_with_feedback(strategy="static_rf")
            opt_status.update({"feedback_saved_to": sample_path, "retrained": train_info})
        except Exception as e:  # noqa: BLE001
            opt_status.update({"skipped": True, "reason": str(e)})

        msg = (
            "当前使用大模型智能解析。"
            if parsed.get("parser_mode") not in (None, "rule_based")
            else "当前使用规则解析（未配置 Key 或大模型解析失败后自动降级）。"
        )
        return _ok(
            {
                "message": msg,
                "parsed": parsed,
                "extracted": extracted,
                "selected": selection,
                "solved": solved,
                "evaluated": {"report": report, "saved_to": report_path, "optimizer": opt_status},
                "notes": [
                    "若未配置百度 Key，系统会自动降级为规则解析，不会崩溃。",
                    "2D 非定常泊松在当前示例中会使用稳态制造解求解器做演示闭环（可后续扩展非定常求解）。"
                    if extracted["equation_type"] not in ("heat1d", "wave1d")
                    else "",
                ],
            }
        )
    except Exception as e:  # noqa: BLE001
        return _err(f"auto_solve 失败：{e}", code="AUTO_SOLVE_ERROR")


@router.api_route("/api/baidu/config", methods=["GET", "POST"])
async def baidu_config(request: Request) -> Any:
    """Simple configuration page for Baidu API keys (thread-safe, in-memory).

    Notes:
    - This does NOT write secrets to disk.
    - Env vars still take precedence if set.
    """
    if request.method.upper() == "GET":
        # Minimal responsive HTML (PC/mobile)
        configured = GLOBAL_BAIDU_KEY_STORE.is_configured()
        html = f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>百度千帆 Key 配置</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, "PingFang SC", "Microsoft YaHei", sans-serif; margin: 0; background: #f6f7fb; }}
    .wrap {{ max-width: 720px; margin: 24px auto; padding: 16px; }}
    .card {{ background: #fff; border-radius: 12px; padding: 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.06); }}
    h1 {{ font-size: 18px; margin: 0 0 8px; }}
    .hint {{ color:#666; font-size: 13px; line-height: 1.6; }}
    label {{ display:block; margin-top: 12px; font-size: 13px; color:#333; }}
    input {{ width:100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 14px; }}
    button {{ margin-top: 14px; width:100%; padding: 10px 12px; border: 0; border-radius: 10px; background:#2563eb; color:#fff; font-size: 14px; }}
    .ok {{ margin-top: 10px; padding: 10px 12px; border-radius: 10px; background: {"#ecfdf5" if configured else "#fff7ed"}; color: {"#065f46" if configured else "#9a3412"}; font-size: 13px; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>百度千帆（ERNIE-Speed-8K）Key 配置</h1>
      <div class="hint">
        本页用于小白快速配置 Key（仅内存保存，进程重启会失效）。更推荐使用环境变量：<br/>
        <code>BAIDU_QIANFAN_API_KEY</code> / <code>BAIDU_QIANFAN_SECRET_KEY</code>
      </div>
      <div class="ok">当前状态：{"已配置（可使用大模型解析）" if configured else "未配置（将自动降级为规则解析）"}</div>
      <form method="post">
        <label>API Key</label>
        <input name="api_key" placeholder="输入 API Key" />
        <label>Secret Key</label>
        <input name="secret_key" placeholder="输入 Secret Key" />
        <button type="submit">保存到当前服务（内存）</button>
      </form>
      <div class="hint" style="margin-top:12px;">
        配置后可在 Swagger 调试：<code>/api/parse_question</code> 与 <code>/api/auto_solve</code>（见 <code>/docs</code>）。
      </div>
    </div>
  </div>
</body>
</html>
"""
        return html

    payload = await _read_payload(request)
    api_key = str(payload.get("api_key", "")).strip()
    secret_key = str(payload.get("secret_key", "")).strip()
    if not api_key or not secret_key:
        return _err("api_key/secret_key 不能为空。", code="INVALID_PARAM")
    GLOBAL_BAIDU_KEY_STORE.set(api_key, secret_key)
    return _ok({"message": "已保存到当前服务内存（重启后失效）。建议仍使用环境变量方式配置。"})
