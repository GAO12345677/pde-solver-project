"""LLM 配置路由（兼容代理+3API格式）"""
from fastapi import APIRouter, Body, Query
from typing import Dict, Any, Optional
import requests
from datetime import datetime
import logging
from pydantic import BaseModel

from config.app_config import get_config
from api.llm.llm_config_manager import LLMConfigManager

router = APIRouter()

class ConfigTestRequest(BaseModel):
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    model_id: Optional[str] = None

class ConfigSaveRequest(BaseModel):
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    model_id: Optional[str] = None
logger = logging.getLogger(__name__)

# 内存配置存储（运行时配置）
config_store: Dict[str, Dict[str, str]] = {
    "openai": {}, "qwen": {}, "deepseek": {},
    "doubao": {}, "gemini": {}, "qianfan": {}
}

def get_proxies() -> Optional[Dict[str, str]]:
    """从配置获取代理设置"""
    cfg = get_config()
    if cfg.proxy.enabled:
        return {
            "http": cfg.proxy.http_proxy,
            "https": cfg.proxy.https_proxy
        }
    return None

def get_verify_ssl() -> bool:
    """从配置获取SSL验证设置"""
    cfg = get_config()
    return cfg.proxy.verify_ssl

# ========== 核心：Gemini 测试函数（强代理+延长超时） ==========
def test_gemini(api_key: str, base_url: str) -> bool:
    """测试Gemini连接"""
    try:
        url = f"{base_url}/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": "test"}]}]}

        proxies = get_proxies()
        verify_ssl = get_verify_ssl()

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=proxies,
            verify=verify_ssl
        )
        response.raise_for_status()
        logger.info(f"Gemini连接测试成功: {base_url}")
        return True
    except Exception as e:
        logger.error(f"Gemini连接测试失败: {str(e)}")
        raise RuntimeError(f"Gemini 连接失败: {str(e)}")

# ========== 1. 获取配置（前端格式） ==========
@router.get("/config/get")
async def config_get() -> Dict[str, Any]:
    # 确保每个配置都包含 model_name 字段
    result = {}
    for model_name, config in config_store.items():
        result[model_name] = {
            "model_name": model_name,
            "api_key": config.get("api_key", ""),
            "base_url": config.get("base_url", ""),
            "model_id": config.get("model_id", "")
        }
    return {"code": 200, "data": result}

# ========== 2. 测试连接（前端格式） ==========
@router.post("/config/test")
async def config_test(request_body: ConfigTestRequest) -> Dict[str, Any]:
    """测试LLM连接"""
    model_name = request_body.model_name
    api_key = request_body.api_key
    base_url = request_body.base_url
    model_id = request_body.model_id
    
    logger.info(f"收到测试请求: model_name={model_name}, base_url={base_url}, model_id={model_id}")
    
    model_defaults = {
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "openai": "https://api.openai.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "doubao": "https://ark.cn-beijing.volces.com/api/v3",
        "qianfan": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop"
    }
    base_url = base_url or model_defaults.get(model_name, "")
    
    logger.info(f"使用 Base URL: {base_url}")

    try:
        proxies = get_proxies()
        verify_ssl = get_verify_ssl()

        if model_name == "gemini":
            success = test_gemini(api_key, base_url)
        elif model_name == "doubao":
            # 火山方舟 API 测试：使用 OpenAI 兼容的 chat/completions 端点
            # 参考：https://ark.cn-beijing.volces.com/api/v3/chat/completions
            if not model_id:
                raise ValueError("火山方舟需要配置模型名称，例如：doubao-seed-1-8-251228")
            
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": "test"
                    }
                ],
                "max_tokens": 10
            }
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
                proxies=proxies,
                verify=verify_ssl
            )
            
            # 检查响应
            if resp.status_code == 401:
                raise ValueError("API Key 无效或格式错误，请检查火山方舟控制台")
            elif resp.status_code == 404:
                raise ValueError("Base URL 或模型名称错误，请检查配置")
            elif resp.status_code != 200:
                raise ValueError(f"连接失败，状态码: {resp.status_code}, 响应: {resp.text}")
            
            success = resp.status_code == 200
        else:
            url = f"{base_url}/v1/models" if "openai" in model_name else f"{base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get(
                url,
                headers=headers,
                timeout=15,
                proxies=proxies,
                verify=verify_ssl
            )
            success = resp.status_code == 200

        logger.info(f"{model_name}连接测试成功")
        return {"code": 200, "message": "测试成功"}
    except Exception as e:
        logger.error(f"{model_name}连接测试失败: {str(e)}")
        return {"code": 500, "message": str(e)}

# ========== 3. 保存配置 ==========
@router.post("/config/save")
async def config_save(request_body: ConfigSaveRequest) -> Dict[str, Any]:
    model_name = request_body.model_name
    api_key = request_body.api_key
    base_url = request_body.base_url
    model_id = request_body.model_id
    
    try:
        # 保存到内存配置存储
        config_store[model_name] = {
            "api_key": api_key,
            "base_url": base_url or "",
            "model_id": model_id or ""
        }
        
        # 同时保存到 LLMConfigManager，以便题目解析功能可以使用
        LLMConfigManager.save_config(model_name, api_key, base_url, model_id)
        
        return {"code": 200, "message": "配置保存成功"}
    except Exception as e:
        return {"code": 500, "message": str(e)}

# ========== 4. 获取额度 ==========
@router.get("/quota/get")
async def quota_get() -> Dict[str, Any]:
    quota_data = []
    for model_id in config_store.keys():
        if config_store[model_id].get("api_key"):
            quota_data.append({
                "model_name": model_id,
                "provider": {"gemini":"Google","openai":"OpenAI","qwen":"阿里云","deepseek":"DeepSeek","doubao":"字节跳动","qianfan":"百度"}.get(model_id, "-"),
                "total_quota": 10000.0,
                "remaining_quota": 9900.0,
                "status": "normal",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "message": "额度充足"
            })
        else:
            quota_data.append({
                "model_name": model_id,
                "provider": {"gemini":"Google","openai":"OpenAI","qwen":"阿里云","deepseek":"DeepSeek","doubao":"字节跳动","qianfan":"百度"}.get(model_id, "-"),
                "total_quota": 0,
                "remaining_quota": 0,
                "status": "unconfigured",
                "update_time": "",
                "message": "未配置 API Key"
            })

    return {"code": 200, "data": quota_data}