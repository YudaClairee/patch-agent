import json
import redis
from src.core.config import settings


def publish_event(agent_run_id: str, payload: dict) -> None:
    r = redis.Redis.from_url(settings.redis_url)
    r.publish(f"agent_run:{agent_run_id}", json.dumps(payload))
    r.close()
