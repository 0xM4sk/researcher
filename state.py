from redis.asyncio import Redis
from config import settings
import json
from typing import Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskState:
    """Represents the state of a research task."""
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    data: Dict[str, Any]
    error: str | None = None

class StateManager:
    """Manages application state using Redis."""
    def __init__(self):
        self.redis = Redis.from_url(settings.queue.REDIS_URL, decode_responses=True)
        
    async def set_state(self, task_id: str, state: TaskState) -> None:
        """Store task state in Redis."""
        state_dict = {
            "task_id": task_id,
            "status": state.status.value,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "data": state.data,
            "error": state.error
        }
        await self.redis.set(f"task:{task_id}", json.dumps(state_dict))
        
    async def get_state(self, task_id: str) -> TaskState | None:
        """Retrieve task state from Redis."""
        state_data = await self.redis.get(f"task:{task_id}")
        if not state_data:
            return None
            
        state_dict = json.loads(state_data)
        return TaskState(
            task_id=state_dict["task_id"],
            status=TaskStatus(state_dict["status"]),
            created_at=datetime.fromisoformat(state_dict["created_at"]),
            updated_at=datetime.fromisoformat(state_dict["updated_at"]),
            data=state_dict["data"],
            error=state_dict["error"]
        )

    async def cleanup(self):
        """Cleanup Redis connections."""
        await self.redis.close()
