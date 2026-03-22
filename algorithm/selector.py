"""Algorithm selection layer (mapping function M: F × H × D → A).

This module provides an `AlgorithmSelector` class implementing two strategies:
- Static selection (supervised learning): RandomForest / XGBoost classifier
- Dynamic adjustment (reinforcement learning): lightweight Q-learning agent

The goal is to make the framework **directly runnable** on Windows 10/11 with
Python 3.10+, while keeping the implementation modular and extensible.

Important practical notes:
- The paper mentions typical application cases (e.g. geological prospecting,
  hydrological runoff). Here we provide a small, *representative* synthetic dataset
  that mirrors those scenarios. Replace `build_typical_case_dataset()` with your
  real logged/annotated dataset when available.
- RL in production would typically use a more advanced library/algorithm. Here we
  implement a minimal Q-learning agent to satisfy "可运行 + 可扩展" requirements.
"""

from __future__ import annotations

import os
import pickle
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from config.constants import ALGORITHM_CANDIDATES_BY_KEY, RequirementLevel


class AlgorithmSelectionError(ValueError):
    """Raised when selection, evaluation, or model I/O fails."""


StrategyName = Literal["static_rf", "static_xgb", "dynamic_rl", "mlp_nn", "gnn_selector"]


def _ensure_model_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _validate_vector(name: str, vec: np.ndarray, expected_len: int) -> np.ndarray:
    try:
        arr = np.asarray(vec, dtype=float).reshape(-1)
    except Exception as e:  # noqa: BLE001
        raise AlgorithmSelectionError(f"{name} 特征向量无法转换为数值数组: {e}") from e
    if arr.shape[0] != expected_len:
        raise AlgorithmSelectionError(f"{name} 特征向量维度不匹配：期望 {expected_len}，实际 {arr.shape[0]}")
    if np.any(np.isnan(arr)) or np.any(~np.isfinite(arr)):
        raise AlgorithmSelectionError(f"{name} 特征向量包含 NaN/Inf，请检查归一化与输入。")
    return arr


def concat_features(physics: np.ndarray, hardware: np.ndarray, domain: np.ndarray) -> np.ndarray:
    """Concatenate normalized feature vectors into a single ML input."""
    p = _validate_vector("Physics", physics, 5)
    h = _validate_vector("Hardware", hardware, 5)
    d = _validate_vector("Domain", domain, 3)
    x = np.concatenate([p, h, d], axis=0).astype(np.float32)
    if x.shape[0] != 13:
        raise AlgorithmSelectionError("拼接后特征维度应为 13。")
    return x


# =========================
# Multi-dimensional evaluation (paper-aligned)
# =========================


@dataclass(frozen=True)
class AlgoScore:
    """Quantified evaluation result for an algorithm candidate."""

    accuracy_score: float  # [0,1]
    convergence_score: float  # [0,1]
    resource_score: float  # [0,1] (higher = less resource consumption)
    total: float  # weighted sum in [0,1]


