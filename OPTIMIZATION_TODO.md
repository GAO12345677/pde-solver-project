# Optimization Todo

## P0 API and Architecture

### 1. Unify 3D solver dispatch

- Goal: remove duplicated `heat3d` / `wave3d` / `poisson3d` parsing and dispatch logic from `/solve_equation` and `/api/auto_solve`.
- Why: the same solver branches currently exist in multiple places, which makes every new method easy to miss in one path.
- Files:
  - [api/routes.py](/D:/cursorku/api/routes.py)
- Suggested result:
  - add a shared builder for equation params
  - add a shared solver dispatch function
  - keep response shaping consistent across direct solve and auto solve
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_heat3d_api.py tests\test_poisson3d_api.py -q`

### 2. Make supported equations frontend-driven

- Goal: let the solve page read algorithm options from `/supported_equations` instead of hardcoded `switch` branches.
- Why: backend capability matrix and frontend dropdowns can drift apart.
- Files:
  - [static/src/pages/SolvePage.tsx](/D:/cursorku/static/src/pages/SolvePage.tsx)
  - [static/src/services/api.ts](/D:/cursorku/static/src/services/api.ts)
  - [static/src/types/index.ts](/D:/cursorku/static/src/types/index.ts)
- Suggested result:
  - fetch supported equations on page load
  - render equation notes and algorithm choices dynamically
  - keep local fallback only if API load fails
- Validation:
  - `D:\软件\npm.cmd run build`

## P1 Solver Quality

### 3. Add real 3D error metrics

- Goal: report `l2_error`, `linf_error`, and boundary residuals for 3D FEM/BEM/FDM baselines.
- Why: current 3D methods are runnable, but benchmarking and paper-style comparison are still thin.
- Files:
  - [solver/numerical_solver.py](/D:/cursorku/solver/numerical_solver.py)
  - [test_case/benchmark_algorithms.py](/D:/cursorku/test_case/benchmark_algorithms.py)
- Suggested result:
  - compare against manufactured solutions
  - expose consistent error fields across 3D solvers
  - include error summaries in benchmark output

### 4. Improve 3D BEM baseline stability

- Goal: replace the current teaching-style approximation with a cleaner and more explainable integral formulation.
- Why: `poisson3d/bem` works as a baseline, but it is still the weakest numerical piece in the 3D stack.
- Files:
  - [solver/numerical_solver.py](/D:/cursorku/solver/numerical_solver.py)
- Suggested result:
  - better boundary quadrature
  - clearer source and boundary term separation
  - tighter error behavior on small and medium grids

## P1 Frontend and Demo Experience

### 5. Add 3D slice controls

- Goal: let users inspect 3D solutions by slice index instead of only flat previews.
- Why: current 3D visualization is functional but not very persuasive in demos.
- Files:
  - [static/src/pages/SolvePage.tsx](/D:/cursorku/static/src/pages/SolvePage.tsx)
  - [static/src/components/SolutionChart.tsx](/D:/cursorku/static/src/components/SolutionChart.tsx)
  - [static/src/components/Heatmap.tsx](/D:/cursorku/static/src/components/Heatmap.tsx)
- Suggested result:
  - add x/y/z slice selector
  - render 2D slice heatmap for 3D arrays
  - show current slice metadata

### 6. Clean up UI text and encoding

- Goal: normalize mixed Chinese/English labels and remove mojibake text.
- Why: the app works, but the current text quality hurts presentation and trust.
- Files:
  - [static/src/pages/SolvePage.tsx](/D:/cursorku/static/src/pages/SolvePage.tsx)
  - [README.md](/D:/cursorku/README.md)
  - [QUICKSTART.md](/D:/cursorku/QUICKSTART.md)
- Suggested result:
  - consistent terminology
  - readable labels
  - cleaner docs for demo and submission

## P2 Tooling and Reliability

### 7. Standardize test commands

- Goal: make testing use the project virtual environment by default.
- Why: the system Python and `.venv` Python currently diverge, which caused confusion around `pytest`.
- Files:
  - new script recommended: [run_tests.ps1](/D:/cursorku/run_tests.ps1)
  - [README.md](/D:/cursorku/README.md)
  - [QUICKSTART.md](/D:/cursorku/QUICKSTART.md)
- Suggested result:
  - one command for common API tests
  - explicit `.venv` usage
  - no ambiguity about interpreter choice

### 8. Add websocket smoke tests

- Goal: cover websocket import and basic task execution paths with lightweight regression tests.
- Why: websocket code has already shown syntax fragility once.
- Files:
  - [api/websocket_routes.py](/D:/cursorku/api/websocket_routes.py)
  - existing websocket tests under [tests](/D:/cursorku/tests)

### 9. Remove deprecation warnings

- Goal: reduce startup noise and keep the project looking maintained.
- Why: current warnings do not block execution, but they lower polish.
- Files:
  - [main.py](/D:/cursorku/main.py)
  - dependency setup docs
- Suggested result:
  - migrate FastAPI startup handling to lifespan
  - document or replace deprecated `pynvml` dependency path

## Execution Order

1. Unify 3D solver dispatch
2. Make supported equations frontend-driven
3. Add real 3D error metrics
4. Add 3D slice controls
5. Clean up UI text and encoding
6. Standardize test commands
7. Add websocket smoke tests
8. Remove deprecation warnings
9. Improve 3D BEM baseline stability

## Progress Tracking

- [x] 1. Unify 3D solver dispatch
- [x] 2. Make supported equations frontend-driven
- [x] 3. Add real 3D error metrics
- [x] 4. Add 3D slice controls
- [x] 5. Clean up UI text and encoding
- [x] 6. Standardize test commands
- [x] 7. Add websocket smoke tests
- [x] 8. Remove deprecation warnings
- [x] 9. Improve 3D BEM baseline stability
