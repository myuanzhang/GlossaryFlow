"""
Rewrite CLI Command

改写功能的 CLI 命令实现。
"""

import argparse
from typing import List

from ..base import CLICommand, BackwardCompatibleCommand
from agents.base import AgentConfig, AgentCapability
from agents.rewrite.agent import RewriteAgent
from core.types import AgentType


class RewriteCommand(CLICommand):
    """
    改写 CLI 命令

    提供文档改写功能的命令行接口。
    """

    def __init__(self):
        super().__init__(
            name="rewrite",
            description="文档改写工具 - 支持多种改写策略"
        )

    def create_parser(self) -> argparse.ArgumentParser:
        """
        创建改写命令的参数解析器

        Returns:
            参数解析器
        """
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  %(prog)s input.md output.md
  %(prog)s input.md output.md --strategy translation_oriented
  %(prog)s input.md output.md --strategy line_by_line --temperature 0.5
  %(prog)s --list-strategies
            """
        )

        # 基本参数
        parser.add_argument(
            'input_file',
            nargs='?',
            help='输入 Markdown 文件路径'
        )

        parser.add_argument(
            'output_file',
            nargs='?',
            help='输出 Markdown 文件路径'
        )

        # 策略相关参数
        parser.add_argument(
            '--strategy',
            help='改写策略名称 (line_by_line, translation_oriented, paragraph_based)',
            default=None
        )

        parser.add_argument(
            '--list-strategies',
            action='store_true',
            help='列出所有可用的改写策略'
        )

        # 处理参数
        parser.add_argument(
            '--temperature',
            type=float,
            default=0.3,
            help='AI 生成温度 (0.0-2.0，默认 0.3)'
        )

        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='单个操作超时时间（秒，默认 30）'
        )

        # 文档上下文参数
        parser.add_argument(
            '--intent',
            default='技术文档',
            help='文档意图（技术文档、商业报告、学术论文等）'
        )

        parser.add_argument(
            '--audience',
            default='技术用户',
            help='目标读者（技术开发人员、业务人员、学生等）'
        )

        parser.add_argument(
            '--tone',
            choices=['professional', 'casual', 'formal'],
            default='professional',
            help='文档语气风格'
        )

        parser.add_argument(
            '--domain',
            default='根据内容推断',
            help='专业领域'
        )

        # 输出控制参数
        parser.add_argument(
            '--output-dir',
            default='rewritten_docs',
            help='输出目录（默认 rewritten_docs）'
        )

        parser.add_argument(
            '--verbose',
            action='store_true',
            help='显示详细处理信息'
        )

        parser.add_argument(
            '--debug',
            action='store_true',
            help='显示调试信息'
        )

        return parser

    def get_agent_type(self) -> AgentType:
        """获取对应的 Agent 类型"""
        return AgentType.REWRITE

    def _create_rewrite_agent(self, strategy_name: str = None, **kwargs) -> BaseAgent:
        """
        设置 Rewrite Agent

        Args:
            strategy_name: 策略名称
            **kwargs: 其他配置参数
        """
        from ...config import config

        # 创建 Agent 配置
        agent_config = AgentConfig(
            agent_id=f"rewrite_cli_{strategy_name or 'default'}",
            agent_type=self.get_agent_type(),
            provider_name=config.provider,
            model_name="gpt-3.5-turbo" if config.provider == "openai" else config.ollama_model,
            strategy_name=strategy_name,
            strategy_config=kwargs,
            capabilities=[AgentCapability.REWRITE],
            timeout_seconds=kwargs.get('timeout', 30),
            temperature=kwargs.get('temperature', 0.3)
        )

        # 创建并返回 Agent
        agent = RewriteAgent(agent_config)
        return agent

    def execute(self, args: List[str] = None) -> int:
        """
        执行改写命令

        Args:
            args: 命令行参数列表

        Returns:
            退出码
        """
        # 解析参数
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        # 处理 --list-strategies
        if parsed_args.list_strategies:
            return self._list_strategies()

        # 验证必需参数
        if not parsed_args.input_file or not parsed_args.output_file:
            parser.error("必须提供输入文件和输出文件路径")

        # 创建 Agent
        agent = self._create_rewrite_agent(
            strategy_name=parsed_args.strategy,
            temperature=parsed_args.temperature,
            timeout=parsed_args.timeout
        )

        # 设置 Agent
        super().setup_agent(agent)

        # 调用父类执行
        return super().execute([parsed_args.input_file, parsed_args.output_file])

    def _list_strategies(self) -> int:
        """
        列出所有可用策略

        Returns:
            退出码
        """
        try:
            # 临时创建 Agent 来获取策略列表
            from ...config import config
            agent_config = AgentConfig(
                agent_id="temp",
                agent_type=AgentType.REWRITE,
                provider_name=config.provider,
                model_name=config.openai_model if config.provider == "openai" else config.ollama_model
            )

            temp_agent = RewriteAgent(agent_config)
            strategies = temp_agent.get_available_strategies()

            print("📝 可用的改写策略:")
            print("=" * 50)

            for strategy in strategies:
                print(f"🔧 {strategy['name']}")
                print(f"   {strategy['description']}")
                print()

            return 0

        except Exception as e:
            print(f"❌ 获取策略列表失败: {str(e)}")
            return 1


class LegacyRewriteCommand(BackwardCompatibleCommand):
    """
    向后兼容的改写命令

    为现有的 rewrite.py 和 rewrite_new.py 提供向后兼容。
    """

    def __init__(self, name: str, description: str, legacy_script_path: str):
        super().__init__(name, description, legacy_script_path)

    def get_agent_type(self) -> AgentType:
        """获取对应的 Agent 类型"""
        return AgentType.REWRITE

    def create_parser(self) -> argparse.ArgumentParser:
        """创建兼容旧版的参数解析器"""
        parser = self.create_legacy_parser()

        # 添加新架构支持的参数
        parser.add_argument(
            '--strategy',
            help='改写策略名称'
        )

        parser.add_argument(
            '--temperature',
            type=float,
            help='AI 生成温度'
        )

        parser.add_argument(
            '--timeout',
            type=int,
            help='操作超时时间（秒）'
        )

        parser.add_argument(
            '--output-dir',
            help='输出目录'
        )

        parser.add_argument(
            '--verbose',
            action='store_true',
            help='显示详细信息'
        )

        return parser

    def get_agent_from_legacy_config(self) -> RewriteAgent:
        """从旧版配置获取 Rewrite Agent"""
        from ...config import config

        agent_config = AgentConfig(
            agent_id="legacy_rewrite",
            agent_type=AgentType.REWRITE,
            provider_name=config.provider,
            model_name=config.openai_model if config.provider == "openai" else config.ollama_model,
            strategy_name=None,  # 使用默认策略
            capabilities=[AgentCapability.REWRITE]
        )

        return RewriteAgent(agent_config)