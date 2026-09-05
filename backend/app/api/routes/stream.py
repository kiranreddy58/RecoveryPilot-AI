"""
Server-Sent Events (SSE) Streaming Route

Streams real-time recovery case updates, step transitions, and metric changes to the frontend UI.
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/events")
async def sse_events_stream(request: Request):
    """
    Server-Sent Events (SSE) endpoint.
    Streams live telemetry to frontend clients:
    - CASE_TRANSITION (DETECTED -> DIAGNOSED -> EXECUTING -> RECOVERED)
    - GUARDIAN_DECISION
    - WEBHOOK_RECONCILED
    - BATCH_COMPLETED
    """
    queue = event_bus.subscribe()

    async def event_generator():
        try:
            # Send initial keepalive & welcome
            welcome_msg = json.dumps({"event": "CONNECTED", "message": "RecoveryPilot Control Tower Stream Connected"})
            yield f"data: {welcome_msg}\n\n"

            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event from bus with timeout for periodic heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep connection alive through proxies
                    yield ": heartbeat\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
