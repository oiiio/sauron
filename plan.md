# 🎯 Sauron Rebuild Plan: Xezbeth Integration

## Overview

Transform Sauron from a standalone red-team agent into an orchestrator that leverages Xezbeth for intelligent prompt selection while providing a rich GUI for evaluation and telemetry.

## Architecture Overview

**Dual-Mode Operation:**
```
┌─────────────────────────────────────────────────┐
│                    Sauron                       │
│  ┌───────────────────────────────────────────┐ │
│  │  Mode: Xezbeth (default) | Standalone     │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌─────────────────┐     ┌──────────────────┐ │
│  │  Xezbeth Mode   │     │ Standalone Mode  │ │
│  │                 │     │                  │ │
│  │  XezbethClient  │     │ ReasoningAgent   │ │
│  │       ↓         │     │       ↓          │ │
│  │  Xezbeth API    │     │  Local Logic     │ │
│  │  (localhost:8000│     │                  │ │
│  └─────────────────┘     └──────────────────┘ │
│            ↓                       ↓            │
│         GandalfClient (Target)                  │
│            ↓                                    │
│         Enhanced GUI + Telemetry Dashboard      │
│            ↓                                    │
│    Session Persistence (SQLite)                 │
└─────────────────────────────────────────────────┘
```

## Requirements Summary

1. **Xezbeth integration is optional** (but the default, standalone should be fallback)
2. **Xezbeth API URL**: http://localhost:8000 (configurable)
3. **Multiple concurrent sessions** supported
4. **Gandalf-focused** (no other target types)
5. **Enhanced GUI** using existing components where possible
6. **No authentication** required for GUI
7. **Persistent session history** with purge capability

## Core Implementation Plan

### Phase 1: Foundation & Infrastructure

#### 1.1 Configuration System
Add environment variables:
```bash
# Xezbeth Configuration
XEZBETH_ENABLED=true  # Toggle Xezbeth vs standalone
XEZBETH_API_URL=http://localhost:8000
XEZBETH_API_KEY=  # Optional for secured Xezbeth

# Gandalf remains the same
# Session persistence
DATABASE_PATH=./data/sauron.db
```

#### 1.2 Database Schema (SQLite)
```sql
-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    xezbeth_session_id TEXT,  -- NULL if standalone mode
    level INTEGER,
    max_attempts INTEGER,
    mode TEXT,  -- 'xezbeth' or 'standalone'
    status TEXT,  -- 'running', 'success', 'failed', 'stopped'
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    extracted_password TEXT
);

-- Attempts table
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    attempt_number INTEGER,
    prompt TEXT,
    response TEXT,
    reasoning TEXT,
    success BOOLEAN,
    timestamp TIMESTAMP,
    
    -- Xezbeth-specific fields
    attack_family TEXT,
    template_id TEXT,
    strategy TEXT,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Telemetry table (for Xezbeth mode)
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    attempt_number INTEGER,
    
    -- Template metrics
    template_success_rate REAL,
    template_quality_score REAL,
    template_relevance_score REAL,
    
    -- Family metrics
    family_id TEXT,
    family_success_rate REAL,
    family_selection_probability REAL,
    
    -- Session progress
    coverage_percentage REAL,
    
    timestamp TIMESTAMP,
    raw_telemetry JSON,  -- Store full telemetry object
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### Phase 2: New Components

#### 2.1 XezbethClient (`src/xezbeth_client.py`)
```python
class XezbethClient:
    """Client for Xezbeth API interactions"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.session = httpx.AsyncClient()
    
    async def create_session(
        self,
        objective: str,
        level: int,
        max_attempts: int
    ) -> str:
        """Create Xezbeth session, returns session_id"""
        
    async def get_next_prompt(
        self,
        session_id: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """Get next prompt with telemetry"""
        
    async def record_attempt(
        self,
        session_id: str,
        attempt_id: str,
        model_response: str,
        aux_signals: Optional[Dict] = None
    ) -> Dict:
        """Record attempt result and get updated metrics"""
        
    async def get_report(self, session_id: str) -> Dict:
        """Get final session report"""
        
    async def get_analytics(self, session_id: str) -> Dict:
        """Get comprehensive session analytics"""
```

#### 2.2 SessionManager (`src/session_manager.py`)
```python
class SessionManager:
    """Manages session persistence and multiple concurrent sessions"""
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_db()
    
    async def create_session(
        self,
        level: int,
        max_attempts: int,
        mode: str,
        xezbeth_session_id: Optional[str] = None
    ) -> str:
        """Create new session"""
        
    async def get_session(self, session_id: str) -> Dict:
        """Get session details"""
        
    async def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List all sessions"""
        
    async def add_attempt(
        self,
        session_id: str,
        attempt_data: Dict
    ):
        """Add attempt to session"""
        
    async def add_telemetry(
        self,
        session_id: str,
        telemetry_data: Dict
    ):
        """Add telemetry data"""
        
    async def purge_sessions(
        self,
        before_date: Optional[datetime] = None
    ):
        """Purge old sessions"""
