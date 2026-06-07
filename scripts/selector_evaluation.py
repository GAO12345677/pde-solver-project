"""Neural Network Algorithm Selector Evaluation.

This script evaluates the algorithm selector by:
1. Generating 1000 diverse PDE problems
2. Running all algorithms on each problem
3. Finding the actual best algorithm
4. Using neural network to predict best algorithm
5. Comparing predictions with actual best
6. Computing selection accuracy

Usage:
  python scripts/selector_evaluation.py run
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    solve_heat2d_fdm,
    solve_heat2d_fem,
    solve_heat2d_fvm,
    solve_wave2d_fdm,
    solve_wave2d_fem,
    solve_wave2d_spectral,
    solve_heat3d_fdm,
    solve_heat3d_fem,
    solve_heat3d_fvm,
    solve_wave3d_fdm,
    solve_wave3d_fem,
    solve_wave3d_spectral,
    solve_poisson3d_fdm,
    solve_poisson3d_fem,
    solve_poisson3d_bem,
)
from algorithm.selector import AlgorithmSelectionError, AlgorithmSelector


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "real_world_benchmark"
DEFAULT_TAG = "selector_evaluation"


def checkpoint_path_for(tag: str) -> Path:
    return OUT_DIR / f"{tag}_checkpoint.json"


def results_path_for(tag: str) -> Path:
    return OUT_DIR / f"{tag}_results.json"
@dataclass
class PDEProblem:
    problem_id: int
    equation_type: str
    dimension: int
    params: Dict[str, Any]
    physics_features: np.ndarray
    hardware_features: np.ndarray
    domain_features: np.ndarray


@dataclass
class EvaluationResult:
    problem_id: int
    equation_type: str
    predicted_algorithm: str
    actual_best_algorithm: str
    prediction_correct: bool
    all_algorithm_errors: Dict[str, float]
    all_algorithm_times: Dict[str, float]
    selector_confidence: Optional[float] = None
    raw_predicted_algorithm: Optional[str] = None
    candidate_algorithms: Optional[List[str]] = None
    actual_best_supported_algorithm: Optional[str] = None
    supported_prediction_correct: Optional[bool] = None
    prediction_error: Optional[str] = None


def generate_diverse_problems(num_problems: int = 1000, seed: int = 42) -> List[PDEProblem]:
    rng = np.random.default_rng(seed)
    problems: List[PDEProblem] = []
    
    equation_types = ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "wave3d", "poisson3d"]
    weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]
    
    problem_id = 0
    while len(problems) < num_problems:
        eq_type = rng.choice(equation_types, p=weights)
        
        if eq_type == "heat1d":
            k = rng.choice([0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0])
            L = rng.choice([0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0])
            nx = rng.choice([51, 76, 101, 151, 201])
            mode = rng.choice([1, 2, 3, 4, 5])
            t_final = 0.01 * L**2 / k
            t_final = max(0.001, min(t_final, 0.5))
            
            dim = 0.0
            nonlinear = rng.uniform(0.0, 0.3)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.1, 0.4)
            problem_size = (nx - 51) / (201 - 51)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.0, 0.3), rng.uniform(0.2, 0.5), rng.uniform(0.1, 0.4), 0.0, rng.uniform(0.3, 0.6)])
            domain = np.array([rng.uniform(0.5, 1.0), rng.uniform(0.3, 0.7), rng.uniform(0.4, 0.8)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=1,
                params={"k": k, "L": L, "nx": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "wave1d":
            c = rng.choice([0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0])
            L = rng.choice([0.5, 0.75, 1.0, 1.5, 2.0, 3.0])
            nx = rng.choice([51, 76, 101, 151, 201])
            mode = rng.choice([1, 2, 3, 4, 5])
            omega = c * mode * np.pi / L
            T = 2 * np.pi / omega
            t_final = min(0.5 * T, 0.5)
            t_final = max(0.1, t_final)
            
            dim = 0.0
            nonlinear = rng.uniform(0.0, 0.2)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.1, 0.3)
            problem_size = (nx - 51) / (201 - 51)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.0, 0.3), rng.uniform(0.2, 0.5), rng.uniform(0.1, 0.4), 0.0, rng.uniform(0.3, 0.6)])
            domain = np.array([rng.uniform(0.4, 0.9), rng.uniform(0.4, 0.8), rng.uniform(0.4, 0.8)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=1,
                params={"c": c, "L": L, "nx": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "heat2d":
            k = rng.choice([0.5, 1.0, 1.5, 2.0, 3.0])
            L = rng.choice([1.0, 1.5, 2.0])
            nx = rng.choice([21, 31, 41, 51])
            mode = rng.choice([1, 2])
            t_final = 0.005 * L**2 / k
            t_final = max(0.001, min(t_final, 0.1))
            
            dim = 0.5
            nonlinear = rng.uniform(0.1, 0.4)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.2, 0.5)
            problem_size = (nx - 21) / (51 - 21)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.2, 0.5), rng.uniform(0.3, 0.6), rng.uniform(0.2, 0.5), rng.uniform(0.0, 0.3), rng.uniform(0.4, 0.7)])
            domain = np.array([rng.uniform(0.5, 1.0), rng.uniform(0.3, 0.6), rng.uniform(0.4, 0.7)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=2,
                params={"k": k, "L": L, "nx": nx, "ny": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "wave2d":
            c = rng.choice([0.5, 1.0, 1.5, 2.0])
            L = rng.choice([1.0, 1.5, 2.0])
            nx = rng.choice([21, 31, 41, 51])
            mode = rng.choice([1, 2])
            t_final = 0.1 * L / c
            t_final = max(0.05, min(t_final, 0.3))
            
            dim = 0.5
            nonlinear = rng.uniform(0.0, 0.3)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.2, 0.4)
            problem_size = (nx - 21) / (51 - 21)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.2, 0.5), rng.uniform(0.3, 0.6), rng.uniform(0.2, 0.5), rng.uniform(0.0, 0.3), rng.uniform(0.4, 0.7)])
            domain = np.array([rng.uniform(0.4, 0.9), rng.uniform(0.4, 0.7), rng.uniform(0.4, 0.7)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=2,
                params={"c": c, "L": L, "nx": nx, "ny": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "heat3d":
            k = rng.choice([0.5, 1.0, 1.5, 2.0])
            L = rng.choice([1.0, 1.5])
            nx = rng.choice([11, 13, 15])
            mode = rng.choice([1, 2])
            t_final = 0.002 * L**2 / k
            t_final = max(0.001, min(t_final, 0.05))
            
            dim = 1.0
            nonlinear = rng.uniform(0.2, 0.5)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.3, 0.6)
            problem_size = (nx - 11) / (15 - 11)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.4, 0.7), rng.uniform(0.4, 0.7), rng.uniform(0.3, 0.6), rng.uniform(0.1, 0.4), rng.uniform(0.5, 0.8)])
            domain = np.array([rng.uniform(0.5, 1.0), rng.uniform(0.2, 0.5), rng.uniform(0.3, 0.6)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=3,
                params={"k": k, "L": L, "nx": nx, "ny": nx, "nz": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "wave3d":
            c = rng.choice([0.5, 1.0, 1.5])
            L = rng.choice([1.0, 1.5])
            nx = rng.choice([11, 13, 15])
            mode = rng.choice([1, 2])
            t_final = 0.05 * L / c
            t_final = max(0.02, min(t_final, 0.2))
            
            dim = 1.0
            nonlinear = rng.uniform(0.1, 0.4)
            unsteady = 1.0
            bc_complexity = rng.uniform(0.3, 0.5)
            problem_size = (nx - 11) / (15 - 11)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.4, 0.7), rng.uniform(0.4, 0.7), rng.uniform(0.3, 0.6), rng.uniform(0.1, 0.4), rng.uniform(0.5, 0.8)])
            domain = np.array([rng.uniform(0.4, 0.9), rng.uniform(0.3, 0.6), rng.uniform(0.3, 0.6)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=3,
                params={"c": c, "L": L, "nx": nx, "ny": nx, "nz": nx, "t_final": t_final, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
            
        elif eq_type == "poisson3d":
            L = rng.choice([1.0, 1.5, 2.0])
            nx = rng.choice([11, 13, 15])
            mode = rng.choice([1, 2])
            
            dim = 1.0
            nonlinear = rng.uniform(0.0, 0.2)
            unsteady = 0.0
            bc_complexity = rng.uniform(0.2, 0.5)
            problem_size = (nx - 11) / (15 - 11)
            
            physics = np.array([dim, nonlinear, unsteady, bc_complexity, problem_size])
            hardware = np.array([rng.uniform(0.3, 0.6), rng.uniform(0.3, 0.6), rng.uniform(0.2, 0.5), rng.uniform(0.0, 0.3), rng.uniform(0.4, 0.7)])
            domain = np.array([rng.uniform(0.6, 1.0), rng.uniform(0.2, 0.5), rng.uniform(0.4, 0.7)])
            
            problems.append(PDEProblem(
                problem_id=problem_id,
                equation_type=eq_type,
                dimension=3,
                params={"L": L, "nx": nx, "ny": nx, "nz": nx, "mode": mode},
                physics_features=physics,
                hardware_features=hardware,
                domain_features=domain,
            ))
        
        problem_id += 1
    
    return problems[:num_problems]


def solve_problem(problem: PDEProblem, num_runs: int = 10) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Solve a problem with all applicable algorithms, return mean errors and times."""
    errors: Dict[str, List[float]] = {}
    times: Dict[str, List[float]] = {}
    
    for run in range(num_runs):
        if problem.equation_type == "heat1d":
            run_errors, run_times = _solve_heat1d(problem)
        elif problem.equation_type == "wave1d":
            run_errors, run_times = _solve_wave1d(problem)
        elif problem.equation_type == "heat2d":
            run_errors, run_times = _solve_heat2d(problem)
        elif problem.equation_type == "wave2d":
            run_errors, run_times = _solve_wave2d(problem)
        elif problem.equation_type == "heat3d":
            run_errors, run_times = _solve_heat3d(problem)
        elif problem.equation_type == "wave3d":
            run_errors, run_times = _solve_wave3d(problem)
        elif problem.equation_type == "poisson3d":
            run_errors, run_times = _solve_poisson3d(problem)
        else:
            continue
        
        for algo, err in run_errors.items():
            if algo not in errors:
                errors[algo] = []
                times[algo] = []
            if err is not None and not np.isnan(err):
                errors[algo].append(err)
                times[algo].append(run_times.get(algo, 0.0))
    
    mean_errors = {algo: float(np.mean(errs)) for algo, errs in errors.items() if errs}
    mean_times = {algo: float(np.mean(ts)) for algo, ts in times.items() if ts}
    
    return mean_errors, mean_times


