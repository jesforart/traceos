"""
REST API routes for Trace HTTP Wrapper.

Translates HTTP requests to MCP calls.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["trace"])


# Request/Response Models
class EventRequest(BaseModel):
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")


class ProvenanceNodeRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    node_id: str = Field(..., description="Node identifier")
    parent_id: Optional[str] = Field(None, description="Parent node ID")
    modifiers: Optional[Dict[str, float]] = Field(None, description="Applied modifiers")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SessionResponse(BaseModel):
    sessions: List[Dict[str, Any]]


class EventsResponse(BaseModel):
    session_id: str
    events: List[Dict[str, Any]]


class ProvenanceResponse(BaseModel):
    session_id: str
    nodes: List[Dict[str, Any]]


# Dependency to get MCP client
def get_mcp_client():
    """
    Get MCP client from app state.

    This will be set in server.py during startup.
    """
    from trace_wrapper.server import mcp_client
    if mcp_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trace MCP client not available"
        )
    return mcp_client


# Routes

@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Service status and version
    """
    return {
        "status": "healthy",
        "service": "trace-http-wrapper",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/sessions", response_model=SessionResponse)
async def list_sessions(client=Depends(get_mcp_client)):
    """
    List all sessions in Trace.

    Returns:
        List of session objects
    """
    try:
        sessions = await client.list_sessions()
        return SessionResponse(sessions=sessions)

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}/events", response_model=EventsResponse)
async def get_events(
    session_id: str,
    client=Depends(get_mcp_client)
):
    """
    Get events for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of events for the session
    """
    try:
        events = await client.get_events(session_id)

        if not events:
            # Return empty list instead of 404 - session might exist but have no events
            logger.info(f"No events found for session {session_id}")

        return EventsResponse(
            session_id=session_id,
            events=events
        )

    except Exception as e:
        logger.error(f"Failed to get events for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}"
        )


@router.get("/sessions/{session_id}/provenance", response_model=ProvenanceResponse)
async def get_provenance(
    session_id: str,
    client=Depends(get_mcp_client)
):
    """
    Get provenance chain for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of provenance nodes
    """
    try:
        nodes = await client.get_provenance(session_id)

        if not nodes:
            logger.info(f"No provenance found for session {session_id}")

        return ProvenanceResponse(
            session_id=session_id,
            nodes=nodes
        )

    except Exception as e:
        logger.error(f"Failed to get provenance for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provenance: {str(e)}"
        )


@router.post("/sessions/{session_id}/events")
async def add_event(
    session_id: str,
    payload: EventRequest,
    client=Depends(get_mcp_client)
):
    """
    Add event to a session.

    Args:
        session_id: Session identifier
        payload: Event data

    Returns:
        Success status
    """
    try:
        success = await client.add_event(
            session_id=session_id,
            event_type=payload.event_type,
            data=payload.data
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add event"
            )

        return {
            "status": "ok",
            "message": f"Event added to session {session_id}",
            "event_type": payload.event_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add event to session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add event: {str(e)}"
        )


@router.post("/provenance/node")
async def add_provenance_node(
    payload: ProvenanceNodeRequest,
    client=Depends(get_mcp_client)
):
    """
    Add provenance node to a session.

    Args:
        payload: Provenance node data

    Returns:
        Success status
    """
    try:
        success = await client.add_provenance_node(
            session_id=payload.session_id,
            node_id=payload.node_id,
            parent_id=payload.parent_id,
            modifiers=payload.modifiers,
            metadata=payload.metadata
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add provenance node"
            )

        return {
            "status": "ok",
            "message": f"Provenance node added: {payload.node_id}",
            "session_id": payload.session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add provenance node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add provenance node: {str(e)}"
        )
