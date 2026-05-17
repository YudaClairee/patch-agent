import uuid

import pytest

from src.services.events import RunawayAgentError, RunEmitter


def _emitter(max_steps: int = 40, dup_limit: int = 3) -> RunEmitter:
    em = RunEmitter(
        agent_run_id=uuid.uuid4(),
        max_steps=max_steps,
        duplicate_streak_limit=dup_limit,
    )
    return em


def test_duplicate_streak_aborts_on_third_identical_call():
    em = _emitter(dup_limit=3)
    try:
        em.register_tool_call("exec_command", {"command": "ls"})
        em.register_tool_call("exec_command", {"command": "ls"})
        with pytest.raises(RunawayAgentError, match="repeated identical"):
            em.register_tool_call("exec_command", {"command": "ls"})
    finally:
        em.close()


def test_duplicate_streak_resets_on_different_call():
    em = _emitter(dup_limit=3)
    try:
        em.register_tool_call("exec_command", {"command": "ls"})
        em.register_tool_call("exec_command", {"command": "ls"})
        em.register_tool_call("exec_command", {"command": "pwd"})  # breaks the streak
        em.register_tool_call("exec_command", {"command": "ls"})
        em.register_tool_call("exec_command", {"command": "ls"})  # only 2 in a row, fine
    finally:
        em.close()


def test_max_steps_aborts():
    em = _emitter(max_steps=5, dup_limit=99)
    try:
        for i in range(5):
            em.register_tool_call("exec_command", {"command": f"echo {i}"})
        with pytest.raises(RunawayAgentError, match="exceeded max steps"):
            em.register_tool_call("exec_command", {"command": "echo 6"})
    finally:
        em.close()
