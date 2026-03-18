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

import numpy as np
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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
from nlp.baidu_parser import GLOBAL_BAIDU_KEY_STORE, PDEQuestionBaiduParser
from api.llm.llm_routes import router as llm_router



router = APIRouter()

router.include_router(llm_router, prefix="/llm")

# Singletons for the service process.
selector = AlgorithmSelector(model_dir="model")
evaluator = ResultEvaluator()
optimizer = ModelOptimizer(model_dir="model", feedback_dir="result")


class ParseQuestionIn(BaseModel):
    question: str = Field(..., description="自然语言题目")


class AutoSolveIn(BaseModel):
    question: str = Field(..., description="自然语言题目")
    return_full_solution: bool = Field(False, description="是否返回完整解数组（可能导致 Swagger 卡顿）")


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

        # Default: do NOT return huge solution arrays in Swagger.
        return_full = str(payload.get("return_full_solution", "false")).strip().lower() in ("1", "true", "yes")

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
            sol_list = sol.tolist()
            data = {
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return _ok(data)

        if eq_type == "poisson2d_nonlinear":
            nx = _to_int(payload.get("nx", 41), "nx")
            ny = _to_int(payload.get("ny", 41), "ny")
            Lx = _to_float(payload.get("Lx", 1.0), "Lx")
            Ly = _to_float(payload.get("Ly", 1.0), "Ly")
            tol = _to_float(payload.get("tol", 1e-6), "tol")
            max_iter = _to_int(payload.get("max_iter", 200), "max_iter")
            sol2d, info = solve_poisson2d_nonlinear(nx=nx, ny=ny, Lx=Lx, Ly=Ly, tol=tol, max_iter=max_iter)
            sol_list = sol2d.reshape(-1).tolist()
            data = {"shape": [ny, nx], "solve_info": info, "solution_preview": _preview_list(sol_list)}
            if return_full:
                data["solution"] = sol_list
            return _ok(data)

        return _err("equation_type 必须是 heat1d 或 poisson2d_nonlinear。", code="INVALID_EQUATION_TYPE")
    except (SolverError, ValueError) as e:
        return _err(str(e), code="SOLVER_ERROR")
    except Exception as e:  # noqa: BLE001
        return _err(f"求解失败: {e}", code="INTERNAL_ERROR")


async def _evaluate_result_impl(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Shared implementation for GET/POST evaluate_result to avoid duplicated OpenAPI IDs."""
    try:
        solution = np.array(payload.get("solution", []), dtype=float).reshape(-1)
        solve_info = payload.get("solve_info", {})
        if not isinstance(solve_info, dict):
            return _err("solve_info 必须是对象(dict)。", code="INVALID_SOLVE_INFO")

        acc = _parse_requirement_level(payload.get("accuracy", "medium"), "accuracy")
        rt = _parse_requirement_level(payload.get("realtime", "medium"), "realtime")
        rb = payload.get("resource_budget", 0.75)
        validation = payload.get("validation", None)

        # DEBUG_BREAKPOINT_API_EVAL: set breakpoint here.
        report = evaluator.evaluate(
            solution=solution,
            solve_info=solve_info,
            domain_requirements={"accuracy": acc, "realtime": rt, "resource_budget": rb},
            validation=validation if isinstance(validation, dict) else None,
        )
        report_path = evaluator.save_report(report, result_dir="result")

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
    except (FeedbackError, AlgorithmSelectionError) as e:
        return _err(str(e), code="FEEDBACK_ERROR")
    except Exception as e:  # noqa: BLE001
        return _err(f"评估失败: {e}", code="INTERNAL_ERROR")


@router.get("/evaluate_result")
async def evaluate_result_get(request: Request) -> Dict[str, Any]:
    payload = await _read_payload(request)
    return await _evaluate_result_impl(payload)


@router.post("/evaluate_result")
async def evaluate_result_post(request: Request) -> Dict[str, Any]:
    payload = await _read_payload(request)
    return await _evaluate_result_impl(payload)


@router.get("/api/parse_question")
async def api_parse_question_get(question: str) -> Dict[str, Any]:
    """Parse question only (GET).

    This is convenient for quick browser tests:
      /api/parse_question?question=...
    """
    try:
        question = str(question).strip()
        if not question:
            return _err("question 不能为空。", code="INVALID_PARAM")
        pde_question_parser = PDEQuestionBaiduParser()
        parsed = pde_question_parser.parse(question)
        msg = (
            "当前使用大模型智能解析（全局配置Key）。"
            if parsed.get("parser_mode") == "baidu_llm"
            else "当前使用规则解析（未配置Key或解析失败自动降级）。"
        )
        return _ok({"message": msg, "parsed": parsed, "key_configured": GLOBAL_BAIDU_KEY_STORE.is_configured()})
    except Exception as e:  # noqa: BLE001
        return _err(str(e), code="PARSE_ERROR")


@router.post("/api/parse_question")
async def api_parse_question_post(payload: ParseQuestionIn) -> Dict[str, Any]:
    """Parse question only (POST JSON).

    Swagger will show an editable JSON body for this endpoint.
    """
    try:
        question = str(payload.question).strip()
        if not question:
            return _err("question 不能为空。", code="INVALID_PARAM")

        # DEBUG_BREAKPOINT_PARSE_QUESTION: set breakpoint here.
        pde_question_parser = PDEQuestionBaiduParser()
        parsed = pde_question_parser.parse(question)
        msg = (
            "当前使用大模型智能解析（全局配置Key）。"
            if parsed.get("parser_mode") == "baidu_llm"
            else "当前使用规则解析（未配置Key或解析失败自动降级）。"
        )
        return _ok({"message": msg, "parsed": parsed, "key_configured": GLOBAL_BAIDU_KEY_STORE.is_configured()})
    except Exception as e:  # noqa: BLE001
        return _err(str(e), code="PARSE_ERROR")


@router.post("/api/auto_solve")
async def api_auto_solve(payload: AutoSolveIn) -> Dict[str, Any]:
    """Full pipeline: natural language -> JSON -> features -> selection -> solve -> evaluate."""
    try:
        question = str(payload.question).strip()
        if not question:
            return _err("question 不能为空。", code="INVALID_PARAM")

        pde_question_parser = PDEQuestionBaiduParser()
        return_full = bool(payload.return_full_solution)

        # 1) Parse
        # DEBUG_BREAKPOINT_AUTO_SOLVE_PARSE: set breakpoint here.
        parsed = pde_question_parser.parse(question)
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

        # 3) Feature extraction (reuse existing endpoint logic)
        feature_payload: Dict[str, Any] = {
            "equation_type": "heat1d" if eq_type == "heat1d" else "poisson2d_nonlinear",
            "accuracy": acc_level,
            "realtime": rt_level,
            "resource_budget": rb,
            "boundary_condition": str(physics_params.get("boundary_condition", "dirichlet")),
        }
        if feature_payload["equation_type"] == "heat1d":
            feature_payload["nx"] = int(physics_params.get("problem_size", 101))
        else:
            # For 2D demo we assume square grid
            n = int(math.sqrt(int(physics_params.get("problem_size", 41 * 41))))
            feature_payload["nx"] = max(5, n)
            feature_payload["ny"] = max(5, n)

        # Call internal logic directly (same as /extract_feature)
        # DEBUG_BREAKPOINT_AUTO_SOLVE_FEATURE: set breakpoint here.
        # physics
        if feature_payload["equation_type"] == "heat1d":
            physics_out = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 1,
                    "linearity": 0,
                    "stationarity": 1 if not stationary else 0,  # extractor uses 0=steady,1=unsteady
                    "boundary_condition": feature_payload["boundary_condition"],
                    "problem_size": int(feature_payload["nx"]),
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
        strategy = "dynamic_rl" if (feature_payload["equation_type"] != "heat1d" or not stationary) else "static_rf"
        if feature_payload["equation_type"] == "heat1d":
            strategy = "static_rf"  # for the hydrology-like case

        # DEBUG_BREAKPOINT_AUTO_SOLVE_SELECT: set breakpoint here.
        if strategy in ("static_rf", "static_xgb"):
            if selector.static_model is None:
                selector.train_static(strategy=strategy)
                selector.save_static()
        else:
            if selector.rl_agent is None:
                selector.train_dynamic(episodes=120)
                selector.save_dynamic()

        selection = selector.select(physics=physics_vec, hardware=hw_vec, domain=domain_vec, strategy=strategy)  # type: ignore[arg-type]

        # 5) Solve equation
        # DEBUG_BREAKPOINT_AUTO_SOLVE_SOLVE: set breakpoint here.
        if extracted["equation_type"] == "heat1d":
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
            solved = {"solve_info": info.__dict__, "validation": validation, "solution_preview": _preview_list(sol_list)}
            if return_full:
                solved["solution"] = sol_list
        else:
            # Note: our current 2D solver is steady manufactured-solution demo.
            sol2d, info = solve_poisson2d_nonlinear(nx=int(feature_payload["nx"]), ny=int(feature_payload["ny"]))
            sol_list = sol2d.reshape(-1).tolist()
            solved = {
                "shape": [int(feature_payload["ny"]), int(feature_payload["nx"])],
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
            "当前使用大模型智能解析（全局配置Key）。"
            if parsed.get("parser_mode") == "baidu_llm"
            else "当前使用规则解析（未配置Key或解析失败自动降级）。"
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
                    if extracted["equation_type"] != "heat1d"
                    else "",
                ],
            }
        )
    except Exception as e:  # noqa: BLE001
        return _err(f"auto_solve 失败：{e}", code="AUTO_SOLVE_ERROR")


@router.get("/api/baidu/config", response_class=HTMLResponse)
async def baidu_config_get() -> HTMLResponse:
    """Simple configuration page for Baidu API keys (thread-safe, in-memory).

    Notes:
    - This does NOT write secrets to disk.
    - Env vars still take precedence if set.
    """
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
    return HTMLResponse(content=html)


@router.post("/api/baidu/config")
async def baidu_config_post(api_key: str = Form(...), secret_key: str = Form(...)) -> Dict[str, Any]:
    api_key = str(api_key).strip()
    secret_key = str(secret_key).strip()
    if not api_key or not secret_key:
        return _err("api_key/secret_key 不能为空。", code="INVALID_PARAM")
    GLOBAL_BAIDU_KEY_STORE.set(api_key, secret_key)
    return _ok({"message": "已保存到当前服务内存（重启后失效）。建议仍使用环境变量方式配置。"})