def evaluate_algorithm(
    algorithm_key: str,
    physics: np.ndarray,
    hardware: np.ndarray,
    domain: np.ndarray,
) -> Tuple[AlgoScore, str]:
    """Compute a paper-style multi-dimensional score and a rationale string.

    This is a *proxy evaluator* for demonstration and for RL reward shaping.
    Replace with real measurements (solver runs, profiling, error metrics) when available.
    """
    x = concat_features(physics, hardware, domain)

    # Interpret some signals (all already in [0,1])
    dim = x[0]
    nonlinear = x[1]
    unsteady = x[2]
    problem_size = x[4]
    hw_parallel = x[9]
    vram = x[11]
    acc_need = x[10]  # domain accuracy scalar
    rt_need = x[11]  # NOTE: careful index? domain realtime scalar is at 11? Actually:
    # layout: p(0-4), h(5-9), d(10-12)
    # so d[0]=10 accuracy, d[1]=11 realtime, d[2]=12 resource_budget
    rt_need = x[11]
    resource_budget = x[12]

    # Base performance priors by algorithm (heuristic)
    priors = {
        "fdm": {"accuracy": 0.55, "conv": 0.75, "resource": 0.85},
        "fem": {"accuracy": 0.75, "conv": 0.70, "resource": 0.60},
        "spectral": {"accuracy": 0.92, "conv": 0.65, "resource": 0.55},
    }
    if algorithm_key not in priors:
        raise AlgorithmSelectionError(f"未知算法 key: {algorithm_key!r}")
    p0 = priors[algorithm_key]

    # Accuracy: spectral benefits high accuracy demand & smooth/steady/linear; FEM handles complexity.
    accuracy = p0["accuracy"]
    if algorithm_key == "spectral":
        accuracy += 0.10 * (1 - nonlinear) * (1 - unsteady)
        accuracy += 0.10 * acc_need
        accuracy -= 0.15 * dim  # higher dim -> harder for spectral in this toy model
    elif algorithm_key == "fem":
        accuracy += 0.10 * dim
        accuracy += 0.05 * nonlinear
        accuracy += 0.05 * unsteady
    else:  # fdm
        accuracy += 0.05 * (1 - dim)
        accuracy += 0.05 * (1 - problem_size)

    # Convergence: toy proxy depending on stiffness/complexity
    conv = p0["conv"]
    conv -= 0.10 * nonlinear
    conv -= 0.05 * unsteady
    if algorithm_key == "fem":
        conv += 0.05 * dim
    if algorithm_key == "spectral":
        conv += 0.05 * (1 - unsteady)

    # Resource: penalize big problems, reward GPU parallel, compare to resource budget
    resource = p0["resource"]
    resource -= 0.25 * problem_size
    resource += 0.15 * hw_parallel
    if algorithm_key == "spectral":
        resource -= 0.05  # FFT/transform overhead in this toy model
    if algorithm_key == "fem":
        resource -= 0.05 * nonlinear
    if algorithm_key == "fdm":
        resource += 0.05 * (1 - dim)

    # Apply budget pressure: if realtime need high, reward higher convergence/resource efficiency
    # If resource budget is tight (smaller), penalize resource usage more.
    w_acc = 0.45 + 0.15 * acc_need
    w_conv = 0.25 + 0.10 * rt_need
    w_res = 0.30 + 0.20 * (1 - resource_budget)
    w_sum = w_acc + w_conv + w_res
    w_acc, w_conv, w_res = w_acc / w_sum, w_conv / w_sum, w_res / w_sum

    accuracy = float(np.clip(accuracy, 0.0, 1.0))
    conv = float(np.clip(conv, 0.0, 1.0))
    resource = float(np.clip(resource, 0.0, 1.0))
    total = float(np.clip(w_acc * accuracy + w_conv * conv + w_res * resource, 0.0, 1.0))

    reason = (
        f"评分依据(代理)：精度权重={w_acc:.2f}、收敛/效率权重={w_conv:.2f}、资源权重={w_res:.2f}；"
        f"精度={accuracy:.2f}、收敛/效率={conv:.2f}、资源利用={resource:.2f}。"
    )
    return AlgoScore(accuracy_score=accuracy, convergence_score=conv, resource_score=resource, total=total), reason


# =========================
# Typical-case dataset (paper-aligned proxy)
# =========================


