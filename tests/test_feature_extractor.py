"""特征提取器测试"""
import pytest
import numpy as np
from feature.extractor import (
    PhysicsFeatureExtractor,
    HardwareFeatureExtractor,
    DomainFeatureExtractor,
    FeatureExtractionError,
)
from config.constants import RequirementLevel


class TestPhysicsFeatureExtractor:
    """物理特征提取器测试"""
    
    def test_extract_from_params_heat1d(self):
        """测试1D热传导方程特征提取"""
        params = {
            "dimension": 1,
            "linearity": 0,
            "stationarity": 1,
            "boundary_condition": "dirichlet",
            "problem_size": 101,
        }
        
        result = PhysicsFeatureExtractor.extract_from_params(params)
        
        assert result is not None
        assert "vector" in result
        assert len(result["vector"]) == 5
        assert result["dimension"] == 1
    
    def test_extract_from_params_poisson2d(self):
        """测试2D Poisson方程特征提取"""
        params = {
            "dimension": 2,
            "linearity": 1,
            "stationarity": 0,
            "boundary_condition": "dirichlet",
            "problem_size": 1681,
        }
        
        result = PhysicsFeatureExtractor.extract_from_params(params)
        
        assert result is not None
        assert "vector" in result
        assert len(result["vector"]) == 5
        assert result["dimension"] == 2
    
    def test_normalize(self):
        """测试特征归一化"""
        params = {
            "dimension": 1,
            "linearity": 0,
            "stationarity": 1,
            "boundary_condition": "dirichlet",
            "problem_size": 101,
        }
        
        result = PhysicsFeatureExtractor.extract_from_params(params)
        normalized = PhysicsFeatureExtractor.normalize(result["vector"])
        
        assert len(normalized) == 5
        assert all(0 <= x <= 1 for x in normalized)
    
    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(FeatureExtractionError):
            PhysicsFeatureExtractor.extract_from_params({
                "dimension": 4,
                "linearity": 0,
                "stationarity": 1,
                "boundary_condition": "dirichlet",
                "problem_size": 101,
            })


class TestHardwareFeatureExtractor:
    """硬件特征提取器测试"""
    
    def test_extract(self):
        """测试硬件特征提取"""
        result = HardwareFeatureExtractor.extract()
        
        assert result is not None
        assert "vector" in result
        assert len(result["vector"]) == 5
        assert "gpu_name" in result
    
    def test_normalize(self):
        """测试硬件特征归一化"""
        result = HardwareFeatureExtractor.extract()
        normalized = HardwareFeatureExtractor.normalize(result["vector"])
        
        assert len(normalized) == 5
        assert all(0 <= x <= 1 for x in normalized)


class TestDomainFeatureExtractor:
    """领域特征提取器测试"""
    
    def test_extract_from_params(self):
        """测试领域需求特征提取"""
        params = {
            "accuracy": RequirementLevel.MEDIUM,
            "realtime": RequirementLevel.HIGH,
            "resource_budget": 0.75,
        }
        
        result = DomainFeatureExtractor.extract_from_params(params)
        
        assert result is not None
        assert "vector" in result
        assert len(result["vector"]) == 3
    
    def test_normalize(self):
        """测试领域特征归一化"""
        params = {
            "accuracy": RequirementLevel.MEDIUM,
            "realtime": RequirementLevel.HIGH,
            "resource_budget": 0.75,
        }
        
        result = DomainFeatureExtractor.extract_from_params(params)
        normalized = DomainFeatureExtractor.normalize(result["vector"])
        
        assert len(normalized) == 3
        assert all(0 <= x <= 1 for x in normalized)
