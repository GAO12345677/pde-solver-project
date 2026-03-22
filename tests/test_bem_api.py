from fastapi.testclient import TestClient

import main


def test_supported_equations_includes_poisson1d_bem() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "poisson1d" in equations
    assert "bem" in equations["poisson1d"]["algorithms"]


def test_solve_equation_poisson1d_bem() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "poisson1d",
            "algorithm_key": "bem",
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
    assert payload["data"]["equation_type"] == "poisson1d"
    assert payload["data"]["recommended_algorithm"] == "bem"
    assert payload["data"]["executed_algorithm"] == "bem"
    assert payload["data"]["solve_info"]["algorithm"] == "bem"
    assert payload["data"]["solve_info"]["status"] == "steady_solved"
    assert payload["data"]["solution_preview"]["count"] == 101
