"""
MCP Client - Communicates with Trace MCP server via stdin/stdout.

The Trace MCP server uses JSON-RPC protocol over stdio.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for communicating with Trace MCP server.

    Uses subprocess to start Trace MCP and communicates via stdin/stdout
    using JSON-RPC protocol.
    """

    def __init__(self, trace_command: str = "/home/jesmosis/trace-server/venv/bin/python -m trace_sde.server"):
        """
        Initialize MCP client.

        Args:
            trace_command: Command to start Trace MCP server
                          Default uses the Python-based trace_sde server
        """
        self.trace_command = trace_command
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self._initialized = False
        logger.info(f"MCPClient initialized with command: {trace_command}")

    async def start(self):
        """Start the Trace MCP server subprocess."""
        if self.process is not None:
            logger.warning("Trace MCP process already running")
            return

        logger.info("Starting Trace MCP server...")
        try:
            self.process = await asyncio.create_subprocess_shell(
                self.trace_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Trace MCP server started (PID: {self.process.pid})")

            # Initialize MCP connection
            await self._initialize()

        except Exception as e:
            logger.error(f"Failed to start Trace MCP server: {e}")
            raise

    async def stop(self):
        """Stop the Trace MCP server subprocess."""
        if self.process is None:
            return

        logger.info("Stopping Trace MCP server...")
        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
            logger.info("Trace MCP server stopped")
        except asyncio.TimeoutError:
            logger.warning("Trace MCP server did not stop gracefully, killing...")
            self.process.kill()
            await self.process.wait()
        finally:
            self.process = None
            self._initialized = False

    async def _initialize(self):
        """Initialize MCP connection with server."""
        logger.info("Initializing MCP connection...")

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "trace-http-wrapper",
                    "version": "1.0.0"
                }
            }
        }

        response = await self._send_request(init_request)

        if response and response.get("result"):
            logger.info("MCP connection initialized successfully")
            self._initialized = True
        else:
            logger.error(f"MCP initialization failed: {response}")
            raise RuntimeError("Failed to initialize MCP connection")

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self.request_id += 1
        return self.request_id

    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send JSON-RPC request to Trace MCP server.

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response or None if error
        """
        if self.process is None or self.process.stdin is None:
            logger.error("Trace MCP process not running")
            return None

        try:
            # Serialize request
            request_json = json.dumps(request) + "\n"
            logger.debug(f"Sending MCP request: {request_json.strip()}")

            # Write to stdin
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # Read response from stdout
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )

            if not response_line:
                logger.error("Empty response from Trace MCP")
                return None

            response = json.loads(response_line.decode())
            logger.debug(f"Received MCP response: {response}")

            return response

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for Trace MCP response")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending MCP request: {e}")
            return None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call a tool on the Trace MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result or None if error
        """
        if not self._initialized:
            logger.error("MCP client not initialized")
            return None

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self._send_request(request)

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            logger.error(f"Tool call error: {response['error']}")
            return None
        else:
            return None

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions in Trace.

        Returns:
            List of session objects
        """
        logger.info("Listing sessions...")

        result = await self.call_tool("list_sessions", {})

        if result and "content" in result:
            # Parse content from MCP response
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        sessions = json.loads(item["text"])
                        return sessions if isinstance(sessions, list) else []
                    except json.JSONDecodeError:
                        pass

        return []

    async def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get events for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of event objects
        """
        logger.info(f"Getting events for session: {session_id}")

        result = await self.call_tool("get_events", {"session_id": session_id})

        if result and "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        events = json.loads(item["text"])
                        return events if isinstance(events, list) else []
                    except json.JSONDecodeError:
                        pass

        return []

    async def get_provenance(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get provenance chain for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of provenance nodes
        """
        logger.info(f"Getting provenance for session: {session_id}")

        result = await self.call_tool("get_provenance", {"session_id": session_id})

        if result and "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        provenance = json.loads(item["text"])
                        return provenance if isinstance(provenance, list) else []
                    except json.JSONDecodeError:
                        pass

        return []

    async def add_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Add event to a session.

        Args:
            session_id: Session identifier
            event_type: Type of event
            data: Event data

        Returns:
            True if successful
        """
        logger.info(f"Adding event to session {session_id}: {event_type}")

        result = await self.call_tool("add_event", {
            "session_id": session_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        return result is not None

    async def add_provenance_node(
        self,
        session_id: str,
        node_id: str,
        parent_id: Optional[str] = None,
        modifiers: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add provenance node to a session.

        Args:
            session_id: Session identifier
            node_id: Node identifier
            parent_id: Parent node ID (optional)
            modifiers: Applied modifiers (optional)
            metadata: Additional metadata (optional)

        Returns:
            True if successful
        """
        logger.info(f"Adding provenance node to session {session_id}: {node_id}")

        result = await self.call_tool("add_provenance_node", {
            "session_id": session_id,
            "node_id": node_id,
            "parent_id": parent_id,
            "modifiers": modifiers or {},
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })

        return result is not None
