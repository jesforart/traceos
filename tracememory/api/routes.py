"""
FastAPI routes for MemAgent service.

Implements all API endpoints:
- Health and status
- Session management
- Memory block operations
- Notes and annotations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, List
import logging

from core.session import SessionManager
from compression.engine import CompressionEngine
from compression.trace_client import TraceClient
from modifiers.engine import ModifierEngine
from modifiers import svg_modifiers  # Register modifiers on import
from models.memory import AssetState, AssetType
from api.models import (
    HealthResponse,
    VersionResponse,
    SessionInitRequest,
    SessionInitResponse,
    MemoryBlockResponse,
    NoteRequest,
    NoteResponse,
    VariationRequest,
    VariationResponse,
    BatchVariationsRequest,
    BatchVariationsResponse,
    AssetUploadRequest,
    AssetUploadResponse,
)
from api.errors import (
    MemAgentException,
    ErrorResponse,
    ErrorCode,
    SessionNotFoundException
)
from config import settings

logger = logging.getLogger(__name__)

# Router with versioning
router = APIRouter(prefix="/v1", tags=["memagent"])

# Singleton instances
_session_manager: Optional[SessionManager] = None
_compression_engine: Optional[CompressionEngine] = None
_trace_client: Optional[TraceClient] = None
_modifier_engine: Optional[ModifierEngine] = None


def get_session_manager() -> SessionManager:
    """
    Dependency injection for SessionManager.

    Returns:
        SessionManager instance (singleton)
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_compression_engine() -> CompressionEngine:
    """
    Dependency injection for CompressionEngine.

    Returns:
        CompressionEngine instance (singleton)
    """
    global _compression_engine
    if _compression_engine is None:
        _compression_engine = CompressionEngine()
    return _compression_engine


def get_trace_client() -> TraceClient:
    """
    Dependency injection for TraceClient.

    Returns:
        TraceClient instance (singleton)
    """
    global _trace_client
    if _trace_client is None:
        _trace_client = TraceClient(settings.TRACE_URL)
    return _trace_client


def get_modifier_engine() -> ModifierEngine:
    """
    Dependency injection for ModifierEngine.

    Returns:
        ModifierEngine instance (singleton)
    """
    global _modifier_engine
    if _modifier_engine is None:
        _modifier_engine = ModifierEngine()
    return _modifier_engine


# ============================================================
# HEALTH & STATUS
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status and component health.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow(),
        components={
            "storage": "healthy",
            "trace": "unknown",  # TODO: ping Trace when implemented
            "hf_model": "healthy" if settings.USE_HF_MODEL else "disabled"
        }
    )


@router.get("/version", response_model=VersionResponse)
async def get_version():
    """
    Return API and service version information.
    """
    return VersionResponse(
        api_version=settings.API_VERSION,
        service_version="1.0.0",
        hf_model=settings.HF_MODEL_PATH if settings.USE_HF_MODEL else None
    )


# ============================================================
# SESSION MANAGEMENT
# ============================================================

