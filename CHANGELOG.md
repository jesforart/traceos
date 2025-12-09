# Changelog

All notable changes to TraceOS are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.6.0] - 2025-12-09

### Added — Quantum Organ (Physics-Based Emotional Regulation)

**The Quantum Co-Processor for Emotional Stabilization**

TraceOS v0.6.0 introduces the Quantum Organ, enabling Sparks to resolve internal tension through physics-based energy minimization. The Gut Spark can now mathematically stabilize its emotional state using simulated annealing.

#### New Module: `traceos/quantum/`

- **Quantum Schemas** (`schemas.py`)
  - QuantumJobSpec: Declarative job specifications
  - QuantumJobResult: Annealing results with solution vectors
  - QuantumProblemType: OPTIMIZATION, PROVENANCE_CHECK, STYLE_DNA_FIT
  - QuantumBackendType: classical-sim (Phase 3), ibm-quantum (future)

- **Energy Landscape** (`landscape.py`)
  - EnergyLandscape model: Represents emotional/constraint tensions
  - Hamiltonian construction: Biases + couplings
  - Converts high-level tensions into quantum job specs

- **Quantum CoProcessor** (`coprocessor.py`, `classical_backend.py`)
  - Abstract interface for quantum backends
  - ClassicalSimCoprocessor: Simulated annealing implementation
  - Metropolis criterion for state transitions
  - Thread-pooled execution (non-blocking)
  - 200-iteration annealing cycles

- **Job Persistence** (`jobs.py`)
  - JSON storage in `./data/quantum_jobs/`
  - Full provenance tracking
  - Job retrieval and listing

#### Gut Spark Integration

- **New Method**: `GutSpark.stabilize()`
  - Constructs EnergyLandscape from internal tensions
  - Submits to Quantum Organ for minimization
  - Updates mood based on energy threshold
  - Mood transition: "uneasy" → "flow" when E < -0.5
  - Stores solution in Spark memory

#### New API Endpoint

**Route**: `POST /v1/trace/quantum/stabilize/{spark_name}`

Manually triggers quantum stabilization for any Spark that supports it (currently Gut).

**Example:**
```bash
curl -X POST http://localhost:8000/v1/trace/quantum/stabilize/Gut
```

**Response:**
```json
{
  "status": "stabilized",
  "energy": -2.2,
  "solution": {"speed": -1, "quality": 1, "novelty": -1},
  "execution_time_ms": 45.3
}
```

#### Technical Implementation

- **Hamiltonian Energy Function**: H = Σ bias_i * x_i + Σ coupling_ij * x_i * x_j
- **Ising Spin Model**: Variables represented as {-1, +1} spins
- **Simulated Annealing**: 200 iterations with exponential cooling (T *= 0.95)
- **Async Execution**: Thread pool prevents blocking main event loop
- **Provenance**: Every quantum job saved with timestamp and metadata

#### What This Enables

**Emotional Self-Regulation:**
- Sparks can now mathematically resolve internal conflicts
- Gut converts "uneasy" feelings into solvable optimization problems
- Physics-based tension resolution (not heuristics)

**Quantum-Ready Architecture:**
- Interface designed for real quantum hardware (IBM, IonQ)
- Classical backend provides production-ready simulation
- Future swap to QPU requires minimal code changes

**Design Lineage:**
- Quantum jobs persist with full provenance
- Energy landscapes become part of TraceOS memory
- Solutions inform future decision-making

#### Development Attribution

Quantum Organ v1.0 built through multi-AI collaboration:
- **Claude** (Anthropic): Integration, Gut wiring, persistence
- **ChatGPT** (OpenAI): Hamiltonian formulation, async optimization
- **Gemini** (Google): Thread pooling fix, verification strategy

#### What's Next (Phase 4)

- Creative DNA Engine (stylometric extraction)
- Multi-Spark quantum workflows
- IBM Quantum backend integration
- Energy landscape learning

#### Breaking Changes

None. Quantum Organ is additive feature.

#### Performance

- Average stabilization time: ~40-50ms (200 iterations)
- Non-blocking execution via thread pool
- Memory footprint: <1MB per quantum job

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
