"""Numerical solver layer.

Implements three numerical solvers corresponding to the algorithm candidates:
- FiniteDifferenceSolver (FDM)
- FiniteElementSolver    (FEM, 1D linear elements baseline)
- SpectralMethodSolver   (Spectral, 1D sine-basis baseline)

Primary target:
- 1D linear heat conduction equation (优先):
    u_t = k * u_xx + s(x,t)
  on x in [0, L], with Dirichlet/Neumann/Mixed BC.

Design goals (paper-aligned):
- Be modular and extensible to 2D/3D later.
- Provide physics constraints (e.g. non-negative temperature) and BC enforcement.
- Provide validation of physical reasonableness and numerical stability.

Implementation notes:
- Time integration uses scipy.integrate.solve_ivp where applicable.
- Computation uses numpy for vectorization.

Compatibility:
- Python 3.10+ (Windows 10/11)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from config.constants import BoundaryCondition, Dimension, Linearity, Stationarity


class SolverError(RuntimeError):
    """Raised when the PDE cannot be solved under given settings."""


SourceFn = Callable[[np.ndarray, float], np.ndarray]
InitFn = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class Heat1DParams:
    """Structured parameters for 1D heat equation."""

    k: float  # diffusion coefficient, must be >0
    L: float  # domain length, must be >0
    nx: int  # number of grid points/nodes, >= 5 recommended
    t_span: Tuple[float, float]  # (t0, t1); if t0==t1 -> steady solve
    dt_out: float = 0.0  # output sampling step; 0 means "solver internal only"
    enforce_nonnegativity: bool = True
    # Intended for extension: dimension/linearity/stationarity flags (paper feature alignment)
    dimension: Dimension = Dimension.D1
    linearity: Linearity = Linearity.LINEAR
    stationarity: Stationarity = Stationarity.UNSTEADY


@dataclass(frozen=True)
class BoundarySpec:
    """Boundary condition specification for 1D heat equation.

    For Dirichlet: u(0,t)=left_value(t), u(L,t)=right_value(t)
    For Neumann:   u_x(0,t)=left_value(t), u_x(L,t)=right_value(t)
    For Mixed:     alpha*u + beta*u_x = g(t)  (encoded via (alpha, beta, g(t)) per side)
    """

    bc_type: BoundaryCondition
    left_value: Optional[Callable[[float], float]] = None
    right_value: Optional[Callable[[float], float]] = None
    left_mixed: Optional[Tuple[float, float, Callable[[float], float]]] = None
    right_mixed: Optional[Tuple[float, float, Callable[[float], float]]] = None


@dataclass
class SolveInfo:
    """Solver run metadata used for feedback evaluation."""

    algorithm: str
    elapsed_s: float
    nfev: int
    status: str
    # Proxy metrics; replace with real measurements when integrated with profilers.
    estimated_error: Optional[float] = None
    resource_proxy: Optional[float] = None


def _validate_heat_params(p: Heat1DParams) -> None:
    if p.dimension != Dimension.D1:
        raise SolverError("当前实现优先支持 1D；2D/3D 请使用扩展接口（预留未实现）。")
    if p.linearity != Linearity.LINEAR:
        raise SolverError("当前求解器示例仅支持线性方程（linearity=LINEAR）。")
    if p.k <= 0 or not math.isfinite(p.k):
        raise SolverError("扩散系数 k 必须为正且有限。")
    if p.L <= 0 or not math.isfinite(p.L):
        raise SolverError("区间长度 L 必须为正且有限。")
    if p.nx < 5:
        raise SolverError("nx 太小（建议 >= 5）。")
    t0, t1 = p.t_span
    if not (math.isfinite(t0) and math.isfinite(t1)):
        raise SolverError("t_span 必须为有限数值。")
    if t1 < t0:
        raise SolverError("t_span 必须满足 t1 >= t0。")
    if p.dt_out < 0:
        raise SolverError("dt_out 不能为负。")


def _validate_bc(bc: BoundarySpec) -> None:
    if bc.bc_type == BoundaryCondition.DIRICHLET:
        if bc.left_value is None or bc.right_value is None:
            raise SolverError("Dirichlet 边界需要 left_value(t) 与 right_value(t)。")
    elif bc.bc_type == BoundaryCondition.NEUMANN:
        if bc.left_value is None or bc.right_value is None:
            raise SolverError("Neumann 边界需要 left_value(t) 与 right_value(t)（表示导数值）。")
    elif bc.bc_type == BoundaryCondition.MIXED:
        if bc.left_mixed is None or bc.right_mixed is None:
            raise SolverError("Mixed 边界需要 left_mixed/right_mixed=(alpha,beta,g(t))。")
    else:
        raise SolverError(f"未知边界类型: {bc.bc_type}")


def _default_source(x: np.ndarray, t: float) -> np.ndarray:
    return np.zeros_like(x, dtype=float)


def _enforce_nonneg(u: np.ndarray) -> np.ndarray:
    u2 = u.copy()
    u2[u2 < 0] = 0.0
    return u2


def _make_grid(L: float, nx: int) -> Tuple[np.ndarray, float]:
    x = np.linspace(0.0, float(L), int(nx), dtype=float)
    dx = float(x[1] - x[0])
    return x, dx


def _apply_dirichlet(u: np.ndarray, left: float, right: float) -> None:
    u[0] = float(left)
    u[-1] = float(right)


def _laplacian_fdm(u: np.ndarray, dx: float) -> np.ndarray:
    """Second derivative for interior points with central differences.

    Boundary handling is done separately by each solver implementation.
    """
    d2 = np.zeros_like(u, dtype=float)
    inv_dx2 = 1.0 / (dx * dx)
    d2[1:-1] = (u[2:] - 2.0 * u[1:-1] + u[:-2]) * inv_dx2
    return d2


def validate_solution(
    u: np.ndarray,
    bc: BoundarySpec,
    params: Heat1DParams,
    x: np.ndarray,
    t: float,
    tol: float = 1e-6,
) -> Dict[str, Any]:
    """Validate physical reasonableness and numerical stability."""
    report: Dict[str, Any] = {
        "finite": bool(np.all(np.isfinite(u))),
        "nonnegative": bool(np.min(u) >= -tol),
        "bc_satisfied": True,
        "notes": [],
    }
    if not report["finite"]:
        report["bc_satisfied"] = False
        report["notes"].append("解包含 NaN/Inf，可能存在数值溢出或不稳定。建议减小时间步/更换求解方法。")
        return report

    # BC validation (weak check)
    try:
        if bc.bc_type == BoundaryCondition.DIRICHLET:
            lv = float(bc.left_value(t))  # type: ignore[misc]
            rv = float(bc.right_value(t))  # type: ignore[misc]
            if abs(u[0] - lv) > 10 * tol or abs(u[-1] - rv) > 10 * tol:
                report["bc_satisfied"] = False
                report["notes"].append("Dirichlet 边界未满足（可能是求解器未强制施加或参数冲突）。")
        elif bc.bc_type == BoundaryCondition.NEUMANN:
            dx = float(x[1] - x[0])
            left_grad = (u[1] - u[0]) / dx
            right_grad = (u[-1] - u[-2]) / dx
            lv = float(bc.left_value(t))  # type: ignore[misc]
            rv = float(bc.right_value(t))  # type: ignore[misc]
            if abs(left_grad - lv) > 1e-3 or abs(right_grad - rv) > 1e-3:
                report["bc_satisfied"] = False
                report["notes"].append("Neumann 边界导数未满足（可能是离散边界处理不一致）。")
        else:
            # Mixed: alpha*u + beta*u_x = g
            dx = float(x[1] - x[0])
            a, b, g = bc.left_mixed  # type: ignore[misc]
            left_expr = float(a) * float(u[0]) + float(b) * float((u[1] - u[0]) / dx)
            if abs(left_expr - float(g(t))) > 1e-3:
                report["bc_satisfied"] = False
                report["notes"].append("Mixed 左边界未满足。")
            a, b, g = bc.right_mixed  # type: ignore[misc]
            right_expr = float(a) * float(u[-1]) + float(b) * float((u[-1] - u[-2]) / dx)
            if abs(right_expr - float(g(t))) > 1e-3:
                report["bc_satisfied"] = False
                report["notes"].append("Mixed 右边界未满足。")
    except Exception as e:  # noqa: BLE001
        report["bc_satisfied"] = False
        report["notes"].append(f"边界验证失败: {e}")

    if params.enforce_nonnegativity and not report["nonnegative"]:
        report["notes"].append("出现负温度（违反非负约束）。建议启用/加强非负投影或收紧时间步。")

    # Numerical stability proxy: large gradients may indicate instability
    grad = np.abs(np.gradient(u, x))
    report["max_gradient"] = float(np.max(grad))
    if report["max_gradient"] > 1e6:
        report["notes"].append("梯度异常大，可能存在数值振荡/不稳定。建议检查网格与时间积分设置。")

    return report


class BaseHeatSolver1D:
    """Base class defining shared interface and helpers for 1D heat solvers."""

    algorithm_key: str = "base"

    def solve(
        self,
        params: Heat1DParams,
        bc: BoundarySpec,
        initial: InitFn,
        source: SourceFn = _default_source,
    ) -> Tuple[np.ndarray, SolveInfo, Dict[str, Any]]:
        raise NotImplementedError


class FiniteDifferenceSolver(BaseHeatSolver1D):
    """1D heat equation solver using finite differences + solve_ivp."""

    algorithm_key = "fdm"

    def solve(
        self,
        params: Heat1DParams,
        bc: BoundarySpec,
        initial: InitFn,
        source: SourceFn = _default_source,
    ) -> Tuple[np.ndarray, SolveInfo, Dict[str, Any]]:
        _validate_heat_params(params)
        _validate_bc(bc)
        x, dx = _make_grid(params.L, params.nx)
        t0, t1 = params.t_span

        u0 = np.asarray(initial(x), dtype=float).reshape(-1)
        if u0.shape[0] != params.nx:
            raise SolverError("初始条件返回数组长度必须等于 nx。")
        if np.any(~np.isfinite(u0)):
            raise SolverError("初始条件包含 NaN/Inf。")

        if bc.bc_type == BoundaryCondition.DIRICHLET:
            _apply_dirichlet(u0, bc.left_value(t0), bc.right_value(t0))  # type: ignore[misc]
        if params.enforce_nonnegativity:
            u0 = _enforce_nonneg(u0)

        def rhs(t: float, u_flat: np.ndarray) -> np.ndarray:
            u = u_flat.reshape(-1)
            if bc.bc_type == BoundaryCondition.DIRICHLET:
                _apply_dirichlet(u, bc.left_value(t), bc.right_value(t))  # type: ignore[misc]
            # Neumann/Mixed: handled via ghost-point style modifications
            d2 = _laplacian_fdm(u, dx)

            if bc.bc_type == BoundaryCondition.NEUMANN:
                # u_x(0)=g0 => (u1-u0)/dx = g0 => u0 = u1 - g0*dx
                g0 = float(bc.left_value(t))  # type: ignore[misc]
                gL = float(bc.right_value(t))  # type: ignore[misc]
                u0_ghost = u[1] - g0 * dx
                uL_ghost = u[-2] + gL * dx
                d2[0] = (u[1] - 2.0 * u[0] + u0_ghost) / (dx * dx)
                d2[-1] = (uL_ghost - 2.0 * u[-1] + u[-2]) / (dx * dx)
            elif bc.bc_type == BoundaryCondition.MIXED:
                # alpha*u + beta*u_x = g. Use one-sided gradient approximation.
                a, b, g = bc.left_mixed  # type: ignore[misc]
                gt = float(g(t))
                # (u1-u0)/dx approx u_x
                # a*u0 + b*(u1-u0)/dx = gt -> u0*(a - b/dx) + u1*(b/dx) = gt
                denom = float(a) - float(b) / dx
                if abs(denom) < 1e-12:
                    raise SolverError("Mixed 左边界参数导致奇异约束（a - b/dx 接近 0）。")
                u0_enforced = (gt - (float(b) / dx) * float(u[1])) / denom
                u0_ghost = u[1] - (float(b) and 0.0)  # placeholder (not used)
                u[0] = u0_enforced

                a, b, g = bc.right_mixed  # type: ignore[misc]
                gt = float(g(t))
                denom = float(a) + float(b) / dx  # u_x ~ (uN-uN-1)/dx
                if abs(denom) < 1e-12:
                    raise SolverError("Mixed 右边界参数导致奇异约束（a + b/dx 接近 0）。")
                uL_enforced = (gt + (float(b) / dx) * float(u[-2])) / denom
                u[-1] = uL_enforced

            s = np.asarray(source(x, t), dtype=float).reshape(-1)
            if s.shape[0] != params.nx:
                raise SolverError("source(x,t) 返回长度必须等于 nx。")
            dudt = params.k * d2 + s

            if bc.bc_type == BoundaryCondition.DIRICHLET:
                dudt[0] = 0.0
                dudt[-1] = 0.0
            return dudt

        t_eval = None
        if params.dt_out > 0 and t1 > t0:
            n = int(math.floor((t1 - t0) / params.dt_out)) + 1
            t_eval = np.linspace(t0, t0 + params.dt_out * (n - 1), n, dtype=float)

        start = time.perf_counter()
        try:
            if t1 == t0:
                # Steady fallback: solve k*u_xx + s(x)=0 with Dirichlet by simple linear system
                if bc.bc_type != BoundaryCondition.DIRICHLET:
                    raise SolverError("稳态示例仅实现 Dirichlet 边界。")
                A = np.zeros((params.nx, params.nx), dtype=float)
                bvec = -np.asarray(source(x, t0), dtype=float).reshape(-1)
                inv_dx2 = 1.0 / (dx * dx)
                for i in range(1, params.nx - 1):
                    A[i, i - 1] = params.k * inv_dx2
                    A[i, i] = -2.0 * params.k * inv_dx2
                    A[i, i + 1] = params.k * inv_dx2
                A[0, 0] = 1.0
                A[-1, -1] = 1.0
                bvec[0] = float(bc.left_value(t0))  # type: ignore[misc]
                bvec[-1] = float(bc.right_value(t0))  # type: ignore[misc]
                u_end = np.linalg.solve(A, bvec)
                nfev = 0
                status = "steady_solved"
            else:
                sol = solve_ivp(
                    rhs,
                    (t0, t1),
                    u0.astype(float),
                    method="RK45",
                    t_eval=t_eval,
                    rtol=1e-6,
                    atol=1e-9,
                )
                if not sol.success:
                    raise SolverError(f"时间积分失败: {sol.message}")
                u_end = sol.y[:, -1]
                nfev = int(sol.nfev)
                status = "ok"
        except FloatingPointError as e:
            raise SolverError(f"计算溢出/非法浮点: {e}。建议减小步长或检查参数规模。") from e
        except np.linalg.LinAlgError as e:
            raise SolverError(f"线性求解失败(可能无解/病态): {e}。建议检查边界条件是否冲突。") from e
        finally:
            elapsed = time.perf_counter() - start

        if params.enforce_nonnegativity:
            u_end = _enforce_nonneg(np.asarray(u_end, dtype=float))
        if bc.bc_type == BoundaryCondition.DIRICHLET:
            _apply_dirichlet(u_end, bc.left_value(t1), bc.right_value(t1))  # type: ignore[misc]

        validation = validate_solution(u_end, bc, params, x=x, t=t1)
        info = SolveInfo(
            algorithm=self.algorithm_key,
            elapsed_s=float(elapsed),
            nfev=int(nfev),
            status=status,
            resource_proxy=float(params.nx) / 1e6,
        )
        return u_end, info, validation


class FiniteElementSolver(BaseHeatSolver1D):
    """1D linear FEM baseline using mass+stiffness matrices and solve_ivp on nodal DOFs."""

    algorithm_key = "fem"

    def solve(
        self,
        params: Heat1DParams,
        bc: BoundarySpec,
        initial: InitFn,
        source: SourceFn = _default_source,
    ) -> Tuple[np.ndarray, SolveInfo, Dict[str, Any]]:
        _validate_heat_params(params)
        _validate_bc(bc)
        if bc.bc_type != BoundaryCondition.DIRICHLET:
            raise SolverError("FEM 示例优先实现 Dirichlet 边界（可扩展 Neumann/Mixed）。")

        x, dx = _make_grid(params.L, params.nx)
        t0, t1 = params.t_span

        u0 = np.asarray(initial(x), dtype=float).reshape(-1)
        if u0.shape[0] != params.nx:
            raise SolverError("初始条件返回数组长度必须等于 nx。")
        _apply_dirichlet(u0, bc.left_value(t0), bc.right_value(t0))  # type: ignore[misc]
        if params.enforce_nonnegativity:
            u0 = _enforce_nonneg(u0)

        # Assemble 1D linear element matrices (uniform mesh)
        n = params.nx
        M = np.zeros((n, n), dtype=float)
        K = np.zeros((n, n), dtype=float)
        # Element mass: (dx/6) * [[2,1],[1,2]]
        # Element stiffness: (1/dx) * [[1,-1],[-1,1]]
        for e in range(n - 1):
            idx = [e, e + 1]
            Me = (dx / 6.0) * np.array([[2.0, 1.0], [1.0, 2.0]], dtype=float)
            Ke = (1.0 / dx) * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float)
            for a in range(2):
                for b in range(2):
                    M[idx[a], idx[b]] += Me[a, b]
                    K[idx[a], idx[b]] += Ke[a, b]

        # Apply Dirichlet by eliminating first/last DOFs (interior only)
        interior = slice(1, n - 1)
        Mi = M[interior, interior]
        Ki = K[interior, interior]

        # Pre-factorize Mi for efficiency
        try:
            Mi_inv = np.linalg.inv(Mi)
        except np.linalg.LinAlgError as e:
            raise SolverError(f"FEM 质量矩阵不可逆(病态)：{e}") from e

        def rhs(t: float, ui: np.ndarray) -> np.ndarray:
            u_full = np.zeros((n,), dtype=float)
            u_full[0] = float(bc.left_value(t))  # type: ignore[misc]
            u_full[-1] = float(bc.right_value(t))  # type: ignore[misc]
            u_full[1:-1] = ui
            f = np.asarray(source(x, t), dtype=float).reshape(-1)
            if f.shape[0] != n:
                raise SolverError("source(x,t) 返回长度必须等于 nx。")
            fi = f[1:-1]
            # Semi-discrete: M du/dt + k K u = f  -> du/dt = M^{-1}(f - k K u)
            dudt = Mi_inv @ (fi - params.k * (Ki @ ui))
            return dudt

        start = time.perf_counter()
        try:
            if t1 == t0:
                # Steady: k*K*u = f with Dirichlet
                f0 = np.asarray(source(x, t0), dtype=float).reshape(-1)
                fi = f0[1:-1]
                ui = np.linalg.solve(params.k * Ki, fi)
                nfev = 0
                status = "steady_solved"
            else:
                sol = solve_ivp(
                    rhs,
                    (t0, t1),
                    u0[1:-1].astype(float),
                    method="RK45",
                    rtol=1e-6,
                    atol=1e-9,
                )
                if not sol.success:
                    raise SolverError(f"时间积分失败: {sol.message}")
                ui = sol.y[:, -1]
                nfev = int(sol.nfev)
                status = "ok"
        except np.linalg.LinAlgError as e:
            raise SolverError(f"线性求解失败：{e}") from e
        finally:
            elapsed = time.perf_counter() - start

        u_end = np.zeros((n,), dtype=float)
        u_end[0] = float(bc.left_value(t1))  # type: ignore[misc]
        u_end[-1] = float(bc.right_value(t1))  # type: ignore[misc]
        u_end[1:-1] = ui
        if params.enforce_nonnegativity:
            u_end = _enforce_nonneg(u_end)

        validation = validate_solution(u_end, bc, params, x=x, t=t1)
        info = SolveInfo(
            algorithm=self.algorithm_key,
            elapsed_s=float(elapsed),
            nfev=int(nfev),
            status=status,
            resource_proxy=float(params.nx) / 8e5,
        )
        return u_end, info, validation


class SpectralMethodSolver(BaseHeatSolver1D):
    """1D spectral Galerkin (sine basis) baseline for Dirichlet BC."""

    algorithm_key = "spectral"

    def solve(
        self,
        params: Heat1DParams,
        bc: BoundarySpec,
        initial: InitFn,
        source: SourceFn = _default_source,
    ) -> Tuple[np.ndarray, SolveInfo, Dict[str, Any]]:
        _validate_heat_params(params)
        _validate_bc(bc)
        if bc.bc_type != BoundaryCondition.DIRICHLET:
            raise SolverError("谱方法示例优先实现 Dirichlet 边界（正弦基）。")

        from scipy.fft import dst, idst  # local import to keep base deps light

        x, _ = _make_grid(params.L, params.nx)
        t0, t1 = params.t_span

        u0 = np.asarray(initial(x), dtype=float).reshape(-1)
        if u0.shape[0] != params.nx:
            raise SolverError("初始条件返回数组长度必须等于 nx。")

        # Enforce Dirichlet boundaries by subtracting a linear "lift" matching BCs.
        def lift(t: float) -> np.ndarray:
            left = float(bc.left_value(t))  # type: ignore[misc]
            right = float(bc.right_value(t))  # type: ignore[misc]
            return left + (right - left) * (x / params.L)

        u0_h = u0 - lift(t0)
        u0_h[0] = 0.0
        u0_h[-1] = 0.0

        # Use sine-series coefficients on interior points (exclude endpoints)
        u_int0 = u0_h[1:-1]
        a0 = dst(u_int0, type=1)  # coefficients (unnormalized)
        n_modes = a0.shape[0]
        m = np.arange(1, n_modes + 1, dtype=float)
        lam = (math.pi * m / params.L) ** 2  # eigenvalues of -d2/dx2

        def rhs(t: float, a: np.ndarray) -> np.ndarray:
            # Reconstruct u on interior to evaluate source term if present.
            u_int = idst(a, type=1) / (2 * (n_modes + 1))
            u_full_h = np.zeros((params.nx,), dtype=float)
            u_full_h[1:-1] = u_int
            u_full = u_full_h + lift(t)

            s = np.asarray(source(x, t), dtype=float).reshape(-1)
            if s.shape[0] != params.nx:
                raise SolverError("source(x,t) 返回长度必须等于 nx。")
            s_h = s.copy()
            # Project source interior onto sine basis
            s_int = s_h[1:-1]
            s_a = dst(s_int, type=1)
            # Modal ODE: a_t = -k*lam*a + s_a
            return (-params.k * lam) * a + s_a

        start = time.perf_counter()
        try:
            if t1 == t0:
                # Steady: -k*lam*a + s_a = 0 -> a = s_a/(k*lam)
                s0 = np.asarray(source(x, t0), dtype=float).reshape(-1)
                s_a0 = dst(s0[1:-1], type=1)
                a_end = s_a0 / (params.k * lam)
                nfev = 0
                status = "steady_solved"
            else:
                sol = solve_ivp(rhs, (t0, t1), a0.astype(float), method="RK45", rtol=1e-6, atol=1e-9)
                if not sol.success:
                    raise SolverError(f"时间积分失败: {sol.message}")
                a_end = sol.y[:, -1]
                nfev = int(sol.nfev)
                status = "ok"
        finally:
            elapsed = time.perf_counter() - start

        u_int = idst(a_end, type=1) / (2 * (n_modes + 1))
        u_full_h = np.zeros((params.nx,), dtype=float)
        u_full_h[1:-1] = u_int
        u_end = u_full_h + lift(t1)
        _apply_dirichlet(u_end, bc.left_value(t1), bc.right_value(t1))  # type: ignore[misc]
        if params.enforce_nonnegativity:
            u_end = _enforce_nonneg(u_end)

        validation = validate_solution(u_end, bc, params, x=x, t=t1)
        info = SolveInfo(
            algorithm=self.algorithm_key,
            elapsed_s=float(elapsed),
            nfev=int(nfev),
            status=status,
            resource_proxy=float(params.nx) / 1.2e6,
        )
        return u_end, info, validation


def get_solver(algorithm_key: str) -> BaseHeatSolver1D:
    """Factory for solver instances based on algorithm key."""
    k = str(algorithm_key).strip().lower()
    if k == "fdm":
        return FiniteDifferenceSolver()
    if k == "fem":
        return FiniteElementSolver()
    if k == "spectral":
        return SpectralMethodSolver()
    raise SolverError(f"未知求解算法: {algorithm_key!r}")

