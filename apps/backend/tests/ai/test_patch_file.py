import importlib
import subprocess

import pytest


exec_tools = importlib.import_module("src.ai.tools.exec")


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(exec_tools, "WORKSPACE", str(tmp_path))
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def test_patch_file_accepts_hunk_only_diff(workspace):
    target = workspace / "hello.txt"
    target.write_text("one\ntwo\nthree\n")

    result = exec_tools.patch_file(
        "hello.txt",
        "@@ -1,3 +1,3 @@\n one\n-two\n+TWO\n three\n",
    )

    assert result["ok"] is True
    assert result["normalized_from"] == "hunk-only"
    assert target.read_text() == "one\nTWO\nthree\n"


def test_patch_file_accepts_unified_diff_without_ab_prefix(workspace):
    target = workspace / "hello.txt"
    target.write_text("one\ntwo\nthree\n")

    result = exec_tools.patch_file(
        "hello.txt",
        "--- hello.txt\n+++ hello.txt\n@@ -1,3 +1,3 @@\n one\n-two\n+TWO\n three\n",
    )

    assert result["ok"] is True
    assert result["applied_with"] == "git apply --recount -p0"
    assert target.read_text() == "one\nTWO\nthree\n"


def test_patch_file_accepts_codex_style_update_patch(workspace):
    target = workspace / "hello.txt"
    target.write_text("one\ntwo\nthree\n")

    result = exec_tools.patch_file(
        "hello.txt",
        """*** Begin Patch
*** Update File: hello.txt
@@
 one
-two
+TWO
 three
*** End Patch
""",
    )

    assert result == {
        "ok": True,
        "path": "hello.txt",
        "applied_with": "codex apply_patch format",
        "hunks_applied": 1,
        "stdout": "",
        "stderr": "",
    }
    assert target.read_text() == "one\nTWO\nthree\n"


def test_patch_file_extracts_markdown_fenced_patch(workspace):
    target = workspace / "hello.txt"
    target.write_text("one\ntwo\nthree\n")

    result = exec_tools.patch_file(
        "hello.txt",
        """Here is the patch:

```diff
@@ -1,3 +1,3 @@
 one
-two
+TWO
 three
```
""",
    )

    assert result["ok"] is True
    assert result["normalized_from"] == "hunk-only"
    assert target.read_text() == "one\nTWO\nthree\n"


def test_patch_file_rejects_mismatched_target_path(workspace):
    (workspace / "hello.txt").write_text("one\ntwo\nthree\n")
    (workspace / "other.txt").write_text("one\ntwo\nthree\n")

    with pytest.raises(PermissionError, match="other.txt"):
        exec_tools.patch_file(
            "hello.txt",
            "--- a/other.txt\n+++ b/other.txt\n@@ -1,3 +1,3 @@\n one\n-two\n+TWO\n three\n",
        )
