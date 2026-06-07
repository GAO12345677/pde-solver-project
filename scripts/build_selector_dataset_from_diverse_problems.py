"""Build selector dataset from the same diverse-problem generator used in evaluation."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from scripts.selector_evaluation import generate_diverse_problems, solve_problem

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "real_world_benchmark" / "selector_training_dataset_diverse.json"


def build_dataset(num_problems: int, num_runs: int, seed: int, output_path: Path) -> Dict[str, Any]:
    problems = generate_diverse_problems(num_problems=num_problems, seed=seed)
    started = time.time()
    records: List[Dict[str, Any]] = []

    for idx, problem in enumerate(problems):
        if idx == 0 or (idx + 1) % 50 == 0:
            elapsed = time.time() - started
            done = idx + 1
            eta = (elapsed / done) * (len(problems) - done) if done else 0.0
            print(f"  Progress: {done}/{len(problems)} ({done/len(problems)*100:.1f}%) - ETA: {eta:.0f}s")

        errors, times = solve_problem(problem, num_runs=num_runs)
        if not errors:
            continue

        records.append(
            {
                "problem_id": int(problem.problem_id),
                "equation_type": str(problem.equation_type),
                "dimension": int(problem.dimension),
                "params": {
                    key: (value.item() if isinstance(value, np.generic) else value)
                    for key, value in problem.params.items()
                },
                "physics_features": problem.physics_features.tolist(),
                "hardware_features": problem.hardware_features.tolist(),
                "domain_features": problem.domain_features.tolist(),
                "metadata": {
                    "source_type": "diverse_generator",
                    "source_reference": "scripts.selector_evaluation.generate_diverse_problems",
                    "variation_notes": "Generated from the same distribution family as the formal selector benchmark.",
                    "boundary_type": "dirichlet",
                    "expected_algorithm_bias": "mixed",
                },
                "algorithm_results": {
                    algo: {
                        "mean_error": float(errors[algo]),
                        "std_error": 0.0,
                        "mean_time": float(times.get(algo, 0.0)),
                    }
                    for algo in errors
                },
                "best_algorithm": min(errors.keys(), key=lambda algo: errors[algo]),
                "best_error": float(min(errors.values())),
            }
        )

    eq_dist: Dict[str, int] = {}
    label_dist: Dict[str, int] = {}
    for record in records:
        eq = record["equation_type"]
        label = record["best_algorithm"]
        eq_dist[eq] = eq_dist.get(eq, 0) + 1
        label_dist[label] = label_dist.get(label, 0) + 1

    payload = {
        "generated_at": time.time(),
        "config": {
            "num_problems_input": num_problems,
            "num_problems_output": len(records),
            "num_runs": num_runs,
            "seed": seed,
            "source": "diverse_problem_generator",
        },
        "summary": {
            "equation_distribution": eq_dist,
            "best_algorithm_distribution": label_dist,
            "elapsed_s": float(time.time() - started),
        },
        "problems": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build selector dataset from diverse benchmark problems")
    parser.add_argument("--problems", type=int, default=300)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output_path = Path(args.output)
    print("=" * 70)
    print("BUILD SELECTOR DATASET FROM DIVERSE PROBLEMS")
    print("=" * 70)
    payload = build_dataset(
        num_problems=int(args.problems),
        num_runs=int(args.runs),
        seed=int(args.seed),
        output_path=output_path,
    )
    print(f"\nEquation distribution: {payload['summary']['equation_distribution']}")
    print(f"Best algorithm distribution: {payload['summary']['best_algorithm_distribution']}")
    print(f"[ok] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
