"""Shared feature engineering utilities for selector training/evaluation."""

from __future__ import annotations

import math
from typing import Any, Dict

import numpy as np

EQUATION_KEYS = ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "wave3d", "poisson3d"]
BOUNDARY_KEYS = ["dirichlet", "periodic", "mixed", "mixed_dirichlet_neumann", "mixed_3d", "robin", "inlet_outlet", "inlet_outlet_3d"]


def _one_hot(value: str, keys: list[str]) -> np.ndarray:
    arr = np.zeros((len(keys),), dtype=np.float32)
    if value in keys:
        arr[keys.index(value)] = 1.0
    return arr


def build_selector_features(
    *,
    physics: np.ndarray,
    hardware: np.ndarray,
    domain: np.ndarray,
    equation_type: str,
    dimension: int,
    params: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
) -> np.ndarray:
    metadata = metadata or {}
    physics_arr = np.asarray(physics, dtype=np.float32).reshape(-1)
    hardware_arr = np.asarray(hardware, dtype=np.float32).reshape(-1)
    domain_arr = np.asarray(domain, dtype=np.float32).reshape(-1)

    equation_one_hot = _one_hot(str(equation_type), EQUATION_KEYS)
    dimension_one_hot = _one_hot(f"{int(dimension)}d", ["1d", "2d", "3d"])

    boundary_type = str(metadata.get("boundary_type", "dirichlet"))
    boundary_one_hot = _one_hot(boundary_type, BOUNDARY_KEYS)
    is_periodic = np.array([1.0 if boundary_type == "periodic" else 0.0], dtype=np.float32)

    nx = float(params.get("nx", 0.0) or 0.0)
    ny = float(params.get("ny", nx) or nx)
    nz = float(params.get("nz", nx if int(dimension) == 3 else 1.0) or 1.0)
    grid_points = max(nx, 1.0) * max(ny, 1.0) * max(nz, 1.0)
    grid_features = np.array(
        [
            min(nx / 401.0, 1.0),
            min(ny / 401.0, 1.0),
            min(nz / 401.0, 1.0),
            min(math.log10(max(grid_points, 1.0)) / 8.0, 1.0),
        ],
        dtype=np.float32,
    )

    frequency_indicator = float(params.get("mode", 0.0) or 0.0)
    mx = float(params.get("mx", 0.0) or 0.0)
    my = float(params.get("my", 0.0) or 0.0)
    modes = params.get("modes")
    if isinstance(modes, list) and modes:
        frequency_indicator = max(float(v) for v in modes)
    if mx or my:
        frequency_indicator = math.sqrt(max(mx, 0.0) ** 2 + max(my, 0.0) ** 2)
    if "scale_ratio" in params:
        frequency_indicator = max(frequency_indicator, float(params["scale_ratio"]) / 5.0)

    t_final = float(params.get("t_final", 0.0) or 0.0)
    coeff_scale = 1.0
    if "k" in params:
        coeff_scale = float(params["k"])
    elif "c" in params:
        coeff_scale = float(params["c"])
    temporal_behavior = str(metadata.get("solution_characteristics", {}).get("temporal_behavior", ""))
    is_steady = 1.0 if temporal_behavior in {"steady", "steady_state"} or t_final <= 0.0 else 0.0
    flux_like = 1.0 if boundary_type in {"inlet_outlet", "inlet_outlet_3d"} or metadata.get("expected_algorithm_bias") == "fvm_friendly" else 0.0

    engineered = np.array(
        [
            min(frequency_indicator / 10.0, 1.0),
            min(abs(t_final) / 2.0, 1.0),
            min(coeff_scale / 8.0, 1.0),
            is_steady,
            flux_like,
        ],
        dtype=np.float32,
    )

    return np.concatenate(
        [
            physics_arr,
            hardware_arr,
            domain_arr,
            equation_one_hot,
            dimension_one_hot,
            boundary_one_hot,
            is_periodic,
            grid_features,
            engineered,
        ],
        axis=0,
    ).astype(np.float32)
