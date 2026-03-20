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

class BaseParser(abc.ABC):
    """
    抽象基类，定义了所有 PDE 问题解析器应实现的核心接口。
    """
    @abc.abstractmethod
    async def parse(self, question: str) -> Dict[str, Any]:
        """
        将自然语言的 PDE 问题描述解析为结构化 JSON。

        Args:
            question: 自然语言的 PDE 问题描述。

        Returns:
            包含解析结果的字典。
        """
        pass
