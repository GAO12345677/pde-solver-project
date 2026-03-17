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

import time
from typing import Any, Dict, Optional

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
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    SolverError,
    get_solver,
    solve_poisson2d_nonlinear,
)


router = APIRouter()

# Singletons for the service process.
selector = AlgorithmSelector(model_dir="model")
evaluator = ResultEvaluator()
optimizer = ModelOptimizer(model_dir="model", feedback_dir="result")


def _ok(data: Any) -> Dict[str, Any]:
    return {"status": "ok", "success": True, "error": None, "data": data}


def _err(message: str, *, code: str = "BAD_REQUEST", details: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "data": None,
    }


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
      - equation_type: "heat1d" or "poisson2d_nonlinear"
      - (for heat1d) dimension/linearity/stationarity/boundary_condition/problem_size or inferable keys
    - domain: accuracy/realtime/resource_budget
    Output:
    - normalized physics/hardware/domain vectors
    - concatenated 13-dim vector (x13)
    """
    payload = await _read_payload(request)
    try:
        eq_type = str(payload.get("equation_type", "heat1d")).strip().lower()

        # Physics features (normalized)
        if eq_type == "heat1d":
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
        else:
            return _err("equation_type 必须是 heat1d 或 poisson2d_nonlinear。", code="INVALID_EQUATION_TYPE")

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
        if strategy not in ("static_rf", "static_xgb", "dynamic_rl"):
            return _err("strategy 必须是 static_rf/static_xgb/dynamic_rl。", code="INVALID_STRATEGY")

        physics = np.array(payload.get("physics", []), dtype=float)
        hardware = np.array(payload.get("hardware", []), dtype=float)
        domain = np.array(payload.get("domain", []), dtype=float)

        # Auto-load/train to keep the service "no extra config" runnable.
        if strategy in ("static_rf", "static_xgb"):
            if selector.static_model is None:
                selector.train_static(strategy=strategy)  # train typical-case proxy dataset
                selector.save_static()
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
        if algorithm_key not in ("fdm", "fem", "spectral"):
            return _err("algorithm_key 必须是 fdm/fem/spectral。", code="INVALID_ALGORITHM_KEY")

        # DEBUG_BREAKPOINT_API_SOLVE: set breakpoint here.
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
            return _ok({"solution": sol.tolist(), "solve_info": info.__dict__, "validation": validation})

        if eq_type == "poisson2d_nonlinear":
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            Lx = _to_float(payload.get("Lx", 1.0), "Lx")
            Ly = _to_float(payload.get("Ly", 1.0), "Ly")
            tol = _to_float(payload.get("tol", 1e-6), "tol")
            max_iter = _to_int(payload.get("max_iter", 200), "max_iter")
            sol2d, info = solve_poisson2d_nonlinear(nx=nx, ny=ny, Lx=Lx, Ly=Ly, tol=tol, max_iter=max_iter)
            return _ok({"solution": sol2d.reshape(-1).tolist(), "shape": [ny, nx], "solve_info": info})

        return _err("equation_type 必须是 heat1d 或 poisson2d_nonlinear。", code="INVALID_EQUATION_TYPE")
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

