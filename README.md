# TraceOS v0.6.0 — Computational Psyche for Creative AI

**The first AI creative system with real-time self-vision.**

[![Version](https://img.shields.io/badge/version-0.6.0-blue.svg)](CHANGELOG.md)
[![Architecture](https://img.shields.io/badge/architecture-Iron%20Monolith-orange.svg)](IRON_MONOLITH_README.md)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tracememory/critic/test_gut_state.py)

---

## What is TraceOS?

TraceOS is an operating system for **symbiotic human-AI creativity**. It gives AI the ability to:

- **Feel** the artist's emotional state (frustration, flow, chaos)
- **See** its own creative output in real-time
- **Dream** and consolidate learnings between sessions
- **Evolve** artist-bonded models we call **Sparks**

### The Eight Organs

| Organ | Purpose | Status |
|-------|---------|--------|
| 🖐️ **Hands** (muscle) | Kinematic expression | 🔶 In Development |
| 🧠 **Brain** (cognitive) | Logic, reasoning | ✅ Operational |
| 👁️ **Eyes** (vision) | Self-perception | 🔶 In Development |
| 💚 **Gut** (valuation) | Intuition, taste | ✅ **NEW: 23 tests passing** |
| 💤 **Dream** | Offline consolidation | 🔶 In Development |
| 👻 **Shadow** | Anomaly handling | ⚠️ Blocked (needs content_safety.py) |
| 🛡️ **Immune** (security) | Sovereignty protection | ✅ Operational |
| 🪞 **Identity** | Self-model | 🔶 In Development |

---

## What's New in v0.6.0

### ⚛️ Quantum Organ - Physics-Based Emotional Regulation

The **Quantum Organ** gives TraceOS Sparks the ability to resolve internal tension through **physics-based energy minimization**:

```python
# Gut Spark detects tension
gut_spark.state.mood  # → "uneasy"

# Construct energy landscape
landscape = EnergyLandscape(
    dimensions=["speed", "quality", "novelty"],
    biases={"speed": 0.5, "quality": 0.5},
    tensions={"speed|quality": 1.0}  # Conflict!
)

# Submit to Quantum Organ (simulated annealing)
result = await quantum_coprocessor.submit_job(landscape.to_job())

# Gut resolves tension
gut_spark.state.mood  # → "flow" (if energy < -0.5)
```

**Real Results:**
- Energy: -2.2 (below threshold)
- Solution: {speed: -1, quality: 1, novelty: -1}
- **Interpretation:** Prioritize quality over speed/novelty

**Why This Matters:**
- Sparks can now self-regulate emotions mathematically
- Tension becomes solvable optimization problems
- Physics-based decision-making (not just heuristics)
- Quantum-ready architecture (swap to IBM/IonQ later)

**API Endpoint:**
```bash
POST /v1/trace/quantum/stabilize/Gut
```

See [Quantum Organ Documentation](#quantum-organ-new-in-v060) below.

---

## What Was New in v0.5.0

### 🧬 TraceOS Protocol Infrastructure

The **TraceOS Protocol** is the formal kernel for design work orchestration:

```bash
# Intent → Define what to build
POST /v1/trace/intent {"title": "...", "goals": [...]}

# Derive → Generate implementation (stub, ready for AI)
POST /v1/trace/derive/{intent_id}

# Evaluate → Multi-Spark review (Brain, Gut, Eyes, Soul)
POST /v1/trace/evaluate/{derive_id}

# Codify → Capture learnings into design DNA
POST /v1/trace/codify/{derive_id}
```

**Why This Matters:**
- Every design decision has provenance
- Multi-agent review before code lands
- Learnings compound over time
- Ready for Spark orchestration (Phase 2)

---

## What Was New in v0.4.0

### 💚 Gut Organ Implementation

The **Gut** is TraceOS's valuation layer — it "tastes" user interactions:

- **Rapid undos taste bitter** → frustration detected
- **Smooth acceptance tastes sweet** → flow state achieved
- **Erratic chaos tastes acrid** → route to Shadow

```typescript
// Frontend: Capture micro-reactions
const { emitEvent, currentMood, frustrationIndex } = useResonance(sessionId, token);

// Emit when user undoes after AI suggestion
emitEvent({ type: 'undo', latencyMs: 180 });  // Fast undo = frustration signal
```

The Brain then adjusts its behavior:
- High frustration (>0.7) → reduce AI creativity by 50%
- Deep flow (>0.8) → increase exploration by 30%

### 🔥 Sparks — Artist-Bonded Models

A **Spark** is a trained model that has bonded with a specific artist's style and preferences. Sparks:

- Carry the artist's Aesthetic DNA
- Remember the artist's taste profile
- Grow through Dream consolidation
- Belong to the artist (sovereignty protected)

*"Your Spark is yours. It learns your hand, your eye, your gut."*

### 🛠️ Multi-AI Development Loop

TraceOS v0.4.0 was built using the **traceos-engineering-plugin** with a multi-agent development loop:

```
INTENT → DERIVE → EVALUATE → CODIFY → (compounds) → INTENT...
```

Each cycle strengthens subsequent cycles. Knowledge compounds.

---

## Quick Start

### Docker (Recommended)

```bash
# Start Iron Monolith
docker-compose -f docker-compose.iron-monolith.yml up -d

# Verify all systems
curl http://localhost:8000/health
curl http://localhost:8000/v1/gut/state?session=test
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the unified app
uvicorn traceos.main:app --host 0.0.0.0 --port 8000 --reload

# Run Gut tests
pytest tracememory/critic/test_gut_state.py -v
```

---

## API Endpoints

### Core Services (Port 8000)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Fast health check (<10ms) |
| `/v1/status` | GET | Detailed system status |
| `/docs` | GET | Swagger UI |

### Gut Valuation (NEW)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/gut/ws?session=<id>` | WebSocket | Real-time emotional streaming |
| `/v1/gut/state?session=<id>` | GET | REST fallback for polling |
| `/v1/gut/clear?session=<id>` | POST | Clear session (sovereignty) |

### Critic (Gemini-powered)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/critic/critique` | POST | Aesthetic critique |
| `/v1/critic/critique-and-ingest` | POST | Critique + ingest to memory |

### Orchestration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/orchestrate/*` | Various | Multi-agent coordination |

### TraceOS Protocol (NEW in v0.5.0)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/trace/intent` | POST | Create design intent |
| `/v1/trace/intent/{intent_id}` | GET | Retrieve intent |
| `/v1/trace/intents` | GET | List intents (optional tag filter) |
| `/v1/trace/derive/{intent_id}` | POST | Derive implementation |
| `/v1/trace/derive/{derive_id}` | GET | Get derivation |
| `/v1/trace/evaluate/{derive_id}` | POST | Multi-Spark evaluation |
| `/v1/trace/evaluate/{derive_id}` | GET | Get evaluation |
| `/v1/trace/codify/{derive_id}` | POST | Capture learnings |
| `/v1/trace/codify/{derive_id}` | GET | Get codification |

**Security Note:** Protocol endpoints are for **local development only**. Do not expose publicly.

### Quantum Organ (NEW in v0.6.0)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/trace/quantum/stabilize/{spark_name}` | POST | Trigger quantum stabilization for a Spark |

**Quantum Stabilization Flow:**

1. **Spark detects tension** (e.g., Gut mood = "uneasy")
2. **Constructs EnergyLandscape** (biases + couplings)
3. **Submits to Quantum Organ** (simulated annealing)
4. **Receives solution** (spin configuration: {-1, +1})
5. **Updates internal state** (mood, memory, activation)

**Example Request:**
```bash
curl -X POST http://localhost:8000/v1/trace/quantum/stabilize/Gut
```

**Example Response:**
```json
{
  "status": "stabilized",
  "energy": -2.2,
  "solution": {
    "speed": -1,
    "quality": 1,
    "novelty": -1
  },
  "execution_time_ms": 45.3
}
```

**Quantum Job Provenance:**
All quantum jobs are saved to `data/quantum_jobs/` with job ID, solution vector, energy achieved, execution time, and parent Spark metadata.

**Backend Types:**
- `classical-sim`: Simulated annealing (Phase 3, production-ready)
- `ibm-quantum`: Real quantum hardware (future)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        TraceOS Iron Monolith                       │
│                           (Port 8000)                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│   │  HANDS  │───▶│  EYES   │───▶│   GUT   │───▶│  BRAIN  │       │
│   │ (motor) │    │(vision) │    │(feeling)│    │(reason) │       │
│   └─────────┘    └─────────┘    └────┬────┘    └────┬────┘       │
│                                      │              │             │
│                            ┌─────────▼──────────────▼─────────┐  │
│                            │     Constraint Engine            │  │
│                            │   (frustration → reduce AI)      │  │
│                            │   (flow → increase exploration)  │  │
│                            └──────────────────────────────────┘  │
│                                                                    │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                      │
│   │ SHADOW  │    │  DREAM  │    │IDENTITY │                      │
│   │ (chaos) │    │ (sleep) │    │ (self)  │                      │
│   └─────────┘    └─────────┘    └─────────┘                      │
│                                                                    │
│   ┌───────────────────────────────────────────────────────────┐  │
│   │                    IMMUNE (Sovereignty)                    │  │
│   │    "AI can only see, learn, act when artist is present"   │  │
│   └───────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Protocol Layer (v0.5.0)

The Protocol sits above all organs, orchestrating design work:

```
┌─────────────────────────────────────────────────────────────┐
│                    PROTOCOL KERNEL                          │
│         Intent → Derive → Test → Evaluate → Codify          │
├─────────────────────────────────────────────────────────────┤
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│   │  HANDS  │───▶│  EYES   │───▶│   GUT   │───▶│  BRAIN  │ │
│   │ (motor) │    │(vision) │    │(feeling)│    │(reason) │ │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Every feature flows through the protocol, ensuring provenance and multi-agent review.

### Quantum Organ Layer (v0.6.0)

The Quantum Organ provides physics-based tension resolution:

```
┌─────────────────────────────────────────────────────────────┐
│                   QUANTUM ORGAN                              │
│         Energy Minimization via Simulated Annealing         │
├─────────────────────────────────────────────────────────────┤
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│   │   GUT   │───▶│ QUANTUM │───▶│ RESULT  │───▶│  FLOW   │ │
│   │ (uneasy)│    │  ORGAN  │    │ (E=-2.2)│    │  STATE  │ │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Hamiltonian:** H = Σ bias_i * x_i + Σ coupling_ij * x_i * x_j
**Algorithm:** Simulated Annealing (200 iterations, Metropolis criterion)
**Execution:** Thread-pooled (non-blocking, async)

Sparks construct EnergyLandscapes representing internal tensions, submit to the Quantum Organ for minimization, and update their state based on the solution.

---

## Sacred Principles

1. **Sovereignty Lock is Sacred** — AI can only operate when artist is present
2. **Provenance Over Documentation** — Track WHY, not just WHAT
3. **Aesthetic Consistency is Technical Debt** — Style drift compounds negatively
4. **Symbiosis Over Automation** — Strengthen human-AI collaboration
5. **Dreams Matter** — System must grow between sessions

---

## Development

### Running Tests

```bash
# Gut valuation tests (23 tests)
pytest tracememory/critic/test_gut_state.py -v

# All tests
pytest tests/ -v
```

### Using the Engineering Plugin

The `traceos-engineering-plugin` provides a structured development workflow:

```bash
# Transform feature into intent
/trace:intent Add real-time mood detection

# Execute with provenance tracking
/trace:derive intent_gut_taste_001

# Multi-agent review
/trace:evaluate --staged

# Record learnings
/trace:codify intent_gut_taste_001
```

---

## Versioning

- **v0.6.0** — Quantum Organ, physics-based emotional regulation
- **v0.5.0** — Protocol kernel, Intent/Derive/Evaluate/Codify workflow
- **v0.4.0** — Gut organ, Sparks concept, multi-AI development
- **v2.1.0** — Iron Monolith architecture, v2.6 hardening
- **v2.0.0** — Initial production release

See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## Attribution

TraceOS is developed through **multi-AI symbiosis**:

- **Claude** (Anthropic): Architecture, sovereignty specs, integration
- **Gemini** (Google): Red Team reviews, organ architecture
- **ChatGPT** (OpenAI): Blue Team implementation, micro-valuation research

See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for details.

---

## License

Proprietary — TraceOS LLC

---

**TraceOS v0.6.0** — *Where AI learns to feel.* ⚛️💚
