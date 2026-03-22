import numpy as np

from algorithm.selector import AlgorithmSelector, build_feature_graph_dataset


def test_build_feature_graph_dataset_shape() -> None:
    X = np.random.default_rng(7).random((4, 13), dtype=np.float32)
    graphs = build_feature_graph_dataset(X)
    assert graphs["node_features"].shape == (4, 10, 5)
    assert graphs["edge_index"].shape[0] == 2
    assert graphs["edge_features"].shape[0] == 4
    assert np.allclose(graphs["node_features"][0, 0], X[0, 0:5])
    assert np.allclose(graphs["node_features"][0, 1], X[0, 5:10])
    assert np.allclose(graphs["node_features"][0, 2, 0:3], X[0, 10:13])
    assert np.allclose(graphs["node_features"][0, 7], np.array([0.55, 0.75, 0.85, 0.35, 0.15], dtype=np.float32))


def test_train_and_select_gnn_selector(tmp_path) -> None:
    selector = AlgorithmSelector(model_dir=str(tmp_path))
    train_info = selector.train_static(strategy="gnn_selector", seed=7)
    assert train_info["strategy"] == "gnn_selector"
    assert "training_summary" in train_info
    assert train_info["training_summary"]["epochs_run"] >= 1
    assert train_info["training_summary"]["best_epoch"] >= 1

    saved_path = selector.save_static()
    assert saved_path.endswith("static_gnn_selector.pkl")

    selector2 = AlgorithmSelector(model_dir=str(tmp_path))
    load_info = selector2.load_static(saved_path)
    assert "training_summary" in load_info
    assert load_info["training_summary"]["best_val_loss"] >= 0.0

    physics = np.array([0.0, 0.0, 1.0, 0.0, 0.3], dtype=float)
    hardware = np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float)
    domain = np.array([0.5, 0.5, 0.7], dtype=float)

    out = selector2.select(physics=physics, hardware=hardware, domain=domain, strategy="gnn_selector")
    assert out["strategy"] == "gnn_selector"
    assert out["algorithm_key"] in ("fdm", "fem", "spectral")
    assert "static_probs" in out