def build_typical_case_dataset(seed: int = 42) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Build a small representative dataset.

    Returns:
        X: (N, 13) normalized feature matrix
        y: (N,) integer labels
        label_keys: mapping index -> algorithm key
    """
    rng = np.random.default_rng(seed)

    label_keys = ["fdm", "fem", "spectral"]
    key_to_idx = {k: i for i, k in enumerate(label_keys)}

    def jitter(x: np.ndarray, scale: float = 0.03) -> np.ndarray:
        return np.clip(x + rng.normal(0.0, scale, size=x.shape), 0.0, 1.0)

    samples: List[np.ndarray] = []
    labels: List[int] = []

    # Case A: hydrological runoff (often 1D/2D, unsteady, realtime medium/high, resource constrained) -> FDM/FEM
    for _ in range(80):
        physics = np.array([0.0, 0.2, 1.0, 0.2, 0.3], dtype=float)  # dim~1, linear-ish, unsteady, bc, size medium
        hardware = np.array([0.0, 0.3, 0.2, 0.0, 0.4], dtype=float)  # CPU-ish
        domain = np.array([0.5, 1.0, 0.5], dtype=float)  # accuracy med, realtime high, budget med
        x = np.concatenate([jitter(physics), jitter(hardware), jitter(domain)])
        samples.append(x)
        labels.append(key_to_idx["fdm"])

    # Case B: geological prospecting (3D, nonlinear, possibly unsteady, large scale) -> FEM
    for _ in range(90):
        physics = np.array([1.0, 1.0, 0.7, 0.6, 0.9], dtype=float)  # dim~3, nonlinear, semi-unsteady, large
        hardware = np.array([0.7, 0.8, 0.7, 0.6, 1.0], dtype=float)  # GPU-ish
        domain = np.array([0.5, 0.5, 0.7], dtype=float)  # accuracy med, realtime med, budget ok
        x = np.concatenate([jitter(physics), jitter(hardware), jitter(domain)])
        samples.append(x)
        labels.append(key_to_idx["fem"])

    # Case C: high-accuracy steady linear benchmark (1D/2D, steady, linear, smooth) -> Spectral
    for _ in range(70):
        physics = np.array([0.5, 0.0, 0.0, 0.2, 0.4], dtype=float)  # dim~2, linear, steady, moderate size
        hardware = np.array([0.7, 0.5, 0.5, 0.5, 1.0], dtype=float)
        domain = np.array([1.0, 0.2, 0.8], dtype=float)  # accuracy high, realtime low, budget ok
        x = np.concatenate([jitter(physics), jitter(hardware), jitter(domain)])
        samples.append(x)
        labels.append(key_to_idx["spectral"])

    X = np.stack(samples, axis=0).astype(np.float32)
    y = np.array(labels, dtype=int)
    return X, y, label_keys


def build_feature_graph_dataset(X: np.ndarray) -> Dict[str, np.ndarray]:
    """Convert x13 tabular features into a richer relational graph dataset.

    Nodes:
    - 0: physics aggregate
    - 1: hardware aggregate
    - 2: domain aggregate
    - 3: equation-type relation node
    - 4: accuracy-demand node
    - 5: realtime-demand node
    - 6: resource-budget node
    - 7: fdm prototype
    - 8: fem prototype
    - 9: spectral prototype
    """
    arr = np.asarray(X, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] != 13:
        raise AlgorithmSelectionError("GNN 图数据构建要求输入形状为 (N, 13)。")

    physics = arr[:, 0:5]
    hardware = arr[:, 5:10]
    domain = np.pad(arr[:, 10:13], ((0, 0), (0, 2)), mode="constant")

    equation_type = np.stack(
        [
            arr[:, 0],
            arr[:, 1],
            arr[:, 2],
            1.0 - arr[:, 0],
            arr[:, 4],
        ],
        axis=1,
    ).astype(np.float32)
    accuracy_node = np.stack(
        [
            arr[:, 10],
            arr[:, 10] ** 2,
            1.0 - arr[:, 10],
            arr[:, 12],
            arr[:, 0],
        ],
        axis=1,
    ).astype(np.float32)
    realtime_node = np.stack(
        [
            arr[:, 11],
            arr[:, 11] ** 2,
            1.0 - arr[:, 11],
            arr[:, 9],
            arr[:, 2],
        ],
        axis=1,
    ).astype(np.float32)
    budget_node = np.stack(
        [
            arr[:, 12],
            arr[:, 12] ** 2,
            1.0 - arr[:, 12],
            arr[:, 9],
            arr[:, 4],
        ],
        axis=1,
    ).astype(np.float32)

    algo_prototypes = np.array(
        [
            [0.55, 0.75, 0.85, 0.35, 0.15],
            [0.75, 0.70, 0.60, 0.65, 0.55],
            [0.92, 0.65, 0.55, 0.85, 0.45],
        ],
        dtype=np.float32,
    )

    node_features = np.concatenate(
        [
            np.stack([physics, hardware, domain, equation_type, accuracy_node, realtime_node, budget_node], axis=1),
            np.broadcast_to(algo_prototypes[None, :, :], (arr.shape[0], 3, 5)).copy(),
        ],
        axis=1,
    ).astype(np.float32)

    edges: List[Tuple[int, int, float, float]] = []
    aggregate_nodes = [0, 1, 2]
    relation_nodes = [3, 4, 5, 6]
    algo_nodes = [7, 8, 9]

    for i in aggregate_nodes:
        for j in aggregate_nodes:
            if i != j:
                edges.append((i, j, 0.25, 0.0))

    for src in aggregate_nodes:
        for dst in relation_nodes:
            edges.append((src, dst, 0.50, 0.5))
            edges.append((dst, src, 0.50, -0.5))

    for src in relation_nodes:
        for dst in algo_nodes:
            edges.append((src, dst, 0.75, 1.0))
            edges.append((dst, src, 0.75, -1.0))

    for src in aggregate_nodes:
        for dst in algo_nodes:
            edges.append((src, dst, 0.35, 0.25))

    edge_index = np.array([[src for src, _, _, _ in edges], [dst for _, dst, _, _ in edges]], dtype=np.int64)
    edge_features = np.zeros((arr.shape[0], len(edges), 5), dtype=np.float32)

    for edge_idx, (src, dst, base_strength, direction) in enumerate(edges):
        src_feat = node_features[:, src, :]
        dst_feat = node_features[:, dst, :]
        mean_abs_diff = np.mean(np.abs(src_feat - dst_feat), axis=1)
        mean_product = np.mean(src_feat * dst_feat, axis=1)
        if src in aggregate_nodes and dst in aggregate_nodes:
            relation_type = 0.0
        elif (src in aggregate_nodes and dst in relation_nodes) or (src in relation_nodes and dst in aggregate_nodes):
            relation_type = 1.0
        elif src in relation_nodes and dst in algo_nodes:
            relation_type = 2.0
        elif src in algo_nodes and dst in relation_nodes:
            relation_type = 3.0
        else:
            relation_type = 4.0
        edge_features[:, edge_idx, :] = np.stack(
            [
                np.full((arr.shape[0],), base_strength, dtype=np.float32),
                mean_abs_diff.astype(np.float32),
                mean_product.astype(np.float32),
                np.full((arr.shape[0],), relation_type / 4.0, dtype=np.float32),
                np.full((arr.shape[0],), 1.0 if direction > 0 else 0.0, dtype=np.float32),
            ],
            axis=1,
        )

    return {
        "node_features": node_features,
        "edge_index": edge_index,
        "edge_features": edge_features,
    }


class _SimpleGraphConvNet:
    """A relational graph selector built only with torch."""

    def __init__(
        self,
        seed: int = 42,
        hidden_dim: int = 16,
        epochs: int = 180,
        lr: float = 1e-2,
        patience: int = 18,
        min_delta: float = 1e-4,
        validation_fraction: float = 0.2,
    ) -> None:
        try:
            import torch
            import torch.nn as nn
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError("无法导入 torch，无法训练 GNN 原型。请确认 requirements 已安装。") from e

        self._torch = torch
        self._nn = nn
        self.hidden_dim = int(hidden_dim)
        self.epochs = int(epochs)
        self.lr = float(lr)
        self.seed = int(seed)
        self.patience = int(patience)
        self.min_delta = float(min_delta)
        self.validation_fraction = float(validation_fraction)
        self.num_classes: Optional[int] = None
        self.net: Optional[Any] = None
        self._graph_cache: Dict[str, Dict[str, np.ndarray]] = {}
        self.training_summary: Dict[str, Any] = {}

    def __getstate__(self) -> Dict[str, Any]:
        state = {
            "seed": self.seed,
            "hidden_dim": self.hidden_dim,
            "epochs": self.epochs,
            "lr": self.lr,
            "patience": self.patience,
            "min_delta": self.min_delta,
            "validation_fraction": self.validation_fraction,
            "num_classes": self.num_classes,
            "training_summary": self.training_summary,
            "net_state_dict": None,
        }
        if self.net is not None:
            state["net_state_dict"] = self.net.state_dict()
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__init__(
            seed=int(state.get("seed", 42)),
            hidden_dim=int(state.get("hidden_dim", 16)),
            epochs=int(state.get("epochs", 180)),
            lr=float(state.get("lr", 1e-2)),
            patience=int(state.get("patience", 18)),
            min_delta=float(state.get("min_delta", 1e-4)),
            validation_fraction=float(state.get("validation_fraction", 0.2)),
        )
        self.num_classes = state.get("num_classes")
        self.training_summary = state.get("training_summary", {})
        net_state_dict = state.get("net_state_dict")
        if self.num_classes is not None and net_state_dict is not None:
            self.net = self._build_net(in_dim=5, edge_dim=5, num_classes=int(self.num_classes))
            self.net.load_state_dict(net_state_dict)

    def _build_net(self, in_dim: int, edge_dim: int, num_classes: int) -> Any:
        torch = self._torch
        nn = self._nn

        class RelationalGraphBlock(nn.Module):
            def __init__(self, in_features: int, edge_features: int, out_features: int) -> None:
                super().__init__()
                self.lin_self = nn.Linear(in_features, out_features)
                self.lin_src = nn.Linear(in_features, out_features)
                self.lin_edge = nn.Linear(edge_features, out_features)

            def forward(self, x: Any, edge_index: Any, edge_attr: Any) -> Any:
                src, dst = edge_index
                batch_size, num_nodes, _ = x.shape
                out_dim = self.lin_self.out_features
                agg = torch.zeros((batch_size, num_nodes, out_dim), dtype=x.dtype, device=x.device)
                deg = torch.zeros((batch_size, num_nodes, 1), dtype=x.dtype, device=x.device)

                src_feat = x[:, src, :]
                msg = torch.relu(self.lin_src(src_feat) + self.lin_edge(edge_attr))
                for edge_pos in range(edge_index.shape[1]):
                    target = int(dst[edge_pos].item())
                    agg[:, target, :] += msg[:, edge_pos, :]
                    deg[:, target, :] += 1.0

                deg = deg.clamp(min=1.0)
                return torch.relu(self.lin_self(x) + agg / deg)

        class Net(nn.Module):
            def __init__(self, hidden_dim: int, out_dim: int) -> None:
                super().__init__()
                self.block1 = RelationalGraphBlock(in_dim, edge_dim, hidden_dim)
                self.block2 = RelationalGraphBlock(hidden_dim, edge_dim, hidden_dim)
                self.head = nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, out_dim),
                )

            def forward(self, x: Any, edge_index: Any, edge_attr: Any) -> Any:
                h = self.block1(x, edge_index, edge_attr)
                h = self.block2(h, edge_index, edge_attr)
                algo_nodes = h[:, 7:10, :]
                pooled = algo_nodes.mean(dim=1)
                return self.head(pooled)

        return Net(self.hidden_dim, num_classes)

    @staticmethod
    def _cache_key(X: np.ndarray) -> str:
        arr = np.ascontiguousarray(np.asarray(X, dtype=np.float32))
        digest = hashlib.sha1(arr.view(np.uint8)).hexdigest()
        return f"{arr.shape}:{digest}"

    def _graphify(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        key = self._cache_key(X)
        if key not in self._graph_cache:
            self._graph_cache[key] = build_feature_graph_dataset(np.asarray(X, dtype=np.float32))
        return self._graph_cache[key]

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_SimpleGraphConvNet":
        torch = self._torch
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.int64).reshape(-1)
        if X_arr.shape[0] < 8:
            train_idx = np.arange(X_arr.shape[0])
            val_idx = np.arange(X_arr.shape[0])
        else:
            rng = np.random.default_rng(self.seed)
            indices = np.arange(X_arr.shape[0])
            rng.shuffle(indices)
            split = max(1, int(X_arr.shape[0] * (1.0 - self.validation_fraction)))
            split = min(split, X_arr.shape[0] - 1)
            train_idx = indices[:split]
            val_idx = indices[split:]

        graphs = self._graphify(X_arr)
        labels = np.asarray(y, dtype=np.int64).reshape(-1)
        self.num_classes = int(np.max(labels)) + 1
        self.net = self._build_net(
            in_dim=graphs["node_features"].shape[-1],
            edge_dim=graphs["edge_features"].shape[-1],
            num_classes=self.num_classes,
        )

        x_tensor = torch.tensor(graphs["node_features"], dtype=torch.float32)
        y_tensor = torch.tensor(labels, dtype=torch.long)
        edge_index = torch.tensor(graphs["edge_index"], dtype=torch.long)
        edge_attr = torch.tensor(graphs["edge_features"], dtype=torch.float32)
        train_idx_tensor = torch.tensor(train_idx, dtype=torch.long)
        val_idx_tensor = torch.tensor(val_idx, dtype=torch.long)

        optimizer = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        criterion = self._nn.CrossEntropyLoss()
        best_state: Optional[Dict[str, Any]] = None
        best_val_loss = float("inf")
        stale_rounds = 0
        best_epoch = 0
        epochs_run = 0
        early_stopped = False

        self.net.train()
        for epoch in range(self.epochs):
            epochs_run = epoch + 1
            optimizer.zero_grad()
            logits = self.net(x_tensor, edge_index, edge_attr)
            train_loss = criterion(logits[train_idx_tensor], y_tensor[train_idx_tensor])
            train_loss.backward()
            optimizer.step()

            self.net.eval()
            with torch.no_grad():
                val_logits = self.net(x_tensor, edge_index, edge_attr)
                val_loss = float(criterion(val_logits[val_idx_tensor], y_tensor[val_idx_tensor]).item())
            self.net.train()

            if val_loss + self.min_delta < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch + 1
                best_state = {
                    key: value.detach().cpu().clone()
                    for key, value in self.net.state_dict().items()
                }
                stale_rounds = 0
            else:
                stale_rounds += 1
                if stale_rounds >= self.patience:
                    early_stopped = True
                    break

        if best_state is not None:
            self.net.load_state_dict(best_state)
        self.training_summary = {
            "epochs_configured": self.epochs,
            "epochs_run": epochs_run,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "early_stopped": early_stopped,
            "patience": self.patience,
            "validation_fraction": self.validation_fraction,
            "hidden_dim": self.hidden_dim,
        }
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.net is None or self.num_classes is None:
            raise AlgorithmSelectionError("GNN 模型尚未训练。")
        torch = self._torch
        graphs = self._graphify(np.asarray(X, dtype=np.float32))
        x_tensor = torch.tensor(graphs["node_features"], dtype=torch.float32)
        edge_index = torch.tensor(graphs["edge_index"], dtype=torch.long)
        edge_attr = torch.tensor(graphs["edge_features"], dtype=torch.float32)

        self.net.eval()
        with torch.no_grad():
            logits = self.net(x_tensor, edge_index, edge_attr)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


# =========================
# Dynamic adjustment (RL): minimal Q-learning
# =========================


def _discretize(x: np.ndarray, bins: int = 5) -> Tuple[int, ...]:
    """Discretize [0,1] continuous vector into a tuple state."""
    x = np.clip(np.asarray(x, dtype=float).reshape(-1), 0.0, 1.0)
    q = np.floor(x * (bins - 1e-9) * bins).astype(int)
    q = np.clip(q, 0, bins - 1)
    return tuple(int(v) for v in q.tolist())


@dataclass
class QLearningAgent:
    """A minimal tabular Q-learning agent for dynamic algorithm adjustment."""

    actions: List[str]
    alpha: float = 0.15
    gamma: float = 0.95
    epsilon: float = 0.15
    bins: int = 5
    q: Dict[Tuple[int, ...], np.ndarray] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.q is None:
            self.q = {}

    def _q_row(self, state: Tuple[int, ...]) -> np.ndarray:
        if state not in self.q:
            self.q[state] = np.zeros((len(self.actions),), dtype=np.float32)
        return self.q[state]

    def act(self, state_vec: np.ndarray, explore: bool = True) -> str:
        s = _discretize(state_vec, bins=self.bins)
        q_row = self._q_row(s)
        if explore and np.random.rand() < self.epsilon:
            return self.actions[int(np.random.randint(0, len(self.actions)))]
        return self.actions[int(np.argmax(q_row))]

    def update(self, s_vec: np.ndarray, a_key: str, reward: float, s2_vec: np.ndarray) -> None:
        s = _discretize(s_vec, bins=self.bins)
        s2 = _discretize(s2_vec, bins=self.bins)
        q_s = self._q_row(s)
        q_s2 = self._q_row(s2)
        try:
            a = self.actions.index(a_key)
        except ValueError as e:
            raise AlgorithmSelectionError(f"RL 动作不在动作集合中: {a_key!r}") from e
        td_target = float(reward) + self.gamma * float(np.max(q_s2))
        q_s[a] = q_s[a] + self.alpha * (td_target - q_s[a])


# =========================
# AlgorithmSelector (core mapping M)
# =========================


class AlgorithmSelector:
    """Core selector implementing M: F×H×D -> A with switchable strategies."""

    def __init__(self, model_dir: str = "model") -> None:
        self.model_dir = model_dir
        _ensure_model_dir(self.model_dir)

        self.static_model: Optional[Any] = None
        self.static_label_keys: Optional[List[str]] = None
        self.static_strategy: StrategyName = "static_rf"

        self.rl_agent: Optional[QLearningAgent] = None
        self.dynamic_strategy: StrategyName = "dynamic_rl"

    @staticmethod
    def _force_single_thread_static_model(model: Any) -> Any:
        """Normalize sklearn-style models for restricted Windows environments."""
        if hasattr(model, "n_jobs"):
            try:
                model.n_jobs = 1
            except Exception:
                pass
        return model

    # ---------- Static selection (supervised learning) ----------

    def train_static(self, strategy: StrategyName = "static_rf", seed: int = 42) -> Dict[str, Any]:
        """Train a static selector (RF, XGB, MLP, or GNN prototype) using proxy data."""
        X, y, label_keys = build_typical_case_dataset(seed=seed)

        if strategy == "static_rf":
            try:
                from sklearn.ensemble import RandomForestClassifier  # type: ignore
            except Exception as e:  # noqa: BLE001
                raise AlgorithmSelectionError(
                    "无法导入 scikit-learn。请执行 `pip install -r requirements.txt`。"
                ) from e
            model = RandomForestClassifier(
                n_estimators=300,
                random_state=seed,
                # Keep training single-process so it works reliably in constrained
                # Windows test environments where joblib pipe creation can fail.
                n_jobs=1,
            )
        elif strategy == "static_xgb":
            try:
                from xgboost import XGBClassifier  # type: ignore
            except Exception as e:  # noqa: BLE001
                raise AlgorithmSelectionError("无法导入 xgboost。请执行 `pip install -r requirements.txt`。") from e
            model = XGBClassifier(
                n_estimators=500,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=seed,
                eval_metric="mlogloss",
                tree_method="hist",
            )
        elif strategy == "mlp_nn":
            try:
                from sklearn.neural_network import MLPClassifier  # type: ignore
            except Exception as e:  # noqa: BLE001
                raise AlgorithmSelectionError(
                    "无法导入 sklearn.neural_network.MLPClassifier。请确认 scikit-learn 已安装。"
                ) from e
            model = MLPClassifier(
                hidden_layer_sizes=(32, 16),
                activation="relu",
                solver="adam",
                alpha=1e-4,
                batch_size=32,
                learning_rate_init=1e-3,
                max_iter=600,
                random_state=seed,
                early_stopping=True,
                validation_fraction=0.15,
            )
        elif strategy == "gnn_selector":
            model = _SimpleGraphConvNet(
                seed=seed,
                hidden_dim=16,
                epochs=180,
                lr=1e-2,
                patience=18,
                min_delta=1e-4,
                validation_fraction=0.2,
            )
        else:
            raise AlgorithmSelectionError(f"未知静态策略: {strategy!r}，请使用 static_rf/static_xgb/mlp_nn/gnn_selector。")

        model.fit(X, y)
        self.static_model = self._force_single_thread_static_model(model)
        self.static_label_keys = label_keys
        self.static_strategy = strategy
        result = {"strategy": strategy, "num_samples": int(X.shape[0]), "labels": label_keys}
        training_summary = getattr(model, "training_summary", None)
        if training_summary:
            result["training_summary"] = training_summary
        return result

    def save_static(self, filename: Optional[str] = None) -> str:
        """Save trained static model to model_dir."""
        if self.static_model is None or self.static_label_keys is None:
            raise AlgorithmSelectionError("静态模型尚未训练，无法保存。请先调用 train_static().")
        fn = filename or f"static_{self.static_strategy}.pkl"
        path = os.path.join(self.model_dir, fn)
        payload = {
            "strategy": self.static_strategy,
            "label_keys": self.static_label_keys,
            "model": self.static_model,
            "training_summary": getattr(self.static_model, "training_summary", None),
        }
        try:
            with open(path, "wb") as f:
                pickle.dump(payload, f)
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError(f"保存静态模型失败: {e}") from e
        return path

    def load_static(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Load static model from disk (offline loading)."""
        p = path or os.path.join(self.model_dir, "static_static_rf.pkl")
        try:
            with open(p, "rb") as f:
                payload = pickle.load(f)
        except FileNotFoundError as e:
            raise AlgorithmSelectionError(
                f"静态模型文件不存在: {p!r}。请先训练并保存，或传入正确路径。"
            ) from e
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError(f"加载静态模型失败: {e}") from e

        self.static_model = self._force_single_thread_static_model(payload.get("model"))
        self.static_label_keys = payload.get("label_keys")
        self.static_strategy = payload.get("strategy", "static_rf")
        if self.static_model is not None and payload.get("training_summary") is not None:
            setattr(self.static_model, "training_summary", payload.get("training_summary"))
        if self.static_model is None or not self.static_label_keys:
            raise AlgorithmSelectionError("静态模型文件内容不完整。请重新训练/保存。")
        result = {"strategy": self.static_strategy, "labels": self.static_label_keys, "path": p}
        training_summary = getattr(self.static_model, "training_summary", None)
        if training_summary:
            result["training_summary"] = training_summary
        return result

    def _load_or_train_static(self, strategy: StrategyName) -> None:
        """Ensure the requested static selector is available."""
        expected_path = os.path.join(self.model_dir, f"static_{strategy}.pkl")
        if self.static_model is not None and self.static_label_keys and self.static_strategy == strategy:
            return
        try:
            self.load_static(path=expected_path)
        except AlgorithmSelectionError:
            self.train_static(strategy=strategy)
            self.save_static(filename=f"static_{strategy}.pkl")

    def predict_static(self, physics: np.ndarray, hardware: np.ndarray, domain: np.ndarray) -> Tuple[str, Dict[str, float]]:
        """Predict best algorithm key using the trained static model."""
        if self.static_model is None or not self.static_label_keys:
            raise AlgorithmSelectionError("静态模型未加载/未训练。请先调用 train_static() 或 load_static().")
        self._force_single_thread_static_model(self.static_model)
        x = concat_features(physics, hardware, domain).reshape(1, -1)
        try:
            proba = self.static_model.predict_proba(x)[0]
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError(f"静态模型推理失败: {e}") from e
        idx = int(np.argmax(proba))
        key = self.static_label_keys[idx]
        probs = {self.static_label_keys[i]: float(proba[i]) for i in range(len(self.static_label_keys))}
        return key, probs

    # ---------- Dynamic adjustment (reinforcement learning) ----------

    def init_dynamic(self, seed: int = 42) -> Dict[str, Any]:
        """Initialize RL agent for dynamic adjustment."""
        np.random.seed(seed)
        actions = ["fdm", "fem", "spectral"]
        self.rl_agent = QLearningAgent(actions=actions)
        return {"strategy": "dynamic_rl", "actions": actions}

    def train_dynamic(self, episodes: int = 200, seed: int = 42) -> Dict[str, Any]:
        """Train RL agent using the proxy evaluator as reward signal.

        Training task:
        - focus on unsteady settings where dynamic adjustment is meaningful
        - state = concatenated feature vector (13 dims)
        - reward = selected algorithm's total score (0..1), shaped by unsteady penalty/bonus
        """
        if self.rl_agent is None:
            self.init_dynamic(seed=seed)
        assert self.rl_agent is not None

        rng = np.random.default_rng(seed)
        rewards: List[float] = []

        for _ in range(int(episodes)):
            # Sample a random unsteady scenario (normalized features)
            physics = np.array(
                [rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0), 1.0, rng.uniform(0.0, 1.0), rng.uniform(0.1, 1.0)],
                dtype=float,
            )
            hardware = np.array(
                [rng.uniform(0.0, 1.0), rng.uniform(0.1, 1.0), rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0)],
                dtype=float,
            )
            domain = np.array([rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0), rng.uniform(0.2, 1.0)], dtype=float)
            s = concat_features(physics, hardware, domain)

            a = self.rl_agent.act(s, explore=True)
            score, _ = evaluate_algorithm(a, physics, hardware, domain)
            # Encourage adaptation in unsteady cases: if unsteady and realtime high, prefer efficient solvers.
            shaped_reward = float(score.total) + 0.05 * float(domain[1])  # realtime pressure
            shaped_reward = float(np.clip(shaped_reward, 0.0, 1.0))

            # Next state: small perturbation to mimic real-time feedback drift.
            s2 = np.clip(s + rng.normal(0.0, 0.02, size=s.shape), 0.0, 1.0)
            self.rl_agent.update(s, a, shaped_reward, s2)
            rewards.append(shaped_reward)

        return {"episodes": int(episodes), "avg_reward": float(np.mean(rewards)), "min": float(np.min(rewards)), "max": float(np.max(rewards))}

    def save_dynamic(self, filename: str = "dynamic_rl.pkl") -> str:
        """Save RL agent Q-table to disk."""
        if self.rl_agent is None:
            raise AlgorithmSelectionError("动态策略未初始化，无法保存。请先调用 init_dynamic()/train_dynamic().")
        path = os.path.join(self.model_dir, filename)
        try:
            with open(path, "wb") as f:
                pickle.dump({"agent": self.rl_agent}, f)
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError(f"保存动态模型失败: {e}") from e
        return path

    def load_dynamic(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Load RL agent from disk."""
        p = path or os.path.join(self.model_dir, "dynamic_rl.pkl")
        try:
            with open(p, "rb") as f:
                payload = pickle.load(f)
        except FileNotFoundError as e:
            raise AlgorithmSelectionError(f"动态模型文件不存在: {p!r}。请先训练并保存，或传入正确路径。") from e
        except Exception as e:  # noqa: BLE001
            raise AlgorithmSelectionError(f"加载动态模型失败: {e}") from e
        agent = payload.get("agent")
        if agent is None:
            raise AlgorithmSelectionError("动态模型文件内容不完整。请重新训练/保存。")
        self.rl_agent = agent
        return {"strategy": "dynamic_rl", "path": p, "actions": getattr(self.rl_agent, "actions", None)}

    def act_dynamic(self, physics: np.ndarray, hardware: np.ndarray, domain: np.ndarray) -> str:
        """Select an action using the RL policy (no exploration)."""
        if self.rl_agent is None:
            raise AlgorithmSelectionError("动态策略未加载/未训练。请先调用 train_dynamic() 或 load_dynamic().")
        s = concat_features(physics, hardware, domain)
        return self.rl_agent.act(s, explore=False)

    # ---------- Unified selection API (M) ----------

    def select(
        self,
        physics: np.ndarray,
        hardware: np.ndarray,
        domain: np.ndarray,
        strategy: StrategyName = "static_rf",
    ) -> Dict[str, Any]:
        """Select best algorithm and return scores + rationale.

        Output:
            {
              "algorithm_key": "...",
              "algorithm_name": "...",
              "score": {accuracy, convergence, resource, total},
              "reason": "...",
              "strategy": "...",
              "static_probs": {...} (optional)
            }
        """
        if strategy in ("static_rf", "static_xgb", "mlp_nn", "gnn_selector"):
            self._load_or_train_static(strategy)
            alg_key, probs = self.predict_static(physics, hardware, domain)
            static_probs = probs
        elif strategy == "dynamic_rl":
            if self.rl_agent is None:
                try:
                    self.load_dynamic()
                except AlgorithmSelectionError:
                    self.train_dynamic()
            alg_key = self.act_dynamic(physics, hardware, domain)
            static_probs = None
        else:
            raise AlgorithmSelectionError(f"未知策略: {strategy!r}")

        # Evaluate chosen algorithm + provide ranking for transparency
        chosen_score, reason = evaluate_algorithm(alg_key, physics, hardware, domain)
        ranking = []
        for k in ("fdm", "fem", "spectral"):
            s, _ = evaluate_algorithm(k, physics, hardware, domain)
            ranking.append({"key": k, "name": ALGORITHM_CANDIDATES_BY_KEY[k].name, "total": s.total})
        ranking.sort(key=lambda r: r["total"], reverse=True)

        result = {
            "strategy": strategy,
            "algorithm_key": alg_key,
            "algorithm_name": ALGORITHM_CANDIDATES_BY_KEY[alg_key].name,
            "score": {
                "accuracy": chosen_score.accuracy_score,
                "convergence": chosen_score.convergence_score,
                "resource": chosen_score.resource_score,
                "total": chosen_score.total,
            },
            "reason": reason,
            "ranking": ranking,
            **({"static_probs": static_probs} if static_probs is not None else {}),
        }
        result["selected_algorithm"] = alg_key
        result["algorithm_scores"] = result["score"]
        result["rationale"] = reason
        return result

