# 🏗️ TraceOS Iron Monolith + v2.6 Hardening

## What Changed?

TraceOS has been refactored from a distributed microservice architecture into a **unified high-performance monolith** while preserving all v2.6 hardening features.

### Before (Distributed):
```
tracememory:8000 ────┐
                     ├──→ Network calls
orchestrator:8888 ───┘
trace-wrapper:8787 ──→ (stays separate)
```

### After (Iron Monolith):
```
traceos-core:8000 ───→ Single unified app
  ├─ TraceMemory routes: /v1/*
  ├─ Orchestrator routes: /v1/orchestrate/*
  ├─ Critic routes: /v1/critic/*
  └─ Shared in-process state (no HTTP overhead)

trace-wrapper:8787 ──→ (unchanged)
```

---

## Architecture

### Single Unified Entry Point
- **File**: `traceos/main.py`
- **Port**: 8000 only
- **Routes**: All previous routes mounted under single app

### Global Resource Container
- **File**: `traceos/globals.py`
- **Purpose**: Shared state eliminates inter-service HTTP calls
- **Resources**: Database, Storage, DualDNA, Critic, AI Pool

### Lifecycle Management
- **File**: `traceos/lifespan.py`
- **Startup**: Initialize all resources with v2.6 hardening
- **Shutdown**: Explicit cleanup (Parquet writers, ProcessPool, DB)

---

## V2.6 Hardening (Preserved)

All v2.6 hardening features are **active** in the Iron Monolith:

✅ **Task 1**: Multi-process migration locking (portalocker)
✅ **Task 2**: Global storage singleton (dependency injection)
✅ **Task 3**: Explicit Parquet writer lifecycle
✅ **Task 4**: Automatic vector checksums (SHA-256)
✅ **Task 5**: Enhanced migration error handling

**PLUS:**
✅ **Iron Monolith**: ProcessPool for non-blocking AI inference
✅ **Iron Monolith**: SQLite WAL mode for concurrent access
✅ **Iron Monolith**: Real sentence-transformers embeddings (ready when installed)

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build the unified core
docker-compose -f docker-compose.iron-monolith.yml build

# Start services (core + trace-wrapper)
docker-compose -f docker-compose.iron-monolith.yml up -d

# Check logs
docker-compose -f docker-compose.iron-monolith.yml logs -f traceos-core

# Verify health
curl http://localhost:8000/health

# Check detailed status
curl http://localhost:8000/v1/status
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the unified app
uvicorn traceos.main:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
python -m traceos.main
```

---

## API Endpoints

All existing endpoints work **unchanged**, just on port 8000:

### Health & Status
- `GET /` - Root information
- `GET /health` - Fast health check (<10ms even during AI)
- `GET /v1/status` - Detailed status with v2.6 features

### TraceMemory Routes (was port 8000)
- `POST /v1/session/init` - Initialize session
- `GET /v1/session/{session_id}/memory-block` - Get memory
- `POST /v1/session/{session_id}/note` - Add note
- ... all existing `/v1/*` routes

### Orchestrator Routes (was port 8888)
- All orchestrator routes now at `/v1/orchestrate/*`

### Critic Routes (v2.6)
- `POST /v1/critic/critique` - Critique artifact
- `POST /v1/critic/critique-and-ingest` - Critique + ingest

### Documentation
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI

---

## Environment Variables

### Optional (all have fallbacks):

```bash
# Gemini API for critic (falls back to mock mode)
GOOGLE_API_KEY=your_gemini_key

# Claude API for compression
ANTHROPIC_API_KEY=your_claude_key

# Trace MCP URL (default: http://trace-wrapper:8787)
TRACE_MCP_URL=http://localhost:8787

# Log level
LOG_LEVEL=INFO
```

---

## Verification

### Test Health Responsiveness
```bash
# Should respond in <10ms
time curl http://localhost:8000/health
```

### Verify WAL Mode
```bash
sqlite3 data/tracememory.db "PRAGMA journal_mode;"
# Expected: wal
```

### Check Cognitive Kernel Tables
```bash
sqlite3 data/tracememory.db ".tables"
# Expected: cognitive_memory_blocks, style_dna, intent_profiles, telemetry_chunks
```

### Verify V2.6 Features
```bash
curl http://localhost:8000/v1/status | jq '.hardening_features'
# Should show all 5 tasks + iron_monolith_ai_pool as "active"
```

---

## Migration from Old Architecture

If you have existing containers running:

```bash
# Stop old services
docker-compose down

# Backup data (if any)
cp -r data data.backup

# Build and start Iron Monolith
docker-compose -f docker-compose.iron-monolith.yml up -d

# Old endpoints still work (just on port 8000)
```

**No API changes required** - all existing clients work as-is, just point to port 8000.

---

## Resource Requirements

### Minimum:
- **CPU**: 1 core
- **RAM**: 2GB
- **Disk**: 500MB (for models)

### Recommended:
- **CPU**: 2 cores (for ProcessPool)
- **RAM**: 4GB (sentence-transformers + PyTorch)
- **Disk**: 1GB

---

## Files Added

```
traceos/
├── __init__.py            # Package marker
├── globals.py             # Global resource container (116 lines)
├── lifespan.py            # Lifecycle management (185 lines)
└── main.py                # Unified FastAPI app (230 lines)

requirements.txt           # Merged dependencies
Dockerfile.core            # Unified Docker image
docker-compose.iron-monolith.yml  # 2-service compose
IRON_MONOLITH_README.md   # This file
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'sentence_transformers'"

The Iron Monolith is ready to use real embeddings when `sentence-transformers` is installed. Until then, placeholder vectors are used.

To enable real embeddings:
```bash
pip install sentence-transformers torch
```

### "Health check slow during inference"

If health checks timeout, the ProcessPool isn't working. Check logs for ProcessPoolExecutor initialization.

### "SQLITE_BUSY errors"

WAL mode should prevent this. Verify:
```bash
sqlite3 data/tracememory.db "PRAGMA journal_mode;"
```

Should return `wal`. If not, check lifespan.py initialization.

---

## Next Steps

1. ✅ **Deploy**: Use docker-compose.iron-monolith.yml
2. ✅ **Test**: Run verification checks above
3. ✅ **Monitor**: Check `/v1/status` for health
4. 🔜 **Real AI**: Install sentence-transformers for real embeddings
5. 🔜 **Scale**: Add more workers (`--workers 4` in Docker CMD)

---

## Support

- **Docs**: `/docs` endpoint
- **Status**: `/v1/status` endpoint
- **Logs**: `docker-compose -f docker-compose.iron-monolith.yml logs -f`

**Version**: 2.1.0 (Iron Monolith + v2.6 Hardening)
**Architecture**: Unified Modular Monolith
**Production Ready**: ✅
