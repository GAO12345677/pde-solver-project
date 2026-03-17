"""Global constants and tunable parameters for the framework.

This module is intentionally **configuration-only**:
- It defines enumerations / constant sets for features, requirements, and hardware.
- It defines algorithm candidates and their applicable feature constraints.
- It defines ML model hyperparameters (RF / XGBoost / RL agent) as dictionaries for easy overrides.

Design notes (paper-aligned, high-level):
- The "adaptive selection" pipeline typically consumes three groups of signals:
  (1) PDE/physics equation characteristics
  (2) hardware/compute characteristics
  (3) domain requirements (accuracy/latency/resource budget)
- Downstream modules should import from here and must NOT hardcode these values.

Compatibility:
- Python 3.9+ (Windows 10/11)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


# =========================
# Physics / PDE feature constants
# =========================


class Dimension(int, Enum):
    """Spatial dimension of the physical equation/problem."""

    D1 = 1
    D2 = 2
    D3 = 3


class Linearity(int, Enum):
    """Linearity type of the governing equation."""

    LINEAR = 0
    NONLINEAR = 1


class Stationarity(int, Enum):
    """Time-dependence of the equation."""

    STEADY = 0
    UNSTEADY = 1


class BoundaryCondition(str, Enum):
    """Boundary condition category.

    - DIRICHLET: prescribe value
    - NEUMANN: prescribe flux/gradient
    - MIXED: combination/Robin-like
    """

    DIRICHLET = "dirichlet"
    NEUMANN = "neumann"
    MIXED = "mixed"


# =========================
# Hardware feature constants
# =========================


class HardwareType(str, Enum):
    """Compute hardware category used by the solver runtime."""

    CPU = "cpu"
    GPU = "gpu"
    HETEROGENEOUS = "heterogeneous"  # CPU+GPU / multi-device


class GpuModel(str, Enum):
    """GPU model categories we explicitly recognize in heuristic rules.

    Note:
    - Real detection returns full names (e.g., "NVIDIA GeForce RTX 4060 Laptop GPU").
    - Downstream matching can map detected name -> one of these enums.
    """

    RTX4060 = "rtx4060"
    RTX3090 = "rtx3090"


# Thresholds used for coarse-grained decision rules.
# These are intentionally "soft" parameters; tune per environment.
#
# - COMPUTE_TFLOPS_THRESHOLD: used to classify "low/medium/high" compute capability.
# - VRAM_GB_THRESHOLD: used to classify available GPU memory.
COMPUTE_TFLOPS_THRESHOLD: float = 20.0
VRAM_GB_THRESHOLD: float = 8.0


# =========================
# Domain requirement constants
# =========================


class RequirementLevel(str, Enum):
    """Generic level enum for accuracy / realtime / etc."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Resource budget threshold (example defaults; tune per project).
# This can be interpreted by downstream modules as:
# - max CPU utilization percentage, max memory (GB), or max time (s) depending on implementation.
RESOURCE_CONSUMPTION_THRESHOLD: float = 0.75


# =========================
# Algorithm candidate set
# =========================


@dataclass(frozen=True)
class AlgorithmApplicability:
    """Feature constraints describing where an algorithm is applicable.

    Use `None` to indicate "don't care" (wildcard).
    """

    dimensions: Optional[Tuple[Dimension, ...]] = None
    linearity: Optional[Linearity] = None
    stationarity: Optional[Stationarity] = None
    boundary_conditions: Optional[Tuple[BoundaryCondition, ...]] = None


@dataclass(frozen=True)
class AlgorithmCandidate:
    """Algorithm candidate metadata used by the selection framework."""

    key: str
    name: str
    description: str
    applicability: AlgorithmApplicability


