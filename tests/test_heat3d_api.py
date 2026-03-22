from fastapi.testclient import TestClient

import main


def test_extract_feature_heat3d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "heat3d",
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "heat3d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_includes_heat3d() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "heat3d" in equations
    assert equations["heat3d"]["algorithms"] == ["fdm", "fvm", "fem"]


def test_solve_equation_heat3d_fdm() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "heat3d",
            "algorithm_key": "fdm",
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "k": 1.0,
            "t0": 0.0,
            "t1": 0.02,
            "nt": 32,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "heat3d"
    assert payload["data"]["recommended_algorithm"] == "fdm"
    assert payload["data"]["executed_algorithm"] == "fdm"
    assert payload["data"]["shape"] == [9, 9, 9]
    solve_info = payload["data"]["solve_info"]
    assert solve_info["l2_error"] >= 0.0
    assert solve_info["linf_error"] >= 0.0
    assert solve_info["boundary_residual"] <= 1e-8


def test_solve_equation_heat3d_fem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "heat3d",
            "algorithm_key": "fem",
            "nx": 7,
            "ny": 7,
            "nz": 7,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "k": 1.0,
            "t0": 0.0,
            "t1": 0.01,
            "nt": 12,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "heat3d"
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["shape"] == [7, 7, 7]
    solve_info = payload["data"]["solve_info"]
    assert solve_info["l2_error"] >= 0.0
    assert solve_info["linf_error"] >= 0.0
    assert solve_info["boundary_residual"] <= 1e-8
