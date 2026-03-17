"""End-to-end framework tests (paper typical cases).

Runs two test cases:
1) 1D linear heat conduction (hydrological runoff proxy) -> validate static selection
2) 2D nonlinear Poisson-like equation (geological prospecting proxy) -> validate dynamic adjustment

Each case performs:
  Feature extraction -> Algorithm selection -> Equation solving -> Result evaluation

Outputs:
- prints step-by-step results
- generates a JSON test report under `result/`

Run:
  python -m test_case.test_framework
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi.testclient import TestClient

import main


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@dataclass
class StepTiming:
    extract_s: float
    select_s: float
    solve_s: float
    eval_s: float


def _call(client: TestClient, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if method.upper() == "GET":
        r = client.get(path, params=payload)
    else:
        r = client.post(path, json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"{path} failed: {r.status_code} {r.text}")
    out = r.json()
    if not out.get("success", False):
        raise RuntimeError(f"{path} returned error: {out}")
    return out["data"]


def test_case_1_heat1d_static(client: TestClient) -> Dict[str, Any]:
    """Case 1: 1D linear heat conduction (hydrological runoff proxy).

    Expected:
    - static strategy should typically recommend FDM for realtime pressure.
    """
    t0 = time.perf_counter()
    feat = _call(
        client,
        "POST",
        "/extract_feature",
        {
            "equation_type": "heat1d",
            "nx": 101,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "high",
            "resource_budget": 0.5,
        },
    )
    t1 = time.perf_counter()

    sel = _call(
        client,
        "POST",
        "/select_algorithm",
        {
            "strategy": "static_rf",
            "physics": feat["physics"],
            "hardware": feat["hardware"],
            "domain": feat["domain"],
        },
    )
    t2 = time.perf_counter()

    # Solve using selected algorithm
    alg_key = sel["algorithm_key"]
    sol = _call(
        client,
        "POST",
        "/solve_equation",
        {
            "equation_type": "heat1d",
            "algorithm_key": alg_key,
            "k": 1.0,
            "L": 1.0,
            "nx": 101,
            "t0": 0.0,
            "t1": 0.05,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
            "initial": "sine_nonnegative",
            "enforce_nonnegativity": True,
        },
    )
    t3 = time.perf_counter()

    evalr = _call(
        client,
        "POST",
        "/evaluate_result",
        {
            "solution": sol["solution"],
            "solve_info": sol["solve_info"],
            "validation": sol.get("validation"),
            "accuracy": "medium",
            "realtime": "high",
            "resource_budget": 0.5,
            "x13": feat["x13"],
            "selected_algorithm": alg_key,
            "retrain_strategy": "static_rf",
        },
    )
    t4 = time.perf_counter()

    # Accuracy proxy for this test: physical constraints and boundary satisfaction.
    validation = sol.get("validation", {})
    stable_ok = bool(validation.get("finite", True)) and bool(validation.get("bc_satisfied", True))
    nonneg_ok = bool(validation.get("nonnegative", True))
    match_expected = alg_key == "fdm"  # typical hydrology/realtime -> FDM

    timings = StepTiming(extract_s=t1 - t0, select_s=t2 - t1, solve_s=t3 - t2, eval_s=t4 - t3)
    return {
        "name": "case1_heat1d_hydrology_static",
        "selected_algorithm": alg_key,
        "match_expected": match_expected,
        "constraints_ok": {"stable_ok": stable_ok, "nonneg_ok": nonneg_ok},
        "total_score": evalr["report"]["metrics"]["total"],
        "timing": timings.__dict__,
    }


def test_case_2_poisson2d_dynamic(client: TestClient) -> Dict[str, Any]:
    """Case 2: 2D nonlinear Poisson (geological prospecting proxy).

    Expected:
    - dynamic strategy often prefers FEM for high complexity, but our dynamic agent
      is heuristic; we validate the **dynamic policy path** and solver error.
    """
    t0 = time.perf_counter()
    feat = _call(
        client,
        "POST",
        "/extract_feature",
        {
            "equation_type": "poisson2d_nonlinear",
            "nx": 41,
            "ny": 41,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
        },
    )
    t1 = time.perf_counter()

    sel = _call(
        client,
        "POST",
        "/select_algorithm",
        {
            "strategy": "dynamic_rl",
            "physics": feat["physics"],
            "hardware": feat["hardware"],
            "domain": feat["domain"],
        },
    )
    t2 = time.perf_counter()

    alg_key = sel["algorithm_key"]
    sol = _call(
        client,
        "POST",
        "/solve_equation",
        {
            "equation_type": "poisson2d_nonlinear",
            "algorithm_key": alg_key,
            "nx": 41,
            "ny": 41,
            "Lx": 1.0,
            "Ly": 1.0,
            "tol": 1e-6,
            "max_iter": 200,
        },
    )
    t3 = time.perf_counter()

    # The 2D solver includes an estimated_error against manufactured solution.
    est_err = float(sol["solve_info"].get("estimated_error", 1.0))

    evalr = _call(
        client,
        "POST",
        "/evaluate_result",
        {
            "solution": sol["solution"],
            "solve_info": sol["solve_info"],
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
            "x13": feat["x13"],
            "selected_algorithm": alg_key,
            "retrain_strategy": "static_rf",
        },
    )
    t4 = time.perf_counter()

    timings = StepTiming(extract_s=t1 - t0, select_s=t2 - t1, solve_s=t3 - t2, eval_s=t4 - t3)
    return {
        "name": "case2_poisson2d_geology_dynamic",
        "selected_algorithm": alg_key,
        "estimated_l2_error": est_err,
        "solve_status": sol["solve_info"].get("status"),
        "total_score": evalr["report"]["metrics"]["total"],
        "timing": timings.__dict__,
    }


def run_all() -> Dict[str, Any]:
    client = TestClient(main.app)

    start = time.perf_counter()
    results: List[Dict[str, Any]] = []

    r1 = test_case_1_heat1d_static(client)
    print("\n[case1] result:", r1)
    results.append(r1)

    r2 = test_case_2_poisson2d_dynamic(client)
    print("\n[case2] result:", r2)
    results.append(r2)

    elapsed = time.perf_counter() - start

    accuracy = float(np.mean([1.0 if r.get("match_expected") else 0.0 for r in results if "match_expected" in r]))
    report = {
        "timestamp": time.time(),
        "elapsed_s": float(elapsed),
        "cases": results,
        "algorithm_match_accuracy": accuracy,
        "notes": [
            "case1 的 expected=fdm 为典型场景假设，用于验证静态策略路径是否正常。",
            "case2 使用制造解的 estimated_error 用于验证 2D 求解与动态策略路径可运行。",
        ],
    }

    _ensure_dir("result")
    path = os.path.join("result", f"test_report_{int(report['timestamp'])}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n[test] report saved to:", path)
    return report


if __name__ == "__main__":
    run_all()

