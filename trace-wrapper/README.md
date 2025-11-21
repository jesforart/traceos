# Trace HTTP Wrapper

REST API wrapper for Trace MCP server. Exposes Trace functionality via HTTP endpoints.

## Overview

The Trace HTTP Wrapper translates HTTP requests into MCP (Model Context Protocol) calls to the Trace server, enabling REST API access to Trace functionality.

### Architecture

```
HTTP Request → FastAPI → MCPClient → Trace MCP (stdin/stdout) → Response
```

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The wrapper expects Trace MCP server to be available at:
```
node /home/jesmosis/trace-server/build/index.js
```

To customize, modify `trace_command` in `trace_wrapper/mcp_client.py`.

## Running

```bash
# Start the server
python3 main.py
```

Server will start on `http://localhost:8787`

## API Endpoints

### Health Check

```bash
GET /v1/health
```

Returns service status and version.

### List Sessions

```bash
GET /v1/sessions
```

Returns list of all sessions in Trace.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session_abc",
      "created_at": "2025-10-30T...",
      ...
    }
  ]
}
```

### Get Session Events

```bash
GET /v1/sessions/{session_id}/events
```

Returns all events for a session.

**Response:**
```json
{
  "session_id": "session_abc",
  "events": [
    {
      "event_id": "evt_001",
      "event_type": "session.created",
      "timestamp": "2025-10-30T...",
      "data": {...}
    }
  ]
}
```

### Get Provenance Chain

```bash
GET /v1/sessions/{session_id}/provenance
```

Returns provenance chain for a session.

**Response:**
```json
{
  "session_id": "session_abc",
  "nodes": [
    {
      "node_id": "node_001",
      "parent_id": null,
      "modifiers": {...},
      "timestamp": "2025-10-30T..."
    }
  ]
}
```

### Add Event

```bash
POST /v1/sessions/{session_id}/events
```

Add event to a session.

**Request:**
```json
{
  "event_type": "variation.applied",
  "data": {
    "modifier": "hue_shift",
    "value": 0.3
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Event added to session session_abc",
  "event_type": "variation.applied"
}
```

### Add Provenance Node

```bash
POST /v1/provenance/node
```

Add provenance node to a session.

**Request:**
```json
{
  "session_id": "session_abc",
  "node_id": "node_hero_v2",
  "parent_id": "node_hero_v1",
  "modifiers": {
    "stroke_weight": 0.7,
    "hue_shift": 0.3
  },
  "metadata": {
    "variation_applied": true
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Provenance node added: node_hero_v2",
  "session_id": "session_abc"
}
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8787/docs`
- ReDoc: `http://localhost:8787/redoc`

## Usage Examples

### Using curl

```bash
# List sessions
curl http://localhost:8787/v1/sessions

# Get events for a session
curl http://localhost:8787/v1/sessions/session_abc/events

# Add event
curl -X POST http://localhost:8787/v1/sessions/session_abc/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_note.added",
    "data": {"text": "Prefer muted colors"}
  }'
```

### Using Python

```python
import httpx

# List sessions
response = httpx.get("http://localhost:8787/v1/sessions")
sessions = response.json()["sessions"]

# Get events
response = httpx.get("http://localhost:8787/v1/sessions/session_abc/events")
events = response.json()["events"]

# Add event
response = httpx.post(
    "http://localhost:8787/v1/sessions/session_abc/events",
    json={
        "event_type": "variation.applied",
        "data": {"modifier": "hue_shift", "value": 0.3}
    }
)
```

## Integration with MemAgent

Update MemAgent's `TraceClient` to use HTTP instead of MCP:

```python
# In memagent/compression/trace_client.py
async def fetch_events(self, session_id: str) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8787/v1/sessions/{session_id}/events"
        )
        data = response.json()
        return data["events"]
```

## Development

### Running Tests

```bash
pytest
```

### Development Mode

Start with auto-reload:
```python
# In main.py, change reload=True
uvicorn.run(..., reload=True)
```

## Project Structure

```
trace-http-wrapper/
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── README.md                    # Documentation
└── trace_wrapper/
    ├── __init__.py             # Package init
    ├── server.py               # FastAPI application
    ├── routes.py               # API routes
    └── mcp_client.py           # MCP client
```

## Logging

Logs are written to stdout with format:
```
2025-10-30 10:00:00 - trace_wrapper.mcp_client - INFO - Starting Trace MCP server...
```

## Error Handling

- **503**: MCP client not available
- **500**: Internal server or MCP error
- **400**: Invalid request parameters

All errors return JSON:
```json
{
  "detail": "Error message here"
}
```

## Port Configuration

Default port: `8787`

To change, modify `main.py`:
```python
uvicorn.run(..., port=8787)
```

## Security Notes

**Current version is for development/internal use.**

For production:
- Add authentication (API keys, JWT)
- Configure CORS properly (restrict origins)
- Add rate limiting
- Use HTTPS
- Validate all inputs thoroughly

## Troubleshooting

### MCP client fails to start

Check that Trace MCP server is built and path is correct:
```bash
node /home/jesmosis/trace-server/build/index.js
```

### Empty responses

- Verify Trace MCP server is running
- Check logs for MCP communication errors
- Ensure session IDs are correct

### Port already in use

Change port in `main.py` or stop conflicting service:
```bash
lsof -i :8787
kill <PID>
```

## License

MIT

## Version

1.0.0