```

#### 2.3 ModeSelector (`src/mode_selector.py`)
```python
class ModeSelector:
    """Determines and manages Xezbeth vs Standalone mode"""
    
    @staticmethod
    def should_use_xezbeth() -> bool:
        """Check if Xezbeth mode should be used"""
        
    @staticmethod
    async def test_xezbeth_connection(url: str) -> bool:
        """Test if Xezbeth API is reachable"""
        
    @staticmethod
    def get_mode_config() -> Dict:
        """Get current mode configuration"""
```

### Phase 3: Modified Components

#### 3.1 Updated State (`src/state.py`)
```python
class AgentState(BaseModel):
    # Existing fields...
    
    # New fields for Xezbeth
    mode: str = "xezbeth"  # or "standalone"
    xezbeth_session_id: Optional[str] = None
    attack_family: Optional[str] = None
    template_id: Optional[str] = None
    current_telemetry: Optional[Dict] = None
    
    # Session management
    sauron_session_id: str  # Our internal session ID
```

#### 3.2 Updated Graph (`src/graph.py`)
```python
class GandalfGraph:
    def __init__(self, ...):
        # Detect mode
        self.mode = self._determine_mode()
        
        if self.mode == "xezbeth":
            self.xezbeth_client = XezbethClient(...)
            self.session_manager = SessionManager(...)
        else:
            self.reasoning_agent = ReasoningAgent(...)
    
    def _build_graph(self):
        if self.mode == "xezbeth":
            # New workflow: xezbeth_prompt → interact → record → evaluate
            workflow.add_node("xezbeth_prompt", self._xezbeth_prompt_node)
            workflow.add_node("record_to_xezbeth", self._record_node)
        else:
            # Original workflow: reason → interact → evaluate
            workflow.add_node("reason", self._reason_node)
    
    async def _xezbeth_prompt_node(self, state):
        """Get next prompt from Xezbeth"""
        
    async def _record_node(self, state):
        """Record result back to Xezbeth"""
```

### Phase 4: Enhanced GUI

#### 4.1 New Dashboard Components

**Session Selector:**
```html
<div class="session-panel">
  <h3>Active Sessions</h3>
  <select id="sessionSelector">
    <option value="new">+ New Session</option>
    <!-- Populated dynamically -->
  </select>
  <button id="purgeBtn">🗑️ Purge History</button>
</div>
```

**Mode Indicator:**
```html
<div class="mode-badge">
  <span id="modeBadge">🔗 Xezbeth Mode</span>
  <small id="xezbethStatus">Connected to localhost:8000</small>
</div>
```

**Telemetry Dashboard (Xezbeth mode only):**
```html
<div class="telemetry-panel">
  <h3>📊 Xezbeth Telemetry</h3>
  
  <div class="metric-grid">
    <div class="metric">
      <label>Attack Family</label>
      <span id="currentFamily">-</span>
    </div>
    <div class="metric">
      <label>Template Quality</label>
      <span id="templateQuality">-</span>
    </div>
    <div class="metric">
      <label>Coverage</label>
      <div class="progress-bar">
        <div id="coverageProgress"></div>
      </div>
    </div>
  </div>
  
  <div class="family-stats">
    <h4>Family Performance</h4>
    <div id="familyChart"><!-- Chart here --></div>
  </div>
