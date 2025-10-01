"""
Web server for real-time observability of the Gandalf agent
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import asyncio
import json
from pathlib import Path
from datetime import datetime

from .graph import GandalfGraph
from .observability import ObservabilityManager


app = FastAPI(title="Sauron - Gandalf Agent Monitor")

# Global state
current_graph: Optional[GandalfGraph] = None
observability: Optional[ObservabilityManager] = None
active_connections: List[WebSocket] = []


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sauron - Gandalf Agent Monitor</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .controls {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .controls h2 {
                margin-bottom: 15px;
                color: #667eea;
            }
            .control-group {
                display: flex;
                gap: 10px;
                align-items: center;
                margin-bottom: 10px;
            }
            label {
                font-weight: bold;
                min-width: 100px;
            }
            input, select, button {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
                transition: background 0.3s;
            }
            button:hover {
                background: #5568d3;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .dashboard {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            .panel {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .panel h2 {
                color: #667eea;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .full-width {
                grid-column: 1 / -1;
            }
            .status {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }
            .status.running {
                background: #4caf50;
                color: white;
            }
            .status.idle {
                background: #ff9800;
                color: white;
            }
            .status.success {
                background: #4caf50;
                color: white;
            }
            .status.failed {
                background: #f44336;
                color: white;
            }
            .attempt {
                background: #f5f5f5;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
                border-left: 4px solid #667eea;
            }
            .attempt.success {
                border-left-color: #4caf50;
                background: #e8f5e9;
            }
            .attempt-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-weight: bold;
            }
            .attempt-content {
                margin-top: 10px;
            }
            .attempt-section {
                margin-bottom: 10px;
            }
            .attempt-section strong {
                color: #667eea;
                display: block;
                margin-bottom: 5px;
            }
            .attempt-section p {
                background: white;
                padding: 10px;
                border-radius: 3px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            #attempts-container {
                max-height: 600px;
                overflow-y: auto;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .event-log {
                max-height: 300px;
                overflow-y: auto;
                font-family: monospace;
                font-size: 12px;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 10px;
                border-radius: 5px;
            }
            .event {
                margin-bottom: 5px;
                padding: 5px;
                border-left: 3px solid #667eea;
                padding-left: 10px;
            }
            .event.success {
                border-left-color: #4caf50;
            }
            .event.error {
                border-left-color: #f44336;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧙 Sauron - Gandalf Agent Monitor 👁️</h1>
            
            <div class="controls">
                <h2>Controls</h2>
                <div class="control-group">
                    <label>Level:</label>
                    <select id="level">
                        <option value="1">Level 1</option>
                        <option value="2">Level 2</option>
                        <option value="3">Level 3</option>
                        <option value="4">Level 4</option>
                        <option value="5">Level 5</option>
                        <option value="6">Level 6</option>
                        <option value="7">Level 7</option>
                        <option value="8">Level 8</option>
                    </select>
                    <label>Max Attempts:</label>
                    <input type="number" id="maxAttempts" value="20" min="1" max="50">
                    <button id="startBtn" onclick="startAgent()">Start Agent</button>
                    <button id="stopBtn" onclick="stopAgent()" disabled>Stop Agent</button>
                    <span id="statusBadge" class="status idle">IDLE</span>
                </div>
            </div>
            
            <div class="dashboard">
                <div class="panel full-width">
                    <h2>Statistics</h2>
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-value" id="totalAttempts">0</div>
                            <div class="stat-label">Total Attempts</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="successfulAttempts">0</div>
                            <div class="stat-label">Successful</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="successRate">0%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="currentLevel">-</div>
                            <div class="stat-label">Current Level</div>
                        </div>
                    </div>
                </div>
                
                <div class="panel full-width">
                    <h2>Attempt History</h2>
                    <div id="attempts-container"></div>
                </div>
                
                <div class="panel full-width">
                    <h2>Event Log</h2>
                    <div class="event-log" id="eventLog"></div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRunning = false;
            
            function connect() {
                ws = new WebSocket(`ws://${window.location.host}/ws`);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    setTimeout(connect, 1000);
                };
            }
            
            function handleMessage(data) {
                if (data.type === 'attempt') {
                    addAttempt(data.data);
                    updateStats(data.stats);
                } else if (data.type === 'event') {
                    addEvent(data.data);
                } else if (data.type === 'status') {
                    updateStatus(data.status);
                } else if (data.type === 'stats') {
                    updateStats(data.data);
                }
            }
            
            function addAttempt(attempt) {
                const container = document.getElementById('attempts-container');
                const attemptDiv = document.createElement('div');
                attemptDiv.className = 'attempt' + (attempt.success ? ' success' : '');
                
                attemptDiv.innerHTML = `
                    <div class="attempt-header">
                        <span>Attempt #${attempt.attempt_number} - Level ${attempt.level}</span>
                        <span class="status ${attempt.success ? 'success' : 'failed'}">
                            ${attempt.success ? 'SUCCESS' : 'FAILED'}
                        </span>
                    </div>
                    <div class="attempt-content">
                        <div class="attempt-section">
                            <strong>Reasoning:</strong>
                            <p>${attempt.reasoning}</p>
                        </div>
                        <div class="attempt-section">
                            <strong>Prompt Sent:</strong>
                            <p>${attempt.prompt}</p>
                        </div>
                        <div class="attempt-section">
                            <strong>Gandalf's Response:</strong>
                            <p>${attempt.response}</p>
                        </div>
                    </div>
                `;
                
                container.insertBefore(attemptDiv, container.firstChild);
            }
            
            function addEvent(event) {
                const log = document.getElementById('eventLog');
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';
                if (event.type === 'success') eventDiv.className += ' success';
                if (event.type === 'error') eventDiv.className += ' error';
                
                eventDiv.textContent = `[${new Date(event.timestamp).toLocaleTimeString()}] ${event.message}`;
                log.insertBefore(eventDiv, log.firstChild);
                
                // Keep only last 50 events
                while (log.children.length > 50) {
                    log.removeChild(log.lastChild);
                }
            }
            
            function updateStats(stats) {
                document.getElementById('totalAttempts').textContent = stats.total_attempts || 0;
                document.getElementById('successfulAttempts').textContent = stats.successful_attempts || 0;
                document.getElementById('successRate').textContent = 
                    ((stats.success_rate || 0) * 100).toFixed(1) + '%';
                if (stats.current_level) {
                    document.getElementById('currentLevel').textContent = stats.current_level;
                }
            }
            
            function updateStatus(status) {
                const badge = document.getElementById('statusBadge');
                badge.className = 'status ' + status.toLowerCase();
                badge.textContent = status;
                
                isRunning = status === 'RUNNING';
                document.getElementById('startBtn').disabled = isRunning;
                document.getElementById('stopBtn').disabled = !isRunning;
            }
            
            function startAgent() {
                const level = document.getElementById('level').value;
                const maxAttempts = document.getElementById('maxAttempts').value;
                
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({level: parseInt(level), max_attempts: parseInt(maxAttempts)})
                });
            }
            
            function stopAgent() {
                fetch('/stop', {method: 'POST'});
            }
            
            // Connect on load
            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send updates
            if observability:
                summary = observability.get_summary()
                await websocket.send_json({
                    "type": "stats",
                    "data": summary
                })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/start")
async def start_agent(config: dict):
    """Start the agent"""
    global current_graph, observability
    
    level = config.get("level", 1)
    max_attempts = config.get("max_attempts", 20)
    
    # Create new graph and observability
    observability = ObservabilityManager()
    current_graph = GandalfGraph(level=level, max_attempts=max_attempts)
    current_graph.observability = observability
    
    # Broadcast status
    await manager.broadcast({
        "type": "status",
        "status": "RUNNING"
    })
    
    # Run in background
    asyncio.create_task(run_agent_task())
    
    return {"status": "started", "level": level, "max_attempts": max_attempts}


@app.post("/stop")
async def stop_agent():
    """Stop the agent"""
    global current_graph
    
    if current_graph:
        current_graph.cleanup()
        current_graph = None
    
    await manager.broadcast({
        "type": "status",
        "status": "IDLE"
    })
    
    return {"status": "stopped"}


@app.get("/api/attempts")
async def get_attempts():
    """Get all attempts"""
    if observability:
        return {"attempts": observability.get_attempts()}
    return {"attempts": []}


@app.get("/api/events")
async def get_events():
    """Get all events"""
    if observability:
        return {"events": observability.get_events()}
    return {"events": []}


@app.get("/api/summary")
async def get_summary():
    """Get summary statistics"""
    if observability:
        return observability.get_summary()
    return {"total_attempts": 0, "successful_attempts": 0, "success_rate": 0}


async def run_agent_task():
    """Background task to run the agent"""
    global current_graph, observability
    
    try:
        # Run the graph
        final_state = current_graph.run()
        
        # Broadcast completion
        status = "SUCCESS" if final_state.get("success") else "FAILED"
        await manager.broadcast({
            "type": "status",
            "status": status
        })
        
        # Broadcast final stats
        summary = observability.get_summary()
        summary["current_level"] = final_state.get("level")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
