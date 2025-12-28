"""
CLI Base Classes

定义 CLI 层的基础类和接口，实现 CLI 与 Agent 的解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import argparse
import sys
from pathlib import Path

from agents.base import BaseAgent
from ..core.job import Job
from ..core.types import AgentType, DocumentContext


class CLICommand(ABC):
    """
    CLI 命令基类

    定义了 CLI 命令的统一接口和通用行为。
    """

    def __init__(self, name: str, description: str):
        """
        初始化 CLI 命令

        Args:
            name: 命令名称
            description: 命令描述
        """
        self.name = name
        self.description = description
        self.agent: Optional[BaseAgent] = None

    @abstractmethod
    def create_parser(self) -> argparse.ArgumentParser:
        """
        创建命令行参数解析器

        Returns:
            参数解析器
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> AgentType:
        """
        获取对应的 Agent 类型

        Returns:
            Agent 类型
        """
        pass

    def setup_agent(self, agent: BaseAgent) -> None:
        """
        设置 Agent

        Args:
            agent: Agent 实例
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError("agent must be an instance of BaseAgent")

        self.agent = agent

    def create_job_from_args(self, args: argparse.Namespace) -> Job:
        """
        从命令行参数创建作业

        Args:
            args: 解析后的命令行参数

        Returns:
            创建的作业
        """
        # 读取输入文件
        input_path = Path(args.input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建文档上下文
        context = DocumentContext(
            intent=getattr(args, 'intent', '技术文档'),
            target_audience=getattr(args, 'audience', '技术用户'),
            tone=getattr(args, 'tone', 'professional'),
            domain=getattr(args, 'domain', '根据内容推断'),
            source_lang=getattr(args, 'source_lang', 'zh'),
            target_lang=getattr(args, 'target_lang', 'en')
        )

        # 创建作业
        job = Job.create_new(
            agent_type=self.get_agent_type(),
            content=content,
            context=context,
            strategy_name=getattr(args, 'strategy', None),
            temperature=getattr(args, 'temperature', None),
            timeout=getattr(args, 'timeout', None)
        )

        return job

    def save_result(self, result: Dict[str, Any], output_path: str) -> None:
        """
        保存处理结果

        Args:
            result: 处理结果
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 提取结果内容
        if result.get('result') and result['result'].get('content'):
            content = result['result']['content']
        else:
            content = result.get('content', '')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def format_output(self, result: Dict[str, Any], verbose: bool = False) -> None:
        """
        格式化输出结果

        Args:
            result: 处理结果
            verbose: 是否显示详细信息
        """
        status = result.get('status', 'unknown')
        job_id = result.get('job_id', 'unknown')

        # 基本信息
        print(f"✅ {'处理完成' if status == 'completed' else '处理失败'}")
        print(f"📋 作业ID: {job_id}")

        if verbose:
            # Agent 信息
            agent_info = result.get('agent_info', {})
            if agent_info:
                print(f"🤖 使用的 Agent: {agent_info.get('agent_id', 'unknown')}")
                print(f"🌐 Provider: {agent_info.get('provider', 'unknown')}")
                print(f"🧠 模型: {agent_info.get('model', 'unknown')}")
                if agent_info.get('strategy'):
                    print(f"📝 策略: {agent_info.get('strategy')}")

            # 统计信息
            if result.get('result') and result['result'].get('stats'):
                stats = result['result']['stats']
                print(f"📊 处理统计:")
                print(f"   - 处理单元数: {stats.get('units_processed', 0)}")
                print(f"   - 改写单元数: {stats.get('units_rewritten', 0)}")
                print(f"   - 改写率: {stats.get('rewrite_rate', 0):.1%}")
                print(f"   - 处理时间: {stats.get('processing_time_ms', 0):.1f}ms")

            # 警告信息
            if result.get('result') and result['result'].get('warnings'):
                warnings = result['result']['warnings']
                if warnings:
                    print(f"⚠️  警告 ({len(warnings)} 个):")
                    for warning in warnings[:3]:  # 只显示前3个
                        print(f"   - {warning}")
                    if len(warnings) > 3:
                        print(f"   - ... 还有 {len(warnings) - 3} 个警告")

        # 错误信息
        if result.get('error'):
            print(f"❌ 错误: {result['error']}")

    def execute(self, args: List[str] = None) -> int:
        """
        执行命令

        Args:
            args: 命令行参数列表

        Returns:
            退出码
        """
        if not self.agent:
            print("❌ 错误: Agent 未设置", file=sys.stderr)
            return 1

        try:
            # 解析参数
            parser = self.create_parser()
            parsed_args = parser.parse_args(args)

            # 创建作业
            job = self.create_job_from_args(parsed_args)

            # 执行处理
            result = self.agent.execute(job.to_dict())

            # 保存结果
            if hasattr(parsed_args, 'output_file') and parsed_args.output_file:
                self.save_result(result, parsed_args.output_file)
                print(f"💾 结果已保存到: {parsed_args.output_file}")

            # 显示输出
            verbose = getattr(parsed_args, 'verbose', False)
            self.format_output(result, verbose)

            # 返回退出码
            return 0 if result.get('status') == 'completed' else 1

        except KeyboardInterrupt:
            print("\n❌ 用户中断", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"❌ 错误: {str(e)}", file=sys.stderr)
            if getattr(parsed_args, 'debug', False):
                import traceback
                traceback.print_exc()
            return 1

    def __repr__(self) -> str:
        return f"<CLICommand(name={self.name})>"


class BackwardCompatibleCommand(CLICommand):
    """
    向后兼容的命令基类

    为现有的 CLI 脚本提供向后兼容性。
    """

    def __init__(self, name: str, description: str, legacy_script_path: str):
        """
        初始化向后兼容命令

        Args:
            name: 命令名称
            description: 命令描述
            legacy_script_path: 原有脚本路径
        """
        super().__init__(name, description)
        self.legacy_script_path = legacy_script_path

    def create_legacy_parser(self) -> argparse.ArgumentParser:
        """
        创建兼容旧版脚本的解析器

        Returns:
            参数解析器
        """
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # 基本参数
        parser.add_argument(
            'input_file',
            help='输入 Markdown 文件路径'
        )
        parser.add_argument(
            'output_file',
            help='输出 Markdown 文件路径'
        )

        return parser

    def get_agent_from_legacy_config(self) -> BaseAgent:
        """
        从旧版配置获取 Agent

        子类需要实现此方法来创建对应的 Agent。

        Returns:
            Agent 实例
        """
        raise NotImplementedError("Subclasses must implement get_agent_from_legacy_config")

    def execute_legacy(self, args: List[str] = None) -> int:
        """
        执行向后兼容命令

        Args:
            args: 命令行参数列表

        Returns:
            退出码
        """
        try:
            # 尝试使用新的 Agent 架构
            agent = self.get_agent_from_legacy_config()
            self.setup_agent(agent)
            return self.execute(args)

        except Exception as e:
            # 如果新架构失败，回退到旧版脚本
            print(f"⚠️  新架构执行失败，回退到旧版脚本: {str(e)}")
            import subprocess
            return subprocess.call([sys.executable, self.legacy_script_path] + (args or []))