"""
Rewrite Agent Implementation

重构后的 Rewrite Agent，实现统一的 BaseAgent 接口。
"""

import logging
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent, AgentConfig, AgentCapability
from core.types import (
    AgentType, JobStatus, ProcessingResult, ProcessingStats,
    DocumentContext, SectionInfo
)
from core.job import Job
from providers.registry import provider_registry
from providers.base import BaseProvider
from .strategies.factory import RewriteStrategyFactory
from .strategies.base import RewriteStrategy, RewriteResult

logger = logging.getLogger(__name__)


class RewriteAgent(BaseAgent):
    """
    Rewrite Agent 实现

    负责文档改写功能，支持多种改写策略。
    """

    def __init__(self, config: AgentConfig):
        """
        初始化 Rewrite Agent

        Args:
            config: Agent 配置
        """
        # 确保配置包含正确的类型和能力
        config.agent_type = AgentType.REWRITE
        if not config.capabilities:
            config.capabilities = [AgentCapability.REWRITE]

        super().__init__(config)

    def _initialize_components(self) -> None:
        """初始化 Rewrite Agent 特有的组件"""
        # 初始化 Provider
        self._provider = provider_registry.get_or_create(
            self.config.provider_name,
            self.config.model_name
        )

        if not self._provider:
            raise ValueError(f"Provider {self.config.provider_name} not available")

        # 初始化 Strategy Factory
        self._strategy_factory = RewriteStrategyFactory()

        # 初始化当前 Strategy
        if self.config.strategy_name:
            self._strategy = self._strategy_factory.create_strategy(
                self.config.strategy_name,
                self._provider,
                self.config.strategy_config
            )
        else:
            # 使用默认策略
            self._strategy = self._strategy_factory.create_default_strategy(
                self._provider
            )

        # 初始化 Prompt Manager (如果需要)
        try:
            from ....prompt.managers.rewrite_prompt_manager import RewritePromptManager
            self._prompt_manager = RewritePromptManager()
        except ImportError:
            self._prompt_manager = None

        logger.info(f"Initialized RewriteAgent with strategy: {self._strategy.get_strategy_name()}")

    def validate_input(self, job: Job) -> bool:
        """
        验证输入数据

        Args:
            job: 作业对象

        Returns:
            验证是否通过
        """
        if not job.content:
            logger.error("Job content is empty")
            return False

        if job.agent_type != AgentType.REWRITE:
            logger.error(f"Invalid agent type: {job.agent_type}")
            return False

        if self.config.strategy_name and job.strategy_name:
            if self.config.strategy_name != job.strategy_name:
                logger.warning(f"Strategy mismatch: config={self.config.strategy_name}, job={job.strategy_name}")

        return True

    def process(self, job: Job) -> ProcessingResult:
        """
        处理改写作业

        Args:
            job: 要处理的作业

        Returns:
            处理结果
        """
        start_time = self._get_current_time_ms()
        logger.info(f"Starting rewrite job {job.job_id}")

        try:
            # 标记作业开始
            job.start_processing()

            # 创建 RewriteContext
            context = self._create_rewrite_context(job)

            # 执行改写
            result = self._strategy.rewrite(job.content, context)

            # 更新作业元数据
            self._update_job_metadata(job, result)

            # 标记作业完成
            job.complete_processing()

            # 创建统计信息
            processing_time = self._get_current_time_ms() - start_time
            stats = ProcessingStats(
                units_processed=result.units_processed,
                units_rewritten=result.units_rewritten,
                rewrite_rate=result.units_rewritten / result.units_processed if result.units_processed > 0 else 0,
                processing_time_ms=processing_time,
                token_usage=self._extract_token_usage(result),
                error_count=len([w for w in result.warnings if "error" in w.lower()]),
                warning_count=len(result.warnings)
            )

            logger.info(f"Rewrite job {job.job_id} completed: {result.units_rewritten}/{result.units_processed} units rewritten")

            return ProcessingResult(
                status=JobStatus.COMPLETED,
                content=result.rewritten_markdown,
                metadata=result.metadata,
                stats=stats,
                warnings=result.warnings
            )

        except Exception as e:
            error_msg = f"Rewrite job {job.job_id} failed: {str(e)}"
            logger.error(error_msg)

            job.fail_processing(error_msg)

            return ProcessingResult(
                status=JobStatus.FAILED,
                content=job.content,  # 返回原始内容
                metadata={"error": error_msg},
                stats=ProcessingStats(error_count=1),
                error=error_msg
            )

    def _create_rewrite_context(self, job: Job) -> 'RewriteContext':
        """
        创建改写上下文

        Args:
            job: 作业对象

        Returns:
            RewriteContext 实例
        """
        from .strategies.base import RewriteContext

        return RewriteContext(
            document_intent=job.context.intent,
            target_audience=job.context.target_audience,
            tone=job.context.tone,
            domain=job.context.domain,
            timeout_seconds=self.config.timeout_seconds,
            temperature=self.config.temperature,
            max_retries=self.config.max_retries
        )

    def _update_job_metadata(self, job: Job, result: RewriteResult) -> None:
        """
        更新作业元数据

        Args:
            job: 作业对象
            result: 改写结果
        """
        job.add_metadata("strategy_used", result.strategy_name)
        job.add_metadata("provider_used", self._provider.get_name())
        job.add_metadata("model_used", self.config.model_name)
        job.add_metadata("processing_details", result.metadata)

    def _extract_token_usage(self, result: RewriteResult) -> Optional[Dict[str, int]]:
        """
        提取 Token 使用情况

        Args:
            result: 改写结果

        Returns:
            Token 使用统计
        """
        metadata = result.metadata or {}
        return metadata.get("token_usage")

    def _get_current_time_ms(self) -> float:
        """获取当前时间（毫秒）"""
        import time
        return time.time() * 1000

    def switch_strategy(self, strategy_name: str, strategy_config: Optional[Dict[str, Any]] = None) -> None:
        """
        切换改写策略

        Args:
            strategy_name: 新策略名称
            strategy_config: 策略配置
        """
        if strategy_name not in self._strategy_factory.list_available_strategies():
            raise ValueError(f"Unknown strategy: {strategy_name}")

        self.config.strategy_name = strategy_name
        self.config.strategy_config = strategy_config or {}

        self._strategy = self._strategy_factory.create_strategy(
            strategy_name,
            self._provider,
            self.config.strategy_config
        )

        logger.info(f"Switched to strategy: {strategy_name}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取当前策略信息

        Returns:
            策略信息字典
        """
        return {
            "current_strategy": self._strategy.get_strategy_name(),
            "strategy_description": self._strategy.get_strategy_description(),
            "available_strategies": self.get_available_strategies()
        }

    def __repr__(self) -> str:
        return f"<RewriteAgent(id={self.agent_id}, strategy={self._strategy.get_strategy_name()})>"