# Agent Orchestrator - Quick Start Guide

Get up and running with Agent Orchestrator in 5 minutes.

## Prerequisites

- Python 3.9+
- Trace HTTP Wrapper (optional but recommended)
- MemAgent (optional, for compression)

## Step 1: Install

```bash
cd ~/agent-orchestrator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Start Dependencies

### Start Trace (Recommended)

```bash
# Terminal 1
cd ~/trace-http-wrapper
source venv/bin/activate
python3 main.py
```

Server runs on http://localhost:8787

### Start MemAgent (Optional)

```bash
# Terminal 2
cd ~/memagent-build
source venv/bin/activate
python3 main.py
```

Server runs on http://localhost:8799

## Step 3: Start Orchestrator

```bash
# Terminal 3
cd ~/agent-orchestrator
source venv/bin/activate
python3 main.py
```

Server runs on http://localhost:8888

You should see:
```
Agent Orchestrator started successfully
Registered agents: ['agent_example_001']
Integration health: {'memagent': False, 'trace': True, 'all_healthy': False}
```

## Step 4: Verify Installation

```bash
# Test health
curl http://localhost:8888/v1/health

# List agents
curl http://localhost:8888/v1/agents

# Or run full test suite
python3 test_orchestrator.py
```

Expected: 6/6 tests passed ✓

## Step 5: Run Your First Task

### Echo Task

```bash
curl -X POST http://localhost:8888/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "capability": "echo",
    "parameters": {
      "text": "Hello, Agent Orchestrator!"
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "message": "Echo: Hello, Agent Orchestrator!"
  },
  "contract_id": "01K8...",
  "agent_id": "agent_example_001"
}
```

### Uppercase Task

```bash
curl -X POST http://localhost:8888/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "capability": "uppercase",
    "parameters": {
      "text": "make me loud"
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "result": "MAKE ME LOUD"
  },
  "contract_id": "01K8...",
  "agent_id": "agent_example_001"
}
```

## Step 6: View Contract History

```bash
curl "http://localhost:8888/v1/contracts?session_id=my_session"
```

You'll see REQUEST and RESPONSE contracts for each task.

## Step 7: Compress Session (Optional)

If MemAgent is running:

```bash
curl -X POST http://localhost:8888/v1/compress \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "intent": "Testing echo and uppercase capabilities"
  }'
```

## Step 8: Check Status

```bash
curl http://localhost:8888/v1/status
```

View:
- Registered agents
- Contract statistics
- Integration health

## Next Steps

### Create Your Own Agent

1. **Create agent file** (`my_agent.py`):

```python
from orchestrator.agents import Agent, AgentCapability
from typing import List, Dict, Any

class GreetingAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_id="agent_greeting_001",
            name="Greeting Agent",
            description="Generates personalized greetings"
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        params = task["parameters"]
        name = params.get("name", "Friend")
        language = params.get("language", "english")
        
        greetings = {
            "english": f"Hello, {name}!",
            "spanish": f"¡Hola, {name}!",
            "french": f"Bonjour, {name}!"
        }
        
        greeting = greetings.get(language, greetings["english"])
        
        return {
            "success": True,
            "data": {
                "greeting": greeting,
                "language": language
            }
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="greet",
                description="Generate personalized greeting",
                parameters={
                    "name": "string",
                    "language": "english|spanish|french"
                }
            )
        ]
```

2. **Register in** `main.py`:

```python
from my_agent import GreetingAgent

# In lifespan function, after orchestrator initialization:
greeting_agent = GreetingAgent()
orchestrator.register_agent(greeting_agent)
```

3. **Restart server**:

```bash
# Stop server (Ctrl+C)
python3 main.py
```

4. **Use your agent**:

```bash
curl -X POST http://localhost:8888/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "greeting_session",
    "capability": "greet",
    "parameters": {
      "name": "Alice",
      "language": "spanish"
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "greeting": "¡Hola, Alice!",
    "language": "spanish"
  },
  "contract_id": "...",
  "agent_id": "agent_greeting_001"
}
```

## Common Tasks

### List Available Capabilities

```bash
curl http://localhost:8888/v1/agents | jq '.agents[].capabilities'
```

### Filter Contracts

```bash
# By agent
curl "http://localhost:8888/v1/contracts?from_agent=orchestrator"

# By session
curl "http://localhost:8888/v1/contracts?session_id=my_session"
```

### Monitor Agent Status

```bash
curl http://localhost:8888/v1/status | jq '.agents'
```

## Interactive API Docs

Open in browser:
- http://localhost:8888/docs (Swagger UI)
- http://localhost:8888/redoc (ReDoc)

Try endpoints interactively!

## Troubleshooting

### Server won't start

Check port 8888 is available:
```bash
lsof -i :8888
```

### Agent not found

List registered agents:
```bash
curl http://localhost:8888/v1/agents
```

### Integration health failing

Check dependencies:
```bash
curl http://localhost:8787/v1/health  # Trace
curl http://localhost:8799/health      # MemAgent
```

## Resources

- Full documentation: `README.md`
- Test examples: `test_orchestrator.py`
- Agent examples: `orchestrator/agents.py`
- API reference: http://localhost:8888/docs

## Support

Questions? Check:
1. Server logs for errors
2. Test suite: `python3 test_orchestrator.py`
3. Status endpoint: `GET /v1/status`

---

**You're ready to orchestrate!** 🎉
