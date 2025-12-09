# Changelog

All notable changes to TraceOS are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.5.0] — 2025-12-08

### Added — TraceOS Protocol (Kernel Infrastructure)

**The Intent → Derive → Test → Evaluate → Codify Workflow**

TraceOS v0.5.0 introduces the formal protocol infrastructure that defines how design work flows through the system. This is the "nervous system" for future Spark orchestration.

#### New Module: `traceos/protocol/`

- **Intent Management** (`intent.py`)
  - Create design intents with goals, tags, and metadata
  - Full persistence via JSON storage
  - Searchable intent history

- **Derivation Engine** (`derive.py`)
  - Stub implementation for code generation
  - Provenance tracking for all derivations
  - Ready for Phase 2 LLM integration

- **Multi-Spark Evaluation** (`evaluate.py`)
  - Brain Spark: Logic, correctness, patterns
  - Gut Spark: UX, vibe, TraceOS feel
  - Eyes Spark: Visual clarity, diagrams
  - Soul Spark: Values, identity alignment
  - Stub reviews with production-ready schema

- **Knowledge Codification** (`codify.py`)
  - Captures patterns and lessons from implementations
  - Prepares for Double DNA Engine integration

- **Protocol Persistence** (`persistence.py`)
  - JSON-based storage in `./data/protocol/`
  - Survives server restarts (no amnesia)
  - Ready for SQLite migration

#### New API Endpoints

All mounted at `/v1/trace/*`:

**Intent Routes:**
- `POST /v1/trace/intent` - Create new intent
- `GET /v1/trace/intent/{intent_id}` - Retrieve intent
- `GET /v1/trace/intents?tags=[]` - List intents with optional tag filter

**Derivation Routes:**
- `POST /v1/trace/derive/{intent_id}` - Derive implementation
- `GET /v1/trace/derive/{derive_id}` - Get derivation

**Evaluation Routes:**
- `POST /v1/trace/evaluate/{derive_id}` - Multi-Spark review
- `GET /v1/trace/evaluate/{derive_id}` - Get evaluation

**Codification Routes:**
- `POST /v1/trace/codify/{derive_id}` - Capture learnings
- `GET /v1/trace/codify/{derive_id}` - Get codification

#### Architecture Improvements

- **Clean Router Pattern**: All protocol routes in dedicated `routes.py`
- **No In-Memory Storage**: Full JSON persistence prevents data loss
- **No Re-Derivation**: Evaluate/Codify load existing outputs
- **Async-Ready**: All handlers prepared for future DB/LLM integration
- **Local-First Security**: Endpoints documented as local development only

#### Development Attribution

Protocol v1.0 built through multi-AI collaboration:
- **Claude** (Anthropic): Core architecture, persistence layer, integration
- **ChatGPT** (OpenAI): Formal protocol specification, schema design
- **Gemini** (Google): Red Team review, critical bug detection

#### What's Next (Phase 2+)

- Replace stub derivations with real LLM code generation
- Wire evaluation to trained Spark organs
- Connect to Double DNA Engine
- Add test execution framework
- Quantum architecture implementation via protocol

#### Breaking Changes

None. Protocol is additive feature.

#### Security Notes

`/v1/trace/*` endpoints are for **LOCAL DEVELOPMENT ONLY**. Do not expose these publicly without authentication and network controls.

---

## [0.4.0] — 2025-11-30

### 🎉 Highlights

**Gut Organ Implementation** — TraceOS can now "feel" the artist's emotional state through micro-reaction analysis. The system tastes interactions (rapid undos = bitter frustration, smooth acceptance = sweet flow) and adjusts AI behavior accordingly.

**Sparks Terminology** — Introduced the concept of "Sparks" as artist-bonded trained models that carry Aesthetic DNA and grow through Dream consolidation.

**Multi-AI Development Loop** — This release was built using the traceos-engineering-plugin with contributions from Claude, Gemini, and ChatGPT working in symbiosis.

### Added

