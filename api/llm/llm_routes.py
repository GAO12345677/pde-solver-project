from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from api.llm.llm_config_manager import LLMConfigManager
from api.llm.llm_factory import LLMFactory

router = APIRouter()

# 定义请求体模型
class LLMConfigSaveRequest(BaseModel):
    model_name: str
    api_key: str
    base_url: Optional[str] = None

class LLMConfigTestRequest(BaseModel):
    model_name: str
    api_key: str
    base_url: Optional[str] = None

# 统一响应格式
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "Success"
    data: Optional[Any] = None

@router.post("/config/save", response_model=ApiResponse, summary="保存 LLM 模型配置")
async def save_llm_config(request: LLMConfigSaveRequest):
    """
    保存单个 LLM 模型的配置信息（API Key, Base URL）。
    """
    try:
        LLMConfigManager.save_config(
            model_name=request.model_name,
            api_key=request.api_key,
            base_url=request.base_url
        )
        # 重新加载配置以确保最新配置生效
        LLMConfigManager.load_config()
        return ApiResponse(message=f"模型 {request.model_name} 配置保存成功。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")

@router.get("/config/get", response_model=ApiResponse, summary="获取 LLM 模型配置")
async def get_llm_config(model_name: Optional[str] = None):
    """
    获取单个或所有 LLM 模型的配置信息。
    API Key 会进行脱敏处理。
    """
    try:
        if model_name:
            config = LLMConfigManager.get_model_config(model_name)
            if not config:
                raise HTTPException(status_code=404, detail=f"未找到模型 {model_name} 的配置。")
            
            # 对 API Key 进行脱敏
            display_config = config.copy()
            if "api_key" in display_config and display_config["api_key"]:
                display_config["api_key"] = LLMConfigManager._mask_api_key(display_config["api_key"])
            return ApiResponse(data=display_config, message=f"已获取模型 {model_name} 的配置。")
        else:
            all_configs = LLMConfigManager.get_all_configs()
            return ApiResponse(data=all_configs, message="已获取所有模型的配置。")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")

@router.post("/config/test", response_model=ApiResponse, summary="测试 LLM 模型配置")
async def test_llm_config(request: LLMConfigTestRequest):
    """
    测试 LLM 模型的 API Key 和 Base URL 是否有效。
    """
    try:
        # 获取最新的配置，包括可能来自环境变量的配置
        config = LLMConfigManager.get_model_config(request.model_name)
        api_key = request.api_key if request.api_key else config.get("api_key")
        base_url = request.base_url if request.base_url else config.get("base_url")

        if not api_key:
            raise HTTPException(status_code=400, detail="API Key 未提供。")

        # 尝试创建 LLM 实例并测试连接
        llm_instance = LLMFactory.create_llm(
            model_name=request.model_name,
            api_key=api_key,
            base_url=base_url
        )
        test_result = await llm_instance.test_connection()

        if test_result.get("success"):
            return ApiResponse(message=f"模型 {request.model_name} 配置测试成功。", data=test_result)
        else:
            return ApiResponse(code=400, message=f"模型 {request.model_name} 配置测试失败: {test_result.get('message', '未知错误')}", data=test_result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"模型错误: {e}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试配置时发生未知错误: {e}")

@router.get("/quota/get", response_model=ApiResponse, summary="获取所有 LLM 模型的额度信息")
async def get_llm_quota():
    """
    获取所有已配置 LLM 模型的额度信息。
    """
    quot_info_list = []  # 修复：把 quot-info-list 改成 quot_info_list
    registered_models = LLMFactory.get_registered_models()

    for model_name in registered_models:
        try:
            # 获取最新的配置，包括可能来自环境变量的配置
            config = LLMConfigManager.get_model_config(model_name)
            if not config or not config.get("api_key"):
                quot_info_list.append({
                    "model_name": model_name,
                    "provider": model_name, # Fallback to model_name if provider not available
                    "remaining_quota": 0,
                    "total_quota": 0,
                    "update_time": datetime.now().isoformat(),
                    "status": "unconfigured",
                    "message": "API Key 未配置或不完整"
                })
                continue

            api_key = config.get("api_key")
            base_url = config.get("base_url")

            llm_instance = LLMFactory.create_llm(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url
            )
            quota_data = await llm_instance.get_quota()
            quot_info_list.append(quota_data)

        except Exception as e:
            # 捕获单个模型获取额度时的异常，不影响其他模型
            quot_info_list.append({
                "model_name": model_name,
                "provider": model_name,
                "remaining_quota": 0,
                "total_quota": 0,
                "update_time": datetime.now().isoformat(),
                "status": "error",
                "message": f"获取额度失败: {e}"
            })
            continue # 继续处理下一个模型

    return ApiResponse(data=quot_info_list, message="已获取所有模型的额度信息。")

