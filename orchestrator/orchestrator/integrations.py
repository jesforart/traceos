"""
Integration clients for MemAgent and Trace.

MemAgent: Compress conversation history to memory blocks
Trace: Log contracts for provenance tracking
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MemAgentClient:
    """
    Client for MemAgent compression API.
    
    Compresses agent conversation history into memory blocks.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize MemAgent client.

        Args:
            base_url: MemAgent base URL (default: http://localhost:8799)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 30.0
        logger.info(f"MemAgentClient initialized: {self.base_url}")

    async def compress_conversation(
        self,
        session_id: str,
        contracts: List[Dict[str, Any]],
        intent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compress conversation to memory block.

        Simple approach: Just send session_id to MemAgent and let it
        fetch its own data. This avoids JSON serialization issues.

        Args:
            session_id: Session identifier
            contracts: List of contracts (not used - kept for API compatibility)
            intent: Optional session intent

        Returns:
            Compression result or None if failed
        """
        try:
            # Simple payload - just session_id and intent
            # Let MemAgent fetch its own memory block data
            payload = {
                "intent": intent or "Multi-agent task execution"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/session/{session_id}/compress",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Compressed conversation for session {session_id}")
                    return result
                else:
                    logger.warning(f"Compression failed: {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"MemAgent timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Failed to compress conversation: {e}")
            return None
    
    def _format_conversation(self, contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format contracts as conversation for MemAgent.
        
        Converts contracts to messages:
        - REQUEST -> User message
        - RESPONSE -> Assistant message
        """
        messages = []
        
        for contract in contracts:
            if contract["contract_type"] == "REQUEST":
                # User request
                capability = contract.get("capability", "unknown")
                payload = contract.get("payload", {})
                
                messages.append({
                    "role": "user",
                    "content": f"[{contract['from_agent']} -> {contract['to_agent']}] {capability}",
                    "timestamp": contract.get("created_at"),
                    "metadata": {
                        "contract_id": contract["contract_id"],
                        "capability": capability,
                        "payload": payload
                    }
                })
            
            elif contract["contract_type"] == "RESPONSE":
                # Agent response
                result = contract.get("result", {})
                error = contract.get("error")
                
                content = f"[{contract['from_agent']} -> {contract['to_agent']}] "
                if error:
                    content += f"Error: {error}"
                else:
                    content += f"Success: {result}"
                
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "timestamp": contract.get("created_at"),
                    "metadata": {
                        "contract_id": contract["contract_id"],
                        "result": result,
                        "error": error
                    }
                })
        
        return messages
    
    async def check_health(self) -> bool:
        """Check if MemAgent is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/v1/health")
                return response.status_code == 200
        except Exception:
            return False


class TraceClient:
    """
    Client for Trace HTTP Wrapper API.
    
    Logs contracts to Trace for provenance tracking.
    """
    
    def __init__(self, base_url: str = "http://localhost:8787"):
        """
        Initialize Trace client.
        
        Args:
            base_url: Trace HTTP Wrapper base URL (default: http://localhost:8787)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 30.0
        logger.info(f"TraceClient initialized: {self.base_url}")
    
    async def log_contract(
        self,
        session_id: str,
        contract: Dict[str, Any]
    ) -> bool:
        """
        Log a contract to Trace as an event.
        
        Args:
            session_id: Session identifier
            contract: Contract to log
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format contract as Trace event
            event_type = f"contract.{contract['contract_type'].lower()}"
            
            payload = {
                "event_type": event_type,
                "data": {
                    "contract_id": contract["contract_id"],
                    "from_agent": contract["from_agent"],
                    "to_agent": contract["to_agent"],
                    "capability": contract.get("capability"),
                    "payload": contract.get("payload"),
                    "status": contract.get("status"),
                    "result": contract.get("result"),
                    "error": contract.get("error")
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/sessions/{session_id}/events",
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Logged contract {contract['contract_id']} to Trace")
                    return True
                else:
                    logger.warning(f"Failed to log contract: {response.status_code}")
                    return False
        
        except httpx.TimeoutException:
            logger.error(f"Trace timeout after {self.timeout}s")
            return False
        except Exception as e:
            logger.error(f"Failed to log contract: {e}")
            return False
    
    async def get_contracts(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all contracts for a session from Trace.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of contract events
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/sessions/{session_id}/events"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    # Filter contract events
                    contract_events = [
                        e for e in events
                        if e.get("event_type", "").startswith("contract.")
                    ]
                    
                    logger.info(f"Retrieved {len(contract_events)} contracts from Trace")
                    return contract_events
                else:
                    logger.warning(f"Failed to get contracts: {response.status_code}")
                    return []
        
        except httpx.TimeoutException:
            logger.error(f"Trace timeout after {self.timeout}s")
            return []
        except Exception as e:
            logger.error(f"Failed to get contracts: {e}")
            return []
    
    async def check_health(self) -> bool:
        """Check if Trace is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/v1/health")
                return response.status_code == 200
        except Exception:
            return False


class IntegrationManager:
    """
    Manages integrations with MemAgent and Trace.
    
    Provides unified interface for:
    - Logging contracts to Trace
    - Compressing conversations to MemAgent
    - Health checking both services
    """
    
    def __init__(
        self,
        memagent_url: str = "http://localhost:8000",
        trace_url: str = "http://localhost:8787"
    ):
        """
        Initialize integration manager.
        
        Args:
            memagent_url: MemAgent base URL
            trace_url: Trace HTTP Wrapper base URL
        """
        self.memagent = MemAgentClient(memagent_url)
        self.trace = TraceClient(trace_url)
    
    async def log_contract(self, session_id: str, contract: Dict[str, Any]) -> bool:
        """Log contract to Trace."""
        return await self.trace.log_contract(session_id, contract)
    
    async def compress_session(
        self,
        session_id: str,
        contracts: List[Dict[str, Any]],
        intent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Compress session to MemAgent."""
        return await self.memagent.compress_conversation(session_id, contracts, intent)
    
    async def check_integrations(self) -> Dict[str, bool]:
        """Check health of all integrations."""
        memagent_ok = await self.memagent.check_health()
        trace_ok = await self.trace.check_health()
        
        return {
            "memagent": memagent_ok,
            "trace": trace_ok,
            "all_healthy": memagent_ok and trace_ok
        }
