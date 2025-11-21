# Trace HTTP Wrapper - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd ~/trace-http-wrapper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Verify Trace Server

The wrapper expects the Trace MCP server at:
```
/home/jesmosis/trace-server/
```

Verify it exists:
```bash
ls ~/trace-server/trace_sde/
```

Should show: `__init__.py`, `server.py`, `storage.py`, `models.py`

### 3. Start the Wrapper

```bash
cd ~/trace-http-wrapper
source venv/bin/activate
python3 main.py
```

Server will start on: `http://localhost:8787`

### 4. Test the Wrapper

In another terminal:
```bash
cd ~/trace-http-wrapper
source venv/bin/activate
python3 test_wrapper.py
```

Or test manually:
```bash
curl http://localhost:8787/v1/health
```

## Architecture

```
┌─────────────────┐
│  HTTP Client    │ (MemAgent, curl, etc.)
└────────┬────────┘
         │ HTTP POST/GET
         ▼
┌─────────────────┐
│  FastAPI Server │ (port 8787)
│  trace_wrapper  │
└────────┬────────┘
         │ JSON-RPC over stdio
         ▼
┌─────────────────┐
│  Trace MCP      │ (Python subprocess)
│  trace_sde      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  File Storage   │ (~/.trace/)
└─────────────────┘
```

## Configuration

### Change Trace Server Path

Edit `trace_wrapper/mcp_client.py`:

```python
def __init__(self, trace_command: str = "/path/to/your/trace/server"):
    ...
```

### Change Port

Edit `main.py`:

```python
uvicorn.run(
    ...,
    port=8787  # Change to your desired port
)
```

## Testing

### Run Test Suite

```bash
python3 test_wrapper.py
```

Expected output:
```
============================================================
Trace HTTP Wrapper - Test Suite
============================================================

✓ Server is ready!
✓ All tests passed!
```

### Manual Testing

```bash
# Health check
curl http://localhost:8787/v1/health

# List sessions
curl http://localhost:8787/v1/sessions

# Get events for a session
curl http://localhost:8787/v1/sessions/session_abc/events

# Add event
curl -X POST http://localhost:8787/v1/sessions/session_abc/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test.event",
    "data": {"test": true}
  }'
```

## Integration with MemAgent

### Update MemAgent's TraceClient

Edit `memagent/compression/trace_client.py`:

```python
class TraceClient:
    def __init__(self, trace_url: str = "http://localhost:8787", use_mock: bool = False):
        self.trace_url = trace_url
        self.use_mock = use_mock

    async def fetch_events_async(self, session_id: str) -> List[Dict]:
        if self.use_mock:
            return self._generate_mock_events(session_id)

        # Use HTTP wrapper instead of direct MCP
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.trace_url}/v1/sessions/{session_id}/events"
            )

            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                return events
            else:
                logger.warning(f"Trace HTTP wrapper error: {response.status_code}")
                return self._generate_mock_events(session_id)
```

### Test MemAgent Integration

```bash
# Terminal 1: Start Trace HTTP Wrapper
cd ~/trace-http-wrapper
source venv/bin/activate
python3 main.py

# Terminal 2: Start MemAgent
cd ~/memagent-build
source venv/bin/activate
python3 main.py

# Terminal 3: Test compression with real Trace
curl -X POST http://localhost:8799/v1/session/init \
  -d '{"session_id": "session_test", "intent": "Test Trace integration"}'

curl -X POST http://localhost:8799/v1/session/session_test/compress
```

## Troubleshooting

### Issue: "Failed to start Trace MCP server"

**Check:**
1. Trace server path is correct
2. Trace server is Python-based (not Node.js)
3. Python executable exists

**Fix:**
```bash
# Verify Trace server
ls -la /home/jesmosis/trace-server/trace_sde/server.py

# Test Trace server directly
cd ~/trace-server
source venv/bin/activate
python -m trace_sde.server
# Should start and wait for JSON-RPC input
```

### Issue: "MCP client not available" (503 error)

**Cause:** Trace MCP subprocess failed to start

**Fix:**
1. Check logs in terminal where wrapper is running
2. Ensure Trace server dependencies are installed:
   ```bash
   cd ~/trace-server
   source venv/bin/activate
   pip install -e .
   ```

### Issue: Empty responses from Trace

**Cause:** Session doesn't exist or has no data

**Solution:** This is expected behavior. Create sessions first:
```bash
# The wrapper doesn't create sessions automatically
# Use Trace server directly or via another client to create sessions
```

### Issue: Port 8787 already in use

**Fix:**
```bash
# Find what's using the port
lsof -i :8787

# Kill it
kill <PID>

# Or change port in main.py
```

## Development

### Enable Debug Logging

Edit `trace_wrapper/server.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Enable Auto-Reload

Edit `main.py`:

```python
uvicorn.run(
    ...,
    reload=True  # Enable auto-reload for development
)
```

### Run with Custom Trace Command

```python
# In server.py, modify the MCPClient initialization:
mcp_client = MCPClient(trace_command="custom-trace-command")
```

## Production Deployment

### Use Production ASGI Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn trace_wrapper.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8787
```

### Add Authentication

```python
# In routes.py, add API key authentication:
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")

# Add to routes:
@router.get("/sessions", dependencies=[Depends(verify_api_key)])
async def list_sessions(...):
    ...
```

### Configure CORS Properly

```python
# In server.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization"],
)
```

## File Structure

```
trace-http-wrapper/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                  # User documentation
├── SETUP.md                   # This file
├── test_wrapper.py            # Test suite
├── venv/                      # Virtual environment
└── trace_wrapper/
    ├── __init__.py           # Package init
    ├── server.py             # FastAPI app
    ├── routes.py             # API endpoints
    └── mcp_client.py         # MCP protocol client
```

## Next Steps

1. ✅ Start the wrapper: `python3 main.py`
2. ✅ Test it: `python3 test_wrapper.py`
3. ✅ Integrate with MemAgent
4. 🔄 Create sessions and test full workflow
5. 📈 Monitor logs and performance

## Support

For issues:
1. Check logs in terminal where wrapper is running
2. Verify Trace server is accessible
3. Test endpoints with curl
4. Check test suite output

---

**Status:** Ready for testing
**Port:** 8787
**Trace Server:** /home/jesmosis/trace-server/
