#!/usr/bin/env python3
"""Pre-tool-use hook handler.

Reads hook payload from stdin (bounded to 64 KB), extracts tool_name and
session_id, writes a start-time marker, and resets turn counter on session
swap. Silent on any error — never blocks the agent.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

STATE_DIR_DEFAULT = os.path.expanduser(
    "~/.cache/alibabacloud-agent-toolkit/telemetry"
)
STATE_DIR_FALLBACK = "/tmp/alibabacloud-agent-toolkit-telemetry"
PLUGIN_PREFIX = "alibabacloud"
STDIN_CAP = 65536


def state_dir() -> str:
    p = os.environ.get("ALIBABACLOUD_TELEMETRY_STATE_DIR") or STATE_DIR_DEFAULT
    try:
        os.makedirs(p, exist_ok=True)
        return p
    except OSError:
        try:
            os.makedirs(STATE_DIR_FALLBACK, exist_ok=True)
        except OSError:
            return ""
        return STATE_DIR_FALLBACK


def read_stdin_bounded() -> bytes:
    return sys.stdin.buffer.read(STDIN_CAP)


def is_ours_tool(tool_name: str, tool_input) -> bool:
    """Return True when this tool call concerns one of our plugins."""
    if not tool_name:
        return False
    lower = tool_name.lower()
    if PLUGIN_PREFIX in lower:
        return True
    if tool_name in ("Skill", "skill"):
        skill = ""
        if isinstance(tool_input, dict):
            skill = tool_input.get("skill", "") or ""
        if isinstance(skill, str) and PLUGIN_PREFIX in skill.lower():
            return True
    if tool_name in ("Agent", "agent"):
        sub = ""
        if isinstance(tool_input, dict):
            sub = tool_input.get("subagent_type", "") or ""
        if isinstance(sub, str) and PLUGIN_PREFIX in sub.lower():
            return True
    if tool_name == "Bash":
        cmd = ""
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "") or ""
        if isinstance(cmd, str) and re.match(r"^\s*aliyun(\s|$)", cmd):
            return True
    return False


def _debug_enabled() -> bool:
    return os.environ.get("ALIBABACLOUD_TELEMETRY_DEBUG") == "1"


def _debug(msg: str) -> None:
    if _debug_enabled():
        try:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
        except Exception:
            pass


def _detail(tool_name: str, tool_input) -> str:
    """Best-effort short tag describing what the tool is about (no PII)."""
    if not isinstance(tool_input, dict):
        return ""
    if tool_name in ("Skill", "skill"):
        v = tool_input.get("skill", "") or ""
        return f"skill={v}" if v else ""
    if tool_name in ("Agent", "agent"):
        v = tool_input.get("subagent_type", "") or ""
        return f"subagent={v}" if v else ""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "") or ""
        if isinstance(cmd, str) and cmd.strip():
            head = cmd.strip().split()[0]
            head = re.sub(r"[^A-Za-z0-9._-]", "_", head)[:32]
            return f"cmd_head={head}"
    return ""


def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        _debug("[pre] decision=skip reason=opted-out")
        return 0
    raw = read_stdin_bounded()
    if not raw:
        _debug("[pre] decision=skip reason=empty-stdin")
        return 0
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        _debug("[pre] decision=skip reason=invalid-json")
        return 0
    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    session_id = data.get("session_id") or ""
    if not is_ours_tool(tool_name, tool_input):
        _debug(
            f"[pre] tool={tool_name or '<none>'} decision=skip reason=not-ours"
        )
        return 0

    sd = state_dir()
    if not sd:
        _debug(
            f"[pre] tool={tool_name} decision=skip reason=no-state-dir"
        )
        return 0

    # Session swap → reset turn
    if session_id:
        last_file = os.path.join(sd, "current-session")
        last = ""
        if os.path.exists(last_file):
            try:
                with open(last_file) as f:
                    last = f.read().strip()
            except OSError:
                pass
        if session_id != last:
            try:
                with open(os.path.join(sd, "turn"), "w") as f:
                    f.write("0")
                with open(last_file, "w") as f:
                    f.write(session_id)
            except OSError:
                pass

    # Write start marker keyed by session+tool (sanitize tool name to filename)
    safe_tool = re.sub(r"[^A-Za-z0-9_-]", "_", tool_name)[:120]
    start_path = os.path.join(sd, f"{session_id}-{safe_tool}.start")
    try:
        with open(start_path, "w") as f:
            f.write(str(int(time.time() * 1000)))
    except OSError:
        pass

    detail = _detail(tool_name, tool_input)
    suffix = (" " + detail) if detail else ""
    _debug(
        f"[pre] tool={tool_name}{suffix} decision=track session={session_id or '<none>'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
