"""
Configuration Management

统一管理系统配置，支持多环境和动态配置。
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

# 加载环境变量（如果 dotenv 可用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """配置管理类 - 从现有的 src/config.py 迁移并增强"""

    def __init__(self):
        # 基础配置
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.cache_dir = self.project_root / ".cache"

        # Agent 配置
        self.default_agent = os.getenv("DEFAULT_AGENT", "rewrite")
        self.default_strategy = os.getenv("DEFAULT_STRATEGY", "line_by_line")

        # Provider 配置
        self.provider = os.getenv("LLM_PROVIDER", "openai")

        # OpenAI 配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_models = self._parse_models(
            os.getenv("OPENAI_MODELS", os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
        )

        # Ollama 配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_models = self._parse_models(
            os.getenv("OLLAMA_MODELS", os.getenv("OLLAMA_MODEL", "llama2"))
        )

        # Mimo 配置
        self.mimo_api_key = os.getenv("MIMO_API_KEY")
        self.mimo_base_url = os.getenv("MIMO_BASE_URL")
        self.mimo_models = self._parse_models(
            os.getenv("MIMO_MODEL_NAME", "")
        )

        # DeepSeek 配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL")
        self.deepseek_models = self._parse_models(
            os.getenv("DEEPSEEK_MODEL_NAME", "")
        )

        # Qwen 配置
        self.qwen_api_key = os.getenv("QWEN_API_KEY")
        self.qwen_base_url = os.getenv("QWEN_BASE_URL")
        self.qwen_models = self._parse_models(
            os.getenv("QWEN_MODEL_NAME", "")
        )

        # 处理配置
        self.default_timeout = int(os.getenv("DEFAULT_TIMEOUT", "120"))  # Increased to 120 seconds for slower models
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

        # 输出配置
        self.default_output_dir = os.getenv("DEFAULT_OUTPUT_DIR", "processed_docs")
        self.preserve_metadata = os.getenv("PRESERVE_METADATA", "true").lower() == "true"

        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE")

        # 缓存配置
        self.enable_cache = os.getenv("ENABLE_CACHE", "false").lower() == "true"
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 秒

        # 术语表配置
        self.default_glossary_path = os.getenv("DEFAULT_GLOSSARY_PATH", "")

        # 模型特定配置
        self.model_configs = self._load_model_configs()

        # 创建必要的目录
        self._ensure_directories()

    def _parse_models(self, models_str: str) -> list[str]:
        """
        解析模型字符串为列表

        支持两种格式：
        1. JSON数组: ["model1", "model2"]
        2. 逗号分隔: model1, model2
        """
        if not models_str:
            return []

        models_str = models_str.strip()

        # 尝试解析为JSON数组
        if models_str.startswith('[') and models_str.endswith(']'):
            try:
                import json
                models = json.loads(models_str)
                if isinstance(models, list):
                    return [str(model).strip() for model in models if model]
            except json.JSONDecodeError:
                pass  # 如果JSON解析失败，回退到逗号分隔解析

        # 使用逗号分隔解析
        models = [model.strip() for model in models_str.split(',')]
        return [model for model in models if model]

    def _load_model_configs(self) -> Dict[str, Dict[str, str]]:
        """加载模型特定配置"""
        model_configs = {}

        for model in self.openai_models:
            config = {}

            # 根据模型名确定配置前缀
            if model.startswith('mimo'):
                prefix = 'MIMO'
            elif model.startswith('glm'):
                prefix = 'GLM'
            elif model.startswith('qwen'):
                prefix = 'QWEN'
            else:
                prefix = 'OPENAI'  # 默认前缀

            # 获取模型特定的 API 密钥和基础 URL
            api_key = os.getenv(f"{prefix}_API_KEY") or self.openai_api_key
            base_url = os.getenv(f"{prefix}_BASE_URL") or self.openai_base_url

            config['api_key'] = api_key
            config['base_url'] = base_url
            config['prefix'] = prefix

            model_configs[model] = config

        return model_configs

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.cache_dir,
            self.project_root / self.default_output_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """获取 Provider 配置"""
        if provider_name == "openai":
            return {
                "provider_type": "openai",
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        elif provider_name == "ollama":
            return {
                "provider_type": "ollama",
                "base_url": self.ollama_base_url,
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        elif provider_name == "mimo":
            return {
                "provider_type": "mimo",
                "api_key": self.mimo_api_key,
                "base_url": self.mimo_base_url,
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        elif provider_name == "deepseek":
            return {
                "provider_type": "deepseek",
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        elif provider_name == "qwen":
            return {
                "provider_type": "qwen",
                "api_key": self.qwen_api_key,
                "base_url": self.qwen_base_url,
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        elif provider_name == "mock":
            return {
                "provider_type": "mock",
                "timeout_seconds": self.default_timeout,
                "max_retries": self.max_retries
            }
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """获取 Agent 配置"""
        return {
            "agent_type": agent_type,
            "provider_name": self.provider,
            "model_name": self.get_default_model(),
            "strategy_name": self.default_strategy,
            "timeout_seconds": self.default_timeout,
            "temperature": self.default_temperature,
            "max_retries": self.max_retries
        }

    def get_default_model(self) -> str:
        """获取默认模型"""
        if self.provider == "openai" and self.openai_models:
            return self.openai_models[0]
        elif self.provider == "ollama" and self.ollama_models:
            return self.ollama_models[0]
        else:
            return "mock-model"

    def get_model_config(self, model_name: str) -> Dict[str, str]:
        """获取模型特定配置"""
        return self.model_configs.get(model_name, {
            'api_key': self.openai_api_key,
            'base_url': self.openai_base_url,
            'prefix': 'OPENAI'
        })

    def update_config(self, updates: Dict[str, Any]) -> None:
        """动态更新配置"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        config = {
            "level": self.log_level,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }

        if self.log_file:
            config["filename"] = self.log_file

        return config

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.provider == "openai":
            return bool(self.openai_api_key)
        elif self.provider == "ollama":
            return True  # Ollama 是本地服务，总是可用
        elif self.provider == "mock":
            return True  # Mock provider 总是可用
        else:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "provider": self.provider,
            "default_agent": self.default_agent,
            "default_strategy": self.default_strategy,
            "openai_models": self.openai_models,
            "ollama_models": self.ollama_models,
            "default_timeout": self.default_timeout,
            "default_temperature": self.default_temperature,
            "max_retries": self.max_retries,
            "default_output_dir": self.default_output_dir,
            "preserve_metadata": self.preserve_metadata,
            "log_level": self.log_level,
            "enable_cache": self.enable_cache,
            "cache_ttl": self.cache_ttl
        }


# 全局配置实例
config = Config()