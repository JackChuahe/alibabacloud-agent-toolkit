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


SKILLS_PATH_RE = re.compile(
    r"(?P<plugin>alibabacloud[-_a-zA-Z0-9]*)/[^/]*?/?skills/(?P<skill>[^/]+)/(?P<rest>.+)$"
)


def classify(tool_name: str, tool_input: Any) -> Optional[dict]:
    if not tool_name:
        return None

    # 1. Skill tool
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

    # 2. Agent (subagent dispatch)
    if tool_name in ("Agent", "agent"):
        sub = ""
        if isinstance(tool_input, dict):
            sub = tool_input.get("subagent_type", "") or ""
        if not isinstance(sub, str) or not sub.lower().startswith(PLUGIN_PREFIX):
            return None
        plugin = sub.split(":", 1)[0] if ":" in sub else ""
        return {
            "event_type": "subagent_dispatch",
            "skill_name": sub,
            "plugin_name": plugin,
        }

    # 3. Read / view / read_file → SKILL.md or reference file
    if tool_name in ("Read", "view", "read_file"):
        path = ""
        if isinstance(tool_input, dict):
            path = (
                tool_input.get("file_path")
                or tool_input.get("filePath")
                or tool_input.get("path")
                or ""
            )
        if not isinstance(path, str) or PLUGIN_PREFIX not in path.lower():
            return None
        m = SKILLS_PATH_RE.search(path.replace("\\", "/"))
        if not m:
            return None
        plugin = m.group("plugin")
        skill = m.group("skill")
        rest = m.group("rest")
        if rest.lower().endswith("skill.md"):
            return {
                "event_type": "skill_invocation",
                "skill_name": skill,
                "plugin_name": plugin,
            }
        return {
            "event_type": "reference_file_read",
            "skill_name": skill,
            "plugin_name": plugin,
            "query_summary": "read:reference-file",
        }

    # 4. Bash with aliyun CLI
    if tool_name == "Bash":
        cmd = ""
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "") or ""
        if not isinstance(cmd, str) or not re.match(r"^\s*aliyun(\s|$)", cmd):
            return None
        return {
            "event_type": "cli_command_use",
            "cli_command": sanitize.sanitize_cli(cmd),
        }

    # 5. MCP tool (alibabacloud-* MCP server)
    lowered = tool_name.lower()
    if PLUGIN_PREFIX in lowered or "alibabacloud___" in lowered:
        seed = {"event_type": "mcp_tool_use"}
        m = re.search(r"(AlibabaCloud___\w+)", tool_name)
        if m:
            seed["mcp_tool"] = m.group(1)
        # Extract plugin from name like mcp__plugin_<plugin>_<plugin>__*
        m2 = re.search(r"mcp__plugin_(alibabacloud[-_a-z0-9]+?)_", tool_name, re.IGNORECASE)
        if m2:
            seed["plugin_name"] = m2.group(1)
        # If MCP CallCLI, lift cli_command
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "") or ""
            if cmd:
                seed["cli_command"] = sanitize.sanitize_cli(cmd)
        return seed

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
        "mcp-tool": seed.get("mcp_tool", ""),
        "skill-name": seed.get("skill_name", ""),
        "plugin-name": seed.get("plugin_name", ""),
        "cli-command": seed.get("cli_command", ""),
        "query-summary": seed.get("query_summary", ""),
    }
    emit(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
