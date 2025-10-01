# Sauron Architecture Documentation

## Overview

Sauron is built with a modular, extensible architecture that separates concerns and makes the codebase easy to maintain and extend. This document explains the architecture and how to work with it.

## Project Structure

```
sauron/
├── src/
│   ├── __init__.py
│   ├── gandalf_client.py      # Gandalf API client
│   ├── state.py                # State management
│   ├── agents.py               # LangChain agents
│   ├── graph.py                # LangGraph orchestration
│   ├── llm_config.py           # Multi-provider LLM configuration
│   ├── observability.py        # Logging and monitoring
│   ├── web_server.py           # Main FastAPI application
│   └── web/                    # Web interface package
│       ├── __init__.py
│       ├── routes.py           # API routes
│       ├── websocket_manager.py # WebSocket management
│       ├── templates.py        # HTML templates
│       └── static/             # Static assets
│           ├── css/
│           │   └── styles.css
│           └── js/
│               └── app.js
├── logs/                       # Log files
├── main.py                     # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Core Components

### 1. Gandalf Client (`gandalf_client.py`)

**Purpose**: Handles all communication with Lakera's Gandalf API.

**Key Classes**:
- `GandalfClient`: Main client for API interactions
- `GandalfResponse`: Pydantic model for API responses

**Responsibilities**:
- Send prompts to Gandalf
- Parse responses
- Detect successful password extraction

**Extension Points**:
- Add new detection heuristics in `_check_success()`
- Support additional Gandalf game modes
- Add retry logic or rate limiting

### 2. State Management (`state.py`)

**Purpose**: Manages the state of the agent system across attempts.

**Key Classes**:
- `AgentState`: Main state container
- `AttemptRecord`: Individual attempt record

**Responsibilities**:
- Track attempt history
- Manage current iteration data
- Extract passwords from responses
- Determine if agent should continue

**Extension Points**:
- Add new state fields for additional tracking
- Implement state persistence
- Add state validation logic

### 3. LLM Configuration (`llm_config.py`)

**Purpose**: Provides unified interface for multiple LLM providers.

**Key Classes**:
- `LLMConfig`: Static configuration manager

**Supported Providers**:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 2.0, Gemini 1.5)

**Extension Points**:
- Add new LLM providers
- Implement provider-specific optimizations
- Add model selection UI

### 4. Agents (`agents.py`)

**Purpose**: Implements the reasoning and interaction agents.

**Key Classes**:
- `ReasoningAgent`: Generates strategic prompts
- `GandalfInteractionAgent`: Sends prompts to Gandalf

**Responsibilities**:
- Analyze previous attempts
- Generate new strategies
- Parse LLM responses
- Execute interactions

**Extension Points**:
- Add new prompt strategies
- Implement multi-agent collaboration
- Add learning from successful attempts

### 5. LangGraph Orchestration (`graph.py`)

**Purpose**: Orchestrates the agent workflow using LangGraph.

**Key Classes**:
- `GandalfGraph`: Main orchestration class

**Workflow**:
```
reason → interact → evaluate → (continue/end)
   ↑                              |
   └──────────────────────────────┘
```

**Extension Points**:
- Add new nodes (e.g., validation, analysis)
- Implement parallel strategies
- Add conditional branching logic

### 6. Observability (`observability.py`)

**Purpose**: Provides logging and monitoring capabilities.

**Key Classes**:
- `ObservabilityManager`: Centralized logging

**Features**:
- Structured JSON logging
- In-memory event storage
- Statistics tracking
- File-based persistence

**Extension Points**:
- Add external logging services (e.g., Datadog, Sentry)
- Implement metrics collection
- Add alerting capabilities

## Web Interface Architecture

### Modular Design

The web interface is split into separate, focused modules:

#### 1. Main Server (`web_server.py`)

**Purpose**: FastAPI application setup and configuration.

**Responsibilities**:
- App initialization
- Static file mounting
- Route registration
- Lifecycle management

**Extension Points**:
- Add middleware
- Configure CORS
- Add authentication

#### 2. Routes (`web/routes.py`)

**Purpose**: API endpoint definitions.

**Endpoints**:
- `POST /start` - Start agent
- `POST /stop` - Stop agent
- `GET /api/attempts` - Get attempts
- `GET /api/events` - Get events
- `GET /api/summary` - Get statistics
- `GET /api/config` - Get LLM config

**Extension Points**:
- Add new endpoints
- Implement request validation
- Add rate limiting

#### 3. WebSocket Manager (`web/websocket_manager.py`)

**Purpose**: Manages real-time WebSocket connections.

**Key Classes**:
- `ConnectionManager`: Connection lifecycle management

**Features**:
- Connection pooling
- Broadcast messaging
- Automatic reconnection
- Error handling

**Extension Points**:
- Add authentication
- Implement rooms/channels
- Add message queuing

#### 4. Templates (`web/templates.py`)

**Purpose**: HTML template generation.

**Extension Points**:
- Use template engine (Jinja2)
- Add multiple page templates
- Implement template inheritance

#### 5. Static Assets

**CSS** (`web/static/css/styles.css`):
- Responsive design
- Animations
- Theme variables

**JavaScript** (`web/static/js/app.js`):
- WebSocket client
- UI updates
- Event handling

**Extension Points**:
- Add CSS preprocessor (SASS/LESS)
- Implement build pipeline
- Add frontend framework (React/Vue)

## Data Flow

### Agent Execution Flow

```
1. User starts agent via web UI
   ↓
