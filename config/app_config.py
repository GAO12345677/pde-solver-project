"""统一配置管理模块

支持环境变量、配置文件、运行时配置的多层级配置管理
"""
import os
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    http_proxy: str = "http://127.0.0.1:7890"
    https_proxy: str = "http://127.0.0.1:7890"
    verify_ssl: bool = False


@dataclass
class LLMConfig:
    """LLM配置"""
    openai: Dict[str, str] = field(default_factory=dict)
    qwen: Dict[str, str] = field(default_factory=dict)
    deepseek: Dict[str, str] = field(default_factory=dict)
    doubao: Dict[str, str] = field(default_factory=dict)
    gemini: Dict[str, str] = field(default_factory=dict)
    qianfan: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "127.0.0.1"
    port: int = 8001
    reload: bool = False
    debug: bool = False


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class AppConfig:
    """应用总配置"""
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_file(cls, config_path: str = "config/app_config.json") -> "AppConfig":
        """从配置文件加载"""
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 手动构造嵌套对象
            proxy_data = data.get("proxy", {})
            proxy = ProxyConfig(**proxy_data)
            
            llm_data = data.get("llm", {})
            llm = LLMConfig(**llm_data)
            
            server_data = data.get("server", {})
            server = ServerConfig(**server_data)
            
            logging_data = data.get("logging", {})
            logging = LoggingConfig(**logging_data)
            
            return cls(proxy=proxy, llm=llm, server=server, logging=logging)
        except Exception as e:
            print(f"配置文件加载失败，使用默认配置: {e}")
            return cls()
    
    def to_file(self, config_path: str = "config/app_config.json") -> None:
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
    
    def update_from_env(self) -> None:
        """从环境变量更新配置"""
        # 代理配置
        if os.getenv("PROXY_ENABLED"):
            self.proxy.enabled = os.getenv("PROXY_ENABLED").lower() in ("1", "true", "yes")
        if os.getenv("HTTP_PROXY"):
            self.proxy.http_proxy = os.getenv("HTTP_PROXY")
        if os.getenv("HTTPS_PROXY"):
            self.proxy.https_proxy = os.getenv("HTTPS_PROXY")
        
        # 服务器配置
        if os.getenv("SERVER_HOST"):
            self.server.host = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            self.server.port = int(os.getenv("SERVER_PORT"))
        if os.getenv("DEBUG"):
            self.server.debug = os.getenv("DEBUG").lower() in ("1", "true", "yes")
        
        # 日志配置
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        
        # LLM配置
        if os.getenv("BAIDU_QIANFAN_API_KEY"):
            self.llm.qianfan["api_key"] = os.getenv("BAIDU_QIANFAN_API_KEY")
        if os.getenv("BAIDU_QIANFAN_SECRET_KEY"):
            self.llm.qianfan["secret_key"] = os.getenv("BAIDU_QIANFAN_SECRET_KEY")


# 全局配置实例
_global_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = AppConfig.from_file()
        _global_config.update_from_env()
    return _global_config


def reset_config() -> None:
    """重置全局配置"""
    global _global_config
    _global_config = None
