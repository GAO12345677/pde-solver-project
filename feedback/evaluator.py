"""Result feedback & model optimization layer.

Implements:
- ResultEvaluator: multi-objective evaluation (accuracy, speed, time, resource, robustness)
- ModelOptimizer : self-optimization loop hook (append samples, retrain/retune models)

This is an executable baseline that fits the paper's architecture and is intended
to be replaced with domain-specific measurement and online-learning logic.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from algorithm.selector import AlgorithmSelector, AlgorithmSelectionError, build_typical_case_dataset
from config.constants import RequirementLevel


class FeedbackError(ValueError):
    """Raised when evaluation/feedback data is invalid."""


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _level_to_target(level: RequirementLevel, low: float, mid: float, high: float) -> float:
    if level == RequirementLevel.LOW:
        return low
    if level == RequirementLevel.MEDIUM:
        return mid
    return high


@dataclass
class EvaluationReport:
    """Structured evaluation report; will be serialized to JSON."""

    timestamp: float
    selected_algorithm: str
    metrics: Dict[str, float]
    pass_fail: Dict[str, bool]
    notes: List[str]
    context: Dict[str, Any]


class ResultEvaluator:
    """Evaluate solver outputs under multi-objective criteria."""

    def evaluate(
        self,
        solution: np.ndarray,
        solve_info: Dict[str, Any],
        domain_requirements: Dict[str, Any],
        validation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute evaluation metrics and return a report dict.

        Inputs:
        - solution: ndarray of solution values (e.g. temperature field)
        - solve_info: dict including elapsed_s / estimated_error / resource_proxy etc.
        - domain_requirements: {accuracy, realtime, resource_budget}
        - validation: optional dict from solver validate_solution()
        """
        if solution is None:
            raise FeedbackError("solution 不能为空。")
        u = np.asarray(solution, dtype=float).reshape(-1)
        if u.size < 5:
            raise FeedbackError("solution 太短，无法评估。")
        if not np.all(np.isfinite(u)):
            raise FeedbackError("solution 包含 NaN/Inf，无法评估。")

        elapsed = float(solve_info.get("elapsed_s", 0.0) or 0.0)
        resource = float(solve_info.get("resource_proxy", 0.0) or 0.0)
        est_err = solve_info.get("estimated_error", None)
        est_err_f = float(est_err) if est_err is not None else float(np.std(u) * 1e-3)  # proxy

        try:
            acc_level = domain_requirements.get("accuracy")
            rt_level = domain_requirements.get("realtime")
            if not isinstance(acc_level, RequirementLevel):
                acc_level = RequirementLevel(str(acc_level).strip().lower())
            if not isinstance(rt_level, RequirementLevel):
                rt_level = RequirementLevel(str(rt_level).strip().lower())
        except Exception as e:  # noqa: BLE001
            raise FeedbackError(f"领域需求参数不合法(accuracy/realtime): {e}") from e

        resource_budget = domain_requirements.get("resource_budget", 0.75)
        try:
            resource_budget = float(resource_budget)
        except Exception as e:  # noqa: BLE001
            raise FeedbackError("resource_budget 必须为数值。") from e

        # Targets derived from domain requirements (proxy thresholds)
        # - accuracy: error threshold
        err_target = _level_to_target(acc_level, low=5e-2, mid=1e-2, high=1e-3)
        # - realtime: time threshold (seconds)
        time_target = _level_to_target(rt_level, low=5.0, mid=1.0, high=0.2)

        # Metrics (all mapped to [0,1], higher is better)
        accuracy_metric = float(np.clip(1.0 - (est_err_f / max(err_target, 1e-12)), 0.0, 1.0))
        time_metric = float(np.clip(1.0 - (elapsed / max(time_target, 1e-6)), 0.0, 1.0))
        resource_metric = float(np.clip(1.0 - (resource / max(resource_budget, 1e-6)), 0.0, 1.0))

        # Robustness proxy: penalize large negative values or extreme gradients
        min_u = float(np.min(u))
        grad = np.gradient(u)
        grad_max = float(np.max(np.abs(grad)))
        robustness_metric = 1.0
        if min_u < -1e-6:
            robustness_metric -= 0.5
        if grad_max > 1e6:
            robustness_metric -= 0.5
        robustness_metric = float(np.clip(robustness_metric, 0.0, 1.0))

        # Convergence speed proxy: use nfev and elapsed together if available
        nfev = float(solve_info.get("nfev", 0) or 0)
        convergence_metric = float(np.clip(1.0 - (nfev / 2000.0), 0.0, 1.0))

        notes: List[str] = []
        if validation:
            if not validation.get("finite", True):
                notes.append("数值不稳定：出现 NaN/Inf。")
            if not validation.get("bc_satisfied", True):
                notes.append("边界条件未满足。")
            if not validation.get("nonnegative", True):
                notes.append("违反非负物理约束（如温度应非负）。")
            notes.extend([str(n) for n in validation.get("notes", []) if n])

        metrics = {
            "accuracy": accuracy_metric,
            "convergence": convergence_metric,
            "time_efficiency": time_metric,
            "resource_efficiency": resource_metric,
            "robustness": robustness_metric,
        }

        # A simple weighted objective (paper-inspired)
        total = float(
            np.clip(
                0.30 * metrics["accuracy"]
                + 0.20 * metrics["convergence"]
                + 0.20 * metrics["time_efficiency"]
                + 0.20 * metrics["resource_efficiency"]
                + 0.10 * metrics["robustness"],
                0.0,
                1.0,
            )
        )
        metrics["total"] = total

        pass_fail = {
            "accuracy_ok": est_err_f <= err_target,
            "time_ok": elapsed <= time_target,
            "resource_ok": resource <= resource_budget,
        }

        report = EvaluationReport(
            timestamp=time.time(),
            selected_algorithm=str(solve_info.get("algorithm") or ""),
            metrics=metrics,
            pass_fail=pass_fail,
            notes=notes,
            context={
                "estimated_error": float(est_err_f),
                "error_target": float(err_target),
                "elapsed_s": float(elapsed),
                "time_target_s": float(time_target),
                "resource_proxy": float(resource),
                "resource_budget": float(resource_budget),
            },
        )
        return asdict(report)

    def save_report(self, report: Dict[str, Any], result_dir: str = "result") -> str:
        """Save report JSON to result/ directory."""
        if not isinstance(report, dict):
            raise FeedbackError("report 必须是 dict。")
        _ensure_dir(result_dir)
        ts = report.get("timestamp", time.time())
        fname = f"report_{int(float(ts))}.json"
        path = os.path.join(result_dir, fname)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            raise FeedbackError(f"保存评估报告失败: {e}") from e
        return path


