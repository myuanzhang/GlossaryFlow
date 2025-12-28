"""
Translation-Oriented Prompt Manager

Provides prompt management for translation-oriented rewrite strategy.
"""

from typing import Dict, Any, List
from ..manager import PromptManager


class TranslationOrientedPromptManager(PromptManager):
    """
    Translation-oriented rewrite prompt manager.

    Manages prompts for optimizing Chinese documents for better machine translation.
    """

    def __init__(self):
        super().__init__()

    def build_rewrite_prompt(self, unit_text: str, context: Dict[str, Any]) -> str:
        """
        Build a rewrite prompt for a given text unit.

        Args:
            unit_text: The text to rewrite
            context: Context information including document type, etc.

        Returns:
            Formatted prompt string
        """
        document_type = context.get('document_type', '通用文档')

        prompt = f"""你是一个专业的中文文档改写专家，专门优化中文文档以提高机器翻译质量。

任务：将以下{document_type}中的中文内容改写为更适合机器翻译的英文表达方式。

改写原则：
1. 简化复杂句子结构，将长句分解为短句
2. 消除中文特有的表达习惯和冗余词汇
3. 明确指代关系，避免歧义
4. 保持原文的核心意思和专业术语
5. 使用更直接、简洁的表达方式
6. 确保改写后的内容符合英文表达习惯

特别注意：
- 保留所有专业术语不翻译
- 保持 Markdown 格式不变
- 不要添加解释性内容
- 改写后的文本应该像是中文母语者写的，但表达更清晰

原文内容：
{unit_text}

请直接输出改写后的中文内容，不要包含任何解释。"""

        return prompt

    def build_validation_prompt(self, original: str, rewritten: str) -> str:
        """
        Build a validation prompt to check rewrite quality.

        Args:
            original: Original text
            rewritten: Rewritten text

        Returns:
            Validation prompt string
        """
        prompt = f"""请评估以下改写质量：

原文：{original}

改写后：{rewritten}

评估标准：
1. 是否保持了原文的核心意思？(是/否)
2. 是否简化了句子结构？(是/否)
3. 是否消除了中文特有的冗余表达？(是/否)
4. 是否提高了翻译友好度？(是/否)
5. 是否保持了专业术语不变？(是/否)

请逐项评估并最后给出总体评分(1-10分)：
"""

        return prompt

    def get_available_templates(self) -> List[str]:
        """Get list of available prompt templates."""
        return [
            'rewrite_prompt',
            'validation_prompt',
            'context_analysis'
        ]

    def render_template(self, template_name: str, **kwargs) -> str:
        """
        Render a prompt template with given context.

        Args:
            template_name: Name of the template
            **kwargs: Template variables

        Returns:
            Rendered prompt string
        """
        if template_name == 'rewrite_prompt':
            return self.build_rewrite_prompt(kwargs.get('unit_text', ''), kwargs.get('context', {}))
        elif template_name == 'validation_prompt':
            return self.build_validation_prompt(kwargs.get('original', ''), kwargs.get('rewritten', ''))
        else:
            return self.build_rewrite_prompt('', {})