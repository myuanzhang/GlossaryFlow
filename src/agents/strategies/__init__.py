"""
Rewrite Strategies Module

Provides pluggable rewrite strategies for different document processing approaches.
"""

from .base import RewriteStrategy, RewriteResult, RewriteContext
from .factory import RewriteStrategyFactory
from .line_by_line import LineByLineRewriteStrategy
from .translation_oriented import TranslationOrientedRewriteStrategy

__all__ = [
    "RewriteStrategy",
    "RewriteResult",
    "RewriteContext",
    "RewriteStrategyFactory",
    "LineByLineRewriteStrategy",
    "TranslationOrientedRewriteStrategy"
]