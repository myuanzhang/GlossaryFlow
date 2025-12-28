"""
Core Type Definitions

定义系统中使用的所有核心类型和枚举。
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass


class AgentType(Enum):
    """Agent 类型枚举"""
    TRANSLATION = "translation"
    REWRITE = "rewrite"
    QA = "qa"
    ORCHESTRATOR = "orchestrator"


class JobStatus(Enum):
    """作业状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StrategyType(Enum):
    """策略类型枚举"""
    TRANSLATION_STRATEGY = "translation_strategy"
    REWRITE_STRATEGY = "rewrite_strategy"
    QA_STRATEGY = "qa_strategy"


class ProviderType(Enum):
    """Provider 类型枚举"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    MOCK = "mock"
    CUSTOM = "custom"
    MIMO = "mimo"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"


@dataclass
class ProcessingStats:
    """处理统计信息"""
    units_processed: int = 0
    units_rewritten: int = 0
    rewrite_rate: float = 0.0
    processing_time_ms: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    error_count: int = 0
    warning_count: int = 0


@dataclass
class ProcessingResult:
    """处理结果"""
    status: JobStatus
    content: str
    metadata: Dict[str, Any]
    stats: ProcessingStats
    warnings: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "content": self.content,
            "metadata": self.metadata,
            "stats": {
                "units_processed": self.stats.units_processed,
                "units_rewritten": self.stats.units_rewritten,
                "rewrite_rate": self.stats.rewrite_rate,
                "processing_time_ms": self.stats.processing_time_ms,
                "token_usage": self.stats.token_usage,
                "error_count": self.stats.error_count,
                "warning_count": self.stats.warning_count
            },
            "warnings": self.warnings,
            "error": self.error
        }


@dataclass
class DocumentContext:
    """文档上下文信息"""
    intent: str = "技术文档"
    target_audience: str = "技术用户"
    tone: str = "professional"
    domain: str = "根据内容推断"
    source_lang: str = "zh"
    target_lang: str = "en"
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class SectionInfo:
    """章节信息"""
    section_type: str  # paragraph, header, list, code_block, etc.
    line_start: int
    line_end: int
    char_start: int
    char_end: int
    content: str


# 类型别名
MarkdownContent = str
StrategyConfig = Dict[str, Any]
ProviderConfig = Dict[str, Any]
JobInput = Dict[str, Any]
JobOutput = Dict[str, Any]