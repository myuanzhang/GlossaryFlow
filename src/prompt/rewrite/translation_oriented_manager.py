"""
Translation-Oriented Prompt Manager

Manages dynamic prompt building for translation-oriented rewriting.
"""

import os
from typing import Dict, Optional
from pathlib import Path

from ...agents.strategies.base import RewriteContext


class TranslationOrientedPromptManager:
    """
    Manages prompts for translation-oriented rewriting strategy.
    """

    def __init__(self):
        """Initialize prompt manager with template path."""
        self.template_path = Path(__file__).parent.parent.parent.parent / "prompts" / "rewrite" / "translation_oriented.md"
        self._cached_template = None

    def _load_template(self) -> str:
        """Load prompt template from file."""
        if self._cached_template is None:
            try:
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    self._cached_template = f.read()
            except FileNotFoundError:
                # Fallback to embedded template if file not found
                self._cached_template = self._get_fallback_template()
        return self._cached_template

    def _get_fallback_template(self) -> str:
        """Get fallback template when file is not available."""
        return """请将以下中文内容改写为更适合机器翻译成英文的格式。

改写原则：
1. 句子简化：拆分复杂长句为简单短句
2. 主语明确：每个句子都有明确的主语
3. 逻辑清晰：显式表达因果关系、条件关系等逻辑连接
4. 术语稳定：保持专业术语的一致性和准确性
5. 去除修辞：减少中文特有的修辞表达、成语、俗语
6. 结构保留：完全保持 Markdown 格式和结构

常见优化规则：
- 事半功倍 → 显著提高效率
- 面面俱到 → 全面覆盖
- 一石二鸟 → 同时支持两种功能
- 总而言之 → 总结来说
- 深受用户喜爱 → 获得用户广泛认可
- 海量数据 → 大量数据

约束条件：
- 只返回改写后的文本，不添加任何解释或元评论
- 完全保持原意，不得改变或添加信息
- 100% 保持 Markdown 格式和结构
- 代码块、内联代码、技术术语完全不变

原文：
{content}

改写后："""

    def build_prompt(self,
                     content: str,
                     context: Optional[RewriteContext] = None,
                     section_type: Optional[str] = None,
                     surrounding_context: Optional[str] = None) -> str:
        """
        Build dynamic prompt based on context.

        Args:
            content: The content to rewrite
            context: Rewrite context with metadata
            section_type: Type of section (header, paragraph, list, etc.)
            surrounding_context: Surrounding text for consistency

        Returns:
            Complete prompt string
        """
        template = self._load_template()

        # Extract the core instruction part
        if "# Task" in template:
            # Extract from Task section to Execution Steps
            task_start = template.find("# Task")
            execution_start = template.find("## Execution Steps")

            if execution_start > task_start:
                core_prompt = template[task_start:execution_start]
            else:
                core_prompt = template[task_start:]
        else:
            # Use fallback simple template
            core_prompt = self._get_fallback_template()

        # Add context information
        context_section = ""
        if context:
            context_parts = []

            if context.document_intent:
                context_parts.append(f"文档意图：{context.document_intent}")

            if context.target_audience:
                context_parts.append(f"目标读者：{context.target_audience}")

            if context.domain:
                context_parts.append(f"专业领域：{context.domain}")

            if context.tone:
                context_parts.append(f"语气风格：{context.tone}")

            if context_parts:
                context_section = f"\n\n上下文信息：\n" + "\n".join(f"- {part}" for part in context_parts)

        # Add section type information
        section_info = ""
        if section_type:
            section_info = f"\n\n内容类型：{section_type}"

        # Add surrounding context if provided
        surrounding_info = ""
        if surrounding_context:
            # Only include relevant surrounding context (last 100 chars)
            if len(surrounding_context) > 100:
                surrounding_context = surrounding_context[-100:]
            surrounding_info = f"\n\n前后文参考：{surrounding_context}"

        # Build final prompt
        # For simplicity, we'll use the fallback template with context
        final_prompt = self._get_fallback_template()

        # Replace placeholders first
        final_prompt = final_prompt.replace("{content}", content)

        # Add context after the content but before "改写后："
        if context_section or section_info or surrounding_info:
            context_addition = context_section + section_info + surrounding_info
            # Insert context between content and "改写后："
            final_prompt = final_prompt.replace("改写后：", f"\n{context_addition}\n改写后：")

        return final_prompt

    def build_simple_prompt(self, content: str) -> str:
        """
        Build simple prompt for quick rewriting.

        Args:
            content: Content to rewrite

        Returns:
            Simple prompt string
        """
        return f"""请将以下中文内容改写为更适合机器翻译成英文的格式。

改写要求：
1. 简化复杂句子，确保主语明确
2. 去除中文特有的修辞表达（如成语、俗语）
3. 保持原意不变，保持 Markdown 格式完整
4. 代码块、链接等技术内容完全不变
5. 只返回改写后的文本，不添加解释

常见优化：
- 事半功倍 → 显著提高效率
- 面面俱到 → 全面覆盖
- 一石二鸟 → 同时支持两种功能
- 总而言之 → 总结来说
- 海量数据 → 大量数据

原文：
{content}

改写后："""

    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate that prompt is properly formed.

        Args:
            prompt: Prompt to validate

        Returns:
            True if valid, False otherwise
        """
        # Check for required elements
        required_elements = [
            "改写",
            "机器翻译",
            "Markdown"
        ]

        for element in required_elements:
            if element not in prompt:
                return False

        return True

    def get_prompt_stats(self) -> Dict[str, any]:
        """
        Get statistics about the prompt template.

        Returns:
            Dictionary with prompt statistics
        """
        template = self._load_template()

        return {
            "template_path": str(self.template_path),
            "template_exists": os.path.exists(self.template_path),
            "template_length": len(template),
            "template_lines": len(template.split('\n')),
            "has_rules": "改写原则" in template,
            "has_examples": "Examples" in template,
            "has_constraints": "Constraints" in template
        }