"""Feature extraction layer.

Implements three main extractors, following the paper's architecture:
- PhysicsFeatureExtractor  : PDE/physics equation features
- HardwareFeatureExtractor : runtime hardware capabilities
- DomainFeatureExtractor   : domain-level requirements and budgets

Requirements:
- Python 3.10+ (Windows 10/11)
- Dependencies: numpy, torch, py-cpuinfo (optional but recommended)

Each extractor:
- exposes an `extract_*` method returning a *raw* feature vector (dict + numpy array)
- exposes a `normalize` method mapping features into [0, 1]
- exposes a `test` classmethod for quick smoke-testing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np

from config.constants import (
    BoundaryCondition,
    Dimension,
    HardwareType,
    Linearity,
    RequirementLevel,
    Stationarity,
    COMPUTE_TFLOPS_THRESHOLD,
    RESOURCE_CONSUMPTION_THRESHOLD,
    VRAM_GB_THRESHOLD,
)


class FeatureExtractionError(ValueError):
    """Raised when feature extraction or validation fails."""


# =========================
# Utility helpers
# =========================


def _to_requirement_level(x: Union[str, RequirementLevel]) -> RequirementLevel:
    """Map user input to `RequirementLevel`, with basic validation."""
    if isinstance(x, RequirementLevel):
        return x
    v = str(x).strip().lower()
    mapping = {
        "high": RequirementLevel.HIGH,
        "h": RequirementLevel.HIGH,
        "中": RequirementLevel.MEDIUM,
        "medium": RequirementLevel.MEDIUM,
        "m": RequirementLevel.MEDIUM,
        "low": RequirementLevel.LOW,
        "l": RequirementLevel.LOW,
    }
    if v in mapping:
        return mapping[v]
    raise FeatureExtractionError(f"无效的需求等级: {x!r}，请使用 high/medium/low 或 对应中文/首字母。")


def _level_to_scalar(level: RequirementLevel) -> float:
    """Map RequirementLevel to a monotone scalar in [0, 1]."""
    if level == RequirementLevel.LOW:
        return 0.0
    if level == RequirementLevel.MEDIUM:
        return 0.5
    return 1.0


def _safe_min_max_norm(val: float, vmin: float, vmax: float) -> float:
    """Normalize `val` to [0,1] given [vmin, vmax], with safeguards."""
    if vmax <= vmin:
        return 0.0
    return float(max(0.0, min(1.0, (val - vmin) / (vmax - vmin))))


# =========================
# Physics feature extractor
# =========================


@dataclass
class PhysicsFeatures:
    dimension: Dimension
    linearity: Linearity
    stationarity: Stationarity
    boundary_condition: BoundaryCondition
    problem_size: int  # e.g. degrees of freedom / grid points


class PhysicsFeatureExtractor:
    """Extract physics/PDE features from text or structured parameters."""

    @staticmethod
    def _validate_dimension(dim: int) -> Dimension:
        if dim not in (1, 2, 3):
            raise FeatureExtractionError(f"维度必须是 1/2/3，当前为: {dim}")
        return Dimension(dim)

    @staticmethod
    def _parse_structured(params: Dict[str, Any]) -> PhysicsFeatures:
        """Parse physics parameters from a structured dict."""
        try:
            dim = PhysicsFeatureExtractor._validate_dimension(int(params.get("dimension", 0)))
        except Exception as e:  # noqa: BLE001
            raise FeatureExtractionError(f"解析维度失败: {e}") from e

        lin_raw = params.get("linearity", 0)
        if isinstance(lin_raw, Linearity):
            linearity = lin_raw
        else:
            try:
                linearity = Linearity(int(lin_raw))
            except Exception as e:  # noqa: BLE001
                raise FeatureExtractionError("线性类型(linearity)只能是 0(线性) 或 1(非线性)。") from e

        sta_raw = params.get("stationarity", 0)
        if isinstance(sta_raw, Stationarity):
            stationarity = sta_raw
        else:
            try:
                stationarity = Stationarity(int(sta_raw))
            except Exception as e:  # noqa: BLE001
                raise FeatureExtractionError("定常类型(stationarity)只能是 0(定常) 或 1(非定常)。") from e

        bc_raw = params.get("boundary_condition")
        try:
            if isinstance(bc_raw, BoundaryCondition):
                boundary = bc_raw
            else:
                v = str(bc_raw or "").strip().lower()
                mapping = {
                    "dirichlet": BoundaryCondition.DIRICHLET,
                    "d": BoundaryCondition.DIRICHLET,
                    "neumann": BoundaryCondition.NEUMANN,
                    "n": BoundaryCondition.NEUMANN,
                    "mixed": BoundaryCondition.MIXED,
                    "m": BoundaryCondition.MIXED,
                }
                boundary = mapping[v]
        except Exception as e:  # noqa: BLE001
            raise FeatureExtractionError("边界条件必须是 dirichlet/neumann/mixed(或首字母)。") from e

        try:
            problem_size = int(params.get("problem_size", 0))
        except Exception as e:  # noqa: BLE001
            raise FeatureExtractionError("problem_size 必须是正整数。") from e
        if problem_size <= 0:
            raise FeatureExtractionError("problem_size 必须是正整数（例如网格点数、自由度数）。")

        return PhysicsFeatures(
            dimension=dim,
            linearity=linearity,
            stationarity=stationarity,
            boundary_condition=boundary,
            problem_size=problem_size,
        )

    @classmethod
    def extract_from_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract physics features from a structured parameter dict."""
        pf = cls._parse_structured(params)
        # Raw vector (not yet normalized); ordering is consistent across extractors.
        vec = np.array(
            [
                int(pf.dimension),  # 1/2/3
                int(pf.linearity),  # 0/1
                int(pf.stationarity),  # 0/1
                {"dirichlet": 0, "neumann": 0.5, "mixed": 1.0}[pf.boundary_condition.value],
                float(pf.problem_size),
            ],
            dtype=float,
        )
        return {
            "features": pf,
            "vector": vec,
        }

    @staticmethod
    def normalize(vec: np.ndarray) -> np.ndarray:
        """Normalize physics feature vector into [0,1]."""
        if vec.shape[0] != 5:
            raise FeatureExtractionError("Physics 特征向量长度必须为 5。")

        dim = _safe_min_max_norm(vec[0], 1.0, 3.0)
        linearity = vec[1]  # already 0/1
        stationarity = vec[2]  # already 0/1
        bc = _safe_min_max_norm(vec[3], 0.0, 1.0)
        # problem size: heuristic range [1e3, 1e7]
        problem_size = _safe_min_max_norm(vec[4], 1e3, 1e7)
        return np.array([dim, linearity, stationarity, bc, problem_size], dtype=float)

    @classmethod
    def test(cls) -> None:
        """Simple test-case runnable in isolation."""
        params = {
            "dimension": 2,
            "linearity": 0,
            "stationarity": 1,
            "boundary_condition": "dirichlet",
            "problem_size": 100_000,
        }
        out = cls.extract_from_params(params)
        norm = cls.normalize(out["vector"])
        print("Physics raw:", out["vector"])
        print("Physics norm:", norm)


