"""Evaluate a trained real-label selector model on diverse PDE problems."""

from __future__ import annotations

import argparse
import json
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from scripts.selector_evaluation import PDEProblem, generate_diverse_problems, solve_problem
from scripts.selector_feature_utils import build_selector_features

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "model" / "selector_real_labels_mlp_hybrid.pkl"
DEFAULT_OUTPUT = ROOT / "real_world_benchmark" / "real_label_selector_evaluation.json"


def load_model(path: Path) -> Dict[str, Any]:
    with open(path, "rb") as f:
        return pickle.load(f)


def feature_vector(problem: PDEProblem) -> np.ndarray:
    metadata = {
        "boundary_type": "dirichlet",
        "expected_algorithm_bias": "mixed",
        "solution_characteristics": {},
    }
    return build_selector_features(
        physics=np.asarray(problem.physics_features, dtype=np.float32),
        hardware=np.asarray(problem.hardware_features, dtype=np.float32),
        domain=np.asarray(problem.domain_features, dtype=np.float32),
        equation_type=str(problem.equation_type),
        dimension=int(problem.dimension),
        params=dict(problem.params),
        metadata=metadata,
    ).reshape(1, -1)


def predict(model_payload: Dict[str, Any], problem: PDEProblem) -> tuple[str, float | None]:
    model = model_payload["model"]
    label_keys = list(model_payload["label_keys"])
    x = feature_vector(problem)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)[0]
        idx = int(np.argmax(proba))
        return label_keys[idx], float(np.max(proba))
    pred = model.predict(x)
    return label_keys[int(pred[0])], None


def summarize_results(results: List[Dict[str, Any]], elapsed_s: float) -> Dict[str, Any]:
    total = len(results)
    total_correct = sum(1 for r in results if r["prediction_correct"])
    tolerant_correct = sum(1 for r in results if r.get("tolerant_prediction_correct"))
    supported_total = sum(1 for r in results if r["actual_best_algorithm"] in r["model_label_keys"])
    supported_correct = sum(
        1 for r in results if r["actual_best_algorithm"] in r["model_label_keys"] and r["prediction_correct"]
    )

    accuracy_by_equation: Dict[str, Dict[str, Any]] = {}
    confusion: Dict[str, Dict[str, int]] = {}
    unsupported_actual_best = 0
    predicted_counts: Dict[str, int] = {}
    actual_counts: Dict[str, int] = {}

    for r in results:
        eq = r["equation_type"]
        accuracy_by_equation.setdefault(eq, {"total": 0, "correct": 0, "supported_total": 0, "supported_correct": 0})
        accuracy_by_equation[eq]["total"] += 1
        if r["prediction_correct"]:
            accuracy_by_equation[eq]["correct"] += 1
        if r.get("tolerant_prediction_correct"):
            accuracy_by_equation[eq]["tolerant_correct"] = accuracy_by_equation[eq].get("tolerant_correct", 0) + 1

        actual = r["actual_best_algorithm"]
        predicted = r["predicted_algorithm"]
        actual_counts[actual] = actual_counts.get(actual, 0) + 1
        predicted_counts[predicted] = predicted_counts.get(predicted, 0) + 1
        confusion.setdefault(actual, {})
        confusion[actual][predicted] = confusion[actual].get(predicted, 0) + 1

        if actual in r["model_label_keys"]:
            accuracy_by_equation[eq]["supported_total"] += 1
            if r["prediction_correct"]:
                accuracy_by_equation[eq]["supported_correct"] += 1
        else:
            unsupported_actual_best += 1

    for stats in accuracy_by_equation.values():
        stats["accuracy"] = float(stats["correct"] / stats["total"]) if stats["total"] else 0.0
        stats["tolerant_accuracy"] = float(stats.get("tolerant_correct", 0) / stats["total"]) if stats["total"] else 0.0
        stats["supported_accuracy"] = (
            float(stats["supported_correct"] / stats["supported_total"]) if stats["supported_total"] else None
        )

    return {
        "overall_accuracy": float(total_correct / total) if total else 0.0,
        "tolerant_accuracy": float(tolerant_correct / total) if total else 0.0,
        "supported_accuracy": float(supported_correct / supported_total) if supported_total else 0.0,
        "total_correct": total_correct,
        "supported_total_correct": supported_correct,
        "total_problems": total,
        "supported_total_problems": supported_total,
        "unsupported_actual_best_count": unsupported_actual_best,
        "elapsed_s": float(elapsed_s),
        "accuracy_by_equation": accuracy_by_equation,
        "confusion_matrix": confusion,
        "predicted_distribution": predicted_counts,
        "actual_distribution": actual_counts,
    }


