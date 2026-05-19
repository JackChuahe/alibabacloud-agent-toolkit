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


def classify_with_reason(
    tool_name: str, tool_input: Any
) -> tuple[Optional[dict], Optional[str], dict]:
    """Classify a tool call.

    Returns (seed, reject_reason, extra) where:
      - seed is a non-empty dict on match (and reject_reason is None)
      - reject_reason is a stable token on miss (and seed is None)
      - extra carries optional debug context (e.g. cmd_head for bash-not-aliyun)
    """
    extra: dict = {}
    if not tool_name:
        return None, "empty-tool-name", extra

    # 1. Skill tool
    if tool_name in ("Skill", "skill"):
        skill = ""
        if isinstance(tool_input, dict):
            skill = tool_input.get("skill", "") or ""
        if not isinstance(skill, str) or not skill.lower().startswith(PLUGIN_PREFIX):
            return None, "non-alibabacloud-skill", extra
        plugin = skill.split(":", 1)[0] if ":" in skill else ""
        return {
            "event_type": "skill_invocation",
            "skill_name": skill,
            "plugin_name": plugin,
        }, None, extra

    # 2. Agent (subagent dispatch)
    if tool_name in ("Agent", "agent"):
        sub = ""
        if isinstance(tool_input, dict):
            sub = tool_input.get("subagent_type", "") or ""
        if not isinstance(sub, str) or not sub.lower().startswith(PLUGIN_PREFIX):
            return None, "non-alibabacloud-subagent", extra
        plugin = sub.split(":", 1)[0] if ":" in sub else ""
        return {
            "event_type": "subagent_dispatch",
            "skill_name": sub,
            "plugin_name": plugin,
        }, None, extra

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
            return None, "read-no-alibabacloud-segment", extra
        m = SKILLS_PATH_RE.search(path.replace("\\", "/"))
        if not m:
            return None, "read-not-in-skills-path", extra
        plugin = m.group("plugin")
        skill = m.group("skill")
        rest = m.group("rest")
        if rest.lower().endswith("skill.md"):
            return {
                "event_type": "skill_invocation",
                "skill_name": skill,
                "plugin_name": plugin,
            }, None, extra
        return {
            "event_type": "reference_file_read",
            "skill_name": skill,
            "plugin_name": plugin,
            "query_summary": "read:reference-file",
        }, None, extra

    # 4. Bash with aliyun CLI
    if tool_name == "Bash":
        cmd = ""
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "") or ""
        if not isinstance(cmd, str) or not re.match(r"^\s*aliyun(\s|$)", cmd):
            head_token = ""
            if isinstance(cmd, str) and cmd.strip():
                head_token = cmd.strip().split()[0]
                # Sanitize: keep alnum, dash, underscore, dot only; cap at 32 chars.
                head_token = re.sub(r"[^A-Za-z0-9._-]", "_", head_token)[:32]
            extra["cmd_head"] = head_token
            return None, "bash-not-aliyun", extra
        return {
            "event_type": "cli_command_use",
            "cli_command": sanitize.sanitize_cli(cmd),
        }, None, extra

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
        return seed, None, extra

    return None, "unknown-tool", extra


def classify(tool_name: str, tool_input: Any) -> Optional[dict]:
    """Backwards-compatible wrapper around :func:`classify_with_reason`."""
    seed, _, _ = classify_with_reason(tool_name, tool_input)
    return seed


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


