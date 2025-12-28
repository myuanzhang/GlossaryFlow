"""
Data Validation

提供各种数据验证功能。
"""

import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from .types import AgentType, JobStatus, ProviderType


class ValidationError(Exception):
    """验证错误异常"""
    pass


class DataValidator:
    """数据验证器"""

    # Markdown 内容的最大长度（字符）
    MAX_CONTENT_LENGTH = 10_000_000  # 10MB

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'.md', '.markdown', '.txt'}

    # 正则表达式模式
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$')

    @staticmethod
    def validate_agent_type(agent_type: Any) -> AgentType:
        """
        验证 Agent 类型

        Args:
            agent_type: Agent 类型

        Returns:
            验证后的 AgentType

        Raises:
            ValidationError: 验证失败
        """
        if isinstance(agent_type, str):
            try:
                return AgentType(agent_type)
            except ValueError:
                raise ValidationError(f"Invalid agent_type: {agent_type}")

        if isinstance(agent_type, AgentType):
            return agent_type

        raise ValidationError(f"agent_type must be string or AgentType, got {type(agent_type)}")

    @staticmethod
    def validate_job_status(status: Any) -> JobStatus:
        """
        验证作业状态

        Args:
            status: 作业状态

        Returns:
            验证后的 JobStatus

        Raises:
            ValidationError: 验证失败
        """
        if isinstance(status, str):
            try:
                return JobStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid job status: {status}")

        if isinstance(status, JobStatus):
            return status

        raise ValidationError(f"status must be string or JobStatus, got {type(status)}")

    @staticmethod
    def validate_provider_type(provider_type: Any) -> ProviderType:
        """
        验证 Provider 类型

        Args:
            provider_type: Provider 类型

        Returns:
            验证后的 ProviderType

        Raises:
            ValidationError: 验证失败
        """
        if isinstance(provider_type, str):
            try:
                return ProviderType(provider_type)
            except ValueError:
                raise ValidationError(f"Invalid provider_type: {provider_type}")

        if isinstance(provider_type, ProviderType):
            return provider_type

        raise ValidationError(f"provider_type must be string or ProviderType, got {type(provider_type)}")

    @staticmethod
    def validate_markdown_content(content: Any) -> str:
        """
        验证 Markdown 内容

        Args:
            content: Markdown 内容

        Returns:
            验证后的内容

        Raises:
            ValidationError: 验证失败
        """
        if content is None:
            raise ValidationError("Content cannot be None")

        if not isinstance(content, str):
            content = str(content)

        if len(content) == 0:
            raise ValidationError("Content cannot be empty")

        if len(content) > DataValidator.MAX_CONTENT_LENGTH:
            raise ValidationError(f"Content too long: {len(content)} > {DataValidator.MAX_CONTENT_LENGTH}")

        # 检查是否包含潜在的恶意内容
        if DataValidator._contains_malicious_patterns(content):
            raise ValidationError("Content contains potentially malicious patterns")

        return content

    @staticmethod
    def validate_file_path(file_path: Any, check_exists: bool = False) -> Path:
        """
        验证文件路径

        Args:
            file_path: 文件路径
            check_exists: 是否检查文件存在

        Returns:
            验证后的 Path 对象

        Raises:
            ValidationError: 验证失败
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")

        try:
            path = Path(file_path)
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")

        # 检查文件扩展名
        if path.suffix.lower() not in DataValidator.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Unsupported file extension: {path.suffix}. Allowed: {DataValidator.ALLOWED_EXTENSIONS}")

        # 检查文件是否存在
        if check_exists and not path.exists():
            raise ValidationError(f"File does not exist: {path}")

        # 检查是否为文件
        if check_exists and path.exists() and not path.is_file():
            raise ValidationError(f"Path is not a file: {path}")

        return path

    @staticmethod
    def validate_temperature(temperature: Any) -> float:
        """
        验证温度参数

        Args:
            temperature: 温度值

        Returns:
            验证后的温度值

        Raises:
            ValidationError: 验证失败
        """
        try:
            temp = float(temperature)
        except (ValueError, TypeError):
            raise ValidationError(f"Temperature must be a number, got {temperature}")

        if not 0.0 <= temp <= 2.0:
            raise ValidationError(f"Temperature must be between 0.0 and 2.0, got {temp}")

        return temp

    @staticmethod
    def validate_timeout(timeout: Any) -> int:
        """
        验证超时参数

        Args:
            timeout: 超时值（秒）

        Returns:
            验证后的超时值

        Raises:
            ValidationError: 验证失败
        """
        try:
            timeout_int = int(timeout)
        except (ValueError, TypeError):
            raise ValidationError(f"Timeout must be an integer, got {timeout}")

        if timeout_int <= 0:
            raise ValidationError(f"Timeout must be positive, got {timeout_int}")

        if timeout_int > 300:  # 5分钟上限
            raise ValidationError(f"Timeout too large: {timeout_int}s > 300s")

        return timeout_int

    @staticmethod
    def validate_max_retries(max_retries: Any) -> int:
        """
        验证最大重试次数

        Args:
            max_retries: 最大重试次数

        Returns:
            验证后的重试次数

        Raises:
            ValidationError: 验证失败
        """
        try:
            retries_int = int(max_retries)
        except (ValueError, TypeError):
            raise ValidationError(f"Max retries must be an integer, got {max_retries}")

        if retries_int < 0:
            raise ValidationError(f"Max retries cannot be negative, got {retries_int}")

        if retries_int > 10:
            raise ValidationError(f"Max retries too large: {retries_int} > 10")

        return retries_int

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱地址

        Args:
            email: 邮箱地址

        Returns:
            是否有效
        """
        return bool(DataValidator.EMAIL_PATTERN.match(email))

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        验证 URL

        Args:
            url: URL 地址

        Returns:
            是否有效
        """
        return bool(DataValidator.URL_PATTERN.match(url))

    @staticmethod
    def validate_model_name(model_name: str, available_models: List[str]) -> str:
        """
        验证模型名称

        Args:
            model_name: 模型名称
            available_models: 可用模型列表

        Returns:
            验证后的模型名称

        Raises:
            ValidationError: 验证失败
        """
        if not model_name:
            raise ValidationError("Model name cannot be empty")

        if not available_models:
            raise ValidationError("Available models list is empty")

        if model_name not in available_models:
            raise ValidationError(f"Model '{model_name}' not available. Available: {available_models}")

        return model_name

    @staticmethod
    def _contains_malicious_patterns(content: str) -> bool:
        """
        检查内容是否包含恶意模式

        Args:
            content: 内容

        Returns:
            是否包含恶意模式
        """
        # 基本的恶意模式检查
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'on\w+\s*=',                # Event handlers
            r'eval\s*\(',                # eval() calls
            r'document\.',               # Document object access
            r'window\.',                 # Window object access
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True

        return False

    @staticmethod
    def sanitize_string(input_string: str, max_length: Optional[int] = None) -> str:
        """
        清理字符串

        Args:
            input_string: 输入字符串
            max_length: 最大长度

        Returns:
            清理后的字符串
        """
        if not isinstance(input_string, str):
            input_string = str(input_string)

        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', input_string)

        # 截断长度
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_dict_structure(data: Dict[str, Any], required_keys: List[str]) -> None:
        """
        验证字典结构

        Args:
            data: 数据字典
            required_keys: 必需的键列表

        Raises:
            ValidationError: 验证失败
        """
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data)}")

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValidationError(f"Missing required keys: {missing_keys}")