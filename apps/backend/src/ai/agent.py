"""
P.A.T.C.H. agent — ReAct-style reasoning over a Codex-style 4-tool surface.

Tools exposed to the model:
  - exec_command(command, cwd="/workspace", timeout=60, background=False)
  - write_stdin(pid, data, expect_exit=False, timeout=30)
  - patch_file(path, diff)
  - submit_pull_request(title, body)

Reasoning: agno's `reasoning=True` enables ReAct-style think/act/observe loops.
Observability: Langfuse via OpenTelemetry OTLP (LiteLLMInstrumentor).
"""
import asyncio
import base64
import os
import time
from typing import Callable

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.tools import tool

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.litellm import LiteLLMInstrumentor

from src.core.config import settings
from src.ai.tools import exec_command, write_stdin, patch_file, write_file, submit_pull_request
from src.services.events import RunawayAgentError, RunEmitter

# --- Langfuse / OTLP tracing setup ---
if settings.langfuse_host and settings.langfuse_public_key and settings.langfuse_secret_key:
    langfuse_auth = base64.b64encode(
        f"{settings.langfuse_public_key}:{settings.langfuse_secret_key}".encode()
    ).decode()
    exporter = OTLPSpanExporter(
        endpoint=f"{settings.langfuse_host.rstrip('/')}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {langfuse_auth}"},
    )
    resource = Resource.create({"service.name": "patch-agent"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    LiteLLMInstrumentor().instrument(tracer_provider=provider)
tracer = trace.get_tracer(__name__)

# Mirror the LLM key into the provider-specific env var LiteLLM reads from.
_provider_prefix = (
    settings.llm_model_id.split("/", 1)[0].upper()
    if "/" in settings.llm_model_id
    else "OPENAI"
)
os.environ[f"{_provider_prefix}_API_KEY"] = settings.llm_api_key

WORKSPACE = "/workspace"

SYSTEM_PROMPT = """\
You are P.A.T.C.H. — an autonomous coding agent in a sandboxed Linux container.
The user's repository is already cloned at /workspace. You modify that real repository
and finalize by opening a Pull Request.

# Operating rule (non-negotiable)

You DO NOT chat. You DO NOT answer with prose, code blocks, or explanations.
Every action you take is a tool call. The ONLY way to make progress is to call
one of the four tools below. If you respond without calling a tool, nothing happens
and the task fails.

# Tools (the only five)

1. exec_command(command, cwd="/workspace", timeout=60, background=False)
   Runs any shell command in a PTY. Use this for EVERYTHING except editing files and
   submitting the PR:
   - search:   rg 'pattern' -n           rg --type py 'def foo'        find . -name '*.ts'
   - structural: ast-grep run -p 'function $A() { $$$ }' -l ts
   - read:     cat path/to/file          head -n 50 file               sed -n '120,180p' file
   - test/lint: pytest -x                ruff check .                  npm test    tsc --noEmit
   - git:      git status                git diff                      git log --oneline -10
   - inspect:  ls -la                    tree -L 2                     which python

2. write_stdin(pid, data, expect_exit=False, timeout=30)
   Feed input to a backgrounded exec_command. Most tasks don't need this.

3. write_file(path, content)
   Write full file content to `path` (creates parent dirs). USE THIS for:
   - NEW files (any task creating a file that doesn't exist)
   - Full rewrites where >50% of the file changes
   Returns {ok, path, bytes_written}.

4. patch_file(path, diff)
   Apply a unified diff to an EXISTING file. Tries `git apply --recount` first
   (forgiving of wrong @@ line counts), falls back to `patch -F3` (fuzz 3).
   ONLY use for surgical edits to existing files. ALWAYS `exec_command("cat path")` FIRST
   so context lines are accurate. If patch_file fails with "malformed patch",
   switch to write_file with the full intended file content.

5. submit_pull_request(title, body)
   FINAL step. Stages, commits, pushes a new branch, opens (or updates) the PR.
   Call this exactly once when the task is complete.

# Required workflow

For every task, no exceptions:
  1. exec_command("ls -la") to see what's in the repo.
  2. (Only if needed) exec_command("cat README.md") and/or exec_command("rg 'KEYWORD' -n") to locate code.
  3. (Only if editing existing file) exec_command("cat path/to/file") to read full context.
  4. Apply the edit:
       - NEW file or full rewrite: write_file(path, content)
       - surgical edit to existing file: patch_file(path, diff)
  5. Verify ONLY if it matches the repo. See "Verification rules" below.
  6. submit_pull_request(title, body) — STOP HERE. Do not call any more tools after this.

# Verification rules (very important — do NOT run irrelevant tests)

Only run a verification command if the repo clearly supports it:
  - `pytest` ONLY if there's a `pyproject.toml` / `setup.py` / `tests/` dir AND a python project.
  - `npm test` / `npm run build` ONLY if there's a `package.json` with a matching script.
  - `cargo test` ONLY if there's a `Cargo.toml`.
  - `go test ./...` ONLY if there's a `go.mod`.
  - For pure HTML/CSS/static-asset changes with NO test framework in the repo,
    DO NOT run any test command. Just verify the file was written
    (e.g. `exec_command("cat path/to/file | head -30")`) and proceed to submit.

If `ls -la` only shows static files (index.html, css/, etc.) and no package manager
config, the right verification is: read back the file you wrote. Then submit.

# After submit_pull_request

Once `submit_pull_request` returns `{ok: true, ...}`, your job is DONE.
Do NOT call any further tools. Do NOT run more tests. Do NOT add commits.
The next message in this stream from you would be ignored — STOP.

# Hard rules

- NEVER write or read files outside /workspace.
- NEVER read .env, .pem, .key files.
- Keep changes minimal and focused. No drive-by refactors.
- If the task is impossible or blocked, call submit_pull_request with a body that
  explains what you tried and what blocks the change — do NOT just stop talking.
- New-file tasks: create the file in a sensible directory under /workspace
  (e.g. examples/, demo/, scripts/, public/). Don't ask where to put it — pick a path
  by inspecting the repo layout with `ls` first.

# Termination

There is exactly one legitimate way to end this run: call `submit_pull_request`.
That holds whether the task succeeded, was already done, or was impossible. If the
change is trivial/done, submit a PR (or a no-op PR body explaining "already done").
If the task is blocked, submit a PR whose body explains what you tried and why you
stopped. Do NOT just stop emitting tool calls — that wastes budget and produces no
artifact for the user.
"""


def _truncate_for_model(result: dict, limit: int) -> dict:
    """Return a copy of `result` with any large string field shortened so the
    model's transcript doesn't balloon. The original `result` is still persisted
    untruncated via `emit_tool_result`, so the UI can show the full output."""
    if not isinstance(result, dict) or limit <= 0:
        return result
    out = dict(result)
    for k, v in list(out.items()):
        if isinstance(v, str) and len(v) > limit:
            half = max(limit // 2, 200)
            dropped = len(v) - half * 2
            out[k] = f"{v[:half]}\n…[truncated {dropped} chars]…\n{v[-half:]}"
    return out


def _instrumented(emitter: RunEmitter | None, tool_name: str, fn: Callable, kwargs: dict) -> dict:
    """Run a tool, emitting tool_call before and tool_result after.
    Captures duration and success/error so the live stream mirrors Langfuse.
    Returns a possibly-truncated copy of the result for the model, while emitting
    the full result to the DB/UI."""
    if emitter is None:
        return fn(**kwargs)
    emitter.register_tool_call(tool_name, kwargs)
    emitter.emit_tool_call(tool_name, kwargs)
    start = time.monotonic()
    try:
        result = fn(**kwargs)
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        emitter.emit_tool_result(tool_name, {}, "error", duration_ms, str(exc))
        raise
    duration_ms = int((time.monotonic() - start) * 1000)
    is_error = isinstance(result, dict) and (
        result.get("ok") is False or result.get("error") is not None
    )
    emitter.emit_tool_result(
        tool_name,
        result,
        "error" if is_error else "success",
        duration_ms,
        error_message=(result.get("error") if is_error and isinstance(result, dict) else None),
    )
    return _truncate_for_model(result, settings.agent_max_tool_output_chars)


def _build_agent(
    instructions: str = SYSTEM_PROMPT,
    done_flag: dict | None = None,
    emitter: RunEmitter | None = None,
) -> Agent:
    model_kwargs: dict = {
        "id": settings.llm_model_id,
        "api_key": settings.llm_api_key,
        "request_params": {"tool_choice": "auto"},
    }
    if settings.llm_base_url:
        model_kwargs["api_base"] = settings.llm_base_url
    model = LiteLLM(**model_kwargs)

    @tool
    def tool_exec_command(
        command: str,
        cwd: str = WORKSPACE,
        timeout: int = 60,
        background: bool = False,
    ) -> dict:
        """Run a shell command in /workspace via PTY. Returns {output, exit_code, timed_out} or {pid, started} if background."""
        return _instrumented(
            emitter,
            "exec_command",
            exec_command,
            {"command": command, "cwd": cwd, "timeout": timeout, "background": background},
        )

    @tool
    def tool_write_stdin(
        pid: int,
        data: str,
        expect_exit: bool = False,
        timeout: int = 30,
    ) -> dict:
        """Write data + newline to a backgrounded process; drain new output. Returns {output, exited, exit_code}."""
        return _instrumented(
            emitter,
            "write_stdin",
            write_stdin,
            {"pid": pid, "data": data, "expect_exit": expect_exit, "timeout": timeout},
        )

    @tool
    def tool_patch_file(path: str, diff: str) -> dict:
        """Apply a unified diff to an EXISTING file under /workspace. Tries git apply --recount first, then patch -F3. Use write_file for new files."""
        return _instrumented(emitter, "patch_file", patch_file, {"path": path, "diff": diff})

    @tool
    def tool_write_file(path: str, content: str) -> dict:
        """Write full file content to path under /workspace. Use for new files or full rewrites — no diff needed."""
        return _instrumented(emitter, "write_file", write_file, {"path": path, "content": content})

    @tool
    def tool_submit_pull_request(title: str, body: str) -> dict:
        """FINAL step. Commit, push, open (or update) the Pull Request. The agent MUST stop after this returns ok=true."""
        result = _instrumented(
            emitter, "submit_pull_request", submit_pull_request, {"title": title, "body": body}
        )
        # submit_pull_request returns {"status": "pr_created" | "pr_recovered" | "comment_added", ...}
        # on success; any of those means the run is done. We tolerate a missing
        # "error" key and the historical `ok: true` shape as well.
        is_done = isinstance(result, dict) and result.get("error") is None and (
            result.get("ok") is True
            or result.get("status") in {"pr_created", "pr_recovered", "comment_added"}
        )
        if done_flag is not None and is_done:
            done_flag["done"] = True
        return result

    return Agent(
        name="P.A.T.C.H.",
        instructions=instructions,
        model=model,
        tools=[
            tool_exec_command,
            tool_write_stdin,
            tool_write_file,
            tool_patch_file,
            tool_submit_pull_request,
        ],
        tool_choice="auto",
    )


async def run_agent(
    emitter: RunEmitter,
    instruction: str,
    workspace_path: str = WORKSPACE,
    repository_id: str = "",
    branch: str = "",
    agent_run_id: str = "",
    follow_up_context: str | None = None,
) -> None:
    """Run the agent to completion. Every observable action (assistant text, tool call,
    tool result, error) is emitted via `emitter` — which writes to DB and Redis — so the
    UI live-stream matches what Langfuse traces."""
    _ = (workspace_path, repository_id, branch)
    instructions = follow_up_context if follow_up_context else SYSTEM_PROMPT
    done_flag: dict = {"done": False}
    agent = _build_agent(instructions=instructions, done_flag=done_flag, emitter=emitter)

    with tracer.start_as_current_span(f"run_{agent_run_id}") as span:
        span.set_attribute("instruction", instruction)
        span.set_attribute("input.value", instruction)
        span.set_attribute("gen_ai.prompt", instruction)
        collected_output: list[str] = []
        # Buffer text deltas instead of emitting one frame per token. We flush
        # only on logical boundaries (sentence/newline or >200 chars) so the
        # timeline shows readable assistant messages, not "Pull / request /
        # created / successfully / ." spam.
        text_buffer: list[str] = []

        def _flush_text() -> None:
            if not text_buffer:
                return
            emitter.emit_message("".join(text_buffer).strip())
            text_buffer.clear()

        def _buffer_text(chunk: str) -> None:
            # Just accumulate. Agno streams content token-by-token, and any
            # mid-stream flush risks splitting a single assistant message into
            # word-sized fragments in the timeline. We flush exactly once at
            # end-of-stream (or in error/timeout handlers), producing one
            # coherent message frame per assistant turn.
            text_buffer.append(chunk)

        try:
            async with asyncio.timeout(settings.agent_max_wall_time_sec):
                async for event in agent.arun(input=instruction, stream=True):  # type: ignore[attr-defined]
                    content = getattr(event, "content", None)
                    if content:
                        collected_output.append(content)
                        _buffer_text(content)
                    if done_flag["done"]:
                        break
            _flush_text()

            final_output = "".join(collected_output)[:8000]
            span.set_attribute("output.value", final_output)
            span.set_attribute("gen_ai.completion", final_output)
            emitter.emit_summary({"agent_run_id": agent_run_id, "output": final_output})
            span.set_attribute("status", "completed")

        except asyncio.TimeoutError:
            _flush_text()
            span.set_attribute("status", "timeout")
            emitter.emit_error(
                f"Agent exceeded wall-time limit of {settings.agent_max_wall_time_sec}s"
            )
            raise

        except RunawayAgentError as exc:
            _flush_text()
            span.set_attribute("status", "aborted")
            span.record_exception(exc)
            emitter.emit_error(str(exc))
            raise

        except Exception as exc:
            _flush_text()
            span.set_attribute("status", "error")
            span.record_exception(exc)
            emitter.emit_error(str(exc))
            raise
