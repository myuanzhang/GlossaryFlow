"""
Base Rewrite Strategy Interface

Defines the abstract interface that all rewrite strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RewriteResult:
    """Result of a rewrite operation"""

    # Core content
    original_markdown: str
    rewritten_markdown: str

    # Statistics
    units_processed: int
    units_rewritten: int

    # Metadata
    strategy_name: str
    processing_time_ms: float
    warnings: List[str]

    # Additional context
    metadata: Dict[str, Any]

    @property
    def rewrite_rate(self) -> str:
        """Calculate rewrite percentage"""
        if self.units_processed == 0:
            return "0%"
        return f"{(self.units_rewritten / self.units_processed * 100):.1f}%"

    @property
    def rewrite_applied(self) -> bool:
        """Whether any rewriting was applied"""
        return self.units_rewritten > 0


@dataclass
class RewriteContext:
    """Context for rewrite operations"""

    # Document-level context
    document_intent: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    domain: Optional[str] = None

    # Processing options
    max_units: Optional[int] = None
    preserve_code_blocks: bool = True
    preserve_formatting: bool = True

    # LLM configuration
    temperature: float = 0.3
    timeout_seconds: int = 30


class RewriteStrategy(ABC):
    """
    Abstract base class for rewrite strategies.

    Each strategy defines how to process documents for rewriting.
    """

    def __init__(self, provider, config: Dict[str, Any] = None):
        """
        Initialize the rewrite strategy.

        Args:
            provider: LLM provider for rewriting operations
            config: Strategy-specific configuration
        """
        self.provider = provider
        self.config = config or {}

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the unique name of this strategy."""
        pass

    @abstractmethod
    def get_strategy_description(self) -> str:
        """Return a human-readable description of this strategy."""
        pass

    @abstractmethod
    def rewrite(self,
                source_markdown: str,
                context: RewriteContext) -> RewriteResult:
        """
        Rewrite the given markdown document.

        Args:
            source_markdown: Original markdown content
            context: Rewrite context and configuration

        Returns:
            RewriteResult with rewritten content and metadata
        """
        pass

    @abstractmethod
    def supports_document_type(self, document_type: str) -> bool:
        """
        Check if this strategy supports the given document type.

        Args:
            document_type: Type of document (e.g., 'markdown', 'plain_text')

        Returns:
            True if supported, False otherwise
        """
        pass

    def validate_configuration(self) -> List[str]:
        """
        Validate the strategy configuration.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if not self.provider:
            errors.append("LLM provider is required")
        elif not self.provider.is_configured():
            errors.append("LLM provider is not properly configured")

        return errors

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return the configuration schema for this strategy.

        Returns:
            Dictionary describing the expected configuration format
        """
        return {
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.3,
                    "description": "Response randomness"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 30,
                    "description": "Timeout in seconds per rewrite operation"
                }
            }
        }