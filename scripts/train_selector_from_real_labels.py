"""Train selector baselines from solver-derived labels.

Supports two dataset styles currently present in the workspace:
1. `records` format from `build_selector_dataset_from_templates.py`
2. legacy `problems` format with nested `algorithm_results`

Supports multiple label targets:
- `strict`: best supported algorithm by pure error
- `score`: best supported algorithm by normalized error/time score
- `hybrid`: score target plus a structure-compatibility penalty derived from
  template metadata (useful when simplified benchmark solvers otherwise make
  spectral dominate mixed-boundary templates unrealistically)
"""

from __future__ import annotations

import argparse
import json
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scripts.selector_feature_utils import build_selector_features

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "real_world_benchmark" / "selector_training_dataset.json"
DEFAULT_OUTPUT = ROOT / "real_world_benchmark" / "selector_real_label_training_results.json"
DEFAULT_MODEL_DIR = ROOT / "model"
SELECTOR_SUPPORTED_ALGOS = {"fdm", "fem", "spectral", "fvm"}


def load_dataset(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_metric_map(metric_map: Dict[str, float]) -> Dict[str, float]:
    values = np.asarray(list(metric_map.values()), dtype=float)
    if values.size == 0:
        return {}
    low = float(np.min(values))
    high = float(np.max(values))
    if abs(high - low) < 1e-12:
        return {key: 0.0 for key in metric_map}
    return {key: float((value - low) / (high - low)) for key, value in metric_map.items()}


def _expected_preference(metadata: Dict[str, Any]) -> str | None:
    bias = str(metadata.get("expected_algorithm_bias", "mixed"))
    return {
        "spectral_friendly": "spectral",
        "fem_friendly": "fem",
        "fvm_friendly": "fvm",
    }.get(bias)


def _compatibility_penalty(algo: str, metadata: Dict[str, Any]) -> float:
    preferred = _expected_preference(metadata)
    boundary_type = str(metadata.get("boundary_type", ""))
    if preferred is not None:
        return 0.0 if algo == preferred else 0.5

    if boundary_type == "periodic":
        return 0.0 if algo == "spectral" else 0.15
    if boundary_type in {"mixed", "mixed_3d", "mixed_dirichlet_neumann", "robin"}:
        if algo == "spectral":
            return 0.4
        if algo == "fem":
            return 0.0
        return 0.1
    if boundary_type in {"inlet_outlet", "inlet_outlet_3d"}:
        if algo == "fvm":
            return 0.0
        if algo == "spectral":
            return 0.4
        return 0.15
    return 0.0


def _derive_label_bundle(
    algorithm_errors: Dict[str, float],
    algorithm_times: Dict[str, float],
    metadata: Dict[str, Any],
    *,
    relative_tolerance: float,
) -> Dict[str, Any]:
    supported_algorithms = sorted(algo for algo in algorithm_errors if algo in SELECTOR_SUPPORTED_ALGOS)
    supported_errors = {algo: float(algorithm_errors[algo]) for algo in supported_algorithms}
    supported_times = {algo: float(algorithm_times.get(algo, 0.0)) for algo in supported_algorithms}
    normalized_errors = _normalize_metric_map(supported_errors)
    normalized_times = _normalize_metric_map(supported_times)

    score_labels: Dict[str, float] = {}
    hybrid_labels: Dict[str, float] = {}
    for algo in supported_algorithms:
        base_score = normalized_errors.get(algo, 0.0) + 0.25 * normalized_times.get(algo, 0.0)
        score_labels[algo] = float(base_score)
        hybrid_labels[algo] = float(base_score + _compatibility_penalty(algo, metadata))

    strict_target = min(supported_algorithms, key=lambda algo: supported_errors[algo]) if supported_algorithms else None
    score_target = min(supported_algorithms, key=lambda algo: score_labels[algo]) if supported_algorithms else None
    hybrid_target = min(supported_algorithms, key=lambda algo: hybrid_labels[algo]) if supported_algorithms else None
    tolerant_strict_target = None
    if supported_algorithms:
        best_error = min(supported_errors.values())
        near_optimal_algorithms = [
            algo for algo in supported_algorithms if supported_errors[algo] <= best_error * (1.0 + relative_tolerance)
        ]
        tolerant_strict_target = min(
            near_optimal_algorithms,
            key=lambda algo: (supported_times.get(algo, float("inf")), supported_errors[algo]),
        )

    return {
        "supported_algorithms": supported_algorithms,
        "strict_target": strict_target,
        "strict_tolerant_target": tolerant_strict_target,
        "score_target": score_target,
        "hybrid_target": hybrid_target,
        "normalized_errors": normalized_errors,
        "normalized_times": normalized_times,
        "score_labels": score_labels,
        "hybrid_labels": hybrid_labels,
    }


def _extract_samples(dataset: Dict[str, Any], *, relative_tolerance: float) -> List[Dict[str, Any]]:
    if "records" in dataset:
        samples: List[Dict[str, Any]] = []
        for record in dataset.get("records", []):
            algorithm_errors = {str(k): float(v) for k, v in record.get("algorithm_errors", {}).items()}
            algorithm_times = {str(k): float(v) for k, v in record.get("algorithm_times", {}).items()}
            if not algorithm_errors:
                continue
            metadata = record.get("metadata", {})
            labels = _derive_label_bundle(
                algorithm_errors,
                algorithm_times,
                metadata,
                relative_tolerance=relative_tolerance,
            )
            samples.append(
                {
                    "problem_id": int(record["problem_id"]),
                    "equation_type": str(record["equation_type"]),
                    "template_id": str(record.get("template_id", "")),
                    "features": build_selector_features(
                        physics=np.asarray(record["physics_features"], dtype=np.float32),
                        hardware=np.asarray(record["hardware_features"], dtype=np.float32),
                        domain=np.asarray(record["domain_features"], dtype=np.float32),
                        equation_type=str(record["equation_type"]),
                        dimension=int(record["dimension"]),
                        params=dict(record.get("params", {})),
                        metadata=metadata,
                    ),
                    "metadata": metadata,
                    "labels": labels,
                }
            )
        return samples

    if "problems" in dataset:
        samples = []
        for record in dataset.get("problems", []):
            raw_results = record.get("algorithm_results", {})
            algorithm_errors = {str(algo): float(values["mean_error"]) for algo, values in raw_results.items()}
            algorithm_times = {str(algo): float(values["mean_time"]) for algo, values in raw_results.items()}
            if not algorithm_errors:
                continue
            metadata = record.get("metadata", {})
            labels = _derive_label_bundle(
                algorithm_errors,
                algorithm_times,
                metadata,
                relative_tolerance=relative_tolerance,
            )
            samples.append(
                {
                    "problem_id": int(record["problem_id"]),
                    "equation_type": str(record["equation_type"]),
                    "template_id": str(record.get("template_id", "")),
                    "features": build_selector_features(
                        physics=np.asarray(record["physics_features"], dtype=np.float32),
                        hardware=np.asarray(record["hardware_features"], dtype=np.float32),
                        domain=np.asarray(record["domain_features"], dtype=np.float32),
                        equation_type=str(record["equation_type"]),
                        dimension=int(record["dimension"]),
                        params=dict(record.get("params", {})),
                        metadata=metadata,
                    ),
                    "metadata": metadata,
                    "labels": labels,
                }
            )
        return samples

    raise ValueError("Unsupported dataset format: expected `records` or `problems` at top level.")


def build_feature_matrix(samples: List[Dict[str, Any]], target_mode: str) -> Tuple[np.ndarray, np.ndarray, List[str], List[Dict[str, Any]]]:
    target_key = {
        "strict": "strict_target",
        "strict_tolerant": "strict_tolerant_target",
        "score": "score_target",
        "hybrid": "hybrid_target",
    }[target_mode]

    usable = [sample for sample in samples if sample["labels"].get(target_key)]
    label_keys = sorted({str(sample["labels"][target_key]) for sample in usable})
    label_to_idx = {label: idx for idx, label in enumerate(label_keys)}

    X = np.stack([sample["features"] for sample in usable], axis=0)
    y = np.asarray([label_to_idx[str(sample["labels"][target_key])] for sample in usable], dtype=np.int64)
    return X, y, label_keys, usable


def stratified_split(y: np.ndarray, test_fraction: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_indices: List[int] = []
    test_indices: List[int] = []

    for label in np.unique(y):
        class_indices = np.where(y == label)[0]
        shuffled = np.array(class_indices, copy=True)
        rng.shuffle(shuffled)
        if len(shuffled) <= 1:
            train_indices.extend(shuffled.tolist())
            continue
        test_count = max(1, int(round(len(shuffled) * test_fraction)))
        if test_count >= len(shuffled):
            test_count = len(shuffled) - 1
        test_indices.extend(shuffled[:test_count].tolist())
        train_indices.extend(shuffled[test_count:].tolist())

    return np.asarray(sorted(train_indices), dtype=np.int64), np.asarray(sorted(test_indices), dtype=np.int64)


def compute_confusion(y_true: np.ndarray, y_pred: np.ndarray, label_keys: List[str]) -> Dict[str, Dict[str, int]]:
    confusion: Dict[str, Dict[str, int]] = {}
    for truth, pred in zip(y_true.tolist(), y_pred.tolist()):
        actual = label_keys[int(truth)]
        predicted = label_keys[int(pred)]
        confusion.setdefault(actual, {})
        confusion[actual][predicted] = confusion[actual].get(predicted, 0) + 1
    return confusion


def accuracy_by_equation(
    usable_samples: List[Dict[str, Any]],
    test_indices: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Dict[str, Any]]:
    summary: Dict[str, Dict[str, Any]] = {}
    for local_idx, dataset_idx in enumerate(test_indices.tolist()):
        eq = str(usable_samples[dataset_idx]["equation_type"])
        summary.setdefault(eq, {"total": 0, "correct": 0})
        summary[eq]["total"] += 1
        if int(y_true[local_idx]) == int(y_pred[local_idx]):
            summary[eq]["correct"] += 1

    for eq, stats in summary.items():
        stats["accuracy"] = float(stats["correct"] / stats["total"]) if stats["total"] else 0.0
    return summary


def build_model(model_name: str, seed: int) -> Any:
    if model_name == "rf":
        from sklearn.ensemble import RandomForestClassifier  # type: ignore

        return RandomForestClassifier(
            n_estimators=300,
            random_state=seed,
            n_jobs=1,
        )

    if model_name == "mlp":
        from sklearn.neural_network import MLPClassifier  # type: ignore

        return MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            alpha=1e-4,
            batch_size=32,
            learning_rate_init=1e-3,
            max_iter=600,
            random_state=seed,
            early_stopping=False,
        )

    raise ValueError(f"unsupported model: {model_name}")


def save_model(
    model: Any,
    model_name: str,
    label_keys: List[str],
    dataset_path: Path,
    target_mode: str,
    relative_tolerance: float,
) -> str:
    DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = DEFAULT_MODEL_DIR / f"selector_real_labels_{model_name}_{target_mode}.pkl"
    payload = {
        "model": model,
        "label_keys": label_keys,
        "source_dataset": str(dataset_path),
        "strategy": model_name,
        "target_mode": target_mode,
        "relative_tolerance": relative_tolerance,
        "feature_mode": "engineered_v1",
        "generated_at": time.time(),
    }
    with open(path, "wb") as f:
        pickle.dump(payload, f)
    return str(path)


def summarize_label_distribution(usable_samples: List[Dict[str, Any]], target_mode: str) -> Dict[str, int]:
    target_key = {
        "strict": "strict_target",
        "strict_tolerant": "strict_tolerant_target",
        "score": "score_target",
        "hybrid": "hybrid_target",
    }[target_mode]
    counts: Dict[str, int] = {}
    for sample in usable_samples:
        label = str(sample["labels"][target_key])
        counts[label] = counts.get(label, 0) + 1
    return counts


def train_and_evaluate(
    dataset_path: Path,
    model_names: List[str],
    test_fraction: float,
    seed: int,
    target_mode: str,
    relative_tolerance: float,
) -> Dict[str, Any]:
    dataset = load_dataset(dataset_path)
    samples = _extract_samples(dataset, relative_tolerance=relative_tolerance)
    X, y, label_keys, usable_samples = build_feature_matrix(samples, target_mode=target_mode)
    train_idx, test_idx = stratified_split(y, test_fraction=test_fraction, seed=seed)

    X_train = X[train_idx]
    y_train = y[train_idx]
    X_test = X[test_idx]
    y_test = y[test_idx]

    results: Dict[str, Any] = {}
    for model_name in model_names:
        model = build_model(model_name, seed=seed)
        started = time.time()
        model.fit(X_train, y_train)
        train_elapsed = time.time() - started

        y_pred = model.predict(X_test) if len(X_test) else np.asarray([], dtype=np.int64)
        train_accuracy = float(np.mean(model.predict(X_train) == y_train)) if len(y_train) else 0.0
        test_accuracy = float(np.mean(y_pred == y_test)) if len(y_test) else 0.0

        result = {
            "model_name": model_name,
            "label_keys": label_keys,
            "num_samples": int(len(usable_samples)),
            "num_train": int(len(train_idx)),
            "num_test": int(len(test_idx)),
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "training_time_s": float(train_elapsed),
            "confusion_matrix": compute_confusion(y_test, y_pred, label_keys) if len(y_test) else {},
            "accuracy_by_equation": accuracy_by_equation(usable_samples, test_idx, y_test, y_pred) if len(y_test) else {},
            "saved_model_path": save_model(model, model_name, label_keys, dataset_path, target_mode, relative_tolerance),
        }
        results[model_name] = result

    payload = {
        "generated_at": time.time(),
        "config": {
            "dataset_path": str(dataset_path),
            "model_names": model_names,
            "test_fraction": test_fraction,
            "seed": seed,
            "target_mode": target_mode,
            "relative_tolerance": relative_tolerance,
            "feature_mode": "engineered_v1",
        },
        "label_distribution": summarize_label_distribution(usable_samples, target_mode=target_mode),
        "results": results,
    }
    if "summary" in dataset:
        payload["dataset_summary"] = dataset["summary"]
    if "config" in dataset:
        payload["source_config"] = dataset["config"]
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Train selector baselines from solver-derived labels")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--models", nargs="+", default=["rf", "mlp"])
    parser.add_argument("--test-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-mode", choices=["strict", "strict_tolerant", "score", "hybrid"], default="hybrid")
    parser.add_argument("--relative-tolerance", type=float, default=0.03)
    args = parser.parse_args()

    dataset_path = Path(args.input)
    output_path = Path(args.output)

    print("=" * 70)
    print("TRAIN SELECTOR FROM REAL LABELS")
    print("=" * 70)
    print(f"Input: {dataset_path}")
    print(f"Models: {args.models}")
    print(f"Target mode: {args.target_mode}")

    payload = train_and_evaluate(
        dataset_path=dataset_path,
        model_names=list(args.models),
        test_fraction=float(args.test_fraction),
        seed=int(args.seed),
        target_mode=str(args.target_mode),
        relative_tolerance=float(args.relative_tolerance),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Label distribution: {payload['label_distribution']}")
    for model_name, result in payload["results"].items():
        print(f"\nModel: {model_name}")
        print(f"  Train accuracy: {result['train_accuracy']:.4f}")
        print(f"  Test accuracy: {result['test_accuracy']:.4f}")
        print(f"  Train size / test size: {result['num_train']} / {result['num_test']}")
        print(f"  Saved model: {result['saved_model_path']}")

    print(f"\n[ok] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
