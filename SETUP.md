# TraceOS v2.0 Complete Setup

## System Overview

TraceOS v2.0 consists of three microservices:

1. **TraceMemory (Port 8000)**
   - Memory storage (ACID-compliant)
   - Context compression (95% token reduction)
   - 12 SVG modifiers (0.14-0.41ms)
   - Uses driaforall/mem-agent LLM

2. **Trace (Port 8787)**
   - Provenance tracking
   - Design lineage
   - Session management

3. **Orchestrator (Port 8888)**
   - Multi-agent coordination
   - Agent contracts
   - Request routing

## Directory Structure
```
~/traceos/
├── docker-compose.yml
├── tracememory/
├── trace-wrapper/
└── orchestrator/
```

## Configuration

### TraceMemory config.py:
- HOST: "0.0.0.0"
- PORT: 8000
- Model: driaforall/mem-agent

### Docker Networking:
- Network: traceos_traceos
- Internal: http://tracememory:8000
- External: http://localhost:8000

## API Endpoints

All services use `/v1/` prefix:
- `/v1/health` - Health check
- `/v1/session/*` - Session operations
- `/v1/compress` - Compression
- `/v1/modify/*` - Modifiers

## Current Status: ✅ All Healthy
