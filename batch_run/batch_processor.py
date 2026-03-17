"""Unattended batch processing for the adaptive solver-selection framework.

Features:
1) Batch processing:
   - Reads JSON configs from input/ directory
   - Runs: feature extraction -> algorithm selection -> equation solving -> result evaluation
   - Saves outputs to output/ (solution + evaluation report + visualization)
2) Scheduling:
   - Uses schedule to run daily at 02:00 by default (customizable)
3) Logging:
   - Writes logs to log/YYYY-MM-DD.log (start/end, success/failure cases)
   - Exceptions are recorded with actionable hints
4) Folder monitoring:
   - Uses watchdog to watch input/ for new JSON files and triggers processing
5) Windows-friendly background usage:
   - Can be run with pythonw for no-console background
   - Can be registered to auto-start via Windows Task Scheduler (see docs)

Run examples (PowerShell, in project root):
  python -m batch_run.batch_processor --once
  python -m batch_run.batch_processor --watch
  python -m batch_run.batch_processor --schedule --at 02:00
  python -m batch_run.batch_processor --watch --schedule --at 02:00

Notes:
- This module calls the same internal components as the API layer, so its behavior
  matches Swagger/Redoc debugging.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from algorithm.selector import AlgorithmSelector, AlgorithmSelectionError, concat_features
from config.constants import BoundaryCondition, RequirementLevel
from feature.extractor import (
    DomainFeatureExtractor,
    FeatureExtractionError,
    HardwareFeatureExtractor,
    PhysicsFeatureExtractor,
)
from feedback.evaluator import FeedbackError, ModelOptimizer, ResultEvaluator
from solver.numerical_solver import BoundarySpec, Heat1DParams, SolverError, get_solver, solve_poisson2d_nonlinear


INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
LOG_DIR = Path("log")
RESULT_DIR = Path("result")


# ---------- logging ----------


def _setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = LOG_DIR / f"{today}.log"

    logger = logging.getLogger("batch_processor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            raise ValueError("JSON must be an object.")
        return obj
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"配置文件解析失败 {path.name}: {e}") from e


def _safe_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _save_plot_heat1d(x: np.ndarray, u: np.ndarray, out_png: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")  # headless-safe
    import matplotlib.pyplot as plt

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 4))
    plt.plot(x, u, linewidth=2)
    plt.title("Heat1D Solution")
    plt.xlabel("x")
    plt.ylabel("u(x)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()


def _save_plot_poisson2d(u2d: np.ndarray, out_png: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 5))
    plt.imshow(u2d, origin="lower", cmap="viridis", aspect="auto")
    plt.colorbar(label="u")
    plt.title("Poisson2D Nonlinear Solution")
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()


# ---------- core pipeline ----------


@dataclass
class BatchResult:
    config_file: str
    success: bool
    error: Optional[str]
    outputs: Dict[str, str]
    elapsed_s: float


def _parse_level(x: Any, field: str) -> RequirementLevel:
    try:
        if isinstance(x, RequirementLevel):
            return x
        return RequirementLevel(str(x).strip().lower())
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"{field} 必须是 high/medium/low。") from e


def run_single_config(
    cfg: Dict[str, Any],
    *,
    selector: AlgorithmSelector,
    evaluator: ResultEvaluator,
    optimizer: ModelOptimizer,
    logger: logging.Logger,
    config_name: str,
) -> BatchResult:
    """Run the full pipeline on a single config dict."""
    start = time.perf_counter()
    out_paths: Dict[str, str] = {}
    try:
        equation_type = str(cfg.get("equation_type", "heat1d")).strip().lower()
        domain_cfg = cfg.get("domain", {}) if isinstance(cfg.get("domain", {}), dict) else {}

        accuracy = _parse_level(domain_cfg.get("accuracy", "medium"), "domain.accuracy")
        realtime = _parse_level(domain_cfg.get("realtime", "medium"), "domain.realtime")
        resource_budget = float(domain_cfg.get("resource_budget", 0.75))

        # ---- feature extraction ----
        if equation_type == "heat1d":
            nx = int(cfg.get("nx", 101))
            bc_name = str(cfg.get("boundary_condition", "dirichlet")).strip().lower()
            physics_raw = PhysicsFeatureExtractor.extract_from_params(
                {"dimension": 1, "linearity": 0, "stationarity": 1, "boundary_condition": bc_name, "problem_size": nx}
            )
        elif equation_type == "poisson2d_nonlinear":
            nx = int(cfg.get("nx", 41))
            ny = int(cfg.get("ny", 41))
            bc_name = str(cfg.get("boundary_condition", "dirichlet")).strip().lower()
            physics_raw = PhysicsFeatureExtractor.extract_from_params(
                {
                    "dimension": 2,
                    "linearity": 1,
                    "stationarity": 0,
                    "boundary_condition": bc_name,
                    "problem_size": nx * ny,
                }
            )
        else:
            raise ValueError("equation_type 必须是 heat1d 或 poisson2d_nonlinear。")

        physics = PhysicsFeatureExtractor.normalize(physics_raw["vector"])
        hw_raw = HardwareFeatureExtractor.extract()
        hardware = HardwareFeatureExtractor.normalize(hw_raw["vector"])
        domain_raw = DomainFeatureExtractor.extract_from_params(
            {"accuracy": accuracy, "realtime": realtime, "resource_budget": resource_budget}
        )
        domain = DomainFeatureExtractor.normalize(domain_raw["vector"])
        x13 = concat_features(physics, hardware, domain)

        # ---- algorithm selection ----
        strategy = str(cfg.get("strategy", "static_rf")).strip().lower()
        if strategy not in ("static_rf", "static_xgb", "dynamic_rl"):
            raise ValueError("strategy 必须是 static_rf/static_xgb/dynamic_rl。")

        # Auto-train/load (offline friendly)
        if strategy in ("static_rf", "static_xgb") and selector.static_model is None:
            selector.train_static(strategy=strategy)
            selector.save_static()
        if strategy == "dynamic_rl" and selector.rl_agent is None:
            selector.train_dynamic(episodes=int(cfg.get("rl_episodes", 120)))
            selector.save_dynamic()

        # DEBUG_BREAKPOINT_BATCH_SELECT: set breakpoint here.
        selection = selector.select(physics=physics, hardware=hardware, domain=domain, strategy=strategy)  # type: ignore[arg-type]
        alg_key = selection["algorithm_key"]

        # ---- equation solving ----
        if equation_type == "heat1d":
            k = float(cfg.get("k", 1.0))
            L = float(cfg.get("L", 1.0))
            t0 = float(cfg.get("t0", 0.0))
            t1 = float(cfg.get("t1", 0.05))
            nx = int(cfg.get("nx", 101))
            bc_type = BoundaryCondition(str(cfg.get("bc_type", "dirichlet")).strip().lower())
            left_bc = float(cfg.get("left_bc", 0.0))
            right_bc = float(cfg.get("right_bc", 0.0))
            enforce_nonneg = bool(cfg.get("enforce_nonnegativity", True))

            params = Heat1DParams(k=k, L=L, nx=nx, t_span=(t0, t1), enforce_nonnegativity=enforce_nonneg)
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

            initial_kind = str(cfg.get("initial", "sine_nonnegative")).strip().lower()

            def initial_fn(x: np.ndarray) -> np.ndarray:
                if initial_kind == "constant":
                    return np.full_like(x, 1.0, dtype=float)
                return np.maximum(0.0, np.sin(np.pi * x / float(L)))

            solver = get_solver(alg_key)
            u, solve_info, validation = solver.solve(params=params, bc=bc, initial=initial_fn)

            # Save solution + plot
            x = np.linspace(0.0, L, nx, dtype=float)
            stem = Path(config_name).stem
            sol_path = OUTPUT_DIR / f"{stem}_solution.json"
            plot_path = OUTPUT_DIR / f"{stem}_plot.png"
            _safe_write_json(sol_path, {"x": x.tolist(), "u": u.tolist(), "shape": [nx]})
            _save_plot_heat1d(x, u, plot_path)
            out_paths["solution_json"] = str(sol_path)
            out_paths["plot_png"] = str(plot_path)

            solve_info_dict = solve_info.__dict__

        else:
            # 2D nonlinear Poisson demo (solver algorithm is fixed baseline FDM internally)
            nx = int(cfg.get("nx", 41))
            ny = int(cfg.get("ny", 41))
            Lx = float(cfg.get("Lx", 1.0))
            Ly = float(cfg.get("Ly", 1.0))
            tol = float(cfg.get("tol", 1e-6))
            max_iter = int(cfg.get("max_iter", 200))
            u2d, solve_info_dict = solve_poisson2d_nonlinear(nx=nx, ny=ny, Lx=Lx, Ly=Ly, tol=tol, max_iter=max_iter)
            validation = {"finite": bool(np.all(np.isfinite(u2d))), "nonnegative": bool(np.min(u2d) >= -1e-12), "bc_satisfied": True, "notes": []}

            stem = Path(config_name).stem
            sol_path = OUTPUT_DIR / f"{stem}_solution.json"
            plot_path = OUTPUT_DIR / f"{stem}_plot.png"
            _safe_write_json(sol_path, {"u": u2d.reshape(-1).tolist(), "shape": [ny, nx]})
            _save_plot_poisson2d(u2d, plot_path)
            out_paths["solution_json"] = str(sol_path)
            out_paths["plot_png"] = str(plot_path)

        # ---- result evaluation + optional self-optimization ----
        report = evaluator.evaluate(
            solution=np.array((u if equation_type == "heat1d" else u2d.reshape(-1)), dtype=float),
            solve_info=solve_info_dict,
            domain_requirements={"accuracy": accuracy, "realtime": realtime, "resource_budget": resource_budget},
            validation=validation,
        )
        report_path = evaluator.save_report(report, result_dir=str(RESULT_DIR))
        out_paths["evaluation_report_json"] = str(report_path)

        # Optimization feedback (append sample + retrain)
        try:
            optimizer.append_training_sample(x13=x13, algorithm_key=alg_key)
            optimizer.retrain_static_with_feedback(strategy="static_rf")
        except Exception as e:  # noqa: BLE001
            logger.warning("ModelOptimizer skipped/failed: %s", e)

        elapsed = time.perf_counter() - start
        logger.info("Processed %s OK (strategy=%s, alg=%s, %.3fs)", config_name, strategy, alg_key, elapsed)
        return BatchResult(config_file=config_name, success=True, error=None, outputs=out_paths, elapsed_s=float(elapsed))

    except (FeatureExtractionError, AlgorithmSelectionError, SolverError, FeedbackError, ValueError) as e:
        elapsed = time.perf_counter() - start
        msg = (
            f"{e}\n"
            "排查建议：\n"
            "- 检查 input JSON 字段是否完整/类型正确\n"
            "- 检查 Python 依赖是否已安装：pip install -r requirements.txt\n"
            "- 若 GPU 检测失败可忽略（CPU 模式仍可运行）\n"
        )
        logger.error("Processed %s FAIL (%.3fs): %s", config_name, elapsed, msg)
        return BatchResult(config_file=config_name, success=False, error=str(e), outputs=out_paths, elapsed_s=float(elapsed))


def process_input_folder(*, logger: logging.Logger) -> Dict[str, Any]:
    """Batch-process all JSON configs in input/ and write outputs."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    selector = AlgorithmSelector(model_dir="model")
    evaluator = ResultEvaluator()
    optimizer = ModelOptimizer(model_dir="model", feedback_dir=str(RESULT_DIR))

    configs = sorted([p for p in INPUT_DIR.glob("*.json") if p.is_file()])
    logger.info("Batch start: %d config(s) in %s", len(configs), str(INPUT_DIR))

    start = time.perf_counter()
    results: List[Dict[str, Any]] = []
    ok = 0
    fail = 0
    for p in configs:
        cfg = _read_json(p)
        r = run_single_config(
            cfg,
            selector=selector,
            evaluator=evaluator,
            optimizer=optimizer,
            logger=logger,
            config_name=p.name,
        )
        results.append(
            {
                "config_file": r.config_file,
                "success": r.success,
                "error": r.error,
                "outputs": r.outputs,
                "elapsed_s": r.elapsed_s,
            }
        )
        ok += 1 if r.success else 0
        fail += 0 if r.success else 1

    elapsed = float(time.perf_counter() - start)
    summary = {"total": len(configs), "success": ok, "failed": fail, "elapsed_s": elapsed, "results": results}
    logger.info("Batch end: success=%d failed=%d elapsed=%.3fs", ok, fail, elapsed)

    # Save batch summary to output/
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = OUTPUT_DIR / f"batch_summary_{ts}.json"
    _safe_write_json(summary_path, summary)
    return {"summary": summary, "summary_path": str(summary_path)}


