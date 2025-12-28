"""
Base Provider Interface

统一定义所有 LLM Provider 的基础接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from core.types import ProviderType


class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    MULTILINGUAL = "multilingual"


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    provider: ProviderType
    capabilities: List[ModelCapability]
    max_tokens: int
    supports_streaming: bool = False
    supports_function_calling: bool = False
    pricing: Optional[Dict[str, float]] = None


@dataclass
class ProviderConfig:
    """Provider 配置"""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 120  # Increased from 30 to 120 seconds for slower models
    max_retries: int = 3
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class BaseProvider(ABC):
    """
    所有 LLM Provider 的基础抽象类

    定义了统一的接口契约，确保所有 Provider 实现一致的行为模式。
    """

    def __init__(self, config: ProviderConfig):
        """
        初始化 Provider

        Args:
            config: Provider 配置信息
        """
        self.config = config
        self._models_cache: Dict[str, ModelInfo] = {}

    @property
    def provider_type(self) -> ProviderType:
        """获取 Provider 类型"""
        return self.config.provider_type

    @abstractmethod
    def is_configured(self) -> bool:
        """
        检查 Provider 是否已正确配置

        Returns:
            bool: 是否已配置
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        验证 Provider 配置是否完整有效

        ⚠️ CRITICAL: 必须由子类实现，校验逻辑因 Provider 类型而异

        Returns:
            (is_valid, error_message): 配置是否有效及错误信息
        """
        pass

    @abstractmethod
    def health_check(self) -> tuple[bool, Optional[str]]:
        """
        真实 Health Check - 验证 Provider 是否能正常工作

        ⚠️ CRITICAL: 必须由子类实现，检查逻辑因 Provider 类型而异:
        - Cloud Provider: 检查 API Key 有效性
        - Local Provider: 检查本地服务可用性

        Returns:
            (is_healthy, error_message): 是否健康及错误信息
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        pass

    @abstractmethod
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        获取模型信息

        Args:
            model_name: 模型名称

        Returns:
            模型信息，如果模型不存在则返回 None
        """
        pass

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        异步生成文本

        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        pass

    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        同步生成文本

        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        # 默认实现：调用异步版本
        import asyncio
        return asyncio.run(self.generate_async(
            prompt, model, temperature, max_tokens, **kwargs
        ))

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            model: 模型名称（可选）
            **kwargs: 其他参数

        Returns:
            翻译后的文本
        """
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """
        获取 Provider 信息

        Returns:
            Provider 信息字典
        """
        return {
            "provider_type": self.provider_type.value,
            "is_configured": self.is_configured(),
            "available_models": self.get_available_models(),
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
                "has_api_key": bool(self.config.api_key),
                "base_url": self.config.base_url
            }
        }

    def validate_model(self, model_name: str) -> bool:
        """
        验证模型是否可用

        Args:
            model_name: 模型名称

        Returns:
            模型是否可用
        """
        available_models = self.get_available_models()
        return model_name in available_models

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(type={self.provider_type.value})>"