# =========================
# Hardware feature extractor
# =========================


@dataclass
class HardwareFeatures:
    hardware_type: HardwareType
    cpu_cores: int
    compute_tflops_est: float
    vram_gb: float
    parallel_mode: float  # scalar in [0,1], more parallelism -> closer to 1


class HardwareFeatureExtractor:
    """Extract hardware features using torch + cpuinfo when available."""

    @staticmethod
    def _estimate_cpu_tflops(cores: int, base_freq_ghz: float) -> float:
        """Very rough CPU TFLOPs estimate.

        This is intentionally approximate; it is only used for *ordering* devices,
        not for precise benchmarking.
        """
        if cores <= 0 or base_freq_ghz <= 0:
            return 0.0
        # Assume ~16 FLOPs per cycle per core as a generous upper bound for modern CPUs.
        return float(cores * base_freq_ghz * 1e3 * 16) / 1e6  # = cores * freq(GHz) * 16 [TFLOPs approx]

    @staticmethod
    def _get_cpu_info() -> Tuple[int, float]:
        """Return (logical_cores, base_freq_ghz)."""
        import os

        cores = int(os.cpu_count() or 0)
        base_freq_ghz = 0.0
        try:
            import cpuinfo  # type: ignore

            info = cpuinfo.get_cpu_info()
            hz = info.get("hz_advertised_raw") or info.get("hz_advertised")
            if isinstance(hz, (tuple, list)) and len(hz) >= 1:
                base_freq_ghz = float(hz[0]) / 1e9
            elif isinstance(hz, (int, float)):
                base_freq_ghz = float(hz) / 1e9
        except Exception:
            # Fallback: leave base_freq_ghz as 0; normalized later.
            base_freq_ghz = 0.0
        return cores, base_freq_ghz

    @staticmethod
    def _get_gpu_info() -> Tuple[Optional[str], float, bool]:
        """Return (name, vram_gb, cuda_available).

        Uses torch.cuda APIs; if torch is not installed or no CUDA is available,
        returns (None, 0.0, False) instead of raising.
        """
        try:
            import torch  # type: ignore
        except Exception:
            return None, 0.0, False

        if not torch.cuda.is_available():
            return None, 0.0, False

        try:
            idx = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(idx)
            name = props.name
            # total_memory is in bytes
            vram_gb = float(props.total_memory) / (1024**3)
            return str(name), vram_gb, True
        except Exception:
            return None, 0.0, False

    @classmethod
    def extract(cls) -> Dict[str, Any]:
        """Detect hardware runtime environment and return raw feature vector.

        Raises:
            FeatureExtractionError: when even basic CPU detection fails.
        """
        cores, base_freq = cls._get_cpu_info()
        if cores <= 0:
            raise FeatureExtractionError(
                "无法检测 CPU 核心数。请检查 Python 运行环境，或在容器/沙箱中打开 CPU 查询权限。"
            )

        cpu_tflops = cls._estimate_cpu_tflops(cores, base_freq)
        gpu_name, vram_gb, cuda_ok = cls._get_gpu_info()

        if cuda_ok and vram_gb > 0:
            hw_type = HardwareType.GPU
            parallel_mode = 1.0
        else:
            hw_type = HardwareType.CPU
            parallel_mode = 0.3  # some degree of CPU parallelism

        hf = HardwareFeatures(
            hardware_type=hw_type,
            cpu_cores=cores,
            compute_tflops_est=cpu_tflops,
            vram_gb=vram_gb,
            parallel_mode=parallel_mode,
        )

        # Vector: [hw_type_scalar, cores, tflops_est, vram_gb, parallel_mode]
        hw_scalar = {
            HardwareType.CPU: 0.0,
            HardwareType.GPU: 0.7,
            HardwareType.HETEROGENEOUS: 1.0,
        }[hw_type]

        vec = np.array(
            [
                hw_scalar,
                float(hf.cpu_cores),
                float(hf.compute_tflops_est),
                float(hf.vram_gb),
                float(hf.parallel_mode),
            ],
            dtype=float,
        )

        return {"features": hf, "vector": vec, "gpu_name": gpu_name}

    @staticmethod
    def normalize(vec: np.ndarray) -> np.ndarray:
        """Normalize hardware feature vector into [0,1]."""
        if vec.shape[0] != 5:
            raise FeatureExtractionError("Hardware 特征向量长度必须为 5。")

        hw_type = _safe_min_max_norm(vec[0], 0.0, 1.0)
        # heuristic: assume cores in [2, 64]
        cores = _safe_min_max_norm(vec[1], 2.0, 64.0)
        # use COMPUTE_TFLOPS_THRESHOLD as a soft cap
        tflops = _safe_min_max_norm(vec[2], 0.0, max(1.0, COMPUTE_TFLOPS_THRESHOLD))
        vram = _safe_min_max_norm(vec[3], 0.0, max(1.0, VRAM_GB_THRESHOLD * 2))
        parallel_mode = _safe_min_max_norm(vec[4], 0.0, 1.0)
        return np.array([hw_type, cores, tflops, vram, parallel_mode], dtype=float)

    @classmethod
    def test(cls) -> None:
        """Simple hardware detection smoke-test."""
        out = cls.extract()
        norm = cls.normalize(out["vector"])
        print("Hardware raw:", out["vector"])
        print("Hardware norm:", norm)
        print("GPU name:", out.get("gpu_name") or "None/CPU only")


