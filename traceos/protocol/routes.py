"""
TraceOS Protocol API Routes

FastAPI router for /v1/trace/* endpoints.

Security Warning: These endpoints allow protocol-level operations.
Intended for LOCAL DEVELOPMENT ONLY.

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .schemas import Intent, DeriveOutput, EvaluateOutput, CodifyOutput
from .persistence import ProtocolStorage
from .intent import IntentHandler
from .derive import DeriveHandler
from .evaluate import EvaluateHandler
from .codify import CodifyHandler

# DNA imports (Phase 4)
from traceos.dna.store import DNAStore
from traceos.dna.schemas import StyleSignature

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize storage (will be injected via dependency in production)
storage = ProtocolStorage()

# Initialize DNA store (Phase 4)
dna_store = DNAStore()

# Initialize handlers
intent_handler = IntentHandler(storage)
derive_handler = DeriveHandler(storage)
evaluate_handler = EvaluateHandler(storage)
codify_handler = CodifyHandler(storage, dna_store=dna_store)  # RED TEAM FIX: pass dna_store


# ============================
# REQUEST MODELS
# ============================

class IntentRequest(BaseModel):
    """Request body for creating an intent."""
    title: str
    goals: List[str]
    tags: Optional[List[str]] = None
    spark: str = "Brain"


# ============================
# INTENT ROUTES
# ============================

@router.post("/intent", response_model=Intent, tags=["Protocol"])
async def trace_intent(request: IntentRequest):
    """
    Create a new design intent.

    This is the entry point for all TraceOS development work.
    Every feature starts with an intent.

    Example:
        POST /v1/trace/intent
        {
            "title": "Implement quantum architecture",
            "goals": ["Create QuantumCoProcessor", "Refactor Gut"],
            "tags": ["quantum", "gut-spark"],
            "spark": "Brain"
        }

    Returns:
        Intent object with generated intent_id
    """
    try:
        intent = intent_handler.create_intent(
            title=request.title,
            goals=request.goals,
            tags=request.tags or [],
            spark=request.spark
        )
        return intent
    except Exception as e:
        logger.error(f"Failed to create intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{intent_id}", response_model=Intent, tags=["Protocol"])
async def get_intent(intent_id: str):
    """
    Retrieve an intent by ID.

    Args:
        intent_id: Intent identifier

    Returns:
        Intent object

    Raises:
        404: Intent not found
    """
    intent = intent_handler.get_intent(intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {intent_id} not found")
    return intent


@router.get("/intents", response_model=List[Intent], tags=["Protocol"])
async def list_intents(tags: Optional[List[str]] = Query(None)):
    """
    List all intents, optionally filtered by tags.

    Args:
        tags: Optional tag filter (comma-separated)

    Returns:
        List of matching intents
    """
    return intent_handler.list_intents(tags=tags)


# ============================
# DERIVE ROUTES
# ============================

@router.post("/derive/{intent_id}", response_model=DeriveOutput, tags=["Protocol"])
async def trace_derive(intent_id: str):
    """
    Derive implementation from an intent.

    NOTE: Currently uses STUB implementation.
    Real code generation requires AI workstation (Phase 2+).

    Args:
        intent_id: Intent to derive from

    Returns:
        DeriveOutput with file manifest and provenance

    Raises:
        404: Intent not found
    """
    # Get intent
    intent = intent_handler.get_intent(intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {intent_id} not found")

    try:
        # Derive (currently stub)
        output = derive_handler.derive(intent)
        return output
    except Exception as e:
        logger.error(f"Failed to derive from {intent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/derive/{derive_id}", response_model=DeriveOutput, tags=["Protocol"])
async def get_derivation(derive_id: str):
    """
    Get a previously saved derivation.

    Args:
        derive_id: Derivation identifier

    Returns:
        DeriveOutput object

    Raises:
        404: Derivation not found
    """
    derivation = derive_handler.get_derivation(derive_id)
    if not derivation:
        raise HTTPException(status_code=404, detail=f"Derivation {derive_id} not found")
    return derivation


# ============================
# EVALUATE ROUTES
# ============================

@router.post("/evaluate/{derive_id}", response_model=EvaluateOutput, tags=["Protocol"])
async def trace_evaluate(derive_id: str):
    """
    Multi-Spark evaluation of derived implementation.

    NOTE: Currently uses STUB Spark reviews.
    Real reviews require trained Sparks (Phase 2+).

    Reviews from:
    - Brain: Logic, correctness, patterns
    - Gut: UX, vibe, TraceOS feel
    - Eyes: Visual clarity, diagrams
    - Soul: Values, identity alignment

    Args:
        derive_id: Derivation to evaluate

    Returns:
        EvaluateOutput with multi-Spark reviews

    Raises:
        404: Derivation not found
    """
    # Load existing derivation (do NOT re-derive!)
    derivation = derive_handler.get_derivation(derive_id)
    if not derivation:
        raise HTTPException(status_code=404, detail=f"Derivation {derive_id} not found")

    try:
        # Evaluate (currently stub reviews)
        output = evaluate_handler.evaluate(derivation)
        return output
    except Exception as e:
        logger.error(f"Failed to evaluate {derive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluate/{derive_id}", response_model=EvaluateOutput, tags=["Protocol"])
async def get_evaluation(derive_id: str):
    """
    Get a previously saved evaluation.

    Args:
        derive_id: Derivation identifier

    Returns:
        EvaluateOutput object

    Raises:
        404: Evaluation not found
    """
    evaluation = evaluate_handler.get_evaluation(derive_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation for {derive_id} not found")
    return evaluation


# ============================
# CODIFY ROUTES
# ============================

@router.post("/codify/{derive_id}", response_model=CodifyOutput, tags=["Protocol"])
async def trace_codify(derive_id: str):
    """
    Capture learnings and Creative DNA for an existing derivation.

    RED TEAM FIX: DO NOT re-run derive() or evaluate()!
    Load the previously saved artifacts.

    Args:
        derive_id: ID of existing derivation

    Returns:
        CodifyOutput with patterns, lessons, and DNA signature
    """
    # 1. Load existing derivation (RED TEAM FIX: no re-derivation!)
    derivation = derive_handler.get_derivation(derive_id)
    if not derivation:
        raise HTTPException(
            status_code=404,
            detail=f"Derivation {derive_id} not found"
        )

    # 2. Load existing evaluation (RED TEAM FIX: no re-evaluation!)
    evaluation = evaluate_handler.get_evaluation(derive_id)
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation for {derive_id} not found. Run evaluate first."
        )

    try:
        # 3. Codify (write DNA)
        output = codify_handler.codify(derivation, evaluation)
        return output
    except Exception as e:
        logger.error(f"Failed to codify {derive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/codify/{derive_id}", response_model=CodifyOutput, tags=["Protocol"])
async def get_codification(derive_id: str):
    """
    Get a previously saved codification.

    Args:
        derive_id: Derivation identifier

    Returns:
        CodifyOutput object

    Raises:
        404: Codification not found
    """
    codification = codify_handler.get_codification(derive_id)
    if not codification:
        raise HTTPException(status_code=404, detail=f"Codification for {derive_id} not found")
    return codification


# ============================
# QUANTUM ROUTES
# ============================

@router.post("/quantum/stabilize/{spark_name}", tags=["Quantum"])
async def quantum_stabilize(spark_name: str):
    """
    Manually trigger quantum stabilization for a Spark.

    Currently only GutSpark supports stabilization via the Quantum Organ.
    Future Sparks may implement their own stabilization methods.

    Args:
        spark_name: Name of the Spark to stabilize (e.g., "Gut")

    Returns:
        Stabilization result with energy and solution

    Raises:
        404: Spark not found
    """
    from traceos.sparks.registry import registry

    spark = registry.get(spark_name)
    if not spark:
        raise HTTPException(status_code=404, detail=f"Spark '{spark_name}' not found")

    if not hasattr(spark, "stabilize"):
        return {
            "error": f"Spark '{spark_name}' does not support quantum stabilization",
            "available_sparks": [s.metadata.name for s in registry.get_all() if hasattr(s, "stabilize")]
        }

    result = await spark.stabilize()
    return result


# ============================
# DNA ROUTES (Phase 4)
# ============================

@router.get("/dna/latest", response_model=StyleSignature, tags=["DNA"])
async def get_latest_dna():
    """
    Get the latest creative DNA signature.

    Returns the most recently created style snapshot,
    showing TraceOS's current creative identity.
    """
    sig = dna_store.get_latest_signature()
    if not sig:
        raise HTTPException(
            status_code=404,
            detail="No DNA signatures found. Create an intent and codify it first."
        )
    return sig


@router.get("/dna/signatures", response_model=List[str], tags=["DNA"])
async def list_dna_signatures():
    """
    List all stored DNA signature IDs.

    Returns chronologically ordered list of all creative DNA snapshots.
    """
    return dna_store.list_signature_ids()


@router.get("/dna/signature/{signature_id}", response_model=StyleSignature, tags=["DNA"])
async def get_dna_signature(signature_id: str):
    """
    Get specific DNA signature by ID.

    Retrieve any historical style snapshot for analysis.
    """
    sig = dna_store.load_signature(signature_id)
    if not sig:
        raise HTTPException(
            status_code=404,
            detail=f"DNA signature {signature_id} not found"
        )
    return sig


@router.get("/dna/lineage", response_model=List[dict], tags=["DNA"])
async def get_dna_lineage():
    """
    Get complete DNA lineage graph.

    Shows how creative identity has evolved over time,
    including parent-child relationships and alignment scores.
    """
    lineage = dna_store.load_lineage()
    return [node.model_dump() for node in lineage]
