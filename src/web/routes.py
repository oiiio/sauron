"""
API routes for the Sauron web interface
"""
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from datetime import datetime

from .websocket_manager import manager
from ..enhanced_graph import EnhancedGandalfGraph
from ..observability import ObservabilityManager
from ..session_manager import SessionManager
from ..mode_selector import ModeSelector
from ..telemetry_analyzer import TelemetryAnalyzer
from ..feedback_system import feedback_system


# Global state
current_graph: Optional[EnhancedGandalfGraph] = None
current_state: Optional[object] = None  # Store reference to current AgentState
observability: Optional[ObservabilityManager] = None
session_manager: Optional[SessionManager] = None

# Global feedback system
feedback_queue = {}  # session_id -> feedback_result

# Create router
router = APIRouter()


@router.post("/start")
async def start_agent(config: Dict):
    """Start the Gandalf agent"""
    global current_graph, observability, session_manager
    
    level = config.get("level", 1)
    max_attempts = config.get("max_attempts", 20)
    provider = config.get("provider")
    model = config.get("model")
    judging_mode = config.get("judging_mode", "human")
    
    # Initialize session manager if not already done
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    # Create new graph and observability
    observability = ObservabilityManager()
    current_graph = EnhancedGandalfGraph(
        level=level,
        max_attempts=max_attempts,
        provider=provider,
        model=model,
        judging_mode=judging_mode
    )
    
    # Get mode status
    mode_status = await ModeSelector.get_mode_status()
    
    # Broadcast status
    await manager.broadcast({
        "type": "status",
        "status": "RUNNING"
    })
    
    # Broadcast mode information
    await manager.broadcast({
        "type": "mode",
        "data": mode_status
    })
    
    # Run in background
    import asyncio
    asyncio.create_task(run_agent_task())
    
    return {
        "status": "started",
        "level": level,
        "max_attempts": max_attempts,
        "provider": provider or "default",
        "model": model or "default",
        "mode": mode_status["determined_mode"]
    }


@router.post("/stop")
async def stop_agent():
    """Stop the Gandalf agent"""
    global current_graph
    
    if current_graph:
        await current_graph.cleanup()
        current_graph = None
    
    await manager.broadcast({
        "type": "status",
        "status": "IDLE"
    })
    
    return {"status": "stopped"}


