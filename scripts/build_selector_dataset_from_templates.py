"""基于模板问题构建算法选择器训练数据集.

Usage:
  python -m scripts.build_selector_dataset_from_templates --input real_world_benchmark/generated_selector_problems_200.json --output real_world_benchmark/selector_training_dataset_200.json --runs 3
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from config.constants import BoundaryCondition
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    Wave1DParams,
    get_solver,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "real_world_benchmark" / "selector_training_dataset.json"


def get_exact_solution_heat1d(params: Dict[str, Any]) -> np.ndarray:
    k = params.get("k", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 51)
    t_final = params.get("t_final", 0.1)
    mode = params.get("mode", 1)

    x = np.linspace(0, L, nx)
    decay = np.exp(-k * (mode * np.pi / L) ** 2 * t_final)
    return decay * np.sin(mode * np.pi * x / L)


def get_exact_solution_wave1d(params: Dict[str, Any]) -> np.ndarray:
    c = params.get("c", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 51)
    t_final = params.get("t_final", 0.1)
    mode = params.get("mode", 1)

    x = np.linspace(0, L, nx)
    omega = c * mode * np.pi / L
    return np.cos(omega * t_final) * np.sin(mode * np.pi * x / L)


def get_exact_solution_heat2d(params: Dict[str, Any]) -> np.ndarray:
    k = params.get("k", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 21)
    ny = params.get("ny", 21)
    t_final = params.get("t_final", 0.1)
    mx = params.get("mx", 1)
    my = params.get("my", 1)

    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")

    decay = np.exp(-k * ((mx * np.pi / L) ** 2 + (my * np.pi / L) ** 2) * t_final)
    return decay * np.sin(mx * np.pi * X / L) * np.sin(my * np.pi * Y / L)


def get_exact_solution_wave2d(params: Dict[str, Any]) -> np.ndarray:
    c = params.get("c", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 21)
    ny = params.get("ny", 21)
    t_final = params.get("t_final", 0.1)
    mx = params.get("mx", 1)
    my = params.get("my", 1)

    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")

    omega = c * np.sqrt((mx * np.pi / L) ** 2 + (my * np.pi / L) ** 2)
    return np.cos(omega * t_final) * np.sin(mx * np.pi * X / L) * np.sin(my * np.pi * Y / L)


def get_exact_solution_heat3d(params: Dict[str, Any]) -> np.ndarray:
    k = params.get("k", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 11)
    ny = params.get("ny", 11)
    nz = params.get("nz", 11)
    t_final = params.get("t_final", 0.1)
    mode = params.get("mode", 1)

    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    z = np.linspace(0, L, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    decay = np.exp(-k * 3 * (mode * np.pi / L) ** 2 * t_final)
    return decay * np.sin(mode * np.pi * X / L) * np.sin(mode * np.pi * Y / L) * np.sin(mode * np.pi * Z / L)


def get_exact_solution_wave3d(params: Dict[str, Any]) -> np.ndarray:
    c = params.get("c", 1.0)
    L = params.get("L", 1.0)
    nx = params.get("nx", 11)
    ny = params.get("ny", 11)
    nz = params.get("nz", 11)
    t_final = params.get("t_final", 0.1)
    mode = params.get("mode", 1)

    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    z = np.linspace(0, L, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    omega = c * mode * np.pi * np.sqrt(3) / L
    return np.cos(omega * t_final) * np.sin(mode * np.pi * X / L) * np.sin(mode * np.pi * Y / L) * np.sin(mode * np.pi * Z / L)


def get_exact_solution_poisson3d(params: Dict[str, Any]) -> np.ndarray:
    L = params.get("L", 1.0)
    nx = params.get("nx", 11)
    ny = params.get("ny", 11)
    nz = params.get("nz", 11)
    mode = params.get("mode", 1)

    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, ny)
    z = np.linspace(0, L, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    return np.sin(mode * np.pi * X / L) * np.sin(mode * np.pi * Y / L) * np.sin(mode * np.pi * Z / L)


def compute_l2_error(solution: np.ndarray, exact: np.ndarray) -> float:
    diff = solution - exact
    return float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))


SOLVER_MAP = {
    "heat1d": {
        "fdm": get_exact_solution_heat1d,
        "fvm": get_exact_solution_heat1d,
        "fem": get_exact_solution_heat1d,
        "spectral": get_exact_solution_heat1d,
    },
    "wave1d": {
        "fdm": get_exact_solution_wave1d,
        "fem": get_exact_solution_wave1d,
        "spectral": get_exact_solution_wave1d,
    },
    "heat2d": {
        "fdm": get_exact_solution_heat2d,
        "fvm": get_exact_solution_heat2d,
        "fem": get_exact_solution_heat2d,
    },
    "wave2d": {
        "fdm": get_exact_solution_wave2d,
        "fem": get_exact_solution_wave2d,
        "spectral": get_exact_solution_wave2d,
    },
    "heat3d": {
        "fdm": get_exact_solution_heat3d,
        "fvm": get_exact_solution_heat3d,
        "fem": get_exact_solution_heat3d,
    },
    "wave3d": {
        "fdm": get_exact_solution_wave3d,
        "fem": get_exact_solution_wave3d,
        "spectral": get_exact_solution_wave3d,
    },
    "poisson3d": {
        "fdm": get_exact_solution_poisson3d,
        "fem": get_exact_solution_poisson3d,
        "bem": get_exact_solution_poisson3d,
    },
}


def solve_single_run(problem: Dict[str, Any], algorithm: str) -> Optional[Dict[str, Any]]:
    eq_type = problem["equation_type"]
    params = problem["params"]

    if eq_type not in SOLVER_MAP or algorithm not in SOLVER_MAP[eq_type]:
        return None

    exact_fn = SOLVER_MAP[eq_type][algorithm]

    try:
        start_time = time.time()

        if eq_type == "heat1d":
            heat_params = Heat1DParams(
                k=params.get("k", 1.0),
                L=params.get("L", 1.0),
                nx=params["nx"],
                t_span=(0.0, params["t_final"]),
                enforce_nonnegativity=False,
            )
            bc = BoundarySpec(
                bc_type=BoundaryCondition.DIRICHLET,
                left_value=lambda t: 0.0,
                right_value=lambda t: 0.0,
            )
            mode = params.get("mode", 1)
            ic_fn = lambda x: np.sin(mode * np.pi * x / params.get("L", 1.0))
            solver = get_solver(algorithm)
            result, info, _ = solver.solve(params=heat_params, bc=bc, initial=ic_fn)

        elif eq_type == "wave1d":
            wave_params = Wave1DParams(
                c=params.get("c", 1.0),
                L=params.get("L", 1.0),
                nx=params["nx"],
                t_span=(0.0, params["t_final"]),
                nt=params.get("nt", 200),
            )
            bc = BoundarySpec(
                bc_type=BoundaryCondition.DIRICHLET,
                left_value=lambda t: 0.0,
                right_value=lambda t: 0.0,
            )
            mode = params.get("mode", 1)
            ic_fn = lambda x: np.sin(mode * np.pi * x / params.get("L", 1.0))
            solver = get_solver(algorithm)
            result, info, _ = solver.solve(params=wave_params, bc=bc, initial=ic_fn)

        elif eq_type == "heat2d":
            nx = params["nx"]
            ny = params.get("ny", nx)
            L = params.get("L", 1.0)
            k = params.get("k", 1.0)
            t_final = params["t_final"]
            nt = params.get("nt", 100)
            
            dx = L / (nx - 1)
            stability_limit = 1.0 / (2.0 * k * (2.0 / dx**2))
            nt = int(np.ceil(t_final / stability_limit))
            
            mx = params.get("mx", 1)
            my = params.get("my", 1)
            x = np.linspace(0.0, L, nx)
            y = np.linspace(0.0, L, ny)
            X, Y = np.meshgrid(x, y, indexing="xy")
            ic_fn = lambda x, y: np.sin(mx * np.pi * X / L) * np.sin(my * np.pi * Y / L)
            
            bc = BoundarySpec(bc_type=BoundaryCondition.DIRICHLET, left_value=lambda t: 0.0, right_value=lambda t: 0.0, top_value=lambda t: 0.0, bottom_value=lambda t: 0.0)
            
            solver = get_solver(algorithm)
            result, info_pack = solver.solve(nx=nx, ny=ny, Lx=L, Ly=L, k=k, t_span=(0.0, t_final), nt=nt, bc=bc, initial=ic_fn)

        elif eq_type == "wave2d":
            nx = params["nx"]
            ny = params.get("ny", nx)
            L = params.get("L", 1.0)
            c = params.get("c", 1.0)
            t_final = params["t_final"]
            nt = params.get("nt", 100)
            
            dx = L / (nx - 1)
            stability_limit = 1.0 / (c * np.sqrt(2.0 / dx**2))
            nt = int(np.ceil(t_final / stability_limit))
            
            mx = params.get("mx", 1)
            my = params.get("my", 1)
            x = np.linspace(0.0, L, nx)
            y = np.linspace(0.0, L, ny)
            X, Y = np.meshgrid(x, y, indexing="xy")
            ic_fn = lambda x, y: np.sin(mx * np.pi * X / L) * np.sin(my * np.pi * Y / L)
            
            bc = BoundarySpec(bc_type=BoundaryCondition.DIRICHLET, left_value=lambda t: 0.0, right_value=lambda t: 0.0, top_value=lambda t: 0.0, bottom_value=lambda t: 0.0)
            
            solver = get_solver(algorithm)
            result, info_pack = solver.solve(nx=nx, ny=ny, Lx=L, Ly=L, c=c, t_span=(0.0, t_final), nt=nt, bc=bc, initial=ic_fn)

        else:
            return None

        elapsed = time.time() - start_time
        exact = exact_fn(params)
        error = compute_l2_error(result, exact)

        return {"algorithm": algorithm, "error": error, "time": elapsed}

    except Exception as e:
        return None


def solve_problem_with_all_algorithms(
    problem: Dict[str, Any], num_runs: int = 3
) -> Dict[str, Any]:
    eq_type = problem["equation_type"]
    algorithms = list(SOLVER_MAP.get(eq_type, {}).keys())

    all_results = {algo: [] for algo in algorithms}

    for run in range(num_runs):
        for algo in algorithms:
            result = solve_single_run(problem, algo)
            if result:
                all_results[algo].append(result)

    avg_results = {}
    for algo, results in all_results.items():
        if results:
            errors = [r["error"] for r in results]
            times = [r["time"] for r in results]
            avg_results[algo] = {
                "mean_error": float(np.mean(errors)),
                "std_error": float(np.std(errors)),
                "mean_time": float(np.mean(times)),
            }

    return avg_results


def process_problems(problems: List[Dict[str, Any]], num_runs: int = 3) -> List[Dict[str, Any]]:
    processed = []
    start_time = time.time()

    for i, problem in enumerate(problems):
        if (i + 1) % 20 == 0:
            elapsed = time.time() - start_time
            eta = elapsed / (i + 1) * (len(problems) - i - 1)
            print(f"  Progress: {i+1}/{len(problems)} ({(i+1)/len(problems)*100:.1f}%) - ETA: {eta:.0f}s")

        avg_results = solve_problem_with_all_algorithms(problem, num_runs)

        if not avg_results:
            continue

        best_algo = min(avg_results.keys(), key=lambda a: avg_results[a]["mean_error"])

        processed.append({
            "problem_id": problem["problem_id"],
            "template_id": problem.get("template_id"),
            "equation_type": problem["equation_type"],
            "dimension": problem["dimension"],
            "params": problem["params"],
            "physics_features": problem["physics_features"],
            "hardware_features": problem["hardware_features"],
            "domain_features": problem["domain_features"],
            "metadata": problem.get("metadata", {}),
            "algorithm_results": avg_results,
            "best_algorithm": best_algo,
            "best_error": avg_results[best_algo]["mean_error"],
        })

    return processed


def main():
    parser = argparse.ArgumentParser(description="构建算法选择器训练数据集")
    parser.add_argument("--input", type=str, required=True, help="输入问题文件")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--runs", type=int, default=3, help="每题求解次数")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("=" * 60)
    print("构建算法选择器训练数据集")
    print("=" * 60)

    print(f"\n[1/2] Loading problems from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problems = data.get("problems", [])
    print(f"  Loaded {len(problems)} problems")

    print(f"\n[2/2] Solving problems with all algorithms ({args.runs} runs each)...")
    processed = process_problems(problems, args.runs)
    print(f"  Processed {len(processed)} problems")

    output_data = {
        "generated_at": time.time(),
        "config": {
            "num_problems_input": len(problems),
            "num_problems_output": len(processed),
            "num_runs": args.runs,
        },
        "problems": processed,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    best_algo_counts = {}
    for p in processed:
        algo = p["best_algorithm"]
        best_algo_counts[algo] = best_algo_counts.get(algo, 0) + 1

    print(f"\n[ok] Output saved to: {output_path}")
    print(f"\nBest algorithm distribution:")
    for algo, count in sorted(best_algo_counts.items(), key=lambda x: -x[1]):
        print(f"  {algo}: {count} ({count/len(processed)*100:.1f}%)")


if __name__ == "__main__":
    main()
