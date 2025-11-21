# Agent Orchestrator

Multi-agent coordination service for TraceOS.

## Overview

The Agent Orchestrator coordinates multiple agents, tracks their communication via contracts, logs to Trace for provenance, and compresses conversations to MemAgent.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Agent Orchestrator                        │
│                     (Port 8888)                             │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │   Agent      │   │  Contract    │   │  Integration │   │
│  │   Registry   │   │  Manager     │   │  Manager     │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│         │                   │                   │           │
│         └───────────────────┴───────────────────┘           │
│                         Core                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────┐                   ┌───────────────┐
│  Trace API    │                   │  MemAgent API │
│  (Port 8787)  │                   │  (Port 8799)  │
│               │                   │               │
│  Logs         │                   │  Compresses   │
│  Contracts    │                   │  Conversations│
└───────────────┘                   └───────────────┘
```

## Features

- **Agent Registry**: Register agents with capabilities
- **Smart Routing**: Route tasks to capable agents
- **Contract Tracking**: Track all agent-to-agent communication
- **Trace Integration**: Log contracts for provenance
- **MemAgent Integration**: Compress conversations to memory blocks
- **Extensible**: Easy to add new agents and capabilities

## Installation

```bash
cd agent-orchestrator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

### 1. Start Dependencies

**Trace HTTP Wrapper:**
```bash
cd ~/trace-http-wrapper
source venv/bin/activate
python3 main.py
# Server on http://localhost:8787
```

**MemAgent (optional):**
```bash
cd ~/memagent-build
source venv/bin/activate
python3 main.py
# Server on http://localhost:8799
```

### 2. Start Agent Orchestrator

```bash
cd ~/agent-orchestrator
source venv/bin/activate
python3 main.py
# Server on http://localhost:8888
```

### 3. Test It

```bash
python3 test_orchestrator.py
```

Expected: 6/6 tests passed ✓

## API Endpoints

### Health Check
```bash
GET /v1/health
```

### List Agents
```bash
GET /v1/agents
```

Response:
```json
{
  "agents": [
    {
      "agent_id": "agent_example_001",
      "name": "Example Agent",
      "status": "available",
      "capabilities": [
        {"name": "echo", "description": "Echo text back"},
        {"name": "uppercase", "description": "Convert to uppercase"}
      ]
    }
  ],
  "total": 1
}
```

### Orchestrate Task
```bash
POST /v1/orchestrate
Content-Type: application/json

{
  "session_id": "session_001",
  "capability": "echo",
  "parameters": {
    "text": "Hello, world!"
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "message": "Echo: Hello, world!"
  },
  "contract_id": "01K8VF9XK83SYH1HAX57ZGJDYS",
  "agent_id": "agent_example_001"
}
```

### Get Contracts
```bash
GET /v1/contracts?session_id=session_001
```

Response:
```json
{
  "contracts": [
    {
      "contract_id": "...",
      "contract_type": "REQUEST",
      "from_agent": "orchestrator",
      "to_agent": "agent_example_001",
      "capability": "echo",
      "status": "completed"
    },
    {
      "contract_id": "...",
      "contract_type": "RESPONSE",
      "from_agent": "agent_example_001",
      "to_agent": "orchestrator",
      "status": "completed",
      "result": {"message": "Echo: Hello, world!"}
    }
  ],
  "total": 2
}
```

### Compress Session
```bash
POST /v1/compress
Content-Type: application/json

{
  "session_id": "session_001",
  "intent": "Testing echo and uppercase"
}
```

### Get Status
```bash
GET /v1/status
```

## Creating Custom Agents

### 1. Define Agent Class

```python
from orchestrator.agents import Agent, AgentCapability

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_001",
            name="My Custom Agent",
            description="Does custom things"
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        capability = task["capability"]
        parameters = task["parameters"]
        
        if capability == "my_capability":
            # Do something
            result = self.process(parameters)
            return {
                "success": True,
                "data": result
            }
        else:
            return {
                "success": False,
                "error": f"Unknown capability: {capability}"
            }
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="my_capability",
                description="My custom capability",
                parameters={"param1": "string"}
            )
        ]
```

### 2. Register Agent

In `main.py`:

```python
from my_agents import MyAgent

# In lifespan function
my_agent = MyAgent()
orchestrator.register_agent(my_agent)
```

### 3. Use Agent

```bash
curl -X POST http://localhost:8888/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "capability": "my_capability",
    "parameters": {"param1": "value"}
  }'
```