ALGORITHM_CANDIDATES: List[AlgorithmCandidate] = [
    AlgorithmCandidate(
        key="fdm",
        name="有限差分法 (FDM)",
        description=(
            "适用于结构化网格/规则区域，离散实现简单，常用于低维问题。"
            "对复杂几何/非结构网格不如 FEM 灵活。"
        ),
        applicability=AlgorithmApplicability(
            dimensions=(Dimension.D1,),
            linearity=Linearity.LINEAR,
            stationarity=Stationarity.STEADY,
            boundary_conditions=(BoundaryCondition.DIRICHLET, BoundaryCondition.NEUMANN, BoundaryCondition.MIXED),
        ),
    ),
    AlgorithmCandidate(
        key="fem",
        name="有限元法 (FEM)",
        description=(
            "适用于复杂几何与非结构网格，工程应用广。"
            "组装与求解复杂度较高，但通用性强。"
        ),
        applicability=AlgorithmApplicability(
            dimensions=(Dimension.D1, Dimension.D2, Dimension.D3),
            linearity=None,  # linear & nonlinear
            stationarity=None,  # steady & unsteady
            boundary_conditions=(BoundaryCondition.DIRICHLET, BoundaryCondition.NEUMANN, BoundaryCondition.MIXED),
        ),
    ),
    AlgorithmCandidate(
        key="spectral",
        name="谱方法 (Spectral)",
        description=(
            "在解足够光滑、区域规则时可获得极高精度（指数收敛），"
            "常用于高精度需求或验证基准。对复杂几何不友好。"
        ),
        applicability=AlgorithmApplicability(
            dimensions=(Dimension.D1, Dimension.D2),
            linearity=Linearity.LINEAR,
            stationarity=Stationarity.STEADY,
            boundary_conditions=(BoundaryCondition.DIRICHLET, BoundaryCondition.MIXED),
        ),
    ),
]


# A quick index by key, for API consumption.
ALGORITHM_CANDIDATES_BY_KEY: Dict[str, AlgorithmCandidate] = {a.key: a for a in ALGORITHM_CANDIDATES}


# =========================
# Machine learning model parameters (tunable)
# =========================

# RandomForest training parameters (scikit-learn)
# These parameters are meant to be overwritten by user configuration later.
RF_TRAIN_PARAMS: Dict[str, object] = {
    # Number of trees in the forest.
    "n_estimators": 300,
    # Tree depth; None lets trees expand until leaves are pure or min_samples_* constraints reached.
    "max_depth": None,
    # Minimum samples to split a node.
    "min_samples_split": 2,
    # Minimum samples in a leaf node.
    "min_samples_leaf": 1,
    # Use all CPU cores by default.
    "n_jobs": -1,
    # Ensure deterministic behavior.
    "random_state": 42,
}

# XGBoost training parameters (xgboost)
XGB_TRAIN_PARAMS: Dict[str, object] = {
    # Objective is chosen for multi-class selection tasks; adjust as needed.
    "objective": "multi:softprob",
    # Booster / regularization settings.
    "n_estimators": 600,
    "learning_rate": 0.05,
    "max_depth": 8,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "reg_lambda": 1.0,
    # Training behavior.
    "random_state": 42,
    "tree_method": "hist",  # CPU-friendly default; switch to "gpu_hist" when GPU is available.
    "eval_metric": "mlogloss",
}

# Reinforcement Learning (RL) agent hyperparameters (gym-based environment)
# This dictionary is framework-agnostic; your RL implementation can map these to its algorithm.
RL_AGENT_HYPERPARAMS: Dict[str, object] = {
    # Discount factor
    "gamma": 0.99,
    # Learning rate for policy/value updates
    "learning_rate": 3e-4,
    # Exploration parameters (for epsilon-greedy style agents)
    "epsilon_start": 1.0,
    "epsilon_end": 0.05,
    "epsilon_decay_steps": 50_000,
    # Experience replay
    "replay_buffer_size": 200_000,
    "batch_size": 256,
    # Target network update frequency (if applicable)
    "target_update_interval": 1_000,
    # Training schedule
    "train_start_steps": 5_000,
    "train_freq": 4,
}

