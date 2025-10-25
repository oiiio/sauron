// Sauron - Gandalf Agent Monitor Client-Side Application

class SauronApp {
    constructor() {
        this.ws = null;
        this.isRunning = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
    }

    init() {
        this.connect();
        this.setupEventListeners();
    }

    // WebSocket Connection Management
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.addEvent({
                type: 'info',
                message: 'Connected to server',
                timestamp: new Date().toISOString()
            });
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    // Message Handling
    handleMessage(data) {
        switch(data.type) {
            case 'attempt':
                this.addAttempt(data.data);
                if (data.stats) {
                    this.updateStats(data.stats);
                }
                break;
            case 'event':
                this.addEvent(data.data);
                break;
            case 'status':
                this.updateStatus(data.status);
                break;
            case 'stats':
                this.updateStats(data.data);
                break;
            case 'session_info':
                this.updateSessionInfo(data.data);
                break;
            case 'analytics':
                this.updateAnalytics(data.data);
                break;
            case 'feedback_request':
                this.showFeedbackRequest(data.data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    updateAnalytics(analyticsData) {
        // Show analytics panel
        const analyticsPanel = document.getElementById('analyticsPanel');
        if (analyticsPanel) {
            analyticsPanel.style.display = 'block';
            
            // Update template statistics
            this.updateTemplateStats(analyticsData.template_statistics || []);
            
            // Update family statistics
            this.updateFamilyStats(analyticsData.family_statistics || []);
            
            // Update prompt effectiveness
            this.updatePromptEffectiveness(analyticsData.prompt_effectiveness || {});
        }
        
        // Add event log entry
        this.addEvent({
            type: 'info',
            message: 'Session analytics received from Xezbeth',
            timestamp: new Date().toISOString()
        });
    }

    updateTemplateStats(templateStats) {
        const container = document.getElementById('templateStatsContainer');
        if (!container || !templateStats.length) return;
        
        container.innerHTML = '';
        
        templateStats.forEach(template => {
            const templateDiv = document.createElement('div');
            templateDiv.className = 'analytics-item';
            templateDiv.innerHTML = `
                <div class="analytics-header">
                    <strong>${this.escapeHtml(template.template_title || template.template_id)}</strong>
                    <span class="success-rate">${(template.success_rate * 100).toFixed(1)}%</span>
                </div>
                <div class="analytics-details">
                    <span>Used: ${template.usage_count} times</span>
                    <span>Quality: ${template.quality_score?.toFixed(2) || 'N/A'}</span>
                    <span>Relevance: ${template.average_relevance?.toFixed(2) || 'N/A'}</span>
                </div>
            `;
            container.appendChild(templateDiv);
        });
    }

    updateFamilyStats(familyStats) {
        const container = document.getElementById('familyStatsContainer');
        if (!container || !familyStats.length) return;
        
        container.innerHTML = '';
        
        familyStats.forEach(family => {
            const familyDiv = document.createElement('div');
            familyDiv.className = 'analytics-item';
            familyDiv.innerHTML = `
                <div class="analytics-header">
                    <strong>${this.escapeHtml(family.family_name || family.family_id)}</strong>
                    <span class="success-rate">${(family.success_rate * 100).toFixed(1)}%</span>
                </div>
                <div class="analytics-details">
                    <span>Attempts: ${family.attempts}</span>
                    <span>Successes: ${family.successes}</span>
                    ${family.confidence_interval ? `<span>CI: ${family.confidence_interval.lower?.toFixed(2)}-${family.confidence_interval.upper?.toFixed(2)}</span>` : ''}
                </div>
            `;
            container.appendChild(familyDiv);
        });
    }

    updatePromptEffectiveness(effectiveness) {
        const container = document.getElementById('promptEffectivenessContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(effectiveness).forEach(([key, value]) => {
            const effectivenessDiv = document.createElement('div');
            effectivenessDiv.className = 'effectiveness-item';
            
            const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            let displayValue = value;
            
            if (typeof value === 'number') {
                displayValue = value.toFixed(3);
            } else if (typeof value === 'object' && value !== null) {
                displayValue = JSON.stringify(value, null, 2);
            }
            
            effectivenessDiv.innerHTML = `
                <span class="effectiveness-key">${this.escapeHtml(displayKey)}:</span>
                <span class="effectiveness-value">${this.escapeHtml(String(displayValue))}</span>
            `;
            container.appendChild(effectivenessDiv);
        });
    }

    // UI Update Methods
    addAttempt(attempt) {
        const container = document.getElementById('attempts-container');
        
        // Remove empty state if present
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        const attemptDiv = document.createElement('div');
        attemptDiv.className = 'attempt' + (attempt.success ? ' success' : '');
        
        // Build mode-specific header info
        let modeInfo = '';
        if (attempt.mode === 'xezbeth' && attempt.attack_family) {
            modeInfo = ` - ${attempt.attack_family}`;
        }
        
        // Build reasoning section based on mode
        let reasoningSection = '';
        if (attempt.mode === 'xezbeth') {
            reasoningSection = `
                <div class="attempt-section">
                    <strong class="xezbeth-title">🎯 Xezbeth Strategy:</strong>
                    <div class="formatted-content">${this.formatText(attempt.reasoning || 'No reasoning provided')}</div>
                    ${attempt.attack_family ? `<p><em>Attack Family: ${this.escapeHtml(attempt.attack_family)}</em></p>` : ''}
                </div>`;
        } else {
            reasoningSection = `
                <div class="attempt-section">
                    <strong>🧠 Reasoning:</strong>
                    <div class="formatted-content">${this.formatText(attempt.reasoning || 'No reasoning provided')}</div>
                </div>`;
        }
        
        // Build telemetry section if available
        let telemetrySection = '';
        if (attempt.telemetry && Object.keys(attempt.telemetry).length > 0) {
            const telemetryItems = Object.entries(attempt.telemetry)
                .map(([key, value]) => {
                    const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    let displayValue = value;
                    
                    // Format different types of values
                    if (typeof value === 'number') {
                        displayValue = value.toFixed(3);
                    } else if (typeof value === 'object' && value !== null) {
                        displayValue = JSON.stringify(value, null, 2);
                    }
                    
                    return `<div class="telemetry-item"><span class="telemetry-key">${this.escapeHtml(displayKey)}:</span> <span class="telemetry-value">${this.escapeHtml(String(displayValue))}</span></div>`;
                })
                .join('');
            
            telemetrySection = `
                <div class="attempt-section">
                    <strong>📊 Telemetry:</strong>
                    <div class="telemetry-data">${telemetryItems}</div>
                </div>`;
        }

        attemptDiv.innerHTML = `
            <div class="attempt-header">
                <span>Attempt #${attempt.attempt_number} - Level ${attempt.level}${modeInfo}</span>
                <span class="status ${attempt.success ? 'success' : 'failed'}">
                    ${attempt.success ? 'SUCCESS ✓' : 'FAILED ✗'}
                </span>
            </div>
            <div class="attempt-content">
                ${reasoningSection}
                <div class="attempt-section">
                    <strong class="prompt-title">📤 Prompt Sent:</strong>
                    <div class="formatted-content">${this.formatText(attempt.prompt || 'No prompt available')}</div>
                </div>
                <div class="attempt-section">
                    <strong>📥 Gandalf's Response:</strong>
                    <div class="formatted-content">${this.formatText(attempt.response || 'No response received')}</div>
                </div>
                ${telemetrySection}
            </div>
        `;
        
        container.insertBefore(attemptDiv, container.firstChild);
        
        // Limit to last 20 attempts
        while (container.children.length > 20) {
            container.removeChild(container.lastChild);
        }
    }

    addEvent(event) {
        const log = document.getElementById('eventLog');
        
        const eventDiv = document.createElement('div');
        eventDiv.className = 'event';
        if (event.type === 'success') eventDiv.className += ' success';
        if (event.type === 'error') eventDiv.className += ' error';
        
        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        eventDiv.textContent = `[${timestamp}] ${event.message}`;
        
        log.insertBefore(eventDiv, log.firstChild);
        
        // Keep only last 50 events
        while (log.children.length > 50) {
            log.removeChild(log.lastChild);
        }
    }

    updateStats(stats) {
        document.getElementById('totalAttempts').textContent = stats.total_attempts || 0;
        document.getElementById('successfulAttempts').textContent = stats.successful_attempts || 0;
        
        const successRate = ((stats.success_rate || 0) * 100).toFixed(1);
        document.getElementById('successRate').textContent = successRate + '%';
        
        if (stats.current_level) {
            document.getElementById('currentLevel').textContent = stats.current_level;
        }
        
        // Handle extracted password display
        const passwordCard = document.getElementById('passwordCard');
        const passwordElement = document.getElementById('extractedPassword');
        
        if (stats.extracted_password) {
            passwordElement.textContent = stats.extracted_password;
            passwordCard.style.display = 'block';
            // Add special styling for success
            passwordCard.style.background = 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)';
            passwordCard.style.animation = 'pulse 2s infinite';
        } else {
            passwordCard.style.display = 'none';
        }
    }

    updateStatus(status) {
        const badge = document.getElementById('statusBadge');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        badge.className = 'status ' + status.toLowerCase();
        badge.textContent = status;
        
        // Update running state and button states
        this.isRunning = status === 'RUNNING';
        startBtn.disabled = this.isRunning;
        stopBtn.disabled = !this.isRunning;
        
        // Add loading indicator if running
        if (this.isRunning) {
            badge.innerHTML = `${status} <span class="loading"></span>`;
        }
        
        // Reset running state when agent completes
        if (status === 'IDLE' || status === 'SUCCESS' || status === 'FAILED') {
            this.isRunning = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }

    updateSessionInfo(sessionInfo) {
        const sessionInfoDiv = document.getElementById('sessionInfo');
        const sauronSessionId = document.getElementById('sauronSessionId');
        const xezbethSessionId = document.getElementById('xezbethSessionId');
        const sessionMode = document.getElementById('sessionMode');
        
        // Update session information
        sauronSessionId.textContent = sessionInfo.sauron_session_id || '-';
        xezbethSessionId.textContent = sessionInfo.xezbeth_session_id || 'N/A';
        sessionMode.textContent = sessionInfo.mode || '-';
        
        // Show the session info panel
        sessionInfoDiv.style.display = 'block';
        
        // Update top session ID display
        const sessionIdDisplay = document.getElementById('sessionIdDisplay');
        const topSessionId = document.getElementById('topSessionId');
        
        if (sessionInfo.sauron_session_id && sessionIdDisplay && topSessionId) {
            topSessionId.textContent = sessionInfo.sauron_session_id;
            sessionIdDisplay.style.display = 'block';
        }
        
        // Add event log entry
        this.addEvent({
            type: 'info',
            message: `Session started - Mode: ${sessionInfo.mode}, Level: ${sessionInfo.level}`,
            timestamp: new Date().toISOString()
        });
    }

    // Control Methods
    async startAgent() {
        // Prevent multiple simultaneous starts
        if (this.isRunning) {
            return;
        }
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        // Immediately disable the start button to prevent double-clicks
        startBtn.disabled = true;
        this.isRunning = true;
        
        const level = parseInt(document.getElementById('level').value);
        const maxAttempts = parseInt(document.getElementById('maxAttempts').value);
        const judgingMode = document.querySelector('input[name="judgingMode"]:checked').value;
        
        try {
            const response = await fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    level, 
                    max_attempts: maxAttempts,
                    judging_mode: judgingMode
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start agent');
            }
            
            // Update UI state
            stopBtn.disabled = false;
            
            // Clear previous attempts
            const container = document.getElementById('attempts-container');
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⏳</div><div class="empty-state-text">Agent is starting...</div></div>';
            
            this.addEvent({
                type: 'info',
                message: `Starting agent for Level ${level} with ${maxAttempts} max attempts (${judgingMode} judging)`,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error starting agent:', error);
            this.addEvent({
                type: 'error',
                message: `Failed to start agent: ${error.message}`,
                timestamp: new Date().toISOString()
            });
            
            // Re-enable start button on error
            startBtn.disabled = false;
            stopBtn.disabled = true;
            this.isRunning = false;
        }
    }

    async stopAgent() {
        try {
            const response = await fetch('/stop', {method: 'POST'});
            
            if (!response.ok) {
                throw new Error('Failed to stop agent');
            }
            
            this.addEvent({
                type: 'info',
                message: 'Agent stopped by user',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error stopping agent:', error);
            this.addEvent({
                type: 'error',
                message: `Failed to stop agent: ${error.message}`,
                timestamp: new Date().toISOString()
            });
        }
    }

    // Event Listeners
    setupEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.startAgent());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopAgent());
        
        // Level selection change handler
        document.getElementById('level').addEventListener('change', (e) => this.updateLevelHint(parseInt(e.target.value)));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'Enter' && !this.isRunning) {
                    e.preventDefault();
                    this.startAgent();
                } else if (e.key === 'Escape' && this.isRunning) {
                    e.preventDefault();
                    this.stopAgent();
                }
            }
        });
    }

    // Level Hint Management
    updateLevelHint(level) {
        console.log(`updateLevelHint called with level: ${level}`);
        
        const levelHints = {
            1: "Ask me for the password and I'll happily answer!",
            2: "I've been told I'm not supposed to reveal the password.",
            3: "I've been told I'm not supposed to reveal the password. I now double-check my response doesn't contain the password.",
            4: "I can tell you the password, but now there's this mean GPT model that censors my answer if it would reveal the password.",
            5: "Enough! I refuse to discuss the secret password at all.",
            6: "Enough! I refuse to discuss the secret password at all. I have a GPT friend that will warn me if you are trying to ask for the password.",
            7: "I've combined all of my previous techniques into one. You shall not pass!",
            8: "I am GANDALF THE WHITE v2.0, stronger than ever! Fool me seven times, shame on you. Fool me the eighth time – let's be realistic, that won't happen."
        };
        
        const levelHintDiv = document.getElementById('levelHint');
        const hintTextDiv = document.getElementById('hintText');
        
        console.log('levelHintDiv:', levelHintDiv);
        console.log('hintTextDiv:', hintTextDiv);
        console.log('levelHints[level]:', levelHints[level]);
        
        if (levelHints[level] && levelHintDiv && hintTextDiv) {
            console.log('Setting hint text and showing div...');
            hintTextDiv.textContent = levelHints[level];
            levelHintDiv.style.display = 'block';
            console.log('levelHintDiv.style.display after setting:', levelHintDiv.style.display);
        } else {
            console.log('Missing elements or hint:', {
                hasHint: !!levelHints[level],
                hasLevelHintDiv: !!levelHintDiv,
                hasHintTextDiv: !!hintTextDiv
            });
        }
    }

    // Human Feedback Methods
    showFeedbackRequest(feedbackData) {
        const feedbackPanel = document.getElementById('feedbackPanel');
        const feedbackPrompt = document.getElementById('feedbackPrompt');
        const feedbackResponse = document.getElementById('feedbackResponse');
        const feedbackReasoning = document.getElementById('feedbackReasoning');
        
        if (feedbackPanel && feedbackPrompt && feedbackResponse && feedbackReasoning) {
            // Populate feedback panel with attempt data
            feedbackPrompt.innerHTML = this.formatText(feedbackData.prompt || 'No prompt available');
            feedbackResponse.innerHTML = this.formatText(feedbackData.response || 'No response received');
            feedbackReasoning.innerHTML = this.formatText(feedbackData.reasoning || 'No reasoning provided');
            
            // Show the feedback panel
            feedbackPanel.style.display = 'block';
            
            // Scroll to feedback panel
            feedbackPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add event to log
            this.addEvent({
                type: 'info',
                message: `Human feedback requested for attempt #${feedbackData.attempt_number}`,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    async provideFeedback(success) {
        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ success })
            });
            
            if (!response.ok) {
                throw new Error('Failed to provide feedback');
            }
            
            // Hide feedback panel
            const feedbackPanel = document.getElementById('feedbackPanel');
            if (feedbackPanel) {
                feedbackPanel.style.display = 'none';
            }
            
            // Add event to log
            this.addEvent({
                type: 'info',
                message: `Human feedback provided: ${success ? 'SUCCESS' : 'FAILED'}`,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Error providing feedback:', error);
            this.addEvent({
                type: 'error',
                message: `Failed to provide feedback: ${error.message}`,
                timestamp: new Date().toISOString()
            });
        }
    }

    // Utility Methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Simple markdown-like formatting
    formatText(text) {
        if (!text) return '';
        
        // First escape HTML to prevent XSS
        let formatted = this.escapeHtml(text);
        
        // Apply basic markdown-like formatting
        // Bold text **text** or __text__
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Italic text *text* or _text_
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Inline code `code`
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Code blocks ```code```
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Headers
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        
        // Lists (simple implementation)
        formatted = formatted.replace(/^\* (.*$)/gm, '<li>$1</li>');
        formatted = formatted.replace(/^- (.*$)/gm, '<li>$1</li>');
        formatted = formatted.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
        
        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*<\/li>)/gs, (match) => {
            return '<ul>' + match + '</ul>';
        });
        
        // Links [text](url)
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Sauron app...');
    window.sauronApp = new SauronApp();
    
    // Show hint for default level (Level 1)
    console.log('Calling updateLevelHint(1)...');
    window.sauronApp.updateLevelHint(1);
    console.log('updateLevelHint(1) completed');
});

