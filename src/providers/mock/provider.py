"""
Mock Provider Implementation

Mock LLM Provider 实现用于测试和开发，不依赖外部 API。
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from providers.base import BaseProvider, ProviderConfig, ModelInfo, ModelCapability
from core.types import ProviderType


class MockProvider(BaseProvider):
    """Mock LLM Provider - 用于测试和开发"""

    def __init__(self, config: ProviderConfig):
        """
        初始化 Mock Provider

        Args:
            config: Provider 配置
        """
        super().__init__(config)
        self.provider_name = "mock"
        self.default_model = "mock-gpt-3.5-turbo"

    def is_configured(self) -> bool:
        """
        Mock Provider 总是已配置

        Returns:
            True
        """
        return True

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        return [
            "mock-gpt-3.5-turbo",
            "mock-gpt-4",
            "mock-claude-3",
            "mock-gemini-pro",
            "mock-llama2",
            "mock-custom-model"
        ]

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        获取模型信息

        Args:
            model_name: 模型名称

        Returns:
            模型信息或 None
        """
        if model_name not in self.get_available_models():
            return None

        capabilities = [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.TRANSLATION,
            ModelCapability.MULTILINGUAL
        ]

        # 为特定模型添加额外能力
        if "gpt-4" in model_name:
            capabilities.append(ModelCapability.CODE_GENERATION)
            capabilities.append(ModelCapability.FUNCTION_CALLING)

        return ModelInfo(
            name=model_name,
            provider=ProviderType.MOCK,
            capabilities=capabilities,
            max_tokens=4096,
            supports_streaming=True,
            supports_function_calling="gpt-4" in model_name,
            pricing={"input": 0.0, "output": 0.0}  # 免费模拟
        )

    async def generate_async(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        异步生成文本

        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        # 模拟处理时间
        await asyncio.sleep(0.1)

        # 根据模型类型生成不同的模拟响应
        if "gpt" in model.lower():
            return self._generate_gpt_style_response(prompt)
        elif "claude" in model.lower():
            return self._generate_claude_style_response(prompt)
        elif "gemini" in model.lower():
            return self._generate_gemini_style_response(prompt)
        else:
            return self._generate_generic_response(prompt)

    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        同步生成文本

        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        import time
        time.sleep(0.1)  # 模拟处理时间

        if "gpt" in model.lower():
            return self._generate_gpt_style_response(prompt)
        elif "claude" in model.lower():
            return self._generate_claude_style_response(prompt)
        elif "gemini" in model.lower():
            return self._generate_gemini_style_response(prompt)
        else:
            return self._generate_generic_response(prompt)

    def translate(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            翻译后的文本
        """
        if not text.strip():
            return text

        # 如果源语言和目标语言相同，可能是改写请求
        if source_lang == target_lang:
            return self._rewrite_content(text)

        # 真正的翻译请求
        if target_lang == "en":
            return f"[MOCK Translation to English: {len(text)} chars from {model or 'default model'}]"
        elif target_lang == "zh":
            return f"[MOCK 翻译为中文：{len(text)} 字符，使用模型 {model or '默认模型'}]"
        else:
            return f"[MOCK Translation to {target_lang}: {len(text)} chars from {model or 'default model'}]"

    def _generate_gpt_style_response(self, prompt: str) -> str:
        """生成 GPT 风格的响应"""
        if "翻译" in prompt or "translate" in prompt:
            return "This is a mock GPT-style translation response."

        if "改写" in prompt or "rewrite" in prompt:
            return "这是一个模拟的 GPT 风格改写响应。内容已经根据要求进行了优化。"

        return f"[Mock GPT Response] Based on your prompt: '{prompt[:50]}...', here's a generated response."

    def _generate_claude_style_response(self, prompt: str) -> str:
        """生成 Claude 风格的响应"""
        if "翻译" in prompt or "translate" in prompt:
            return "This is a mock Claude-style translation response."

        if "改写" in prompt or "rewrite" in prompt:
            return "这是一个模拟的 Claude 风格改写响应。我理解您需要对内容进行优化，以下是改写后的版本。"

        return f"[Mock Claude Response] I'll help you with: '{prompt[:50]}...'"

    def _generate_gemini_style_response(self, prompt: str) -> str:
        """生成 Gemini 风格的响应"""
        if "翻译" in prompt or "translate" in prompt:
            return "This is a mock Gemini-style translation response."

        if "改写" in prompt or "rewrite" in prompt:
            return "这是一个模拟的 Gemini 风格改写响应。我已经理解了您的需求并准备好了相应的内容。"

        return f"[Mock Gemini Response] Based on your input about: '{prompt[:50]}...'"

    def _generate_generic_response(self, str) -> str:
        """生成通用响应"""
        return f"[Mock Response] Generated text for: {str[:50]}..."

    def _rewrite_content(self, text: str) -> str:
        """
        改写内容（基于现有的 mock provider 逻辑）

        Args:
            text: 待改写文本

        Returns:
            改写后的文本
        """
        # 处理翻译导向的提示格式
        if text.endswith("改写后："):
            content_section = text[:-4]  # Remove "改写后："

            # 查找 "原文：" 标记
            if "原文：" in content_section:
                lines = content_section.split('\n')
                original_content = ""
                found_original = False
                for line in lines:
                    if "原文：" in line:
                        original_content = line.split("原文：", 1)[-1].strip()
                        found_original = True
                    elif found_original and line.strip() and not line.strip().startswith('改写后：'):
                        original_content += line.strip()
                    elif line.strip().startswith('改写后：'):
                        break
            else:
                # 尝试找到 "改写后：" 前的最后一行实质性内容
                lines = content_section.split('\n')
                content_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    if (line_stripped and
                        not any(marker in line_stripped for marker in [
                            '改写原则：', '约束条件：', '常见优化规则：', '上下文信息：',
                            '文档意图：', '目标读者：', '专业领域：', '语气风格：',
                            '内容类型：', '前后文参考：', '原文：'
                        ]) and
                        not line_stripped.endswith('：') and
                        len(line_stripped) > 5):
                        content_lines.append(line_stripped)

                original_content = content_lines[-1] if content_lines else ""

            if original_content:
                return self._apply_rewrite_rules(original_content)
            else:
                return "改写后的内容"

        # 处理更适合机器翻译的格式
        if "更适合机器翻译" in text:
            return self._apply_translation_optimization(text)

        # 处理简单的改写请求
        return self._apply_simple_rewrite(text)

    def _apply_rewrite_rules(self, original_content: str) -> str:
        """应用改写规则"""
        # 基本的改写规则
        rewrite_rules = {
            "这是一个非常好的文档": "这是一份卓越的文档",
            "我们一般会写一些比较重要的内容": "笔者通常会撰写若干至关重要的内容",
            "这个功能很不错": "该功能表现优异",
            "大家都应该使用": "各位应当采纳使用",
            "我又回到了职场": "我重返职场",
            "找到了一份高薪工作": "获得了一份高薪工作",
            "生活终于回归正常": "生活恢复正常",
            "经过九个月的旅行后": "经过九个月的旅行",
            "回顾以往": "回顾过去",
            "换句话说": "也就是说",
            "为什么呢？": "原因是什么？"
        }

        optimized_content = original_content
        for original, rewritten in rewrite_rules.items():
            optimized_content = optimized_content.replace(original, rewritten)

        return optimized_content

    def _apply_translation_optimization(self, text: str) -> str:
        """应用翻译优化规则"""
        return "[翻译优化后的内容]"

    def _apply_simple_rewrite(self, text: str) -> str:
        """应用简单改写规则"""
        return text + " [Mock改写]"

    def get_name(self) -> str:
        """获取 Provider 名称"""
        return self.provider_name

    def __repr__(self) -> str:
        return f"<MockProvider(name={self.provider_name})>"