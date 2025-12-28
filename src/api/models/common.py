"""
Common API Models

Shared Pydantic models used across different API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: Dict[str, Any]


class ProviderStatus(BaseModel):
    """Provider status model"""
    success: bool
    available: bool
    provider: str
    models: List[str]
    configuration_status: str


class HealthResponse(BaseResponse):
    """Health check response model"""
    success: bool = True
    status: str  # "healthy" | "degraded" | "down"
    available_providers: List[str]
    provider_status: Dict[str, bool]


class ProvidersResponse(BaseResponse):
    """Available providers response model"""
    success: bool = True
    providers: List[str]


class JobStartResponse(BaseResponse):
    """Job start response model"""
    success: bool = True
    job_id: str
    estimated_duration_ms: int


class LLMConfig(BaseModel):
    """LLM configuration model"""
    provider: str = Field(default="openai", description="LLM provider name")
    model: str = Field(default="gpt-3.5-turbo", description="Model name")
    temperature: Optional[float] = Field(default=0.3, ge=0.0, le=2.0, description="Temperature parameter")
    extra_options: Optional[Dict[str, Any]] = Field(default=None, description="Extra options")


class TranslationRequest(BaseModel):
    """Translation request model"""
    source_markdown: str = Field(..., description="Source markdown content to translate")
    glossary: Optional[Dict[str, str]] = Field(default=None, description="Glossary for term translation")
    llm_config: Optional[LLMConfig] = Field(default=None, description="LLM configuration")


class RewriteRequest(BaseModel):
    """Rewrite request model"""
    source_markdown: str = Field(..., description="Source markdown content to rewrite")
    strategy: Optional[str] = Field(default="line_by_line", description="Rewrite strategy")
    document_context: Optional[Dict[str, Any]] = Field(default=None, description="Document context")
    llm_config: Optional[LLMConfig] = Field(default=None, description="LLM configuration")