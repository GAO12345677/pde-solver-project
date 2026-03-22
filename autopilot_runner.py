"""Autopilot runner for deterministic optimization tasks.

This script does NOT write new architecture code by itself.
It continuously executes automatable tasks, assesses project state,
and writes the next highest-priority coding tasks into a report.

Run:
  python autopilot_runner.py
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parent
TASKS_FILE = ROOT / "autopilot_tasks.json"
STATE_DIR = ROOT / "autopilot_reports"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_command(command: List[str]) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_s": time.time() - started,
    }


def file_exists(path_str: str) -> bool:
    return (ROOT / path_str).exists()


def content_contains(path_str: str, needle: str) -> bool:
    path = ROOT / path_str
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return needle in content


def load_tasks() -> Dict[str, Any]:
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def evaluate_task(task: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    kind = task["kind"]
    if kind == "command":
        result = run_command(task["command"])
        ok = result["returncode"] == 0
        return ok, result
    if kind == "file_check":
        ok = file_exists(task["path"])
        return ok, {"path": task["path"], "exists": ok}
    if kind == "content_check":
        ok = content_contains(task["path"], task["contains"])
        return ok, {"path": task["path"], "contains": task["contains"], "matched": ok}
    return False, {"error": f"Unknown task kind: {kind}"}


def next_manual_tasks(phases: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> List[str]:
    todo: List[str] = []
    for phase in phases:
        for task in phase["tasks"]:
            task_result = next((item for item in results if item["task_id"] == task["id"]), None)
            if task_result and not task_result["ok"] and task["kind"] != "command":
                todo.append(f"[{phase['id']}] {task['title']}")
    return todo[:5]


def write_markdown_report(task_data: Dict[str, Any], results: List[Dict[str, Any]]) -> Path:
    ensure_dir(STATE_DIR)
    path = STATE_DIR / f"autopilot_{int(time.time())}.md"

    lines: List[str] = []
    lines.append(f"# 自动驾驶报告")
    lines.append("")
    lines.append(f"- 当前主方向：`{task_data['focus']}`")
    lines.append(f"- 说明：{task_data['description']}")
    lines.append(f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 当前阶段检查")
    lines.append("")

    for phase in task_data["phases"]:
        lines.append(f"### {phase['title']}")
        lines.append("")
        for task in phase["tasks"]:
            result = next(item for item in results if item["task_id"] == task["id"])
            status = "PASS" if result["ok"] else "PENDING"
            lines.append(f"- `{status}` {task['title']}")
        lines.append("")

    lines.append("## 可自动完成的任务输出")
    lines.append("")
    for result in results:
        if result["kind"] == "command":
            lines.append(f"### {result['task_id']}")
            lines.append("")
            lines.append("```text")
            stdout = (result["details"].get("stdout") or "").strip()
            stderr = (result["details"].get("stderr") or "").strip()
            if stdout:
                lines.append(stdout)
            if stderr:
                lines.append(stderr)
            lines.append("```")
            lines.append("")

    manual = next_manual_tasks(task_data["phases"], results)
    lines.append("## 下一步最优先代码任务")
    lines.append("")
    if manual:
        for item in manual:
            lines.append(f"- {item}")
    else:
        lines.append("- 当前任务清单中的结构性工作已完成，可以扩展到下一轮研究型目标。")

    lines.append("")
    lines.append("## 边界说明")
    lines.append("")
    lines.append("- 这个脚本可以自动跑测试、benchmark、状态检查和报告生成。")
    lines.append("- 它不会像 AI 编码代理一样自己发明并写入新的复杂代码。")
    lines.append("- 如果你希望持续新增代码模块，仍需要我或其他 AI 代理按报告中的优先项继续修改。")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_latest_summary(results: List[Dict[str, Any]], report_path: Path) -> Path:
    ensure_dir(STATE_DIR)
    path = STATE_DIR / "latest_summary.json"
    payload = {
        "generated_at": time.time(),
        "report_path": str(report_path),
        "results": results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    task_data = load_tasks()
    results: List[Dict[str, Any]] = []

    for phase in task_data["phases"]:
        for task in phase["tasks"]:
            ok, details = evaluate_task(task)
            results.append(
                {
                    "phase_id": phase["id"],
                    "task_id": task["id"],
                    "title": task["title"],
                    "kind": task["kind"],
                    "ok": ok,
                    "details": details,
                }
            )

    report_path = write_markdown_report(task_data, results)
    summary_path = write_latest_summary(results, report_path)

    print(f"[autopilot] report: {report_path}")
    print(f"[autopilot] summary: {summary_path}")
    pending = [item for item in results if not item["ok"]]
    print(f"[autopilot] pending tasks: {len(pending)}")
    for item in pending[:5]:
        print(f"[autopilot] next: {item['phase_id']} / {item['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
