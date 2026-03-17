"""FastAPI entrypoint for the adaptive solver-selection framework.

Run (Windows PowerShell):
    python -m uvicorn main:app --reload

Then open:
    Swagger UI: http://127.0.0.1:8000/docs
    Redoc:      http://127.0.0.1:8000/redoc

Debugging in Cursor:
- You can set a breakpoint on the line marked with `# DEBUG_BREAKPOINT`
  and run uvicorn to hit it when calling the endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import numpy as np

from config.constants import (
    ALGORITHM_CANDIDATES,
    BoundaryCondition,
    Dimension,
    Linearity,
    RequirementLevel,
    Stationarity,
)
from services.hardware import hardware_info_dict
from algorithm.selector import AlgorithmSelector, AlgorithmSelectionError


app = FastAPI(
    title="ML-Driven PDE Solver Selection Framework",
    version="0.1.0",
    description=(
        "基于《机器学习驱动的物理方程组求解算法自适应选择框架研究》的理论设计，"
        "提供物理方程特征/硬件特征/领域需求的接口化输入，以及候选算法集合的可视化输出。"
    ),
)

# CORS for web-based testing and integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PhysicsFeaturesIn(BaseModel):
    """PDE/physics features fed into the selection layer."""

    dimension: Dimension = Field(..., description="空间维度：1/2/3")
    linearity: Linearity = Field(..., description="线性类型：0=线性/1=非线性")
    stationarity: Stationarity = Field(..., description="定常类型：0=定常/1=非定常")
    boundary_condition: BoundaryCondition = Field(..., description="边界条件类型：狄利克雷/诺伊曼/混合")


class DomainRequirementsIn(BaseModel):
    """Domain constraints affecting the final solver choice."""

    accuracy: RequirementLevel = Field(..., description="精度要求：高/中/低")
    realtime: RequirementLevel = Field(..., description="实时性要求：高/中/低")
    resource_budget: Optional[float] = Field(
        None, description="资源消耗预算(0-1，越小越严格)。为空则使用默认阈值。"
    )


class FeatureVectorsIn(BaseModel):
    """Normalized feature vectors for selection layer.

    - physics: length 5
    - hardware: length 5
    - domain: length 3
    """

    physics: List[float] = Field(..., description="物理特征向量(归一化到[0,1])，长度=5")
    hardware: List[float] = Field(..., description="硬件特征向量(归一化到[0,1])，长度=5")
    domain: List[float] = Field(..., description="领域特征向量(归一化到[0,1])，长度=3")


class TrainStaticIn(BaseModel):
    strategy: Literal["static_rf", "static_xgb"] = Field("static_rf", description="静态选择策略：RF 或 XGB")
    seed: int = Field(42, description="随机种子")


class TrainDynamicIn(BaseModel):
    episodes: int = Field(200, ge=1, le=5000, description="训练回合数(示例RL)")
    seed: int = Field(42, description="随机种子")


selector = AlgorithmSelector(model_dir="model")


def _is_applicable(alg: Any, features: PhysicsFeaturesIn) -> bool:
    """Hard-filter algorithm candidates by applicability constraints."""
    appc = alg.applicability
    if appc.dimensions is not None and features.dimension not in appc.dimensions:
        return False
    if appc.linearity is not None and features.linearity != appc.linearity:
        return False
    if appc.stationarity is not None and features.stationarity != appc.stationarity:
        return False
    if appc.boundary_conditions is not None and features.boundary_condition not in appc.boundary_conditions:
        return False
    return True


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/constants/algorithms")
def list_algorithms() -> List[Dict[str, Any]]:
    """List all algorithm candidates and their applicability constraints."""
    out: List[Dict[str, Any]] = []
    for a in ALGORITHM_CANDIDATES:
        out.append(
            {
                "key": a.key,
                "name": a.name,
                "description": a.description,
                "applicability": {
                    "dimensions": [int(d) for d in (a.applicability.dimensions or [])] or None,
                    "linearity": int(a.applicability.linearity) if a.applicability.linearity is not None else None,
                    "stationarity": int(a.applicability.stationarity)
                    if a.applicability.stationarity is not None
                    else None,
                    "boundary_conditions": list(a.applicability.boundary_conditions)
                    if a.applicability.boundary_conditions is not None
                    else None,
                },
            }
        )
    return out


@app.get("/hardware")
def get_hardware() -> Dict[str, Any]:
    """Detect and return current hardware info (CPU + optional NVIDIA GPU)."""
    return hardware_info_dict()


@app.post("/selector/train_static")
def train_static(payload: TrainStaticIn) -> Dict[str, Any]:
    """Train static supervised model (RF/XGB) on typical-case proxy dataset."""
    try:
        # DEBUG_BREAKPOINT_TRAIN_STATIC: set breakpoint here.
        info = selector.train_static(strategy=payload.strategy, seed=payload.seed)
        path = selector.save_static()
        return {"trained": info, "saved_to": path}
    except AlgorithmSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/selector/load_static")
def load_static(path: Optional[str] = None) -> Dict[str, Any]:
    """Load static model from model directory or a given path."""
    try:
        # DEBUG_BREAKPOINT_LOAD_STATIC: set breakpoint here.
        return selector.load_static(path=path)
    except AlgorithmSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/selector/train_dynamic")
def train_dynamic(payload: TrainDynamicIn) -> Dict[str, Any]:
    """Train RL dynamic agent using proxy reward shaping."""
    try:
        # DEBUG_BREAKPOINT_TRAIN_DYNAMIC: set breakpoint here.
        info = selector.train_dynamic(episodes=payload.episodes, seed=payload.seed)
        path = selector.save_dynamic()
        return {"trained": info, "saved_to": path}
    except AlgorithmSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/selector/load_dynamic")
def load_dynamic(path: Optional[str] = None) -> Dict[str, Any]:
    """Load RL agent from disk."""
    try:
        # DEBUG_BREAKPOINT_LOAD_DYNAMIC: set breakpoint here.
        return selector.load_dynamic(path=path)
    except AlgorithmSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/selector/select")
def select_algorithm(
    features: FeatureVectorsIn,
    strategy: Literal["static_rf", "static_xgb", "dynamic_rl"] = "static_rf",
) -> Dict[str, Any]:
    """Core mapping function M(F,H,D)->A with scoring & rationale.

    This endpoint expects **normalized** feature vectors (each element in [0,1]).
    You can obtain them from your feature extraction layer, then call this endpoint.
    """
    try:
        # DEBUG_BREAKPOINT_SELECT: set breakpoint here.
        physics = np.array(features.physics, dtype=float)
        hardware = np.array(features.hardware, dtype=float)
        domain = np.array(features.domain, dtype=float)
        return selector.select(physics=physics, hardware=hardware, domain=domain, strategy=strategy)
    except AlgorithmSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/select/rule_based")
def select_rule_based(features: PhysicsFeaturesIn, req: DomainRequirementsIn) -> Dict[str, Any]:
    """A minimal, paper-aligned baseline: rule-based applicability filter.

    In a full implementation, this endpoint would:
    - extract richer PDE features (stiffness, smoothness, geometry complexity, etc.)
    - evaluate hardware capability buckets
    - apply ML model inference (RF/XGB) and/or RL policy
    - output the selected algorithm and rationale
    """
    # DEBUG_BREAKPOINT: set a breakpoint here in Cursor.
    candidates = [a for a in ALGORITHM_CANDIDATES if _is_applicable(a, features)]
    if not candidates:
        raise HTTPException(status_code=404, detail="No applicable algorithms for given features.")

    # Simple preference heuristic:
    # - High accuracy: spectral (if available) > FEM > FDM
    # - High realtime: FDM > FEM > spectral
    preferred_order = []
    if req.accuracy == RequirementLevel.HIGH:
        preferred_order = ["spectral", "fem", "fdm"]
    elif req.realtime == RequirementLevel.HIGH:
        preferred_order = ["fdm", "fem", "spectral"]
    else:
        preferred_order = ["fem", "fdm", "spectral"]

    candidates_by_key = {c.key: c for c in candidates}
    chosen = None
    for k in preferred_order:
        if k in candidates_by_key:
            chosen = candidates_by_key[k]
            break
    chosen = chosen or candidates[0]

    return {
        "selected": {"key": chosen.key, "name": chosen.name},
        "num_applicable": len(candidates),
        "applicable": [{"key": c.key, "name": c.name} for c in candidates],
        "note": "当前为规则基线(可运行)。后续可接入 RF/XGB 推理与 RL 策略。",
    }