- **Gut Valuation System**
  - `tracememory/critic/gut_state.py` — GutCritic class with taste-based emotion detection
  - `tracememory/critic/models/gut_state.py` — Pydantic models for MoodState, ResonanceEvent, GutState
  - `frontend/src/hooks/useResonance.ts` — React hook for capturing micro-reactions
  - `frontend/src/types/gut.ts` — TypeScript types for Gut organ
  - `frontend/src/sovereignty/validateToken.ts` — Sovereignty token validation

- **WebSocket Endpoints**
  - `/v1/gut/ws?session=<id>` — Real-time emotional state streaming
  - `/v1/gut/state?session=<id>` — REST fallback for polling
  - `/v1/gut/clear?session=<id>` — Session cleanup (sovereignty compliance)

- **Brain-Gut Integration**
  - `orchestrator/constraint_engine.py` — Creativity adjustment based on emotional state
  - High frustration (>0.7) reduces AI creativity by 50%
  - Deep flow (>0.8) increases exploration by 30%
  - Chaos state triggers Shadow routing

- **Testing**
  - `tracememory/critic/test_gut_state.py` — 23 comprehensive tests
  - Covers frustration calculation, flow detection, mood transitions, chaos triggers

- **Provenance**
  - `.traceos/provenance/valuation/` — 4 provenance nodes recording all decisions
  - Full lineage from intent_gut_taste_001 to implementation

- **Documentation**
  - `ACKNOWLEDGMENTS.md` — Multi-AI attribution
  - `CHANGELOG.md` — This file
  - Updated `README.md` with organ status and Sparks concept

### Technical Details

- **Rate Limiting**: Token bucket at 100 events/sec with 50ms batching
- **Hysteresis**: 2-second minimum dwell time prevents mood jitter
- **Decay Factor**: 0.95 exponential decay for emotional smoothing
- **Cross-Organ Constraint**: GutState is read-only to non-Valuation organs

### Multi-AI Contributions

| Agent | Contribution |
|-------|--------------|
| Claude | Architecture, sovereignty specs, integration code |
| Gemini | Red Team review, organ metaphor, taste language |
| ChatGPT | Blue Team implementation, micro-valuation research |

---

## [2.1.0] — 2025-11-26

### 🏗️ Iron Monolith Architecture

Refactored from distributed microservices to unified high-performance monolith.

### Added

- `traceos/main.py` — Unified FastAPI entry point
- `traceos/globals.py` — Global resource container
- `traceos/lifespan.py` — Lifecycle management with v2.6 hardening
- ProcessPool for non-blocking AI inference
- SQLite WAL mode for concurrent access

### Changed

- All services now on port 8000
- TraceMemory routes: `/v1/*`
- Orchestrator routes: `/v1/orchestrate/*`
- Critic routes: `/v1/critic/*`

---

## [2.0.6] — 2025-11-23

### 🔒 V2.6 Hardening

### Added

- Task 1: Multi-process migration locking (portalocker)
- Task 2: Global storage singleton
- Task 3: Explicit Parquet writer lifecycle
- Task 4: Automatic vector checksums (SHA-256)
- Task 5: Enhanced migration error handling
- Gemini Critic integration for aesthetic evaluation

---

## [2.0.0] — 2025-10-31

### 🚀 Initial Production Release

### Added

- TraceMemory service (port 8000)
- Trace provenance service (port 8787)
- Orchestrator service (port 8888)
- Docker Compose deployment
- Cognitive Kernel with tri-state memory
- Dual DNA engine for style tracking

---

## Versioning Note

TraceOS uses semantic versioning with the following convention:

- **Major**: Architectural changes (2.x → 3.x)
- **Minor**: New organs or major features (0.3 → 0.4)
- **Patch**: Bug fixes and improvements (0.4.0 → 0.4.1)

The version jumped from 2.x to 0.4.x to reflect the organ-based maturity model:
- v0.x = Foundation organs being built
- v1.0 = All 8 organs operational
- v2.0 = Production hardening complete

---

*Maintained by TraceOS Engineering with multi-AI symbiosis.*
