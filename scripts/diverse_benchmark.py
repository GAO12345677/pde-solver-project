"""Diverse benchmark with multiple test cases per equation type.

This script tests solvers on DIFFERENT problems (not just repeated runs of the same problem).

Usage:
  python scripts/diverse_benchmark.py run
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from config.constants import BoundaryCondition
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    Wave1DParams,
    get_solver,
    solve_wave1d,
    solve_wave1d_fem,
    solve_wave1d_spectral_v2,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "real_world_benchmark"


@dataclass
class TestCase:
    name: str
    equation_type: str
    params: Dict[str, Any]
    initial_condition: str
    boundary_condition: str
    exact_solution_type: str
    mode_number: int


HEAT1D_TEST_CASES: List[TestCase] = [
    TestCase(
        name="heat1d_mode1_k1.0",
        equation_type="heat1d",
        params={"k": 1.0, "L": 1.0, "nx": 101, "t_final": 0.05},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=1,
    ),
    TestCase(
        name="heat1d_mode1_k0.5",
        equation_type="heat1d",
        params={"k": 0.5, "L": 1.0, "nx": 101, "t_final": 0.1},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=1,
    ),
    TestCase(
        name="heat1d_mode1_k2.0",
        equation_type="heat1d",
        params={"k": 2.0, "L": 1.0, "nx": 101, "t_final": 0.025},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=1,
    ),
    TestCase(
        name="heat1d_mode2_k1.0",
        equation_type="heat1d",
        params={"k": 1.0, "L": 1.0, "nx": 101, "t_final": 0.02},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=2,
    ),
    TestCase(
        name="heat1d_mode3_k1.0",
        equation_type="heat1d",
        params={"k": 1.0, "L": 1.0, "nx": 101, "t_final": 0.01},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=3,
    ),
    TestCase(
        name="heat1d_mode5_k1.0",
        equation_type="heat1d",
        params={"k": 1.0, "L": 1.0, "nx": 201, "t_final": 0.005},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=5,
    ),
    TestCase(
        name="heat1d_mode1_L2.0",
        equation_type="heat1d",
        params={"k": 1.0, "L": 2.0, "nx": 201, "t_final": 0.2},
        initial_condition="sin(n*pi*x/L)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_decay",
        mode_number=1,
    ),
    TestCase(
        name="heat1d_mixed_mode",
        equation_type="heat1d",
        params={"k": 1.0, "L": 1.0, "nx": 101, "t_final": 0.02},
        initial_condition="sin(pi*x) + 0.5*sin(2*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="fourier_superposition",
        mode_number=0,
    ),
]


WAVE1D_TEST_CASES: List[TestCase] = [
    TestCase(
        name="wave1d_mode1_c1.0",
        equation_type="wave1d",
        params={"c": 1.0, "L": 1.0, "nx": 101, "t_final": 0.5},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=1,
    ),
    TestCase(
        name="wave1d_mode1_c0.5",
        equation_type="wave1d",
        params={"c": 0.5, "L": 1.0, "nx": 101, "t_final": 1.0},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=1,
    ),
    TestCase(
        name="wave1d_mode1_c2.0",
        equation_type="wave1d",
        params={"c": 2.0, "L": 1.0, "nx": 101, "t_final": 0.25},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=1,
    ),
    TestCase(
        name="wave1d_mode2_c1.0",
        equation_type="wave1d",
        params={"c": 1.0, "L": 1.0, "nx": 101, "t_final": 0.25},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=2,
    ),
    TestCase(
        name="wave1d_mode3_c1.0",
        equation_type="wave1d",
        params={"c": 1.0, "L": 1.0, "nx": 101, "t_final": 0.17},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=3,
    ),
    TestCase(
        name="wave1d_mode5_c1.0",
        equation_type="wave1d",
        params={"c": 1.0, "L": 1.0, "nx": 201, "t_final": 0.1},
        initial_condition="sin(n*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=5,
    ),
    TestCase(
        name="wave1d_mode1_L2.0",
        equation_type="wave1d",
        params={"c": 1.0, "L": 2.0, "nx": 201, "t_final": 1.0},
        initial_condition="sin(n*pi*x/L)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="standing_wave",
        mode_number=1,
    ),
    TestCase(
        name="wave1d_mixed_mode",
        equation_type="wave1d",
        params={"c": 1.0, "L": 1.0, "nx": 101, "t_final": 0.5},
        initial_condition="sin(pi*x) + 0.5*sin(2*pi*x)",
        boundary_condition="dirichlet_0_0",
        exact_solution_type="wave_superposition",
        mode_number=0,
    ),
]


def compute_exact_solution(case: TestCase, x: np.ndarray, t: float) -> np.ndarray:
    params = case.params
    k = params.get("k", 1.0)
    c = params.get("c", 1.0)
    L = params.get("L", 1.0)
    n = case.mode_number
    
    if case.equation_type == "heat1d":
        if case.exact_solution_type == "fourier_decay":
            return np.exp(-k * (n * np.pi / L) ** 2 * t) * np.sin(n * np.pi * x / L)
        elif case.exact_solution_type == "fourier_superposition":
            u1 = np.exp(-k * (np.pi / L) ** 2 * t) * np.sin(np.pi * x / L)
            u2 = 0.5 * np.exp(-k * (2 * np.pi / L) ** 2 * t) * np.sin(2 * np.pi * x / L)
            return u1 + u2
    
    elif case.equation_type == "wave1d":
        if case.exact_solution_type == "standing_wave":
            omega = c * n * np.pi / L
            return np.cos(omega * t) * np.sin(n * np.pi * x / L)
        elif case.exact_solution_type == "wave_superposition":
            omega1 = c * np.pi / L
            omega2 = c * 2 * np.pi / L
            u1 = np.cos(omega1 * t) * np.sin(np.pi * x / L)
            u2 = 0.5 * np.cos(omega2 * t) * np.sin(2 * np.pi * x / L)
            return u1 + u2
    
    return np.zeros_like(x)


def get_initial_condition(case: TestCase):
    params = case.params
    L = params.get("L", 1.0)
    n = case.mode_number
    
    if case.exact_solution_type in ["fourier_superposition", "wave_superposition"]:
        return lambda x: np.sin(np.pi * x / L) + 0.5 * np.sin(2 * np.pi * x / L)
    else:
        return lambda x: np.sin(n * np.pi * x / L)


def run_heat1d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    k = params["k"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    
    heat_params = Heat1DParams(k=k, L=L, nx=nx, t_span=(0.0, t_final), enforce_nonnegativity=False)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )
    
    x = np.linspace(0.0, L, nx)
    ic_fn = get_initial_condition(case)
    exact = compute_exact_solution(case, x, t_final)
    
    results = []
    for algo in algorithms:
        try:
            solver = get_solver(algo)
            sol, info, _ = solver.solve(params=heat_params, bc=bc, initial=ic_fn)
            diff = sol - exact
            results.append({
                "case_name": case.name,
                "equation_type": "heat1d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info.elapsed_s),
                "params": params,
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "heat1d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e),
            })
    
    return results


def run_wave1d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    c = params["c"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    
    nt = max(200, int(t_final * 400))
    
    wave_params = Wave1DParams(c=c, L=L, nx=nx, t_span=(0.0, t_final), nt=nt)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )
    
    x = np.linspace(0.0, L, nx)
    ic_fn = get_initial_condition(case)
    exact = compute_exact_solution(case, x, t_final)
    
    results = []
    solver_fns = {
        "fdm": solve_wave1d,
        "fem": solve_wave1d_fem,
        "spectral": solve_wave1d_spectral_v2,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol, info, _ = solver_fns[algo](
                params=wave_params,
                bc=bc,
                initial_displacement=ic_fn,
                initial_velocity=lambda x: np.zeros_like(x),
            )
            diff = sol - exact
            results.append({
                "case_name": case.name,
                "equation_type": "wave1d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info.elapsed_s),
                "params": params,
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "wave1d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e),
            })
    
    return results


def compute_algorithm_stats(results: List[Dict], algorithm: str) -> Dict[str, Any]:
    algo_results = [r for r in results if r["algorithm"] == algorithm and r["l2_error"] is not None]
    if not algo_results:
        return {"algorithm": algorithm, "num_cases": 0, "mean_l2_error": None, "std_l2_error": None}
    
    l2_errors = [r["l2_error"] for r in algo_results]
    elapsed_times = [r["elapsed_s"] for r in algo_results]
    
    return {
        "algorithm": algorithm,
        "num_cases": len(algo_results),
        "mean_l2_error": float(np.mean(l2_errors)),
        "std_l2_error": float(np.std(l2_errors)),
        "min_l2_error": float(np.min(l2_errors)),
        "max_l2_error": float(np.max(l2_errors)),
        "mean_elapsed_s": float(np.mean(elapsed_times)),
    }


def run_diverse_benchmark() -> Dict[str, Any]:
    all_results: List[Dict[str, Any]] = []
    start_time = time.time()
    
    print("=" * 60)
    print("DIVERSE BENCHMARK: Testing DIFFERENT problems")
    print("=" * 60)
    
    print("\nRunning diverse Heat1D test cases...")
    for case in HEAT1D_TEST_CASES:
        print(f"  {case.name}: k={case.params['k']}, L={case.params['L']}, mode={case.mode_number}")
        results = run_heat1d_case(case, ["fdm", "fvm", "fem", "spectral", "pinn"])
        all_results.extend(results)
    
    print("\nRunning diverse Wave1D test cases...")
    for case in WAVE1D_TEST_CASES:
        print(f"  {case.name}: c={case.params['c']}, L={case.params['L']}, mode={case.mode_number}")
        results = run_wave1d_case(case, ["fdm", "fem", "spectral"])
        all_results.extend(results)
    
    elapsed = time.time() - start_time
    
    heat1d_results = [r for r in all_results if r["equation_type"] == "heat1d"]
    wave1d_results = [r for r in all_results if r["equation_type"] == "wave1d"]
    
    heat1d_stats = [compute_algorithm_stats(heat1d_results, algo) for algo in ["fdm", "fvm", "fem", "spectral", "pinn"]]
    heat1d_stats = [s for s in heat1d_stats if s["num_cases"] > 0]
    
    wave1d_stats = [compute_algorithm_stats(wave1d_results, algo) for algo in ["fdm", "fem", "spectral"]]
    wave1d_stats = [s for s in wave1d_stats if s["num_cases"] > 0]
    
    payload = {
        "generated_at": time.time(),
        "total_elapsed_s": elapsed,
        "total_cases": len(HEAT1D_TEST_CASES) + len(WAVE1D_TEST_CASES),
        "heat1d_cases": len(HEAT1D_TEST_CASES),
        "wave1d_cases": len(WAVE1D_TEST_CASES),
        "heat1d_stats": heat1d_stats,
        "wave1d_stats": wave1d_stats,
        "all_results": all_results,
    }
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "diverse_benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n[ok] Results saved to: {out_path}")
    
    print("\n" + "=" * 60)
    print("Heat1D Statistics (8 DIFFERENT test cases)")
    print("=" * 60)
    print(f"{'Algorithm':<12} {'Mean L2':<15} {'Std L2':<15} {'Min L2':<15} {'Max L2':<15}")
    print("-" * 72)
    for stat in heat1d_stats:
        print(f"{stat['algorithm']:<12} {stat['mean_l2_error']:<15.6e} {stat['std_l2_error']:<15.6e} {stat['min_l2_error']:<15.6e} {stat['max_l2_error']:<15.6e}")
    
    print("\n" + "=" * 60)
    print("Wave1D Statistics (8 DIFFERENT test cases)")
    print("=" * 60)
    print(f"{'Algorithm':<12} {'Mean L2':<15} {'Std L2':<15} {'Min L2':<15} {'Max L2':<15}")
    print("-" * 72)
    for stat in wave1d_stats:
        print(f"{stat['algorithm']:<12} {stat['mean_l2_error']:<15.6e} {stat['std_l2_error']:<15.6e} {stat['min_l2_error']:<15.6e} {stat['max_l2_error']:<15.6e}")
    
    return payload


def main():
    parser = argparse.ArgumentParser(description="Diverse PDE benchmark")
    parser.add_argument("command", choices=["run"])
    args = parser.parse_args()
    
    if args.command == "run":
        run_diverse_benchmark()


if __name__ == "__main__":
    main()
