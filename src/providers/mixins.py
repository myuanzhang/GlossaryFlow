"""
Provider Mixins

提供可复用的 Provider 校验逻辑。
"""

from typing import Optional, Tuple


class CloudProviderValidationMixin:
    """
    Cloud Provider 校验混入类

    适用于需要 API Key 的云端 Provider (OpenAI, DeepSeek, Mimo 等)
    """

    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        验证 API Key 是否有效

        Args:
            api_key: API Key 字符串

        Returns:
            (is_valid, error_message): 是否有效及错误信息
        """
        # 检查 API Key 是否存在
        if not api_key:
            return False, "API key is missing"

        # 检查 API Key 是否为占位符
        placeholder_patterns = [
            "your_", "your-api", "your_api",
            "placeholder", "example", "test_key",
            "sk-xxx", "sk-xxxx", "sk-test",
            "sk-your", "your_key"
        ]
        api_key_lower = api_key.lower()
        if any(pattern in api_key_lower for pattern in placeholder_patterns):
            return False, "API key appears to be a placeholder"

        # 检查 API Key 格式（基本验证）
        if len(api_key) < 10:
            return False, "API key is too short (likely invalid)"

        return True, None


class LocalProviderHealthMixin:
    """
    Local Provider 健康检查混入类

    适用于本地 Provider (Ollama, Mock 等)
    """

    @staticmethod
    def check_service_availability(base_url: str, timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        检查本地服务是否可用

        Args:
            base_url: 服务基础 URL
            timeout: 超时时间（秒）

        Returns:
            (is_available, error_message): 是否可用及错误信息
        """
        try:
            import requests
            response = requests.get(f"{base_url}/api/tags", timeout=timeout)
            if response.status_code == 200:
                return True, None
            else:
                return False, f"Service returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Service not reachable at {base_url}"
        except requests.exceptions.Timeout:
            return False, f"Service timeout after {timeout}s"
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
