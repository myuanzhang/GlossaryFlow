"""
FastAPI Main Application

Document Translation and Rewrite API Server
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.endpoints import translation, rewrite, health, providers
from api.websocket import manager
from core.config import config

# Job storage (in-memory for now, will be replaced with database)
job_storage: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Document Translation API...")
    print(f"📊 Default Provider: {config.provider}")
    print(f"🔧 Available Models: {config.openai_models}")

    yield

    # Shutdown
    print("🛑 Shutting down Document Translation API...")


# Create FastAPI application
app = FastAPI(
    title="Document Translation API",
    description="Multi-Agent document translation and rewrite API",
    version="3.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(translation.router, prefix="/api/v1", tags=["Translation"])
app.include_router(rewrite.router, prefix="/api/v1", tags=["Rewrite"])


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket, job_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await manager.connect(websocket, job_id)
    try:
        # Keep connection alive and wait for messages
        while True:
            # Wait for client messages (ping, etc.)
            data = await websocket.receive_text()
            # Optionally handle client messages here
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        print(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc)
            }
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Document Translation API",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Make job storage available to other modules
def get_job_storage() -> Dict[str, Dict[str, Any]]:
    """Get job storage dictionary"""
    return job_storage


# Dependency for job storage
async def get_job_storage_dep():
    """Dependency to get job storage"""
    return job_storage


if __name__ == "__main__":
    import uvicorn

    print("🌐 Starting Document Translation API Server...")
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )