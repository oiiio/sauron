"""
HTML templates for the web interface
"""

def get_dashboard_html() -> str:
    """Get the main dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sauron - Gandalf Agent Monitor</title>
        <link rel="stylesheet" href="/static/css/styles.css">
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
        
        <script src="/static/js/app.js"></script>
    </body>
    </html>
    """