def _solve_heat1d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    k = params["k"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    heat_params = Heat1DParams(k=k, L=L, nx=nx, t_span=(0.0, t_final), enforce_nonnegativity=False)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )
    
    x = np.linspace(0.0, L, nx)
    ic_fn = lambda x: np.sin(n * np.pi * x / L)
    exact = np.exp(-k * (n * np.pi / L) ** 2 * t_final) * np.sin(n * np.pi * x / L)
    
    errors = {}
    times = {}
    
    for algo in ["fdm", "fvm", "fem", "spectral"]:
        try:
            solver = get_solver(algo)
            start = time.time()
            sol, info, _ = solver.solve(params=heat_params, bc=bc, initial=ic_fn)
            elapsed = time.time() - start
            diff = sol - exact
            errors[algo] = float(np.linalg.norm(diff) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_wave1d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    c = params["c"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    nt = max(200, int(t_final * 400))
    
    wave_params = Wave1DParams(c=c, L=L, nx=nx, t_span=(0.0, t_final), nt=nt)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )
    
    x = np.linspace(0.0, L, nx)
    ic_fn = lambda x: np.sin(n * np.pi * x / L)
    omega = c * n * np.pi / L
    exact = np.cos(omega * t_final) * np.sin(n * np.pi * x / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_wave1d,
        "fem": solve_wave1d_fem,
        "spectral": solve_wave1d_spectral_v2,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol, info, _ = solve_fn(
                params=wave_params,
                bc=bc,
                initial_displacement=ic_fn,
                initial_velocity=lambda x: np.zeros_like(x),
            )
            elapsed = time.time() - start
            diff = sol - exact
            errors[algo] = float(np.linalg.norm(diff) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_heat2d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    k = params["k"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    dx = L / (nx - 1)
    stability_limit = 1.0 / (2.0 * k * (2.0 / dx**2))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, nx)
    X, Y = np.meshgrid(x, y, indexing="xy")
    exact = np.exp(-k * (n * np.pi)**2 * (2.0/L**2) * t_final) * np.sin(n * np.pi * X / L) * np.sin(n * np.pi * Y / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_heat2d_fdm,
        "fvm": solve_heat2d_fvm,
        "fem": solve_heat2d_fem,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol2d, info_pack = solve_fn(nx=nx, ny=nx, Lx=L, Ly=L, k=k, t_span=(0.0, t_final), nt=nt)
            elapsed = time.time() - start
            diff = sol2d - exact
            errors[algo] = float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_wave2d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    c = params["c"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    dx = L / (nx - 1)
    stability_limit = 1.0 / (c * np.sqrt(2.0 / dx**2))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, nx)
    X, Y = np.meshgrid(x, y, indexing="xy")
    omega = c * n * np.pi * np.sqrt(2.0) / L
    exact = np.cos(omega * t_final) * np.sin(n * np.pi * X / L) * np.sin(n * np.pi * Y / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_wave2d_fdm,
        "fem": solve_wave2d_fem,
        "spectral": solve_wave2d_spectral,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol2d, info_pack = solve_fn(nx=nx, ny=nx, Lx=L, Ly=L, c=c, t_span=(0.0, t_final), nt=nt)
            elapsed = time.time() - start
            diff = sol2d - exact
            errors[algo] = float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_heat3d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    k = params["k"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    dx = L / (nx - 1)
    stability_limit = 1.0 / (2.0 * k * (3.0 / dx**2))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, nx)
    z = np.linspace(0.0, L, nx)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = np.exp(-k * (n * np.pi)**2 * (3.0/L**2) * t_final) * np.sin(n * np.pi * X / L) * np.sin(n * np.pi * Y / L) * np.sin(n * np.pi * Z / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_heat3d_fdm,
        "fvm": solve_heat3d_fvm,
        "fem": solve_heat3d_fem,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol3d, info_pack = solve_fn(nx=nx, ny=nx, nz=nx, Lx=L, Ly=L, Lz=L, k=k, t_span=(0.0, t_final), nt=nt)
            elapsed = time.time() - start
            diff = sol3d - exact
            errors[algo] = float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_wave3d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    c = params["c"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = params["mode"]
    
    dx = L / (nx - 1)
    stability_limit = 1.0 / (c * np.sqrt(3.0 / dx**2))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, nx)
    z = np.linspace(0.0, L, nx)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    omega = c * n * np.pi * np.sqrt(3.0) / L
    exact = np.cos(omega * t_final) * np.sin(n * np.pi * X / L) * np.sin(n * np.pi * Y / L) * np.sin(n * np.pi * Z / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_wave3d_fdm,
        "fem": solve_wave3d_fem,
        "spectral": solve_wave3d_spectral,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol3d, info_pack = solve_fn(nx=nx, ny=nx, nz=nx, Lx=L, Ly=L, Lz=L, c=c, t_span=(0.0, t_final), nt=nt)
            elapsed = time.time() - start
            diff = sol3d - exact
            errors[algo] = float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def _solve_poisson3d(problem: PDEProblem) -> Tuple[Dict[str, float], Dict[str, float]]:
    params = problem.params
    L = params["L"]
    nx = params["nx"]
    n = params["mode"]
    
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, L, nx)
    z = np.linspace(0.0, L, nx)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = np.sin(n * np.pi * X / L) * np.sin(n * np.pi * Y / L) * np.sin(n * np.pi * Z / L)
    
    errors = {}
    times = {}
    
    solver_fns = {
        "fdm": solve_poisson3d_fdm,
        "fem": solve_poisson3d_fem,
        "bem": solve_poisson3d_bem,
    }
    
    for algo, solve_fn in solver_fns.items():
        try:
            start = time.time()
            sol3d, info = solve_fn(nx=nx, ny=nx, nz=nx, Lx=L, Ly=L, Lz=L)
            elapsed = time.time() - start
            diff = sol3d - exact
            errors[algo] = float(info.get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)))
            times[algo] = elapsed
        except Exception:
            errors[algo] = float('nan')
            times[algo] = 0.0
    
    return errors, times


def get_selector_prediction(selector: AlgorithmSelector, problem: PDEProblem, strategy: str) -> Tuple[str, Optional[float], Dict[str, float], Optional[str]]:
    try:
        result = selector.select(
            physics=problem.physics_features,
            hardware=problem.hardware_features,
            domain=problem.domain_features,
            strategy=strategy,
        )
        algorithm_key = str(result.get("algorithm_key") or result.get("selected_algorithm") or "")
        if not algorithm_key:
            raise KeyError("selector result missing algorithm_key/selected_algorithm")
        probs = result.get("static_probs") or {}
        confidence = None
        if probs:
            confidence = float(max(probs.values()))
        return algorithm_key, confidence, {str(k): float(v) for k, v in probs.items()}, None
    except Exception as exc:
        return "", None, {}, str(exc)


def choose_best_supported_prediction(
    raw_prediction: str,
    candidate_algorithms: List[str],
    probability_map: Dict[str, float],
) -> str:
    if raw_prediction in candidate_algorithms:
        return raw_prediction

    ranked_supported = [
        algo for algo, _ in sorted(
            ((algo, probability_map.get(algo, float("-inf"))) for algo in candidate_algorithms),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
    if ranked_supported and probability_map:
        return ranked_supported[0]

    return candidate_algorithms[0]


def load_checkpoint(checkpoint_path: Path) -> Tuple[List[EvaluationResult], int]:
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
            results = [EvaluationResult(**r) for r in data.get("results", [])]
            last_idx = data.get("last_problem_index", -1)
            print(f"  [checkpoint] Loaded {len(results)} results from problem index {last_idx}")
            return results, last_idx
        except Exception:
            pass
    return [], -1


def save_checkpoint(results: List[EvaluationResult], last_idx: int, checkpoint_path: Path):
    data = {
        "last_problem_index": last_idx,
        "results": [asdict(r) for r in results],
        "timestamp": time.time(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w") as f:
        json.dump(data, f)


def resolve_selector_strategy(selector: AlgorithmSelector, requested_strategy: str) -> Tuple[str, List[Dict[str, str]]]:
    candidates = [requested_strategy]
    for fallback in ["gnn_selector", "mlp_nn", "static_rf"]:
        if fallback not in candidates:
            candidates.append(fallback)

    failures: List[Dict[str, str]] = []
    for strategy in candidates:
        try:
            selector._load_or_train_static(strategy)
            return strategy, failures
        except AlgorithmSelectionError as exc:
            failures.append({"strategy": strategy, "error": str(exc)})

    raise AlgorithmSelectionError(f"failed to initialize any selector strategy: {failures}")


def run_evaluation(
    num_problems: int = 1000,
    num_runs: int = 10,
    seed: int = 42,
    strategy: str = "gnn_selector",
    tag: str = DEFAULT_TAG,
) -> Dict[str, Any]:
    print("=" * 70)
    print(f"NEURAL NETWORK ALGORITHM SELECTOR EVALUATION")
    print(f"Problems: {num_problems}, Runs per problem: {num_runs}")
    print("=" * 70)
    
    print("\n[1/4] Generating diverse PDE problems...")
    problems = generate_diverse_problems(num_problems, seed)
    print(f"  Generated {len(problems)} problems")
    
    eq_counts = {}
    for p in problems:
        eq_counts[p.equation_type] = eq_counts.get(p.equation_type, 0) + 1
    print(f"  Distribution: {eq_counts}")
    
    print("\n[2/4] Training algorithm selectors...")
    selector = AlgorithmSelector(model_dir="model")
    active_strategy, strategy_failures = resolve_selector_strategy(selector, strategy)
    print(f"  Active strategy: {active_strategy}")
    for failure in strategy_failures:
        print(f"  Skipped {failure['strategy']}: {failure['error']}")

    print("\n[3/4] Evaluating selector on all problems...")
    checkpoint_path = checkpoint_path_for(tag)
    results, start_idx = load_checkpoint(checkpoint_path)
    start_time = time.time()
    
    for i, problem in enumerate(problems):
        if i <= start_idx:
            continue
        
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            done = i + 1 - (start_idx + 1)
            if done > 0:
                rate = elapsed / done
                eta = rate * (len(problems) - i - 1)
            else:
                eta = 0
            print(f"  Progress: {i+1}/{len(problems)} ({(i+1)/len(problems)*100:.1f}%) - ETA: {eta:.0f}s")
        
        mean_errors, mean_times = solve_problem(problem, num_runs)
        
        if not mean_errors:
            save_checkpoint(results, i, checkpoint_path)
            continue
        
        best_algo = min(mean_errors.keys(), key=lambda a: mean_errors[a])
        candidate_algorithms = sorted(mean_errors.keys())

        predicted_algo, confidence, probability_map, prediction_error = get_selector_prediction(selector, problem, active_strategy)
        predicted_algo_mapped = choose_best_supported_prediction(predicted_algo, candidate_algorithms, probability_map)

        supported_candidates = [algo for algo in candidate_algorithms if algo in {"fdm", "fem", "spectral"}]
        actual_best_supported = None
        supported_prediction_correct = None
        if supported_candidates:
            actual_best_supported = min(supported_candidates, key=lambda a: mean_errors[a])
            supported_prediction_correct = predicted_algo_mapped == actual_best_supported
        
        results.append(EvaluationResult(
            problem_id=problem.problem_id,
            equation_type=problem.equation_type,
            predicted_algorithm=predicted_algo_mapped,
            actual_best_algorithm=best_algo,
            prediction_correct=(predicted_algo_mapped == best_algo),
            all_algorithm_errors=mean_errors,
            all_algorithm_times=mean_times,
            selector_confidence=confidence,
            raw_predicted_algorithm=predicted_algo or None,
            candidate_algorithms=candidate_algorithms,
            actual_best_supported_algorithm=actual_best_supported,
            supported_prediction_correct=supported_prediction_correct,
            prediction_error=prediction_error,
        ))
        
        if (i + 1) % 50 == 0:
            save_checkpoint(results, i, checkpoint_path)
    
    total_elapsed = time.time() - start_time
    
    print("\n[4/4] Computing statistics...")
    
    total_correct = sum(1 for r in results if r.prediction_correct)
    overall_accuracy = total_correct / len(results) if results else 0.0
    supported_results = [r for r in results if r.supported_prediction_correct is not None]
    supported_total_correct = sum(1 for r in supported_results if r.supported_prediction_correct)
    supported_accuracy = supported_total_correct / len(supported_results) if supported_results else 0.0
    unsupported_actual_best = sum(1 for r in results if r.actual_best_algorithm not in {"fdm", "fem", "spectral"})
    prediction_failures = [r for r in results if r.prediction_error]
    
    accuracy_by_eq: Dict[str, Dict[str, Any]] = {}
    for eq_type in ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "wave3d", "poisson3d"]:
        eq_results = [r for r in results if r.equation_type == eq_type]
        if eq_results:
            correct = sum(1 for r in eq_results if r.prediction_correct)
            supported_eq_results = [r for r in eq_results if r.supported_prediction_correct is not None]
            supported_eq_correct = sum(1 for r in supported_eq_results if r.supported_prediction_correct)
            accuracy_by_eq[eq_type] = {
                "total": len(eq_results),
                "correct": correct,
                "accuracy": correct / len(eq_results),
                "supported_total": len(supported_eq_results),
                "supported_correct": supported_eq_correct,
                "supported_accuracy": supported_eq_correct / len(supported_eq_results) if supported_eq_results else None,
            }
    
    confusion: Dict[str, Dict[str, int]] = {}
    for r in results:
        actual = r.actual_best_algorithm
        predicted = r.predicted_algorithm
        if actual not in confusion:
            confusion[actual] = {}
        confusion[actual][predicted] = confusion[actual].get(predicted, 0) + 1
    
    algo_stats: Dict[str, Dict[str, Any]] = {}
    for algo in ["fdm", "fvm", "fem", "spectral", "bem"]:
        algo_results = [r for r in results if algo in r.all_algorithm_errors]
        if algo_results:
            errors = [r.all_algorithm_errors[algo] for r in algo_results]
            times = [r.all_algorithm_times[algo] for r in algo_results]
            algo_stats[algo] = {
                "num_problems": len(algo_results),
                "mean_error": float(np.mean(errors)),
                "std_error": float(np.std(errors)),
                "mean_time": float(np.mean(times)),
            }
    
    payload = {
        "generated_at": time.time(),
        "config": {
            "num_problems": num_problems,
            "num_runs_per_problem": num_runs,
            "seed": seed,
            "requested_strategy": strategy,
            "active_strategy": active_strategy,
            "tag": tag,
        },
        "strategy_initialization_failures": strategy_failures,
        "overall_accuracy": overall_accuracy,
        "supported_accuracy": supported_accuracy,
        "supported_total_correct": supported_total_correct,
        "supported_total_problems": len(supported_results),
        "total_correct": total_correct,
        "total_problems": len(results),
        "total_elapsed_s": total_elapsed,
        "unsupported_actual_best_count": unsupported_actual_best,
        "prediction_failure_count": len(prediction_failures),
        "prediction_failure_examples": [
            {
                "problem_id": r.problem_id,
                "equation_type": r.equation_type,
                "prediction_error": r.prediction_error,
            }
            for r in prediction_failures[:10]
        ],
        "accuracy_by_equation": accuracy_by_eq,
        "confusion_matrix": confusion,
        "algorithm_statistics": algo_stats,
        "detailed_results": [asdict(r) for r in results[:100]],
    }
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = results_path_for(tag)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    
    print(f"\n[ok] Results saved to: {out_path}")
    
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"\nOverall Selection Accuracy: {overall_accuracy*100:.2f}%")
    print(f"Supported-Set Accuracy: {supported_accuracy*100:.2f}% ({supported_total_correct}/{len(supported_results)})")
    print(f"Correct Predictions: {total_correct}/{len(results)}")
    print(f"Unsupported Actual-Best Cases: {unsupported_actual_best}")
    print(f"Prediction Failures: {len(prediction_failures)}")
    print(f"Total Time: {total_elapsed:.1f}s")
    
    print("\nAccuracy by Equation Type:")
    print(f"{'Equation':<12} {'Total':<8} {'Correct':<8} {'Accuracy':<10} {'Supp.Acc':<10}")
    print("-" * 56)
    for eq_type, stats in accuracy_by_eq.items():
        supported_str = "n/a" if stats["supported_accuracy"] is None else f"{stats['supported_accuracy']*100:.1f}%"
        print(f"{eq_type:<12} {stats['total']:<8} {stats['correct']:<8} {stats['accuracy']*100:.1f}%   {supported_str:<10}")
    
    print("\nConfusion Matrix (Actual → Predicted):")
    print(f"{'Actual':<10} {'Predicted Counts':<40}")
    print("-" * 50)
    for actual, preds in sorted(confusion.items()):
        pred_str = ", ".join(f"{p}:{c}" for p, c in sorted(preds.items()))
        print(f"{actual:<10} {pred_str}")
    
    return payload


def main():
    parser = argparse.ArgumentParser(description="Algorithm Selector Evaluation")
    parser.add_argument("command", choices=["run", "clear"])
    parser.add_argument("--problems", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--strategy", type=str, default="gnn_selector")
    parser.add_argument("--tag", type=str, default=DEFAULT_TAG)
    args = parser.parse_args()
    
    if args.command == "clear":
        checkpoint_path = checkpoint_path_for(args.tag)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            print(f"Checkpoint cleared: {checkpoint_path}")
        else:
            print("No checkpoint to clear")
    elif args.command == "run":
        run_evaluation(args.problems, args.runs, args.seed, args.strategy, args.tag)


if __name__ == "__main__":
    main()
