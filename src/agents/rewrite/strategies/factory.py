"""
Rewrite Strategy Factory

改写策略工厂，负责创建和管理改写策略。
"""

import logging
from typing import Dict, Any, Optional, List, Type

from .base import RewriteStrategy, RewriteContext
from providers.base import BaseProvider
from .line_by_line import LineByLineRewriteStrategy
from .translation_oriented import TranslationOrientedRewriteStrategy

logger = logging.getLogger(__name__)


class RewriteStrategyFactory:
    """改写策略工厂"""

    def __init__(self):
        self._strategy_classes: Dict[str, Type[RewriteStrategy]] = {}
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """注册默认策略"""
        self.register_strategy("line_by_line", LineByLineRewriteStrategy)
        self.register_strategy("translation_oriented", TranslationOrientedRewriteStrategy)

    def register_strategy(self, name: str, strategy_class: Type[RewriteStrategy]) -> None:
        """
        注册策略类

        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, RewriteStrategy):
            raise ValueError(f"Strategy class must inherit from RewriteStrategy: {strategy_class}")

        self._strategy_classes[name] = strategy_class
        logger.debug(f"Registered rewrite strategy: {name}")

    def create_strategy(
        self,
        name: str,
        provider: BaseProvider,
        config: Dict[str, Any] = None
    ) -> RewriteStrategy:
        """
        创建策略实例

        Args:
            name: 策略名称
            provider: LLM Provider
            config: 策略配置

        Returns:
            策略实例
        """
        if name not in self._strategy_classes:
            raise ValueError(f"Unknown strategy: {name}. Available: {list(self._strategy_classes.keys())}")

        strategy_class = self._strategy_classes[name]
        try:
            strategy = strategy_class(provider, config)

            # 验证策略配置
            if not strategy.validate_configuration():
                logger.warning(f"Strategy configuration validation failed: {name}")

            return strategy

        except Exception as e:
            logger.error(f"Failed to create strategy {name}: {e}")
            raise

    def create_default_strategy(self, provider: BaseProvider) -> RewriteStrategy:
        """
        创建默认策略

        Args:
            provider: LLM Provider

        Returns:
            默认策略实例
        """
        return self.create_strategy("line_by_line", provider)

    def list_available_strategies(self) -> List[Dict[str, str]]:
        """
        列出可用策略

        Returns:
            策略信息列表
        """
        strategies = []

        for name, strategy_class in self._strategy_classes.items():
            # 创建临时实例以获取信息
            try:
                from providers.mock.provider import MockProvider
                from providers.base import ProviderConfig

                mock_config = ProviderConfig(
                    provider_type="mock",
                    timeout_seconds=30,
                    max_retries=3
                )
                mock_provider = MockProvider(mock_config)
                temp_strategy = strategy_class(mock_provider)

                strategies.append({
                    "name": name,
                    "description": temp_strategy.get_strategy_description(),
                    "class": strategy_class.__name__
                })
            except Exception as e:
                logger.warning(f"Failed to get info for strategy {name}: {e}")
                strategies.append({
                    "name": name,
                    "description": f"{strategy_class.__name__} (description unavailable)",
                    "class": strategy_class.__name__
                })

        return strategies

    def list_strategies(self) -> List[str]:
        """
        列出可用策略名称 (向后兼容别名)

        Returns:
            策略名称列表
        """
        return list(self._strategy_classes.keys())

    def get_strategy_info(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取策略信息

        Args:
            name: 策略名称

        Returns:
            策略信息或 None
        """
        strategies = self.list_available_strategies()
        for strategy in strategies:
            if strategy["name"] == name:
                return strategy
        return None

    def is_strategy_available(self, name: str) -> bool:
        """
        检查策略是否可用

        Args:
            name: 策略名称

        Returns:
            是否可用
        """
        return name in self._strategy_classes

    def validate_strategy_config(self, name: str, config: Dict[str, Any]) -> bool:
        """
        验证策略配置

        Args:
            name: 策略名称
            config: 配置字典

        Returns:
            配置是否有效
        """
        if not self.is_strategy_available(name):
            return False

        try:
            from ....providers.mock import MockProvider
            from ....providers.base import ProviderConfig

            mock_config = ProviderConfig(
                provider_type="mock",
                timeout_seconds=30,
                max_retries=3
            )
            mock_provider = MockProvider(mock_config)
            temp_strategy = self.create_strategy(name, mock_provider, config)
            return temp_strategy.validate_configuration()
        except Exception as e:
            logger.error(f"Strategy validation failed: {e}")
            return False

    def get_recommended_strategy(self, content: str, context: RewriteContext) -> str:
        """
        根据内容推荐策略

        Args:
            content: Markdown 内容
            context: 改写上下文

        Returns:
            推荐的策略名称
        """
        # 简单的推荐逻辑
        if "翻译" in content or context.document_intent == "翻译":
            return "translation_oriented"
        else:
            return "line_by_line"

    def migrate_legacy_strategy(self, legacy_name: str) -> str:
        """
        迁移旧版策略名称

        Args:
            legacy_name: 旧版策略名称

        Returns:
            新版策略名称
        """
        # 旧版名称映射
        legacy_mapping = {
            "line-by-line": "line_by_line",
            "translation-oriented": "translation_oriented",
        }

        return legacy_mapping.get(legacy_name, legacy_name)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取工厂统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_strategies": len(self._strategy_classes),
            "available_strategies": list(self._strategy_classes.keys()),
            "strategy_classes": {name: cls.__name__ for name, cls in self._strategy_classes.items()}
        }


# 全局策略工厂实例
rewrite_strategy_factory = RewriteStrategyFactory()