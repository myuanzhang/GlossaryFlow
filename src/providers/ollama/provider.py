"""
Ollama Provider Implementation

Ollama 本地 LLM Provider 实现，支持本地运行的开源模型。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
import requests
import json

from providers.base import BaseProvider, ProviderConfig, ModelInfo, ModelCapability
from providers.mixins import LocalProviderHealthMixin
from core.types import ProviderType

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider, LocalProviderHealthMixin):
    """Ollama Provider 实现"""

    def __init__(self, config: ProviderConfig):
        """
        初始化 Ollama Provider

        Args:
            config: Provider 配置
        """
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.session = requests.Session()
        # Ollama 本地模型可能需要更长时间（特别是7B+模型）
        # 使用更长的超时时间：10分钟
        self.session.timeout = 600

    def is_configured(self) -> bool:
        """
        检查 Provider 是否已配置

        Local Provider 不要求 API Key，只检查服务可用性

        Returns:
            是否已配置
        """
        is_healthy, _ = self.health_check()
        return is_healthy

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """
        验证 Provider 配置

        Local Provider 专用: 不要求 API Key，只检查 base_url 是否可访问

        Returns:
            (is_valid, error_message): 配置是否有效及错误信息
        """
        # Local Provider 不要求 API Key
        # 只检查服务是否可达
        is_available, error_msg = self.check_service_availability(self.base_url, timeout=5)
        if not is_available:
            return False, error_msg

        return True, None

    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        真实 Health Check

        Local Provider 专用: 检查本地 Ollama 服务是否运行且有可用模型

        Returns:
            (is_healthy, error_message): 是否健康及错误信息
        """
        # 检查服务是否可访问
        is_available, error_msg = self.check_service_availability(self.base_url, timeout=5)
        if not is_available:
            return False, error_msg

        # 检查是否有可用模型
        try:
            models = self.get_available_models()
            if not models:
                return False, "No models available - please run 'ollama pull <model>' first"
        except Exception as e:
            return False, f"Failed to list models: {str(e)}"

        return True, None

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model["name"] for model in models]
            else:
                logger.error(f"Failed to fetch Ollama models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            return []

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        获取模型信息

        Args:
            model_name: 模型名称

        Returns:
            模型信息或 None
        """
        available_models = self.get_available_models()
        if model_name not in available_models:
            return None

        # 基于模型名称推断能力
        capabilities = [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.TRANSLATION,
            ModelCapability.MULTILINGUAL
        ]

        supports_streaming = True
        supports_function_calling = False
        max_tokens = 4096

        # 根据模型名称调整参数
        if "code" in model_name.lower() or "coder" in model_name.lower():
            capabilities.append(ModelCapability.CODE_GENERATION)

        if "llama3" in model_name.lower() or "llama-3" in model_name.lower():
            max_tokens = 8192
        elif "llama2" in model_name.lower() or "llama-2" in model_name.lower():
            max_tokens = 4096

        if model_name.startswith("llama3") or "mixtral" in model_name.lower():
            supports_function_calling = True

        return ModelInfo(
            name=model_name,
            provider=ProviderType.OLLAMA,
            capabilities=capabilities,
            max_tokens=max_tokens,
            supports_streaming=supports_streaming,
            supports_function_calling=supports_function_calling,
            pricing={"input": 0.0, "output": 0.0}  # 本地模型免费
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
        # Ollama 的 generate API 本身是同步的，在线程池中运行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, prompt, model, temperature, max_tokens, **kwargs)

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
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=600  # 10 minutes for local models
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
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
            available_models = self.get_available_models()
            if available_models:
                model = available_models[0]
            else:
                raise RuntimeError("No Ollama models available")

        # 检查是否已经包含完整的翻译指令（避免双重包装）
        text_lower = text.lower()
        is_full_prompt = any(keyword in text_lower for keyword in [
            'translate all chinese text',
            'you are a professional translator',
            'important requirements',
            'preserve all markdown formatting'
        ])

        if is_full_prompt:
            # text已经是完整的prompt，直接使用generate
            try:
                return self.generate(text, model, temperature=0.3, **kwargs)
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

    def pull_model(self, model_name: str) -> bool:
        """
        拉取模型

        Args:
            model_name: 模型名称

        Returns:
            是否成功拉取
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型状态

        Args:
            model_name: 模型名称

        Returns:
            模型状态信息
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Model {model_name} not found"}
        except Exception as e:
            logger.error(f"Failed to get model status for {model_name}: {e}")
            return {"error": str(e)}

    def get_name(self) -> str:
        """获取 Provider 名称"""
        return "ollama"

    def __repr__(self) -> str:
        return f"<OllamaProvider(base_url={self.base_url}, configured={self.is_configured()})>"