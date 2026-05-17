import redis

from src.services.events import publish_status_change


def test_publish_status_change_is_non_fatal_when_redis_disconnects(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise redis.ConnectionError("Connection closed by server.")

    monkeypatch.setattr(
        "src.services.events.redis.Redis.from_url",
        raise_connection_error,
    )

    publish_status_change("run-123", "running", sequence=-1)
