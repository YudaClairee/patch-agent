import asyncio
import json
import base64
import os
from typing import AsyncIterator
from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.tools import tool

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.litellm import LiteLLMInstrumentor

from src.core.config import settings
from src.ai.tools import (
    list_files, read_file, write_file, search_file,
    get_git_status, get_git_diff, create_branch, commit_changes, push_branch,
    run_command, run_test, run_lint,
    index_codebase, search_code, get_code_context,
    submit_pull_request,
)

langfuse_auth = base64.b64encode(
    f"{settings.langfuse_public_key}:{settings.langfuse_secret_key}".encode()
).decode()

exporter = OTLPSpanExporter(
    endpoint=f"{settings.langfuse_host}/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {langfuse_auth}"},
)
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)

LiteLLMInstrumentor().instrument(tracer_provider=provider)
tracer = trace.get_tracer(__name__)

os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key

WORKSPACE = "/workspace"

SYSTEM_PROMPT = """
You are P.A.T.C.H. — Programming Assistant for Tasks, Code, and Handoffs.
You are a fully autonomous coding agent. You receive a task and loop until done.

Your workflow is ALWAYS:
1. Search relevant code using search_code to find the right files.
2. Read specific files using read_file for full context.
3. State a clear plan before making ANY changes.
4. Make changes using write_file.
5. Run tests using workspace_run_test to verify correctness.
6. Run lint using workspace_run_lint to verify code style.
7. Call workspace_submit_pull_request to finalize your work.

Hard rules:
- NEVER modify files outside /workspace.
- NEVER read or write .env, .pem, .key files.
- ALWAYS state your plan before editing any file.
- ALWAYS run tests AND lint before calling workspace_submit_pull_request.
- Only call workspace_submit_pull_request after tests and lint pass.
- Keep changes minimal and focused on the task.
- If tests or lint fail, fix the issues and re-run before submitting.
"""


def _build_agent(repository_id: str, branch: str, instructions: str = SYSTEM_PROMPT) -> Agent:
    model = LiteLLM(
        id="openrouter/google/gemini-2.0-flash-001",
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url, # type: ignore
    )

    @tool
    def workspace_list_files(path: str = WORKSPACE) -> dict:
        """List all files in the workspace directory."""
        return list_files(path)

    @tool
    def workspace_read_file(file_path: str) -> dict:
        """Read the content of a specific file."""
        return read_file(WORKSPACE, file_path)

    @tool
    def workspace_write_file(file_path: str, content: str) -> dict:
        """Write or overwrite content to a specific file."""
        return write_file(WORKSPACE, file_path, content)

    @tool
    def workspace_search_file(pattern: str) -> dict:
        """Search files by name pattern inside the workspace."""
        return search_file(WORKSPACE, pattern)

    @tool
    def workspace_git_status() -> dict:
        """Get the current git status of the workspace."""
        return get_git_status(WORKSPACE)

    @tool
    def workspace_git_diff() -> dict:
        """Get the git diff of all current changes."""
        return get_git_diff(WORKSPACE)

    @tool
    def workspace_create_branch(branch_name: str) -> dict:
        """Create and checkout a new git branch."""
        return create_branch(WORKSPACE, branch_name)

    @tool
    def workspace_commit_changes(message: str) -> dict:
        """Stage all changes and commit them with a message."""
        return commit_changes(WORKSPACE, message)

    @tool
    def workspace_push_branch(branch_name: str) -> dict:
        """Push the branch to origin."""
        return push_branch(WORKSPACE, branch_name)

    @tool
    def workspace_run_command(command: str) -> dict:
        """Run a shell command safely inside the workspace."""
        return run_command(WORKSPACE, command)

    @tool
    def workspace_run_test(test_command: str) -> dict:
        """Run testing commands (e.g. pytest). Must pass before creating a PR."""
        return run_test(WORKSPACE, test_command)

    @tool
    def workspace_run_lint(lint_command: str) -> dict:
        """Run linting commands (e.g. ruff). Must pass before creating a PR."""
        return run_lint(WORKSPACE, lint_command)

    @tool
    def codebase_search_code(query: str, n_results: int = 5) -> dict:
        """Search for relevant code snippets in the indexed repository."""
        return search_code(query, repository_id, branch, n_results)

    @tool
    def codebase_get_code_context(file_path: str) -> dict:
        """Get the full content of a specific code file for better context."""
        return get_code_context(WORKSPACE, file_path)

    @tool
    def codebase_index() -> dict:
        """Index all source code files in the workspace into ChromaDB."""
        return index_codebase(WORKSPACE, repository_id, branch)

    @tool
    def workspace_submit_pull_request(title: str, body: str) -> dict:
        """
        Create or update a Pull Request with the current changes.
        Requires workspace_run_test and workspace_run_lint to have passed first.
        This is the FINAL step — call it only when the task is complete.
        """
        return submit_pull_request(title, body)

    return Agent(
        name="P.A.T.C.H.",
        instructions=instructions,
        model=model,
        tools=[
            workspace_list_files, workspace_read_file, workspace_write_file, workspace_search_file,
            workspace_git_status, workspace_git_diff, workspace_create_branch,
            workspace_commit_changes, workspace_push_branch,
            workspace_run_command, workspace_run_test, workspace_run_lint,
            codebase_search_code, codebase_get_code_context, codebase_index,
            workspace_submit_pull_request,
        ],
        show_tool_calls=True,  # type: ignore
    )


async def run_agent_stream(
    instruction: str,
    workspace_path: str = WORKSPACE,
    repository_id: str = "",
    branch: str = "",
    agent_run_id: str = "",
    follow_up_context: str | None = None,
) -> AsyncIterator[str]:

    instructions = follow_up_context if follow_up_context else SYSTEM_PROMPT
    agent = _build_agent(repository_id, branch, instructions=instructions)

    with tracer.start_as_current_span(f"run_{agent_run_id}") as span:
        span.set_attribute("repository_id", repository_id)
        span.set_attribute("instruction", instruction)

        try:
            async with asyncio.timeout(settings.agent_max_wall_time_sec):
                async for event in agent.run_stream(message=instruction, max_turns=15):  # type: ignore
                    if hasattr(event, "content") and event.content:
                        yield f"data: {json.dumps({'type': 'text_delta', 'content': event.content})}\n\n"

                    if hasattr(event, "tool_calls") and event.tool_calls:
                        for call in event.tool_calls:
                            yield f"data: {json.dumps({'type': 'tool_call', 'tool_name': call.function.name, 'tool_input': call.function.arguments})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'agent_run_id': agent_run_id})}\n\n"
            span.set_attribute("status", "completed")

        except asyncio.TimeoutError:
            span.set_attribute("status", "timeout")
            yield f"data: {json.dumps({'type': 'error', 'error': f'Agent exceeded wall-time limit of {settings.agent_max_wall_time_sec}s'})}\n\n"

        except Exception as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
