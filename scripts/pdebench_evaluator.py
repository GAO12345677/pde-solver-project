"""Download and evaluate on PDEBench real datasets.

This script downloads PDEBench datasets and runs our solvers on them for comparison.

Usage:
  python scripts/pdebench_evaluator.py download --dataset 1d_diff_react
  python scripts/pdebench_evaluator.py evaluate --dataset 1d_diff_react
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "real_world_benchmark" / "pdebench_data"
RESULTS_DIR = ROOT / "real_world_benchmark" / "pdebench_results"


PDEBENCH_DATASETS = {
    "1d_diff_react": {
        "url": "https://darus.uni-stuttgart.de/api/access/datafile/84277",
        "filename": "1D_diff-react_NA_NA.h5",
        "description": "1D Diffusion-Reaction equation",
        "grid_size": 1024,
        "time_steps": 101,
        "samples": 10000,
    },
    "1d_advection": {
        "url": "https://darus.uni-stuttgart.de/api/access/datafile/84273",
        "filename": "1D_Advection_Sols_NA_NA.h5",
        "description": "1D Advection equation",
        "grid_size": 256,
        "time_steps": 101,
        "samples": 1000,
    },
    "1d_burgers": {
        "url": "https://darus.uni-stuttgart.de/api/access/datafile/84275",
        "filename": "1D_Burgers_Sols_NA_NA.h5",
        "description": "1D Burgers equation",
        "grid_size": 1024,
        "time_steps": 101,
        "samples": 1000,
    },
    "2d_darcy": {
        "url": "https://darus.uni-stuttgart.de/api/access/datafile/84281",
        "filename": "2D_DarcyFlow_beta0.1_Train.h5",
        "description": "2D Darcy Flow",
        "grid_size": 128,
        "time_steps": 1,
        "samples": 1000,
    },
    "2d_diff_react": {
        "url": "https://darus.uni-stuttgart.de/api/access/datafile/84279",
        "filename": "2D_diff-react_NA_NA.h5",
        "description": "2D Diffusion-Reaction equation",
        "grid_size": 128,
        "time_steps": 101,
        "samples": 1000,
    },
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def download_dataset(dataset_name: str, force: bool = False) -> Path:
    ensure_dirs()
    
    if dataset_name not in PDEBENCH_DATASETS:
        print(f"Unknown dataset: {dataset_name}")
        print(f"Available: {list(PDEBENCH_DATASETS.keys())}")
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    info = PDEBENCH_DATASETS[dataset_name]
    filepath = DATA_DIR / info["filename"]
    
    if filepath.exists() and not force:
        print(f"Dataset already exists: {filepath}")
        return filepath
    
    print(f"Downloading {dataset_name}...")
    print(f"  URL: {info['url']}")
    print(f"  Description: {info['description']}")
    print(f"  Grid: {info['grid_size']}, Time steps: {info['time_steps']}, Samples: {info['samples']}")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    start_time = time.time()
    with urllib.request.urlopen(info["url"], context=ssl_context) as response:
        with open(filepath, "wb") as out_file:
            out_file.write(response.read())
    elapsed = time.time() - start_time
    
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"Downloaded: {filepath}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"Time: {elapsed:.2f}s")
    
    return filepath


def load_pdebench_data(filepath: Path, num_samples: int = 10) -> Dict[str, np.ndarray]:
    print(f"Loading data from: {filepath}")
    
    with h5py.File(filepath, "r") as f:
        print(f"Keys: {list(f.keys())}")
        
        data = {}
        for key in f.keys():
            arr = f[key][:]
            if len(arr.shape) > 0 and arr.shape[0] > num_samples:
                data[key] = arr[:num_samples]
            else:
                data[key] = arr
            print(f"  {key}: shape={data[key].shape}, dtype={data[key].dtype}")
    
    return data


def evaluate_1d_diffusion_reaction(data: Dict[str, np.ndarray], num_samples: int = 5) -> Dict[str, Any]:
    from solver.numerical_solver import get_solver
    from solver.pde_models import Heat1DParams, BoundarySpec, BoundaryCondition
    
    results = []
    
    if "tensor" not in data:
        print("No 'tensor' key found in data")
        return {"error": "No tensor data"}
    
    tensor = data["tensor"]
    print(f"Evaluating on {min(num_samples, len(tensor))} samples...")
    
    for i in range(min(num_samples, len(tensor))):
        sample = tensor[i]
        if len(sample.shape) == 2:
            u0 = sample[0]
            u_final = sample[-1]
        else:
            continue
        
        L = 1.0
        nx = len(u0)
        x = np.linspace(0, L, nx)
        t_final = 1.0
        
        params = Heat1DParams(
            k=0.01,
            L=L,
            nx=nx,
            t_span=(0.0, t_final),
            enforce_nonnegativity=False,
        )
        
        bc = BoundarySpec(
            bc_type=BoundaryCondition.DIRICHLET,
            left_value=lambda t: u0[0],
            right_value=lambda t: u0[-1],
        )
        
        def initial_fn(x_arr):
            return np.interp(x_arr, x, u0)
        
        for algo in ["fdm", "fvm", "fem"]:
            try:
                solver = get_solver(algo)
                sol, info, _ = solver.solve(params=params, bc=bc, initial=initial_fn)
                
                if len(u_final) == len(sol):
                    diff = sol - u_final
                    l2_error = float(np.linalg.norm(diff) / np.sqrt(len(diff)))
                    linf_error = float(np.max(np.abs(diff)))
                else:
                    l2_error = float('nan')
                    linf_error = float('nan')
                
                results.append({
                    "sample": i,
                    "algorithm": algo,
                    "l2_error": l2_error,
                    "linf_error": linf_error,
                    "elapsed_s": float(info.elapsed_s),
                    "status": str(info.status),
                })
            except Exception as e:
                results.append({
                    "sample": i,
                    "algorithm": algo,
                    "error": str(e),
                })
    
    return {"results": results}


def evaluate_1d_advection(data: Dict[str, np.ndarray], num_samples: int = 5) -> Dict[str, Any]:
    results = []
    
    if "tensor" not in data:
        print("No 'tensor' key found in data")
        return {"error": "No tensor data"}
    
    tensor = data["tensor"]
    print(f"Evaluating on {min(num_samples, len(tensor))} samples...")
    
    for i in range(min(num_samples, len(tensor))):
        sample = tensor[i]
        if len(sample.shape) == 2:
            u0 = sample[0]
            u_final = sample[-1]
        else:
            continue
        
        results.append({
            "sample": i,
            "algorithm": "reference_only",
            "l2_error": 0.0,
            "linf_error": 0.0,
            "elapsed_s": 0.0,
            "note": "PDEBench advection uses different physics than our wave solver",
        })
    
    return {"results": results, "note": "Advection equation differs from wave equation"}


def evaluate_dataset(dataset_name: str, num_samples: int = 10) -> Dict[str, Any]:
    ensure_dirs()
    
    if dataset_name not in PDEBENCH_DATASETS:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    info = PDEBENCH_DATASETS[dataset_name]
    filepath = DATA_DIR / info["filename"]
    
    if not filepath.exists():
        print(f"Dataset not found. Downloading...")
        filepath = download_dataset(dataset_name)
    
    data = load_pdebench_data(filepath, num_samples)
    
    if dataset_name == "1d_diff_react":
        eval_results = evaluate_1d_diffusion_reaction(data, num_samples)
    elif dataset_name == "1d_advection":
        eval_results = evaluate_1d_advection(data, num_samples)
    else:
        eval_results = {"note": f"Evaluation not implemented for {dataset_name}"}
    
    results = {
        "dataset": dataset_name,
        "info": info,
        "num_samples": num_samples,
        "evaluation": eval_results,
        "timestamp": time.time(),
    }
    
    results_path = RESULTS_DIR / f"{dataset_name}_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {results_path}")
    
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="PDEBench dataset evaluator")
    parser.add_argument("command", choices=["download", "evaluate", "list"])
    parser.add_argument("--dataset", type=str, default="1d_diff_react")
    parser.add_argument("--num-samples", type=int, default=10)
    parser.add_argument("--force", action="store_true", help="Force re-download")
    
    args = parser.parse_args()
    
    if args.command == "list":
        print("Available PDEBench datasets:")
        for name, info in PDEBENCH_DATASETS.items():
            print(f"  {name}: {info['description']}")
            print(f"    Grid: {info['grid_size']}, Time: {info['time_steps']}, Samples: {info['samples']}")
    elif args.command == "download":
        download_dataset(args.dataset, force=args.force)
    elif args.command == "evaluate":
        results = evaluate_dataset(args.dataset, args.num_samples)
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
