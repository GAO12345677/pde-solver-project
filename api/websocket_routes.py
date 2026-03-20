"""WebSocket路由

提供实时进度推送功能
"""
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any

import numpy as np

from utils.websocket_manager import manager
from solver.numerical_solver import (
    BoundarySpec,
    Heat1DParams,
    SolverError,
    get_solver,
    solve_poisson2d_nonlinear,
)
from config.constants import BoundaryCondition


router = APIRouter()
logger = logging.getLogger(__name__)


def _preview_list(values: list[float], head: int = 50, tail: int = 50) -> Dict[str, Any]:
    """预览列表数据"""
    if not values:
        return {"count": 0, "head": [], "tail": [], "stats": None}
    count = len(values)
    head_vals = values[:head]
    tail_vals = values[-tail:] if tail > 0 else []
    arr = np.array(values)
    stats = {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
    }
    return {"count": count, "head": head_vals, "tail": tail_vals, "stats": stats}


@router.websocket("/ws/solve/{task_id}")
async def websocket_solve(websocket: WebSocket, task_id: str):
    """WebSocket求解端点"""
    await manager.connect(websocket, task_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "solve":
                await handle_solve_request(websocket, task_id, data.get("params", {}))
            elif data.get("action") == "cancel":
                await handle_cancel_request(task_id)
                
    except WebSocketDisconnect:
        manager.disconnect(task_id)
        logger.info(f"WebSocket客户端主动断开: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: task_id={task_id}, error={e}")
        await manager.send_error(task_id, str(e))
        manager.disconnect(task_id)


async def handle_solve_request(websocket: WebSocket, task_id: str, params: Dict[str, Any]):
    """处理求解请求"""
    try:
        await manager.send_progress(task_id, 0.0, "开始求解...", "running")
        
        result = await solve_equation_internal(params, task_id)
        
        await manager.send_progress(task_id, 0.8, "求解完成，准备结果...", "running")
        await manager.send_complete(task_id, result)
        logger.info(f"求解完成: task_id={task_id}")
        
    except Exception as e:
        logger.error(f"求解失败: task_id={task_id}, error={e}")
        await manager.send_error(task_id, str(e))


async def handle_cancel_request(task_id: str):
    """处理取消请求"""
    manager.disconnect(task_id)
    logger.info(f"求解已取消: task_id={task_id}")


async def solve_equation_internal(params: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """内部求解函数，支持进度回调"""
    await manager.send_progress(task_id, 0.2, "解析参数...", "running")
    
    try:
        eq_type = str(params.get("equation_type", "heat1d")).strip().lower()
        algorithm_key = str(params.get("algorithm_key", "")).strip().lower()
        
        if algorithm_key not in ("fdm", "fem", "spectral"):
            raise ValueError("algorithm_key 必须是 fdm/fem/spectral。")

        return_full = str(params.get("return_full_solution", "false")).strip().lower() in ("1", "true", "yes")
        
        await manager.send_progress(task_id, 0.4, "初始化求解器...", "running")
        
        if eq_type == "heat1d":
            k = float(params.get("k", 1.0))
            L = float(params.get("L", 1.0))
            nx = int(params.get("nx", 101))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.1))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            enforce_nonneg = str(params.get("enforce_nonnegativity", "true")).strip().lower() not in ("0", "false", "no")

            heat_params = Heat1DParams(k=k, L=L, nx=nx, t_span=(t0, t1), enforce_nonnegativity=enforce_nonneg)
            
            if bc_type == BoundaryCondition.DIRICHLET:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            elif bc_type == BoundaryCondition.NEUMANN:
                bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)
            else:
                bc = BoundarySpec(
                    bc_type=bc_type,
                    left_mixed=(1.0, 1.0, lambda t: left_bc),
                    right_mixed=(1.0, 1.0, lambda t: right_bc),
                )

            initial_kind = str(params.get("initial", "sine_nonnegative")).strip().lower()

            def initial_fn(x: np.ndarray) -> np.ndarray:
                if initial_kind == "constant":
                    return np.full_like(x, 1.0, dtype=float)
                return np.maximum(0.0, np.sin(np.pi * x / float(L)))

            await manager.send_progress(task_id, 0.6, "正在求解...", "running")
            
            solver = get_solver(algorithm_key)
            sol, info, validation = solver.solve(params=heat_params, bc=bc, initial=initial_fn)
            sol_list = sol.tolist()
            
            data = {
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "poisson2d_nonlinear":
            nx = int(params.get("nx", 41))
            ny = int(params.get("ny", 41))
            Lx = float(params.get("Lx", 1.0))
            Ly = float(params.get("Ly", 1.0))
            tol = float(params.get("tol", 1e-6))
            max_iter = int(params.get("max_iter", 200))
            
            await manager.send_progress(task_id, 0.6, "正在求解...", "running")
            
            sol2d, info = solve_poisson2d_nonlinear(nx=nx, ny=ny, Lx=Lx, Ly=Ly, tol=tol, max_iter=max_iter)
            sol_list = sol2d.reshape(-1).tolist()
            
            data = {"shape": [ny, nx], "solve_info": info, "solution_preview": _preview_list(sol_list)}
            if return_full:
                data["solution"] = sol_list
            return data
        else:
            raise ValueError("equation_type 必须是 heat1d 或 poisson2d_nonlinear。")
            
    except (SolverError, ValueError) as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"求解失败: {e}")
