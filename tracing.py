from contextlib import asynccontextmanager
import structlog
from opentelemetry import trace
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from models import TaskStatus, ResearchQuery, ResearchResult

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

@asynccontextmanager
async def telemetry_context():
    """Context manager for telemetry setup and cleanup."""
    try:
        yield logger
    finally:
        # Cleanup telemetry resources if needed
        pass

class TaskState(BaseModel):
    """Task state tracking model."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

class StateManager:
    """Manages task state persistence."""
    def __init__(self):
        self.states: Dict[str, TaskState] = {}

    async def get_state(self, task_id: str) -> Optional[TaskState]:
        """Get task state by ID."""
        return self.states.get(task_id)

    async def set_state(self, task_id: str, state: TaskState):
        """Set task state."""
        self.states[task_id] = state

    async def delete_state(self, task_id: str):
        """Delete task state."""
        if task_id in self.states:
            del self.states[task_id]
