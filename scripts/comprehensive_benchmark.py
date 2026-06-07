"""Comprehensive benchmark with 100+ diverse test cases.

This script tests solvers on a wide variety of problems to measure robustness.

Usage:
  python scripts/comprehensive_benchmark.py run
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "real_world_benchmark"


@dataclass
class TestCase:
    name: str
    equation_type: str
    dimension: int
    params: Dict[str, Any]
    boundary_type: str
    mode_number: int
    description: str


def generate_heat1d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    k_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    L_values = [0.5, 1.0, 2.0, 5.0]
    nx_values = [51, 101, 201]
    mode_values = [1, 2, 3, 5, 7]
    
    for k in k_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    t_final = 0.01 * L**2 / k
                    t_final = max(0.001, min(t_final, 0.5))
                    
                    cases.append(TestCase(
                        name=f"heat1d_{case_id:03d}_k{k}_L{L}_nx{nx}_m{mode}",
                        equation_type="heat1d",
                        dimension=1,
                        params={"k": k, "L": L, "nx": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Heat1D: k={k}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_wave1d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    c_values = [0.5, 1.0, 2.0, 3.0]
    L_values = [0.5, 1.0, 2.0, 5.0]
    nx_values = [51, 101, 201]
    mode_values = [1, 2, 3, 5, 7]
    
    for c in c_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    omega = c * mode * np.pi / L
                    T = 2 * np.pi / omega
                    t_final = min(0.5 * T, 0.5)
                    t_final = max(0.1, t_final)
                    
                    cases.append(TestCase(
                        name=f"wave1d_{case_id:03d}_c{c}_L{L}_nx{nx}_m{mode}",
                        equation_type="wave1d",
                        dimension=1,
                        params={"c": c, "L": L, "nx": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Wave1D: c={c}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_heat2d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    k_values = [0.5, 1.0, 2.0]
    L_values = [1.0, 2.0]
    nx_values = [21, 41]
    mode_values = [1, 2]
    
    for k in k_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    t_final = 0.005 * L**2 / k
                    t_final = max(0.001, min(t_final, 0.1))
                    
                    cases.append(TestCase(
                        name=f"heat2d_{case_id:03d}_k{k}_L{L}_nx{nx}_m{mode}",
                        equation_type="heat2d",
                        dimension=2,
                        params={"k": k, "Lx": L, "Ly": L, "nx": nx, "ny": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Heat2D: k={k}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_wave2d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    c_values = [0.5, 1.0, 2.0]
    L_values = [1.0, 2.0]
    nx_values = [21, 41]
    mode_values = [1, 2]
    
    for c in c_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    t_final = 0.1 * L / c
                    t_final = max(0.05, min(t_final, 0.3))
                    
                    cases.append(TestCase(
                        name=f"wave2d_{case_id:03d}_c{c}_L{L}_nx{nx}_m{mode}",
                        equation_type="wave2d",
                        dimension=2,
                        params={"c": c, "Lx": L, "Ly": L, "nx": nx, "ny": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Wave2D: c={c}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_heat3d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    k_values = [0.5, 1.0, 2.0]
    L_values = [1.0]
    nx_values = [11, 15]
    mode_values = [1, 2]
    
    for k in k_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    t_final = 0.002 * L**2 / k
                    t_final = max(0.001, min(t_final, 0.05))
                    
                    cases.append(TestCase(
                        name=f"heat3d_{case_id:03d}_k{k}_L{L}_nx{nx}_m{mode}",
                        equation_type="heat3d",
                        dimension=3,
                        params={"k": k, "Lx": L, "Ly": L, "Lz": L, "nx": nx, "ny": nx, "nz": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Heat3D: k={k}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_wave3d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    c_values = [0.5, 1.0, 2.0]
    L_values = [1.0]
    nx_values = [11, 15]
    mode_values = [1, 2]
    
    for c in c_values:
        for L in L_values:
            for nx in nx_values:
                for mode in mode_values:
                    t_final = 0.05 * L / c
                    t_final = max(0.02, min(t_final, 0.2))
                    
                    cases.append(TestCase(
                        name=f"wave3d_{case_id:03d}_c{c}_L{L}_nx{nx}_m{mode}",
                        equation_type="wave3d",
                        dimension=3,
                        params={"c": c, "Lx": L, "Ly": L, "Lz": L, "nx": nx, "ny": nx, "nz": nx, "t_final": t_final},
                        boundary_type="dirichlet",
                        mode_number=mode,
                        description=f"Wave3D: c={c}, L={L}, nx={nx}, mode={mode}",
                    ))
                    case_id += 1
    
    return cases


def generate_poisson3d_cases() -> List[TestCase]:
    cases = []
    case_id = 0
    
    L_values = [1.0, 2.0]
    nx_values = [11, 15]
    mode_values = [1, 2]
    
    for L in L_values:
        for nx in nx_values:
            for mode in mode_values:
                cases.append(TestCase(
                    name=f"poisson3d_{case_id:03d}_L{L}_nx{nx}_m{mode}",
                    equation_type="poisson3d",
                    dimension=3,
                    params={"Lx": L, "Ly": L, "Lz": L, "nx": nx, "ny": nx, "nz": nx},
                    boundary_type="dirichlet",
                    mode_number=mode,
                    description=f"Poisson3D: L={L}, nx={nx}, mode={mode}",
                ))
                case_id += 1
    
    return cases


ALL_CASES = (
    generate_heat1d_cases() +
    generate_wave1d_cases() +
    generate_heat2d_cases() +
    generate_wave2d_cases() +
    generate_heat3d_cases() +
    generate_wave3d_cases() +
    generate_poisson3d_cases()
)


def run_heat1d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    k = params["k"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = case.mode_number
    
    heat_params = Heat1DParams(k=k, L=L, nx=nx, t_span=(0.0, t_final), enforce_nonnegativity=False)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )
    
    x = np.linspace(0.0, L, nx)
    ic_fn = lambda x: np.sin(n * np.pi * x / L)
    exact = np.exp(-k * (n * np.pi / L) ** 2 * t_final) * np.sin(n * np.pi * x / L)
    
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
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "heat1d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_wave1d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    c = params["c"]
    L = params["L"]
    nx = params["nx"]
    t_final = params["t_final"]
    n = case.mode_number
    
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
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "wave1d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_heat2d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    k = params["k"]
    Lx = params["Lx"]
    Ly = params["Ly"]
    nx = params["nx"]
    ny = params["ny"]
    t_final = params["t_final"]
    n = case.mode_number
    
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2)))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    X, Y = np.meshgrid(x, y, indexing="xy")
    exact = np.exp(-k * (n * np.pi)**2 * ((1.0/Lx**2) + (1.0/Ly**2)) * t_final) * np.sin(n * np.pi * X / Lx) * np.sin(n * np.pi * Y / Ly)
    
    results = []
    solver_fns = {
        "fdm": solve_heat2d_fdm,
        "fvm": solve_heat2d_fvm,
        "fem": solve_heat2d_fem,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol2d, info_pack = solver_fns[algo](nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(0.0, t_final), nt=nt)
            diff = sol2d - exact
            results.append({
                "case_name": case.name,
                "equation_type": "heat2d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "heat2d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_wave2d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    c = params["c"]
    Lx = params["Lx"]
    Ly = params["Ly"]
    nx = params["nx"]
    ny = params["ny"]
    t_final = params["t_final"]
    n = case.mode_number
    
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    stability_limit = 1.0 / (c * np.sqrt((1.0 / dx**2) + (1.0 / dy**2)))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    X, Y = np.meshgrid(x, y, indexing="xy")
    omega = c * n * np.pi * np.sqrt((1.0/Lx**2) + (1.0/Ly**2))
    exact = np.cos(omega * t_final) * np.sin(n * np.pi * X / Lx) * np.sin(n * np.pi * Y / Ly)
    
    results = []
    solver_fns = {
        "fdm": solve_wave2d_fdm,
        "fem": solve_wave2d_fem,
        "spectral": solve_wave2d_spectral,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol2d, info_pack = solver_fns[algo](nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(0.0, t_final), nt=nt)
            diff = sol2d - exact
            results.append({
                "case_name": case.name,
                "equation_type": "wave2d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "wave2d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_heat3d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    k = params["k"]
    Lx = params["Lx"]
    Ly = params["Ly"]
    Lz = params["Lz"]
    nx = params["nx"]
    ny = params["ny"]
    nz = params["nz"]
    t_final = params["t_final"]
    n = case.mode_number
    
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    dz = Lz / (nz - 1)
    stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = np.exp(-k * (n * np.pi)**2 * ((1.0/Lx**2) + (1.0/Ly**2) + (1.0/Lz**2)) * t_final) * np.sin(n * np.pi * X / Lx) * np.sin(n * np.pi * Y / Ly) * np.sin(n * np.pi * Z / Lz)
    
    results = []
    solver_fns = {
        "fdm": solve_heat3d_fdm,
        "fvm": solve_heat3d_fvm,
        "fem": solve_heat3d_fem,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol3d, info_pack = solver_fns[algo](nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(0.0, t_final), nt=nt)
            diff = sol3d - exact
            results.append({
                "case_name": case.name,
                "equation_type": "heat3d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "heat3d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_wave3d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    c = params["c"]
    Lx = params["Lx"]
    Ly = params["Ly"]
    Lz = params["Lz"]
    nx = params["nx"]
    ny = params["ny"]
    nz = params["nz"]
    t_final = params["t_final"]
    n = case.mode_number
    
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    dz = Lz / (nz - 1)
    stability_limit = 1.0 / (c * np.sqrt((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
    nt = int(np.ceil(t_final / stability_limit))
    
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    omega = c * n * np.pi * np.sqrt((1.0/Lx**2) + (1.0/Ly**2) + (1.0/Lz**2))
    exact = np.cos(omega * t_final) * np.sin(n * np.pi * X / Lx) * np.sin(n * np.pi * Y / Ly) * np.sin(n * np.pi * Z / Lz)
    
    results = []
    solver_fns = {
        "fdm": solve_wave3d_fdm,
        "fem": solve_wave3d_fem,
        "spectral": solve_wave3d_spectral,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol3d, info_pack = solver_fns[algo](nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(0.0, t_final), nt=nt)
            diff = sol3d - exact
            results.append({
                "case_name": case.name,
                "equation_type": "wave3d",
                "algorithm": algo,
                "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                "linf_error": float(np.max(np.abs(diff))),
                "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                "params": {k: v for k, v in params.items() if k != "t_final"},
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "wave3d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
            })
    
    return results


def run_poisson3d_case(case: TestCase, algorithms: List[str]) -> List[Dict[str, Any]]:
    params = case.params
    Lx = params["Lx"]
    Ly = params["Ly"]
    Lz = params["Lz"]
    nx = params["nx"]
    ny = params["ny"]
    nz = params["nz"]
    n = case.mode_number
    
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = np.sin(n * np.pi * X / Lx) * np.sin(n * np.pi * Y / Ly) * np.sin(n * np.pi * Z / Lz)
    
    results = []
    solver_fns = {
        "fdm": solve_poisson3d_fdm,
        "fem": solve_poisson3d_fem,
        "bem": solve_poisson3d_bem,
    }
    
    for algo in algorithms:
        if algo not in solver_fns:
            continue
        try:
            sol3d, info = solver_fns[algo](nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            diff = sol3d - exact
            results.append({
                "case_name": case.name,
                "equation_type": "poisson3d",
                "algorithm": algo,
                "l2_error": float(info.get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                "linf_error": float(info.get("linf_error", np.max(np.abs(diff)))),
                "elapsed_s": float(info["elapsed_s"]),
                "params": params,
            })
        except Exception as e:
            results.append({
                "case_name": case.name,
                "equation_type": "poisson3d",
                "algorithm": algo,
                "l2_error": None,
                "linf_error": None,
                "elapsed_s": 0.0,
                "error": str(e)[:100],
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
        "median_l2_error": float(np.median(l2_errors)),
        "mean_elapsed_s": float(np.mean(elapsed_times)),
    }


def run_comprehensive_benchmark() -> Dict[str, Any]:
    all_results: List[Dict[str, Any]] = []
    start_time = time.time()
    
    print("=" * 70)
    print(f"COMPREHENSIVE BENCHMARK: {len(ALL_CASES)} test cases")
    print("=" * 70)
    
    case_counts = {
        "heat1d": len([c for c in ALL_CASES if c.equation_type == "heat1d"]),
        "wave1d": len([c for c in ALL_CASES if c.equation_type == "wave1d"]),
        "heat2d": len([c for c in ALL_CASES if c.equation_type == "heat2d"]),
        "wave2d": len([c for c in ALL_CASES if c.equation_type == "wave2d"]),
        "heat3d": len([c for c in ALL_CASES if c.equation_type == "heat3d"]),
        "wave3d": len([c for c in ALL_CASES if c.equation_type == "wave3d"]),
        "poisson3d": len([c for c in ALL_CASES if c.equation_type == "poisson3d"]),
    }
    
    print(f"\nTest case distribution:")
    for eq_type, count in case_counts.items():
        print(f"  {eq_type}: {count} cases")
    
    print("\nRunning Heat1D cases...")
    heat1d_cases = [c for c in ALL_CASES if c.equation_type == "heat1d"]
    for i, case in enumerate(heat1d_cases):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  Progress: {i+1}/{len(heat1d_cases)} - {case.name}")
        results = run_heat1d_case(case, ["fdm", "fvm", "fem", "spectral"])
        all_results.extend(results)
    
    print("\nRunning Wave1D cases...")
    wave1d_cases = [c for c in ALL_CASES if c.equation_type == "wave1d"]
    for i, case in enumerate(wave1d_cases):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  Progress: {i+1}/{len(wave1d_cases)} - {case.name}")
        results = run_wave1d_case(case, ["fdm", "fem", "spectral"])
        all_results.extend(results)
    
    print("\nRunning Heat2D cases...")
    heat2d_cases = [c for c in ALL_CASES if c.equation_type == "heat2d"]
    for i, case in enumerate(heat2d_cases):
        print(f"  Progress: {i+1}/{len(heat2d_cases)} - {case.name}")
        results = run_heat2d_case(case, ["fdm", "fvm", "fem"])
        all_results.extend(results)
    
    print("\nRunning Wave2D cases...")
    wave2d_cases = [c for c in ALL_CASES if c.equation_type == "wave2d"]
    for i, case in enumerate(wave2d_cases):
        print(f"  Progress: {i+1}/{len(wave2d_cases)} - {case.name}")
        results = run_wave2d_case(case, ["fdm", "fem", "spectral"])
        all_results.extend(results)
    
    print("\nRunning Heat3D cases...")
    heat3d_cases = [c for c in ALL_CASES if c.equation_type == "heat3d"]
    for i, case in enumerate(heat3d_cases):
        print(f"  Progress: {i+1}/{len(heat3d_cases)} - {case.name}")
        results = run_heat3d_case(case, ["fdm", "fvm", "fem"])
        all_results.extend(results)
    
    print("\nRunning Wave3D cases...")
    wave3d_cases = [c for c in ALL_CASES if c.equation_type == "wave3d"]
    for i, case in enumerate(wave3d_cases):
        print(f"  Progress: {i+1}/{len(wave3d_cases)} - {case.name}")
        results = run_wave3d_case(case, ["fdm", "fem", "spectral"])
        all_results.extend(results)
    
    print("\nRunning Poisson3D cases...")
    poisson3d_cases = [c for c in ALL_CASES if c.equation_type == "poisson3d"]
    for i, case in enumerate(poisson3d_cases):
        print(f"  Progress: {i+1}/{len(poisson3d_cases)} - {case.name}")
        results = run_poisson3d_case(case, ["fdm", "fem", "bem"])
        all_results.extend(results)
    
    elapsed = time.time() - start_time
    
    stats_by_eq: Dict[str, List[Dict]] = {}
    for eq_type in ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "wave3d", "poisson3d"]:
        eq_results = [r for r in all_results if r["equation_type"] == eq_type]
        
        if eq_type == "heat1d":
            algos = ["fdm", "fvm", "fem", "spectral"]
        elif eq_type == "wave1d":
            algos = ["fdm", "fem", "spectral"]
        elif eq_type in ["heat2d", "heat3d"]:
            algos = ["fdm", "fvm", "fem"]
        elif eq_type in ["wave2d", "wave3d"]:
            algos = ["fdm", "fem", "spectral"]
        else:
            algos = ["fdm", "fem", "bem"]
        
        stats_by_eq[eq_type] = [compute_algorithm_stats(eq_results, algo) for algo in algos]
        stats_by_eq[eq_type] = [s for s in stats_by_eq[eq_type] if s["num_cases"] > 0]
    
    payload = {
        "generated_at": time.time(),
        "total_elapsed_s": elapsed,
        "total_cases": len(ALL_CASES),
        "case_counts": case_counts,
        "stats_by_equation": stats_by_eq,
        "all_results": all_results,
    }
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "comprehensive_benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n[ok] Results saved to: {out_path}")
    
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    
    for eq_type, stats in stats_by_eq.items():
        print(f"\n{eq_type.upper()} ({case_counts[eq_type]} cases)")
        print(f"{'Algorithm':<12} {'Mean L2':<15} {'Std L2':<15} {'Median L2':<15} {'Cases':<8}")
        print("-" * 65)
        for stat in stats:
            print(f"{stat['algorithm']:<12} {stat['mean_l2_error']:<15.6e} {stat['std_l2_error']:<15.6e} {stat['median_l2_error']:<15.6e} {stat['num_cases']:<8}")
    
    print(f"\nTotal elapsed time: {elapsed:.2f}s")
    
    return payload


def main():
    parser = argparse.ArgumentParser(description="Comprehensive PDE benchmark")
    parser.add_argument("command", choices=["run", "count"])
    args = parser.parse_args()
    
    if args.command == "count":
        print(f"Total test cases: {len(ALL_CASES)}")
        for eq_type in ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "wave3d", "poisson3d"]:
            count = len([c for c in ALL_CASES if c.equation_type == eq_type])
            print(f"  {eq_type}: {count}")
    elif args.command == "run":
        run_comprehensive_benchmark()


if __name__ == "__main__":
    main()
