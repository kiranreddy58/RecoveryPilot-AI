"""
In-Memory Event Bus for Real-Time Server-Sent Events (SSE) Streaming

Broadcasts case state changes, recovery verification events, and metric updates
to all connected browser clients with zero external dependencies.
"""
import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe a new client SSE connection."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        logger.debug(f"SSE client subscribed. Total active listeners: {len(self._subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Remove a disconnected client."""
        self._subscribers.discard(queue)
        logger.debug(f"SSE client disconnected. Remaining listeners: {len(self._subscribers)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Asynchronously send an event to all active subscriber queues."""
        if not self._subscribers:
            return

        message = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        dead_queues = set()
        for q in self._subscribers:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(q)
            except Exception as e:
                logger.debug(f"Error publishing to subscriber: {e}")
                dead_queues.add(q)

        for q in dead_queues:
            self._subscribers.discard(q)

    def publish_sync(self, event_type: str, data: Dict[str, Any]):
        """Synchronous wrapper for broadcasting from synchronous FastAPI endpoints/services."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(event_type, data))
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except Exception:
            # If no running loop, create a task in the background loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast(event_type, data))
            except Exception as e:
                logger.debug(f"Event bus publish error: {e}")


# Singleton instance
event_bus = EventBus()
