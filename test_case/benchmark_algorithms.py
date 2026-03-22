"""Benchmark selector strategies and numerical solvers for course demos.

Outputs:
- console summary
- JSON report under benchmark/

Run:
  python -m test_case.benchmark_algorithms
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np

from algorithm.selector import AlgorithmSelector, build_typical_case_dataset, evaluate_algorithm
from config.constants import BoundaryCondition
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    solve_heat3d_fdm,
    solve_heat3d_fem,
    solve_heat3d_fvm,
    Wave1DParams,
    get_solver,
    solve_heat2d_fdm,
    solve_heat2d_fem,
    solve_heat2d_fvm,
    solve_poisson3d_bem,
    solve_poisson3d_fdm,
    solve_poisson3d_fem,
    solve_wave2d_fdm,
    solve_wave2d_fem,
    solve_wave2d_spectral,
    solve_wave1d_fem,
    solve_wave1d,
    solve_wave3d_fdm,
    solve_wave3d_fem,
    solve_wave3d_spectral,
    solve_wave1d_spectral_v2,
)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _train_test_split(X: np.ndarray, y: np.ndarray, seed: int = 7, test_ratio: float = 0.25) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(X.shape[0])
    rng.shuffle(idx)
    split = int(X.shape[0] * (1.0 - test_ratio))
    train_idx = idx[:split]
    test_idx = idx[split:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


@dataclass
class SelectorBenchmark:
    strategy: str
    accuracy: float
    num_test_samples: int
    details: Dict[str, Any]


@dataclass
class SolverBenchmark:
    equation_type: str
    algorithm: str
    l2_error: float
    linf_error: float
    elapsed_s: float
    solver_status: str
    details: Dict[str, Any] | None = None


@dataclass
class SelectorVsBenchmark:
    case_name: str
    equation_type: str
    strategy: str
    selector_pick: str
    benchmark_best_by_error: str
    benchmark_best_by_time: str
    benchmark_best_balanced: str
    matches_best_balanced: bool
    details: Dict[str, Any]


def benchmark_selector_strategies(seed: int = 7) -> List[SelectorBenchmark]:
    X, y, label_keys = build_typical_case_dataset(seed=seed)
    X_train, X_test, y_train, y_test = _train_test_split(X, y, seed=seed)
    out: List[SelectorBenchmark] = []

    for strategy in ("static_rf", "mlp_nn", "gnn_selector"):
        selector = AlgorithmSelector(model_dir="model")
        info = selector.train_static(strategy=strategy, seed=seed)
        model = selector.static_model
        assert model is not None
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = float(np.mean(preds == y_test))
        out.append(
            SelectorBenchmark(
                strategy=strategy,
                accuracy=acc,
                num_test_samples=int(X_test.shape[0]),
                details={
                    "trained_samples": int(X_train.shape[0]),
                    "labels": label_keys,
                    "train_info": info,
                    **({"training_summary": info["training_summary"]} if "training_summary" in info else {}),
                },
            )
        )

    # Dynamic strategy: compare chosen action with proxy best algorithm on held-out states.
    selector = AlgorithmSelector(model_dir="model")
    train_info = selector.train_dynamic(episodes=200, seed=seed)
    correct = 0
    for sample, label in zip(X_test, y_test):
        physics = sample[:5]
        hardware = sample[5:10]
        domain = sample[10:]
        predicted = selector.act_dynamic(physics, hardware, domain)
        expected = label_keys[int(label)]
        if predicted == expected:
            correct += 1
    out.append(
        SelectorBenchmark(
            strategy="dynamic_rl",
            accuracy=float(correct / max(1, X_test.shape[0])),
            num_test_samples=int(X_test.shape[0]),
            details={"train_info": train_info, "note": "Accuracy is measured against proxy labels from the synthetic dataset."},
        )
    )
    return out


def benchmark_heat_solvers() -> List[SolverBenchmark]:
    params = Heat1DParams(k=1.0, L=1.0, nx=101, t_span=(0.0, 0.05), enforce_nonnegativity=False)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )

    def initial_fn(x: np.ndarray) -> np.ndarray:
        return np.sin(np.pi * x)

    x = np.linspace(0.0, params.L, params.nx)
    exact = np.exp(-params.k * (np.pi**2) * params.t_span[1]) * np.sin(np.pi * x)

    results: List[SolverBenchmark] = []
    for algorithm in ("fdm", "fvm", "fem", "spectral", "pinn"):
        solver = get_solver(algorithm)
        sol, info, _validation = solver.solve(params=params, bc=bc, initial=initial_fn)
        diff = sol - exact
        results.append(
            SolverBenchmark(
                equation_type="heat1d",
                algorithm=algorithm,
                l2_error=float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                linf_error=float(np.max(np.abs(diff))),
                elapsed_s=float(info.elapsed_s),
                solver_status=str(info.status),
                details=getattr(info, "details", None),
            )
        )
    return results


def benchmark_poisson1d_solvers() -> List[SolverBenchmark]:
    params = Heat1DParams(k=1.0, L=1.0, nx=101, t_span=(0.0, 0.0), enforce_nonnegativity=False)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )

    def initial_fn(x: np.ndarray) -> np.ndarray:
        return np.zeros_like(x, dtype=float)

    def source_fn(x: np.ndarray, t: float) -> np.ndarray:
        return (np.pi**2) * np.sin(np.pi * x)

    x = np.linspace(0.0, params.L, params.nx)
    exact = np.sin(np.pi * x)

    results: List[SolverBenchmark] = []
    for algorithm in ("fdm", "fem", "spectral", "bem"):
        solver = get_solver(algorithm)
        sol, info, _validation = solver.solve(params=params, bc=bc, initial=initial_fn, source=source_fn)
        diff = sol - exact
        results.append(
            SolverBenchmark(
                equation_type="poisson1d",
                algorithm=algorithm,
                l2_error=float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                linf_error=float(np.max(np.abs(diff))),
                elapsed_s=float(info.elapsed_s),
                solver_status=str(info.status),
            )
        )
    return results


def benchmark_poisson3d_solver() -> List[SolverBenchmark]:
    nx = 15
    ny = 15
    nz = 15
    Lx = 1.0
    Ly = 1.0
    Lz = 1.0
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = np.sin(np.pi * X / Lx) * np.sin(np.pi * Y / Ly) * np.sin(np.pi * Z / Lz)

    out: List[SolverBenchmark] = []
    for algorithm, solve_fn in (("fdm", solve_poisson3d_fdm), ("fem", solve_poisson3d_fem), ("bem", solve_poisson3d_bem)):
        sol3d, info = solve_fn(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
        diff = sol3d - exact
        out.append(
            SolverBenchmark(
                equation_type="poisson3d",
                algorithm=algorithm,
                l2_error=float(info.get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                linf_error=float(info.get("linf_error", np.max(np.abs(diff)))),
                elapsed_s=float(info["elapsed_s"]),
                solver_status=str(info["status"]),
                details={"boundary_residual": float(info.get("boundary_residual", 0.0))},
            )
        )
    return out


def benchmark_wave_solver() -> List[SolverBenchmark]:
    params = Wave1DParams(c=1.0, L=1.0, nx=101, t_span=(0.0, 0.5), nt=200)
    bc = BoundarySpec(
        bc_type=BoundaryCondition.DIRICHLET,
        left_value=lambda t: 0.0,
        right_value=lambda t: 0.0,
    )

    def initial_displacement(x: np.ndarray) -> np.ndarray:
        return np.sin(np.pi * x)

    def initial_velocity(x: np.ndarray) -> np.ndarray:
        return np.zeros_like(x)

    x = np.linspace(0.0, params.L, params.nx)
    exact = np.cos(params.c * np.pi * params.t_span[1]) * np.sin(np.pi * x)
    results: List[SolverBenchmark] = []
    for algorithm, solve_fn in (
        ("fdm", solve_wave1d),
        ("fem", solve_wave1d_fem),
        ("spectral", solve_wave1d_spectral_v2),
    ):
        sol, info, _validation = solve_fn(
            params=params,
            bc=bc,
            initial_displacement=initial_displacement,
            initial_velocity=initial_velocity,
        )
        diff = sol - exact
        results.append(
            SolverBenchmark(
                equation_type="wave1d",
                algorithm=algorithm,
                l2_error=float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                linf_error=float(np.max(np.abs(diff))),
                elapsed_s=float(info.elapsed_s),
                solver_status=str(info.status),
            )
        )
    return results


def benchmark_heat2d_solver() -> List[SolverBenchmark]:
    nx = 41
    ny = 41
    Lx = 1.0
    Ly = 1.0
    k = 1.0
    t1 = 0.05
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2)))
    nt = int(np.ceil(t1 / stability_limit))
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    X, Y = np.meshgrid(x, y, indexing="xy")
    exact = np.exp(-k * (np.pi**2) * ((1.0 / Lx**2) + (1.0 / Ly**2)) * t1) * np.sin(np.pi * X / Lx) * np.sin(np.pi * Y / Ly)

    out: List[SolverBenchmark] = []
    for algorithm, solve_fn in (("fdm", solve_heat2d_fdm), ("fvm", solve_heat2d_fvm), ("fem", solve_heat2d_fem)):
        sol2d, info_pack = solve_fn(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(0.0, t1), nt=nt)
        diff = sol2d - exact
        out.append(
            SolverBenchmark(
                equation_type="heat2d",
                algorithm=algorithm,
                l2_error=float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                linf_error=float(np.max(np.abs(diff))),
                elapsed_s=float(info_pack["solve_info"]["elapsed_s"]),
                solver_status=str(info_pack["solve_info"]["status"]),
            )
        )
    return out


def benchmark_heat3d_solver() -> List[SolverBenchmark]:
    nx = 11
    ny = 11
    nz = 11
    Lx = 1.0
    Ly = 1.0
    Lz = 1.0
    k = 1.0
    t1 = 0.02
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    dz = Lz / (nz - 1)
    stability_limit = 1.0 / (2.0 * k * ((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
    nt = int(np.ceil(t1 / stability_limit))
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    exact = (
        np.exp(-k * (np.pi**2) * ((1.0 / Lx**2) + (1.0 / Ly**2) + (1.0 / Lz**2)) * t1)
        * np.sin(np.pi * X / Lx)
        * np.sin(np.pi * Y / Ly)
        * np.sin(np.pi * Z / Lz)
    )

    out: List[SolverBenchmark] = []
    for algorithm, solve_fn in (("fdm", solve_heat3d_fdm), ("fvm", solve_heat3d_fvm), ("fem", solve_heat3d_fem)):
        sol3d, info_pack = solve_fn(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(0.0, t1), nt=nt)
        diff = sol3d - exact
        out.append(
            SolverBenchmark(
                equation_type="heat3d",
                algorithm=algorithm,
                l2_error=float(info_pack["solve_info"].get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                linf_error=float(info_pack["solve_info"].get("linf_error", np.max(np.abs(diff)))),
                elapsed_s=float(info_pack["solve_info"]["elapsed_s"]),
                solver_status=str(info_pack["solve_info"]["status"]),
                details={"boundary_residual": float(info_pack["solve_info"].get("boundary_residual", 0.0))},
            )
        )
    return out


def benchmark_wave3d_solver() -> List[SolverBenchmark]:
    nx = 15
    ny = 15
    nz = 15
    Lx = 1.0
    Ly = 1.0
    Lz = 1.0
    c = 1.0
    t1 = 0.15
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    dz = Lz / (nz - 1)
    stability_limit = 1.0 / (c * np.sqrt((1.0 / dx**2) + (1.0 / dy**2) + (1.0 / dz**2)))
    nt = int(np.ceil(t1 / stability_limit))
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    z = np.linspace(0.0, Lz, nz)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    omega = c * np.pi * np.sqrt((1.0 / Lx**2) + (1.0 / Ly**2) + (1.0 / Lz**2))
    exact = np.cos(omega * t1) * np.sin(np.pi * X / Lx) * np.sin(np.pi * Y / Ly) * np.sin(np.pi * Z / Lz)
    out: List[SolverBenchmark] = []
    for algorithm, solve_fn in (
        ("fdm", solve_wave3d_fdm),
        ("fem", solve_wave3d_fem),
        ("spectral", solve_wave3d_spectral),
    ):
        sol3d, info_pack = solve_fn(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(0.0, t1), nt=nt)
        diff = sol3d - exact
        out.append(
            SolverBenchmark(
                equation_type="wave3d",
                algorithm=algorithm,
                l2_error=float(info_pack["solve_info"].get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                linf_error=float(info_pack["solve_info"].get("linf_error", np.max(np.abs(diff)))),
                elapsed_s=float(info_pack["solve_info"]["elapsed_s"]),
                solver_status=str(info_pack["solve_info"]["status"]),
                details={"boundary_residual": float(info_pack["solve_info"].get("boundary_residual", 0.0))},
            )
        )
    return out


def benchmark_wave2d_solver() -> List[SolverBenchmark]:
    nx = 41
    ny = 41
    Lx = 1.0
    Ly = 1.0
    c = 1.0
    t1 = 0.2
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    stability_limit = 1.0 / (c * np.sqrt((1.0 / dx**2) + (1.0 / dy**2)))
    nt = int(np.ceil(t1 / stability_limit))
    x = np.linspace(0.0, Lx, nx)
    y = np.linspace(0.0, Ly, ny)
    X, Y = np.meshgrid(x, y, indexing="xy")
    omega = c * np.pi * np.sqrt((1.0 / Lx**2) + (1.0 / Ly**2))
    exact = np.cos(omega * t1) * np.sin(np.pi * X / Lx) * np.sin(np.pi * Y / Ly)

    out: List[SolverBenchmark] = []
    for algorithm, solve_fn in (("fdm", solve_wave2d_fdm), ("fem", solve_wave2d_fem), ("spectral", solve_wave2d_spectral)):
        sol2d, info_pack = solve_fn(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(0.0, t1), nt=nt)
        diff = sol2d - exact
        out.append(
            SolverBenchmark(
                equation_type="wave2d",
                algorithm=algorithm,
                l2_error=float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                linf_error=float(np.max(np.abs(diff))),
                elapsed_s=float(info_pack["solve_info"]["elapsed_s"]),
                solver_status=str(info_pack["solve_info"]["status"]),
            )
        )
    return out


def benchmark_solver_sweeps() -> Dict[str, Any]:
    """Run small resolution sweeps to make the benchmark less single-point dependent."""

    sweep_report: Dict[str, Any] = {"heat1d": {}, "poisson1d": {}, "poisson3d": {}, "wave1d": {}, "heat2d": {}, "heat3d": {}, "wave2d": {}, "wave3d": {}}

    for algorithm in ("fdm", "fvm", "fem", "spectral", "pinn"):
        heat_runs: List[Dict[str, Any]] = []
        for nx in (51, 101, 201):
            x = np.linspace(0.0, 1.0, nx)

            heat_params = Heat1DParams(k=1.0, L=1.0, nx=nx, t_span=(0.0, 0.05), enforce_nonnegativity=False)
            heat_bc = BoundarySpec(
                bc_type=BoundaryCondition.DIRICHLET,
                left_value=lambda t: 0.0,
                right_value=lambda t: 0.0,
            )
            heat_exact = np.exp(-(np.pi**2) * heat_params.t_span[1]) * np.sin(np.pi * x)
            heat_solver = get_solver(algorithm)
            heat_sol, heat_info, _ = heat_solver.solve(
                params=heat_params,
                bc=heat_bc,
                initial=lambda xx: np.sin(np.pi * xx),
            )
            heat_diff = heat_sol - heat_exact
            heat_runs.append(
                {
                    "nx": nx,
                    "l2_error": float(np.linalg.norm(heat_diff) / np.sqrt(heat_diff.size)),
                    "elapsed_s": float(heat_info.elapsed_s),
                }
            )

        sweep_report["heat1d"][algorithm] = {
            "runs": heat_runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in heat_runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in heat_runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in heat_runs])),
        }

    for algorithm in ("fdm", "fem", "spectral", "bem"):
        poisson_runs: List[Dict[str, Any]] = []
        for nx in (51, 101, 201):
            x = np.linspace(0.0, 1.0, nx)
            heat_bc = BoundarySpec(
                bc_type=BoundaryCondition.DIRICHLET,
                left_value=lambda t: 0.0,
                right_value=lambda t: 0.0,
            )
            poisson_params = Heat1DParams(k=1.0, L=1.0, nx=nx, t_span=(0.0, 0.0), enforce_nonnegativity=False)
            poisson_exact = np.sin(np.pi * x)
            poisson_solver = get_solver(algorithm)
            poisson_sol, poisson_info, _ = poisson_solver.solve(
                params=poisson_params,
                bc=heat_bc,
                initial=lambda xx: np.zeros_like(xx, dtype=float),
                source=lambda xx, t: (np.pi**2) * np.sin(np.pi * xx),
            )
            poisson_diff = poisson_sol - poisson_exact
            poisson_runs.append(
                {
                    "nx": nx,
                    "l2_error": float(np.linalg.norm(poisson_diff) / np.sqrt(poisson_diff.size)),
                    "elapsed_s": float(poisson_info.elapsed_s),
                }
            )

        sweep_report["poisson1d"][algorithm] = {
            "runs": poisson_runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in poisson_runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in poisson_runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in poisson_runs])),
        }

    for algorithm, solve_fn in (
        ("fdm", solve_wave1d),
        ("fem", solve_wave1d_fem),
        ("spectral", solve_wave1d_spectral_v2),
    ):
        wave_runs: List[Dict[str, Any]] = []
        for nx in (51, 101, 201):
            x = np.linspace(0.0, 1.0, nx)
            nt = nx - 1
            params = Wave1DParams(c=1.0, L=1.0, nx=nx, t_span=(0.0, 0.5), nt=nt)
            bc = BoundarySpec(
                bc_type=BoundaryCondition.DIRICHLET,
                left_value=lambda t: 0.0,
                right_value=lambda t: 0.0,
            )
            exact = np.cos(np.pi * params.t_span[1]) * np.sin(np.pi * x)
            sol, info, _ = solve_fn(
                params=params,
                bc=bc,
                initial_displacement=lambda xx: np.sin(np.pi * xx),
                initial_velocity=lambda xx: np.zeros_like(xx, dtype=float),
            )
            diff = sol - exact
            wave_runs.append(
                {
                    "nx": nx,
                    "nt": nt,
                    "l2_error": float(np.linalg.norm(diff) / np.sqrt(diff.size)),
                    "elapsed_s": float(info.elapsed_s),
                }
            )
        sweep_report["wave1d"][algorithm] = {
            "runs": wave_runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in wave_runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in wave_runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in wave_runs])),
        }

    heat2d_runs_by_algorithm: Dict[str, List[Dict[str, Any]]] = {"fdm": [], "fvm": [], "fem": []}
    for n in (21, 31, 41):
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        X, Y = np.meshgrid(x, y, indexing="xy")
        t1 = 0.05
        exact = np.exp(-2.0 * (np.pi**2) * t1) * np.sin(np.pi * X) * np.sin(np.pi * Y)
        dx = 1.0 / (n - 1)
        dy = 1.0 / (n - 1)
        stability_limit = 1.0 / (2.0 * ((1.0 / dx**2) + (1.0 / dy**2)))
        nt = int(np.ceil(t1 / stability_limit))
        for algorithm, solve_fn in (("fdm", solve_heat2d_fdm), ("fvm", solve_heat2d_fvm), ("fem", solve_heat2d_fem)):
            sol2d, info_pack = solve_fn(nx=n, ny=n, Lx=1.0, Ly=1.0, k=1.0, t_span=(0.0, t1), nt=nt)
            diff = sol2d - exact
            heat2d_runs_by_algorithm[algorithm].append(
                {
                    "nx": n,
                    "ny": n,
                    "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                    "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                }
            )
    for algorithm, runs in heat2d_runs_by_algorithm.items():
        sweep_report["heat2d"][algorithm] = {
            "runs": runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in runs])),
        }

    heat3d_runs_by_algorithm: Dict[str, List[Dict[str, Any]]] = {"fdm": [], "fvm": [], "fem": []}
    for n in (7, 9, 11):
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        z = np.linspace(0.0, 1.0, n)
        Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
        t1 = 0.02
        exact = np.exp(-3.0 * (np.pi**2) * t1) * np.sin(np.pi * X) * np.sin(np.pi * Y) * np.sin(np.pi * Z)
        dx = 1.0 / (n - 1)
        stability_limit = 1.0 / (2.0 * ((3.0) / dx**2))
        nt = int(np.ceil(t1 / stability_limit))
        for algorithm, solve_fn in (("fdm", solve_heat3d_fdm), ("fvm", solve_heat3d_fvm), ("fem", solve_heat3d_fem)):
            sol3d, info_pack = solve_fn(nx=n, ny=n, nz=n, Lx=1.0, Ly=1.0, Lz=1.0, k=1.0, t_span=(0.0, t1), nt=nt)
            diff = sol3d - exact
            heat3d_runs_by_algorithm[algorithm].append(
                {
                    "nx": n,
                    "ny": n,
                    "nz": n,
                    "l2_error": float(info_pack["solve_info"].get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                    "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                }
            )
    for algorithm, runs in heat3d_runs_by_algorithm.items():
        sweep_report["heat3d"][algorithm] = {
            "runs": runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in runs])),
        }

    wave2d_runs_by_algorithm: Dict[str, List[Dict[str, Any]]] = {"fdm": [], "fem": [], "spectral": []}
    for n in (21, 31, 41):
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        X, Y = np.meshgrid(x, y, indexing="xy")
        dx = 1.0 / (n - 1)
        dy = 1.0 / (n - 1)
        t1 = 0.2
        stability_limit = 1.0 / np.sqrt((1.0 / dx**2) + (1.0 / dy**2))
        nt = int(np.ceil(t1 / stability_limit))
        omega = np.pi * np.sqrt(2.0)
        exact = np.cos(omega * t1) * np.sin(np.pi * X) * np.sin(np.pi * Y)
        for algorithm, solve_fn in (("fdm", solve_wave2d_fdm), ("fem", solve_wave2d_fem), ("spectral", solve_wave2d_spectral)):
            sol2d, info_pack = solve_fn(nx=n, ny=n, Lx=1.0, Ly=1.0, c=1.0, t_span=(0.0, t1), nt=nt)
            diff = sol2d - exact
            wave2d_runs_by_algorithm[algorithm].append(
                {
                    "nx": n,
                    "nt": nt,
                    "l2_error": float(np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size)),
                    "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                }
            )
    for algorithm, runs in wave2d_runs_by_algorithm.items():
        sweep_report["wave2d"][algorithm] = {
            "runs": runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in runs])),
        }

    wave3d_runs_by_algorithm: Dict[str, List[Dict[str, Any]]] = {"fdm": [], "fem": [], "spectral": []}
    for n in (9, 11, 15):
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        z = np.linspace(0.0, 1.0, n)
        Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
        t1 = 0.15
        dx = 1.0 / (n - 1)
        stability_limit = 1.0 / np.sqrt((3.0) / dx**2)
        nt = int(np.ceil(t1 / stability_limit))
        omega = np.pi * np.sqrt(3.0)
        exact = np.cos(omega * t1) * np.sin(np.pi * X) * np.sin(np.pi * Y) * np.sin(np.pi * Z)
        for algorithm, solve_fn in (
            ("fdm", solve_wave3d_fdm),
            ("fem", solve_wave3d_fem),
            ("spectral", solve_wave3d_spectral),
        ):
            sol3d, info_pack = solve_fn(nx=n, ny=n, nz=n, Lx=1.0, Ly=1.0, Lz=1.0, c=1.0, t_span=(0.0, t1), nt=nt)
            diff = sol3d - exact
            wave3d_runs_by_algorithm[algorithm].append(
                {
                    "nx": n,
                    "ny": n,
                    "nz": n,
                    "nt": nt,
                    "l2_error": float(info_pack["solve_info"].get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                    "elapsed_s": float(info_pack["solve_info"]["elapsed_s"]),
                }
            )
    for algorithm, runs in wave3d_runs_by_algorithm.items():
        sweep_report["wave3d"][algorithm] = {
            "runs": runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in runs])),
        }

    poisson3d_runs_by_algorithm: Dict[str, List[Dict[str, Any]]] = {"fdm": [], "fem": [], "bem": []}
    for n in (11, 15):
        x = np.linspace(0.0, 1.0, n)
        y = np.linspace(0.0, 1.0, n)
        z = np.linspace(0.0, 1.0, n)
        Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
        exact = np.sin(np.pi * X) * np.sin(np.pi * Y) * np.sin(np.pi * Z)
        for algorithm, solve_fn in (("fdm", solve_poisson3d_fdm), ("fem", solve_poisson3d_fem), ("bem", solve_poisson3d_bem)):
            sol3d, info = solve_fn(nx=n, ny=n, nz=n, Lx=1.0, Ly=1.0, Lz=1.0)
            diff = sol3d - exact
            poisson3d_runs_by_algorithm[algorithm].append(
                {
                    "nx": n,
                    "ny": n,
                    "nz": n,
                    "l2_error": float(info.get("l2_error", np.linalg.norm(diff.reshape(-1)) / np.sqrt(diff.size))),
                    "elapsed_s": float(info["elapsed_s"]),
                }
            )
    for algorithm, runs in poisson3d_runs_by_algorithm.items():
        sweep_report["poisson3d"][algorithm] = {
            "runs": runs,
            "mean_l2_error": float(np.mean([item["l2_error"] for item in runs])),
            "max_l2_error": float(np.max([item["l2_error"] for item in runs])),
            "mean_elapsed_s": float(np.mean([item["elapsed_s"] for item in runs])),
        }

    return sweep_report


def benchmark_selector_recommendations() -> Dict[str, Any]:
    """Show what each strategy recommends on a few representative scenes."""
    scenes = {
        "heat1d_realtime": {
            "physics": np.array([0.0, 0.0, 1.0, 0.0, 0.3], dtype=float),
            "hardware": np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float),
            "domain": np.array([0.5, 1.0, 0.5], dtype=float),
        },
        "wave1d_balanced": {
            "physics": np.array([0.0, 0.0, 1.0, 0.0, 0.3], dtype=float),
            "hardware": np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float),
            "domain": np.array([0.5, 0.5, 0.7], dtype=float),
        },
        "poisson2d_complex": {
            "physics": np.array([0.5, 1.0, 0.0, 0.0, 0.7], dtype=float),
            "hardware": np.array([0.7, 0.8, 0.7, 0.6, 1.0], dtype=float),
            "domain": np.array([0.8, 0.5, 0.7], dtype=float),
        },
    }

    selector = AlgorithmSelector(model_dir="model")
    selector._load_or_train_static("static_rf")
    selector._load_or_train_static("mlp_nn")
    selector._load_or_train_static("gnn_selector")
    if selector.rl_agent is None:
        selector.train_dynamic(episodes=200)

    report: Dict[str, Any] = {}
    for scene_name, payload in scenes.items():
        scene_report: Dict[str, Any] = {}
        for strategy in ("static_rf", "mlp_nn", "gnn_selector", "dynamic_rl"):
            selected = selector.select(
                physics=payload["physics"],
                hardware=payload["hardware"],
                domain=payload["domain"],
                strategy=strategy,
            )
            scene_report[strategy] = {
                "algorithm_key": selected["algorithm_key"],
                "score_total": float(selected["score"]["total"]),
                "reason": selected["reason"],
            }
        report[scene_name] = scene_report
    return report


def benchmark_selector_vs_solver_best(solver_rows: List[SolverBenchmark]) -> List[SelectorVsBenchmark]:
    """Compare selector picks against empirically best solver choices on aligned demo cases.

    Since the selector currently chooses among fdm/fem/spectral only, comparisons are restricted
    to equations where at least two of those candidates exist in solver benchmarks.
    """
    cases = [
        {
            "case_name": "heat1d_accuracy_oriented",
            "equation_type": "heat1d",
            "physics": np.array([0.0, 0.0, 0.0, 0.1, 0.4], dtype=float),
            "hardware": np.array([0.3, 0.4, 0.4, 0.3, 0.6], dtype=float),
            "domain": np.array([1.0, 0.2, 0.8], dtype=float),
        },
        {
            "case_name": "wave1d_balanced",
            "equation_type": "wave1d",
            "physics": np.array([0.0, 0.0, 1.0, 0.0, 0.3], dtype=float),
            "hardware": np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float),
            "domain": np.array([0.5, 0.5, 0.7], dtype=float),
        },
        {
            "case_name": "heat2d_standard",
            "equation_type": "heat2d",
            "physics": np.array([0.5, 0.0, 0.2, 0.2, 0.5], dtype=float),
            "hardware": np.array([0.2, 0.3, 0.2, 0.1, 0.5], dtype=float),
            "domain": np.array([0.7, 0.6, 0.6], dtype=float),
        },
        {
            "case_name": "wave2d_accuracy_oriented",
            "equation_type": "wave2d",
            "physics": np.array([0.5, 0.0, 0.8, 0.2, 0.5], dtype=float),
            "hardware": np.array([0.4, 0.5, 0.4, 0.2, 0.8], dtype=float),
            "domain": np.array([1.0, 0.3, 0.7], dtype=float),
        },
        {
            "case_name": "heat3d_balanced",
            "equation_type": "heat3d",
            "physics": np.array([1.0, 0.0, 0.3, 0.3, 0.6], dtype=float),
            "hardware": np.array([0.5, 0.6, 0.5, 0.4, 0.8], dtype=float),
            "domain": np.array([0.7, 0.6, 0.6], dtype=float),
        },
        {
            "case_name": "wave3d_accuracy_oriented",
            "equation_type": "wave3d",
            "physics": np.array([1.0, 0.0, 0.8, 0.2, 0.6], dtype=float),
            "hardware": np.array([0.6, 0.7, 0.6, 0.5, 0.9], dtype=float),
            "domain": np.array([1.0, 0.4, 0.7], dtype=float),
        },
    ]

    selector = AlgorithmSelector(model_dir="model")
    selector._load_or_train_static("static_rf")
    selector._load_or_train_static("mlp_nn")
    selector._load_or_train_static("gnn_selector")
    if selector.rl_agent is None:
        selector.train_dynamic(episodes=200)

    out: List[SelectorVsBenchmark] = []
    strategies = ("static_rf", "mlp_nn", "gnn_selector", "dynamic_rl")
    candidate_keys = {"fdm", "fem", "spectral"}

    for case in cases:
        rows = [
            row for row in solver_rows
            if row.equation_type == case["equation_type"] and row.algorithm in candidate_keys
        ]
        if not rows:
            continue

        best_by_error = min(rows, key=lambda r: r.l2_error)
        best_by_time = min(rows, key=lambda r: r.elapsed_s)
        min_err = min(r.l2_error for r in rows)
        max_err = max(r.l2_error for r in rows)
        min_t = min(r.elapsed_s for r in rows)
        max_t = max(r.elapsed_s for r in rows)

        def balanced_score(row: SolverBenchmark) -> float:
            err = 0.0 if max_err == min_err else (row.l2_error - min_err) / (max_err - min_err)
            tim = 0.0 if max_t == min_t else (row.elapsed_s - min_t) / (max_t - min_t)
            return 0.65 * err + 0.35 * tim

        best_balanced = min(rows, key=balanced_score)
        ranking = sorted(
            [{"algorithm": row.algorithm, "balanced_score": float(balanced_score(row))} for row in rows],
            key=lambda item: item["balanced_score"],
        )

        for strategy in strategies:
            selected = selector.select(
                physics=case["physics"],
                hardware=case["hardware"],
                domain=case["domain"],
                strategy=strategy,  # type: ignore[arg-type]
            )
            pick = str(selected["algorithm_key"])
            out.append(
                SelectorVsBenchmark(
                    case_name=str(case["case_name"]),
                    equation_type=str(case["equation_type"]),
                    strategy=strategy,
                    selector_pick=pick,
                    benchmark_best_by_error=best_by_error.algorithm,
                    benchmark_best_by_time=best_by_time.algorithm,
                    benchmark_best_balanced=best_balanced.algorithm,
                    matches_best_balanced=pick == best_balanced.algorithm,
                    details={
                        "benchmark_ranking": ranking,
                        "selector_reason": str(selected["reason"]),
                    },
                )
            )
    return out


def build_report() -> Dict[str, Any]:
    selector_benchmarks = benchmark_selector_strategies()
    solver_benchmarks = (
        benchmark_heat_solvers()
        + benchmark_poisson1d_solvers()
        + benchmark_poisson3d_solver()
        + benchmark_wave_solver()
        + benchmark_heat2d_solver()
        + benchmark_heat3d_solver()
        + benchmark_wave2d_solver()
        + benchmark_wave3d_solver()
    )
    recommendation_examples = benchmark_selector_recommendations()
    selector_vs_benchmark = benchmark_selector_vs_solver_best(solver_benchmarks)

    return {
        "generated_at": time.time(),
        "selector_accuracy": [asdict(item) for item in selector_benchmarks],
        "solver_accuracy": [asdict(item) for item in solver_benchmarks],
        "solver_sweeps": benchmark_solver_sweeps(),
        "recommendation_examples": recommendation_examples,
        "selector_vs_benchmark": [asdict(item) for item in selector_vs_benchmark],
        "notes": [
            "Selector accuracy is measured on the project's synthetic representative dataset.",
            "Solver accuracy is measured against simple analytical solutions for heat1d, poisson1d, poisson3d, wave1d, heat2d, heat3d, wave2d and wave3d.",
            "heat1d now includes an FVM baseline for conservative discretization comparison.",
            "heat1d now also includes a minimal PINN prototype under zero-Dirichlet, source-free conditions.",
            "Resolution sweeps are included to reduce dependence on a single benchmark point.",
            "wave1d currently benchmarks FDM/FEM/spectral under zero Dirichlet boundaries.",
            "heat2d currently benchmarks zero-Dirichlet FDM/FVM/FEM baselines on square domains.",
            "heat3d currently benchmarks zero-Dirichlet FDM/FVM/FEM manufactured-solution baselines on cubic domains.",
            "wave2d currently benchmarks zero-Dirichlet FDM/FEM/spectral baselines on square domains.",
            "wave3d currently benchmarks zero-Dirichlet FDM/FEM/spectral manufactured-solution baselines on cubic domains.",
            "poisson3d currently benchmarks zero-Dirichlet FDM/FEM/BEM manufactured-solution baselines on cubic domains.",
        ],
    }


def save_report(report: Dict[str, Any], output_dir: str = "benchmark") -> str:
    _ensure_dir(output_dir)
    path = os.path.join(output_dir, f"benchmark_{int(report['generated_at'])}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def print_summary(report: Dict[str, Any], path: str) -> None:
    print("=== Selector Accuracy ===")
    for item in report["selector_accuracy"]:
        print(f"{item['strategy']}: accuracy={item['accuracy']:.3f} on {item['num_test_samples']} samples")
        summary = item.get("details", {}).get("training_summary")
        if summary:
            print(
                "  "
                f"epochs_run={summary['epochs_run']}, best_epoch={summary['best_epoch']}, "
                f"best_val_loss={summary['best_val_loss']:.6f}, early_stopped={summary['early_stopped']}"
            )

    print("\n=== Solver Accuracy ===")
    for item in report["solver_accuracy"]:
        print(
            f"{item['equation_type']} / {item['algorithm']}: "
            f"L2={item['l2_error']:.6e}, Linf={item['linf_error']:.6e}, elapsed={item['elapsed_s']:.4f}s"
        )

    if "solver_sweeps" in report:
        print("\n=== Sweep Summary ===")
        for equation_type, algorithms in report["solver_sweeps"].items():
            for algorithm, item in algorithms.items():
                print(
                    f"{equation_type} / {algorithm}: "
                    f"mean_L2={item['mean_l2_error']:.6e}, "
                    f"max_L2={item['max_l2_error']:.6e}, "
                    f"mean_elapsed={item['mean_elapsed_s']:.4f}s"
                )

    if "selector_vs_benchmark" in report:
        print("\n=== Selector vs Benchmark ===")
        for item in report["selector_vs_benchmark"]:
            print(
                f"{item['case_name']} / {item['strategy']}: "
                f"pick={item['selector_pick']}, balanced_best={item['benchmark_best_balanced']}, "
                f"match={item['matches_best_balanced']}"
            )

    print(f"\nSaved benchmark report to: {path}")


def main() -> Dict[str, Any]:
    report = build_report()
    path = save_report(report)
    print_summary(report, path)
    return report


if __name__ == "__main__":
    main()