2. POST /start creates GandalfGraph
   ↓
3. Graph runs in background task
   ↓
4. For each iteration:
   a. ReasoningAgent generates prompt
   b. GandalfInteractionAgent sends to API
   c. Response evaluated
   d. State updated
   e. Observability logs created
   f. WebSocket broadcasts update
   ↓
5. Loop continues until success or max attempts
   ↓
6. Final status broadcast to UI
```

### Real-time Update Flow

```
1. Agent logs event/attempt
   ↓
2. ObservabilityManager stores data
   ↓
3. WebSocket manager broadcasts
   ↓
4. All connected clients receive update
   ↓
5. JavaScript updates UI
```

## Configuration

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=openai|anthropic|gemini
LLM_MODEL=model-name

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Optional: LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=sauron

# Server
HOST=0.0.0.0
PORT=8000
```

### Programmatic Configuration

```python
from src.graph import GandalfGraph

# Configure agent
graph = GandalfGraph(
    level=3,
    max_attempts=20,
    provider="anthropic",
    model="claude-3-5-haiku-20241022"
)

# Run
final_state = graph.run()
```

## Extension Guide

### Adding a New LLM Provider

1. Update `llm_config.py`:
```python
@staticmethod
def _get_newprovider_llm(model: str, temperature: float):
    api_key = os.getenv("NEWPROVIDER_API_KEY")
    if not api_key:
        raise ValueError("NEWPROVIDER_API_KEY not found")
    
    return ChatNewProvider(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
```

2. Update `get_llm()` method
3. Add to `DEFAULT_MODELS` dict
4. Update `.env.example`
5. Update documentation

### Adding a New API Endpoint

1. Add route in `web/routes.py`:
```python
@router.get("/api/new-endpoint")
async def new_endpoint():
    # Implementation
    return {"data": "value"}
```

2. Add client-side handler in `app.js`
3. Update UI if needed

### Adding a New Graph Node

1. Add node method in `graph.py`:
```python
def _new_node(self, state: AgentState) -> Dict[str, Any]:
    # Node logic
    return {"key": "value"}
```

2. Register in `_build_graph()`:
```python
workflow.add_node("new_node", self._new_node)
workflow.add_edge("previous_node", "new_node")
```

### Adding Custom Strategies

1. Update reasoning prompt in `agents.py`
2. Add strategy detection in `_parse_response()`
3. Track in `AgentState.strategies_tried`

## Testing

### Unit Tests

```python
# Test state management
def test_state_management():
    state = AgentState(level=1, max_attempts=5)
    state.add_attempt("prompt", "response", "reasoning", True)
    assert state.current_attempt == 1
    assert state.success == True
```

### Integration Tests

```python
# Test full workflow
async def test_agent_workflow():
    graph = GandalfGraph(level=1, max_attempts=3)
    final_state = graph.run()
    assert final_state.current_attempt <= 3
```

## Performance Considerations

### Optimization Points

1. **WebSocket Broadcasting**: Use message queuing for high connection counts
2. **State Management**: Implement state caching for large histories
3. **LLM Calls**: Add response caching for similar prompts
4. **Logging**: Use async logging for high-throughput scenarios

### Scalability

- **Horizontal**: Deploy multiple instances behind load balancer
- **Vertical**: Increase resources for LLM inference
- **Database**: Add persistent storage for long-term history

## Security Considerations

1. **API Keys**: Never commit to version control
2. **Input Validation**: Validate all user inputs
3. **Rate Limiting**: Implement on API endpoints
4. **CORS**: Configure appropriately for production
5. **Authentication**: Add for production deployments

## Monitoring and Debugging

### Logs

- **File**: `logs/gandalf_agent.log` (structured JSON)
- **Console**: Real-time events in terminal
- **Web UI**: Event log panel

### Debugging Tips

1. Check WebSocket connection in browser DevTools
2. Review structured logs for detailed traces
3. Use LangSmith for LLM call inspection
4. Monitor ObservabilityManager stats

## Future Enhancements

### Planned Features

- [ ] Multi-level campaign mode
- [ ] Strategy effectiveness analytics
- [ ] A/B testing different approaches
- [ ] Collaborative multi-agent system
- [ ] Historical success pattern analysis
- [ ] Custom strategy templates
- [ ] Export/import configurations
- [ ] Advanced visualization dashboard

### Architecture Improvements

- [ ] Implement dependency injection
- [ ] Add comprehensive test suite
- [ ] Create plugin system
- [ ] Add API versioning
- [ ] Implement caching layer
- [ ] Add database integration
- [ ] Create CLI interface
- [ ] Add Docker support

## Contributing

When contributing to Sauron:

1. Follow the modular architecture
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Follow existing code style
6. Add docstrings to public APIs

## License

MIT License - See LICENSE file for details
