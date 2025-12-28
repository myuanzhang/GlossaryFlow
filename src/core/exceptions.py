"""
Translation System Exceptions

定义翻译系统的异常层次结构和错误码。
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """错误码枚举"""

    # Provider 配置错误 (1xxx)
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    PROVIDER_API_KEY_MISSING = "PROVIDER_API_KEY_MISSING"
    PROVIDER_API_KEY_INVALID = "PROVIDER_API_KEY_INVALID"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"

    # 模型相关错误 (2xxx)
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    MODEL_CAPABILITY_UNSUPPORTED = "MODEL_CAPABILITY_UNSUPPORTED"

    # API 调用错误 (3xxx)
    API_REQUEST_FAILED = "API_REQUEST_FAILED"
    API_RATE_LIMIT_EXCEEDED = "API_RATE_LIMIT_EXCEEDED"
    API_TIMEOUT = "API_TIMEOUT"
    API_AUTHENTICATION_FAILED = "API_AUTHENTICATION_FAILED"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"

    # 翻译任务错误 (4xxx)
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    TRANSLATION_EMPTY_INPUT = "TRANSLATION_EMPTY_INPUT"
    TRANSLATION_EMPTY_OUTPUT = "TRANSLATION_EMPTY_OUTPUT"
    TRANSLATION_VALIDATION_FAILED = "TRANSLATION_VALIDATION_FAILED"

    # 系统错误 (5xxx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    INVALID_REQUEST = "INVALID_REQUEST"


class TranslationException(Exception):
    """翻译系统基础异常"""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details
        }


class ProviderException(TranslationException):
    """Provider 相关异常"""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if provider_name:
            details["provider"] = provider_name
        super().__init__(message, code, details)


class ModelException(TranslationException):
    """模型相关异常"""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if model_name:
            details["model"] = model_name
        super().__init__(message, code, details)


class APIException(TranslationException):
    """API 调用相关异常"""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if status_code is not None:
            details["status_code"] = status_code
        super().__init__(message, code, details)


class TranslationValidationException(TranslationException):
    """翻译验证异常"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.TRANSLATION_VALIDATION_FAILED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)
