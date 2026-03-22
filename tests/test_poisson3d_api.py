from fastapi.testclient import TestClient

import main


def test_extract_feature_poisson3d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "poisson3d",
            "nx": 15,
            "ny": 15,
            "nz": 15,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "poisson3d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_includes_poisson3d() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "poisson3d" in equations
    assert equations["poisson3d"]["algorithms"] == ["fdm", "fem", "bem"]


def test_solve_equation_poisson3d_fdm() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson3d",
            "algorithm_key": "fdm",
            "nx": 15,
            "ny": 15,
            "nz": 15,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "poisson3d"
    assert payload["data"]["recommended_algorithm"] == "fdm"
    assert payload["data"]["executed_algorithm"] == "fdm"
    assert payload["data"]["shape"] == [15, 15, 15]
    solve_info = payload["data"]["solve_info"]
    assert solve_info["l2_error"] >= 0.0
    assert solve_info["linf_error"] >= 0.0
    assert solve_info["boundary_residual"] <= 1e-8


def test_solve_equation_poisson3d_fem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson3d",
            "algorithm_key": "fem",
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "poisson3d"
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["shape"] == [9, 9, 9]
    solve_info = payload["data"]["solve_info"]
    assert solve_info["l2_error"] >= 0.0
    assert solve_info["linf_error"] >= 0.0
    assert solve_info["boundary_residual"] <= 1e-8


def test_solve_equation_poisson3d_bem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson3d",
            "algorithm_key": "bem",
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "poisson3d"
    assert payload["data"]["recommended_algorithm"] == "bem"
    assert payload["data"]["executed_algorithm"] == "bem"
    assert payload["data"]["shape"] == [9, 9, 9]
    solve_info = payload["data"]["solve_info"]
    assert solve_info["l2_error"] >= 0.0
    assert solve_info["linf_error"] >= 0.0
    assert solve_info["boundary_residual"] <= 1e-8


def test_auto_solve_poisson3d_supported() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/api/auto_solve",
        json={
            "question": "求解三维 Poisson 方程 -Δu = f，在立方体 [0,1]^3 上，零 Dirichlet 边界，解析解可取 u=sin(pi x)sin(pi y)sin(pi z)。",
            "parser_model": "doubao",
            "return_full_solution": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["parsed"]["physics_params"]["equation_type"] == "poisson3d"
    assert payload["data"]["solved"]["equation_type"] == "poisson3d"
    assert payload["data"]["solved"]["solve_info"]["algorithm"] in {"fdm", "fem", "bem"}
