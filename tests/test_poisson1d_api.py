from fastapi.testclient import TestClient

import main


def test_extract_feature_poisson1d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "poisson1d",
            "nx": 101,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "low",
            "resource_budget": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "poisson1d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_includes_poisson1d() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    equations = payload["data"]["equations"]
    assert "poisson1d" in equations
    assert equations["poisson1d"]["algorithms"] == ["fdm", "fem", "spectral"]


def test_solve_equation_poisson1d_spectral() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson1d",
            "algorithm_key": "spectral",
            "L": 1.0,
            "nx": 101,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["recommended_algorithm"] == "spectral"
    assert payload["data"]["executed_algorithm"] == "spectral"
    assert payload["data"]["solve_info"]["algorithm"] == "spectral"
    assert payload["data"]["solution_preview"]["count"] == 101


def test_auto_solve_poisson1d_is_supported() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/api/auto_solve",
        json={
            "question": "求解一维泊松方程 -u_xx = pi^2 sin(pi x)，在区间 [0,1] 上，边界条件 u(0)=u(1)=0。",
            "parser_model": "doubao",
            "return_full_solution": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["parsed"]["physics_params"]["equation_type"] == "poisson1d"
    assert data["solved"]["equation_type"] == "poisson1d"
    assert data["solved"]["solve_info"]["status"] in ("steady_solved", "ok")
