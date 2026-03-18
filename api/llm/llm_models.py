import httpx
from typing import Dict, Any, Optional
from api.llm.llm_base import BaseLLM
from api.llm.llm_factory import LLMFactory
import openai
import os
from datetime import datetime

import google.generativeai as genai

class OpenAI(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return {"text": response.choices[0].message.content, "usage": response.usage.model_dump()}
        except openai.APIStatusError as e:
            return {"error": f"OpenAI API error: {e.status_code} - {e.response}", "status_code": e.status_code}
        except openai.APIConnectionError as e:
            return {"error": f"OpenAI API connection error: {e.message}", "status_code": 500}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        # OpenAI 没有直接的额度查询 API，这里我们返回一个模拟的额度信息。
        # 实际项目中，可能需要通过用户自己的账单系统或使用量数据来获取。
        return {
            "model_name": self.model_name,
            "provider": "OpenAI",
            "remaining_quota": "N/A",  # 实际额度需要通过其他方式获取
            "total_quota": "N/A",
            "update_time": datetime.now().isoformat(),
            "status": "normal"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            # 尝试列出模型，如果成功则认为连接有效
            await self.client.models.list()
            return {"success": True, "message": "OpenAI API 连接成功。"}
        except openai.AuthenticationError:
            return {"success": False, "message": "OpenAI API Key 无效。"}
        except openai.APIStatusError as e:
            return {"success": False, "message": f"OpenAI API 错误: {e.status_code} - {e.response}"}
        except openai.APIConnectionError as e:
            return {"success": False, "message": f"OpenAI API 连接错误: {e.message}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册 OpenAI 模型
LLMFactory.register_llm("openai", OpenAI)


class GoogleGemini(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        genai.configure(api_key=self.api_key)
        # Note: base_url is not directly used by genai.configure,
        # but could be used if we were to directly use httpx or requests
        # with a custom endpoint. For now, we rely on the default endpoint.
        # model_name for Gemini is typically "gemini-pro" or "gemini-ultra"

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(prompt, **kwargs)
            # Assuming 'text' is the primary output. Gemini response object might be more complex.
            return {"text": response.text, "usage": {}} # Gemini Python SDK doesn't directly expose usage in a simple way for generate_content
        except Exception as e:
            return {"error": f"Google Gemini API error: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        # Google Gemini 也没有直接的额度查询 API，返回模拟信息
        return {
            "model_name": self.model_name,
            "provider": "Google Gemini",
            "remaining_quota": "N/A",
            "total_quota": "N/A",
            "update_time": datetime.now().isoformat(),
            "status": "normal"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            # 尝试生成一个短内容来测试连接
            model = genai.GenerativeModel(self.model_name)
            await model.generate_content_async("hello", stream=False)
            return {"success": True, "message": "Google Gemini API 连接成功。"}
        except genai.APIError as e:
            return {"success": False, "message": f"Google Gemini API 错误: {e.args[0]}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册 Google Gemini 模型
LLMFactory.register_llm("gemini", GoogleGemini)
LLMFactory.register_llm("gemini-pro", GoogleGemini)

from dashscope import Generation
from http import HTTPStatus

class Qwen(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            messages = [{'role': 'user', 'content': prompt}]
            response = Generation.call(
                model=self.model_name,
                messages=messages,
                api_key=self.api_key,
                result_format='message',
                **kwargs
            )
            if response.status_code == HTTPStatus.OK:
                return {"text": response.output.choices[0].message.content, "usage": response.usage}
            else:
                return {"error": f"Qwen API error: {response.code} - {response.message}", "status_code": response.status_code}
        except Exception as e:
            return {"error": f"An unexpected error occurred with Qwen API: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": "通义千问 (Qwen)",
            "remaining_quota": "N/A",
            "total_quota": "N/A",
            "update_time": datetime.now().isoformat(),
            "status": "normal"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            messages = [{'role': 'user', 'content': 'hello'}]
            response = Generation.call(
                model=self.model_name,
                messages=messages,
                api_key=self.api_key,
                result_format='message',
                stream=False,
                max_tokens=1
            )
            if response.status_code == HTTPStatus.OK:
                return {"success": True, "message": "通义千问 API 连接成功。"}
            else:
                return {"success": False, "message": f"通义千问 API 连接失败: {response.code} - {response.message}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册通义千问模型
LLMFactory.register_llm("qwen", Qwen)
LLMFactory.register_llm("qwen-turbo", Qwen)
LLMFactory.register_llm("qwen-plus", Qwen)

class DeepSeek(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        if not self.base_url:
            self.base_url = "https://api.deepseek.com/v1" 
        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return {"text": response.choices[0].message.content, "usage": response.usage.model_dump()}
        except openai.APIStatusError as e:
            return {"error": f"DeepSeek API error: {e.status_code} - {e.response}", "status_code": e.status_code}
        except openai.APIConnectionError as e:
            return {"error": f"DeepSeek API connection error: {e.message}", "status_code": 500}
        except Exception as e:
            return {"error": f"An unexpected error occurred with DeepSeek API: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": "DeepSeek",
            "remaining_quota": "N/A",
            "total_quota": "N/A",
            "update_time": datetime.now().isoformat(),
            "status": "normal"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            return {"success": True, "message": "DeepSeek API 连接成功。"}
        except openai.AuthenticationError:
            return {"success": False, "message": "DeepSeek API Key 无效。"}
        except openai.APIStatusError as e:
            return {"success": False, "message": f"DeepSeek API 错误: {e.status_code} - {e.response}"}
        except openai.APIConnectionError as e:
            return {"success": False, "message": f"DeepSeek API 连接错误: {e.message}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册 DeepSeek 模型
LLMFactory.register_llm("deepseek", DeepSeek)
LLMFactory.register_llm("deepseek-chat", DeepSeek)

class Doubao(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        if not self.base_url:
            self.base_url = "https://api.doubao.com/v1" 
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                **kwargs
            }
            response = await self.client.post("/chat/completions", headers=headers, json=payload, timeout=30)
            response.raise_for_status() 
            response_json = response.json()
            return {"text": response_json["choices"][0]["message"]["content"], "usage": response_json.get("usage", {})}
        except httpx.HTTPStatusError as e:
            return {"error": f"Doubao API error: {e.response.status_code} - {e.response.text}", "status_code": e.response.status_code}
        except httpx.RequestError as e:
            return {"error": f"Doubao API connection error: {e}", "status_code": 500}
        except Exception as e:
            return {"error": f"An unexpected error occurred with Doubao API: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        total_quota = 1000 
        remaining_quota = total_quota 
        
        return {
            "model_name": self.model_name,
            "provider": "豆包 (Doubao)",
            "remaining_quota": remaining_quota,
            "total_quota": total_quota,
            "update_time": datetime.now().isoformat(),
            "status": "normal" if remaining_quota > 0 else "exhausted"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "hello"}],
                "max_tokens": 1
            }
            response = await self.client.post("/chat/completions", headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return {"success": True, "message": "豆包 API 连接成功。"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"success": False, "message": "豆包 API Key 无效。"}
            return {"success": False, "message": f"豆包 API 错误: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"success": False, "message": f"豆包 API 连接错误: {e}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册豆包模型
LLMFactory.register_llm("doubao", Doubao)
LLMFactory.register_llm("doubao-pro", Doubao)

import qianfan

class BaiduQianfan(BaseLLM):
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        self.client = qianfan.Completion(ak=self.api_key, sk=os.environ.get("QIANFAN_SECRET_KEY")) 

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return {"text": response.body["result"], "usage": response.body.get("usage", {})}
        except qianfan.RequestError as e:
            return {"error": f"Baidu Qianfan API request error: {e.msg}", "status_code": e.error_code}
        except Exception as e:
            return {"error": f"An unexpected error occurred with Baidu Qianfan API: {e}", "status_code": 500}

    async def get_quota(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": "百度千帆 (Baidu Qianfan)",
            "remaining_quota": "N/A",
            "total_quota": "N/A",
            "update_time": datetime.now().isoformat(),
            "status": "normal"
        }

    async def test_connection(self) -> Dict[str, Any]:
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                temperature=0.1, 
                top_p=0.1
            )
            if response.body and response.body.get("result"):
                return {"success": True, "message": "百度千帆 API 连接成功。"}
            else:
                return {"success": False, "message": f"百度千帆 API 连接失败: {response.body.get('error_msg', '未知错误')}"}
        except qianfan.RequestError as e:
            return {"success": False, "message": f"百度千帆 API 错误: {e.msg}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试发生未知错误: {e}"}

# 注册百度千帆模型
LLMFactory.register_llm("qianfan", BaiduQianfan)
LLMFactory.register_llm("ERNIE-Bot", BaiduQianfan)
LLMFactory.register_llm("ERNIE-Bot-4", BaiduQianfan)




