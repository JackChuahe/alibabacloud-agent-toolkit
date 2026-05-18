#!/usr/bin/env python3
"""Post-tool-use hook handler.

Reads hook payload from stdin (bounded), classifies the event, detects
status, sanitizes outputs, and prints a flat list of CLI args (key on one
line, value on the next) for the bash wrapper to assemble into:

    uvx alibabacloud.mcp-proxy@latest plugin-telemetry <args>

Exit codes:
    0 — args printed (caller should upload)
    1 — event filtered out (no upload)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, Optional

# Make sibling modules importable when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sanitize  # noqa: E402

STATE_DIR_DEFAULT = os.path.expanduser(
    "~/.cache/alibabacloud-agent-toolkit/telemetry"
)
STATE_DIR_FALLBACK = "/tmp/alibabacloud-agent-toolkit-telemetry"
PLUGIN_PREFIX = "alibabacloud"
STDIN_CAP = 65536
JSON_PARSE_WINDOW = 16384
ERROR_REGEX_WINDOW = 500


def state_dir() -> str:
    p = os.environ.get("ALIBABACLOUD_TELEMETRY_STATE_DIR") or STATE_DIR_DEFAULT
    try:
        os.makedirs(p, exist_ok=True)
        return p
    except OSError:
        try:
            os.makedirs(STATE_DIR_FALLBACK, exist_ok=True)
            return STATE_DIR_FALLBACK
        except OSError:
            return ""


def detect_client(payload_str: str) -> str:
    if os.environ.get("COPILOT_CLI") == "1":
        return "copilot-cli"
    if os.environ.get("CODEX_CLI") == "1":
        return "codex"
    if os.environ.get("QODER_WORK") == "1":
        return "qoderwork"
    if "__vscode" in payload_str:
        return "vscode"
    return "claude-code"


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def iso_from_ms(ms: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ms / 1000.0))


def read_start_ts(sd: str, session_id: str, tool_name: str) -> Optional[int]:
    if not sd or not session_id or not tool_name:
        return None
    safe_tool = re.sub(r"[^A-Za-z0-9_-]", "_", tool_name)[:120]
    path = os.path.join(sd, f"{session_id}-{safe_tool}.start")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            ms = int(f.read().strip())
        os.unlink(path)
        return ms
    except (OSError, ValueError):
        return None


def read_turn(sd: str) -> int:
    if not sd:
        return 0
    try:
        with open(os.path.join(sd, "turn")) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0


def classify(tool_name: str, tool_input: Any) -> Optional[dict]:
    """Return event seed (event_type, plugin_name, skill_name, etc.) or None."""
    if not tool_name:
        return None

    # Case 1: Skill tool
    if tool_name in ("Skill", "skill"):
        skill = ""
        if isinstance(tool_input, dict):
            skill = tool_input.get("skill", "") or ""
        if not isinstance(skill, str) or not skill.lower().startswith(PLUGIN_PREFIX):
            return None
        plugin = skill.split(":", 1)[0] if ":" in skill else ""
        return {
            "event_type": "skill_invocation",
            "skill_name": skill,
            "plugin_name": plugin,
        }

    return None


def emit(args: dict) -> None:
    """Print args as alternating --key / value lines, in canonical order."""
    order = [
        "client-name", "event-type", "start-timestamp", "end-timestamp",
        "tool-name", "session-id", "status", "turn",
        "mcp-tool", "skill-name", "plugin-name", "tool-request-id",
        "cli-command", "query-summary", "error-message",
    ]
    for key in order:
        v = args.get(key)
        if v is None or v == "":
            continue
        print(f"--{key}")
        print(v)


def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        return 1
    raw = sys.stdin.buffer.read(STDIN_CAP)
    if not raw:
        return 1
    try:
        text = raw.decode("utf-8", errors="replace")
        data = json.loads(text)
    except Exception:
        return 1

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    session_id = data.get("session_id") or ""

    seed = classify(tool_name, tool_input)
    if seed is None:
        return 1

    sd = state_dir()
    start_ms = read_start_ts(sd, session_id, tool_name)
    end_ms = int(time.time() * 1000)
    if start_ms is None:
        start_ms = end_ms - 1
    turn = read_turn(sd)

    # Status detection (placeholder — Task 9 will replace with full algorithm)
    status = "success"

    args = {
        "client-name": detect_client(text),
        "event-type": seed.get("event_type", ""),
        "start-timestamp": iso_from_ms(start_ms),
        "end-timestamp": iso_from_ms(end_ms),
        "tool-name": tool_name,
        "session-id": session_id,
        "status": status,
        "turn": str(turn),
        "skill-name": seed.get("skill_name", ""),
        "plugin-name": seed.get("plugin_name", ""),
    }
    emit(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
