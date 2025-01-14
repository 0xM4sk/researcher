from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Agent(ABC):
    """Base Agent class that defines the interface for all agents."""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the agent's main task."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup agent resources."""
        pass