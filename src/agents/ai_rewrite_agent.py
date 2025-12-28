"""
AI Rewrite Agent - 基于 Stage 01、02 结构的纯 AI 改写代理

使用 .env 中配置的 LLM 进行文档改写，保持与项目架构的一致性。
"""

import json
import uuid
import logging
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import config
from translator.base import provider_registry
from translator import providers  # 触发注册

logger = logging.getLogger(__name__)


class AIRewriteOutput:
    """AI 改写输出结构"""

    def __init__(self, rewritten_markdown: str, metadata: Dict):
        self.rewritten_markdown = rewritten_markdown
        self.metadata = metadata


class AIRewriteInput:
    """AI 改写输入结构"""

    def __init__(self, source_markdown: str, document_context: Optional[Dict] = None):
        self.source_markdown = source_markdown
        self.document_context = document_context or {}


class AIRewriteAgent:
    """
    AI 改写代理

    基于项目现有架构，使用 .env 配置的 LLM 进行文档改写。
    """

    def __init__(self, output_dir: str = "rewritten_docs"):
        """
        初始化 AI 改写代理

        Args:
            output_dir: 改写文档输出目录
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

    def rewrite(self, rewrite_input: AIRewriteInput) -> AIRewriteOutput:
        """
        改写文档

        Args:
            rewrite_input: 改写输入

        Returns:
            AIRewriteOutput: 改写结果
        """
        logger.info(f"Starting AI rewrite for document of length {len(rewrite_input.source_markdown)}")

        # 解析文档为句子
        sentences = self._parse_sentences(rewrite_input.source_markdown)
        logger.info(f"Parsed {len(sentences)} sentences for rewriting")

        # 改写句子
        rewritten_sentences = []
        rewritten_count = 0
        warnings = []

        for i, sentence in enumerate(sentences, 1):
            try:
                # 显示进度（每10个句子显示一次）
                if i % 10 == 1:
                    logger.info(f"Processing sentence {i}/{len(sentences)}")

                # 跳过空行
                if not sentence.strip():
                    rewritten_sentences.append(sentence)
                    continue

                # 跳过代码内容
                if self._is_code_content(sentence, rewrite_input.source_markdown):
                    rewritten_sentences.append(sentence)
                    continue

                # AI 改写句子
                rewritten = self._rewrite_sentence_with_ai(sentence, rewrite_input.document_context)

                # 验证改写结果
                if self._validate_rewrite(sentence, rewritten):
                    rewritten_sentences.append(rewritten)
                    if rewritten != sentence:
                        rewritten_count += 1
                        logger.debug(f"Sentence {i} rewritten: '{sentence}' -> '{rewritten}'")
                else:
                    rewritten_sentences.append(sentence)
                    warnings.append(f"Sentence {i}: Rewrite validation failed, using original")

            except Exception as e:
                logger.warning(f"Failed to rewrite sentence {i}: {e}")
                rewritten_sentences.append(sentence)
                warnings.append(f"Sentence {i}: Rewrite failed, using original")

        # 重构文档
        rewritten_markdown = self._reconstruct_document(
            rewrite_input.source_markdown,
            sentences,
            rewritten_sentences
        )

        # 创建元数据
        metadata = self._create_metadata(len(sentences), rewritten_count, warnings)

        logger.info(f"AI rewrite completed: {rewritten_count}/{len(sentences)} sentences rewritten")

        return AIRewriteOutput(rewritten_markdown, metadata)

    def rewrite_and_save(self, source_markdown: str, document_context: Optional[Dict] = None) -> Dict:
        """
        改写并保存文档

        Args:
            source_markdown: 原始 Markdown 内容
            document_context: 文档上下文

        Returns:
            Dict: 包含改写结果和保存信息的字典
        """
        # 创建改写输入
        rewrite_input = AIRewriteInput(source_markdown, document_context)

        # 执行改写
        result = self.rewrite(rewrite_input)

        # 保存结果
        save_info = self._save_result(result.rewritten_markdown, result.metadata)

        return {
            "rewritten_content": result.rewritten_markdown,
            "metadata": result.metadata,
            "save_info": save_info
        }

    def _rewrite_sentence_with_ai(self, sentence: str, context: Dict) -> str:
        """使用 AI 改写单个句子"""

        # 构建改写提示
        prompt = self._build_rewrite_prompt(sentence, context)

        # 调用 AI provider，添加超时处理
        try:
            logger.debug(f"Rewriting sentence: {sentence[:50]}...")
            logger.debug(f"Using provider: {self.provider.get_name()}")

            # 使用 signal 设置超时（30秒）
            def timeout_handler(signum, frame):
                raise TimeoutError("AI provider call timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30秒超时

            try:
                response = self.provider.translate(prompt, source_lang="zh", target_lang="zh")
                signal.alarm(0)  # 取消超时

                logger.debug(f"Provider response received: {response[:100] if response else 'empty'}...")

                # 提取改写结果
                rewritten = self._extract_rewritten_sentence(response, sentence)

                logger.debug(f"Extracted rewritten sentence: {rewritten[:50] if rewritten != sentence else 'unchanged'}...")

                return rewritten

            except TimeoutError as e:
                logger.error(f"AI provider timeout: {e}")
                return sentence

        except Exception as e:
            logger.error(f"AI rewrite failed: {e}")
            logger.error(f"Provider used: {self.provider.get_name()}")
            logger.error(f"Sentence: {sentence}")
            return sentence
        finally:
            signal.alarm(0)  # 确保取消超时

    def _build_rewrite_prompt(self, sentence: str, context: Dict) -> str:
        """构建改写提示"""

        # 基础改写提示
        prompt = f"""请改写以下中文句子，使其表达更加清晰、专业和优雅。

