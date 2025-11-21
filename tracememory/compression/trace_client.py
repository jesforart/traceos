"""
Trace Client - Fetches events from Trace MCP.

Connects to real Trace service with graceful fallback to mock mode.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx

from config import settings

logger = logging.getLogger(__name__)


class TraceClient:
    """
    Client for fetching events from Trace MCP.

    Connects to real Trace API at http://localhost:8787
    Falls back to mock mode if Trace is unavailable.
    """

    def __init__(self, trace_url: Optional[str] = None, use_mock: bool = False):
        """
        Initialize Trace client.

        Args:
            trace_url: Base URL for Trace MCP service (default: from settings)
            use_mock: Force mock mode for testing (default: False)
        """
        self.trace_url = trace_url or settings.TRACE_URL
        self.timeout = settings.TRACE_TIMEOUT
        self.use_mock = use_mock
        self._trace_available = None  # Lazy check on first call

        mode = "mock mode" if use_mock else "real API mode"
        logger.info(f"TraceClient initialized ({mode}) - {self.trace_url}")

    async def _check_trace_available(self) -> bool:
        """Check if Trace service is available."""
        if self._trace_available is not None:
            return self._trace_available

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.trace_url}/v1/health")
                self._trace_available = response.status_code == 200
                logger.info(f"Trace service available: {self._trace_available}")
                return self._trace_available
        except Exception as e:
            logger.warning(f"Trace service unavailable: {e}")
            self._trace_available = False
            return False

    def fetch_events(self, session_id: str) -> List[Dict]:
        """
        Fetch events for a session from Trace.

        Args:
            session_id: Session identifier

        Returns:
            List of event dictionaries with priority scoring

        Note: Falls back to mock mode if Trace is unavailable.
        """
        if self.use_mock:
            logger.info(f"Fetching events for session: {session_id} (forced mock mode)")
            return self._generate_mock_events(session_id)

        try:
            # Synchronous wrapper for async call
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.fetch_events_async(session_id))

        except Exception as e:
            logger.warning(f"Failed to fetch events from Trace, using mock data: {e}")
            return self._generate_mock_events(session_id)

    def _generate_mock_events(self, session_id: str) -> List[Dict]:
        """
        Generate realistic mock events for testing.

        These simulate a typical design session with:
        - Session creation
        - User notes
        - Variation applications
        - Asset creation
        - Decision points
        """
        base_time = datetime.utcnow() - timedelta(minutes=30)

        events = [
            {
                "event_id": "evt_001",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=0)).isoformat(),
                "event_type": "session.created",
                "actor": "user",
                "data": {
                    "intent": "Create organic hero section with modern aesthetic",
                    "created_by": "designer_01"
                }
            },
            {
                "event_id": "evt_002",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=10)).isoformat(),
                "event_type": "user_note.added",
                "actor": "user",
                "data": {
                    "text": "Prefer muted color palette with high contrast"
                }
            },
            {
                "event_id": "evt_003",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=30)).isoformat(),
                "event_type": "asset.created",
                "actor": "system",
                "data": {
                    "asset_type": "svg",
                    "asset_id": "asset_hero_001"
                }
            },
            {
                "event_id": "evt_004",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
                "event_type": "variation.applied",
                "actor": "user",
                "data": {
                    "modifier": "stroke_weight",
                    "value": 0.3
                }
            },
            {
                "event_id": "evt_005",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "event_type": "variation.applied",
                "actor": "user",
                "data": {
                    "modifier": "hue_shift",
                    "value": 0.15
                }
            },
            {
                "event_id": "evt_006",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "event_type": "variation.rejected",
                "actor": "user",
                "data": {
                    "reason": "Too bold, not aligned with muted palette goal"
                }
            },
            {
                "event_id": "evt_007",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=4)).isoformat(),
                "event_type": "variation.applied",
                "actor": "user",
                "data": {
                    "modifier": "stroke_weight",
                    "value": 0.5
                }
            },
            {
                "event_id": "evt_008",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                "event_type": "variation.applied",
                "actor": "user",
                "data": {
                    "modifier": "fill_opacity",
                    "value": 0.85
                }
            },
            {
                "event_id": "evt_009",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=6)).isoformat(),
                "event_type": "user_note.added",
                "actor": "user",
                "data": {
                    "text": "WCAG AA contrast required for accessibility"
                }
            },
            {
                "event_id": "evt_010",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=7)).isoformat(),
                "event_type": "variation.accepted",
                "actor": "user",
                "data": {
                    "variant_id": "var_final_001",
                    "note": "Balanced composition with good contrast"
                }
            },
            {
                "event_id": "evt_011",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=8)).isoformat(),
                "event_type": "provenance.stored",
                "actor": "system",
                "data": {
                    "node_id": "node_hero_v3",
                    "parent_node": "node_hero_v2"
                }
            },
        ]

        return events

    async def fetch_events_async(self, session_id: str) -> List[Dict]:
        """
        Async version of fetch_events - calls real Trace API.

        Args:
            session_id: Session identifier

        Returns:
            List of event dictionaries with priority scoring
        """
        if self.use_mock:
            return self._generate_mock_events(session_id)

        # Check if Trace is available
        if not await self._check_trace_available():
            logger.warning("Trace unavailable, using mock data")
            return self._generate_mock_events(session_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call Trace HTTP Wrapper to get events
                response = await client.get(
                    f"{self.trace_url}/v1/sessions/{session_id}/events"
                )

                if response.status_code == 200:
                    events = response.json().get("events", [])
                    logger.info(f"Fetched {len(events)} events from Trace for session {session_id}")

                    # Map Trace events to MemAgent format with priority
                    mapped_events = [self._map_trace_event(event) for event in events]
                    return mapped_events

                elif response.status_code == 404:
                    logger.info(f"No events found in Trace for session {session_id}")
                    return []

                else:
                    logger.warning(f"Trace API error {response.status_code}, using mock data")
                    return self._generate_mock_events(session_id)

        except httpx.TimeoutException:
            logger.warning(f"Trace API timeout after {self.timeout}s, using mock data")
            return self._generate_mock_events(session_id)

        except Exception as e:
            logger.warning(f"Failed to fetch from Trace: {e}, using mock data")
            return self._generate_mock_events(session_id)

    def fetch_provenance_nodes(self, session_id: str) -> List[Dict]:
        """
        Fetch design provenance chain from Trace.

        Args:
            session_id: Session identifier

        Returns:
            List of provenance node dictionaries
        """
        if self.use_mock:
            logger.info(f"Fetching provenance for session: {session_id} (mock mode)")
            return self._generate_mock_provenance(session_id)

        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.fetch_provenance_nodes_async(session_id))

        except Exception as e:
            logger.warning(f"Failed to fetch provenance from Trace: {e}")
            return []

    async def fetch_provenance_nodes_async(self, session_id: str) -> List[Dict]:
        """
        Async version - fetch design provenance chain from Trace.

        Args:
            session_id: Session identifier

        Returns:
            List of provenance nodes with parent relationships and modifiers
        """
        if self.use_mock:
            return self._generate_mock_provenance(session_id)

        if not await self._check_trace_available():
            logger.warning("Trace unavailable, cannot fetch provenance")
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.trace_url}/v1/sessions/{session_id}/provenance"
                )

                if response.status_code == 200:
                    nodes = response.json().get("nodes", [])
                    logger.info(f"Fetched {len(nodes)} provenance nodes from Trace")

                    # Parse and map provenance data
                    mapped_nodes = [self._map_provenance_node(node) for node in nodes]
                    return mapped_nodes

                elif response.status_code == 404:
                    logger.info(f"No provenance found for session {session_id}")
                    return []

                else:
                    logger.warning(f"Trace API error {response.status_code} for provenance")
                    return []

        except httpx.TimeoutException:
            logger.warning(f"Trace API timeout fetching provenance")
            return []

        except Exception as e:
            logger.warning(f"Failed to fetch provenance: {e}")
            return []

    def fetch_agent_contracts(self, session_id: str) -> List[Dict]:
        """
        Fetch agent-to-agent communication contracts from Trace.

        Args:
            session_id: Session identifier

        Returns:
            List of agent contract dictionaries (REQUEST/RESPONSE pairs)
        """
        if self.use_mock:
            logger.info(f"Fetching agent contracts for session: {session_id} (mock mode)")
            return self._generate_mock_contracts(session_id)

        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.fetch_agent_contracts_async(session_id))

        except Exception as e:
            logger.warning(f"Failed to fetch agent contracts from Trace: {e}")
            return []

    async def fetch_agent_contracts_async(self, session_id: str) -> List[Dict]:
        """
        Async version - fetch agent-to-agent contracts from Trace.

        Args:
            session_id: Session identifier

        Returns:
            List of agent contracts with REQUEST/RESPONSE patterns
        """
        if self.use_mock:
            return self._generate_mock_contracts(session_id)

        if not await self._check_trace_available():
            logger.warning("Trace unavailable, cannot fetch agent contracts")
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.trace_url}/v1/trace/contracts/{session_id}"
                )

                if response.status_code == 200:
                    contracts = response.json().get("contracts", [])
                    logger.info(f"Fetched {len(contracts)} agent contracts from Trace")

                    # Parse and map contract data
                    mapped_contracts = [self._map_agent_contract(contract) for contract in contracts]
                    return mapped_contracts

                elif response.status_code == 404:
                    logger.info(f"No agent contracts found for session {session_id}")
                    return []

                else:
                    logger.warning(f"Trace API error {response.status_code} for contracts")
                    return []

        except httpx.TimeoutException:
            logger.warning(f"Trace API timeout fetching agent contracts")
            return []

        except Exception as e:
            logger.warning(f"Failed to fetch agent contracts: {e}")
            return []

    def _map_trace_event(self, trace_event: Dict) -> Dict:
        """
        Map Trace event format to MemAgent format with priority scoring.

        Args:
            trace_event: Raw event from Trace API

        Returns:
            Mapped event with priority field
        """
        event_type = trace_event.get("event_type", "unknown")

        # Assign priority based on event type importance
        priority = "LOW"
        if event_type in ["session.created", "user_note.added", "variation.accepted", "variation.rejected"]:
            priority = "HIGH"
        elif event_type in ["variation.applied", "asset.created", "decision.made"]:
            priority = "MEDIUM"

        return {
            "event_id": trace_event.get("event_id", "unknown"),
            "session_id": trace_event.get("session_id"),
            "timestamp": trace_event.get("timestamp"),
            "event_type": event_type,
            "actor": trace_event.get("actor", "system"),
            "data": trace_event.get("data", {}),
            "priority": priority
        }

    def _map_provenance_node(self, node: Dict) -> Dict:
        """
        Map Trace provenance node to MemAgent format.

        Args:
            node: Raw provenance node from Trace API

        Returns:
            Mapped provenance node with parent relationships
        """
        return {
            "node_id": node.get("node_id"),
            "parent_id": node.get("parent_node_id"),
            "session_id": node.get("session_id"),
            "timestamp": node.get("timestamp"),
            "modifiers": node.get("modifiers", {}),
            "distances": node.get("distances", {}),
            "metadata": node.get("metadata", {})
        }

    def _map_agent_contract(self, contract: Dict) -> Dict:
        """
        Map Trace agent contract to MemAgent format.

        Args:
            contract: Raw contract from Trace API

        Returns:
            Mapped agent contract with REQUEST/RESPONSE structure
        """
        return {
            "contract_id": contract.get("contract_id"),
            "session_id": contract.get("session_id"),
            "timestamp": contract.get("timestamp"),
            "from_agent": contract.get("from_agent"),
            "to_agent": contract.get("to_agent"),
            "contract_type": contract.get("type", "REQUEST"),  # REQUEST or RESPONSE
            "payload": contract.get("payload", {}),
            "status": contract.get("status", "pending")
        }

    def _generate_mock_provenance(self, session_id: str) -> List[Dict]:
        """Generate mock provenance chain for testing."""
        base_time = datetime.utcnow() - timedelta(minutes=30)

        return [
            {
                "node_id": "node_hero_v1",
                "parent_id": None,
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=30)).isoformat(),
                "modifiers": {},
                "distances": {},
                "metadata": {"initial": True}
            },
            {
                "node_id": "node_hero_v2",
                "parent_id": "node_hero_v1",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
                "modifiers": {"stroke_weight": 0.3, "hue_shift": 0.15},
                "distances": {"perceptual": 0.25, "semantic": 0.15},
                "metadata": {"variation_applied": True}
            },
            {
                "node_id": "node_hero_v3",
                "parent_id": "node_hero_v2",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                "modifiers": {"stroke_weight": 0.5, "fill_opacity": 0.85},
                "distances": {"perceptual": 0.35, "semantic": 0.20},
                "metadata": {"accepted": True}
            }
        ]

    def _generate_mock_contracts(self, session_id: str) -> List[Dict]:
        """Generate mock agent contracts for testing."""
        base_time = datetime.utcnow() - timedelta(minutes=30)

        return [
            {
                "contract_id": "contract_001",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=5)).isoformat(),
                "from_agent": "memagent",
                "to_agent": "modifier_engine",
                "contract_type": "REQUEST",
                "payload": {"action": "apply_variation", "modifiers": {"stroke_weight": 0.3}},
                "status": "completed"
            },
            {
                "contract_id": "contract_002",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(seconds=7)).isoformat(),
                "from_agent": "modifier_engine",
                "to_agent": "memagent",
                "contract_type": "RESPONSE",
                "payload": {"success": True, "variant_id": "var_001"},
                "status": "delivered"
            },
            {
                "contract_id": "contract_003",
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
                "from_agent": "memagent",
                "to_agent": "trace",
                "contract_type": "REQUEST",
                "payload": {"action": "store_provenance", "node_id": "node_hero_v2"},
                "status": "completed"
            }
        ]
