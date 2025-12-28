"""
Provider Registry

Provider 注册中心，管理所有 LLM Provider 的注册和创建。
"""

import logging
from typing import Dict, Any, Optional, List
from core.types import ProviderType
from providers.base import BaseProvider, ProviderConfig

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Provider 注册中心"""

    def __init__(self):
        self._providers: Dict[str, type] = {}
        self._provider_classes: Dict[ProviderType, type] = {}
        self._instances: Dict[str, BaseProvider] = {}

        # 注册默认 Provider 类
        self._register_default_classes()

    def _register_default_classes(self) -> None:
        """注册默认的 Provider 类"""
        # 延迟导入避免循环依赖
        try:
            from .openai.provider import OpenAIProvider
            self.register_provider_class(ProviderType.OPENAI, OpenAIProvider)
        except ImportError:
            logger.warning("OpenAI provider not available")

        try:
            from .ollama.provider import OllamaProvider
            self.register_provider_class(ProviderType.OLLAMA, OllamaProvider)
        except ImportError:
            logger.warning("Ollama provider not available")

        try:
            from .mimo.provider import MimoProvider
            self.register_provider_class(ProviderType.MIMO, MimoProvider)
        except ImportError:
            logger.warning("Mimo provider not available")

        try:
            from .deepseek.provider import DeepSeekProvider
            self.register_provider_class(ProviderType.DEEPSEEK, DeepSeekProvider)
        except ImportError:
            logger.warning("DeepSeek provider not available")

        try:
            from .mock.provider import MockProvider
            self.register_provider_class(ProviderType.MOCK, MockProvider)
        except ImportError:
            logger.warning("Mock provider not available")

        try:
            from .qwen.provider import QwenProvider
            self.register_provider_class(ProviderType.QWEN, QwenProvider)
        except ImportError:
            logger.warning("Qwen provider not available")

    def register_provider_class(self, provider_type: ProviderType, provider_class: type) -> None:
        """
        注册 Provider 类

        Args:
            provider_type: Provider 类型
            provider_class: Provider 类
        """
        if not issubclass(provider_class, BaseProvider):
            raise ValueError(f"Provider class must inherit from BaseProvider: {provider_class}")

        self._provider_classes[provider_type] = provider_class
        logger.debug(f"Registered provider class: {provider_type.value} -> {provider_class.__name__}")

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """
        注册 Provider 实例

        Args:
            name: Provider 名称
            provider: Provider 实例
        """
        if not isinstance(provider, BaseProvider):
            raise ValueError(f"Provider must be an instance of BaseProvider: {type(provider)}")

        self._providers[name.lower()] = provider
        logger.debug(f"Registered provider: {name}")

    def get_or_create(self, provider_name: str, model: Optional[str] = None, config: Optional[ProviderConfig] = None) -> Optional[BaseProvider]:
        """
        获取或创建 Provider 实例

        Args:
            provider_name: Provider 名称
            model: 模型名称
            config: Provider 配置

        Returns:
            Provider 实例或 None
        """
        provider_name = provider_name.lower()

        # 尝试从现有实例获取
        cache_key = f"{provider_name}:{model or 'default'}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        # 尝试从注册的类创建
        provider_type = self._get_provider_type(provider_name)
        if provider_type and provider_type in self._provider_classes:
            try:
                # 如果没有提供配置，使用默认配置
                if config is None:
                    from core.config import config as global_config
                    config_dict = global_config.get_provider_config(provider_name)
                    config = ProviderConfig(**config_dict)

                # 根据provider类型传递不同的参数
                from core.config import config as global_config

                if provider_type == ProviderType.OPENAI:
                    # OpenAI Provider需要传递配置的模型列表
                    models_config = global_config.openai_models
                    provider = self._provider_classes[provider_type](config, models_config)
                elif provider_type == ProviderType.MIMO:
                    # Mimo Provider需要传递配置的模型列表
                    models_config = global_config.mimo_models
                    provider = self._provider_classes[provider_type](config, models_config)
                elif provider_type == ProviderType.DEEPSEEK:
                    # DeepSeek Provider需要传递配置的模型列表
                    models_config = global_config.deepseek_models
                    provider = self._provider_classes[provider_type](config, models_config)
                elif provider_type == ProviderType.QWEN:
                    # Qwen Provider需要传递配置的模型列表
                    models_config = global_config.qwen_models
                    provider = self._provider_classes[provider_type](config, models_config)
                else:
                    # 其他Provider使用原有方式
                    provider = self._provider_classes[provider_type](config)

                # 缓存实例
                self._instances[cache_key] = provider
                logger.debug(f"Created provider: {cache_key}")

                return provider

            except Exception as e:
                logger.error(f"Failed to create provider {provider_name}: {e}")
                return None

        logger.warning(f"Provider not found: {provider_name}")
        return None

    def get_provider_class(self, provider_type: ProviderType) -> Optional[type]:
        """
        获取 Provider 类

        Args:
            provider_type: Provider 类型

        Returns:
            Provider 类或 None
        """
        return self._provider_classes.get(provider_type)

    def list_available_providers(self) -> List[str]:
        """
        列出所有可用的 Provider

        Returns:
            Provider 名称列表
        """
        providers = list(self._providers.keys())

        # 添加可创建但未实例化的 Provider
        for provider_type in self._provider_classes:
            if provider_type.value not in providers:
                providers.append(provider_type.value)

        return sorted(providers)

    def list_available_models(self, provider_name: str) -> List[str]:
        """
        列出指定 Provider 的可用模型

        Args:
            provider_name: Provider 名称

        Returns:
            模型名称列表
        """
        provider = self.get_or_create(provider_name)
        if provider:
            return provider.get_available_models()
        return []

    def is_provider_available(self, provider_name: str) -> bool:
        """
        检查 Provider 是否可用

        Args:
            provider_name: Provider 名称

        Returns:
            是否可用
        """
        provider = self.get_or_create(provider_name)
        return provider is not None and provider.is_configured()

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取 Provider 信息

        Args:
            provider_name: Provider 名称

        Returns:
            Provider 信息或 None
        """
        provider = self.get_or_create(provider_name)
        if provider:
            return provider.get_provider_info()
        return None

    def _get_provider_type(self, provider_name: str) -> Optional[ProviderType]:
        """
        根据名称获取 Provider 类型

        Args:
            provider_name: Provider 名称

        Returns:
            Provider 类型或 None
        """
        provider_mapping = {
            "openai": ProviderType.OPENAI,
            "ollama": ProviderType.OLLAMA,
            "mimo": ProviderType.MIMO,
            "deepseek": ProviderType.DEEPSEEK,
            "mock": ProviderType.MOCK,
            "qwen": ProviderType.QWEN,
        }

        return provider_mapping.get(provider_name.lower())

    def clear_cache(self) -> None:
        """清除 Provider 实例缓存"""
        self._instances.clear()
        logger.debug("Cleared provider cache")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取注册中心统计信息

        Returns:
            统计信息字典
        """
        return {
            "registered_classes": len(self._provider_classes),
            "registered_instances": len(self._providers),
            "cached_instances": len(self._instances),
            "available_providers": self.list_available_providers(),
            "provider_types": [pt.value for pt in self._provider_classes.keys()]
        }

    def validate_provider_config(self, config: Dict[str, Any]) -> bool:
        """
        验证 Provider 配置

        Args:
            config: 配置字典

        Returns:
            验证是否通过
        """
        required_fields = ["provider_type"]

        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field in provider config: {field}")
                return False

        try:
            provider_type = ProviderType(config["provider_type"])
            return provider_type in self._provider_classes
        except ValueError:
            logger.error(f"Invalid provider_type: {config.get('provider_type')}")
            return False

    def create_provider_from_config(self, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """
        从配置创建 Provider

        Args:
            config: 配置字典

        Returns:
            Provider 实例或 None
        """
        if not self.validate_provider_config(config):
            return None

        try:
            provider_config = ProviderConfig(**config)
            provider_type = ProviderType(config["provider_type"])

            if provider_type in self._provider_classes:
                provider = self._provider_classes[provider_type](provider_config)
                return provider

            logger.error(f"Provider class not registered: {provider_type}")
            return None

        except Exception as e:
            logger.error(f"Failed to create provider from config: {e}")
            return None


# 全局 Provider 注册中心实例
provider_registry = ProviderRegistry()