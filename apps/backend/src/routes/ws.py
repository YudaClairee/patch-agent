import asyncio
import json
import logging
import uuid
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.config import settings
from src.core.auth import current_user_ws
from src.core.database import Session, engine
from src.models.enums import RunStatus
from src.repositories.agent_runs import (
    get_agent_run_for_user,
    get_pull_request_for_run_for_user,
    list_events_for_user,
)

logger = logging.getLogger(__name__)

ws_router = APIRouter(tags=["WebSocket"])

TERMINAL_STATUSES = {RunStatus.succeeded, RunStatus.failed, RunStatus.cancelled}
TERMINAL_STATUS_VALUES = {s.value for s in TERMINAL_STATUSES}


def _event_to_frame(event) -> dict:
    return {
        "type": event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
        "payload": event.payload or {},
        "sequence": event.sequence,
    }


def _terminal_frame(status: RunStatus, pr_url: str | None, pr_number: int | None) -> dict:
    return {
        "type": "terminal",
        "status": status.value,
        "pr_url": pr_url,
        "pr_number": pr_number,
    }


@ws_router.websocket("/ws/agent_runs/{run_id}")
async def agent_run_ws(websocket: WebSocket, run_id: uuid.UUID):
    await websocket.accept()

    try:
        user = await current_user_ws(websocket)
    except Exception:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4001)
        return

    if not settings.redis_url:
        await websocket.close(code=4005)
        return

    def _load_run_state():
        with Session(engine) as session:
            run = get_agent_run_for_user(session, run_id, user.id)
            if not run:
                return None
            events = list_events_for_user(session, run_id, user.id, limit=100)
            pr_url: str | None = None
            pr_number: int | None = None
            if run.status in TERMINAL_STATUSES:
                pr = get_pull_request_for_run_for_user(session, run_id, user.id)
                if pr:
                    pr_url = pr.url
                    pr_number = pr.github_pr_number
            return run.status, [_event_to_frame(e) for e in events], pr_url, pr_number

    state = await asyncio.to_thread(_load_run_state)
    if state is None:
        await websocket.close(code=4004)
        return

    status, history_frames, pr_url, pr_number = state

    try:
        for frame in history_frames:
            await websocket.send_json(frame)
        # Always replay the current status as a synthetic status_change so the
        # client knows the current state even if it connected after the
        # original status_change(running) was published.
        # Negative sequence so it never collides with the run's own counter.
        await websocket.send_json(
            {
                "type": "status_change",
                "payload": {"new_status": status.value},
                "sequence": -1,
            }
        )
    except Exception:
        return

    if status in TERMINAL_STATUSES:
        try:
            await websocket.send_json(_terminal_frame(status, pr_url, pr_number))
            await websocket.close(code=1000)
        except Exception:
            pass
        return

    last_sequence = history_frames[-1]["sequence"] if history_frames else -1
    redis = None
    pubsub = None
    channel = f"agent_run:{run_id}"
    try:
        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        # Race guard: the run may have completed between _load_run_state above and
        # subscribe() finishing. Without this re-check we'd miss the final
        # status_change frame and the UI would stay on "running" until refresh.
        post_subscribe = await asyncio.to_thread(_load_run_state)
        if post_subscribe is not None:
            ps_status, ps_history, ps_pr_url, ps_pr_number = post_subscribe
            if ps_status in TERMINAL_STATUSES:
                for frame in ps_history:
                    if frame["sequence"] > last_sequence:
                        await websocket.send_json(frame)
                        last_sequence = frame["sequence"]
                await websocket.send_json(_terminal_frame(ps_status, ps_pr_url, ps_pr_number))
                await websocket.close(code=1000)
                return

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            data = message["data"]
            try:
                event = json.loads(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            seq = event.get("sequence")
            if isinstance(seq, int) and seq <= last_sequence:
                continue
            if isinstance(seq, int):
                last_sequence = seq

            await websocket.send_json(event)

            event_type = event.get("type")
            is_terminal_frame = event_type == "terminal"
            is_terminal_status_change = (
                event_type == "status_change"
                and event.get("payload", {}).get("new_status") in TERMINAL_STATUS_VALUES
            )
            if is_terminal_frame or is_terminal_status_change:
                if is_terminal_status_change:
                    new_status = RunStatus(event["payload"]["new_status"])
                    try:
                        await websocket.send_json(
                            _terminal_frame(new_status, None, None)
                        )
                    except Exception:
                        pass
                try:
                    await websocket.close(code=1000)
                except Exception:
                    pass
                break

    except WebSocketDisconnect:
        pass
    except (aioredis.RedisError, OSError) as exc:
        logger.error("Redis connection failed: %s", exc)
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4005)
    finally:
        if pubsub:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass
        if redis:
            try:
                await redis.close()
            except Exception:
                pass
