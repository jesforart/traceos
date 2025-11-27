"""
FastAPI routes for Agent Orchestrator.

Endpoints:
- POST /v1/agents/register - Register new agent
- GET  /v1/agents - List agents
- POST /v1/orchestrate - Execute task
- GET  /v1/contracts - Get contract history
- POST /v1/compress - Compress session to MemAgent
- GET  /v1/status - Get orchestrator status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from orchestrator.core import Orchestrator
from orchestrator.agents import AgentMetadata, AgentCapability, AgentStatus
from orchestrator.contracts import Contract, ContractType, ContractStatus

router = APIRouter()

# Global orchestrator instance (initialized in main.py)
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator


def set_orchestrator(orchestrator: Orchestrator):
    """Set global orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator


# ========== Request/Response Models ==========

class AgentRegisterRequest(BaseModel):
    """Request to register external agent."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="What this agent does")
    capabilities: List[AgentCapability] = Field(..., description="Agent capabilities")
    endpoint: str = Field(..., description="Agent API endpoint")
    version: str = Field(default="1.0.0")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_image_gen_001",
                "name": "ImageGen Agent",
                "description": "Generates images from text",
                "capabilities": [
                    {
                        "name": "text_to_image",
                        "description": "Convert text to image",
                        "parameters": {"prompt": "string"}
                    }
                ],
                "endpoint": "http://localhost:9000",
                "version": "1.0.0"
            }
        }


class AgentRegisterResponse(BaseModel):
    """Response from agent registration."""
    status: str
    agent_id: str
    message: str


class AgentListResponse(BaseModel):
    """Response listing all agents."""
    agents: List[AgentMetadata]
    total: int


class OrchestrateRequest(BaseModel):
    """Request to orchestrate a task."""
    session_id: str = Field(..., description="Session identifier")
    capability: str = Field(..., description="Required capability")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional context")
    intent: Optional[str] = Field(None, description="Session intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_001",
                "capability": "echo",
                "parameters": {
                    "text": "Hello, world!"
                },
                "intent": "Test echo capability"
            }
        }


class OrchestrateResponse(BaseModel):
    """Response from task orchestration."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    contract_id: str
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContractListResponse(BaseModel):
    """Response listing contracts."""
    session_id: Optional[str]
    contracts: List[Contract]
    total: int


class CompressRequest(BaseModel):
    """Request to compress session."""
    session_id: str = Field(..., description="Session to compress")
    intent: Optional[str] = Field(None, description="Session intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_001",
                "intent": "Multi-agent image generation task"
            }
        }


class CompressResponse(BaseModel):
    """Response from compression."""
    status: str
    session_id: str
    compressed: bool
    memory_block: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Orchestrator status response."""
    orchestrator: str
    agents: Dict[str, Any]
    contracts: Dict[str, Any]
    integrations: Dict[str, Any]


# ========== Routes ==========

@router.post("/agents/register", response_model=AgentRegisterResponse)
async def register_agent(
    payload: AgentRegisterRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Register a new external agent.
    
    External agents provide an HTTP endpoint that implements:
    - POST /execute - Execute a task
    - GET /health - Health check
    """
    # Note: This endpoint is for registering external agents
    # Internal agents are registered programmatically via orchestrator.register_agent()
    
    # TODO: Implement external agent wrapper that calls HTTP endpoint
    # For now, return not implemented
    
    raise HTTPException(
        status_code=501,
        detail="External agent registration not yet implemented. Use internal agent registration."
    )


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    List all registered agents.
    
    Returns agent metadata including:
    - Agent ID and name
    - Capabilities
    - Status (available, busy, offline, error)
    - Task statistics
    """
    agents = orchestrator.list_agents()
    
    return AgentListResponse(
        agents=agents,
        total=len(agents)
    )


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_task(
    payload: OrchestrateRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Orchestrate a task to appropriate agent(s).
    
    Process:
    1. Find agent with required capability
    2. Create REQUEST contract
    3. Execute task on agent
    4. Create RESPONSE contract
    5. Log contracts to Trace
    6. Return result
    
    The orchestrator will:
    - Route to available agent with capability
    - Track execution with contracts
    - Log to Trace for provenance
    - Handle errors gracefully
    """
    task = {
        "capability": payload.capability,
        "parameters": payload.parameters,
        "context": payload.context
    }
    
    result = await orchestrator.orchestrate(
        session_id=payload.session_id,
        task=task
    )
    
    return OrchestrateResponse(**result)


@router.get("/contracts", response_model=ContractListResponse)
async def get_contracts(
    session_id: Optional[str] = None,
    from_agent: Optional[str] = None,
    to_agent: Optional[str] = None,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get contract history with optional filtering.
    
    Query parameters:
    - session_id: Filter by session
    - from_agent: Filter by source agent
    - to_agent: Filter by target agent
    
    Returns list of contracts (REQUEST and RESPONSE pairs).
    """
    contracts = orchestrator.get_contracts(
        session_id=session_id,
        from_agent=from_agent,
        to_agent=to_agent
    )
    
    return ContractListResponse(
        session_id=session_id,
        contracts=contracts,
        total=len(contracts)
    )


@router.post("/compress", response_model=CompressResponse)
async def compress_session(
    payload: CompressRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Compress a session's conversation to MemAgent.
    
    Process:
    1. Retrieve all contracts for session
    2. Format as conversation (REQUEST/RESPONSE)
    3. Send to MemAgent compression API
    4. Return compressed memory block
    
    The compressed memory block contains:
    - Session summary
    - Key insights
    - Important events
    - Design decisions (if applicable)
    """
    result = await orchestrator.compress_session(
        session_id=payload.session_id,
        intent=payload.intent
    )
    
    if result:
        return CompressResponse(
            status="ok",
            session_id=payload.session_id,
            compressed=True,
            memory_block=result
        )
    else:
        return CompressResponse(
            status="error",
            session_id=payload.session_id,
            compressed=False,
            error="Failed to compress session. Check that MemAgent is running."
        )


@router.get("/status", response_model=StatusResponse)
async def get_status(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    Get orchestrator status.
    
    Returns:
    - Orchestrator health
    - Registered agents and their status
    - Contract statistics
    - Integration health (MemAgent, Trace)
    """
    status = await orchestrator.get_status()
    return StatusResponse(**status)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "agent-orchestrator",
        "status": "healthy",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "agent-orchestrator",
        "description": "Multi-agent coordination for TraceOS",
        "version": "1.0.0",
        "endpoints": {
            "health": "/v1/health",
            "status": "/v1/status",
            "agents": "/v1/agents",
            "orchestrate": "/v1/orchestrate",
            "contracts": "/v1/contracts",
            "compress": "/v1/compress"
        },
        "docs": "/docs"
    }