改写要求：
1. 保持原意完全不变
2. 优化表达方式，使其更专业
3. 提高语言的流畅性和精确性
4. 保持语句结构完整
5. 只返回改写后的句子，不要解释

原句：{sentence}

改写："""

        # 添加上下文信息
        if context:
            context_info = []
            if "intent" in context:
                context_info.append(f"文档意图: {context['intent']}")
            if "target_audience" in context:
                context_info.append(f"目标读者: {context['target_audience']}")
            if "tone" in context:
                context_info.append(f"语气风格: {context['tone']}")
            if "domain" in context:
                context_info.append(f"领域: {context['domain']}")

            if context_info:
                context_prompt = "\n\n上下文信息：\n" + "\n".join(f"- {info}" for info in context_info)
                prompt = prompt + context_prompt

        return prompt

    def _extract_rewritten_sentence(self, response: str, original: str) -> str:
        """从 AI 响应中提取改写后的句子"""

        # 清理响应
        rewritten = response.strip()

        # 移除可能的解释
        if "改写：" in rewritten:
            rewritten = rewritten.split("改写：")[-1].strip()
        elif "Rewrite:" in rewritten:
            rewritten = rewritten.split("Rewrite:")[-1].strip()

        # 如果响应太长，可能包含解释，尝试提取第一行
        if len(rewritten) > len(original) * 2:
            lines = rewritten.split('\n')
            if lines:
                rewritten = lines[0].strip()

        # 如果提取的句子为空或太短，返回原句
        if not rewritten or len(rewritten) < len(original) * 0.3:
            return original

        return rewritten

    def _validate_rewrite(self, original: str, rewritten: str) -> bool:
        """验证改写结果"""

        if not rewritten or len(rewritten) < len(original) * 0.3:
            return False

        if len(rewritten) > len(original) * 3:
            return False

        return True

    def _parse_sentences(self, text: str) -> List[str]:
        """解析文档为句子列表"""

        sentences = []
        lines = text.split('\n')
        current_pos = 0

        for line in lines:
            if not line.strip():
                # 空行
                current_pos += len(line) + 1
                sentences.append('')
                continue

            # 跳过代码块
            if line.strip().startswith('```'):
                sentences.append(line)
                continue

            # 简单的句子分割：按行处理
            # 这里可以进一步优化为更智能的句子分割
            sentences.append(line)
            current_pos += len(line) + 1

        return sentences

    def _is_code_content(self, text: str, full_text: str) -> bool:
        """判断是否为代码内容"""

        # 检查是否在代码块中
        lines = full_text.split('\n')
        current_line_index = 0

        for i, line in enumerate(lines):
            if text in line:
                current_line_index = i
                break

        # 检查前后是否为代码块
        in_code_block = False
        for line in lines[:current_line_index]:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

        if in_code_block:
            return True

        # 检查是否为代码行（简单启发式）
        text_stripped = text.strip()
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'function', 'var ', 'let ', 'const ',
            'if ', 'for ', 'while ', 'return ', 'print(', 'console.log',
            '=>', '&&', '||', '++', '--', '/*', '*/', '//', '#include', '#define'
        ]

        for indicator in code_indicators:
            if indicator in text_stripped:
                return True

        return False

    def _reconstruct_document(self, original: str, original_sentences: List[str], rewritten_sentences: List[str]) -> str:
        """重构文档"""

        # 简单的行级别重构
        return '\n'.join(rewritten_sentences)

    def _create_metadata(self, sentences_processed: int, sentences_rewritten: int, warnings: List[str]) -> Dict:
        """创建元数据"""

        return {
            "job_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "provider_used": config.provider,
            "model_used": config.openai_model if config.provider == "openai" else config.ollama_model,
            "rewrite_applied": sentences_rewritten > 0,
            "sentences_processed": sentences_processed,
            "sentences_rewritten": sentences_rewritten,
            "rewrite_rate": f"{(sentences_rewritten / sentences_processed * 100):.1f}%" if sentences_processed > 0 else "0%",
            "warnings": warnings
        }

    def _save_result(self, content: str, metadata: Dict) -> Dict:
        """保存改写结果"""

        # 创建文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = metadata["job_id"]

        doc_filename = f"rewritten_{timestamp}_{job_id}.md"
        meta_filename = f"{doc_filename}.metadata.json"

        # 保存文档
        doc_path = self.output_dir / doc_filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 保存元数据
        meta_path = self.output_dir / meta_filename
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            "document_path": str(doc_path),
            "metadata_path": str(meta_path),
            "output_directory": str(self.output_dir)
        }