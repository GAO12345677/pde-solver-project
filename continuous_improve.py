"""One-click optimization loop for the course project.

What this script can do automatically:
- retrain static selectors (RF / MLP)
- retrain dynamic RL policy
- run benchmark suite
- run targeted regression tests
- generate a markdown progress report with next-step suggestions

What it cannot do automatically:
- invent new code changes on its own
- modify project architecture without a human or coding agent

Run:
  python continuous_improve.py
  python continuous_improve.py --iterations 3
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from algorithm.selector import AlgorithmSelector
from test_case.benchmark_algorithms import build_report, save_report


ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "improvement_reports"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_command(cmd: List[str]) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_s": time.time() - started,
    }


@dataclass
class ImprovementIteration:
    iteration: int
    rf_trained: bool
    mlp_trained: bool
    rl_trained: bool
    benchmark_path: str
    tests_ok: bool
    notes: List[str]


def retrain_models() -> Dict[str, Any]:
    selector = AlgorithmSelector(model_dir="model")
    rf = selector.train_static(strategy="static_rf")
    selector.save_static(filename="static_static_rf.pkl")

    mlp = selector.train_static(strategy="mlp_nn")
    selector.save_static(filename="static_mlp_nn.pkl")

    rl = selector.train_dynamic(episodes=300)
    selector.save_dynamic(filename="dynamic_rl.pkl")

    return {"static_rf": rf, "mlp_nn": mlp, "dynamic_rl": rl}


def run_regression_tests() -> Dict[str, Any]:
    return run_command(
        [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "pytest",
            "-q",
            "tests/test_wave1d_api.py",
            "tests/test_mlp_selector.py",
            "tests/test_algorithm_selector.py",
        ]
    )


def classify_findings(benchmark_report: Dict[str, Any], test_result: Dict[str, Any]) -> List[str]:
    notes: List[str] = []

    selector_rows = {row["strategy"]: row for row in benchmark_report.get("selector_accuracy", [])}
    rl_acc = selector_rows.get("dynamic_rl", {}).get("accuracy", 0.0)
    if rl_acc < 0.6:
        notes.append("`dynamic_rl` 准确率偏低，建议优先扩展状态表示、奖励设计和训练轮数。")

    solver_rows = benchmark_report.get("solver_accuracy", [])
    for row in solver_rows:
        if row["equation_type"] == "wave1d" and row["algorithm"] == "fdm" and row["l2_error"] > 1e-3:
            notes.append("`wave1d / fdm` 误差偏高，建议细化 nt 或检查 CFL 设置。")
        if row["equation_type"] == "heat1d" and row["algorithm"] == "spectral" and row["l2_error"] > 1e-6:
            notes.append("`heat1d / spectral` 精度仍有异常，建议继续检查谱方法实现。")

    if test_result["returncode"] != 0:
        notes.append("回归测试未全部通过，应优先修复接口/求解器回归。")
    else:
        notes.append("当前回归测试通过，可以继续做能力扩展。")

    if not notes:
        notes.append("当前版本稳定，下一步可优先扩展 `wave1d` 多算法实现和 RL 能力。")
    return notes


def write_markdown_report(
    *,
    iteration: int,
    benchmark_path: Path,
    benchmark_report: Dict[str, Any],
    retrain_info: Dict[str, Any],
    test_result: Dict[str, Any],
    notes: List[str],
) -> Path:
    _ensure_dir(REPORT_DIR)
    path = REPORT_DIR / f"improvement_iteration_{iteration}.md"

    lines: List[str] = []
    lines.append(f"# 持续优化报告 #{iteration}")
    lines.append("")
    lines.append(f"- 时间戳：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 基准报告：`{benchmark_path}`")
    lines.append(f"- 回归测试状态：`{'PASS' if test_result['returncode'] == 0 else 'FAIL'}`")
    lines.append("")
    lines.append("## 模型重训练")
    lines.append("")
    lines.append(f"- `static_rf`: {retrain_info['static_rf']}")
    lines.append(f"- `mlp_nn`: {retrain_info['mlp_nn']}")
    lines.append(f"- `dynamic_rl`: {retrain_info['dynamic_rl']}")
    lines.append("")
    lines.append("## 选择器准确率")
    lines.append("")
    for row in benchmark_report.get("selector_accuracy", []):
        lines.append(f"- `{row['strategy']}`: `accuracy={row['accuracy']:.3f}` on `{row['num_test_samples']}` samples")
    lines.append("")
    lines.append("## 求解器误差")
    lines.append("")
    for row in benchmark_report.get("solver_accuracy", []):
        lines.append(
            f"- `{row['equation_type']} / {row['algorithm']}`: "
            f"`L2={row['l2_error']:.6e}`, `Linf={row['linf_error']:.6e}`, `elapsed={row['elapsed_s']:.4f}s`"
        )
    lines.append("")
    lines.append("## 回归测试输出")
    lines.append("")
    lines.append("```text")
    lines.append((test_result.get("stdout") or "").strip())
    if test_result.get("stderr"):
        lines.append(test_result["stderr"].strip())
    lines.append("```")
    lines.append("")
    lines.append("## 下一步建议")
    lines.append("")
    for note in notes:
        lines.append(f"- {note}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_iteration(iteration: int) -> ImprovementIteration:
    retrain_info = retrain_models()
    benchmark_report = build_report()
    benchmark_path = Path(save_report(benchmark_report))
    test_result = run_regression_tests()
    notes = classify_findings(benchmark_report, test_result)
    write_markdown_report(
        iteration=iteration,
        benchmark_path=benchmark_path,
        benchmark_report=benchmark_report,
        retrain_info=retrain_info,
        test_result=test_result,
        notes=notes,
    )
    return ImprovementIteration(
        iteration=iteration,
        rf_trained=True,
        mlp_trained=True,
        rl_trained=True,
        benchmark_path=str(benchmark_path),
        tests_ok=test_result["returncode"] == 0,
        notes=notes,
    )


def write_index(results: List[ImprovementIteration]) -> Path:
    _ensure_dir(REPORT_DIR)
    path = REPORT_DIR / "latest_summary.json"
    payload = {
        "generated_at": time.time(),
        "iterations": [
            {
                "iteration": item.iteration,
                "rf_trained": item.rf_trained,
                "mlp_trained": item.mlp_trained,
                "rl_trained": item.rl_trained,
                "benchmark_path": item.benchmark_path,
                "tests_ok": item.tests_ok,
                "notes": item.notes,
            }
            for item in results
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1, help="How many optimization/reporting loops to run.")
    args = parser.parse_args()

    _ensure_dir(REPORT_DIR)
    results: List[ImprovementIteration] = []
    for i in range(1, max(1, args.iterations) + 1):
        print(f"[continuous_improve] starting iteration {i}")
        result = run_iteration(i)
        results.append(result)
        print(f"[continuous_improve] benchmark saved to {result.benchmark_path}")
        print(f"[continuous_improve] tests_ok={result.tests_ok}")
        for note in result.notes:
            print(f"[continuous_improve] note: {note}")

    summary_path = write_index(results)
    print(f"[continuous_improve] summary written to {summary_path}")
    print(f"[continuous_improve] detailed markdown reports are under {REPORT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
