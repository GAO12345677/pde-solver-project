from fastapi.testclient import TestClient

import main


def test_extract_feature_wave1d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/extract_feature",
        json={
            "equation_type": "wave1d",
            "nx": 101,
            "boundary_condition": "dirichlet",
            "accuracy": "medium",
            "realtime": "medium",
            "resource_budget": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "wave1d"
    assert len(payload["data"]["x13"]) == 13


def test_supported_equations_endpoint() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    equations = payload["data"]["equations"]
    assert "wave1d" in equations
    assert equations["wave1d"]["algorithms"] == ["fdm", "fem", "spectral"]


def test_benchmark_latest_endpoint() -> None:
    client = TestClient(main.app)
    response = client.get("/benchmark/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    report = payload["data"]["report"]
    assert report["selector_accuracy"]
    assert report["solver_accuracy"]
    assert "recommendation_examples" in report


def test_solve_equation_wave1d() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave1d",
            "algorithm_key": "fdm",
            "c": 1.0,
            "L": 1.0,
            "nx": 101,
            "nt": 200,
            "t0": 0.0,
            "t1": 0.2,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["recommended_algorithm"] == "fdm"
    assert payload["data"]["executed_algorithm"] == "fdm"
    assert payload["data"]["solve_info"]["algorithm"] == "fdm"
    assert payload["data"]["solution_preview"]["count"] == 101
    assert payload["data"]["validation"]["finite"] is True


def test_solve_equation_wave1d_spectral() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave1d",
            "algorithm_key": "spectral",
            "c": 1.0,
            "L": 1.0,
            "nx": 101,
            "nt": 200,
            "t0": 0.0,
            "t1": 0.2,
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
    assert payload["data"]["validation"]["finite"] is True


def test_solve_equation_wave1d_spectral_neumann() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave1d",
            "algorithm_key": "spectral",
            "c": 1.0,
            "L": 1.0,
            "nx": 101,
            "nt": 200,
            "t0": 0.0,
            "t1": 0.2,
            "bc_type": "neumann",
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
    assert payload["data"]["validation"]["finite"] is True


def test_solve_equation_wave1d_fem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave1d",
            "algorithm_key": "fem",
            "c": 1.0,
            "L": 1.0,
            "nx": 101,
            "nt": 200,
            "t0": 0.0,
            "t1": 0.2,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["solve_info"]["algorithm"] == "fem"
    assert payload["data"]["solution_preview"]["count"] == 101
    assert payload["data"]["validation"]["finite"] is True


def test_solve_equation_wave1d_fem_neumann() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "wave1d",
            "algorithm_key": "fem",
            "c": 1.0,
            "L": 1.0,
            "nx": 101,
            "nt": 200,
            "t0": 0.0,
            "t1": 0.2,
            "bc_type": "neumann",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["recommended_algorithm"] == "fem"
    assert payload["data"]["executed_algorithm"] == "fem"
    assert payload["data"]["solve_info"]["algorithm"] == "fem"
    assert payload["data"]["validation"]["finite"] is True


def test_auto_solve_wave1d_is_unsteady_and_consistent() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/api/auto_solve",
        json={
            "question": "求解一维波动方程 u_tt = c^2 u_xx，在区间 [0,1] 上，边界条件 u(0,t)=u(1,t)=0，初始条件 u(x,0)=sin(pi x)",
            "parser_model": "doubao",
            "return_full_solution": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["parsed"]["physics_params"]["equation_type"] == "wave1d"
    assert data["parsed"]["physics_params"]["stationary"] is False
    assert data["solved"]["solve_info"]["status"] != "steady_initial_state"
    assert data["selected"]["algorithm_key"] == data["solved"]["solve_info"]["algorithm"]
