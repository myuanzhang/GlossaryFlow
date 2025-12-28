"""
Job Management

定义作业的核心数据结构和管理逻辑。
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .types import (
    AgentType, JobStatus, DocumentContext,
    MarkdownContent, StrategyConfig
)


@dataclass
class Job:
    """
    表示一个处理作业的核心数据结构

    包含了作业处理所需的所有信息和状态。
    """
    job_id: str
    agent_type: AgentType
    content: MarkdownContent
    status: JobStatus = JobStatus.PENDING
    context: DocumentContext = field(default_factory=DocumentContext)
    strategy_name: Optional[str] = None
    strategy_config: StrategyConfig = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_new(
        cls,
        agent_type: AgentType,
        content: MarkdownContent,
        context: Optional[DocumentContext] = None,
        strategy_name: Optional[str] = None,
        strategy_config: Optional[StrategyConfig] = None,
        **kwargs
    ) -> 'Job':
        """
        创建新的作业

        Args:
            agent_type: Agent 类型
            content: Markdown 内容
            context: 文档上下文
            strategy_name: 策略名称
            strategy_config: 策略配置
            **kwargs: 其他元数据

        Returns:
            新的 Job 实例
        """
        job_id = str(uuid.uuid4())

        if context is None:
            context = DocumentContext()

        if strategy_config is None:
            strategy_config = {}

        metadata = {k: v for k, v in kwargs.items() if v is not None}

        return cls(
            job_id=job_id,
            agent_type=agent_type,
            content=content,
            context=context,
            strategy_name=strategy_name,
            strategy_config=strategy_config,
            metadata=metadata
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """
        从字典创建 Job

        Args:
            data: 字典数据

        Returns:
            Job 实例
        """
        # 提取上下文信息
        context_data = data.get('context', {})
        context = DocumentContext(
            intent=context_data.get('intent', '技术文档'),
            target_audience=context_data.get('target_audience', '技术用户'),
            tone=context_data.get('tone', 'professional'),
            domain=context_data.get('domain', '根据内容推断'),
            source_lang=context_data.get('source_lang', 'zh'),
            target_lang=context_data.get('target_lang', 'en'),
            additional_params=context_data.get('additional_params', {})
        )

        return cls(
            job_id=data.get('job_id', str(uuid.uuid4())),
            agent_type=AgentType(data.get('agent_type', 'rewrite')),
            content=data.get('content', ''),
            status=JobStatus(data.get('status', 'pending')),
            context=context,
            strategy_name=data.get('strategy_name'),
            strategy_config=data.get('strategy_config', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            字典表示的作业数据
        """
        return {
            'job_id': self.job_id,
            'agent_type': self.agent_type.value,
            'content': self.content,
            'status': self.status.value,
            'context': {
                'intent': self.context.intent,
                'target_audience': self.context.target_audience,
                'tone': self.context.tone,
                'domain': self.context.domain,
                'source_lang': self.context.source_lang,
                'target_lang': self.context.target_lang,
                'additional_params': self.context.additional_params
            },
            'strategy_name': self.strategy_name,
            'strategy_config': self.strategy_config,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'metadata': self.metadata
        }

    def start_processing(self) -> None:
        """标记作业开始处理"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def complete_processing(self) -> None:
        """标记作业处理完成"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()

    def fail_processing(self, error_message: str) -> None:
        """
        标记作业处理失败

        Args:
            error_message: 错误信息
        """
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()

    def cancel_processing(self) -> None:
        """取消作业处理"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()

    @property
    def processing_time_seconds(self) -> Optional[float]:
        """
        获取处理时间（秒）

        Returns:
            处理时间，如果作业未完成则返回 None
        """
        if not self.started_at or not self.completed_at:
            return None

        return (self.completed_at - self.started_at).total_seconds()

    @property
    def content_length(self) -> int:
        """获取内容长度"""
        return len(self.content)

    def add_metadata(self, key: str, value: Any) -> None:
        """
        添加元数据

        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        获取元数据

        Args:
            key: 元数据键
            default: 默认值

        Returns:
            元数据值
        """
        return self.metadata.get(key, default)

    def __repr__(self) -> str:
        return f"<Job(id={self.job_id[:8]}..., type={self.agent_type.value}, status={self.status.value})>"