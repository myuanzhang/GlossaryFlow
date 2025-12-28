#!/usr/bin/env python3
"""
GlossaryFlow Web Server Entry Point

This is the recommended way to start the web service.
Usage: python run_web.py
"""

import uvicorn


def main():
    """Start the FastAPI web server"""
    print("🌐 Starting GlossaryFlow Web Server...")
    print("📊 Backend will run on http://localhost:8000")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/api/v1/health")
    print("\n⚠️  Make sure frontend is running separately:")
    print("   cd frontend && npm run dev")
    print("\n" + "="*60 + "\n")

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
