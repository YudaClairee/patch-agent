import json
import logging
import threading
import uuid
from datetime import datetime, timezone

import redis
from sqlmodel import Session

from src.core.config import settings
from src.core.database import engine
from src.models.agent_run_event import AgentRunEvent
from src.models.enums import EventType, ToolCallStatus
from src.models.tool_call import ToolCall

logger = logging.getLogger(__name__)


def _publish(agent_run_id: str, frame: dict) -> None:
    r = redis.Redis.from_url(settings.redis_url)
    try:
        r.publish(f"agent_run:{agent_run_id}", json.dumps(frame, default=str))
    finally:
        r.close()


def publish_event(agent_run_id: str, payload: dict) -> None:
    """Publish a pre-shaped frame. Caller is responsible for the {type, payload, sequence}
    contract — prefer the typed helpers below when constructing new emitters."""
    _publish(agent_run_id, payload)


def publish_run_frame(
    agent_run_id: str,
    event_type: EventType,
    payload: dict,
    sequence: int,
) -> None:
    """Publish a frame in the canonical {type, payload, sequence} shape consumed by
    the frontend's AgentRunWebSocketFrame type."""
    _publish(
        agent_run_id,
        {"type": event_type.value, "payload": payload, "sequence": sequence},
    )


def publish_status_change(agent_run_id: str, new_status: str, sequence: int) -> None:
    publish_run_frame(
        agent_run_id,
        EventType.status_change,
        {"new_status": new_status},
        sequence,
    )


def publish_error(agent_run_id: str, message: str, sequence: int) -> None:
    publish_run_frame(agent_run_id, EventType.error, {"message": message}, sequence)


class RunawayAgentError(RuntimeError):
    """Raised when the agent hits the step cap or repeats the same tool call too many
    times in a row. Surfaced as a friendly error frame in the live stream."""


def _normalize_payload(value) -> dict:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"result": str(value)}


class RunEmitter:
    """Owns the per-run sequence counter and writes every event to both the DB
    and Redis. Used by the runner loop AND by the @tool wrappers inside the agent —
    that way every observable action (tool call start, tool result, assistant text)
    becomes a frame in the live stream, matching what Langfuse captures."""

    def __init__(
        self,
        agent_run_id: uuid.UUID,
        max_steps: int = 40,
        duplicate_streak_limit: int = 3,
    ) -> None:
        self.agent_run_id = agent_run_id
        self.agent_run_id_str = str(agent_run_id)
        self._lock = threading.Lock()
        self._sequence = 0
        self.total_tool_calls = 0
        self.max_steps = max_steps
        self.duplicate_streak_limit = duplicate_streak_limit
        self.step_count = 0
        self._last_tool_signature: tuple[str, str] | None = None
        self.duplicate_streak = 0

    def register_tool_call(self, tool_name: str, kwargs: dict) -> None:
        """Bump counters and raise RunawayAgentError if the agent is looping or
        has exceeded the step cap. Call once per tool invocation, before running it."""
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise RunawayAgentError(
                f"aborted: exceeded max steps ({self.max_steps}) without completing"
            )
        try:
            args_blob = json.dumps(kwargs, sort_keys=True, default=str)[:512]
        except Exception:
            args_blob = repr(kwargs)[:512]
        sig = (tool_name, args_blob)
        if sig == self._last_tool_signature:
            self.duplicate_streak += 1
        else:
            self.duplicate_streak = 1
            self._last_tool_signature = sig
        if self.duplicate_streak >= self.duplicate_streak_limit:
            raise RunawayAgentError(
                f"aborted: repeated identical tool call {self.duplicate_streak}x ({tool_name})"
            )

    def _next_seq(self) -> int:
        with self._lock:
            seq = self._sequence
            self._sequence += 1
            return seq

    def _append_event(self, event_type: EventType, payload: dict, seq: int) -> None:
        try:
            with Session(engine) as session:
                session.add(
                    AgentRunEvent(
                        agent_run_id=self.agent_run_id,
                        sequence=seq,
                        event_type=event_type,
                        payload=payload,
                    )
                )
                session.commit()
        except Exception:
            logger.exception("failed to persist agent_run_event seq=%s", seq)

    def emit_message(self, content: str) -> None:
        seq = self._next_seq()
        payload = {"content": content}
        self._append_event(EventType.message, payload, seq)
        publish_run_frame(self.agent_run_id_str, EventType.message, payload, seq)

    def emit_tool_call(self, tool_name: str, tool_input: dict) -> int:
        seq = self._next_seq()
        started_at = datetime.now(timezone.utc)
        payload = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "started_at": started_at.isoformat(),
        }
        self._append_event(EventType.tool_call, payload, seq)
        try:
            with Session(engine) as session:
                session.add(
                    ToolCall(
                        agent_run_id=self.agent_run_id,
                        sequence=seq,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        status=ToolCallStatus.pending,
                        started_at=started_at,
                    )
                )
                session.commit()
        except Exception:
            logger.exception("failed to persist tool_call seq=%s", seq)
        publish_run_frame(self.agent_run_id_str, EventType.tool_call, payload, seq)
        self.total_tool_calls += 1
        return seq

    def emit_tool_result(
        self,
        tool_name: str,
        tool_output,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
    ) -> None:
        seq = self._next_seq()
        output_dict = _normalize_payload(tool_output)
        payload = {
            "tool_name": tool_name,
            "tool_output": output_dict,
            "status": status,
            "duration_ms": duration_ms,
            "error_message": error_message,
        }
        self._append_event(EventType.tool_result, payload, seq)
        try:
            with Session(engine) as session:
                session.add(
                    ToolCall(
                        agent_run_id=self.agent_run_id,
                        sequence=seq,
                        tool_name=tool_name,
                        tool_input={},
                        status=ToolCallStatus.success if status == "success" else ToolCallStatus.error,
                        tool_output=output_dict,
                        error_message=error_message,
                        duration_ms=duration_ms,
                        finished_at=datetime.now(timezone.utc),
                    )
                )
                session.commit()
        except Exception:
            logger.exception("failed to persist tool_result seq=%s", seq)
        publish_run_frame(self.agent_run_id_str, EventType.tool_result, payload, seq)

    def emit_error(self, message: str) -> None:
        seq = self._next_seq()
        payload = {"message": message}
        self._append_event(EventType.error, payload, seq)
        publish_run_frame(self.agent_run_id_str, EventType.error, payload, seq)

    def emit_summary(self, payload: dict) -> None:
        seq = self._next_seq()
        self._append_event(EventType.summary, payload, seq)
        publish_run_frame(self.agent_run_id_str, EventType.summary, payload, seq)
