"""Ways to get an answer from a model. Each backend returns {answer, citations, handoff} plus metadata."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from assistant.corpus import Chunk

# Every answer has this shape, whichever version or model produced it.
SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "The reply shown to the customer."},
        "citations": {"type": "array", "items": {"type": "string"}, "description": "IDs of the sources used."},
        "handoff": {"type": "boolean", "description": "True if a person from support needs to follow up."},
    },
    "required": ["answer", "citations", "handoff"],
}

# Real-model sessions run from an empty folder, so no project files or settings leak in.
SANDBOX = Path(tempfile.gettempdir()) / "rag-docs-assistant-sandbox"


class ModelError(RuntimeError):
    pass


class UsageLimit(RuntimeError):
    """The Claude subscription's usage limit was hit. Retrying won't help until it resets."""


def run_claude_code(system: str, user: str, model: str, chunks: list[Chunk]) -> dict:
    """One `claude -p` call: our system prompt, no tools, no MCP servers, structured output."""
    SANDBOX.mkdir(exist_ok=True)
    cmd = ["claude", "-p", "--model", model, "--system-prompt", system, "--tools", "", "--setting-sources", "",
           "--strict-mcp-config", "--exclude-dynamic-system-prompt-sections",
           "--output-format", "json", "--json-schema", json.dumps(SCHEMA)]
    proc = subprocess.run(cmd, input=user, cwd=SANDBOX, capture_output=True, text=True, timeout=300,
                          env={**os.environ, "ENABLE_TOOL_SEARCH": "false"})
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise ModelError(f"{proc.stdout[-300:]} {proc.stderr[-300:]}")
    result = str(data.get("result"))
    if "hit your session limit" in result or "usage limit" in result.lower():
        raise UsageLimit(result)
    out = data.get("structured_output")
    if proc.returncode or data.get("is_error") or not isinstance(out, dict):
        raise ModelError(result[:300])
    return {"answer": out.get("answer", ""), "citations": list(out.get("citations") or []),
            "handoff": bool(out.get("handoff")), "cost_usd": float(data.get("total_cost_usd") or 0),
            "duration_ms": int(data.get("duration_ms") or 0), "model_ids": sorted(data.get("modelUsage") or {})}


def run_mock(system: str, user: str, model: str, chunks: list[Chunk]) -> dict:
    """Offline stand-in for a model: replies with the first lines of the top source and cites it.
    It never hands off and never checks anything. Used in CI to test the pipeline, guards and grader;
    it says nothing about how a real model behaves."""
    top = chunks[0]
    body = [ln for ln in top.text.splitlines()[1:] if ln.strip()] if top.meta else top.text.splitlines()
    return {"answer": " ".join(body[:6])[:600], "citations": [top.id], "handoff": False,
            "cost_usd": 0.0, "duration_ms": 0, "model_ids": []}


BACKENDS = {"mock": run_mock, "claude-code": run_claude_code}

# Claude Code can add local paths or the account email to a session. Keep them out of saved results.
_PATH = re.compile(r"(/Users/|/home/|/private/|/var/folders/)\S+")
_EMAIL = re.compile(r"[\w.+-]+@(?![\w-]+(\.[\w-]+)*\.example\b)[\w-]+(\.[\w-]+)+")


def redact(text: str) -> str:
    return _PATH.sub("[path]", _EMAIL.sub("[email]", text))
