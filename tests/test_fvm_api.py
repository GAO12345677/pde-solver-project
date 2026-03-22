from fastapi.testclient import TestClient

import main


def test_supported_equations_includes_heat1d_fvm() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "heat1d" in equations
    assert "fvm" in equations["heat1d"]["algorithms"]


def test_solve_equation_heat1d_fvm() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "heat1d",
            "algorithm_key": "fvm",
            "k": 1.0,
            "L": 1.0,
            "nx": 101,
            "t0": 0.0,
            "t1": 0.05,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["equation_type"] == "heat1d"
    assert payload["data"]["recommended_algorithm"] == "fvm"
    assert payload["data"]["executed_algorithm"] == "fvm"
    assert payload["data"]["solve_info"]["algorithm"] == "fvm"
    assert payload["data"]["solution_preview"]["count"] == 101


def test_poisson1d_fvm_is_rejected() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson1d",
            "algorithm_key": "fvm",
            "L": 1.0,
            "nx": 101,
            "bc_type": "dirichlet",
            "left_bc": 0.0,
            "right_bc": 0.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNSUPPORTED_ALGORITHM"

