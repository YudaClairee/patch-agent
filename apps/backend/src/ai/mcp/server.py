from mcp.server.fastmcp import FastMCP
from src.ai.tools import (
    list_files, read_file, write_file, search_file,
    get_git_status, get_git_diff, create_branch, commit_changes, push_branch,
    run_command, run_test, run_lint,
    index_codebase, search_code, get_code_context
)

mcp = FastMCP("P.A.T.C.H. Tools")

@mcp.tool()
def mcp_list_files(workspace_path: str) -> dict: return list_files(workspace_path)

@mcp.tool()
def mcp_read_file(workspace_path: str, file_path: str) -> dict: return read_file(workspace_path, file_path)

@mcp.tool()
def mcp_write_file(workspace_path: str, file_path: str, content: str) -> dict: return write_file(workspace_path, file_path, content)

@mcp.tool()
def mcp_search_file(workspace_path: str, pattern: str) -> dict: return search_file(workspace_path, pattern)

@mcp.tool()
def mcp_git_status(workspace_path: str) -> dict: return get_git_status(workspace_path)

@mcp.tool()
def mcp_git_diff(workspace_path: str) -> dict: return get_git_diff(workspace_path)

@mcp.tool()
def mcp_create_branch(workspace_path: str, branch_name: str) -> dict: return create_branch(workspace_path, branch_name)

@mcp.tool()
def mcp_commit_changes(workspace_path: str, message: str) -> dict: return commit_changes(workspace_path, message)

@mcp.tool()
def mcp_push_branch(workspace_path: str, branch_name: str) -> dict: return push_branch(workspace_path, branch_name)

@mcp.tool()
def mcp_run_command(workspace_path: str, command: str) -> dict: return run_command(workspace_path, command)

@mcp.tool()
def mcp_run_test(workspace_path: str, test_command: str) -> dict: return run_test(workspace_path, test_command)

@mcp.tool()
def mcp_run_lint(workspace_path: str, lint_command: str) -> dict: return run_lint(workspace_path, lint_command)

@mcp.tool()
def mcp_search_code(query: str, repository_id: str, branch: str) -> dict: return search_code(query, repository_id, branch)

@mcp.tool()
def mcp_get_code_context(workspace_path: str, file_path: str) -> dict: return get_code_context(workspace_path, file_path)

@mcp.tool()
def mcp_index_codebase(workspace_path: str, repository_id: str, branch: str) -> dict: return index_codebase(workspace_path, repository_id, branch)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")