def extract_request_id(tool_result: Any) -> str:
    """Return RequestId / PopRequestId or empty string. Bounded JSON parse."""
    obj = None
    if isinstance(tool_result, dict):
        obj = tool_result
    elif isinstance(tool_result, str) and tool_result:
        try:
            obj = json.loads(tool_result[:JSON_PARSE_WINDOW])
        except Exception:
            obj = None
    if not isinstance(obj, dict):
        return ""

    candidate_keys_pri = ("RequestId", "requestId", "request_id")
    candidate_keys_sec = ("PopRequestId", "popRequestId", "pop_request_id")

    def look(d: dict, keys) -> str:
        for k in keys:
            v = d.get(k)
            if isinstance(v, str) and v:
                return v
            if isinstance(v, (int, float)):
                return str(v)
        return ""

    for keys in (candidate_keys_pri, candidate_keys_sec):
        v = look(obj, keys)
        if v:
            return v
        nested = obj.get("data")
        if isinstance(nested, dict):
            v = look(nested, keys)
            if v:
                return v
        body = obj.get("body")
        if isinstance(body, dict):
            v = look(body, keys)
            if v:
                return v
        # Aliyun MCP CallCLI failure shape: {"isError":true,"error":{"RequestId":"..."}}
        err = obj.get("error")
        if isinstance(err, dict):
            v = look(err, keys)
            if v:
                return v
    return ""


ALIYUN_ERROR_CODES_RE = re.compile(
    r"\b(InvalidParameter|NoPermission|Forbidden|AccessDenied|"
    r"InvalidAccessKey[A-Za-z]*|Unauthorized|RequestTimeout|"
    r"ServiceUnavailable|InternalError|Throttling|QuotaExceeded)\b"
)
CLIENT_ERROR_RE = re.compile(
    r"(Connection refused|EOF\b|\btimeout\b|failed to|unreachable|"
    r"connection reset|no route to host)",
    re.IGNORECASE,
)


def _scan_dict_for_error(d: dict) -> Optional[str]:
    if not isinstance(d, dict):
        return None
    if d.get("isError") is True:
        msg = d.get("error") or d.get("message") or "isError=true"
        if isinstance(msg, dict):
            return msg.get("Message") or msg.get("message") or "isError=true"
        return str(msg)
    if d.get("Code") or d.get("error") or d.get("Error"):
        return (
            d.get("Message")
            or d.get("message")
            or (d.get("error") if isinstance(d.get("error"), str) else "")
            or str(d.get("Code") or d.get("Error") or "")
        )
    status = d.get("status")
    if isinstance(status, str) and status.lower() in ("errored", "error", "failed", "failure"):
        return d.get("Message") or d.get("message") or f"status: {status}"
    return None


def detect_status(data: dict) -> tuple[str, str]:
    """Return ("success" | "failure", error_message_sanitized_or_empty)."""
    tool_response = data.get("tool_response") or {}
    tool_error = data.get("tool_error") or data.get("error") or ""
    tool_result = data.get("tool_result", "")
    if not tool_result and isinstance(tool_response, dict):
        tool_result = tool_response.get("stdout", "") or ""

    def _result_message(plain_fallback: bool = False) -> str:
        """Extract the most informative error message from tool_result.

        When ``plain_fallback`` is True (only set by callers that have already
        independently determined the call failed — e.g. Signal 1's
        ``is_error=true`` / ``status="Errored"`` branches), a non-empty
        plain-text ``tool_result`` that did not match the JSON / Aliyun /
        client-error branches falls back to its first non-empty line. This
        lets free-text error strings surface as the error message instead of
        the generic sentinel. ``plain_fallback`` is intentionally False for
        Signal 4 so that successful tool calls with plain-text output are not
        misclassified as failures.
        """
        if isinstance(tool_result, dict):
            return _scan_dict_for_error(tool_result) or ""
        if isinstance(tool_result, str) and tool_result:
            head = tool_result[:JSON_PARSE_WINDOW]
            try:
                parsed = json.loads(head)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                m = _scan_dict_for_error(parsed)
                if m:
                    return m
                if ALIYUN_ERROR_CODES_RE.search(head[:ERROR_REGEX_WINDOW]):
                    return head.split("\n", 1)[0]
            elif CLIENT_ERROR_RE.search(tool_result[:ERROR_REGEX_WINDOW]):
                return tool_result.split("\n", 1)[0]
            if plain_fallback:
                for line in tool_result.split("\n"):
                    line = line.strip()
                    if line:
                        return line
        return ""

    # Signal 1: tool_response.is_error / status
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") is True:
            msg = (
                _result_message(plain_fallback=True)
                or tool_response.get("error")
                or tool_response.get("stderr")
                or "tool_response.is_error=true"
            )
            return "failure", sanitize.sanitize_error(msg)
        if str(tool_response.get("status", "")).lower() == "errored":
            msg = (
                _result_message(plain_fallback=True)
                or "tool_response.status=Errored"
            )
            return "failure", sanitize.sanitize_error(msg)

    # Signal 2: top-level tool_error / error
    if tool_error:
        return "failure", sanitize.sanitize_error(tool_error)

    # Signal 3: Bash exit_code != 0
    if isinstance(tool_response, dict):
        ec = tool_response.get("exit_code")
        if isinstance(ec, int) and ec != 0:
            stderr = tool_response.get("stderr") or ""
            stdout = tool_response.get("stdout") or ""
            return "failure", sanitize.sanitize_error(stderr or stdout or f"exit_code={ec}")

    # Signal 4: parse tool_result (bounded)
    msg = _result_message()
    if msg:
        return "failure", sanitize.sanitize_error(msg)

    return "success", ""


