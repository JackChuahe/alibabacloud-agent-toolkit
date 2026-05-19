#!/usr/bin/env python3
"""Stop / StopFailure hook handler. Increments per-session turn counter."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from state import SessionState, cleanup_stale_sessions  # noqa: E402

DEBUG = os.environ.get("ALIBABACLOUD_TELEMETRY_DEBUG") == "1"


def _detect_client(payload_str: str) -> str:
    if os.environ.get("COPILOT_CLI") == "1":
        return "copilot-cli"
    if os.environ.get("CODEX_CLI") == "1":
        return "codex"
    if os.environ.get("QODER_WORK") == "1":
        return "qoderwork"
    if "__vscode" in payload_str:
        return "vscode"
    return "claude-code"


def _debug(msg: str) -> None:
    if DEBUG:
        try:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
        except Exception:
            pass


def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        _debug("[stop] decision=skip reason=opted-out")
        return 0
    raw = sys.stdin.buffer.read(65536)
    if not raw:
        _debug("[stop] decision=skip reason=empty-stdin")
        return 0
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception:
        data = {}
    session_id = data.get("session_id") or ""
    if not session_id:
        # No session_id → can't track turn
        _debug("[stop] decision=skip reason=no-session-id")
        return 0
    client = _detect_client(text)
    new_turn = 0
    try:
        with SessionState(client, session_id) as st:
            st.data["turn"] = int(st.data.get("turn", 0)) + 1
            new_turn = st.data["turn"]
    except Exception:
        pass
    _debug(f"[stop] turn={new_turn} session={session_id} client={client}")
    # Opportunistic cleanup (cheap)
    try:
        cleanup_stale_sessions(client)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
