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
            default:
                console.log('Unknown message type:', data.type);
        }
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
        
        attemptDiv.innerHTML = `
            <div class="attempt-header">
                <span>Attempt #${attempt.attempt_number} - Level ${attempt.level}</span>
                <span class="status ${attempt.success ? 'success' : 'failed'}">
                    ${attempt.success ? 'SUCCESS ✓' : 'FAILED ✗'}
                </span>
            </div>
            <div class="attempt-content">
                <div class="attempt-section">
                    <strong>🧠 Reasoning:</strong>
                    <p>${this.escapeHtml(attempt.reasoning)}</p>
                </div>
                <div class="attempt-section">
                    <strong>📤 Prompt Sent:</strong>
                    <p>${this.escapeHtml(attempt.prompt)}</p>
                </div>
                <div class="attempt-section">
                    <strong>📥 Gandalf's Response:</strong>
                    <p>${this.escapeHtml(attempt.response)}</p>
                </div>
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
    }

    updateStatus(status) {
        const badge = document.getElementById('statusBadge');
        badge.className = 'status ' + status.toLowerCase();
        badge.textContent = status;
        
        this.isRunning = status === 'RUNNING';
        document.getElementById('startBtn').disabled = this.isRunning;
        document.getElementById('stopBtn').disabled = !this.isRunning;
        
        // Add loading indicator if running
        if (this.isRunning) {
            badge.innerHTML = `${status} <span class="loading"></span>`;
        }
    }

    // Control Methods
    async startAgent() {
        const level = parseInt(document.getElementById('level').value);
        const maxAttempts = parseInt(document.getElementById('maxAttempts').value);
        
        try {
            const response = await fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({level, max_attempts: maxAttempts})
            });
            
            if (!response.ok) {
                throw new Error('Failed to start agent');
            }
            
            // Clear previous attempts
            const container = document.getElementById('attempts-container');
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⏳</div><div class="empty-state-text">Agent is starting...</div></div>';
            
            this.addEvent({
                type: 'info',
                message: `Starting agent for Level ${level} with ${maxAttempts} max attempts`,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error starting agent:', error);
            this.addEvent({
                type: 'error',
                message: `Failed to start agent: ${error.message}`,
                timestamp: new Date().toISOString()
            });
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

    // Utility Methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.sauronApp = new SauronApp();
});

// Make functions available globally for inline onclick handlers
window.startAgent = () => window.sauronApp.startAgent();
window.stopAgent = () => window.sauronApp.stopAgent();