## Contract Flow

1. **User sends task** → Orchestrator
2. **Orchestrator creates REQUEST contract**
3. **Task routed to capable agent**
4. **REQUEST logged to Trace**
5. **Agent executes task**
6. **Orchestrator creates RESPONSE contract**
7. **RESPONSE logged to Trace**
8. **Result returned to user**

All contracts stored locally and in Trace for provenance.

## Project Structure

```
agent-orchestrator/
├── orchestrator/
│   ├── __init__.py
│   ├── agents.py          # Agent base class
│   ├── contracts.py       # Contract model & storage
│   ├── core.py           # Core orchestrator
│   ├── integrations.py   # MemAgent & Trace clients
│   └── routes.py         # FastAPI routes
├── data/
│   └── contracts/        # Contract storage
├── main.py               # Entry point
├── test_orchestrator.py  # Test suite
├── requirements.txt
└── README.md
```

## Configuration

Environment variables (optional):

```bash
export MEMAGENT_URL=http://localhost:8799
export TRACE_URL=http://localhost:8787
export ORCHESTRATOR_PORT=8888
```

Default values are shown above.

## Testing

```bash
# Run test suite
python3 test_orchestrator.py

# Manual testing
curl http://localhost:8888/v1/health
curl http://localhost:8888/v1/agents
curl -X POST http://localhost:8888/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "capability": "echo", "parameters": {"text": "hi"}}'
```

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8888/docs
- ReDoc: http://localhost:8888/redoc

## Use Cases

### 1. Multi-Agent Image Generation

```python
# Register image generation agent
orchestrator.register_agent(ImageGenAgent())

# Generate image
result = await orchestrator.orchestrate(
    session_id="design_001",
    task={
        "capability": "text_to_image",
        "parameters": {
            "prompt": "A serene landscape",
            "style": "realistic"
        }
    }
)
```

### 2. Code Analysis Pipeline

```python
# Register agents
orchestrator.register_agent(CodeAnalysisAgent())
orchestrator.register_agent(SecurityScanAgent())
orchestrator.register_agent(DocumentationAgent())

# Analyze code
await orchestrator.orchestrate(session_id, {"capability": "analyze_code", ...})
await orchestrator.orchestrate(session_id, {"capability": "security_scan", ...})
await orchestrator.orchestrate(session_id, {"capability": "generate_docs", ...})

# Compress to memory
await orchestrator.compress_session(session_id)
```

### 3. Data Processing Workflow

```python
# Chain multiple agents
orchestrator.register_agent(DataCleaningAgent())
orchestrator.register_agent(AnalysisAgent())
orchestrator.register_agent(VisualizationAgent())

# Execute pipeline
for capability in ["clean_data", "analyze", "visualize"]:
    await orchestrator.orchestrate(session_id, {"capability": capability, ...})
```

## Troubleshooting

### Agent Not Found

Error: "No agent available for capability: X"

**Solution:** Register an agent that provides capability X

### Contract Not Logged to Trace

**Check:**
1. Trace HTTP Wrapper is running: `curl http://localhost:8787/v1/health`
2. Check orchestrator logs for Trace errors

### Compression Failed

**Check:**
1. MemAgent is running: `curl http://localhost:8799/health`
2. Session has contracts: `GET /v1/contracts?session_id=X`

## Performance

| Operation | Duration |
|-----------|----------|
| Task routing | <1ms |
| Contract creation | ~1-5ms |
| Agent execution | Varies by agent |
| Trace logging | ~10-50ms (async) |
| Compression | ~1-5s (Claude API) |

## Roadmap

- [ ] External agent registration via HTTP
- [ ] Agent health monitoring
- [ ] Task queuing and prioritization
- [ ] Parallel agent execution
- [ ] Agent authentication
- [ ] Web UI for monitoring
- [ ] Metrics and analytics

## Contributing

To add new agents:

1. Create agent class extending `Agent`
2. Implement `execute()` and `get_capabilities()`
3. Register in `main.py`
4. Add tests
5. Update documentation

## License

MIT

## Support

For issues and questions:
- GitHub Issues: (add your repo URL)
- Documentation: `/docs` endpoint
- Examples: `test_orchestrator.py`

---

**Version:** 1.0.0  
**Status:** Production-ready  
**Dependencies:** FastAPI, httpx, pydantic, uvicorn, python-ulid
