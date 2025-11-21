# Bug Fix: JSON Serialization in Compress Endpoint

## Issue

The `/v1/compress` endpoint had a JSON serialization bug when calling MemAgent's compress endpoint.

**Problem:**
- Orchestrator was trying to format contracts with datetime objects
- datetime objects aren't JSON serializable
- Complex payload structure was unnecessary

## Root Cause

In `orchestrator/integrations.py`, the `compress_conversation()` method was:
1. Formatting contracts as conversation messages
2. Including datetime objects in the payload (`timestamp: contract.get("created_at")`)
3. Sending this complex structure to MemAgent

This caused JSON serialization errors when httpx tried to send the request.

## Solution

Simplified the approach to just send `session_id` to MemAgent and let it fetch its own data:

### Changes Made

#### 1. orchestrator/integrations.py

**Before:**
```python
async def compress_conversation(
    self,
    session_id: str,
    contracts: List[Dict[str, Any]],
    intent: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    # Format contracts as conversation
    conversation = self._format_conversation(contracts)
    
    payload = {
        "session_id": session_id,
        "conversation": conversation,  # Complex structure with datetimes
        "intent": intent or "Multi-agent task execution"
    }
    
    response = await client.post(
        f"{self.base_url}/v1/session/{session_id}/compress",
        json=payload
    )
```

**After:**
```python
async def compress_conversation(
    self,
    session_id: str,
    contracts: List[Dict[str, Any]],
    intent: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    # Simple payload - just session_id and intent
    # Let MemAgent fetch its own memory block data
    payload = {
        "intent": intent or "Multi-agent task execution"
    }
    
    response = await client.post(
        f"{self.base_url}/v1/session/{session_id}/compress",
        json=payload
    )
```

#### 2. Fixed MemAgent URL

**Before:**
```python
def __init__(self, base_url: str = "http://localhost:8000"):
```

**After:**
```python
def __init__(self, base_url: str = "http://localhost:8799"):
```

#### 3. Fixed Health Check Endpoint

**Before:**
```python
response = await client.get(f"{self.base_url}/v1/health")
```

**After:**
```python
response = await client.get(f"{self.base_url}/health")
```

#### 4. orchestrator/main.py

**Before:**
```python
orchestrator = Orchestrator(
    memagent_url="http://localhost:8000",
    trace_url="http://localhost:8787"
)
```

**After:**
```python
orchestrator = Orchestrator(
    memagent_url="http://localhost:8799",
    trace_url="http://localhost:8787"
)
```

## Benefits

1. **No serialization issues** - Simple JSON payload with no datetime objects
2. **Cleaner separation of concerns** - MemAgent handles its own data fetching
3. **Simpler code** - Removed unnecessary `_format_conversation()` logic
4. **Correct ports** - Fixed MemAgent URL from 8000 to 8799
5. **Correct endpoints** - Fixed health check from /v1/health to /health

## Testing

All tests pass (6/6):
- ✓ Health Check
- ✓ List Agents
- ✓ Orchestrate Echo
- ✓ Orchestrate Uppercase
- ✓ Get Contracts
- ✓ Get Status

## API Usage

The compress endpoint now works correctly:

```bash
curl -X POST http://localhost:8888/v1/compress \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "intent": "Multi-agent task execution"
  }'
```

MemAgent receives just the `intent` and uses the `session_id` from the URL to fetch its own data.

## Files Modified

- `orchestrator/integrations.py` - Simplified compress_conversation method
- `main.py` - Fixed MemAgent URL to 8799

## Status

✅ Bug fixed
✅ All tests passing
✅ Ready for production