@router.post(
    "/session/init",
    response_model=SessionInitResponse,
    status_code=status.HTTP_201_CREATED
)
async def init_session(
    payload: SessionInitRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Initialize MemAgent tracking for a new Trace session.

    Creates:
    - Empty memory container
    - Session state tracking
    - Storage directory structure

    Returns:
    - memory_block_id for referencing this session

    Errors:
    - 409: Session already exists
    - 500: Internal server error
    """
    try:
        memory_block = manager.create_session(
            session_id=payload.session_id,
            intent=payload.intent,
            created_by=payload.created_by
        )

        logger.info(f"Session initialized: {payload.session_id}")

        return SessionInitResponse(
            status="ok",
            memory_block_id=memory_block.memory_block_id,
            session_id=memory_block.session_id
        )

    except MemAgentException:
        raise
    except Exception as e:
        logger.error(f"Session init failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/session/{session_id}/memory-block",
    response_model=MemoryBlockResponse
)
async def get_memory_block(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Get compressed memory block for session.

    Returns:
    - Complete session state
    - Compressed narrative summary
    - Latest asset and modifiers
    - Design DNA and provenance

    Used by:
    - Claude when resuming session
    - UI for state restoration

    Errors:
    - 404: Session not found
    - 500: Internal server error
    """
    try:
        memory_block = manager.get_session(session_id)

        # Convert to response model using model_dump for proper serialization
        # This handles nested Pydantic models like AssetState correctly
        memory_dict = memory_block.model_dump()

        # Map user_preferences to user_notes for API response
        memory_dict['user_notes'] = memory_dict.pop('user_preferences', [])

        return MemoryBlockResponse(**memory_dict)

    except SessionNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Get memory block failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/list")
async def list_sessions(
    limit: int = 100,
    offset: int = 0,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    List all sessions with metadata.

    Query params:
    - limit: Maximum number of sessions to return (default: 100)
    - offset: Number of sessions to skip (default: 0)

    Returns:
    - List of session metadata (session_id, last_updated, size, etc.)
    - Sessions sorted by last_updated (most recent first)
    """
    try:
        sessions = manager.list_sessions(limit=limit, offset=offset)

        return {
            "sessions": sessions,
            "count": len(sessions),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"List sessions failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Delete a session and all associated data.

    This permanently removes:
    - Memory block
    - All assets
    - Backups
    - Index entry

    Errors:
    - 404: Session not found
    - 500: Internal server error
    """
    try:
        manager.delete_session(session_id)
        logger.info(f"Session deleted via API: {session_id}")

    except SessionNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Delete session failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/session/{session_id}/compress")
async def compress_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    compression_engine: CompressionEngine = Depends(get_compression_engine),
    trace_client: TraceClient = Depends(get_trace_client)
):
    """
    Compress session events into memory summary.

    Process:
    1. Fetch events from Trace
    2. Compress using Claude API
    3. Update memory block with compressed summary
    4. Return compression results

    Returns:
    - Compression summary
    - Key decisions extracted
    - Active modifiers
    - User preferences
    - Compression metrics (ratio, tokens)

    Errors:
    - 404: Session not found
    - 500: Compression failed or Claude API error
    """
    try:
        # Verify session exists
        memory_block = manager.get_session(session_id)

        # Fetch events from Trace
        logger.info(f"Fetching events for session: {session_id}")
        events = trace_client.fetch_events(session_id)

        if not events:
            logger.warning(f"No events found for session {session_id}")
            return {
                "status": "ok",
                "message": "No events to compress",
                "events_processed": 0
            }

        # Compress events
        logger.info(f"Compressing {len(events)} events for session: {session_id}")
        result = compression_engine.compress_events(events)

        # Update memory block with compression results
        memory_block.summary = result.summary
        memory_block.key_decisions = result.key_decisions
        memory_block.active_modifiers.update(result.active_modifiers)
        memory_block.user_preferences.extend(result.user_preferences)

        if result.design_intent:
            memory_block.design_intent = result.design_intent

        memory_block.event_count = result.events_processed

        # Save updated memory block
        manager.storage.save_memory_block(memory_block)

        logger.info(
            f"Compression complete for {session_id}: "
            f"{result.events_processed} events → {result.tokens_out} tokens "
            f"(ratio: {result.compression_ratio:.2f}x)"
        )

        # Return results
        return {
            "status": "ok",
            "compression": result.to_dict(),
            "session_id": session_id,
            "memory_block_id": memory_block.memory_block_id
        }

    except SessionNotFoundException:
        raise
    except RuntimeError as e:
        # Compression engine not configured
        logger.error(f"Compression failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Compression failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compression failed: {str(e)}"
        )


# ============================================================
# VARIATIONS & MODIFIERS
# ============================================================

@router.post("/session/{session_id}/variation", response_model=VariationResponse)
async def apply_variation(
    session_id: str,
    payload: VariationRequest,
    manager: SessionManager = Depends(get_session_manager),
    modifier_engine: ModifierEngine = Depends(get_modifier_engine)
):
    """
    Apply single modifier to session's last asset.

    Process:
    1. Get session's latest SVG asset
    2. Apply modifier with specified value
    3. Store result as new asset
    4. Return modified SVG and metadata

    Modifiers:
    - stroke_weight, fill_opacity, hue_shift, scale, rotate
    - brightness, saturation, contrast, blur
    - x_offset, y_offset, skew

    Request body:
    {
        "modifier": "stroke_weight",
        "value": 0.7
    }

    Returns:
    - status: "ok"
    - variant_id: unique ID for this variation
    - svg_data: modified SVG content
    - metadata: modifier info, timestamps, checksums

    Errors:
    - 404: Session not found or no asset exists
    - 400: Invalid modifier or value
    - 500: Modifier application failed
    """
    try:
        # Verify session exists
        memory_block = manager.get_session(session_id)

        # Get last asset
        latest_asset = manager.storage.load_latest_asset(session_id)
        if not latest_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No asset found for session {session_id}"
            )

        # Verify it's SVG
        if latest_asset.type != AssetType.SVG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset must be SVG, got {latest_asset.type}"
            )

        # Apply modifier
        logger.info(f"Applying {payload.modifier}={payload.value} to session {session_id}")
        result = modifier_engine.apply_modifier(
            svg_data=latest_asset.data,
            modifier_name=payload.modifier,
            value=payload.value
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        # Create new asset
        from utils.ulid import generate_ulid
        variant_id = generate_ulid()

        new_asset = AssetState(
            type=AssetType.SVG,
            data=result["svg_data"],
            uri=f"mem://svg/{session_id}/{variant_id}.svg",
            created_at=datetime.utcnow()
        )

        # Save asset
        manager.storage.save_asset(session_id, new_asset)

        # Update memory block
        memory_block.last_asset = new_asset
        memory_block.active_modifiers[payload.modifier] = payload.value
        manager.storage.save_memory_block(memory_block)

        logger.info(
            f"Variation created: {variant_id} "
            f"({payload.modifier}={payload.value}) "
            f"in {result['metadata']['duration_ms']:.2f}ms"
        )

        return VariationResponse(
            status="ok",
            session_id=session_id,
            variant_id=variant_id,
            modifier=payload.modifier,
            value=payload.value,
            svg_data=result["svg_data"],
            metadata=result["metadata"]
        )

    except SessionNotFoundException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Variation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variation failed: {str(e)}"
        )


