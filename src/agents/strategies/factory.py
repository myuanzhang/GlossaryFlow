"""
Rewrite Strategy Factory

Provides factory methods for creating and selecting rewrite strategies.
"""

import logging
from typing import Dict, List, Optional, Type

from .base import RewriteStrategy
from .line_by_line import LineByLineRewriteStrategy
from .translation_oriented import TranslationOrientedRewriteStrategy

logger = logging.getLogger(__name__)


class RewriteStrategyFactory:
    """
    Factory for creating rewrite strategies.

    Supports strategy selection by name, configuration-based selection,
    and automatic strategy recommendation.
    """

    # Registry of available strategies
    _strategies: Dict[str, Type[RewriteStrategy]] = {
        "line_by_line": LineByLineRewriteStrategy,
        "translation_oriented": TranslationOrientedRewriteStrategy,
        # Future strategies will be registered here:
        # "paragraph_based": ParagraphBasedRewriteStrategy,
        # "semantic_aware": SemanticAwareRewriteStrategy,
    }

    @classmethod
    def create_strategy(cls,
                       strategy_name: str,
                       provider,
                       config: Dict = None) -> RewriteStrategy:
        """
        Create a rewrite strategy instance.

        Args:
            strategy_name: Name of the strategy to create
            provider: LLM provider instance
            config: Strategy-specific configuration

        Returns:
            RewriteStrategy instance

        Raises:
            ValueError: If strategy name is not recognized
        """
        if strategy_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown rewrite strategy: '{strategy_name}'. "
                f"Available strategies: {available}"
            )

        strategy_class = cls._strategies[strategy_name]
        strategy_instance = strategy_class(provider, config)

        logger.info(f"Created rewrite strategy: {strategy_name}")
        return strategy_instance

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """
        Get list of available strategy names.

        Returns:
            List of strategy names
        """
        return list(cls._strategies.keys())

    @classmethod
    def register_strategy(cls,
                         name: str,
                         strategy_class: Type[RewriteStrategy]):
        """
        Register a new rewrite strategy.

        Args:
            name: Unique name for the strategy
            strategy_class: Strategy class implementing RewriteStrategy

        Raises:
            ValueError: If strategy name already exists
        """
        if name in cls._strategies:
            raise ValueError(f"Strategy '{name}' is already registered")

        if not issubclass(strategy_class, RewriteStrategy):
            raise ValueError(f"Strategy class must inherit from RewriteStrategy")

        cls._strategies[name] = strategy_class
        logger.info(f"Registered rewrite strategy: {name}")

    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Optional[Dict]:
        """
        Get information about a specific strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Dictionary with strategy information, or None if not found
        """
        if strategy_name not in cls._strategies:
            return None

        strategy_class = cls._strategies[strategy_name]
        temp_instance = strategy_class(None, {})

        return {
            "name": strategy_name,
            "description": temp_instance.get_strategy_description(),
            "supports": ["markdown", "plain_text"],  # Could be dynamic
            "config_schema": temp_instance.get_config_schema()
        }

    @classmethod
    def list_strategies_with_info(cls) -> List[Dict]:
        """
        Get information about all available strategies.

        Returns:
            List of strategy information dictionaries
        """
        strategies_info = []
        for strategy_name in cls._strategies:
            info = cls.get_strategy_info(strategy_name)
            if info:
                strategies_info.append(info)

        return strategies_info

    @classmethod
    def create_default_strategy(cls, provider, config: Dict = None) -> RewriteStrategy:
        """
        Create the default rewrite strategy.

        Currently returns the legacy line-by-line strategy for backward compatibility.

        Args:
            provider: LLM provider instance
            config: Strategy configuration

        Returns:
            Default RewriteStrategy instance
        """
        return cls.create_strategy("line_by_line", provider, config)

    @classmethod
    def recommend_strategy(cls,
                          document_type: str,
                          document_length: int,
                          use_case: str = "general") -> str:
        """
        Recommend a strategy based on document characteristics.

        Args:
            document_type: Type of document ('markdown', 'plain_text')
            document_length: Length of document in characters
            use_case: Specific use case ('general', 'technical', 'creative')

        Returns:
            Recommended strategy name
        """
        # For now, always recommend line_by_line as it's the only available one
        # This method can be extended when more strategies are added
        return "line_by_line"

    @classmethod
    def validate_strategy_config(cls,
                                strategy_name: str,
                                config: Dict) -> List[str]:
        """
        Validate configuration for a specific strategy.

        Args:
            strategy_name: Name of the strategy
            config: Configuration to validate

        Returns:
            List of validation errors, empty if valid
        """
        if strategy_name not in cls._strategies:
            return [f"Unknown strategy: {strategy_name}"]

        strategy_class = cls._strategies[strategy_name]
        temp_instance = strategy_class(None, {})
        return temp_instance.validate_configuration()


class RewriteStrategySelector:
    """
    Strategy selector that can choose strategies based on various criteria.

    This class provides a higher-level interface for strategy selection,
    supporting configuration files, environment variables, and runtime parameters.
    """

    def __init__(self, default_strategy: str = "line_by_line"):
        """
        Initialize the strategy selector.

        Args:
            default_strategy: Default strategy name to use
        """
        self.default_strategy = default_strategy
        self.factory = RewriteStrategyFactory()

    def select_strategy(self,
                       strategy_name: Optional[str] = None,
                       config: Optional[Dict] = None,
                       document_type: str = "markdown",
                       document_length: int = 0) -> RewriteStrategy:
        """
        Select and create a rewrite strategy.

        Selection order:
        1. Explicit strategy_name parameter
        2. Configuration setting
        3. Default strategy

        Args:
            strategy_name: Explicit strategy name (highest priority)
            config: Strategy configuration
            document_type: Type of document
            document_length: Length of document

        Returns:
            Selected RewriteStrategy instance
        """
        # Use explicit strategy name if provided
        if strategy_name:
            selected_name = strategy_name
        else:
            # Use recommendation or default
            selected_name = self.factory.recommend_strategy(
                document_type, document_length
            )

        logger.info(f"Selected rewrite strategy: {selected_name}")
        return self.factory.create_strategy(selected_name, None, config)