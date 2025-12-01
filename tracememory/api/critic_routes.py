"""
Critic API routes for Cognitive Kernel v2.5 + Gut Valuation v3.0

RED TEAM FIX #5: Structured JSON output from Gemini API.
INTENT gut_taste_001: WebSocket endpoint for emotional state streaming.

Provides aesthetic critique endpoints integrated with tri-state memory,
plus real-time Gut valuation for emotional state tracking.

@organ valuation
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import base64

from tracememory.critic.gemini_critic import GeminiCritic, AestheticCritique
from tracememory.critic.gut_state import GutCritic
from tracememory.critic.models.gut_state import GutState, ResonanceEvent
from tracememory.storage.memory_storage import MemoryStorage
from tracememory.dual_dna.engine import DualDNAEngine

logger = logging.getLogger(__name__)

# Router with versioning
router = APIRouter(prefix="/v1/critic", tags=["critic"])

# Singleton instances
_critic: Optional[GeminiCritic] = None
_memory_storage: Optional[MemoryStorage] = None
_dual_dna_engine: Optional[DualDNAEngine] = None

# Gut valuation instances (per-session)
_gut_critics: Dict[str, GutCritic] = {}


def get_critic() -> GeminiCritic:
    """
    Dependency injection for GeminiCritic.

    Uses mock mode if GOOGLE_API_KEY not set.
    """
    global _critic
    if _critic is None:
        try:
            # Try to initialize with API key
            _critic = GeminiCritic(mock_mode=False)
            logger.info("GeminiCritic initialized with API key")
        except ValueError:
            # Fall back to mock mode
            _critic = GeminiCritic(mock_mode=True)
            logger.warning("GeminiCritic initialized in MOCK MODE (no API key)")
    return _critic


def get_memory_storage() -> MemoryStorage:
    """Dependency injection for MemoryStorage"""
    global _memory_storage
    if _memory_storage is None:
        # Use default path from configuration
        _memory_storage = MemoryStorage()
        _memory_storage.run_cognitive_kernel_migration()
    return _memory_storage


def get_dual_dna_engine() -> DualDNAEngine:
    """Dependency injection for DualDNAEngine"""
    global _dual_dna_engine
    if _dual_dna_engine is None:
        storage = get_memory_storage()
        _dual_dna_engine = DualDNAEngine(memory_storage=storage)
    return _dual_dna_engine


def get_gut_critic(session_id: str) -> GutCritic:
    """
    Get or create GutCritic for a session.

    Each session has its own GutCritic instance to maintain
    separate emotional state per artist session.

    SOVEREIGNTY: GutState is cleared on session end.
    No cross-session mood persistence without consent.
    """
    global _gut_critics
    if session_id not in _gut_critics:
        _gut_critics[session_id] = GutCritic()
        logger.info(f"[Gut] Created GutCritic for session: {session_id}")
    return _gut_critics[session_id]


def clear_gut_critic(session_id: str) -> None:
    """
    Clear GutCritic for a session.

    Called on session end — no emotional surveillance.
    """
    global _gut_critics
    if session_id in _gut_critics:
        _gut_critics[session_id].clear()
        del _gut_critics[session_id]
        logger.info(f"[Gut] Cleared GutCritic for session: {session_id}")


# Request/Response Models

class CritiqueRequest(BaseModel):
    """Request for artifact critique"""
    session_id: str = Field(..., description="Session identifier")
    artifact_id: str = Field(..., description="Artifact identifier")
    image_data: Optional[str] = Field(
        None,
        description="Base64-encoded image data (PNG/JPEG)"
    )
    svg_data: Optional[str] = Field(
        None,
        description="SVG XML string"
    )
    include_intent: bool = Field(
        default=True,
        description="Include IntentProfile context in critique"
    )


class CritiqueResponse(BaseModel):
    """Response with aesthetic critique"""
    status: str = "ok"
    session_id: str
    artifact_id: str
    critique: Dict[str, Any]  # AestheticCritique serialized
    critique_id: Optional[str] = None
    mock_mode: bool = Field(
        default=False,
        description="True if using mock responses (no API calls)"
    )


# Routes

@router.post("/critique", response_model=CritiqueResponse)
async def critique_artifact(
    payload: CritiqueRequest,
    critic: GeminiCritic = Depends(get_critic),
    storage: MemoryStorage = Depends(get_memory_storage)
):
    """
    Critique an artifact using Gemini 2.0 Flash API.

    RED TEAM FIX #5: Structured JSON output guaranteed.

    Process:
    1. Retrieve artifact from tri-state memory (optional)
    2. Load IntentProfile for context (optional)
    3. Call Gemini API with structured output
    4. Return validated critique JSON

    Request body:
    ```json
    {
        "session_id": "sess_123",
        "artifact_id": "art_456",
        "image_data": "base64...",  // PNG/JPEG (or SVG via svg_data)
        "svg_data": "<svg>...</svg>",  // Alternative to image_data
        "include_intent": true
    }
    ```

    Returns:
    - Structured aesthetic critique with scores (0.0-1.0)
    - Dimension scores: composition, color_harmony, balance, visual_interest, technical_execution
    - Strengths and areas for improvement
    - Style tags

    Errors:
    - 400: Missing image/SVG data
    - 404: Session or artifact not found (if include_intent=true)
    - 500: Gemini API error
    """
    try:
        # Validate input
        if not payload.image_data and not payload.svg_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image_data or svg_data must be provided"
            )

        # Build context from IntentProfile (optional)
        context = None
        if payload.include_intent:
            try:
                # Try to get IntentProfile from memory
                memory_block = storage.get_cognitive_memory_block_by_artifact(
                    payload.session_id,
                    payload.artifact_id
                )

                if memory_block and memory_block.intent_profile_id:
                    intent_profile = storage.get_intent_profile(memory_block.intent_profile_id)
                    if intent_profile:
                        context = {
                            "intent": {
                                "emotional_register": intent_profile.emotional_register,
                                "target_audience": intent_profile.target_audience,
                                "style_keywords": intent_profile.style_keywords
                            }
                        }
                        logger.info(
                            f"Loaded IntentProfile context for critique: {payload.artifact_id}"
                        )
            except Exception as e:
                logger.warning(f"Could not load IntentProfile context: {e}")
                # Continue without context

        # Perform critique
        if payload.svg_data:
            # SVG critique
            logger.info(f"Critiquing SVG artifact: {payload.artifact_id}")
            critique = critic.critique_svg(
                svg_data=payload.svg_data,
                context=context
            )
        else:
            # Image critique
            logger.info(f"Critiquing raster artifact: {payload.artifact_id}")
            image_bytes = base64.b64decode(payload.image_data)

            # Detect MIME type (simple heuristic)
            mime_type = "image/png"
            if image_bytes[:4] == b'\xff\xd8\xff\xe0' or image_bytes[:4] == b'\xff\xd8\xff\xe1':
                mime_type = "image/jpeg"

            critique = critic.critique_image(
                image_data=image_bytes,
                mime_type=mime_type,
                context=context
            )

        logger.info(
            f"Critique complete for {payload.artifact_id}: "
            f"overall_score={critique.overall_score:.2f}"
        )

        return CritiqueResponse(
            status="ok",
            session_id=payload.session_id,
            artifact_id=payload.artifact_id,
            critique=critique.model_dump(),
            mock_mode=critic.mock_mode
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critique failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Critique failed: {str(e)}"
        )


@router.post("/critique-and-ingest")
async def critique_and_ingest(
    payload: CritiqueRequest,
    critic: GeminiCritic = Depends(get_critic),
    engine: DualDNAEngine = Depends(get_dual_dna_engine)
):
    """
    Critique artifact AND ingest into tri-state memory in one operation.

    RED TEAM FIX #5: Structured JSON critique with tri-state integration.

    Process:
    1. Critique artifact using Gemini API
    2. Ingest artifact into tri-state memory (CognitiveMemoryBlock, StyleDNA, IntentProfile)
    3. Attach critique metadata to memory block
    4. Return both critique and ingestion results

    This is a convenience endpoint combining two operations for efficiency.

    Request body: Same as /critique

    Returns:
    - Critique results
    - Ingestion IDs (memory_block_id, style_dna_id, intent_profile_id)

    Errors:
    - 400: Missing image/SVG data
    - 500: Critique or ingestion failed
    """
    try:
        # Validate input
        if not payload.image_data and not payload.svg_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image_data or svg_data must be provided"
            )

        # Step 1: Perform critique
        if payload.svg_data:
            critique = critic.critique_svg(svg_data=payload.svg_data)
        else:
            image_bytes = base64.b64decode(payload.image_data)
            mime_type = "image/png"
            if image_bytes[:4] == b'\xff\xd8\xff\xe0' or image_bytes[:4] == b'\xff\xd8\xff\xe1':
                mime_type = "image/jpeg"
            critique = critic.critique_image(image_data=image_bytes, mime_type=mime_type)

        logger.info(
            f"Critique complete for {payload.artifact_id}: "
            f"overall_score={critique.overall_score:.2f}"
        )

        # Step 2: Build IntentProfile from critique (inferring from critique results)
        intent = {
            "emotional_register": {},  # Could infer from style_tags
            "target_audience": None,
            "style_keywords": critique.style_tags,
            "source": "critic_inferred"
        }

        # Step 3: Ingest into tri-state memory
        memory_block_id, style_dna_id, intent_profile_id = engine.ingest_artifact(
            session_id=payload.session_id,
            artifact_id=payload.artifact_id,
            svg_data=payload.svg_data,
            intent=intent,
            tags=["critiqued"] + critique.style_tags[:3],  # Add critique tags
            notes=f"Overall score: {critique.overall_score:.2f}. {critique.overall_feedback}"
        )

        logger.info(
            f"Artifact ingested with critique: {payload.artifact_id} → {memory_block_id}"
        )

        return {
            "status": "ok",
            "session_id": payload.session_id,
            "artifact_id": payload.artifact_id,
            "critique": critique.model_dump(),
            "ingestion": {
                "memory_block_id": memory_block_id,
                "style_dna_id": style_dna_id,
                "intent_profile_id": intent_profile_id
            },
            "mock_mode": critic.mock_mode
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critique-and-ingest failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Critique-and-ingest failed: {str(e)}"
        )


@router.get("/health")
async def health_check(
    critic: GeminiCritic = Depends(get_critic)
):
    """
    Health check for critic service.

    Returns:
    - Service status
    - Mock mode status
    - Gemini API connectivity (if not mock mode)
    """
    return {
        "status": "healthy",
        "mock_mode": critic.mock_mode,
        "model": critic.model if not critic.mock_mode else None,
        "message": "Critic service operational" + (
            " (MOCK MODE - no API calls)" if critic.mock_mode else ""
        )
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GUT VALUATION ENDPOINTS (intent_gut_taste_001)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# Create a separate router for Gut endpoints (different prefix)
gut_router = APIRouter(prefix="/v1/gut", tags=["gut"])


@gut_router.websocket("/ws")
async def gut_websocket(
    websocket: WebSocket,
    session: str = Query(..., description="Session ID")
):
    """
    WebSocket endpoint for real-time emotional signal streaming.

    The Gut listens here — it feels every interaction event
    and responds with its current emotional state.

    Protocol:
    1. Client connects with ?session=<session_id>
    2. Client sends: { "type": "resonance_batch", "events": [...] }
    3. Server responds: { "type": "gut_state", "state": {...} }

    Events are processed in batches for efficiency.
    The Gut tastes each batch and shares how it feels.

    SOVEREIGNTY: No validation here (handled by frontend).
    Session cleanup clears GutState — no emotional surveillance.

    @provenance intent_gut_taste_001
    @organ valuation
    """
    await websocket.accept()
    logger.info(f"[Gut] WebSocket connected for session: {session}")

    # Get or create GutCritic for this session
    critic = get_gut_critic(session)

    try:
        while True:
            # Wait for messages from the frontend
            msg = await websocket.receive_json()

            if msg.get("type") == "resonance_batch":
                events_data = msg.get("events", [])

                if not events_data:
                    continue

                # Parse events
                events = []
                for e in events_data:
                    try:
                        # Convert camelCase to snake_case
                        event = ResonanceEvent(
                            type=e.get("type"),
                            timestamp=e.get("timestamp"),
                            session_id=e.get("sessionId", session),
                            latency_ms=e.get("latencyMs"),
                            erratic_input=e.get("erraticInput"),
                            context=e.get("context")
                        )
                        events.append(event)
                    except Exception as parse_error:
                        logger.warning(f"[Gut] Failed to parse event: {parse_error}")

                if events:
                    # The Gut tastes this batch of interactions
                    critic.ingest_batch(events)

                    # Share how the Gut feels
                    await websocket.send_json({
                        "type": "gut_state",
                        "state": critic.to_dict()
                    })

    except WebSocketDisconnect:
        # Session ended — the Gut goes quiet
        logger.info(f"[Gut] WebSocket disconnected for session: {session}")
        # Note: Don't clear critic here — session might reconnect
        # Clear on explicit session end or timeout
    except Exception as e:
        logger.error(f"[Gut] WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass


@gut_router.get("/state")
async def get_gut_state(
    session: str = Query(..., description="Session ID")
):
    """
    REST fallback for polling GutState.

    Use the WebSocket endpoint for real-time updates.
    This is a fallback for when WebSocket is unavailable.

    @provenance intent_gut_taste_001
    @organ valuation
    """
    critic = get_gut_critic(session)
    return {
        "status": "ok",
        "session_id": session,
        "state": critic.to_dict()
    }


@gut_router.post("/clear")
async def clear_session_gut(
    session: str = Query(..., description="Session ID")
):
    """
    Clear GutState for a session.

    Called on session end to ensure no emotional surveillance.
    SOVEREIGNTY: Mood data cleared per requirements.

    @provenance intent_gut_taste_001
    @organ valuation
    """
    clear_gut_critic(session)
    return {
        "status": "ok",
        "message": f"GutState cleared for session: {session}"
    }