@router.post("/session/{session_id}/batch-variations", response_model=BatchVariationsResponse)
async def apply_batch_variations(
    session_id: str,
    payload: BatchVariationsRequest,
    manager: SessionManager = Depends(get_session_manager),
    modifier_engine: ModifierEngine = Depends(get_modifier_engine)
):
    """
    Apply multiple modifiers in sequence to create a variation.

    Process:
    1. Get session's latest SVG asset
    2. Apply modifiers sequentially
    3. Store final result
    4. Return composite variation

    Request body:
    {
        "modifiers": {
            "stroke_weight": 0.7,
            "hue_shift": 0.3,
            "fill_opacity": 0.8
        }
    }

    Returns:
    - status: "ok"
    - variant_id: unique ID for this composite variation
    - modifiers_applied: list of applied modifiers with metadata
    - svg_data: final SVG after all modifiers
    - metadata: composite metadata with timing info

    Errors:
    - 404: Session not found or no asset exists
    - 400: Invalid modifier or value
    - 500: Modifier application failed
    """
    try:
        # Verify session exists
        memory_block = manager.get_session(session_id)

        # Get last asset
        latest_asset = manager.storage.load_latest_asset(session_id)
        if not latest_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No asset found for session {session_id}"
            )

        # Verify it's SVG
        if latest_asset.type != AssetType.SVG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset must be SVG, got {latest_asset.type}"
            )

        # Apply multiple modifiers
        logger.info(
            f"Applying batch modifiers to session {session_id}: "
            f"{', '.join([f'{k}={v}' for k, v in payload.modifiers.items()])}"
        )

        result = modifier_engine.apply_multiple(
            svg_data=latest_asset.data,
            modifiers=payload.modifiers
        )

        if not result["success"]:
            # Partial failure - some modifiers failed
            errors = result["metadata"]["errors"]
            error_msg = "; ".join([f"{e['modifier']}: {e['error']}" for e in errors])
            logger.warning(f"Batch variations had errors: {error_msg}")

            # If ALL failed, return error
            if len(result["metadata"]["modifiers_applied"]) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"All modifiers failed: {error_msg}"
                )

        # Create new asset
        from utils.ulid import generate_ulid
        variant_id = generate_ulid()

        new_asset = AssetState(
            type=AssetType.SVG,
            data=result["svg_data"],
            uri=f"mem://svg/{session_id}/{variant_id}.svg",
            created_at=datetime.utcnow()
        )

        # Save asset
        manager.storage.save_asset(session_id, new_asset)

        # Update memory block with ALL modifiers (even if some failed)
        memory_block.last_asset = new_asset
        for modifier_name, value in payload.modifiers.items():
            memory_block.active_modifiers[modifier_name] = value

        manager.storage.save_memory_block(memory_block)

        logger.info(
            f"Batch variation created: {variant_id} "
            f"({len(result['metadata']['modifiers_applied'])} modifiers) "
            f"in {result['metadata']['total_duration_ms']:.2f}ms"
        )

        return BatchVariationsResponse(
            status="ok",
            session_id=session_id,
            variant_id=variant_id,
            modifiers_applied=result["metadata"]["modifiers_applied"],
            svg_data=result["svg_data"],
            metadata=result["metadata"]
        )

    except SessionNotFoundException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch variations failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch variations failed: {str(e)}"
        )


