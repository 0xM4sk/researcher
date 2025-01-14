from redis.asyncio import Redis
from typing import Dict, Any, Callable
import asyncio
import json
import uuid
from datetime import datetime
from models import TaskStatus

class MessageQueue:
    """Handles async message queuing and processing using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        
    async def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return await self.redis.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            return False

    async def enqueue_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Enqueue a new task."""
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.redis.lpush("task_queue", json.dumps(task_data))
        await self.redis.hset(
            f"task:{task_id}",
            mapping={
                "status": TaskStatus.PENDING.value,
                "data": json.dumps(task_data)
            }
        )
        return task_id

    async def process_queue(self, handlers: Dict[str, Callable]):
        """Process tasks from the queue."""
        while True:
            try:
                # Use blpop with timeout
                result = await self.redis.blpop(["task_queue"], timeout=1)
                if not result:
                    await asyncio.sleep(0.1)
                    continue
                
                _, task_json = result
                task = json.loads(task_json)
                task_id = task["task_id"]
                handler = handlers.get(task["task_type"])
                
                if not handler:
                    continue
                
                # Update task status
                await self.redis.hset(
                    f"task:{task_id}",
                    "status",
                    TaskStatus.IN_PROGRESS.value
                )
                
                try:
                    result = await handler(task["payload"])
                    await self.redis.hset(
                        f"task:{task_id}",
                        mapping={
                            "status": TaskStatus.COMPLETED.value,
                            "result": json.dumps(result),
                            "completed_at": datetime.utcnow().isoformat()
                        }
                    )
                except Exception as e:
                    await self.redis.hset(
                        f"task:{task_id}",
                        mapping={
                            "status": TaskStatus.FAILED.value,
                            "error": str(e),
                            "failed_at": datetime.utcnow().isoformat()
                        }
                    )
                    
            except Exception as e:
                print(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a task."""
        task_data = await self.redis.hgetall(f"task:{task_id}")
        if not task_data:
            return None
        return task_data

    async def cleanup(self):
        """Cleanup Redis connections."""
        await self.redis.close()