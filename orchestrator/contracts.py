"""
Contract model and storage for agent-to-agent communication.

Contracts track:
- REQUEST: Agent A asks Agent B to do something
- RESPONSE: Agent B responds to Agent A

All contracts are logged to Trace for provenance tracking.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from ulid import ULID
import json
from pathlib import Path


class ContractType(str, Enum):
    """Contract type enum."""
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"


class ContractStatus(str, Enum):
    """Contract status enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Contract(BaseModel):
    """
    Agent-to-agent contract (REQUEST or RESPONSE).
    
    Tracks communication between agents for:
    - Orchestration transparency
    - Provenance tracking
    - Debugging and auditing
    """
    contract_id: str = Field(..., description="Unique contract ID (ULID)")
    session_id: str = Field(..., description="Session this contract belongs to")
    contract_type: ContractType = Field(..., description="REQUEST or RESPONSE")
    
    # Agent information
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    
    # Task information
    capability: Optional[str] = Field(None, description="Required capability")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Contract payload")
    
    # Status tracking
    status: ContractStatus = Field(default=ContractStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Results (for RESPONSE contracts)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "01HCKT5VSXM7YZ4W9P2J3B6F8K",
                "session_id": "session_design_001",
                "contract_type": "REQUEST",
                "from_agent": "orchestrator",
                "to_agent": "agent_image_gen_001",
                "capability": "text_to_image",
                "payload": {
                    "prompt": "A serene landscape with mountains",
                    "style": "realistic"
                },
                "status": "pending"
            }
        }


class ContractStore:
    """
    In-memory contract storage with disk persistence.
    
    Stores contracts by session_id for efficient retrieval.
    Persists to disk for durability.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize contract store.
        
        Args:
            storage_path: Path to store contracts (default: ./data/contracts)
        """
        self.storage_path = storage_path or Path("./data/contracts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage: session_id -> List[Contract]
        self._contracts: Dict[str, List[Contract]] = {}
        
        # Load existing contracts
        self._load_from_disk()
    
    def create_contract(
        self,
        session_id: str,
        contract_type: ContractType,
        from_agent: str,
        to_agent: str,
        capability: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Contract:
        """
        Create a new contract.
        
        Args:
            session_id: Session identifier
            contract_type: REQUEST or RESPONSE
            from_agent: Source agent ID
            to_agent: Target agent ID
            capability: Required capability (for REQUEST)
            payload: Contract payload
        
        Returns:
            Created Contract object
        """
        contract = Contract(
            contract_id=str(ULID()),
            session_id=session_id,
            contract_type=contract_type,
            from_agent=from_agent,
            to_agent=to_agent,
            capability=capability,
            payload=payload or {},
            status=ContractStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Store in memory
        if session_id not in self._contracts:
            self._contracts[session_id] = []
        self._contracts[session_id].append(contract)
        
        # Persist to disk
        self._save_to_disk(session_id)
        
        return contract
    
    def update_contract(
        self,
        contract_id: str,
        status: Optional[ContractStatus] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Contract]:
        """
        Update an existing contract.
        
        Args:
            contract_id: Contract to update
            status: New status
            result: Result data (for RESPONSE)
            error: Error message (if failed)
        
        Returns:
            Updated Contract or None if not found
        """
        # Find contract
        for session_id, contracts in self._contracts.items():
            for contract in contracts:
                if contract.contract_id == contract_id:
                    # Update fields
                    if status:
                        contract.status = status
                    if result:
                        contract.result = result
                    if error:
                        contract.error = error
                    
                    if status in [ContractStatus.COMPLETED, ContractStatus.FAILED]:
                        contract.completed_at = datetime.utcnow()
                    
                    # Persist
                    self._save_to_disk(session_id)
                    return contract
        
        return None
    
    def get_contracts(
        self,
        session_id: Optional[str] = None,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None
    ) -> List[Contract]:
        """
        Get contracts with optional filtering.
        
        Args:
            session_id: Filter by session
            from_agent: Filter by source agent
            to_agent: Filter by target agent
            contract_type: Filter by type (REQUEST/RESPONSE)
            status: Filter by status
        
        Returns:
            List of matching contracts
        """
        # Start with all contracts or just for session
        if session_id:
            contracts = self._contracts.get(session_id, [])
        else:
            contracts = []
            for session_contracts in self._contracts.values():
                contracts.extend(session_contracts)
        
        # Apply filters
        if from_agent:
            contracts = [c for c in contracts if c.from_agent == from_agent]
        if to_agent:
            contracts = [c for c in contracts if c.to_agent == to_agent]
        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]
        if status:
            contracts = [c for c in contracts if c.status == status]
        
        return contracts
    
    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """Get a single contract by ID."""
        for contracts in self._contracts.values():
            for contract in contracts:
                if contract.contract_id == contract_id:
                    return contract
        return None
    
    def get_conversation(self, session_id: str) -> List[Contract]:
        """
        Get all contracts for a session, ordered by time.
        
        Returns conversation flow for compression to MemAgent.
        """
        contracts = self.get_contracts(session_id=session_id)
        return sorted(contracts, key=lambda c: c.created_at)
    
    def _save_to_disk(self, session_id: str):
        """Persist contracts for a session to disk."""
        contracts = self._contracts.get(session_id, [])
        
        file_path = self.storage_path / f"{session_id}.json"
        
        with open(file_path, "w") as f:
            json.dump(
                [contract.model_dump(mode="json") for contract in contracts],
                f,
                indent=2,
                default=str
            )
    
    def _load_from_disk(self):
        """Load all contracts from disk."""
        if not self.storage_path.exists():
            return
        
        for file_path in self.storage_path.glob("*.json"):
            session_id = file_path.stem
            
            with open(file_path, "r") as f:
                contract_dicts = json.load(f)
                contracts = [Contract(**c) for c in contract_dicts]
                self._contracts[session_id] = contracts
    
    def clear_session(self, session_id: str):
        """Clear all contracts for a session."""
        if session_id in self._contracts:
            del self._contracts[session_id]
        
        file_path = self.storage_path / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_contracts = sum(len(contracts) for contracts in self._contracts.values())
        
        # Count by status
        by_status = {}
        for contracts in self._contracts.values():
            for contract in contracts:
                by_status[contract.status] = by_status.get(contract.status, 0) + 1
        
        return {
            "total_sessions": len(self._contracts),
            "total_contracts": total_contracts,
            "by_status": by_status
        }
