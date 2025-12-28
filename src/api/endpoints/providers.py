"""
Providers Endpoint

Manages and provides information about available LLM providers.
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Path

from providers.registry import provider_registry
from api.models.common import ProvidersResponse, ProviderStatus

router = APIRouter()


@router.get("/", response_model=ProvidersResponse)
async def list_providers():
    """
    List all available LLM providers
    """
    try:
        providers = provider_registry.list_available_providers()
        return ProvidersResponse(providers=providers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.get("/{provider_name}/status", response_model=ProviderStatus)
async def get_provider_status(provider_name: str = Path(..., description="Provider name (e.g., openai, ollama, mock)")):
    """
    Get status and information for a specific provider

    ⚠️ CRITICAL: 使用真实 health_check() 而非简单的 is_configured()
    """
    try:
        provider = provider_registry.get_or_create(provider_name)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

        # ✅ 使用真实 health_check()
        is_healthy, error_msg = provider.health_check()

        models = provider.get_available_models()

        return ProviderStatus(
            success=True,
            available=is_healthy,
            provider=provider_name,
            models=models,
            configuration_status="Healthy" if is_healthy else f"Unhealthy: {error_msg}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")


@router.get("/{provider_name}/models")
async def get_provider_models(provider_name: str = Path(..., description="Provider name")):
    """
    Get available models for a specific provider
    """
    try:
        provider = provider_registry.get_or_create(provider_name)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

        models = provider.get_available_models()
        return {
            "provider": provider_name,
            "models": models,
            "count": len(models)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider models: {str(e)}")