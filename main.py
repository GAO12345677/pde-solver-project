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

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.constants import (
    ALGORITHM_CANDIDATES,
    BoundaryCondition,
    Dimension,
    Linearity,
    RequirementLevel,
    Stationarity,
)
from services.hardware import hardware_info_dict


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