@router.post("/session/{session_id}/asset", response_model=AssetUploadResponse)
async def upload_asset(
    session_id: str,
    payload: AssetUploadRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Upload SVG/PNG/GLTF asset to a session.

    Allows uploading design assets that can be transformed with modifiers.

    Supported types:
    - svg: SVG markup (as string)
    - png: PNG image (base64 encoded)
    - gltf: GLTF 3D model (base64 encoded)

    Request body:
    {
        "type": "svg",
        "data": "<svg>...</svg>",
        "uri": "mem://svg/hero_design.svg"  // optional
    }

    Process:
    1. Get session from SessionManager
    2. Create AssetState with data
    3. Generate URI if not provided
    4. Update memory block's last_asset
    5. Save asset to storage
    6. Return asset metadata

    Returns:
    - status: "ok"
    - asset: metadata (type, uri, size_bytes, created_at)

    Errors:
    - 404: Session not found
    - 413: Asset too large (>10MB)
    - 400: Invalid asset type
    - 500: Storage or internal error
    """
    try:
        # Verify session exists
        memory_block = manager.get_session(session_id)

        # Check asset size
        data_size = len(payload.data.encode('utf-8'))
        max_size = 10 * 1024 * 1024  # 10MB

        if data_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Asset too large: {data_size} bytes (max {max_size} bytes)"
            )

        # Generate URI if not provided
        if payload.uri:
            asset_uri = payload.uri
        else:
            from utils.ulid import generate_ulid
            asset_id = generate_ulid()
            asset_uri = f"mem://{payload.type}/{session_id}/asset_{asset_id}.{payload.type}"

        # Map type string to AssetType enum
        type_map = {
            'svg': AssetType.SVG,
            'png': AssetType.PNG,
            'gltf': AssetType.GLTF
        }

        # Create asset
        asset = AssetState(
            type=type_map[payload.type],
            data=payload.data,
            uri=asset_uri,
            created_at=datetime.utcnow()
        )

        logger.info(
            f"Uploading {payload.type.upper()} asset to session {session_id}: "
            f"{data_size} bytes"
        )

        # Save asset to storage
        asset_path = manager.storage.save_asset(session_id, asset)

        # Update memory block
        memory_block.last_asset = asset
        manager.storage.save_memory_block(memory_block)

        logger.info(f"Asset uploaded successfully: {asset_uri}")

        return AssetUploadResponse(
            status="ok",
            asset={
                "type": payload.type,
                "uri": asset_uri,
                "size_bytes": asset.size_bytes,
                "created_at": asset.created_at.isoformat()
            }
        )

    except SessionNotFoundException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Asset upload failed: {str(e)}"
        )


# ============================================================
# MEMORY & NOTES
# ============================================================

@router.post("/session/{session_id}/note", response_model=NoteResponse)
async def add_note(
    session_id: str,
    payload: NoteRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Add human note to session memory.

    Examples:
    - "user prefers muted palette"
    - "WCAG AA required"
    - "avoid harsh transitions"

    Notes are:
    - Stored in memory block
    - Included in compression
    - Visible to Claude

    Errors:
    - 404: Session not found
    - 400: Invalid note (empty, too long)
    - 500: Internal server error
    """
    try:
        # Validate note length
        if len(payload.text) > 500:
            raise MemAgentException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Note text too long (max 500 characters)",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        manager.add_note(session_id, payload.text)

        return NoteResponse(status="ok")

    except SessionNotFoundException:
        raise
    except MemAgentException:
        raise
    except Exception as e:
        logger.error(f"Add note failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/storage/stats")
async def get_storage_stats(
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Get storage statistics.

    Returns:
    - Total sessions
    - Total storage size
    - Storage path

    Useful for monitoring and maintenance.
    """
    try:
        stats = manager.get_storage_stats()
        return stats

    except Exception as e:
        logger.error(f"Get storage stats failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================
# ADMIN / MAINTENANCE (Future)
# ============================================================

@router.post("/admin/repair-storage")
async def repair_storage(
    manager: SessionManager = Depends(get_session_manager)
):
    """
    Repair storage index by scanning disk.

    Use when:
    - Index corruption detected
    - After manual file operations
    - After restoring from backup

    Note: This is an admin operation and should be authenticated in production.
    """
    try:
        manager.repair_storage()
        return {"status": "ok", "message": "Storage index repaired"}

    except Exception as e:
        logger.error(f"Storage repair failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
