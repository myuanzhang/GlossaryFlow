"""
Rewrite Strategies Package

提供各种改写策略实现。
"""

from .base import RewriteStrategy, RewriteResult, RewriteContext
from .factory import RewriteStrategyFactory, rewrite_strategy_factory
from .line_by_line import LineByLineRewriteStrategy
from .translation_oriented import TranslationOrientedRewriteStrategy

__all__ = [
    "RewriteStrategy",
    "RewriteResult",
    "RewriteContext",
    "RewriteStrategyFactory",
    "rewrite_strategy_factory",
    "LineByLineRewriteStrategy",
    "TranslationOrientedRewriteStrategy"
]