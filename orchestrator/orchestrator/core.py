"""
Core orchestrator for multi-agent coordination.

Manages:
- Agent registration and discovery
- Task routing to appropriate agents
- Contract creation and tracking
- Integration with Trace and MemAgent
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ulid import ULID

from orchestrator.agents import Agent, AgentStatus, AgentMetadata, AgentCapability
from orchestrator.contracts import (
    Contract,
    ContractStore,
    ContractType,
    ContractStatus
)
from orchestrator.integrations import IntegrationManager

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Multi-agent orchestrator.
    
    Core responsibilities:
    1. Agent registry - register/deregister agents
    2. Task routing - route tasks to capable agents
    3. Contract management - track agent communication
    4. Integration - log to Trace, compress to MemAgent
    
    Usage:
        orchestrator = Orchestrator()
        
        # Register agents
        orchestrator.register_agent(my_agent)
        
        # Execute task
        result = await orchestrator.orchestrate(
            session_id="session_001",
            task={
                "capability": "image_generation",
                "parameters": {"prompt": "A sunset"}
            }
        )
    """
    
    def __init__(
        self,
        memagent_url: str = "http://localhost:8000",
        trace_url: str = "http://localhost:8787"
    ):
        """
        Initialize orchestrator.
        
        Args:
            memagent_url: MemAgent base URL
            trace_url: Trace HTTP Wrapper base URL
        """
        # Agent registry
        self._agents: Dict[str, Agent] = {}
        
        # Contract storage
        self.contracts = ContractStore()
        
        # Integrations
        self.integrations = IntegrationManager(memagent_url, trace_url)
        
        logger.info("Orchestrator initialized")
    
    # ========== Agent Management ==========
    
    def register_agent(self, agent: Agent) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: Agent instance to register
        
        Returns:
            True if registered, False if already exists
        """
        agent_id = agent.metadata.agent_id
        
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} already registered")
            return False
        
        self._agents[agent_id] = agent
        agent.update_status(AgentStatus.AVAILABLE)
        
        logger.info(f"Registered agent: {agent_id} ({agent.metadata.name})")
        logger.info(f"  Capabilities: {[c.name for c in agent.metadata.capabilities]}")
        
        return True
    
    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            True if deregistered, False if not found
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        del self._agents[agent_id]
        logger.info(f"Deregistered agent: {agent_id}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[AgentMetadata]:
        """List all registered agents."""
        return [agent.metadata for agent in self._agents.values()]
    
    def find_agent_by_capability(self, capability: str) -> Optional[Agent]:
        """
        Find an available agent that can handle a capability.
        
        Args:
            capability: Required capability name
        
        Returns:
            Agent instance or None if no capable agent available
        """
        for agent in self._agents.values():
            if (agent.metadata.status == AgentStatus.AVAILABLE and
                agent.can_handle(capability)):
                return agent
        
        return None
    
    # ========== Task Orchestration ==========
    
    async def orchestrate(
        self,
        session_id: str,
        task: Dict[str, Any],
        from_agent: str = "orchestrator"
    ) -> Dict[str, Any]:
        """
        Orchestrate a task to appropriate agent(s).
        
        Args:
            session_id: Session identifier
            task: Task dictionary with:
                - capability: Required capability
                - parameters: Task parameters
                - context: Optional context
            from_agent: Source agent (default: "orchestrator")
        
        Returns:
            Result dictionary with:
                - success: bool
                - data: Result data (if success)
                - error: Error message (if failed)
                - contract_id: Contract ID for tracking
        """
        capability = task.get("capability")
        parameters = task.get("parameters", {})
        
        logger.info(f"Orchestrating task: {capability}")
        
        # Find capable agent
        agent = self.find_agent_by_capability(capability)
        
        if not agent:
            error_msg = f"No agent available for capability: {capability}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        agent_id = agent.metadata.agent_id
        logger.info(f"Routing to agent: {agent_id}")
        
        # Create REQUEST contract
        request_contract = self.contracts.create_contract(
            session_id=session_id,
            contract_type=ContractType.REQUEST,
            from_agent=from_agent,
            to_agent=agent_id,
            capability=capability,
            payload=parameters
        )
        
        # Log to Trace
        await self.integrations.log_contract(
            session_id,
            request_contract.model_dump()
        )
        
        # Update contract status
        self.contracts.update_contract(
            request_contract.contract_id,
            status=ContractStatus.IN_PROGRESS
        )
        
        # Execute task
        try:
            agent.update_status(AgentStatus.BUSY)
            
            result = await agent.execute({
                "task_id": request_contract.contract_id,
                "capability": capability,
                "parameters": parameters,
                "context": task.get("context", {})
            })
            
            # Update agent
            agent.update_status(AgentStatus.AVAILABLE)
            agent.increment_task_count(success=result.get("success", False))
            
            # Update REQUEST contract
            if result.get("success"):
                self.contracts.update_contract(
                    request_contract.contract_id,
                    status=ContractStatus.COMPLETED,
                    result=result.get("data")
                )
            else:
                self.contracts.update_contract(
                    request_contract.contract_id,
                    status=ContractStatus.FAILED,
                    error=result.get("error")
                )
            
            # Create RESPONSE contract
            response_contract = self.contracts.create_contract(
                session_id=session_id,
                contract_type=ContractType.RESPONSE,
                from_agent=agent_id,
                to_agent=from_agent,
                payload=result
            )
            
            response_contract.status = ContractStatus.COMPLETED
            response_contract.result = result.get("data")
            response_contract.error = result.get("error")
            
            # Log RESPONSE to Trace
            await self.integrations.log_contract(
                session_id,
                response_contract.model_dump()
            )
            
            # Return result with contract ID
            return {
                **result,
                "contract_id": request_contract.contract_id,
                "agent_id": agent_id
            }
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            
            # Mark agent as error
            agent.update_status(AgentStatus.ERROR)
            agent.increment_task_count(success=False)
            
            # Update contract
            self.contracts.update_contract(
                request_contract.contract_id,
                status=ContractStatus.FAILED,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "contract_id": request_contract.contract_id,
                "agent_id": agent_id
            }
    
    # ========== Contract Management ==========
    
    def get_contracts(
        self,
        session_id: Optional[str] = None,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None
    ) -> List[Contract]:
        """Get contracts with optional filtering."""
        return self.contracts.get_contracts(
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent
        )
    
    def get_conversation(self, session_id: str) -> List[Contract]:
        """Get all contracts for a session, ordered by time."""
        return self.contracts.get_conversation(session_id)
    
    # ========== Compression ==========
    
    async def compress_session(
        self,
        session_id: str,
        intent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compress a session's conversation to MemAgent.
        
        Args:
            session_id: Session to compress
            intent: Optional session intent
        
        Returns:
            Compression result or None if failed
        """
        logger.info(f"Compressing session: {session_id}")
        
        # Get all contracts for session
        contracts = self.get_conversation(session_id)
        
        if not contracts:
            logger.warning(f"No contracts found for session {session_id}")
            return None
        
        # Convert to dicts
        contract_dicts = [c.model_dump() for c in contracts]
        
        # Compress via MemAgent
        result = await self.integrations.compress_session(
            session_id,
            contract_dicts,
            intent
        )
        
        if result:
            logger.info(f"Session {session_id} compressed successfully")
        else:
            logger.error(f"Failed to compress session {session_id}")
        
        return result
    
    # ========== Health & Status ==========
    
    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        # Check integrations
        integration_health = await self.integrations.check_integrations()
        
        # Count agents by status
        agents_by_status = {}
        for agent in self._agents.values():
            status = agent.metadata.status
            agents_by_status[status] = agents_by_status.get(status, 0) + 1
        
        # Contract stats
        contract_stats = self.contracts.get_stats()
        
        return {
            "orchestrator": "healthy",
            "agents": {
                "total": len(self._agents),
                "by_status": agents_by_status,
                "registered": [
                    {
                        "agent_id": a.metadata.agent_id,
                        "name": a.metadata.name,
                        "status": a.metadata.status,
                        "capabilities": [c.name for c in a.metadata.capabilities],
                        "tasks_completed": a.metadata.tasks_completed,
                        "tasks_failed": a.metadata.tasks_failed
                    }
                    for a in self._agents.values()
                ]
            },
            "contracts": contract_stats,
            "integrations": integration_health
        }
