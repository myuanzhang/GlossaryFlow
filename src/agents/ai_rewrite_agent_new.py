"""
AI Rewrite Agent - 重构版本，支持策略模式

基于 Stage 01、02 结构的纯 AI 改写代理，支持可插拔的改写策略。
"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import config
from ..translator.base import provider_registry
from ..translator import providers  # 触发注册
from .strategies import RewriteStrategyFactory, RewriteContext, RewriteResult

logger = logging.getLogger(__name__)


class AIRewriteAgent:
    """
    AI 改写代理 - 重构版本

    支持策略模式的文档改写代理，保持向后兼容性。
    """

    def __init__(self,
                 output_dir: str = "rewritten_docs",
                 strategy_name: Optional[str] = None,
                 strategy_config: Optional[Dict] = None):
        """
        初始化 AI 改写代理

        Args:
            output_dir: 改写文档输出目录
            strategy_name: 改写策略名称（None表示使用默认策略）
            strategy_config: 策略配置
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 确保 providers 已注册
        from ..translator import providers  # 触发注册

        # 获取配置的 provider
        self.provider = provider_registry.get_or_create(
            config.provider,
            config.openai_model if config.provider == "openai" else config.ollama_model
        )

        if not self.provider.is_configured():
            raise ValueError(f"LLM provider {config.provider} is not properly configured")

        # 选择改写策略
        self.strategy_name = strategy_name or getattr(config, 'rewrite_strategy', 'line_by_line')
        self.strategy_config = strategy_config or self._get_default_strategy_config()

        self.strategy = RewriteStrategyFactory.create_strategy(
            self.strategy_name,
            self.provider,
            self.strategy_config
        )

        logger.info(f"Initialized AIRewriteAgent with strategy: {self.strategy_name}")

    def _get_default_strategy_config(self) -> Dict:
        """获取默认策略配置"""
        return {
            'temperature': getattr(config, 'rewrite_temperature', 0.3),
            'timeout_seconds': getattr(config, 'rewrite_timeout_seconds', 30),
        }

    def rewrite_and_save(self,
                        source_markdown: str,
                        document_context: Optional[Dict] = None,
                        strategy_name: Optional[str] = None) -> Dict:
        """
        改写并保存文档

        Args:
            source_markdown: 原始 Markdown 内容
            document_context: 文档上下文
            strategy_name: 临时策略名称（覆盖初始化时的策略）

        Returns:
            Dict: 包含改写结果和保存信息的字典
        """
        # 创建改写上下文
        context = self._build_rewrite_context(document_context or {})

        # 如果指定了临时策略，切换策略
        strategy = self.strategy
        if strategy_name and strategy_name != self.strategy_name:
            strategy = RewriteStrategyFactory.create_strategy(strategy_name, self.provider, self.strategy_config)
            logger.info(f"Using temporary strategy: {strategy_name}")

        # 执行改写
        result = strategy.rewrite(source_markdown, context)

        # 保存结果
        save_info = self._save_result(result)

        return {
            "rewritten_content": result.rewritten_markdown,
            "metadata": self._convert_result_to_metadata(result),
            "save_info": save_info,
            "strategy_used": result.strategy_name
        }

    def _build_rewrite_context(self, document_context: Dict) -> RewriteContext:
        """构建改写上下文"""
        return RewriteContext(
            document_intent=document_context.get("intent"),
            target_audience=document_context.get("target_audience"),
            tone=document_context.get("tone"),
            domain=document_context.get("domain"),
            temperature=self.strategy_config.get("temperature", 0.3),
            timeout_seconds=self.strategy_config.get("timeout_seconds", 30),
            preserve_code_blocks=True,
            preserve_formatting=True
        )

    def _save_result(self, result: RewriteResult) -> Dict:
        """保存改写结果"""
        # 创建文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = str(uuid.uuid4())[:8]

        doc_filename = f"rewritten_{timestamp}_{job_id}_{result.strategy_name}.md"
        meta_filename = f"{doc_filename}.metadata.json"

        # 保存文档
        doc_path = self.output_dir / doc_filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(result.rewritten_markdown)

        # 保存元数据
        metadata = self._convert_result_to_metadata(result)
        meta_path = self.output_dir / meta_filename
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            "document_path": str(doc_path),
            "metadata_path": str(meta_path),
            "output_directory": str(self.output_dir)
        }

    def _convert_result_to_metadata(self, result: RewriteResult) -> Dict:
        """将 RewriteResult 转换为元数据格式"""
        return {
            "job_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "strategy_used": result.strategy_name,
            "provider_used": result.metadata.get("provider_used", "unknown"),
            "model_used": config.openai_model if config.provider == "openai" else config.ollama_model,
            "rewrite_applied": result.rewrite_applied,
            "units_processed": result.units_processed,
            "units_rewritten": result.units_rewritten,
            "rewrite_rate": result.rewrite_rate,
            "processing_time_ms": result.processing_time_ms,
            "warnings": result.warnings,
            "strategy_description": result.metadata.get("strategy_description", ""),
            "context": result.metadata.get("context", {})
        }

    def get_available_strategies(self) -> List[Dict]:
        """获取可用的改写策略列表"""
        return RewriteStrategyFactory.list_strategies_with_info()

    def get_current_strategy_info(self) -> Dict:
        """获取当前策略信息"""
        return RewriteStrategyFactory.get_strategy_info(self.strategy_name) or {}

    def switch_strategy(self, strategy_name: str, strategy_config: Optional[Dict] = None):
        """切换改写策略"""
        self.strategy_name = strategy_name
        if strategy_config:
            self.strategy_config = strategy_config

        self.strategy = RewriteStrategyFactory.create_strategy(
            strategy_name,
            self.provider,
            self.strategy_config
        )
        logger.info(f"Switched to strategy: {strategy_name}")

    # 向后兼容的接口
    def rewrite(self, rewrite_input) -> 'AIRewriteOutput':
        """
        向后兼容的改写接口

        Args:
            rewrite_input: AIRewriteInput 实例

        Returns:
            AIRewriteOutput 实例
        """
        # 转换为新的接口调用
        result = self.strategy.rewrite(
            rewrite_input.source_markdown,
            self._build_rewrite_context(rewrite_input.document_context)
        )

        return AIRewriteOutput(result.rewritten_markdown, self._convert_result_to_metadata(result))


class AIRewriteInput:
    """向后兼容的输入结构"""

    def __init__(self, source_markdown: str, document_context: Optional[Dict] = None):
        self.source_markdown = source_markdown
        self.document_context = document_context or {}


class AIRewriteOutput:
    """向后兼容的输出结构"""

    def __init__(self, rewritten_markdown: str, metadata: Dict):
        self.rewritten_markdown = rewritten_markdown
        self.metadata = metadata