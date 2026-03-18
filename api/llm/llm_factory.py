from typing import Dict, Type
from api.llm.llm_base import BaseLLM

class LLMFactory:
    """
    LLM 工厂类，用于注册和创建不同类型的 LLM 实例。
    """
    _llm_registry: Dict[str, Type[BaseLLM]] = {}

    @classmethod
    def register_llm(cls, model_name: str, llm_class: Type[BaseLLM]):
        """
        注册一个 LLM 模型。

        Args:
            model_name: 模型的名称，例如 "openai", "qwen"。
            llm_class: 实现了 BaseLLM 抽象类的具体 LLM 类。
        """
        if not issubclass(llm_class, BaseLLM):
            raise ValueError(f"Class {llm_class.__name__} must inherit from BaseLLM")
        cls._llm_registry[model_name] = llm_class

    @classmethod
    def create_llm(cls, model_name: str, api_key: str, base_url: str = None) -> BaseLLM:
        """
        创建指定名称的 LLM 实例。

        Args:
            model_name: 要创建的模型的名称。
            api_key: 模型的 API Key。
            base_url: 模型的 Base URL (可选)。

        Returns:
            一个 BaseLLM 的实例。

        Raises:
            ValueError: 如果模型名称未注册。
        """
        llm_class = cls._llm_registry.get(model_name)
        if not llm_class:
            raise ValueError(f"LLM model '{model_name}' not registered.")
        return llm_class(model_name=model_name, api_key=api_key, base_url=base_url)

    @classmethod
    def get_registered_models(cls) -> list[str]:
        """
        获取所有已注册的模型名称列表。
        """
        return list(cls._llm_registry.keys())
