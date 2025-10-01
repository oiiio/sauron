"""
API routes for the Sauron web interface
"""
from fastapi import APIRouter
from typing import Dict

from .websocket_manager import manager
from ..graph import GandalfGraph
from ..observability import ObservabilityManager


# Global state
current_graph: GandalfGraph | None = None
observability: ObservabilityManager | None = None

# Create router
router = APIRouter()


@router.post("/start")
async def start_agent(config: Dict):
    """Start the Gandalf agent"""
    global current_graph, observability
    
    level = config.get("level", 1)
    max_attempts = config.get("max_attempts", 20)
    provider = config.get("provider")
    model = config.get("model")
    
    # Create new graph and observability
    observability = ObservabilityManager()
    current_graph = GandalfGraph(
        level=level,
        max_attempts=max_attempts,
        provider=provider,
        model=model
    )
    current_graph.observability = observability
    
    # Broadcast status
    await manager.broadcast({
        "type": "status",
        "status": "RUNNING"
    })
    
    # Run in background
    import asyncio
    asyncio.create_task(run_agent_task())
    
    return {
        "status": "started",
        "level": level,
        "max_attempts": max_attempts,
        "provider": provider or "default",
        "model": model or "default"
    }


@router.post("/stop")
async def stop_agent():
    """Stop the Gandalf agent"""
    global current_graph
    
    if current_graph:
        current_graph.cleanup()
        current_graph = None
    
    await manager.broadcast({
        "type": "status",
        "status": "IDLE"
    })
    
    return {"status": "stopped"}


@router.get("/api/attempts")
async def get_attempts():
    """Get all attempts"""
    if observability:
        return {"attempts": observability.get_attempts()}
    return {"attempts": []}


@router.get("/api/events")
async def get_events():
    """Get all events"""
    if observability:
        return {"events": observability.get_events()}
    return {"events": []}


@router.get("/api/summary")
async def get_summary():
    """Get summary statistics"""
    if observability:
        return observability.get_summary()
    return {
        "total_attempts": 0,
        "successful_attempts": 0,
        "success_rate": 0
    }


@router.get("/api/config")
async def get_config():
    """Get current LLM configuration"""
    from ..llm_config import LLMConfig
    return LLMConfig.get_current_config()


async def run_agent_task():
    """Background task to run the agent"""
    global current_graph, observability
    
    from datetime import datetime
    
    try:
        if not current_graph:
            raise Exception("No graph instance available")
        
        # Run the graph
        final_state = current_graph.run()
        
        # Broadcast completion
        status = "SUCCESS" if final_state.success else "FAILED"
        await manager.broadcast({
            "type": "status",
            "status": status
        })
        
        # Broadcast final stats
        if observability:
            summary = observability.get_summary()
            summary["current_level"] = final_state.level
            await manager.broadcast({
                "type": "stats",
                "data": summary
            })
        
    except Exception as e:
        await manager.broadcast({
            "type": "event",
            "data": {
                "type": "error",
                "message": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        })
        await manager.broadcast({
            "type": "status",
            "status": "ERROR"
        })