class ModelOptimizer:
    """Use evaluation feedback to update the selection model (self-optimization hook)."""

    def __init__(self, model_dir: str = "model", feedback_dir: str = "result") -> None:
        self.model_dir = model_dir
        self.feedback_dir = feedback_dir
        _ensure_dir(self.model_dir)
        _ensure_dir(self.feedback_dir)
        self.selector = AlgorithmSelector(model_dir=self.model_dir)

    def append_training_sample(
        self,
        x13: np.ndarray,
        algorithm_key: str,
        filename: str = "feedback_samples.npz",
    ) -> str:
        """Append a new (feature->label) sample for later offline retraining."""
        x = np.asarray(x13, dtype=np.float32).reshape(-1)
        if x.shape[0] != 13:
            raise FeedbackError("反馈样本特征向量必须为 13 维（physics+hardware+domain 拼接）。")
        if algorithm_key not in ("fdm", "fem", "spectral"):
            raise FeedbackError("algorithm_key 必须为 fdm/fem/spectral。")

        path = os.path.join(self.feedback_dir, filename)
        if os.path.exists(path):
            data = np.load(path, allow_pickle=False)
            X = data["X"]
            y = data["y"]
        else:
            X = np.zeros((0, 13), dtype=np.float32)
            y = np.zeros((0,), dtype=np.int64)

        key_to_idx = {"fdm": 0, "fem": 1, "spectral": 2}
        X2 = np.vstack([X, x.reshape(1, -1)])
        y2 = np.concatenate([y, np.array([key_to_idx[algorithm_key]], dtype=np.int64)])
        np.savez_compressed(path, X=X2, y=y2)
        return path

    def retrain_static_with_feedback(self, strategy: str = "static_rf", seed: int = 42) -> Dict[str, Any]:
        """Retrain static model by mixing typical-case dataset with accumulated feedback samples."""
        X_base, y_base, label_keys = build_typical_case_dataset(seed=seed)

        fb_path = os.path.join(self.feedback_dir, "feedback_samples.npz")
        if os.path.exists(fb_path):
            fb = np.load(fb_path, allow_pickle=False)
            X_fb = fb["X"].astype(np.float32)
            y_fb = fb["y"].astype(int)
            X = np.vstack([X_base, X_fb])
            y = np.concatenate([y_base, y_fb])
        else:
            X, y = X_base, y_base

        try:
            info = self.selector.train_static(strategy=strategy, seed=seed)
            path = self.selector.save_static()
        except AlgorithmSelectionError as e:
            raise FeedbackError(f"模型训练/保存失败: {e}") from e
        return {"trained": info, "saved_to": path, "num_samples_total": int(X.shape[0]), "labels": label_keys}

