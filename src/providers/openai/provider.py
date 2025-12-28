"""
OpenAI Provider Implementation

OpenAI API Provider 实现，支持 GPT 模型。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
import openai

from providers.base import BaseProvider, ProviderConfig, ModelInfo, ModelCapability
from providers.mixins import CloudProviderValidationMixin
from core.types import ProviderType

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider, CloudProviderValidationMixin):
    """OpenAI GPT Provider 实现"""

    def __init__(self, provider_config: ProviderConfig, models_config: Optional[List[str]] = None):
        """
        初始化 OpenAI Provider

        Args:
            provider_config: Provider 配置
            models_config: 从配置文件中读取的允许使用的模型列表
        """
        super().__init__(provider_config)
        self.api_key = provider_config.api_key
        self.base_url = provider_config.base_url
        self._configured_models = models_config  # 使用配置中的模型列表
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """初始化 OpenAI 客户端"""
        if not self.api_key:
            logger.warning("OpenAI API key not provided, provider will not be functional")
            return

        try:
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self.client = openai.OpenAI(**client_kwargs)
            logger.info("OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def is_configured(self) -> bool:
        """
        检查 Provider 是否已配置

        Returns:
            是否已配置
        """
        return bool(self.client)

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """
        验证 Provider 配置

        Cloud Provider 专用: 检查 API Key 有效性

        Returns:
            (is_valid, error_message): 配置是否有效及错误信息
        """
        # 使用 Cloud Provider 通用校验逻辑
        return self.validate_api_key(self.config.api_key)

    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        真实 Health Check

        Cloud Provider 专用: 验证 API Key + 尝试初始化

        Returns:
            (is_healthy, error_message): 是否健康及错误信息
        """
        # 第一步: 配置验证
        is_valid, error_msg = self.validate_configuration()
        if not is_valid:
            return False, error_msg

        # 第二步: 尝试获取可用模型列表
        try:
            models = self.get_available_models()
            if not models:
                return False, "No models configured"
        except Exception as e:
            return False, f"Provider initialization failed: {str(e)}"

        return True, None

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表（仅返回配置中声明的模型）
        """
        if not self.is_configured():
            return []

        # 返回配置文件中明确声明的模型列表
        if self._configured_models and len(self._configured_models) > 0:
            return self._configured_models

        # 如果没有配置，返回空列表而不是硬编码列表
        return []

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

        # 根据模型名称确定能力
        capabilities = [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.TRANSLATION,
            ModelCapability.MULTILINGUAL
        ]

        supports_streaming = True
        supports_function_calling = False
        max_tokens = 4096

        if model_name.startswith("gpt-4"):
            supports_function_calling = True
            max_tokens = 8192 if "32k" not in model_name else 32768
        elif model_name.startswith("gpt-3.5"):
            max_tokens = 4096 if "16k" not in model_name else 16384
        elif "gpt-4o" in model_name:
            supports_function_calling = True
            max_tokens = 128000
        elif model_name.startswith("o1"):
            max_tokens = 128000
            supports_streaming = False

        return ModelInfo(
            name=model_name,
            provider=ProviderType.OPENAI,
            capabilities=capabilities,
            max_tokens=max_tokens,
            supports_streaming=supports_streaming,
            supports_function_calling=supports_function_calling,
            pricing=self._get_pricing_info(model_name)
        )

    def _get_pricing_info(self, model_name: str) -> Optional[Dict[str, float]]:
        """获取模型定价信息"""
        # 简化的定价信息（实际应用中可以从 API 获取）
        pricing_info = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }

        return pricing_info.get(model_name)

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
        if not self.is_configured():
            raise RuntimeError("OpenAI provider is not configured")

        try:
            messages = [{"role": "user", "content": prompt}]

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.config.timeout_seconds,
                **kwargs
            )

            return response.choices[0].message.content

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            raise

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
        if not self.is_configured():
            raise RuntimeError("OpenAI provider is not configured")

        try:
            messages = [{"role": "user", "content": prompt}]

            logger.info(f"Calling OpenAI API with model={model}, prompt_length={len(prompt)}")

            # Set a reasonable max_tokens if not specified
            # For translation, we need more tokens than input
            # Use a much higher limit for document translation (up to 16k for most models)
            if max_tokens:
                actual_max_tokens = max_tokens
            else:
                # Estimate: Chinese ~2-3 chars per token, translation needs similar or more tokens
                # Multiply by 4 to be safe, cap at model's max
                estimated_tokens = len(prompt) * 4

                # Determine model-specific max_tokens limit
                # DeepSeek models: 8192, OpenAI: up to 16384/32768, others: vary
                model_lower = model.lower()
                if 'deepseek' in model_lower:
                    model_max_tokens = 8192
                elif 'gpt-4' in model_lower or 'gpt-4o' in model_lower:
                    model_max_tokens = 16384
                elif 'gpt-3.5' in model_lower:
                    model_max_tokens = 4096
                elif 'o1' in model_lower:
                    model_max_tokens = 32768
                else:
                    # Conservative default for unknown models
                    model_max_tokens = 4096

                actual_max_tokens = min(model_max_tokens, estimated_tokens)

            logger.info(f"Using max_tokens={actual_max_tokens} (estimated_input_tokens~{len(prompt)//3})")

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=actual_max_tokens,
                timeout=self.config.timeout_seconds,
                **kwargs
            )

            # Debug: log the entire response
            logger.info(f"OpenAI API response: choices={len(response.choices) if response.choices else 0}")

            if not response.choices:
                logger.error(f"OpenAI API returned no choices. Full response: {response}")
                return ""

            choice = response.choices[0]
            logger.info(f"Choice: finish_reason={choice.finish_reason}, index={choice.index}")

            # Check if output was truncated due to max_tokens limit
            if choice.finish_reason == 'length':
                logger.warning(f"⚠️ Output was truncated due to max_tokens limit! Content may be incomplete.")
                logger.warning(f"⚠️ Current max_tokens={actual_max_tokens}, consider increasing this limit for longer documents")
                # Log usage info if available
                if hasattr(response, 'usage') and response.usage:
                    logger.warning(f"⚠️ Token usage: {response.usage.total_tokens} total (prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens})")

            message = choice.message
            if not message:
                logger.error(f"OpenAI API returned empty message. Choice: {choice}")
                return ""

            content = message.content
            logger.info(f"OpenAI API returned content_length={len(content) if content else 0}")
            if content:
                logger.info(f"Content preview (first 200 chars): {content[:200]}")
                # Check if content is mostly Chinese
                chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                chinese_ratio = chinese_chars / len(content) if content else 0
                logger.info(f"Content Chinese character ratio: {chinese_ratio:.2%}")

            # CRITICAL: For reasoning models (DeepSeek R1, etc.), discard reasoning_content
            # We only want the final translated content, not the thinking process
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                logger.info(f"⚠️ Found reasoning_content ({len(message.reasoning_content)} chars), DISCARDING it to prevent reasoning leakage")
                logger.info(f"✅ Using only final content ({len(content) if content else 0} chars)")

            # Only return the actual translated content, never reasoning_content
            if content:
                logger.info(f"✅ Returning final content only (length={len(content)})")
                return content
            else:
                logger.warning(f"⚠️ No content available, reasoning_content was discarded")
                return ""

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            import traceback
            traceback.print_exc()
            raise

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

        如果text已经包含完整的prompt，则直接使用，不再包装。

        Args:
            text: 待翻译文本（可能是完整的prompt）
            source_lang: 源语言
            target_lang: 目标语言
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            翻译后的文本
        """
        if not text.strip():
            return text

        # 使用默认模型
        if not model:
            model = "gpt-3.5-turbo"

        # 检查是否已经包含完整的翻译指令（避免双重包装）
        text_lower = text.lower()
        is_full_prompt = any(keyword in text_lower for keyword in [
            'translate all chinese text',
            'you are a professional translator',
            'important requirements',
            'preserve all markdown formatting',
            'translate the following markdown document',
            'critical output requirements'
        ])

        logger.info(f"OpenAIProvider.translate: is_full_prompt={is_full_prompt}, text_length={len(text)}, model={model}")
        logger.info(f"OpenAIProvider.translate: text_preview={text[:200]}")

        if is_full_prompt:
            # text已经是完整的prompt，直接使用generate
            try:
                result = self.generate(text, model, temperature=0.3, **kwargs)
                logger.info(f"OpenAIProvider.translate: generate result length={len(result)}, first_100={result[:100]}")
                return result
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return text

        # 否则，使用原有的翻译逻辑
        if source_lang == target_lang:
            # 如果源语言和目标语言相同，可能是改写请求
            prompt = f"""请将以下{source_lang}内容改写为更清晰、更流畅的表达：

{text}

请只返回改写后的内容，不要添加任何解释。"""
        else:
            # 真正的翻译请求
            prompt = f"""请将以下{source_lang}文本翻译为{target_lang}：

{text}

要求：
1. 保持原文的意思和语气
2. 使用自然流畅的{target_lang}表达
3. 只返回翻译结果，不要添加解释"""

        try:
            return self.generate(prompt, model, temperature=0.3, **kwargs)
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # 返回原文本作为后备
            return text

    def get_name(self) -> str:
        """获取 Provider 名称"""
        return "openai"

    def __repr__(self) -> str:
        return f"<OpenAIProvider(base_url={self.base_url}, configured={self.is_configured()})>"