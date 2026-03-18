import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

CONFIG_FILE_PATH = Path("d:/cursorku/config/llm_config.json")

class LLMConfigManager:
    _config: Dict[str, Any] = {}

    @classmethod
    def load_config(cls):
        """
        从配置文件或环境变量加载 LLM 配置。
        优先读取环境变量。
        """
        if CONFIG_FILE_PATH.exists():
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                cls._config = json.load(f)
        else:
            cls._config = {}

        # 遍历已注册的模型，从环境变量覆盖配置
        # 这里需要LLMFactory，但为了避免循环引用，我们只处理已注册模型的key
        # 实际使用时，可以先加载配置，再注册模型，或者在模型注册时动态更新配置
        # 为了简化，这里假设我们知道模型名称
        # 更好的做法是在这里导入 LLMFactory.get_registered_models()
        # 但是为了避免循环依赖，我将手动列出预期的模型键
        known_model_names = ["openai", "gemini", "gemini-pro", "qwen", "qwen-turbo", "qwen-plus", "deepseek", "deepseek-chat", "doubao", "doubao-pro", "qianfan", "ERNIE-Bot", "ERNIE-Bot-4"]

        for model_name in known_model_names:
            env_api_key = os.getenv(f"{model_name.upper()}_API_KEY")
            env_base_url = os.getenv(f"{model_name.upper()}_BASE_URL")

            if model_name not in cls._config:
                cls._config[model_name] = {}

            if env_api_key:
                cls._config[model_name]["api_key"] = env_api_key
            if env_base_url:
                cls._config[model_name]["base_url"] = env_base_url

    @classmethod
    def save_config(cls, model_name: str, api_key: str, base_url: Optional[str] = None):
        """
        保存单个 LLM 模型的配置到文件。
        """
        if model_name not in cls._config:
            cls._config[model_name] = {}
        
        # 检查是否与环境变量冲突，如果环境变量已设置，则不覆盖
        env_api_key = os.getenv(f"{model_name.upper()}_API_KEY")
        env_base_url = os.getenv(f"{model_name.upper()}_BASE_URL")

        if not env_api_key: # 如果环境变量没有设置，才允许从接口保存
            cls._config[model_name]["api_key"] = api_key
        
        if not env_base_url: # 如果环境变量没有设置，才允许从接口保存
            cls._config[model_name]["base_url"] = base_url if base_url else ""

        # 确保目录存在
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cls._config, f, ensure_ascii=False, indent=4)

    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """
        获取指定模型的配置信息。
        """
        config = cls._config.get(model_name, {})
        
        # 优先从环境变量读取
        env_api_key = os.getenv(f"{model_name.upper()}_API_KEY")
        env_base_url = os.getenv(f"{model_name.upper()}_BASE_URL")

        if env_api_key:
            config["api_key"] = env_api_key
        if env_base_url:
            config["base_url"] = env_base_url

        return config

    @classmethod
    def get_all_configs(cls) -> Dict[str, Any]:
        """
        获取所有模型的配置信息（脱敏处理 API Key）。
        """
        all_configs = {}
        for model_name, model_config in cls._config.items():
            display_config = model_config.copy()
            
            # 优先从环境变量读取
            env_api_key = os.getenv(f"{model_name.upper()}_API_KEY")
            env_base_url = os.getenv(f"{model_name.upper()}_BASE_URL")

            if env_api_key:
                display_config["api_key"] = env_api_key
            if env_base_url:
                display_config["base_url"] = env_base_url

            if "api_key" in display_config and display_config["api_key"]:
                display_config["api_key"] = cls._mask_api_key(display_config["api_key"])
            all_configs[model_name] = display_config
        return all_configs

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """
        对 API Key 进行脱敏处理。
        """
        if len(api_key) > 8:
            return f"{api_key[:4]}********{api_key[-4:]}"
        return "********"

# 初始化加载配置
LLMConfigManager.load_config()
