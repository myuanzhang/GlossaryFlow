"""
Mimo Provider Implementation

Mimo API Provider 实现，兼容 OpenAI API。
"""

import logging
from typing import Dict, Any, Optional, List

from providers.base import BaseProvider, ProviderConfig, ModelInfo, ModelCapability
from providers.openai.provider import OpenAIProvider
from core.types import ProviderType

logger = logging.getLogger(__name__)


class MimoProvider(OpenAIProvider):
    """Mimo API Provider 实现 - 继承自OpenAIProvider"""

    def __init__(self, provider_config: ProviderConfig, models_config: Optional[List[str]] = None):
        """
        初始化 Mimo Provider

        Args:
            provider_config: Provider 配置
            models_config: 从配置文件中读取的允许使用的模型列表
        """
        # 调用父类OpenAIProvider的初始化
        super().__init__(provider_config, models_config)
        logger.info(f"Mimo Provider initialized with models: {models_config}")

    def get_name(self) -> str:
        """获取 Provider 名称"""
        return "mimo"

    def get_provider_info(self) -> Dict[str, Any]:
        """获取 Provider 信息"""
        info = super().get_provider_info()
        info["provider_type"] = ProviderType.MIMO.value
        return info

    def __repr__(self) -> str:
        return f"<MimoProvider(base_url={self.base_url}, configured={self.is_configured()})>"
