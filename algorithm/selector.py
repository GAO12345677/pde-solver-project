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
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from config.constants import ALGORITHM_CANDIDATES_BY_KEY, RequirementLevel


class AlgorithmSelectionError(ValueError):
    """Raised when selection, evaluation, or model I/O fails."""


StrategyName = Literal["static_rf", "static_xgb", "dynamic_rl"]


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
        """Train a static selector (RF or XGB) using typical-case proxy dataset."""
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
        else:
            raise AlgorithmSelectionError(f"未知静态策略: {strategy!r}，请使用 static_rf/static_xgb。")

        model.fit(X, y)
        self.static_model = self._force_single_thread_static_model(model)
        self.static_label_keys = label_keys
        self.static_strategy = strategy
        return {"strategy": strategy, "num_samples": int(X.shape[0]), "labels": label_keys}

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
        if self.static_model is None or not self.static_label_keys:
            raise AlgorithmSelectionError("静态模型文件内容不完整。请重新训练/保存。")
        return {"strategy": self.static_strategy, "labels": self.static_label_keys, "path": p}

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
        if strategy in ("static_rf", "static_xgb"):
            if self.static_model is None or not self.static_label_keys:
                try:
                    self.load_static()
                except AlgorithmSelectionError:
                    self.train_static(strategy=strategy)
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

