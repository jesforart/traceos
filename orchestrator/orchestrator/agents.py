"""
Agent base class and capabilities for multi-agent orchestration.

Defines:
- AgentCapabilities: What an agent can do
- AgentStatus: Current state of an agent
- Agent: Base class for all agents
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod


class AgentStatus(str, Enum):
    """Agent status enum."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AgentCapability(BaseModel):
    """
    Capability definition for an agent.
    
    Example capabilities:
    - text_generation
    - image_generation
    - code_analysis
    - data_processing
    """
    name: str = Field(..., description="Capability name (e.g., 'image_generation')")
    description: str = Field(..., description="Human-readable description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Required parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "image_generation",
                "description": "Generate images from text prompts",
                "parameters": {
                    "max_resolution": "1024x1024",
                    "formats": ["png", "jpg"]
                }
            }
        }


class AgentMetadata(BaseModel):
    """Metadata about an agent."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="What this agent does")
    capabilities: List[AgentCapability] = Field(default_factory=list)
    status: AgentStatus = Field(default=AgentStatus.AVAILABLE)
    version: str = Field(default="1.0.0")
    endpoint: Optional[str] = Field(None, description="Agent API endpoint if external")
    
    # Tracking
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    tasks_completed: int = Field(default=0)
    tasks_failed: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_image_gen_001",
                "name": "ImageGen Agent",
                "description": "Generates images from text descriptions",
                "capabilities": [
                    {
                        "name": "text_to_image",
                        "description": "Convert text to image",
                        "parameters": {"style": ["realistic", "artistic"]}
                    }
                ],
                "status": "available",
                "endpoint": "http://localhost:9000"
            }
        }


class Agent(ABC):
    """
    Base class for all agents in the orchestrator.
    
    Agents must implement:
    - execute(): Process a task
    - get_capabilities(): Report what they can do
    
    Usage:
        class MyAgent(Agent):
            def __init__(self):
                super().__init__(
                    agent_id="my_agent_001",
                    name="My Agent",
                    description="Does something useful"
                )
            
            async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
                # Process task
                return {"result": "success"}
            
            def get_capabilities(self) -> List[AgentCapability]:
                return [
                    AgentCapability(
                        name="my_capability",
                        description="My capability description",
                        parameters={}
                    )
                ]
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        endpoint: Optional[str] = None
    ):
        """
        Initialize agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Display name
            description: What this agent does
            version: Agent version
            endpoint: External API endpoint (optional)
        """
        self.metadata = AgentMetadata(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            endpoint=endpoint,
            capabilities=self.get_capabilities(),
            status=AgentStatus.AVAILABLE
        )
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: Task dictionary with:
                - task_id: Unique task identifier
                - capability: Required capability name
                - parameters: Task parameters
                - context: Optional context from previous tasks
        
        Returns:
            Result dictionary with:
                - success: bool
                - data: Result data
                - error: Optional error message
        
        Raises:
            Exception: If task execution fails
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Return list of capabilities this agent provides.
        
        Returns:
            List of AgentCapability objects
        """
        pass
    
    def update_status(self, status: AgentStatus):
        """Update agent status."""
        self.metadata.status = status
        self.metadata.last_heartbeat = datetime.utcnow()
    
    def increment_task_count(self, success: bool):
        """Increment task counter."""
        if success:
            self.metadata.tasks_completed += 1
        else:
            self.metadata.tasks_failed += 1
    
    def can_handle(self, capability_name: str) -> bool:
        """Check if agent can handle a capability."""
        return any(cap.name == capability_name for cap in self.metadata.capabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent metadata to dictionary."""
        return self.metadata.model_dump()


class ExampleAgent(Agent):
    """
    Example agent implementation for testing.
    
    Provides basic text processing capabilities.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="agent_example_001",
            name="Example Agent",
            description="Example agent for testing orchestration"
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a simple echo task."""
        capability = task.get("capability")
        parameters = task.get("parameters", {})
        
        if capability == "echo":
            return {
                "success": True,
                "data": {
                    "message": f"Echo: {parameters.get('text', 'No text provided')}"
                }
            }
        elif capability == "uppercase":
            text = parameters.get("text", "")
            return {
                "success": True,
                "data": {
                    "result": text.upper()
                }
            }
        else:
            return {
                "success": False,
                "error": f"Unknown capability: {capability}"
            }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return example capabilities."""
        return [
            AgentCapability(
                name="echo",
                description="Echo back the input text",
                parameters={"text": "string"}
            ),
            AgentCapability(
                name="uppercase",
                description="Convert text to uppercase",
                parameters={"text": "string"}
            )
        ]
