from fastapi.testclient import TestClient

import main


def test_extract_feature_wave2d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "wave2d",
            "nx": 31,
            "ny": 31,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave2d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_includes_wave2d() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "wave2d" in equations
    assert equations["wave2d"]["algorithms"] == ["fdm", "fem", "spectral"]


def test_solve_equation_wave2d_fdm() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave2d",
            "algorithm_key": "fdm",
            "c": 1.0,
            "nx": 31,
            "ny": 31,
            "Lx": 1.0,
            "Ly": 1.0,
            "t0": 0.0,
            "t1": 0.2,
            "nt": 200,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave2d"
    assert payload["data"]["recommended_algorithm"] == "fdm"
    assert payload["data"]["executed_algorithm"] == "fdm"
    assert payload["data"]["shape"] == [31, 31]


def test_solve_equation_wave2d_fem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave2d",
            "algorithm_key": "fem",
            "c": 1.0,
            "nx": 31,
            "ny": 31,
            "Lx": 1.0,
            "Ly": 1.0,
            "t0": 0.0,
            "t1": 0.2,
            "nt": 200,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave2d"
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["shape"] == [31, 31]


def test_solve_equation_wave2d_spectral() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave2d",
            "algorithm_key": "spectral",
            "c": 1.0,
            "nx": 31,
            "ny": 31,
            "Lx": 1.0,
            "Ly": 1.0,
            "t0": 0.0,
            "t1": 0.2,
            "nt": 200,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave2d"
    assert payload["data"]["recommended_algorithm"] == "spectral"
    assert payload["data"]["executed_algorithm"] == "spectral"
    assert payload["data"]["shape"] == [31, 31]


def test_auto_solve_wave2d_supported() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/api/auto_solve",
        json={
            "question": "求解二维波动方程 u_tt = c^2 (u_xx + u_yy)，在区域 [0,1]x[0,1] 上，边界条件为零 Dirichlet 边界，初始条件 u(x,y,0)=sin(pi x)sin(pi y)。",
            "parser_model": "doubao",
            "return_full_solution": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["parsed"]["physics_params"]["equation_type"] == "wave2d"
    assert payload["data"]["solved"]["equation_type"] == "wave2d"
    assert payload["data"]["solved"]["solve_info"]["algorithm"] in {"fdm", "fem", "spectral"}
