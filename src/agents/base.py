"""
Base Agent Interface

统一定义所有 Agent 的基础接口和契约。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.types import AgentType, JobStatus, ProcessingResult
from core.job import Job
from core.metadata import Metadata


class AgentCapability(Enum):
    """Agent 能力枚举"""
    TRANSLATION = "translation"
    REWRITE = "rewrite"
    QA = "qa"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_id: str
    agent_type: AgentType
    provider_name: str
    model_name: str
    strategy_name: Optional[str] = None
    strategy_config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[AgentCapability] = field(default_factory=list)
    timeout_seconds: int = 30
    max_retries: int = 3
    temperature: float = 0.3


class BaseAgent(ABC):
    """
    所有 Agent 的基础抽象类

    定义了统一的接口契约，确保所有 Agent 实现一致的行为模式。
    """

    def __init__(self, config: AgentConfig):
        """
        初始化 Agent

        Args:
            config: Agent 配置信息
        """
        self.config = config
        self.metadata = Metadata()
        self._provider = None
        self._strategy = None
        self._prompt_manager = None

        # 初始化组件
        self._initialize_components()

    @property
    def agent_id(self) -> str:
        """获取 Agent ID"""
        return self.config.agent_id

    @property
    def agent_type(self) -> AgentType:
        """获取 Agent 类型"""
        return self.config.agent_type

    @property
    def capabilities(self) -> List[AgentCapability]:
        """获取 Agent 能力列表"""
        return self.config.capabilities

    @abstractmethod
    def _initialize_components(self) -> None:
        """
        初始化 Agent 特有的组件

        子类必须实现此方法来初始化：
        - Provider
        - Strategy (如果有)
        - Prompt Manager
        """
        pass

    @abstractmethod
    def validate_input(self, job: Job) -> bool:
        """
        验证输入数据

        Args:
            job: 作业对象

        Returns:
            bool: 验证是否通过
        """
        pass

    @abstractmethod
    def process(self, job: Job) -> ProcessingResult:
        """
        处理单个作业

        Args:
            job: 要处理的作业

        Returns:
            ProcessingResult: 处理结果
        """
        pass

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent 的主要功能

        这是 CLI 和其他系统调用的主要接口。

        Args:
            input_data: 输入数据，包含：
                - job_id: 作业ID
                - content: Markdown 内容
                - source_lang: 源语言
                - target_lang: 目标语言
                - strategy_name: 策略名称
                - additional_params: 额外参数

        Returns:
            Dict[str, Any]: 输出数据，包含：
                - job_id: 作业ID
                - status: 处理状态
                - result: 处理结果
                - metadata: 元数据
                - error: 错误信息 (如果有)
        """
        try:
            # 创建作业对象
            job = Job.from_dict(input_data)

            # 验证输入
            if not self.validate_input(job):
                raise ValueError(f"Invalid input for agent {self.agent_id}")

            # 处理作业
            result = self.process(job)

            # 返回结果
            return {
                "job_id": job.job_id,
                "status": result.status.value,
                "result": result.to_dict(),
                "metadata": self.metadata.to_dict(),
                "agent_info": {
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type.value,
                    "provider": self.config.provider_name,
                    "model": self.config.model_name,
                    "strategy": self.config.strategy_name
                }
            }

        except Exception as e:
            return {
                "job_id": input_data.get("job_id", "unknown"),
                "status": JobStatus.FAILED.value,
                "result": None,
                "metadata": self.metadata.to_dict(),
                "error": str(e),
                "agent_info": {
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type.value,
                    "provider": self.config.provider_name,
                    "model": self.config.model_name,
                    "strategy": self.config.strategy_name
                }
            }

    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        获取可用策略列表

        Returns:
            策略信息列表
        """
        if not hasattr(self, '_strategy_factory'):
            return []

        return self._strategy_factory.list_strategies()

    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取 Agent 信息

        Returns:
            Agent 信息字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "provider": self.config.provider_name,
            "model": self.config.model_name,
            "strategy": self.config.strategy_name,
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
                "temperature": self.config.temperature
            }
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, type={self.agent_type.value})>"