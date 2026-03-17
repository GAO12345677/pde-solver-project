"""Hardware detection utilities (Windows-friendly).

This module is intentionally defensive:
- If optional dependencies are missing or drivers are not installed, it still returns
  useful CPU-only information and a clear error field for GPU detection.

Dependencies:
- py-cpuinfo
-(optional) pynvml (NVIDIA Management Library wrapper)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class GpuInfo:
    name: str
    vram_total_gb: float
    driver_version: Optional[str] = None


@dataclass
class HardwareInfo:
    cpu_brand: Optional[str]
    cpu_count_logical: int
    gpu: Optional[GpuInfo]
    gpu_error: Optional[str] = None


def detect_cpu() -> Dict[str, Any]:
    """Return basic CPU info using py-cpuinfo when available."""
    cpu_brand = None
    try:
        import cpuinfo  # type: ignore

        info = cpuinfo.get_cpu_info()
        cpu_brand = info.get("brand_raw") or info.get("brand") or info.get("arch_string_raw")
    except Exception:
        # Keep it minimal; downstream can still read os.cpu_count().
        cpu_brand = None
    return {"cpu_brand": cpu_brand}


def detect_gpu() -> Dict[str, Any]:
    """Return basic GPU info using pynvml when available.

    If NVML isn't installed, drivers are missing, or the machine has no NVIDIA GPU,
    returns {"gpu": None, "gpu_error": "..."} instead of raising.
    """
    try:
        from pynvml import (  # type: ignore
            nvmlInit,
            nvmlShutdown,
            nvmlDeviceGetCount,
            nvmlDeviceGetHandleByIndex,
            nvmlDeviceGetName,
            nvmlDeviceGetMemoryInfo,
            nvmlSystemGetDriverVersion,
        )

        nvmlInit()
        try:
            count = nvmlDeviceGetCount()
            if count < 1:
                return {"gpu": None, "gpu_error": "No NVIDIA GPU detected (NVML count=0)."}

            # Use the first GPU for a simple baseline.
            handle = nvmlDeviceGetHandleByIndex(0)
            name = nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="ignore")
            mem = nvmlDeviceGetMemoryInfo(handle)
            vram_total_gb = float(mem.total) / (1024**3)
            driver = nvmlSystemGetDriverVersion()
            if isinstance(driver, bytes):
                driver = driver.decode("utf-8", errors="ignore")

            return {
                "gpu": {
                    "name": str(name),
                    "vram_total_gb": round(vram_total_gb, 3),
                    "driver_version": str(driver),
                },
                "gpu_error": None,
            }
        finally:
            nvmlShutdown()
    except Exception as e:
        return {"gpu": None, "gpu_error": f"GPU detection unavailable: {e.__class__.__name__}: {e}"}


def detect_hardware() -> HardwareInfo:
    """Detect CPU and (optional) GPU information."""
    import os

    cpu = detect_cpu()
    gpu = detect_gpu()
    gpu_obj = None
    if gpu.get("gpu"):
        g = gpu["gpu"]
        gpu_obj = GpuInfo(
            name=str(g.get("name", "")),
            vram_total_gb=float(g.get("vram_total_gb", 0.0)),
            driver_version=g.get("driver_version"),
        )

    return HardwareInfo(
        cpu_brand=cpu.get("cpu_brand"),
        cpu_count_logical=int(os.cpu_count() or 0),
        gpu=gpu_obj,
        gpu_error=gpu.get("gpu_error"),
    )


def hardware_info_dict() -> Dict[str, Any]:
    """Serialize `HardwareInfo` to a JSON-friendly dict."""
    info = detect_hardware()
    d = asdict(info)
    return d

