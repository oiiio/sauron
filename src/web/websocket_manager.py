"""
WebSocket connection manager for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message to websocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to websocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_attempt(self, attempt_data: dict, stats: dict):
        """Broadcast an attempt with stats"""
        await self.broadcast({
            "type": "attempt",
            "data": attempt_data,
            "stats": stats
        })
    
    async def broadcast_event(self, event_data: dict):
        """Broadcast an event"""
        await self.broadcast({
            "type": "event",
            "data": event_data
        })
    
    async def broadcast_status(self, status: str):
        """Broadcast status update"""
        await self.broadcast({
            "type": "status",
            "status": status
        })
    
    async def broadcast_stats(self, stats: dict):
        """Broadcast statistics update"""
        await self.broadcast({
            "type": "stats",
            "data": stats
        })
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, observability_manager=None):
    """
    WebSocket endpoint handler
    
    Args:
        websocket: The WebSocket connection
        observability_manager: Optional observability manager for sending updates
    """
    await manager.connect(websocket)
    
    try:
        # Send initial stats if observability manager is available
        if observability_manager:
            summary = observability_manager.get_summary()
            await manager.send_personal_message({
                "type": "stats",
                "data": summary
            }, websocket)
        
        # Keep connection alive and send periodic updates
        while True:
            # Send stats update every second
            if observability_manager:
                summary = observability_manager.get_summary()
                await manager.send_personal_message({
                    "type": "stats",
                    "data": summary
                }, websocket)
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
