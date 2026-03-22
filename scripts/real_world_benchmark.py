"""Build a real-world-inspired PDE benchmark library and compare local methods with external baselines.

This script is intentionally standalone. It only writes under `real_world_benchmark/`
and reuses existing benchmark entry points without modifying solver code.

Commands:
  python scripts/real_world_benchmark.py collect
  python scripts/real_world_benchmark.py run-local
  python scripts/real_world_benchmark.py compare
  python scripts/real_world_benchmark.py all
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List

from test_case.benchmark_algorithms import (
    benchmark_heat2d_solver,
    benchmark_heat3d_solver,
    benchmark_heat_solvers,
    benchmark_poisson1d_solvers,
    benchmark_poisson3d_solver,
    benchmark_selector_strategies,
    benchmark_wave1d_solver as benchmark_wave_solver,
    benchmark_wave2d_solver,
    benchmark_wave3d_solver,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "real_world_benchmark"
MANIFEST_PATH = OUT_DIR / "literature_cases.json"
SOTA_TEMPLATE_PATH = OUT_DIR / "sota_results.template.json"
SOTA_RESULTS_PATH = OUT_DIR / "sota_results.json"
LOCAL_LATEST_PATH = OUT_DIR / "latest_local_results.json"
REPORT_LATEST_PATH = OUT_DIR / "latest_report.md"


def ensure_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def timestamp() -> int:
    return int(time.time())


def default_manifest() -> Dict[str, Any]:
    return {
        "generated_at": time.time(),
        "scope": "Collect publicly documented PDE benchmark sources and map them to current project coverage.",
        "public_sources": [
            {
                "source_id": "pdebench_darus",
                "title": "PDEBench Datasets",
                "kind": "academic_dataset",
                "doi_or_url": "https://doi.org/10.18419/DARUS-2986",
                "repo_url": "https://github.com/pdebench/PDEBench",
                "citation": "Takamoto et al., PDEBench: An Extensive Benchmark for Scientific Machine Learning, NeurIPS 2022.",
                "pdes": [
                    "1D diffusion-sorption",
                    "2D Darcy flow",
                    "2D shallow water",
                    "1D/2D diffusion-reaction",
                ],
                "notes": "Public academic dataset with physically grounded PDE scenarios and pretrained surrogate baselines.",
            },
            {
                "source_id": "pdearena_repo",
                "title": "PDEArena",
                "kind": "benchmark_repo",
                "doi_or_url": "https://github.com/pdearena/pdearena",
                "citation": "Gupta and Brandstetter, Towards Multi-spatiotemporal-scale Generalized PDE Modeling, arXiv 2022.",
                "pdes": ["Shallow water", "Navier-Stokes", "Maxwell-related benchmark ecosystem"],
                "notes": "Useful for future SOTA surrogate comparisons and benchmark adapters.",
            },
            {
                "source_id": "pdebench_pretrained",
                "title": "PDEBench Pretrained Models",
                "kind": "pretrained_models",
                "doi_or_url": "https://doi.org/10.18419/DARUS-2987",
                "citation": "PDEBench pretrained FNO / U-Net / PINN baselines.",
                "pdes": ["Aligned with PDEBench datasets"],
                "notes": "Can be used later as external baseline references without rewriting core project code.",
            },
        ],
        "runnable_aligned_cases": [
            {
                "case_name": "heat1d_rod_cooling",
                "equation_type": "heat1d",
                "application": "1D heat conduction in a rod / diffusion-like transport analogue",
                "algorithms": ["fdm", "fvm", "fem", "spectral", "pinn"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
            {
                "case_name": "poisson1d_steady_diffusion",
                "equation_type": "poisson1d",
                "application": "1D steady diffusion / source-driven potential field",
                "algorithms": ["fdm", "fem", "spectral", "bem"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
            {
                "case_name": "wave1d_string_vibration",
                "equation_type": "wave1d",
                "application": "1D vibrating string benchmark",
                "algorithms": ["fdm", "fem", "spectral"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
            {
                "case_name": "heat2d_square_plate",
                "equation_type": "heat2d",
                "application": "2D square plate conduction benchmark",
                "algorithms": ["fdm", "fvm", "fem"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
            {
                "case_name": "wave2d_membrane",
                "equation_type": "wave2d",
                "application": "2D membrane / shallow-water-like wave propagation analogue",
                "algorithms": ["fdm", "fem", "spectral"],
                "source_refs": ["pdebench_darus", "pdearena_repo"],
                "status": "ready",
            },
            {
                "case_name": "heat3d_cube_conduction",
                "equation_type": "heat3d",
                "application": "3D cube conduction benchmark",
                "algorithms": ["fdm", "fvm", "fem"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
            {
                "case_name": "wave3d_cavity_vibration",
                "equation_type": "wave3d",
                "application": "3D cavity/acoustic-wave benchmark",
                "algorithms": ["fdm", "fem", "spectral"],
                "source_refs": ["pdearena_repo"],
                "status": "ready",
            },
            {
                "case_name": "poisson3d_electrostatic_box",
                "equation_type": "poisson3d",
                "application": "3D electrostatic / Darcy-like elliptic benchmark",
                "algorithms": ["fdm", "fem", "bem"],
                "source_refs": ["pdebench_darus"],
                "status": "ready",
            },
        ],
        "future_adapter_cases": [
            {
                "case_name": "pdebench_diffusion_sorption",
                "dataset_source": "pdebench_darus",
                "mapping_note": "Most similar to heat1d / transport-diffusion class, but requires dataset adapter and data normalization.",
                "status": "pending_adapter",
            },
            {
                "case_name": "pdebench_darcy_flow_2d",
                "dataset_source": "pdebench_darus",
                "mapping_note": "Closest to 2D Poisson / Darcy elliptic flow, but current project lacks a dedicated 2D linear Poisson solver benchmark path.",
                "status": "pending_adapter",
            },
            {
                "case_name": "pdebench_shallow_water_2d",
                "dataset_source": "pdebench_darus",
                "mapping_note": "Closest to wave2d-like hyperbolic behavior; requires a benchmark adapter instead of direct reuse.",
                "status": "pending_adapter",
            },
        ],
        "limitations": [
            "Current local runs use project-supported aligned analogue cases, not direct ingestion of all external datasets.",
            "Automatic SOTA reruns usually require extra repos, GPU resources, and dataset-specific adapters.",
            "This script therefore separates source collection, local benchmarking, and external baseline ingestion.",
        ],
    }


def default_sota_template() -> Dict[str, Any]:
    return {
        "generated_at": time.time(),
        "instructions": [
            "Fill this file with published or externally reproduced baseline numbers.",
            "One entry per case_name. Keep metrics comparable to local results: l2_error, linf_error, elapsed_s.",
            "Suggested sources: PDEBench pretrained models, PDEArena experiments, or literature-reported benchmark tables.",
        ],
        "baselines": [
            {
                "case_name": "wave2d_membrane",
                "model_name": "FNO",
                "source": "PDEBench or PDEArena",
                "citation": "Replace with paper or dataset URL",
                "metrics": {
                    "l2_error": None,
                    "linf_error": None,
                    "elapsed_s": None,
                },
                "notes": "Fill manually after reproducing or extracting from a paper table.",
            }
        ],
    }


RUNNERS: Dict[str, Callable[[], List[Any]]] = {
    "heat1d": benchmark_heat_solvers,
    "poisson1d": benchmark_poisson1d_solvers,
    "wave1d": benchmark_wave_solver,
    "heat2d": benchmark_heat2d_solver,
    "wave2d": benchmark_wave2d_solver,
    "heat3d": benchmark_heat3d_solver,
    "wave3d": benchmark_wave3d_solver,
    "poisson3d": benchmark_poisson3d_solver,
}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_sources() -> Dict[str, Any]:
    ensure_dir()
    manifest = default_manifest()
    write_json(MANIFEST_PATH, manifest)
    if not SOTA_TEMPLATE_PATH.exists():
        write_json(SOTA_TEMPLATE_PATH, default_sota_template())
    return manifest


def _balanced_pick(rows: List[Dict[str, Any]]) -> str:
    min_err = min(r["l2_error"] for r in rows)
    max_err = max(r["l2_error"] for r in rows)
    min_t = min(r["elapsed_s"] for r in rows)
    max_t = max(r["elapsed_s"] for r in rows)

    def score(row: Dict[str, Any]) -> float:
        err = 0.0 if max_err == min_err else (row["l2_error"] - min_err) / (max_err - min_err)
        tim = 0.0 if max_t == min_t else (row["elapsed_s"] - min_t) / (max_t - min_t)
        return 0.65 * err + 0.35 * tim

    return min(rows, key=score)["algorithm"]


def run_local() -> Dict[str, Any]:
    ensure_dir()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else collect_sources()
    local_cases: List[Dict[str, Any]] = []

    by_equation: Dict[str, List[Dict[str, Any]]] = {}
    for equation_type, runner in RUNNERS.items():
        rows = [asdict(item) for item in runner()]
        by_equation[equation_type] = rows

    for case in manifest["runnable_aligned_cases"]:
        eq = case["equation_type"]
        rows = by_equation.get(eq, [])
        if not rows:
            continue
        filtered = [row for row in rows if row["algorithm"] in case["algorithms"]]
        if not filtered:
            continue
        best_by_error = min(filtered, key=lambda r: r["l2_error"])["algorithm"]
        best_by_time = min(filtered, key=lambda r: r["elapsed_s"])["algorithm"]
        best_balanced = _balanced_pick(filtered)
        local_cases.append(
            {
                **case,
                "results": filtered,
                "best_by_error": best_by_error,
                "best_by_time": best_by_time,
                "best_balanced": best_balanced,
            }
        )

    selector_rows = [asdict(item) for item in benchmark_selector_strategies()]

    payload = {
        "generated_at": time.time(),
        "manifest_path": str(MANIFEST_PATH),
        "local_cases": local_cases,
        "selector_accuracy": selector_rows,
        "notes": [
            "These are aligned runnable analogue cases mapped to public benchmark sources.",
            "They are safe to run inside the current project without modifying core solver code.",
        ],
    }

    stamped = OUT_DIR / f"local_results_{timestamp()}.json"
    write_json(stamped, payload)
    write_json(LOCAL_LATEST_PATH, payload)
    return payload


def compare_with_sota() -> Dict[str, Any]:
    ensure_dir()
    if not LOCAL_LATEST_PATH.exists():
        run_local()
    local_payload = json.loads(LOCAL_LATEST_PATH.read_text(encoding="utf-8"))
    sota_payload = json.loads(SOTA_RESULTS_PATH.read_text(encoding="utf-8")) if SOTA_RESULTS_PATH.exists() else {"baselines": []}

    baselines_by_case: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in sota_payload.get("baselines", []):
        baselines_by_case[str(item["case_name"])].append(item)

    comparison_rows: List[Dict[str, Any]] = []
    for case in local_payload["local_cases"]:
        case_name = case["case_name"]
        for local_result in case["results"]:
            comparison_rows.append(
                {
                    "case_name": case_name,
                    "entry_type": "local",
                    "name": local_result["algorithm"],
                    "l2_error": local_result["l2_error"],
                    "linf_error": local_result["linf_error"],
                    "elapsed_s": local_result["elapsed_s"],
                    "notes": f"local_{case['equation_type']}",
                }
            )
        for baseline in baselines_by_case.get(case_name, []):
            metrics = baseline.get("metrics", {})
            comparison_rows.append(
                {
                    "case_name": case_name,
                    "entry_type": "external",
                    "name": baseline.get("model_name", "unknown"),
                    "l2_error": metrics.get("l2_error"),
                    "linf_error": metrics.get("linf_error"),
                    "elapsed_s": metrics.get("elapsed_s"),
                    "notes": baseline.get("citation", ""),
                }
            )

    payload = {
        "generated_at": time.time(),
        "local_results_path": str(LOCAL_LATEST_PATH),
        "sota_results_path": str(SOTA_RESULTS_PATH) if SOTA_RESULTS_PATH.exists() else None,
        "rows": comparison_rows,
    }
    write_json(OUT_DIR / f"comparison_{timestamp()}.json", payload)
    return payload


def render_markdown(local_payload: Dict[str, Any], comparison_payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Real World Benchmark Report")
    lines.append("")
    lines.append(f"- Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(local_payload['generated_at']))}`")
    lines.append(f"- Manifest: [{MANIFEST_PATH.name}]({MANIFEST_PATH.as_posix()})")
    lines.append("")
    lines.append("## Selector Accuracy")
    lines.append("")
    lines.append("| Strategy | Accuracy | Test Samples |")
    lines.append("| --- | ---: | ---: |")
    for row in local_payload["selector_accuracy"]:
        lines.append(f"| {row['strategy']} | {row['accuracy']:.3f} | {row['num_test_samples']} |")

    lines.append("")
    lines.append("## Local Runnable Cases")
    lines.append("")
    for case in local_payload["local_cases"]:
        lines.append(f"### {case['case_name']}")
        lines.append("")
        lines.append(f"- Equation: `{case['equation_type']}`")
        lines.append(f"- Application: {case['application']}")
        lines.append(f"- Best by error: `{case['best_by_error']}`")
        lines.append(f"- Best by time: `{case['best_by_time']}`")
        lines.append(f"- Best balanced: `{case['best_balanced']}`")
        lines.append("")
        lines.append("| Algorithm | L2 Error | Linf Error | Elapsed (s) |")
        lines.append("| --- | ---: | ---: | ---: |")
        for row in case["results"]:
            lines.append(
                f"| {row['algorithm']} | {row['l2_error']:.6e} | {row['linf_error']:.6e} | {row['elapsed_s']:.6f} |"
            )
        lines.append("")

    lines.append("## External Baseline Comparison")
    lines.append("")
    if not comparison_payload["rows"] or not any(row["entry_type"] == "external" for row in comparison_payload["rows"]):
        lines.append("- No external SOTA baseline has been filled yet. Populate `real_world_benchmark/sota_results.json` from the template first.")
    else:
        current_case = None
        for row in comparison_payload["rows"]:
            if row["case_name"] != current_case:
                current_case = row["case_name"]
                lines.append(f"### {current_case}")
                lines.append("")
                lines.append("| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |")
                lines.append("| --- | --- | ---: | ---: | ---: | --- |")
            l2 = "N/A" if row["l2_error"] is None else f"{row['l2_error']:.6e}"
            li = "N/A" if row["linf_error"] is None else f"{row['linf_error']:.6e}"
            el = "N/A" if row["elapsed_s"] is None else f"{row['elapsed_s']:.6f}"
            lines.append(f"| {row['entry_type']} | {row['name']} | {l2} | {li} | {el} | {row['notes']} |")
            if row is comparison_payload["rows"][-1] or comparison_payload["rows"][comparison_payload["rows"].index(row)+1]["case_name"] != current_case:
                lines.append("")

    return "\n".join(lines) + "\n"


def all_in_one() -> Dict[str, Any]:
    collect_sources()
    local_payload = run_local()
    comparison_payload = compare_with_sota()
    report_md = render_markdown(local_payload, comparison_payload)
    REPORT_LATEST_PATH.write_text(report_md, encoding="utf-8")
    return {
        "manifest": str(MANIFEST_PATH),
        "local_results": str(LOCAL_LATEST_PATH),
        "report": str(REPORT_LATEST_PATH),
        "sota_template": str(SOTA_TEMPLATE_PATH),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-world-inspired PDE benchmark helper.")
    parser.add_argument("command", choices=["collect", "run-local", "compare", "all"])
    args = parser.parse_args()

    if args.command == "collect":
        collect_sources()
        print(f"[ok] wrote manifest: {MANIFEST_PATH}")
        print(f"[ok] wrote SOTA template: {SOTA_TEMPLATE_PATH}")
    elif args.command == "run-local":
        payload = run_local()
        print(f"[ok] wrote local results: {LOCAL_LATEST_PATH}")
        print(f"[info] runnable cases: {len(payload['local_cases'])}")
    elif args.command == "compare":
        payload = compare_with_sota()
        report_md = render_markdown(json.loads(LOCAL_LATEST_PATH.read_text(encoding='utf-8')), payload)
        REPORT_LATEST_PATH.write_text(report_md, encoding="utf-8")
        print(f"[ok] wrote comparison report: {REPORT_LATEST_PATH}")
    else:
        summary = all_in_one()
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
