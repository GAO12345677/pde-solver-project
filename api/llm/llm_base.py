import abc
from typing import Dict, Any, Optional

class BaseLLM(abc.ABC):
    """
    抽象基类，定义了所有大型语言模型应实现的核心接口。
    """

    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    @abc.abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        根据给定的 prompt 生成文本。
        子类需要实现此方法以与特定的 LLM API 进行交互。

        Args:
            prompt: 输入的文本 prompt。
            **kwargs: 其他模型生成参数。

        Returns:
            包含生成结果的字典。
        """
        pass

    @abc.abstractmethod
    async def get_quota(self) -> Dict[str, Any]:
        """
        获取当前模型的额度信息。
        子类需要实现此方法以从特定的 LLM API 获取额度。

        Returns:
            包含额度信息的字典，例如：
            {
                "model_name": "openai",
                "provider": "OpenAI",
                "remaining_quota": 8500,
                "total_quota": 10000,
                "update_time": "2026-03-18 10:00:00",
                "status": "normal" // normal/insufficient/exhausted
            }
        """
        pass

    @abc.abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试与模型 API 的连接和认证是否有效。

        Returns:
            包含测试结果的字典，例如：
            {"success": True, "message": "连接成功"}
            {"success": False, "message": "连接失败: API Key 无效"}
        """
        pass