# ---------- scheduling & watching ----------


def start_schedule(at_time: str, *, logger: logging.Logger) -> None:
    """Start daily schedule runner."""
    try:
        import schedule  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("缺少 schedule 依赖，请执行 pip install -r requirements.txt") from e

    logger.info("Scheduling enabled: daily at %s", at_time)
    schedule.clear()
    schedule.every().day.at(at_time).do(lambda: process_input_folder(logger=logger))

    while True:
        schedule.run_pending()
        time.sleep(1.0)


def start_watch(*, logger: logging.Logger, debounce_s: float = 1.5) -> None:
    """Watch input/ for new JSON files and trigger processing."""
    try:
        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("缺少 watchdog 依赖，请执行 pip install -r requirements.txt") from e

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Watching enabled: %s", str(INPUT_DIR))

    last_trigger = {"t": 0.0}

    class Handler(FileSystemEventHandler):
        def on_created(self, event):  # type: ignore[no-untyped-def]
            if getattr(event, "is_directory", False):
                return
            p = Path(getattr(event, "src_path", ""))
            if p.suffix.lower() != ".json":
                return
            now = time.time()
            if now - last_trigger["t"] < debounce_s:
                return
            last_trigger["t"] = now
            logger.info("New config detected: %s -> trigger batch", p.name)
            process_input_folder(logger=logger)

    observer = Observer()
    observer.schedule(Handler(), str(INPUT_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1.0)
    finally:
        observer.stop()
        observer.join(timeout=5)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Unattended batch processor")
    parser.add_argument("--once", action="store_true", help="Run batch once and exit")
    parser.add_argument("--schedule", action="store_true", help="Enable daily schedule runner")
    parser.add_argument("--at", default="02:00", help="Schedule time HH:MM (default 02:00)")
    parser.add_argument("--watch", action="store_true", help="Watch input/ for new configs and trigger")
    args = parser.parse_args(argv)

    logger = _setup_logger()
    logger.info("Batch processor started (pid=%s)", os.getpid())

    if args.once:
        process_input_folder(logger=logger)
        return 0

    # If both watch and schedule are enabled, run schedule in main thread and watcher in a daemon thread.
    if args.watch and args.schedule:
        import threading

        t = threading.Thread(target=start_watch, kwargs={"logger": logger}, daemon=True)
        t.start()
        start_schedule(args.at, logger=logger)
        return 0

    if args.watch:
        start_watch(logger=logger)
        return 0

    if args.schedule:
        start_schedule(args.at, logger=logger)
        return 0

    # Default: show help-like guidance
    logger.info("No mode selected. Use --once / --watch / --schedule.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

