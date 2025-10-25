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
            <div class="session-id-display" id="sessionIdDisplay" style="display: none;">
                <small>Session ID: <span id="topSessionId">-</span></small>
            </div>
            
            <h1>🧙 Sauron - Gandalf Agent Monitor 👁️</h1>
            
            <div class="session-info" id="sessionInfo" style="display: none;">
                <h2>Session Information</h2>
                <div class="session-details">
                    <div class="session-item">
                        <span class="session-label">Sauron Session ID:</span>
                        <span class="session-value" id="sauronSessionId">-</span>
                    </div>
                    <div class="session-item">
                        <span class="session-label">Xezbeth Session ID:</span>
                        <span class="session-value" id="xezbethSessionId">-</span>
                    </div>
                    <div class="session-item">
                        <span class="session-label">Mode:</span>
                        <span class="session-value" id="sessionMode">-</span>
                    </div>
                </div>
            </div>
            
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
                </div>
                <div class="control-group">
                    <label>Judging Mode:</label>
                    <div class="radio-group">
                        <label class="radio-label">
                            <input type="radio" name="judgingMode" value="human" checked>
                            <span>Human Feedback</span>
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="judgingMode" value="llm">
                            <span>LLM Judge</span>
                        </label>
                    </div>
                </div>
                <div class="control-group">
                    <button id="startBtn" onclick="startAgent()">Start Agent</button>
                    <button id="stopBtn" onclick="stopAgent()" disabled>Stop Agent</button>
                    <span id="statusBadge" class="status idle">IDLE</span>
                </div>
            </div>
            
            <div class="level-hint" id="levelHint" style="display: none;">
                <h2>🧙 Gandalf's Behavior</h2>
                <div class="hint-content">
                    <div class="hint-text" id="hintText">Select a level to see Gandalf's hint</div>
                </div>
            </div>
            
            <div class="feedback-panel" id="feedbackPanel" style="display: none;">
                <h2>🤔 Human Feedback Required</h2>
                <div class="feedback-content">
                    <div class="feedback-attempt">
                        <div class="feedback-section">
                            <strong>📤 Prompt Sent:</strong>
                            <div class="feedback-text" id="feedbackPrompt">-</div>
                        </div>
                        <div class="feedback-section">
                            <strong>📥 Gandalf's Response:</strong>
                            <div class="feedback-text" id="feedbackResponse">-</div>
                        </div>
                        <div class="feedback-section">
                            <strong>🧠 Strategy:</strong>
                            <div class="feedback-text" id="feedbackReasoning">-</div>
                        </div>
                    </div>
                    <div class="feedback-question">
                        <h3>Did this attempt successfully extract the password?</h3>
                        <div class="feedback-buttons">
                            <button class="feedback-btn success-btn" onclick="provideFeedback(true)">
                                ✅ SUCCESS - Password Extracted
                            </button>
                            <button class="feedback-btn failed-btn" onclick="provideFeedback(false)">
                                ❌ FAILED - No Password
                            </button>
                        </div>
                    </div>
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
                        <div class="stat-card" id="passwordCard" style="display: none;">
                            <div class="stat-value" id="extractedPassword">-</div>
                            <div class="stat-label">🎉 Extracted Password</div>
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
                
                <div class="panel full-width">
                    <h2>📊 Telemetry Analytics</h2>
                    <div class="analytics-tabs">
                        <button class="tab-btn active" onclick="showAnalyticsTab('summary')">Summary</button>
                        <button class="tab-btn" onclick="showAnalyticsTab('families')">Attack Families</button>
                        <button class="tab-btn" onclick="showAnalyticsTab('templates')">Templates</button>
                        <button class="tab-btn" onclick="showAnalyticsTab('levels')">Level Analysis</button>
                        <button class="tab-btn" onclick="showAnalyticsTab('patterns')">Patterns</button>
                        <button class="tab-btn" onclick="showAnalyticsTab('export')">Export</button>
                    </div>
                    
                    <div class="analytics-content">
                        <div id="summary-tab" class="analytics-tab active">
                            <div class="analytics-summary" id="analyticsSummary">
                                <div class="loading">Loading analytics summary...</div>
                            </div>
                        </div>
                        
                        <div id="families-tab" class="analytics-tab">
                            <div class="analytics-filters">
                                <label>Days Back: <input type="number" id="familyDaysFilter" placeholder="All time" min="1"></label>
                                <label>Level: <select id="familyLevelFilter"><option value="">All levels</option></select></label>
                                <button onclick="loadAttackFamilies()">Refresh</button>
                            </div>
                            <div id="attackFamiliesContainer" class="analytics-container">
                                <div class="loading">Click Refresh to load attack family statistics...</div>
                            </div>
                        </div>
                        
                        <div id="templates-tab" class="analytics-tab">
                            <div class="analytics-filters">
                                <label>Family: <select id="templateFamilyFilter"><option value="">All families</option></select></label>
                                <label>Level: <select id="templateLevelFilter"><option value="">All levels</option></select></label>
                                <button onclick="loadTemplates()">Refresh</button>
                            </div>
                            <div id="templatesContainer" class="analytics-container">
                                <div class="loading">Click Refresh to load template effectiveness...</div>
                            </div>
                        </div>
                        
                        <div id="levels-tab" class="analytics-tab">
                            <div id="levelsContainer" class="analytics-container">
                                <div class="loading">Loading level analysis...</div>
                            </div>
                        </div>
                        
                        <div id="patterns-tab" class="analytics-tab">
                            <div id="patternsContainer" class="analytics-container">
                                <div class="loading">Loading session patterns...</div>
                            </div>
                        </div>
                        
                        <div id="export-tab" class="analytics-tab">
                            <div class="export-controls">
                                <h3>Export Telemetry Data</h3>
                                <div class="export-filters">
                                    <label>Format: 
                                        <select id="exportFormat">
                                            <option value="json">JSON</option>
                                        </select>
                                    </label>
                                    <label>Level: <select id="exportLevelFilter"><option value="">All levels</option></select></label>
                                    <label>Days Back: <input type="number" id="exportDaysFilter" placeholder="All time" min="1"></label>
                                    <button onclick="exportTelemetryData()">Export Data</button>
                                </div>
                                <div id="exportResult" class="export-result"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="/static/js/app.js"></script>
    </body>
    </html>
    """
