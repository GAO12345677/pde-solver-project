from fastapi.testclient import TestClient

import main


def test_extract_feature_wave3d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "wave3d",
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
    assert payload["data"]["equation_type"] == "wave3d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_includes_wave3d() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "wave3d" in equations
    assert equations["wave3d"]["algorithms"] == ["fdm", "fem", "spectral"]


def test_solve_equation_wave3d_fdm() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave3d",
            "algorithm_key": "fdm",
            "c": 1.0,
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "t0": 0.0,
            "t1": 0.1,
            "nt": 60,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave3d"
    assert payload["data"]["recommended_algorithm"] == "fdm"
    assert payload["data"]["executed_algorithm"] == "fdm"
    assert payload["data"]["shape"] == [9, 9, 9]


def test_solve_equation_wave3d_fem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave3d",
            "algorithm_key": "fem",
            "c": 1.0,
            "nx": 7,
            "ny": 7,
            "nz": 7,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "t0": 0.0,
            "t1": 0.06,
            "nt": 18,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave3d"
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["shape"] == [7, 7, 7]


def test_solve_equation_wave3d_spectral() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave3d",
            "algorithm_key": "spectral",
            "c": 1.0,
            "nx": 9,
            "ny": 9,
            "nz": 9,
            "Lx": 1.0,
            "Ly": 1.0,
            "Lz": 1.0,
            "t0": 0.0,
            "t1": 0.1,
            "nt": 20,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave3d"
    assert payload["data"]["recommended_algorithm"] == "spectral"
    assert payload["data"]["executed_algorithm"] == "spectral"
    assert payload["data"]["shape"] == [9, 9, 9]


def test_auto_solve_wave3d_supported() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/api/auto_solve",
        json={
            "question": "求解三维波动方程 u_tt = c^2 (u_xx + u_yy + u_zz)，在 [0,1]^3 上，零 Dirichlet 边界，初始位移取 sin(pi x)sin(pi y)sin(pi z)。",
            "parser_model": "doubao",
            "return_full_solution": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["parsed"]["physics_params"]["equation_type"] == "wave3d"
    assert payload["data"]["solved"]["equation_type"] == "wave3d"
    assert payload["data"]["solved"]["solve_info"]["algorithm"] in {"fdm", "fem", "spectral"}
