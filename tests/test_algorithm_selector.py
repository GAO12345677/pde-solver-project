"""算法选择器测试"""
import pytest
import numpy as np
from algorithm.selector import (
    AlgorithmSelector,
    AlgorithmSelectionError,
    concat_features,
    evaluate_algorithm,
)


class TestConcatFeatures:
    """特征拼接测试"""
    
    def test_concat_features_valid(self):
        """测试有效特征拼接"""
        physics = np.array([0.0, 0.0, 1.0, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        result = concat_features(physics, hardware, domain)
        
        assert result.shape == (13,)
        assert np.allclose(result[:5], physics)
        assert np.allclose(result[5:10], hardware)
        assert np.allclose(result[10:], domain)
    
    def test_concat_features_invalid_dimension(self):
        """测试无效维度"""
        physics = np.array([0.0, 0.0, 1.0])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        with pytest.raises(AlgorithmSelectionError):
            concat_features(physics, hardware, domain)
    
    def test_concat_features_nan(self):
        """测试包含NaN的特征"""
        physics = np.array([0.0, 0.0, np.nan, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        with pytest.raises(AlgorithmSelectionError):
            concat_features(physics, hardware, domain)


class TestEvaluateAlgorithm:
    """算法评估测试"""
    
    def test_evaluate_algorithm_fdm(self):
        """测试FDM算法评估"""
        physics = np.array([0.0, 0.0, 1.0, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        score, reason = evaluate_algorithm("fdm", physics, hardware, domain)
        
        assert 0 <= score.accuracy_score <= 1
        assert 0 <= score.convergence_score <= 1
        assert 0 <= score.resource_score <= 1
        assert 0 <= score.total <= 1
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_evaluate_algorithm_fem(self):
        """测试FEM算法评估"""
        physics = np.array([1.0, 1.0, 0.7, 0.6, 0.9])
        hardware = np.array([0.7, 0.8, 0.7, 0.6, 1.0])
        domain = np.array([0.5, 0.5, 0.7])
        
        score, reason = evaluate_algorithm("fem", physics, hardware, domain)
        
        assert 0 <= score.accuracy_score <= 1
        assert 0 <= score.convergence_score <= 1
        assert 0 <= score.resource_score <= 1
        assert 0 <= score.total <= 1
    
    def test_evaluate_algorithm_spectral(self):
        """测试Spectral算法评估"""
        physics = np.array([0.5, 0.0, 0.0, 0.2, 0.4])
        hardware = np.array([0.7, 0.5, 0.5, 0.5, 1.0])
        domain = np.array([1.0, 0.2, 0.8])
        
        score, reason = evaluate_algorithm("spectral", physics, hardware, domain)
        
        assert 0 <= score.accuracy_score <= 1
        assert 0 <= score.convergence_score <= 1
        assert 0 <= score.resource_score <= 1
        assert 0 <= score.total <= 1
    
    def test_evaluate_algorithm_invalid(self):
        """测试无效算法"""
        physics = np.array([0.0, 0.0, 1.0, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        with pytest.raises(AlgorithmSelectionError):
            evaluate_algorithm("invalid", physics, hardware, domain)


class TestAlgorithmSelector:
    """算法选择器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        selector = AlgorithmSelector(model_dir="model")
        
        assert selector is not None
        assert selector.model_dir == "model"
    
    def test_train_static_rf(self):
        """测试训练静态RandomForest模型"""
        selector = AlgorithmSelector(model_dir="model")
        result = selector.train_static(strategy="static_rf")
        
        assert "strategy" in result
        assert result["strategy"] == "static_rf"
        assert "num_samples" in result
        assert result["num_samples"] > 0
        assert selector.static_model is not None
    
    def test_predict_static(self):
        """测试静态预测"""
        selector = AlgorithmSelector(model_dir="model")
        selector.train_static(strategy="static_rf")
        
        physics = np.array([0.0, 0.0, 1.0, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        algorithm, probs = selector.predict_static(physics, hardware, domain)
        
        assert algorithm in ["fdm", "fem", "spectral"]
        assert len(probs) == 3
        assert all(0 <= p <= 1 for p in probs.values())
        assert abs(sum(probs.values()) - 1.0) < 1e-6
    
    def test_select_without_training(self):
        """测试未训练的选择"""
        selector = AlgorithmSelector(model_dir="model")
        
        physics = np.array([0.0, 0.0, 1.0, 0.0, 0.5])
        hardware = np.array([0.0, 0.5, 0.5, 0.0, 1.0])
        domain = np.array([0.5, 0.5, 0.75])
        
        result = selector.select(physics, hardware, domain, strategy="static_rf")
        
        assert "selected_algorithm" in result
        assert "algorithm_scores" in result
        assert "rationale" in result
    
    def test_train_dynamic_rl(self):
        """测试训练动态RL模型"""
        selector = AlgorithmSelector(model_dir="model")
        result = selector.train_dynamic(episodes=10)
        
        assert "episodes" in result
        assert result["episodes"] == 10
        assert "avg_reward" in result
        assert selector.rl_agent is not None
