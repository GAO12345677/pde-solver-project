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
    solve_heat3d_fdm,
    solve_heat3d_fvm,
    get_solver,
    solve_heat2d_fdm,
    solve_heat2d_fem,
    solve_heat2d_fvm,
    solve_poisson3d_fdm,
    solve_poisson2d_nonlinear,
    Wave1DParams,
    solve_wave2d_fdm,
    solve_wave2d_fem,
    solve_wave2d_spectral,
    solve_wave1d_fem,
    solve_wave1d,
    solve_wave3d_fdm,
    solve_wave1d_spectral_v2,
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
        
        if algorithm_key not in ("fdm", "fvm", "fem", "spectral", "pinn", "bem"):
            raise ValueError("algorithm_key 必须是 fdm/fvm/fem/spectral。")

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

        elif eq_type == "heat2d":
            if algorithm_key not in ("fdm", "fvm", "fem"):
                raise ValueError("heat2d 当前仅支持 FDM/FVM/FEM。")

            k = float(params.get("k", 1.0))
            nx = int(params.get("nx", 41))
            ny = int(params.get("ny", 41))
            Lx = float(params.get("Lx", params.get("L", 1.0)))
            Ly = float(params.get("Ly", params.get("L", 1.0)))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.05))
            nt = int(params.get("nt", 200))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("heat2d 当前仅支持零 Dirichlet 边界。")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                raise ValueError("heat2d 当前要求零 Dirichlet 边界。")

            await manager.send_progress(task_id, 0.6, "正在求解二维热传导方程...", "running")

            if algorithm_key in ("fvm", "pinn"):
                sol2d, info_pack = solve_heat2d_fvm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "fem":
                sol2d, info_pack = solve_heat2d_fem(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            else:
                sol2d, info_pack = solve_heat2d_fdm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, k=k, t_span=(t0, t1), nt=nt)
            sol_list = sol2d.reshape(-1).tolist()
            data = {
                "shape": [ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "heat3d":
            if algorithm_key not in ("fdm", "fvm"):
                raise ValueError("heat3d 当前仅支持 FDM。")

            k = float(params.get("k", 1.0))
            nx = int(params.get("nx", 11))
            ny = int(params.get("ny", 11))
            nz = int(params.get("nz", 11))
            Lx = float(params.get("Lx", params.get("L", 1.0)))
            Ly = float(params.get("Ly", params.get("L", 1.0)))
            Lz = float(params.get("Lz", params.get("L", 1.0)))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.02))
            nt = int(params.get("nt", 200))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("heat3d 当前仅支持零 Dirichlet 边界。")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                raise ValueError("heat3d 当前要求零 Dirichlet 边界。")

            await manager.send_progress(task_id, 0.6, "正在求解三维热传导方程...", "running")

            if algorithm_key == "fvm":
                sol3d, info_pack = solve_heat3d_fvm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(t0, t1), nt=nt)
            else:
                sol3d, info_pack = solve_heat3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, k=k, t_span=(t0, t1), nt=nt)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "wave2d":
            if algorithm_key not in ("fdm", "fem", "spectral"):
                raise ValueError("wave2d 当前仅支持 FDM。")

            c = float(params.get("c", 1.0))
            nx = int(params.get("nx", 41))
            ny = int(params.get("ny", 41))
            Lx = float(params.get("Lx", params.get("L", 1.0)))
            Ly = float(params.get("Ly", params.get("L", 1.0)))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.2))
            nt = int(params.get("nt", 200))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("wave2d 当前仅支持零 Dirichlet 边界。")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                raise ValueError("wave2d 当前要求零 Dirichlet 边界。")

            await manager.send_progress(task_id, 0.6, "正在求解二维波动方程...", "running")

            if algorithm_key == "fem":
                sol2d, info_pack = solve_wave2d_fem(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1), nt=nt)
            elif algorithm_key == "spectral":
                sol2d, info_pack = solve_wave2d_spectral(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1))
            else:
                sol2d, info_pack = solve_wave2d_fdm(nx=nx, ny=ny, Lx=Lx, Ly=Ly, c=c, t_span=(t0, t1), nt=nt)
            sol_list = sol2d.reshape(-1).tolist()
            data = {
                "shape": [ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "wave3d":
            if algorithm_key != "fdm":
                raise ValueError("wave3d currently only supports FDM.")

            c = float(params.get("c", 1.0))
            nx = int(params.get("nx", 15))
            ny = int(params.get("ny", 15))
            nz = int(params.get("nz", 15))
            Lx = float(params.get("Lx", params.get("L", 1.0)))
            Ly = float(params.get("Ly", params.get("L", 1.0)))
            Lz = float(params.get("Lz", params.get("L", 1.0)))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.15))
            nt = int(params.get("nt", 200))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("wave3d currently only supports zero Dirichlet boundaries.")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                raise ValueError("wave3d currently requires zero Dirichlet boundary values.")

            await manager.send_progress(task_id, 0.6, "Running 3D wave solver...", "running")
            sol3d, info_pack = solve_wave3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz, c=c, t_span=(t0, t1), nt=nt)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info_pack["solve_info"]["algorithm"],
                "solve_info": info_pack["solve_info"],
                "validation": info_pack["validation"],
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "poisson1d":
            if algorithm_key == "fvm":
                raise ValueError("poisson1d 当前尚未实现 FVM。")
            L = float(params.get("L", 1.0))
            nx = int(params.get("nx", 101))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("poisson1d 当前仅支持 Dirichlet 边界。")
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            poisson_params = Heat1DParams(k=1.0, L=L, nx=nx, t_span=(0.0, 0.0), enforce_nonnegativity=False)
            bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)

            def initial_fn(x: np.ndarray) -> np.ndarray:
                return np.zeros_like(x, dtype=float)

            def source_fn(x: np.ndarray, t: float) -> np.ndarray:
                return (np.pi ** 2) * np.sin(np.pi * x / float(L))

            await manager.send_progress(task_id, 0.6, "姝ｅ湪姹傝В...", "running")

            solver = get_solver(algorithm_key)
            sol, info, validation = solver.solve(params=poisson_params, bc=bc, initial=initial_fn, source=source_fn)
            sol_list = sol.tolist()
            data = {
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.algorithm,
                "solve_info": info.__dict__,
                "validation": validation,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "poisson3d":
            if algorithm_key != "fdm":
                raise ValueError("poisson3d 当前仅支持 FDM。")
            nx = int(params.get("nx", 21))
            ny = int(params.get("ny", 21))
            nz = int(params.get("nz", 21))
            Lx = float(params.get("Lx", params.get("L", 1.0)))
            Ly = float(params.get("Ly", params.get("L", 1.0)))
            Lz = float(params.get("Lz", params.get("L", 1.0)))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type != BoundaryCondition.DIRICHLET:
                raise ValueError("poisson3d 当前仅支持 Dirichlet 边界。")
            if abs(left_bc) > 1e-12 or abs(right_bc) > 1e-12:
                raise ValueError("poisson3d 当前要求零 Dirichlet 边界。")

            await manager.send_progress(task_id, 0.6, "正在求解三维 Poisson 方程...", "running")

            sol3d, info = solve_poisson3d_fdm(nx=nx, ny=ny, nz=nz, Lx=Lx, Ly=Ly, Lz=Lz)
            sol_list = sol3d.reshape(-1).tolist()
            data = {
                "shape": [nz, ny, nx],
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.get("algorithm", algorithm_key),
                "solve_info": info,
                "solution_preview": _preview_list(sol_list),
            }
            if return_full:
                data["solution"] = sol_list
            return data

        elif eq_type == "wave1d":
            if algorithm_key == "fvm":
                raise ValueError("wave1d 当前尚未实现 FVM。")
            c = float(params.get("c", 1.0))
            L = float(params.get("L", 1.0))
            nx = int(params.get("nx", 101))
            nt = int(params.get("nt", 200))
            t0 = float(params.get("t0", 0.0))
            t1 = float(params.get("t1", 0.5))
            bc_type = BoundaryCondition(str(params.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(params.get("left_bc", 0.0))
            right_bc = float(params.get("right_bc", 0.0))
            if bc_type == BoundaryCondition.MIXED:
                raise ValueError("wave1d 当前仅支持 Dirichlet 或 Neumann 边界。")

            wave_params = Wave1DParams(c=c, L=L, nx=nx, t_span=(t0, t1), nt=nt)
            bc = BoundarySpec(bc_type=bc_type, left_value=lambda t: left_bc, right_value=lambda t: right_bc)

            def initial_fn(x: np.ndarray) -> np.ndarray:
                return np.sin(np.pi * x / float(L))

            def velocity_fn(x: np.ndarray) -> np.ndarray:
                return np.zeros_like(x, dtype=float)

            await manager.send_progress(task_id, 0.6, "正在求解...", "running")

            if algorithm_key == "spectral":
                sol, info, validation = solve_wave1d_spectral_v2(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            elif algorithm_key == "fem":
                sol, info, validation = solve_wave1d_fem(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            else:
                sol, info, validation = solve_wave1d(
                    params=wave_params,
                    bc=bc,
                    initial_displacement=initial_fn,
                    initial_velocity=velocity_fn,
                )
            sol_list = sol.tolist()
            data = {
                "equation_type": eq_type,
                "recommended_algorithm": algorithm_key,
                "executed_algorithm": info.algorithm,
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
            raise ValueError("equation_type 必须是 heat1d、heat2d、heat3d、wave1d、wave2d、poisson1d、poisson3d 或 poisson2d_nonlinear。")
            
    except (SolverError, ValueError) as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"求解失败: {e}")