# =========================
# Domain feature extractor
# =========================


@dataclass
class DomainFeatures:
    accuracy: RequirementLevel
    realtime: RequirementLevel
    resource_budget: float  # 0-1, lower = more strict


class DomainFeatureExtractor:
    """Extract domain-level requirement features."""

    @classmethod
    def extract_from_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract domain requirement features from a structured dict."""
        acc = _to_requirement_level(params.get("accuracy"))
        rt = _to_requirement_level(params.get("realtime"))

        rb = params.get("resource_budget", RESOURCE_CONSUMPTION_THRESHOLD)
        try:
            rb_f = float(rb)
        except Exception as e:  # noqa: BLE001
            raise FeatureExtractionError("resource_budget 必须是 0-1 之间的数值。") from e
        if not (0.0 < rb_f <= 1.0):
            raise FeatureExtractionError("resource_budget 必须在 (0,1] 区间内，1 表示资源充足，值越小约束越强。")

        df = DomainFeatures(accuracy=acc, realtime=rt, resource_budget=rb_f)
        vec = np.array(
            [
                _level_to_scalar(df.accuracy),
                _level_to_scalar(df.realtime),
                df.resource_budget,
            ],
            dtype=float,
        )
        return {"features": df, "vector": vec}

    @staticmethod
    def normalize(vec: np.ndarray) -> np.ndarray:
        """Normalize domain feature vector into [0,1]."""
        if vec.shape[0] != 3:
            raise FeatureExtractionError("Domain 特征向量长度必须为 3。")
        # All components are already between 0 and 1 by construction.
        return np.clip(vec.astype(float), 0.0, 1.0)

    @classmethod
    def test(cls) -> None:
        """Domain feature extraction test-case."""
        params = {"accuracy": "high", "realtime": "medium", "resource_budget": 0.6}
        out = cls.extract_from_params(params)
        norm = cls.normalize(out["vector"])
        print("Domain raw:", out["vector"])
        print("Domain norm:", norm)


if __name__ == "__main__":
    # Quick manual tests when running this module directly.
    print("=== PhysicsFeatureExtractor test ===")
    PhysicsFeatureExtractor.test()
    print("\n=== HardwareFeatureExtractor test ===")
    HardwareFeatureExtractor.test()
    print("\n=== DomainFeatureExtractor test ===")
    DomainFeatureExtractor.test()

