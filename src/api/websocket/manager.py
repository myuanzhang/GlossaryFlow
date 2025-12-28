"""
WebSocket Connection Manager

Manages WebSocket connections for real-time progress updates.
"""

import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for job progress updates"""

    def __init__(self):
        # Dictionary mapping job_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        print(f"🔌 WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        print(f"🔌 WebSocket disconnected for job {job_id}")

    async def send_personal_message(self, message: Dict[str, Any], job_id: str):
        """Send a message to all connections for a specific job"""
        if job_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected_connections.append(connection)

            # Remove disconnected connections
            for connection in disconnected_connections:
                self.disconnect(connection, job_id)

    async def broadcast_progress(self, job_id: str, progress: float, phase: str, message: str = None):
        """Send progress update to all connections for a job"""
        await self.send_personal_message({
            "type": "progress_update",
            "job_id": job_id,
            "progress": progress,
            "phase": phase,
            "phase_progress": progress,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }, job_id)

    async def send_status_update(self, job_id: str, status: str, progress: float = None):
        """Send status update to all connections for a job"""
        message = {
            "type": "status_update",
            "job_id": job_id,
            "status": status,
            "timestamp": asyncio.get_event_loop().time()
        }
        if progress is not None:
            message["progress"] = progress

        await self.send_personal_message(message, job_id)

    async def send_warning(self, job_id: str, warning_message: str):
        """Send warning to all connections for a job"""
        await self.send_personal_message({
            "type": "warning",
            "job_id": job_id,
            "message": warning_message,
            "timestamp": asyncio.get_event_loop().time()
        }, job_id)

    async def send_completed(self, job_id: str, result: Dict[str, Any]):
        """Send completion message to all connections for a job"""
        await self.send_personal_message({
            "type": "completed",
            "job_id": job_id,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }, job_id)

    async def send_error(self, job_id: str, error_code: str, error_message: str, details: Any = None):
        """Send error message to all connections for a job"""
        await self.send_personal_message({
            "type": "error",
            "job_id": job_id,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": details
            },
            "timestamp": asyncio.get_event_loop().time()
        }, job_id)

    def get_connection_count(self, job_id: str) -> int:
        """Get number of active connections for a job"""
        return len(self.active_connections.get(job_id, []))


# Global connection manager instance
manager = ConnectionManager()