from fastapi.testclient import TestClient

import main


def _receive_until_terminal(websocket, limit: int = 8) -> list[dict]:
    messages = []
    for _ in range(limit):
        message = websocket.receive_json()
        messages.append(message)
        if message["type"] in {"complete", "error"}:
            break
    return messages


def test_websocket_heat1d_solve_completes() -> None:
    client = TestClient(main.app)

    with client.websocket_connect("/ws/solve/test-heat1d") as websocket:
        websocket.send_json(
            {
                "action": "solve",
                "params": {
                    "equation_type": "heat1d",
                    "algorithm_key": "fdm",
                    "nx": 21,
                    "L": 1.0,
                    "k": 1.0,
                    "t0": 0.0,
                    "t1": 0.01,
                    "bc_type": "dirichlet",
                    "left_bc": 0.0,
                    "right_bc": 0.0,
                },
            }
        )

        messages = _receive_until_terminal(websocket)

    assert messages[0]["type"] == "progress"
    assert messages[1]["type"] == "progress"
    assert messages[2]["type"] == "progress"
    assert messages[-1]["type"] == "complete"
    result = messages[-1]["result"]
    assert result["solve_info"]["algorithm"] == "fdm"
    assert "solution_preview" in result


def test_websocket_invalid_algorithm_reports_error() -> None:
    client = TestClient(main.app)

    with client.websocket_connect("/ws/solve/test-error") as websocket:
        websocket.send_json(
            {
                "action": "solve",
                "params": {
                    "equation_type": "heat1d",
                    "algorithm_key": "invalid",
                },
            }
        )

        messages = _receive_until_terminal(websocket)

    assert messages[0]["type"] == "progress"
    assert messages[-1]["type"] == "error"
    assert "algorithm_key" in messages[-1]["error"]
