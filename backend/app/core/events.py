import asyncio
import json
from typing import AsyncGenerator, Dict, Set
from pydantic import BaseModel

class ReviewEvent(BaseModel):
    review_id: str
    event_type: str  # "task_started", "task_progress", "task_completed", "finding_added", "review_completed", "error"
    agent_id: str
    timestamp: str
    message: str
    data: dict = {}

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def subscribe(self, review_id: str) -> asyncio.Queue:
        if review_id not in self._subscribers:
            self._subscribers[review_id] = set()
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[review_id].add(queue)
        return queue

    def unsubscribe(self, review_id: str, queue: asyncio.Queue):
        if review_id in self._subscribers:
            self._subscribers[review_id].discard(queue)
            if not self._subscribers[review_id]:
                del self._subscribers[review_id]

    async def publish(self, event: ReviewEvent):
        if event.review_id in self._subscribers:
            for queue in list(self._subscribers[event.review_id]):
                await queue.put(event)

    async def sse_generator(self, review_id: str) -> AsyncGenerator[str, None]:
        queue = self.subscribe(review_id)
        try:
            # Send initial connection ping
            yield f"event: ping\ndata: {json.dumps({'status': 'connected'})}\n\n"
            while True:
                try:
                    event: ReviewEvent = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"
                    if event.event_type in ("review_completed", "review_failed"):
                        break
                except asyncio.TimeoutError:
                    yield f"event: ping\ndata: {json.dumps({'status': 'keep-alive'})}\n\n"
        finally:
            self.unsubscribe(review_id, queue)

event_bus = EventBus()
