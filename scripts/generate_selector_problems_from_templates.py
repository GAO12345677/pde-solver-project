"""基于模板生成算法选择器训练问题.

Usage:
  python -m scripts.generate_selector_problems_from_templates --count 1000 --output output.json
  python -m scripts.generate_selector_problems_from_templates --sample 50
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "real_world_benchmark" / "pde_problem_templates.json"
DEFAULT_OUTPUT = ROOT / "real_world_benchmark" / "generated_selector_problems.json"


def load_templates() -> Dict[str, Any]:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for template in data.get("templates", []):
        _enrich_template_metadata(template)

    return data


def _infer_source_type(template: Dict[str, Any]) -> str:
    tags = set(template.get("difficulty_tags", []))
    boundary_type = template.get("boundary_type", "")
    name_blob = " ".join(
        [
            template.get("template_id", ""),
            template.get("name", ""),
            template.get("description", ""),
            " ".join(tags),
        ]
    ).lower()

    if "benchmark" in tags or "canonical" in tags or "classic" in name_blob:
        return "canonical"
    if boundary_type in {"mixed", "mixed_3d", "mixed_dirichlet_neumann", "robin", "inlet_outlet", "inlet_outlet_3d"}:
        return "template_derived"
    if any(token in name_blob for token in ["multi_scale", "high_frequency", "steep_gradient", "flux", "localized", "exploration"]):
        return "synthetic_exploration"
    return "template_derived"


def _default_source_reference(template: Dict[str, Any], source_type: str) -> str:
    eq = template.get("equation_type", "pde")
    if source_type == "canonical":
        return f"canonical_{eq}_benchmark_family"
    if source_type == "synthetic_exploration":
        return f"structured_synthetic_{eq}_selector_stress_case"
    return f"template_derived_{eq}_family"


def _default_variation_notes(template: Dict[str, Any], source_type: str) -> str:
    boundary_type = template.get("boundary_type", "dirichlet")
    bias = template.get("expected_algorithm_bias", "mixed")
    if source_type == "canonical":
        return f"Derived from a standard {template.get('equation_type')} teaching/benchmark pattern with controlled parameter sampling and {boundary_type} boundaries."
    if source_type == "synthetic_exploration":
        return f"Constructed to stress selector decision boundaries through {bias} behavior, nontrivial gradients, or multi-scale structure."
    return f"Template variation built from a structured mother problem by perturbing coefficients, grids, and {boundary_type} boundary settings."


def _enrich_template_metadata(template: Dict[str, Any]) -> None:
    source_type = template.get("source_type") or _infer_source_type(template)
    template["source_type"] = source_type
    template["source_reference"] = template.get("source_reference") or _default_source_reference(template, source_type)
    template["variation_notes"] = template.get("variation_notes") or _default_variation_notes(template, source_type)


def sample_from_range(min_val: float, max_val: float, rng: np.random.Generator) -> float:
    return float(rng.uniform(min_val, max_val))


def sample_discrete(values: List[Any], weights: Optional[List[float]], rng: np.random.Generator) -> Any:
    if weights is None:
        idx = rng.integers(0, len(values))
    else:
        cumsum = np.cumsum(weights)
        r = rng.random() * cumsum[-1]
        idx = np.searchsorted(cumsum, r)
        idx = min(idx, len(values) - 1)
    result = values[idx]
    if isinstance(result, (list, tuple)):
        return list(result)
    return result


def generate_params_from_template(template: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    params = {}
    param_ranges = template.get("parameter_ranges", {})

    for param_name, param_spec in param_ranges.items():
        param_type = param_spec.get("type")

        if param_type == "discrete":
            values = param_spec["values"]
            weights = param_spec.get("weights")
            params[param_name] = sample_discrete(values, weights, rng)

        elif param_type == "range":
            params[param_name] = sample_from_range(
                param_spec["min"], param_spec["max"], rng
            )

        elif param_type == "derived":
            continue

        elif param_type == "fixed":
            params[param_name] = param_spec["value"]

    return params


def derive_time_from_template(
    template: Dict[str, Any], params: Dict[str, Any], rng: np.random.Generator
) -> float:
    time_ranges = template.get("time_ranges", {})
    t_spec = time_ranges.get("t_final", {})
    time_type = t_spec.get("type")

    if time_type == "fixed":
        return float(t_spec.get("value", 0.0))

    elif time_type == "range":
        return sample_from_range(
            t_spec["min"], t_spec["max"], rng
        )

    elif time_type == "derived":
        formula = t_spec.get("formula", "")
        constraint = t_spec.get("constraint", "")

        derived_params = dict(params)

        if "L" in derived_params and "k" in derived_params:
            if "mode" in derived_params:
                mode = derived_params["mode"]
            else:
                mode = 1

            if formula == "0.5 * L^2 / k / mode^2":
                result = 0.5 * (derived_params["L"] ** 2) / derived_params["k"] / (mode ** 2)
                if "ensure_decay_factor_0.01_to_0.5" in constraint:
                    result = np.clip(result, 0.01, 0.5)
                return float(result)

            elif formula == "0.2 * L^2 / k":
                result = 0.2 * (derived_params["L"] ** 2) / derived_params["k"]
                if "ensure_visible_decay" in constraint:
                    result = max(result, 0.01)
                return float(result)

            elif formula == "0.5 * L / c / mode":
                result = 0.5 * derived_params["L"] / derived_params["c"] / mode
                if "one_to_two_periods" in constraint:
                    result = np.clip(result, 0.1, 2.0)
                return float(result)

            elif formula == "0.3 * L / c / sqrt(mx**2 + my**2)":
                mx = derived_params.get("mx", 1)
                my = derived_params.get("my", 1)
                result = 0.3 * derived_params["L"] / derived_params["c"] / np.sqrt(mx**2 + my**2)
                if "visible_wave_motion" in constraint:
                    result = max(result, 0.05)
                return float(result)

            elif formula == "0.2 * L^2 / k / mode^2":
                result = 0.2 * (derived_params["L"] ** 2) / derived_params["k"] / (mode ** 2)
                if "visible_decay" in constraint:
                    result = max(result, 0.01)
                return float(result)

            elif formula == "0.2 * L / c / mode":
                result = 0.2 * derived_params["L"] / derived_params["c"] / mode
                if "one_period_minimum" in constraint:
                    result = max(result, 0.05)
                return float(result)

            elif formula == "0.3 * L / c":
                result = 0.3 * derived_params["L"] / derived_params["c"]
                if "visible_wave_motion" in constraint:
                    result = max(result, 0.05)
                return float(result)

            elif formula == "0.5 * L / v_magnitude":
                result = 0.5 * derived_params["L"] / derived_params["v_magnitude"]
                if "advective_time_scale" in constraint:
                    result = max(result, 0.01)
                return float(result)

            elif formula == "0.15 * L / c / mode":
                result = 0.15 * derived_params["L"] / derived_params["c"] / mode
                if "short_duration" in constraint:
                    result = np.clip(result, 0.02, 0.2)
                return float(result)

            elif formula == "0.3 * L^2 / k / (mx^2 + my^2)":
                mx = derived_params.get("mx", 1)
                my = derived_params.get("my", 1)
                result = 0.3 * (derived_params["L"] ** 2) / derived_params["k"] / (mx**2 + my**2)
                if "visible_decay" in constraint:
                    result = max(result, 0.01)
                return float(result)

        if "L" in derived_params and "c" in derived_params:
            if formula == "0.15 * L / c / mode":
                mode = derived_params.get("mode", 1)
                result = 0.15 * derived_params["L"] / derived_params["c"] / mode
                if "short_duration" in constraint:
                    result = np.clip(result, 0.02, 0.2)
                return float(result)

        if "L" in derived_params and "v" in derived_params:
            if formula == "0.5 * L / v":
                result = 0.5 * derived_params["L"] / derived_params["v"]
                return float(result)

        return 0.1

    equation_type = template.get("equation_type", "")
    if equation_type.startswith(("heat", "wave")):
        return 0.1
    return 0.0


def get_grid_from_template(template: Dict[str, Any], rng: np.random.Generator) -> Dict[str, int]:
    grid_ranges = template.get("grid_ranges", {})
    grid_specs = {}

    for dim in ["nx", "ny", "nz"]:
        if dim in grid_ranges:
            spec = grid_ranges[dim]
            param_type = spec.get("type")

            if param_type == "discrete":
                values = spec["values"]
                weights = spec.get("weights")
                grid_specs[dim] = sample_discrete(values, weights, rng)

            elif param_type == "range":
                grid_specs[dim] = int(sample_from_range(spec["min"], spec["max"], rng))

    return grid_specs


def build_physics_features(template: Dict[str, Any], params: Dict[str, Any], grid_specs: Dict[str, int], t_final: float) -> np.ndarray:
    dim = template.get("dimension", 1)
    eq_type = template.get("equation_type", "")
    solution_chars = template.get("solution_characteristics", {})

    dim_feature = {
        1: 0.0,
        2: 0.5,
        3: 1.0,
    }.get(dim, 0.5)

    smoothness = solution_chars.get("smoothness", "moderate")
    smoothness_map = {
        "very_smooth": 0.0,
        "smooth": 0.2,
        "smooth_to_moderate": 0.3,
        "moderate": 0.5,
        "smooth_to_linear": 0.3,
        "initially_discontinuous": 0.8,
        "possibly_discontinuous": 0.9,
    }
    nonlinear_feature = smoothness_map.get(smoothness, 0.5) * 0.5

    temporal = solution_chars.get("temporal_behavior", "steady")
    unsteady_map = {
        "exponential_decay": 1.0,
        "multi_exponential_decay": 1.0,
        "transient": 0.8,
        "transient_to_steady": 0.6,
        "diffusion_smoothing": 0.7,
        "oscillatory": 1.0,
        "complex_oscillatory": 1.0,
        "damped_oscillatory": 0.9,
        "high_frequency_oscillatory": 1.0,
        "multi_decay": 1.0,
        "transport_dominated": 0.7,
        "oscillatory_2d": 1.0,
        "oscillatory_3d": 1.0,
        "scale_separation": 0.8,
        "complex_reflection": 0.9,
        "steady_state": 0.0,
        "steady": 0.0,
    }
    unsteady_feature = unsteady_map.get(temporal, 0.5)

    bc_type = template.get("boundary_type", "dirichlet")
    bc_complexity_map = {
        "dirichlet": 0.1,
        "neumann": 0.3,
        "mixed": 0.5,
        "mixed_dirichlet_neumann": 0.5,
        "robin": 0.6,
        "periodic": 0.2,
        "inlet_outlet": 0.7,
        "inlet_outlet_3d": 0.8,
        "mixed_3d": 0.6,
    }
    bc_feature = bc_complexity_map.get(bc_type, 0.3)

    nx = grid_specs.get("nx", 50)
    size_feature = (nx - 11) / (401 - 11) if nx >= 11 else 0.0

    physics = np.array([
        dim_feature,
        nonlinear_feature,
        unsteady_feature,
        bc_feature,
        size_feature,
    ], dtype=np.float32)

    return physics


def build_hardware_features(rng: np.random.Generator) -> np.ndarray:
    hardware = np.array([
        rng.uniform(0.2, 0.6),
        rng.uniform(0.3, 0.6),
        rng.uniform(0.2, 0.5),
        rng.uniform(0.0, 0.3),
        rng.uniform(0.3, 0.7),
    ], dtype=np.float32)
    return hardware


def build_domain_features(template: Dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    solution_chars = template.get("solution_characteristics", {})
    expected_bias = template.get("expected_algorithm_bias", "mixed")

    accuracy_map = {
        "excellent_for_spectral": 0.9,
        "good_for_spectral": 0.7,
        "degraded": 0.4,
        "poor": 0.3,
    }
    accuracy_demand = accuracy_map.get(
        solution_chars.get("spectral_quality", "good_for_spectral"),
        0.6
    )
    accuracy_demand = np.clip(accuracy_demand + rng.uniform(-0.1, 0.1), 0.2, 1.0)

    temporal = solution_chars.get("temporal_behavior", "steady")
    if temporal in ["steady", "steady_state"]:
        realtime_demand = 0.1 + rng.uniform(0.0, 0.2)
    elif temporal in ["exponential_decay", "multi_decay"]:
        realtime_demand = 0.3 + rng.uniform(0.0, 0.3)
    else:
        realtime_demand = 0.5 + rng.uniform(0.0, 0.4)

    budget_demand = rng.uniform(0.3, 0.7)

    domain = np.array([
        accuracy_demand,
        realtime_demand,
        budget_demand,
    ], dtype=np.float32)

    return domain


def generate_problem(
    template: Dict[str, Any],
    problem_id: int,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    template_id = template["template_id"]

    params = generate_params_from_template(template, rng)
    grid_specs = get_grid_from_template(template, rng)
    t_final = derive_time_from_template(template, params, rng)

    params["nx"] = grid_specs.get("nx", 51)
    if "ny" in grid_specs:
        params["ny"] = grid_specs["ny"]
    if "nz" in grid_specs:
        params["nz"] = grid_specs["nz"]
    params["t_final"] = t_final

    physics_features = build_physics_features(template, params, grid_specs, t_final)
    hardware_features = build_hardware_features(rng)
    domain_features = build_domain_features(template, rng)

    problem = {
        "problem_id": problem_id,
        "template_id": template_id,
        "equation_type": template["equation_type"],
        "dimension": template["dimension"],
        "params": params,
        "physics_features": physics_features.tolist(),
        "hardware_features": hardware_features.tolist(),
        "domain_features": domain_features.tolist(),
        "metadata": {
            "template_name": template["name"],
            "boundary_type": template["boundary_type"],
            "solution_characteristics": template["solution_characteristics"],
            "expected_algorithm_bias": template["expected_algorithm_bias"],
            "difficulty_tags": template["difficulty_tags"],
            "source_type": template["source_type"],
            "source_reference": template["source_reference"],
            "variation_notes": template["variation_notes"],
        },
    }

    return problem


def get_template_category(template: Dict[str, Any]) -> str:
    bias = template.get("expected_algorithm_bias", "mixed")
    if bias == "spectral_friendly":
        return "spectral"
    elif bias == "fem_friendly":
        return "fem"
    elif bias == "fvm_friendly":
        return "fvm"
    else:
        return "classic"


def _build_distribution(num_problems: int, categories: List[str], weights: Dict[str, float]) -> Dict[str, int]:
    raw = {category: num_problems * weights.get(category, 0.0) for category in categories}
    distribution = {category: int(np.floor(value)) for category, value in raw.items()}
    assigned = sum(distribution.values())
    remainder = num_problems - assigned

    if remainder > 0:
        ranked = sorted(categories, key=lambda cat: (raw[cat] - distribution[cat]), reverse=True)
        for idx in range(remainder):
            distribution[ranked[idx % len(ranked)]] += 1

    return distribution


def _ensure_minimum_dimension_coverage(
    selected_templates: List[Dict[str, Any]],
    all_templates: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    needed_dims = {1, 2, 3}
    present_dims = {int(t.get("dimension", 0)) for t in selected_templates}
    missing_dims = needed_dims - present_dims
    if not missing_dims or not selected_templates:
        return selected_templates

    adjusted = list(selected_templates)
    for missing_dim in sorted(missing_dims):
        candidates = [t for t in all_templates if int(t.get("dimension", 0)) == missing_dim]
        if not candidates:
            continue
        replacement = candidates[int(rng.integers(0, len(candidates)))]
        replace_index = int(rng.integers(0, len(adjusted)))
        adjusted[replace_index] = replacement
    return adjusted


def generate_problem_set(
    templates: List[Dict[str, Any]],
    num_problems: int,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)

    template_by_bias = {"classic": [], "spectral": [], "fem": [], "fvm": []}
    for t in templates:
        cat = get_template_category(t)
        template_by_bias[cat].append(t)

    distribution = _build_distribution(
        num_problems,
        ["classic", "spectral", "fem", "fvm"],
        {"classic": 0.40, "spectral": 0.25, "fem": 0.20, "fvm": 0.15},
    )

    print(f"Target distribution: {distribution}")

    selected_templates: List[Dict[str, Any]] = []

    for category, count in distribution.items():
        if count <= 0:
            continue

        category_templates = template_by_bias[category]
        if not category_templates:
            print(f"  Warning: No templates for category {category}")
            continue

        template_order = list(rng.permutation(len(category_templates)))
        actual_count = 0
        while actual_count < count:
            template_index = template_order[actual_count % len(template_order)]
            selected_templates.append(category_templates[template_index])
            actual_count += 1

        print(f"  {category}: assigned {actual_count} problems across {len(category_templates)} templates")

    if len(selected_templates) < num_problems:
        fallback_templates = list(templates)
        while len(selected_templates) < num_problems:
            selected_templates.append(fallback_templates[len(selected_templates) % len(fallback_templates)])

    selected_templates = selected_templates[:num_problems]
    selected_templates = _ensure_minimum_dimension_coverage(selected_templates, templates, rng)

    problems = [
        generate_problem(template, problem_id, rng)
        for problem_id, template in enumerate(selected_templates)
    ]

    rng.shuffle(problems)
    for i, p in enumerate(problems):
        p["problem_id"] = i

    return problems


def summarize_problems(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
    eq_counts = {}
    dim_counts = {}
    bias_counts = {}
    bc_counts = {}
    source_counts = {}
    invalid_time_problem_ids = []

    for p in problems:
        eq = p["equation_type"]
        dim = p["dimension"]
        bias = p["metadata"]["expected_algorithm_bias"]
        bc = p["metadata"]["boundary_type"]
        source_type = p["metadata"].get("source_type", "unknown")

        eq_counts[eq] = eq_counts.get(eq, 0) + 1
        dim_counts[dim] = dim_counts.get(dim, 0) + 1
        bias_counts[bias] = bias_counts.get(bias, 0) + 1
        bc_counts[bc] = bc_counts.get(bc, 0) + 1
        source_counts[source_type] = source_counts.get(source_type, 0) + 1

        temporal_behavior = p["metadata"]["solution_characteristics"].get("temporal_behavior", "")
        is_transient = temporal_behavior not in {"steady", "steady_state"}
        if is_transient and p["equation_type"].startswith(("heat", "wave")) and float(p["params"].get("t_final", 0.0)) <= 0.0:
            invalid_time_problem_ids.append(int(p["problem_id"]))

    param_ranges = {}
    for p in problems:
        for k, v in p["params"].items():
            if k not in param_ranges:
                param_ranges[k] = {"min": v, "max": v, "values": set()}
            if isinstance(v, (int, float)):
                param_ranges[k]["min"] = min(param_ranges[k]["min"], v)
                param_ranges[k]["max"] = max(param_ranges[k]["max"], v)
            param_ranges[k]["values"].add(str(v))

    param_summary = {}
    for k, v in param_ranges.items():
        if len(v["values"]) <= 10:
            param_summary[k] = {"type": "discrete", "unique_values": len(v["values"])}
        else:
            param_summary[k] = {"type": "continuous", "min": v["min"], "max": v["max"]}

    return {
        "total_problems": len(problems),
        "equation_distribution": eq_counts,
        "dimension_distribution": dim_counts,
        "algorithm_bias_distribution": bias_counts,
        "boundary_condition_distribution": bc_counts,
        "source_type_distribution": source_counts,
        "invalid_t_final_problem_ids": invalid_time_problem_ids,
        "parameter_summary": param_summary,
    }


def main():
    parser = argparse.ArgumentParser(description="基于模板生成算法选择器问题")
    parser.add_argument("--count", type=int, default=100, help="生成问题数量")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--sample", action="store_true", help="生成 50 道样例")
    args = parser.parse_args()

    if args.sample:
        args.count = 50

    print("=" * 60)
    print("基于模板生成算法选择器问题")
    print("=" * 60)

    print(f"\n[1/3] Loading templates from {TEMPLATE_PATH}...")
    template_data = load_templates()
    templates = template_data["templates"]
    print(f"  Loaded {len(templates)} templates")

    template_by_eq = {}
    for t in templates:
        eq = t["equation_type"]
        if eq not in template_by_eq:
            template_by_eq[eq] = []
        template_by_eq[eq].append(t)

    print("\n  Templates by equation type:")
    for eq, ts in template_by_eq.items():
        print(f"    {eq}: {len(ts)} templates")

    print(f"\n[2/3] Generating {args.count} problems...")
    problems = generate_problem_set(templates, args.count, args.seed)
    print(f"  Generated {len(problems)} problems")

    print(f"\n[3/3] Summary:")
    summary = summarize_problems(problems)
    print(f"  Total: {summary['total_problems']}")
    print(f"  Equation distribution: {summary['equation_distribution']}")
    print(f"  Dimension distribution: {summary['dimension_distribution']}")
    print(f"  Algorithm bias distribution: {summary['algorithm_bias_distribution']}")
    print(f"  Boundary condition distribution: {summary['boundary_condition_distribution']}")

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "generated_at": time.time(),
        "config": {
            "num_problems": len(problems),
            "seed": args.seed,
            "template_version": template_data.get("version", "unknown"),
        },
        "summary": summary,
        "problems": problems,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n[ok] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
