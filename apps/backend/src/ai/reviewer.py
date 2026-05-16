"""
P.A.T.C.H. Reviewer — analyses a PR diff and returns structured findings.

Runs as a direct LiteLLM call (no Docker container, no ReAct loop) from within
the Celery worker. The reviewer is intentionally stateless and read-only.
"""
import json
import logging
import os
import re

import litellm

from src.core.config import settings

logger = logging.getLogger(__name__)

REVIEWER_SYSTEM_PROMPT = """\
You are P.A.T.C.H. Reviewer, a senior software engineer performing automated code review.

Your job: read a PR diff and identify real bugs, security vulnerabilities, or missing test coverage.

Output ONLY a JSON object — no markdown, no extra text:
{"findings": [
  {
    "file_path": "<path of the affected file>",
    "severity": "critical|high|medium|low",
    "category": "correctness|security|tests|style|performance",
    "issue": "<concise description of what is wrong>",
    "suggestion": "<specific, actionable fix>"
  }
]}

Severity guide:
  critical — will cause runtime errors, panics, data loss, or security vulnerabilities
  high     — likely bugs, missing tests for changed behaviour, broken contracts
  medium   — bad patterns, missing edge cases, poor error handling
  low      — style, naming, minor nitpicks

Rules:
  - Be conservative. Report only issues you are confident about.
  - Prefer 3–5 high-confidence findings over 15 guesses.
  - Do NOT flag whitespace, comments, or formatting unless clearly broken.
  - If the diff looks correct and complete, return {"findings": []}.
"""


def run_review(diff_text: str, pr_title: str = "") -> list[dict]:
    """
    Analyse a unified diff and return a list of structured findings.
    Makes a single LiteLLM call with json_object response format where supported.
    Falls back to regex parsing if the provider wraps output in markdown fences.
    """
    model_id = settings.llm_reviewer_model_id or settings.llm_model_id
    api_key = settings.llm_api_key

    # Mirror key into provider-specific env var (same pattern as agent.py)
    if "/" in model_id:
        provider = model_id.split("/", 1)[0].upper()
        os.environ[f"{provider}_API_KEY"] = api_key

    truncated_diff = diff_text[:12000]
    if len(diff_text) > 12000:
        truncated_diff += "\n\n...[diff truncated — remaining changes not shown]..."

    user_msg = f"PR title: {pr_title}\n\nDiff:\n{truncated_diff}" if pr_title else f"Diff:\n{truncated_diff}"

    base_kwargs: dict = {
        "model": model_id,
        "api_key": api_key,
        "messages": [
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    }
    if settings.llm_base_url:
        base_kwargs["api_base"] = settings.llm_base_url

    try:
        # Try JSON-mode first; not all providers support it, so fall back gracefully.
        try:
            response = litellm.completion(**{**base_kwargs, "response_format": {"type": "json_object"}})
        except Exception:
            response = litellm.completion(**base_kwargs)

        content = (response.choices[0].message.content or "{}").strip()
        # Strip markdown code fences if the model wrapped its output
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content).strip()

        data = json.loads(content)
        findings = data.get("findings", [])
        # Validate shape; drop malformed entries silently
        return [
            f for f in findings
            if isinstance(f, dict)
            and all(k in f for k in ("file_path", "severity", "category", "issue", "suggestion"))
        ]
    except Exception:
        logger.exception("Reviewer LLM call failed for model=%s", model_id)
        return []