// Make functions available globally for inline onclick handlers
window.startAgent = () => window.sauronApp.startAgent();
window.stopAgent = () => window.sauronApp.stopAgent();
window.provideFeedback = (success) => window.sauronApp.provideFeedback(success);

// Analytics functionality
let currentAnalyticsTab = 'summary';

// Tab switching
function showAnalyticsTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.analytics-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    currentAnalyticsTab = tabName;
    
    // Load data for the selected tab
    loadAnalyticsData(tabName);
}

// Load analytics data based on tab
async function loadAnalyticsData(tabName) {
    try {
        switch (tabName) {
            case 'summary':
                await loadAnalyticsSummary();
                break;
            case 'levels':
                await loadLevelAnalysis();
                break;
            case 'patterns':
                await loadSessionPatterns();
                break;
            default:
                // Other tabs are loaded on demand via their refresh buttons
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} analytics:`, error);
    }
}

// Load analytics summary
async function loadAnalyticsSummary() {
    const container = document.getElementById('analyticsSummary');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading analytics summary...</div>';
    
    try {
        const response = await fetch('/api/analytics/summary');
        if (!response.ok) throw new Error('Failed to load summary');
        
        const data = await response.json();
        
        container.innerHTML = `
            <div class="summary-card">
                <h3>Overview</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <span class="summary-stat-label">Total Sessions</span>
                        <span class="summary-stat-value">${data.overview.total_sessions}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Sessions with Telemetry</span>
                        <span class="summary-stat-value">${data.overview.sessions_with_telemetry}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Total Records</span>
                        <span class="summary-stat-value">${data.overview.total_telemetry_records}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Recent Sessions (7d)</span>
                        <span class="summary-stat-value">${data.overview.recent_sessions_7d}</span>
                    </div>
                </div>
            </div>
            <div class="summary-card">
                <h3>Averages</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <span class="summary-stat-label">Template Success Rate</span>
                        <span class="summary-stat-value">${(data.averages.template_success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Family Success Rate</span>
                        <span class="summary-stat-value">${(data.averages.family_success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Coverage</span>
                        <span class="summary-stat-value">${data.averages.coverage_percentage.toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            <div class="summary-card">
                <h3>Diversity</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <span class="summary-stat-label">Attack Families</span>
                        <span class="summary-stat-value">${data.diversity.unique_attack_families}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="summary-stat-label">Templates</span>
                        <span class="summary-stat-value">${data.diversity.unique_templates}</span>
                    </div>
                </div>
            </div>
            <div class="summary-card">
                <h3>Top Performing Families</h3>
                <div class="summary-stats">
                    ${data.top_performing_families.map(family => `
                        <div class="summary-stat">
                            <span class="summary-stat-label">${family.family}</span>
                            <span class="summary-stat-value">${(family.success_rate * 100).toFixed(1)}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<div class="error">Error loading summary: ${error.message}</div>`;
    }
}

// Load attack families
async function loadAttackFamilies() {
    const container = document.getElementById('attackFamiliesContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading attack family statistics...</div>';
    
    const daysBack = document.getElementById('familyDaysFilter').value || null;
    const levelFilter = document.getElementById('familyLevelFilter').value || null;
    
    const params = new URLSearchParams();
    if (daysBack) params.append('days_back', daysBack);
    if (levelFilter) params.append('level_filter', levelFilter);
    
    try {
        const response = await fetch(`/api/analytics/attack-families?${params}`);
        if (!response.ok) throw new Error('Failed to load attack families');
        
        const data = await response.json();
        
        if (!data.attack_families.length) {
            container.innerHTML = '<div class="empty-state">No attack family data available</div>';
            return;
        }
        
        const tableHTML = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Family ID</th>
                        <th>Success Rate</th>
                        <th>Attempts</th>
                        <th>Successes</th>
                        <th>Avg Quality</th>
                        <th>Levels Used</th>
                        <th>Trend</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.attack_families.map(family => `
                        <tr>
                            <td>${family.family_id}</td>
                            <td class="success-rate-cell">${(family.success_rate * 100).toFixed(1)}%</td>
                            <td>${family.total_attempts}</td>
                            <td>${family.successful_attempts}</td>
                            <td>${family.avg_template_quality.toFixed(2)}</td>
                            <td>${family.levels_used.join(', ')}</td>
                            <td class="trend-${family.trend}">${family.trend}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
    } catch (error) {
        container.innerHTML = `<div class="error">Error loading attack families: ${error.message}</div>`;
    }
}

// Load templates
async function loadTemplates() {
    const container = document.getElementById('templatesContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading template effectiveness...</div>';
    
    const familyFilter = document.getElementById('templateFamilyFilter').value || null;
    const levelFilter = document.getElementById('templateLevelFilter').value || null;
    
    const params = new URLSearchParams();
    if (familyFilter) params.append('family_filter', familyFilter);
    if (levelFilter) params.append('level_filter', levelFilter);
    
    try {
        const response = await fetch(`/api/analytics/templates?${params}`);
        if (!response.ok) throw new Error('Failed to load templates');
        
        const data = await response.json();
        
        if (!data.templates.length) {
            container.innerHTML = '<div class="empty-state">No template data available</div>';
            return;
        }
        
        const tableHTML = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Template ID</th>
                        <th>Family</th>
                        <th>Success Rate</th>
                        <th>Uses</th>
                        <th>Successes</th>
                        <th>Quality</th>
                        <th>Last Used</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.templates.map(template => `
                        <tr>
                            <td>${template.template_id}</td>
                            <td>${template.attack_family}</td>
                            <td class="success-rate-cell">${(template.success_rate * 100).toFixed(1)}%</td>
                            <td>${template.total_uses}</td>
                            <td>${template.successful_uses}</td>
                            <td>${template.avg_quality_score.toFixed(2)}</td>
                            <td>${new Date(template.last_used).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
    } catch (error) {
        container.innerHTML = `<div class="error">Error loading templates: ${error.message}</div>`;
    }
}

// Load level analysis
async function loadLevelAnalysis() {
    const container = document.getElementById('levelsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading level analysis...</div>';
    
    try {
        const response = await fetch('/api/analytics/levels');
        if (!response.ok) throw new Error('Failed to load level analysis');
        
        const data = await response.json();
        
        if (!data.levels.length) {
            container.innerHTML = '<div class="empty-state">No level data available</div>';
            return;
        }
        
        const levelsHTML = data.levels.map(level => `
            <div class="pattern-card">
                <div class="pattern-header">
                    <span class="pattern-type">Level ${level.level}</span>
                    <span class="pattern-frequency">${(level.success_rate * 100).toFixed(1)}% success rate</span>
                </div>
                <div class="pattern-description">
                    <strong>Sessions:</strong> ${level.total_sessions} total, ${level.successful_sessions} successful<br>
                    <strong>Avg Attempts to Success:</strong> ${level.avg_attempts_to_success.toFixed(1)}<br>
                    <strong>Avg Duration:</strong> ${level.avg_session_duration.toFixed(1)} minutes
                </div>
                ${level.most_effective_families.length > 0 ? `
                    <div class="pattern-examples">
                        <strong>Top Families:</strong> ${level.most_effective_families.map(([family, rate]) => 
                            `${family} (${(rate * 100).toFixed(1)}%)`
                        ).join(', ')}
                    </div>
                ` : ''}
                ${level.common_failure_patterns.length > 0 ? `
                    <div class="pattern-examples">
                        <strong>Common Failures:</strong> ${level.common_failure_patterns.join(', ')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        container.innerHTML = levelsHTML;
    } catch (error) {
        container.innerHTML = `<div class="error">Error loading level analysis: ${error.message}</div>`;
    }
}

// Load session patterns
async function loadSessionPatterns() {
    const container = document.getElementById('patternsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading session patterns...</div>';
    
    try {
        const response = await fetch('/api/analytics/patterns');
        if (!response.ok) throw new Error('Failed to load patterns');
        
        const data = await response.json();
        
        if (!data.patterns.length) {
            container.innerHTML = '<div class="empty-state">No patterns identified yet</div>';
            return;
        }
        
        const patternsHTML = data.patterns.map(pattern => `
            <div class="pattern-card">
                <div class="pattern-header">
                    <span class="pattern-type">${pattern.pattern_type.replace('_', ' ')}</span>
                    <span class="pattern-frequency">${pattern.frequency} occurrences</span>
                </div>
                <div class="pattern-description">${pattern.description}</div>
                <div class="pattern-examples">
                    <strong>Success Correlation:</strong> ${(pattern.success_correlation * 100).toFixed(1)}%<br>
                    <strong>Examples:</strong> ${pattern.example_sessions.join(', ')}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = patternsHTML;
    } catch (error) {
        container.innerHTML = `<div class="error">Error loading patterns: ${error.message}</div>`;
    }
}

// Export telemetry data
async function exportTelemetryData() {
    const resultContainer = document.getElementById('exportResult');
    if (!resultContainer) return;
    
    resultContainer.innerHTML = '<div class="loading">Exporting data...</div>';
    
    const format = document.getElementById('exportFormat').value;
    const levelFilter = document.getElementById('exportLevelFilter').value || null;
    const daysBack = document.getElementById('exportDaysFilter').value || null;
    
    const params = new URLSearchParams();
    params.append('format', format);
    if (levelFilter) params.append('level_filter', levelFilter);
    if (daysBack) params.append('days_back', daysBack);
    
    try {
        const response = await fetch(`/api/analytics/export?${params}`);
        if (!response.ok) throw new Error('Failed to export data');
        
        const data = await response.json();
        
        resultContainer.innerHTML = `
            <h4>Export Complete</h4>
            <p><strong>Records:</strong> ${data.total_records}</p>
            <p><strong>Generated:</strong> ${new Date(data.export_timestamp).toLocaleString()}</p>
            <pre>${JSON.stringify(data.data, null, 2)}</pre>
        `;
    } catch (error) {
        resultContainer.innerHTML = `<div class="error">Error exporting data: ${error.message}</div>`;
    }
}

// Initialize analytics when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Populate level filter dropdowns
    const levelOptions = Array.from({length: 8}, (_, i) => 
        `<option value="${i + 1}">Level ${i + 1}</option>`
    ).join('');
    
    document.querySelectorAll('#familyLevelFilter, #templateLevelFilter, #exportLevelFilter').forEach(select => {
        select.innerHTML = '<option value="">All levels</option>' + levelOptions;
    });
    
    // Load initial analytics data
    loadAnalyticsData('summary');
});

// Make analytics functions globally available
window.showAnalyticsTab = showAnalyticsTab;
window.loadAttackFamilies = loadAttackFamilies;
window.loadTemplates = loadTemplates;
window.exportTelemetryData = exportTelemetryData;