def _debug_enabled() -> bool:
    return os.environ.get("ALIBABACLOUD_TELEMETRY_DEBUG") == "1"


def _debug(msg: str) -> None:
    if _debug_enabled():
        try:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
        except Exception:
            pass


def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        _debug("[post] decision=reject reason=opted-out")
        return 1
    raw = sys.stdin.buffer.read(STDIN_CAP)
    if not raw:
        _debug("[post] decision=reject reason=empty-stdin")
        return 1
    try:
        text = raw.decode("utf-8", errors="replace")
        data = json.loads(text)
    except Exception:
        _debug("[post] decision=reject reason=invalid-json")
        return 1

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    session_id = data.get("session_id") or ""
    hook_event_name = data.get("hook_event_name") or ""

    _debug(f"[post] event_name={hook_event_name or '<none>'} tool={tool_name or '<none>'}")

    seed, reject_reason, extra = classify_with_reason(tool_name, tool_input)
    if seed is None:
        suffix = ""
        if extra.get("cmd_head"):
            suffix = f" cmd_head={extra['cmd_head']}"
        _debug(
            f"[post] event_name={hook_event_name or '<none>'} "
            f"tool={tool_name or '<none>'} decision=reject reason={reject_reason}"
            f"{suffix}"
        )
        return 1

    sd = state_dir()
    start_ms = read_start_ts(sd, session_id, tool_name)
    end_ms = int(time.time() * 1000)
    fallback_used = start_ms is None
    if fallback_used:
        start_ms = end_ms - 1
    turn = read_turn(sd)

    status, error_message = detect_status(data)

    # Override: PostToolUseFailure always implies failure status, even if
    # the 4-signal heuristics couldn't surface a specific error message.
    if hook_event_name == "PostToolUseFailure":
        if status != "failure":
            status = "failure"
            if not error_message:
                error_message = sanitize.sanitize_error("PostToolUseFailure event")

    tool_result = data.get("tool_result", "")
    tool_response = data.get("tool_response") or {}
    if not tool_result and isinstance(tool_response, dict):
        tool_result = tool_response.get("stdout", "") or ""

    request_id = extract_request_id(tool_result)

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
        "tool-request-id": request_id,
        "cli-command": seed.get("cli_command", ""),
        "query-summary": seed.get("query_summary", ""),
        "error-message": error_message,
    }
    if fallback_used and not args.get("query-summary"):
        args["query-summary"] = "start-fallback"
    emit(args)

    _debug(
        f"[post] event_name={hook_event_name or '<none>'} "
        f"tool={tool_name or '<none>'} decision=upload "
        f"event={seed.get('event_type', '')} status={status}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
