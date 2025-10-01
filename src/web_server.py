"""
Refactored web server for Sauron - Gandalf Agent Monitor
Uses modular architecture for better maintainability and extensibility
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .web.routes import router
from .web.websocket_manager import websocket_endpoint, manager
from .web.templates import get_dashboard_html
from .web.routes import observability


# Create FastAPI app
app = FastAPI(
    title="Sauron - Gandalf Agent Monitor",
    description="Real-time monitoring interface for the Gandalf agent system",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    return get_dashboard_html()


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_endpoint(websocket, observability)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": manager.get_connection_count()
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Sauron web server starting...")
    print(f"📁 Static files: {static_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 Sauron web server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
