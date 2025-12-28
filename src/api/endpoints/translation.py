"""
Translation Endpoint

Handles document translation requests with real-time progress updates.
"""

import uuid
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from translator.markdown_translator import MarkdownTranslator
from translator.glossary import Glossary
from api.models.common import JobStartResponse, TranslationRequest
from api.websocket.manager import manager
from providers.registry import provider_registry
from core.exceptions import (
    ErrorCode,
    ProviderException,
    TranslationException,
    TranslationValidationException
)

router = APIRouter()


# In-memory job storage (will be replaced with database)
job_storage: Dict[str, Dict[str, Any]] = {}


def create_error_response(exception: TranslationException) -> Dict[str, Any]:
    """
    创建符合前端期望的错误响应格式

    Args:
        exception: 翻译异常

    Returns:
        标准错误响应字典
    """
    return {
        "success": False,
        "error": {
            "code": exception.code.value,
            "message": exception.message,
            "details": exception.details
        }
    }


def validate_provider_availability(provider_name: str, model_name: str) -> None:
    """
    验证 Provider 是否可用（Fail Fast 预检查）

    Args:
        provider_name: Provider 名称
        model_name: 模型名称

    Raises:
        ProviderException: 如果 Provider 不可用
    """
    # 检查 Provider 是否存在
    provider = provider_registry.get_or_create(provider_name)
    if not provider:
        raise ProviderException(
            f"Provider '{provider_name}' not found",
            ErrorCode.PROVIDER_NOT_FOUND,
            provider_name=provider_name,
            details={"available_providers": provider_registry.list_available_providers()}
        )

    # 检查 Provider 配置
    if not provider.is_configured():
        raise ProviderException(
            f"Provider '{provider_name}' is not configured",
            ErrorCode.PROVIDER_NOT_CONFIGURED,
            provider_name=provider_name
        )

    # 详细配置验证
    is_valid, error_msg = provider.validate_configuration()
    if not is_valid:
        raise ProviderException(
            f"Provider '{provider_name}' configuration invalid: {error_msg}",
            ErrorCode.PROVIDER_API_KEY_INVALID,
            provider_name=provider_name,
            details={"validation_error": error_msg}
        )

    # 检查模型是否可用
    available_models = provider.get_available_models()
    if model_name not in available_models:
        raise ProviderException(
            f"Model '{model_name}' not available in provider '{provider_name}'",
            ErrorCode.MODEL_NOT_AVAILABLE,
            provider_name=provider_name,
            details={
                "requested_model": model_name,
                "available_models": available_models
            }
        )


