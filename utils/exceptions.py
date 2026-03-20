"""统一异常处理模块

定义应用级别的异常类型和错误响应格式
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppError(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        details: Optional[Any] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AppError):
    """参数验证错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FeatureExtractionError(AppError):
    """特征提取错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="FEATURE_EXTRACTION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AlgorithmSelectionError(AppError):
    """算法选择错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="ALGORITHM_SELECTION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SolverError(AppError):
    """求解器错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="SOLVER_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LLMConfigError(AppError):
    """LLM配置错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="LLM_CONFIG_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LLMConnectionError(AppError):
    """LLM连接错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="LLM_CONNECTION_ERROR",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ResourceNotFoundError(AppError):
    """资源未找到错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConfigurationError(AppError):
    """配置错误"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_error_response(
    message: str,
    code: str = "ERROR",
    details: Optional[Any] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> Dict[str, Any]:
    """创建标准错误响应"""
    return {
        "status": "error",
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "data": None
    }


def create_success_response(data: Any) -> Dict[str, Any]:
    """创建标准成功响应"""
    return {
        "status": "ok",
        "success": True,
        "error": None,
        "data": data
    }
