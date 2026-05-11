import asyncio
import json
import uuid
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.config import settings
from src.core.auth import current_user_ws
from src.core.database import Session, engine
from src.repositories.agent_runs import get_agent_run_for_user

ws_router = APIRouter(tags=["WebSocket"])

@ws_router.websocket("/ws/agent_runs/{run_id}")
async def agent_run_ws(websocket: WebSocket, run_id: uuid.UUID):
    try:
        user = await current_user_ws(websocket)
    except Exception:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4001)
        return

    await websocket.accept()

    def _validate_run():
        with Session(engine) as session:
            return get_agent_run_for_user(session, run_id, user.id)

    run = await asyncio.to_thread(_validate_run)
    if not run:
        await websocket.close(code=4004)
        return

    if not settings.redis_url:
        await websocket.close(code=4005)
        return

    try:
        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        channel = f"agent_run:{run_id}"
        await pubsub.subscribe(channel)
    except Exception:
        await websocket.close(code=4005)
        return

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            
            data = message["data"]
            try:
                event = json.loads(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            
            await websocket.send_json(event)
            
            if event.get("type") == "terminal":
                await websocket.close(code=1000)
                break
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis.close()
        except Exception:
            pass
