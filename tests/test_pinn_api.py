from fastapi.testclient import TestClient

import main


def test_supported_equations_includes_heat1d_pinn() -> None:
    client = TestClient(main.app)
    response = client.get("/supported_equations")
    assert response.status_code == 200
    payload = response.json()
    equations = payload["data"]["equations"]
    assert "heat1d" in equations
    assert "pinn" in equations["heat1d"]["algorithms"]


def test_solve_equation_heat1d_pinn() -> None:
    client = TestClient(main.app)
    response = client.post(
        "/solve_equation",
        json={
            "equation_type": "heat1d",
            "algorithm_key": "pinn",
            "k": 1.0,
            "L": 1.0,
            "nx": 51,
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
    assert payload["data"]["recommended_algorithm"] == "pinn"
    assert payload["data"]["executed_algorithm"] == "pinn"
    assert payload["data"]["solve_info"]["algorithm"] == "pinn"
    training_summary = payload["data"]["solve_info"]["details"]["training_summary"]
    assert "best_loss" in training_summary
    if training_summary["cache_hit"]:
        assert payload["data"]["solve_info"]["status"] == "ok_cached"
        assert training_summary["cached_adam_epochs_run"] >= 1
        assert training_summary["cached_lbfgs_steps_run"] >= 1
    else:
        assert training_summary["adam_epochs_run"] >= 1
        assert training_summary["lbfgs_steps_run"] >= 1


def test_solve_equation_heat1d_pinn_reuses_cache() -> None:
    client = TestClient(main.app)
    payload = {
        "equation_type": "heat1d",
        "algorithm_key": "pinn",
        "k": 1.0,
        "L": 1.0,
        "nx": 51,
        "t0": 0.0,
        "t1": 0.05,
        "bc_type": "dirichlet",
        "left_bc": 0.0,
        "right_bc": 0.0,
    }
    first = client.post("/solve_equation", json=payload)
    second = client.post("/solve_equation", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    second_summary = second.json()["data"]["solve_info"]["details"]["training_summary"]
    assert second.json()["data"]["solve_info"]["status"] == "ok_cached"
    assert second_summary["cache_hit"] is True
    assert second_summary["adam_epochs_run"] == 0
    assert second_summary["lbfgs_steps_run"] == 0
    assert second_summary["cached_adam_epochs_run"] >= 1
    assert second_summary["cached_lbfgs_steps_run"] >= 1
    assert second_summary["cache_origin"] in {"memory", "disk"}