def evaluate(
    model_path: Path,
    output_path: Path,
    num_problems: int,
    num_runs: int,
    seed: int,
    relative_tolerance: float,
) -> Dict[str, Any]:
    model_payload = load_model(model_path)
    problems = generate_diverse_problems(num_problems=num_problems, seed=seed)
    started = time.time()
    results: List[Dict[str, Any]] = []

    for idx, problem in enumerate(problems):
        if idx == 0 or (idx + 1) % 50 == 0:
            print(f"  Progress: {idx + 1}/{len(problems)}")

        errors, times = solve_problem(problem, num_runs=num_runs)
        if not errors:
            continue

        actual_best = min(errors.keys(), key=lambda algo: errors[algo])
        predicted, confidence = predict(model_payload, problem)
        best_error = errors[actual_best]
        near_optimal_algorithms = [algo for algo, err in errors.items() if err <= best_error * (1.0 + relative_tolerance)]
        results.append(
            {
                "problem_id": problem.problem_id,
                "equation_type": problem.equation_type,
                "predicted_algorithm": predicted,
                "actual_best_algorithm": actual_best,
                "prediction_correct": predicted == actual_best,
                "tolerant_prediction_correct": predicted in near_optimal_algorithms,
                "model_confidence": confidence,
                "model_label_keys": list(model_payload["label_keys"]),
                "near_optimal_algorithms": near_optimal_algorithms,
                "all_algorithm_errors": errors,
                "all_algorithm_times": times,
            }
        )

    summary = summarize_results(results, elapsed_s=time.time() - started)
    payload = {
        "generated_at": time.time(),
        "config": {
            "model_path": str(model_path),
            "num_problems": num_problems,
            "num_runs_per_problem": num_runs,
            "seed": seed,
            "relative_tolerance": relative_tolerance,
            "label_keys": list(model_payload["label_keys"]),
            "strategy": model_payload.get("strategy"),
            "target_mode": model_payload.get("target_mode"),
            "feature_mode": model_payload.get("feature_mode", "raw"),
        },
        "summary": summary,
        "detailed_results": results[:100],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate real-label selector model")
    parser.add_argument("--model", type=str, default=str(DEFAULT_MODEL))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--problems", type=int, default=100)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--relative-tolerance", type=float, default=0.03)
    args = parser.parse_args()

    model_path = Path(args.model)
    output_path = Path(args.output)

    print("=" * 70)
    print("EVALUATE REAL-LABEL SELECTOR")
    print("=" * 70)
    print(f"Model: {model_path}")
    payload = evaluate(
        model_path=model_path,
        output_path=output_path,
        num_problems=int(args.problems),
        num_runs=int(args.runs),
        seed=int(args.seed),
        relative_tolerance=float(args.relative_tolerance),
    )
    summary = payload["summary"]
    print(f"\nOverall accuracy: {summary['overall_accuracy']*100:.2f}%")
    print(f"Tolerant accuracy: {summary['tolerant_accuracy']*100:.2f}%")
    print(f"Supported accuracy: {summary['supported_accuracy']*100:.2f}%")
    print(f"Unsupported actual-best count: {summary['unsupported_actual_best_count']}")
    print(f"[ok] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
