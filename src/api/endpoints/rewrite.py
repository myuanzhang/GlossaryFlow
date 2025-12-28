"""
Rewrite Endpoint

Handles document rewrite requests with real-time progress updates.
"""

import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks

from agents.ai_rewrite_agent import AIRewriteAgent
from api.models.common import JobStartResponse
from api.websocket.manager import manager

router = APIRouter()


# In-memory job storage (will be replaced with database)
job_storage: Dict[str, Dict[str, Any]] = {}


@router.post("/rewrite", response_model=JobStartResponse)
async def start_rewrite(
    background_tasks: BackgroundTasks,
    source_markdown: str,
    strategy: Optional[str] = "line_by_line",
    document_context: Optional[Dict[str, Any]] = None,
    llm_config: Optional[Dict[str, Any]] = None
):
    """
    Start a document rewrite job
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job storage
        job_storage[job_id] = {
            "id": job_id,
            "status": "validating",
            "progress": 0.0,
            "source_markdown": source_markdown,
            "strategy": strategy,
            "document_context": document_context or {},
            "llm_config": llm_config or {},
            "start_time": None,
            "end_time": None,
            "result": None,
            "error": None
        }

        # Validate inputs
        if not source_markdown.strip():
            raise HTTPException(status_code=400, detail="Source markdown cannot be empty")

        # Create output directory
        output_dir = "rewritten_docs"

        # Start rewrite in background
        background_tasks.add_task(
            perform_rewrite,
            job_id,
            source_markdown,
            strategy,
            document_context or {},
            output_dir
        )

        return JobStartResponse(
            job_id=job_id,
            estimated_duration_ms=len(source_markdown) * 80  # Rough estimate
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start rewrite: {str(e)}")


@router.get("/rewrite/{job_id}/status")
async def get_rewrite_status(job_id: str):
    """
    Get the status of a rewrite job
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
        "result": job.get("result")
    }


@router.get("/rewrite/{job_id}/result")
async def get_rewrite_result(job_id: str):
    """
    Get the final rewrite result
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job["result"]:
        raise HTTPException(status_code=404, detail="Rewrite result not available")

    return job["result"]


@router.get("/rewrite/strategies")
async def list_rewrite_strategies():
    """
    List available rewrite strategies
    """
    try:
        # This would integrate with the strategy factory
        strategies = [
            {
                "name": "line_by_line",
                "description": "Line-by-line rewrite strategy",
                "description_detailed": "Rewrites document line by line, preserving structure"
            },
            {
                "name": "translation_oriented",
                "description": "Translation-oriented rewrite strategy",
                "description_detailed": "Optimizes Chinese documents for better machine translation"
            }
        ]

        return {
            "success": True,
            "strategies": strategies
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


async def perform_rewrite(
    job_id: str,
    source_markdown: str,
    strategy: str,
    document_context: Dict[str, Any],
    output_dir: str
):
    """
    Perform rewrite in background
    """
    try:
        # Update job status
        job_storage[job_id]["status"] = "processing"
        job_storage[job_id]["start_time"] = asyncio.get_event_loop().time()

        await manager.send_status_update(job_id, "processing", 0.0)

        # Create rewrite agent
        agent = AIRewriteAgent(output_dir)

        await manager.send_status_update(job_id, "processing", 10.0)

        # Perform rewrite
        result = agent.rewrite_and_save(source_markdown, document_context)

        await manager.send_status_update(job_id, "processing", 90.0)

        # Create result
        rewrite_result = {
            "rewritten_content": result["rewritten_content"],
            "metadata": {
                "strategy_used": strategy,
                "sentences_processed": result["sentences_processed"],
                "sentences_rewritten": result["sentences_rewritten"],
                "rewrite_rate": result["rewrite_rate"],
                "provider_used": result["provider_used"],
                "output_file": result.get("output_file"),
                "warnings": result.get("warnings", [])
            }
        }

        # Update job storage
        job_storage[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "end_time": asyncio.get_event_loop().time(),
            "result": rewrite_result
        })

        # Send completion notification
        await manager.send_completed(job_id, rewrite_result)

    except Exception as e:
        # Update job with error
        job_storage[job_id].update({
            "status": "error",
            "progress": 0.0,
            "end_time": asyncio.get_event_loop().time(),
            "error": str(e)
        })

        # Send error notification
        await manager.send_error(job_id, "REWRITE_ERROR", str(e))