</div>
```

#### 4.2 Enhanced Attempt Display:
```html
<div class="attempt xezbeth">
  <!-- Existing attempt info -->
  
  <!-- New Xezbeth info -->
  <div class="xezbeth-meta">
    <span class="badge family">LLM01: Prompt Injection</span>
    <span class="badge template">Role Confusion Attack</span>
    <span class="badge quality">Quality: 0.85</span>
  </div>
  
  <div class="telemetry-details">
    <div class="telemetry-item">
      <strong>Selection Probability:</strong> 65%
    </div>
    <div class="telemetry-item">
      <strong>Template Success Rate:</strong> 42%
    </div>
  </div>
</div>
```

### Phase 5: API Routes Updates

**New Routes** (`src/web/routes.py`):
```python
@router.get("/api/sessions")
async def list_sessions():
    """List all sessions"""

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get specific session details"""

@router.get("/api/sessions/{session_id}/telemetry")
async def get_session_telemetry(session_id: str):
    """Get telemetry data for session"""

@router.get("/api/sessions/{session_id}/analytics")
async def get_session_analytics(session_id: str):
    """Get Xezbeth analytics if available"""

@router.delete("/api/sessions")
async def purge_sessions(before_date: Optional[str] = None):
    """Purge old sessions"""

@router.get("/api/mode")
async def get_mode():
    """Get current mode (xezbeth/standalone)"""
```

## Implementation Sequence

1. **Database & Session Management** (Critical foundation)
2. **XezbethClient** (Core integration)
3. **ModeSelector** (Enables dual-mode)
4. **Updated Graph & State** (Workflow changes)
5. **Enhanced Routes** (Backend API)
6. **GUI Enhancements** (Frontend visualization)
7. **Testing & Documentation**

## File Structure After Rebuild

```
sauron/
├── data/
│   └── sauron.db              # Session persistence
├── src/
│   ├── xezbeth_client.py      # NEW
│   ├── session_manager.py     # NEW
│   ├── mode_selector.py       # NEW
│   ├── state.py               # MODIFIED
│   ├── graph.py               # MODIFIED
│   ├── agents.py              # KEPT (for standalone)
│   ├── gandalf_client.py      # KEPT
│   ├── web/
│   │   ├── routes.py          # MODIFIED
│   │   └── static/
│   │       ├── js/
│   │       │   ├── app.js     # MODIFIED
│   │       │   └── telemetry.js  # NEW
│   │       └── css/
│   │           └── styles.css  # MODIFIED
├── .env                       # MODIFIED
└── requirements.txt           # MODIFIED (add httpx, aiosqlite)
```

## Key Features After Rebuild

✅ **Dual-mode operation** (Xezbeth/Standalone)
✅ **Multiple concurrent sessions**
✅ **Persistent session history**
✅ **Rich telemetry dashboard** (Xezbeth mode)
✅ **Session management UI**
✅ **Purge capability**
✅ **Real-time WebSocket updates**
✅ **Configurable Xezbeth endpoint**
✅ **Graceful fallback** to standalone
✅ **Enhanced attempt visualization**

## Progress Tracking

### Phase 1: Foundation & Infrastructure
- [ ] Database schema implementation
- [ ] Session persistence layer
- [ ] Configuration system updates

### Phase 2: New Components
- [ ] XezbethClient implementation
- [ ] SessionManager implementation
- [ ] ModeSelector implementation

### Phase 3: Modified Components
- [ ] State management updates
- [ ] Graph workflow modifications
- [ ] Agent integration updates

### Phase 4: Enhanced GUI
- [ ] Session management UI
- [ ] Telemetry dashboard
- [ ] Enhanced attempt visualization

### Phase 5: Testing & Documentation
- [ ] Integration testing
- [ ] Documentation updates
- [ ] Deployment verification

---

This plan maintains the best parts of existing Sauron while adding powerful Xezbeth integration with graceful fallback to standalone mode.
