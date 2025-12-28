"""
Rewrite Strategy Base

改写策略的抽象基类。
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from core.types import ProcessingResult, JobStatus, ProcessingStats, DocumentContext
from providers.base import BaseProvider


class RewriteContext:
    """改写上下文"""

    def __init__(
        self,
        document_intent: str = "技术文档",
        target_audience: str = "技术用户",
        tone: str = "professional",
        domain: str = "根据内容推断",
        timeout_seconds: int = 30,
        temperature: float = 0.3,
        max_retries: int = 3
    ):
        self.document_intent = document_intent
        self.target_audience = target_audience
        self.tone = tone
        self.domain = domain
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_retries = max_retries


class RewriteResult:
    """改写结果"""

    def __init__(
        self,
        rewritten_markdown: str,
        original_markdown: str,
        units_processed: int,
        units_rewritten: int,
        strategy_name: str,
        processing_time_ms: float,
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.rewritten_markdown = rewritten_markdown
        self.original_markdown = original_markdown
        self.units_processed = units_processed
        self.units_rewritten = units_rewritten
        self.strategy_name = strategy_name
        self.processing_time_ms = processing_time_ms
        self.warnings = warnings or []
        self.metadata = metadata or {}

    @property
    def rewrite_rate(self) -> float:
        """改写率"""
        if self.units_processed == 0:
            return 0.0
        return self.units_rewritten / self.units_processed


class RewriteStrategy(ABC):
    """改写策略抽象基类"""

    def __init__(self, provider: BaseProvider, config: Dict[str, Any] = None):
        """
        初始化改写策略

        Args:
            provider: LLM Provider
            config: 策略配置
        """
        self.provider = provider
        self.config = config or {}
        self.name = self.__class__.__name__.replace('RewriteStrategy', '').lower()

    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass

    @abstractmethod
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        pass

    @abstractmethod
    def rewrite(self, source_markdown: str, context: RewriteContext) -> RewriteResult:
        """
        执行改写

        Args:
            source_markdown: 源 Markdown 内容
            context: 改写上下文

        Returns:
            改写结果
        """
        pass

    def supports_document_type(self, document_type: str) -> bool:
        """
        检查是否支持特定文档类型

        Args:
            document_type: 文档类型

        Returns:
            是否支持
        """
        return document_type in ["markdown", "plain_text"]

    def validate_configuration(self) -> bool:
        """
        验证策略配置

        Returns:
            配置是否有效
        """
        return True

    def get_default_temperature(self) -> float:
        """获取默认温度"""
        return 0.3

    def get_max_tokens(self) -> Optional[int]:
        """获取最大 token 数"""
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, provider={self.provider.get_name()})>"