@router.post("/translate", response_model=JobStartResponse)
async def start_translation(
    request: TranslationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a document translation job
    """
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"[{time.time() - start_time:.3f}s] ⏱️  POST /translate called")

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        print(f"[{time.time() - start_time:.3f}s] 🆔 Job ID generated: {job_id}")

        # Extract data from request
        source_markdown = request.source_markdown
        glossary = request.glossary
        llm_config = request.llm_config
        print(f"[{time.time() - start_time:.3f}s] 📦 Request data extracted")

        # Initialize job storage
        job_storage[job_id] = {
            "id": job_id,
            "status": "validating",
            "progress": 0.0,
            "source_markdown": source_markdown,
            "glossary": glossary,
            "llm_config": llm_config.dict() if llm_config else {},
            "start_time": None,
            "end_time": None,
            "result": None,
            "error": None
        }
        print(f"[{time.time() - start_time:.3f}s] 💾 Job storage initialized")

        # Validate inputs
        if not source_markdown.strip():
            exc = TranslationException(
                "Source markdown cannot be empty",
                ErrorCode.TRANSLATION_EMPTY_INPUT
            )
            return JSONResponse(
                status_code=400,
                content=create_error_response(exc)
            )

        # Extract LLM config with defaults
        provider_name = llm_config.provider if llm_config else "openai"
        model_name = llm_config.model if llm_config else "gpt-3.5-turbo"
        temperature = llm_config.temperature if llm_config else 0.3

        # Log translation request
        print(f"[{time.time() - start_time:.3f}s] 📝 Translation config: provider={provider_name}, model={model_name}, content_length={len(source_markdown)}")

        # ⚠️ CRITICAL: Fail Fast - 验证 Provider 可用性（在创建任务前）
        try:
            validate_provider_availability(provider_name, model_name)
        except ProviderException as e:
            # Provider 验证失败，直接返回错误（不创建任务）
            print(f"[{time.time() - start_time:.3f}s] ❌ Provider validation failed: {e.message}")
            return JSONResponse(
                status_code=400,
                content=create_error_response(e)
            )

        # Create glossary if provided
        gloss = None
        if glossary:
            print(f"[{time.time() - start_time:.3f}s] 📖 Creating glossary...")
            gloss = Glossary(glossary)
            print(f"[{time.time() - start_time:.3f}s] ✅ Glossary created")

        # Start translation in background
        print(f"[{time.time() - start_time:.3f}s] 🚀 Adding background task for job {job_id}")
        background_tasks.add_task(
            perform_translation,
            job_id,
            source_markdown,
            provider_name,
            model_name,
            temperature,
            gloss
        )
        print(f"[{time.time() - start_time:.3f}s] ✅ Background task added")

        response = JobStartResponse(
            job_id=job_id,
            estimated_duration_ms=len(source_markdown) * 50  # Rough estimate
        )

        total_time = time.time() - start_time
        print(f"[{total_time:.3f}s] ✅ Translation job started: {job_id}")
        print(f"{'='*60}\n")
        return response

    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        print(f"[{total_time:.3f}s] ❌ Failed to start translation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start translation: {str(e)}")


@router.get("/translate/{job_id}/status")
async def get_translation_status(job_id: str):
    """
    Get the status of a translation job
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    return {
        "success": True,
        "status": job["status"],
        "progress": job["progress"],
        "start_time": job["start_time"],
        "estimated_completion": job.get("estimated_completion"),
        "warnings": job.get("warnings", []),
        "error": job.get("error"),
        "result": job.get("result")
    }


@router.get("/translate/{job_id}/result")
async def get_translation_result(job_id: str):
    """
    Get the final translation result (returns only the translated markdown content)
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job["result"]:
        raise HTTPException(status_code=404, detail="Translation result not available")

    # Return only the translated markdown content, not the full result object
    from fastapi.responses import Response
    translated_content = job["result"]["translated_markdown"]
    return Response(content=translated_content, media_type="text/markdown")


async def perform_translation(
    job_id: str,
    source_markdown: str,
    provider_name: str,
    model_name: str,
    temperature: float,
    glossary: Optional[Glossary]
):
    """
    Perform translation in background (runs in thread pool to avoid blocking)
    """
    try:
        # Update job status
        job_storage[job_id]["status"] = "translating"
        job_storage[job_id]["start_time"] = asyncio.get_event_loop().time()

        await manager.send_status_update(job_id, "translating", 0.0)

        # Create translator
        translator = MarkdownTranslator(
            provider_name=provider_name,
            model_name=model_name,
            glossary=glossary
        )

        # Perform translation in thread pool to avoid blocking event loop
        await manager.send_status_update(job_id, "translating", 10.0)

        # Run the synchronous translate() method in a thread pool
        loop = asyncio.get_event_loop()
        translated_content = await loop.run_in_executor(
            None,  # Use default thread pool executor
            translator.translate,
            source_markdown
        )

        await manager.send_status_update(job_id, "translating", 90.0)

        # ⚠️ CRITICAL: 验证翻译结果，禁止返回原文作为"翻译结果"
        if not translated_content or translated_content == source_markdown:
            raise TranslationException(
                "Translation failed: output is empty or identical to input",
                ErrorCode.TRANSLATION_VALIDATION_FAILED,
                details={
                    "output_length": len(translated_content) if translated_content else 0,
                    "input_length": len(source_markdown),
                    "output_equals_input": translated_content == source_markdown
                }
            )

        # 验证翻译质量（中文字符比例）
        chinese_chars = sum(1 for c in translated_content if '\u4e00' <= c <= '\u9fff')
        chinese_ratio = chinese_chars / len(translated_content) if translated_content else 0
        if chinese_ratio > 0.5:
            raise TranslationValidationException(
                f"Translation validation failed: output contains {chinese_ratio:.1%} Chinese characters",
                details={
                    "chinese_ratio": f"{chinese_ratio:.2%}",
                    "chinese_chars": chinese_chars,
                    "total_chars": len(translated_content)
                }
            )

        # Create result
        result = {
            "translated_markdown": translated_content,
            "metadata": {
                "provider_used": provider_name,
                "model_used": model_name,
                "glossary_applied": glossary is not None,
                "warnings": []
            }
        }

        # Update job storage
        job_storage[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "end_time": asyncio.get_event_loop().time(),
            "result": result
        })

        # Send completion notification
        await manager.send_completed(job_id, result)

    except Exception as e:
        # Update job with error
        error_msg = str(e)
        print(f"❌ Translation failed for job {job_id}: {error_msg}")
        import traceback
        traceback.print_exc()

        job_storage[job_id].update({
            "status": "error",
            "progress": 0.0,
            "end_time": asyncio.get_event_loop().time(),
            "error": error_msg
        })

        # Send error notification
        await manager.send_error(job_id, "TRANSLATION_ERROR", error_msg)