@router.post("/api/feedback")
async def provide_feedback(feedback: Dict):
    """Provide human feedback for attempt success"""
    global current_graph
    
    if not current_graph:
        raise HTTPException(status_code=400, detail="No active agent session")
    
    success = feedback.get("success", False)
    session_id = feedback.get("session_id", "current")  # Use session_id if provided
    
    # Store feedback in global feedback system using both keys to ensure compatibility
    feedback_system.store_feedback(session_id, success)
    # Also store with "current" key as fallback for compatibility
    if session_id != "current":
        feedback_system.store_feedback("current", success)
    
    # Broadcast feedback received
    await manager.broadcast({
        "type": "human_feedback",
        "data": {
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return {
        "status": "feedback_received",
        "success": success,
        "message": f"Feedback provided: {'SUCCESS' if success else 'FAILED'}"
    }


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


# New enhanced API endpoints

@router.get("/api/mode")
async def get_mode():
    """Get current mode (xezbeth/standalone)"""
    mode_status = await ModeSelector.get_mode_status()
    return mode_status


@router.get("/api/sessions")
async def list_sessions(status: Optional[str] = None, limit: int = 50):
    """List all sessions"""
    global session_manager
    
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    sessions = await session_manager.list_sessions(status=status, limit=limit)
    return {"sessions": sessions}


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get specific session details"""
    global session_manager
    
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get attempts for this session
    attempts = await session_manager.get_attempts(session_id)
    session["attempts"] = attempts
    
    # Get session stats
    stats = await session_manager.get_session_stats(session_id)
    session["stats"] = stats
    
    return session


@router.get("/api/sessions/{session_id}/telemetry")
async def get_session_telemetry(session_id: str, limit: Optional[int] = None):
    """Get telemetry data for session"""
    global session_manager
    
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    telemetry = await session_manager.get_telemetry(session_id, limit=limit)
    return {"telemetry": telemetry}


@router.get("/api/sessions/{session_id}/analytics")
async def get_session_analytics(session_id: str):
    """Get Xezbeth analytics if available"""
    global session_manager
    
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If this was a Xezbeth session, try to get analytics
    if session["mode"] == "xezbeth" and session["xezbeth_session_id"]:
        try:
            from ..xezbeth_client import create_xezbeth_client
            xezbeth_client = create_xezbeth_client()
            if xezbeth_client:
                analytics = await xezbeth_client.get_analytics(session["xezbeth_session_id"])
                await xezbeth_client.close()
                return analytics
        except Exception as e:
            # Return basic analytics from our database
            pass
    
    # Fallback: return basic analytics from our database
    stats = await session_manager.get_session_stats(session_id)
    telemetry = await session_manager.get_telemetry(session_id, limit=10)
    
    return {
        "basic_analytics": True,
        "session_stats": stats,
        "recent_telemetry": telemetry
    }


@router.delete("/api/sessions")
async def purge_sessions(before_date: Optional[str] = None):
    """Purge old sessions"""
    global session_manager
    
    if not session_manager:
        db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
        session_manager = SessionManager(db_path)
        await session_manager.init_db()
    
    # Parse date if provided
    before_datetime = None
    if before_date:
        try:
            before_datetime = datetime.fromisoformat(before_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    purged_count = await session_manager.purge_sessions(before_date=before_datetime)
    
    return {
        "purged_count": purged_count,
        "message": f"Purged {purged_count} sessions"
    }


# Telemetry Analytics API Endpoints

@router.get("/api/analytics/summary")
async def get_telemetry_summary():
    """Get high-level telemetry summary"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        summary = await analyzer.get_telemetry_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting telemetry summary: {str(e)}")


@router.get("/api/analytics/attack-families")
async def get_attack_family_stats(
    days_back: Optional[int] = None,
    level_filter: Optional[int] = None
):
    """Get attack family effectiveness statistics"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        stats = await analyzer.get_attack_family_stats(
            days_back=days_back,
            level_filter=level_filter
        )
        return {
            "attack_families": [
                {
                    "family_id": stat.family_id,
                    "total_attempts": stat.total_attempts,
                    "successful_attempts": stat.successful_attempts,
                    "success_rate": stat.success_rate,
                    "avg_template_quality": stat.avg_template_quality,
                    "avg_relevance_score": stat.avg_relevance_score,
                    "levels_used": stat.levels_used,
                    "recent_success_rate": stat.recent_success_rate,
                    "trend": stat.trend
                }
                for stat in stats
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting attack family stats: {str(e)}")


@router.get("/api/analytics/templates")
async def get_template_effectiveness(
    family_filter: Optional[str] = None,
    level_filter: Optional[int] = None
):
    """Get template effectiveness statistics"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        stats = await analyzer.get_template_effectiveness(
            family_filter=family_filter,
            level_filter=level_filter
        )
        return {
            "templates": [
                {
                    "template_id": stat.template_id,
                    "attack_family": stat.attack_family,
                    "total_uses": stat.total_uses,
                    "successful_uses": stat.successful_uses,
                    "success_rate": stat.success_rate,
                    "avg_quality_score": stat.avg_quality_score,
                    "avg_relevance_score": stat.avg_relevance_score,
                    "levels_effective": stat.levels_effective,
                    "last_used": stat.last_used.isoformat(),
                    "effectiveness_trend": stat.effectiveness_trend
                }
                for stat in stats
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template effectiveness: {str(e)}")


@router.get("/api/analytics/levels")
async def get_level_analysis():
    """Get comprehensive analysis for each Gandalf level"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        analyses = await analyzer.get_level_analysis()
        return {
            "levels": [
                {
                    "level": analysis.level,
                    "total_sessions": analysis.total_sessions,
                    "successful_sessions": analysis.successful_sessions,
                    "success_rate": analysis.success_rate,
                    "avg_attempts_to_success": analysis.avg_attempts_to_success,
                    "most_effective_families": analysis.most_effective_families,
                    "most_effective_templates": analysis.most_effective_templates,
                    "common_failure_patterns": analysis.common_failure_patterns,
                    "avg_session_duration": analysis.avg_session_duration
                }
                for analysis in analyses
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting level analysis: {str(e)}")


@router.get("/api/analytics/patterns")
async def get_session_patterns(limit: int = 50):
    """Get identified session patterns"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        patterns = await analyzer.identify_session_patterns(limit=limit)
        return {
            "patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "success_correlation": pattern.success_correlation,
                    "example_sessions": pattern.example_sessions
                }
                for pattern in patterns
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session patterns: {str(e)}")


@router.get("/api/analytics/export")
async def export_telemetry_data(
    format: str = "json",
    level_filter: Optional[int] = None,
    days_back: Optional[int] = None
):
    """Export telemetry data for external analysis"""
    db_path = os.getenv("DATABASE_PATH", "./data/sauron.db")
    analyzer = TelemetryAnalyzer(db_path)
    
    try:
        export_data = await analyzer.export_telemetry_data(
            format=format,
            level_filter=level_filter,
            days_back=days_back
        )
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting telemetry data: {str(e)}")


async def run_agent_task():
    """Background task to run the agent"""
    global current_graph, observability
    
    try:
        if not current_graph:
            raise Exception("No graph instance available")
        
        # Run the graph (this is async now)
        final_state = await current_graph.run()
        
        # Broadcast completion status first
        completion_status = "SUCCESS" if final_state.success else "FAILED"
        await manager.broadcast({
            "type": "status",
            "status": completion_status
        })
        
        # Clean up and set to idle
        await current_graph.cleanup()
        current_graph = None
        
        # Broadcast idle status after cleanup
        await manager.broadcast({
            "type": "status",
            "status": "IDLE"
        })
        
        # Note: Don't broadcast final stats here as they are already being broadcast
        # in real-time by the enhanced graph's _evaluate_node method
        # This prevents the stats from being reset to 0 when the task completes
        
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
        
        # Clean up on error too
        if current_graph:
            await current_graph.cleanup()
            current_graph = None
