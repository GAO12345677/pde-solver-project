import numpy as np

from algorithm.selector import AlgorithmSelector


def test_mlp_selector_can_train_and_select() -> None:
    selector = AlgorithmSelector(model_dir="model")
    train_info = selector.train_static(strategy="mlp_nn", seed=7)
    assert train_info["strategy"] == "mlp_nn"

    physics = np.array([0.0, 0.0, 1.0, 0.2, 0.3], dtype=float)
    hardware = np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float)
    domain = np.array([0.5, 0.9, 0.5], dtype=float)

    out = selector.select(physics=physics, hardware=hardware, domain=domain, strategy="mlp_nn")
    assert out["strategy"] == "mlp_nn"
    assert out["algorithm_key"] in {"fdm", "fem", "spectral"}
    assert "static_probs" in out
