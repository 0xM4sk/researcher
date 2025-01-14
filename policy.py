from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Action:
    """Represents an action that can be taken by the agent."""
    name: str
    priority: int
    params: Dict[str, Any] = None

class ResearchPolicy:
    """Policy for determining the next action in the research process."""
    
    def select_action(self, state: Dict[str, Any]) -> Optional[Action]:
        """Select the next action based on the current state."""
        if not state.get("searched"):
            return Action("search", priority=1)
        if not state.get("analyzed"):
            return Action("analyze", priority=2)
        return Action("summarize", priority=3)