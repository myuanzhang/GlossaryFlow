"""
Health Check Endpoint

Provides health status and system information.
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from api.models.common import HealthResponse

from providers.registry import provider_registry
from core.config import config

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check API health and system information

    ⚠️ CRITICAL: available_providers 仅包含真正可用的 provider
    """
    try:
        all_providers = provider_registry.list_available_providers()

        provider_status = {}
        truly_available_providers = []

        for provider_name in all_providers:
            provider = provider_registry.get_or_create(provider_name)
            # ✅ 使用真实 health_check()
            if provider:
                is_healthy, _ = provider.health_check()
                provider_status[provider_name] = is_healthy

                # ⚠️ CRITICAL: 仅统计真正可用的 provider
                if is_healthy:
                    truly_available_providers.append(provider_name)
            else:
                provider_status[provider_name] = False

        # Determine overall health status
        # ⚠️ CRITICAL: 至少有一个可用 provider 才算 healthy
        if len(truly_available_providers) > 0:
            status = "healthy"
        elif all_providers:
            status = "degraded"  # 有 provider 但都不可用
        else:
            status = "down"  # 没有 provider

        return HealthResponse(
            status=status,
            available_providers=truly_available_providers,  # ✅ 仅返回可用的
            provider_status=provider_status
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/version")
async def get_version():
    """
    Get API version information
    """
    return {
        "api_version": "3.0.0",
        "backend": "FastAPI + Multi-Agent Architecture",
        "features": {
            "translation": True,
            "rewrite": True,
            "websocket": True,
            "multi_agent": True
        }
    }