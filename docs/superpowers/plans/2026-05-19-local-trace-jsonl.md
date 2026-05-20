# Local Audit Trace (JSONL) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a comprehensive local JSONL trace log that records all Alibaba Cloud tool interactions (prompts, inputs, responses, errors) per-session for user self-audit.

**Architecture:** A single new module `trace_writer.py` handles all trace I/O (file append, sanitization, truncation). Existing handlers (`pre_handler.py`, `post_handler.py`, `prompt_handler.py`, `stop_handler.py`) each gain a few lines to write trace events. Prompts are deferred and backfilled at Stop only if the turn involved alibabacloud tools — this avoids noise from non-alibabacloud turns while ensuring complete audit trails.

**Tech Stack:** Python 3.8+, JSONL (one JSON object per line), `os.open` with `O_APPEND` for atomic writes, `uuid` for span IDs.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `tools/hooks/scripts/lib/trace_writer.py` | **Create** | Core trace module: enabled check, dir resolution, append, sanitize, truncate |
| `tools/hooks/scripts/lib/prompt_handler.py` | Modify | Store prompt + span_id in session state for later backfill |
| `tools/hooks/scripts/lib/pre_handler.py` | Modify | Write `tool_start` event, mark turn as having trace activity |
| `tools/hooks/scripts/lib/post_handler.py` | Modify | Write `tool_end` event with full response |
| `tools/hooks/scripts/lib/stop_handler.py` | Modify | Backfill prompt, write `turn_end`, reset state |
| `tools/hooks/scripts/test-trace.sh` | **Create** | Integration test harness for trace feature |
| `tools/hooks/scripts/test-fixtures/trace/` | **Create** | Fixture directory for trace tests |

---

### Task 1: Create `trace_writer.py` — Core Module

**Files:**
- Create: `tools/hooks/scripts/lib/trace_writer.py`

- [ ] **Step 1: Create trace_writer.py with all functions**

```python
#!/usr/bin/env python3
"""Local audit trace writer.

Appends JSONL records to per-session trace files for user self-audit.
Default ON — set ALIBABACLOUD_TRACE=false to disable.
Never uploaded. Never auto-cleaned. User owns their data.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from state import client_dir  # noqa: E402

TRACE_MAX_BYTES = 65536  # 64KB response cap

# --- Light sanitization patterns (local data, minimal masking) ---

_TRACE_SANITIZE_PATTERNS = [
    # Alibaba Cloud AccessKey IDs
    (re.compile(r"\bLTAI[A-Za-z0-9]{8,30}\b"), "***"),
    # STS tokens
    (re.compile(r"\bSTS\.[A-Za-z0-9+/=]{10,}"), "***"),
    # JWT tokens
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"), "***"),
    # PEM private key blocks
    (re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----[\s\S]*?-----END[^-]*PRIVATE KEY-----"), "***"),
    # key=value credential patterns
    (re.compile(r"(?i)\b(accesskeysecret|accesskey_secret|secret_access_key)\s*[=:]\s*\S+"), r"\1=***"),
    # CN mobile
    (re.compile(r"\b1[3-9]\d{9}\b"), "***"),
    # Email
    (re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "***"),
]


def trace_enabled() -> bool:
    """Return True unless ALIBABACLOUD_TRACE is explicitly 'false'."""
    return os.environ.get("ALIBABACLOUD_TRACE", "").lower() != "false"


def trace_dir(client: str) -> str:
    """Return trace directory path, creating it if needed.

    Priority: ALIBABACLOUD_TRACE_DIR env > <client_dir>/traces/
    """
    override = os.environ.get("ALIBABACLOUD_TRACE_DIR", "").strip()
    if override:
        try:
            os.makedirs(override, mode=0o700, exist_ok=True)
            return override
        except OSError:
            return ""
    cd = client_dir(client)
    if not cd:
        return ""
    traces = os.path.join(cd, "traces")
    try:
        os.makedirs(traces, mode=0o700, exist_ok=True)
        return traces
    except OSError:
        return ""


def _iso_from_ms(ms: int) -> str:
    """Convert epoch milliseconds to ISO 8601 string with ms precision."""
    secs = ms / 1000.0
    t = time.gmtime(secs)
    millis = int(ms % 1000)
    return time.strftime("%Y-%m-%dT%H:%M:%S", t) + f".{millis:03d}Z"


def sanitize_trace_value(value: Any) -> Any:
    """Recursively sanitize strings in dicts/lists. Light patterns only."""
    if isinstance(value, str):
        s = value
        for pat, repl in _TRACE_SANITIZE_PATTERNS:
            s = pat.sub(repl, s)
        return s
    if isinstance(value, dict):
        return {k: sanitize_trace_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_trace_value(item) for item in value]
    return value


def truncate_response(obj: Any, max_bytes: int = TRACE_MAX_BYTES) -> Tuple[Any, bool]:
    """Serialize obj to JSON; if > max_bytes, truncate and return marker.

    Returns (obj_or_truncated_string, was_truncated).
    """
    if obj is None:
        return None, False
    try:
        serialized = json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        serialized = str(obj)
    if len(serialized.encode("utf-8")) <= max_bytes:
        return obj, False
    # Truncate: return raw string capped at max_bytes
    truncated = serialized.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
    return truncated, True


def append_trace(client: str, session_id: str, record: dict) -> None:
    """Append one JSONL record to the session trace file.

    Uses O_APPEND for atomic writes. Best-effort — never raises.
    """
    td = trace_dir(client)
    if not td:
        return
    # Safe filename
    safe_session = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")[:120]
    filepath = os.path.join(td, f"{safe_session}.jsonl")

    # Fill timestamps if not provided
    now_ms = int(time.time() * 1000)
    if "start_timestamp" not in record:
        record["start_timestamp"] = _iso_from_ms(now_ms)
    elif isinstance(record["start_timestamp"], int):
        record["start_timestamp"] = _iso_from_ms(record["start_timestamp"])
    if "end_timestamp" not in record:
        record["end_timestamp"] = record["start_timestamp"]
    elif isinstance(record["end_timestamp"], int):
        record["end_timestamp"] = _iso_from_ms(record["end_timestamp"])

    # Fill common fields
    record.setdefault("session_id", session_id)
    record.setdefault("client", client)

    try:
        line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
        fd = os.open(filepath, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        pass
```

- [ ] **Step 2: Verify module imports cleanly**

Run:
```bash
cd tools/hooks/scripts/lib && python3 -c "import trace_writer; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/lib/trace_writer.py
git commit -m "feat(trace): add trace_writer.py core module for local JSONL audit"
```

---

### Task 2: Modify `prompt_handler.py` — Store Prompt for Backfill

**Files:**
- Modify: `tools/hooks/scripts/lib/prompt_handler.py`

The prompt handler currently only fires telemetry for slash-style skill invocations. We need it to ALSO store every prompt in session state (with span_id and timestamp) so the stop handler can backfill it into the trace if the turn uses alibabacloud tools.

- [ ] **Step 1: Add trace import and prompt storage logic**

Add at the top of `prompt_handler.py`, after the existing imports:

```python
import trace_writer  # noqa: E402
import uuid  # for span_id generation
```

Then in `main()`, add the trace storage block AFTER reading `prompt`, `session_id`, and `client` (around line 100, before the `seed = _classify_prompt(prompt)` line). The key point: this runs for ALL prompts regardless of whether they match a slash-skill — storage is unconditional, actual trace write is deferred to stop_handler.

```python
    # --- Local trace: store prompt for potential backfill at Stop ---
    if trace_writer.trace_enabled() and session_id and prompt:
        try:
            with SessionState(client, session_id) as st:
                st.data["pending_prompt"] = prompt
                st.data["pending_prompt_ts"] = int(time.time() * 1000)
                st.data["prompt_span_id"] = uuid.uuid4().hex[:16]
        except Exception:
            pass
```

The full modified `main()` function becomes:

```python
def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        _debug("[prompt] decision=opted-out")
        return 1
    raw = sys.stdin.buffer.read(STDIN_CAP)
    if not raw:
        _debug("[prompt] decision=skip reason=empty-stdin")
        return 1
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception:
        _debug("[prompt] decision=skip reason=invalid-json")
        return 1
    prompt = data.get("prompt") or ""
    session_id = data.get("session_id") or ""
    if not session_id:
        _debug("[prompt] decision=skip reason=empty-session-id")
        return 1

    client = _detect_client(text)

    # --- Local trace: store prompt for potential backfill at Stop ---
    if trace_writer.trace_enabled() and session_id and prompt:
        try:
            with SessionState(client, session_id) as st:
                st.data["pending_prompt"] = prompt
                st.data["pending_prompt_ts"] = int(time.time() * 1000)
                st.data["prompt_span_id"] = uuid.uuid4().hex[:16]
        except Exception:
            pass

    seed = _classify_prompt(prompt)
    if seed is None:
        _debug("[prompt] decision=skip reason=not-slash-skill")
        return 1

    # Read turn (read-only — Stop hook owns increments)
    turn = 0
    try:
        with SessionState(client, session_id) as st:
            turn = int(st.data.get("turn", 0))
    except Exception:
        pass

    now = _iso_now()
    tool_name = f"skill_{seed['skill_name']}"
    args = {
        "client-name": client,
        "event-type": "skill_invocation",
        "start-timestamp": now,
        "end-timestamp": now,
        "tool-name": tool_name,
        "session-id": session_id,
        "status": "success",
        "turn": str(turn),
        "skill-name": seed["skill_name"],
        "plugin-name": seed["plugin_name"],
    }
    _emit(args)

    _debug(
        f"[prompt] tool={tool_name} decision=upload "
        f"event=skill_invocation skill={seed['skill_name']} "
        f"plugin={seed['plugin_name']} session={session_id} client={client}"
    )
    return 0
```

- [ ] **Step 2: Verify existing dry-run tests still pass**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all
```
Expected: All existing tests PASS (prompt handler change doesn't affect telemetry output).

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/lib/prompt_handler.py
git commit -m "feat(trace): store prompt + span_id in session state for backfill"
```

---

### Task 3: Modify `pre_handler.py` — Write `tool_start` Trace Event

**Files:**
- Modify: `tools/hooks/scripts/lib/pre_handler.py`

- [ ] **Step 1: Add trace import and tool_start write**

Add import at the top (after the existing `from state import SessionState` line):

```python
import trace_writer  # noqa: E402
```

Then in `main()`, AFTER the existing `SessionState` block that writes `tool_starts[key]` (around line 136-138), add the trace write. The modified section of `main()`:

```python
    client = _detect_client(text)
    key = tool_use_id or _sanitize_tool_name(tool_name)
    try:
        with SessionState(client, session_id) as st:
            st.data["tool_starts"][key] = int(time.time() * 1000)
            # --- Local trace: mark turn active, get parent span ---
            if trace_writer.trace_enabled():
                st.data["turn_has_trace"] = True
                parent_span = st.data.get("prompt_span_id")
                turn = int(st.data.get("turn", 0))
    except Exception:
        parent_span = None
        turn = 0

    # --- Local trace: write tool_start event ---
    if trace_writer.trace_enabled() and session_id:
        try:
            now_ms = int(time.time() * 1000)
            trace_writer.append_trace(client, session_id, {
                "event": "tool_start",
                "span_id": tool_use_id or key,
                "parent_span_id": parent_span,
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "tool_input": trace_writer.sanitize_trace_value(tool_input),
                "turn": turn,
                "start_timestamp": now_ms,
                "end_timestamp": now_ms,
            })
        except Exception:
            pass

    detail = _detail(tool_name, tool_input)
    suffix = (" " + detail) if detail else ""
    _debug(
        f"[pre] tool={tool_name}{suffix} decision=track session={session_id or '<none>'}"
    )
    return 0
```

- [ ] **Step 2: Verify existing dry-run tests still pass**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all
```
Expected: All existing tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/lib/pre_handler.py
git commit -m "feat(trace): write tool_start event in pre_handler"
```

---

### Task 4: Modify `post_handler.py` — Write `tool_end` Trace Event

**Files:**
- Modify: `tools/hooks/scripts/lib/post_handler.py`

- [ ] **Step 1: Add trace import and tool_end write**

Add import at top (after existing `from state import SessionState` line):

```python
import trace_writer  # noqa: E402
```

Then in `main()`, AFTER the `emit(args)` call (line 608) and BEFORE the final `_debug(...)` call, add:

```python
    # --- Local trace: write tool_end event with full response ---
    if trace_writer.trace_enabled() and session_id:
        try:
            # Get parent span from state
            parent_span = None
            try:
                with SessionState(client, session_id) as st:
                    parent_span = st.data.get("prompt_span_id")
            except Exception:
                pass
            # Prepare response data
            trace_response = tool_response if isinstance(tool_response, (dict, list)) else tool_result
            response_data, was_truncated = trace_writer.truncate_response(trace_response)
            trace_writer.append_trace(client, session_id, {
                "event": "tool_end",
                "span_id": tool_use_id or marker_key,
                "parent_span_id": parent_span,
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "status": status,
                "error_message": error_message or None,
                "request_id": request_id or None,
                "duration_ms": end_ms - start_ms,
                "tool_response": trace_writer.sanitize_trace_value(response_data),
                "truncated": was_truncated,
                "turn": turn,
                "start_timestamp": start_ms,
                "end_timestamp": end_ms,
            })
        except Exception:
            pass
```

- [ ] **Step 2: Verify existing dry-run tests still pass**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all
```
Expected: All existing tests PASS (trace writes to a separate file, don't affect stdout output).

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/lib/post_handler.py
git commit -m "feat(trace): write tool_end event with full response in post_handler"
```

---

### Task 5: Modify `stop_handler.py` — Backfill Prompt + Write `turn_end`

**Files:**
- Modify: `tools/hooks/scripts/lib/stop_handler.py`

This is the most complex change. At Stop, if `turn_has_trace` is True (meaning alibabacloud tools were used this turn), we:
1. Backfill the prompt as a root span (start_timestamp=prompt time, end_timestamp=now)
2. Write a `turn_end` event
3. Reset trace state keys for next turn

- [ ] **Step 1: Add trace import and backfill logic**

Add import after existing imports:

```python
import trace_writer  # noqa: E402
```

Replace the existing `main()` function with:

```python
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
        _debug("[stop] decision=skip reason=no-session-id")
        return 0
    client = _detect_client(text)
    hook_event_name = data.get("hook_event_name") or "Stop"

    new_turn = 0
    try:
        with SessionState(client, session_id) as st:
            # --- Local trace: backfill prompt and write turn_end ---
            if trace_writer.trace_enabled():
                turn_has_trace = st.data.get("turn_has_trace", False)
                if turn_has_trace:
                    prompt_span = st.data.get("prompt_span_id")
                    pending = st.data.get("pending_prompt")
                    prompt_ts = st.data.get("pending_prompt_ts")
                    stop_ts = int(time.time() * 1000)
                    current_turn = int(st.data.get("turn", 0))
                    # Backfill prompt as root span
                    if pending:
                        trace_writer.append_trace(client, session_id, {
                            "event": "prompt",
                            "span_id": prompt_span,
                            "parent_span_id": None,
                            "prompt": trace_writer.sanitize_trace_value(pending),
                            "turn": current_turn,
                            "start_timestamp": prompt_ts,
                            "end_timestamp": stop_ts,
                        })
                    # Write turn_end (root span close)
                    trace_writer.append_trace(client, session_id, {
                        "event": "turn_end",
                        "span_id": prompt_span,
                        "parent_span_id": None,
                        "stop_reason": hook_event_name,
                        "turn": current_turn,
                        "start_timestamp": stop_ts,
                        "end_timestamp": stop_ts,
                    })
                # Reset trace state for next turn
                st.data.pop("turn_has_trace", None)
                st.data.pop("pending_prompt", None)
                st.data.pop("pending_prompt_ts", None)
                st.data.pop("prompt_span_id", None)

            # Increment turn (existing behavior)
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
```

- [ ] **Step 2: Verify existing dry-run tests still pass**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all
```
Expected: All existing tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/lib/stop_handler.py
git commit -m "feat(trace): backfill prompt and write turn_end in stop_handler"
```

---

### Task 6: Integration Test — Full Trace Flow

**Files:**
- Create: `tools/hooks/scripts/test-trace.sh`
- Create: `tools/hooks/scripts/test-fixtures/trace/prompt-basic.json`
- Create: `tools/hooks/scripts/test-fixtures/trace/pre-mcp-call.json`
- Create: `tools/hooks/scripts/test-fixtures/trace/post-mcp-success.json`
- Create: `tools/hooks/scripts/test-fixtures/trace/stop-basic.json`

- [ ] **Step 1: Create test fixture files**

`tools/hooks/scripts/test-fixtures/trace/prompt-basic.json`:
```json
{
  "session_id": "trace-test-session",
  "prompt": "帮我查看ECS实例列表",
  "hook_event_name": "UserPromptSubmit"
}
```

`tools/hooks/scripts/test-fixtures/trace/pre-mcp-call.json`:
```json
{
  "session_id": "trace-test-session",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_use_id": "toolu_test_001",
  "tool_input": {
    "command": "aliyun ecs DescribeInstances --region cn-hangzhou"
  },
  "hook_event_name": "PreToolUse"
}
```

`tools/hooks/scripts/test-fixtures/trace/post-mcp-success.json`:
```json
{
  "session_id": "trace-test-session",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_use_id": "toolu_test_001",
  "tool_input": {
    "command": "aliyun ecs DescribeInstances --region cn-hangzhou"
  },
  "tool_response": [
    {
      "type": "text",
      "text": "{\"RequestId\": \"A09A8DD7-1234-5678-9ABC-DEF012345678\", \"Instances\": {\"Instance\": [{\"InstanceId\": \"i-bp1abc123\", \"Status\": \"Running\"}]}}"
    }
  ],
  "hook_event_name": "PostToolUse"
}
```

`tools/hooks/scripts/test-fixtures/trace/stop-basic.json`:
```json
{
  "session_id": "trace-test-session",
  "hook_event_name": "Stop"
}
```

- [ ] **Step 2: Create test-trace.sh integration test**

```bash
#!/bin/bash
# Integration test for local JSONL trace feature.
# Simulates a full turn: prompt → pre (tool_start) → post (tool_end) → stop (backfill + turn_end)
# Verifies the trace JSONL file contains all expected events with correct span hierarchy.

set -e

scriptDir="$(cd "$(dirname "$0")" && pwd)"
fixturesDir="$scriptDir/test-fixtures/trace"

# Isolated state + trace dir
stateDir="$(mktemp -d)"
traceDir="$(mktemp -d)"
trap 'rm -rf "$stateDir" "$traceDir"' EXIT

export ALIBABACLOUD_TELEMETRY_STATE_DIR="$stateDir"
export ALIBABACLOUD_TRACE_DIR="$traceDir"
export ALIBABACLOUD_TELEMETRY="true"
export ALIBABACLOUD_TRACE="true"

echo "=== Test: Full trace flow ==="

# 1. Prompt (stores prompt in state, no trace yet)
python3 "$scriptDir/lib/prompt_handler.py" < "$fixturesDir/prompt-basic.json" > /dev/null 2>&1 || true

# 2. Pre (writes tool_start, marks turn_has_trace)
python3 "$scriptDir/lib/pre_handler.py" < "$fixturesDir/pre-mcp-call.json" > /dev/null 2>&1 || true

# 3. Post (writes tool_end with response)
# Need to seed start marker first
python3 "$scriptDir/lib/state.py" seed-marker \
    --client claude-code \
    --session trace-test-session \
    --key toolu_test_001 \
    --ms 1716100000000

python3 "$scriptDir/lib/post_handler.py" < "$fixturesDir/post-mcp-success.json" > /dev/null 2>&1 || true

# 4. Stop (backfills prompt, writes turn_end)
python3 "$scriptDir/lib/stop_handler.py" < "$fixturesDir/stop-basic.json" > /dev/null 2>&1 || true

# Verify trace file exists
traceFile="$traceDir/trace-test-session.jsonl"
if [ ! -f "$traceFile" ]; then
    echo "FAIL: trace file not created at $traceFile"
    echo "Contents of trace dir:"
    ls -la "$traceDir"
    exit 1
fi

# Verify event count (expect: tool_start + tool_end + prompt + turn_end = 4)
lineCount=$(wc -l < "$traceFile" | tr -d ' ')
if [ "$lineCount" -ne 4 ]; then
    echo "FAIL: expected 4 trace events, got $lineCount"
    cat "$traceFile"
    exit 1
fi

# Verify each event type exists
for event in "tool_start" "tool_end" "prompt" "turn_end"; do
    if ! grep -q "\"event\": \"$event\"" "$traceFile" && ! grep -q "\"event\":\"$event\"" "$traceFile"; then
        echo "FAIL: missing event type '$event'"
        cat "$traceFile"
        exit 1
    fi
done

# Verify span hierarchy: tool events have parent_span_id matching prompt's span_id
promptSpan=$(python3 -c "
import json
for line in open('$traceFile'):
    r = json.loads(line)
    if r['event'] == 'prompt':
        print(r['span_id'])
        break
")
toolParent=$(python3 -c "
import json
for line in open('$traceFile'):
    r = json.loads(line)
    if r['event'] == 'tool_start':
        print(r.get('parent_span_id', ''))
        break
")
if [ "$promptSpan" != "$toolParent" ]; then
    echo "FAIL: span hierarchy broken. prompt span_id=$promptSpan, tool parent_span_id=$toolParent"
    cat "$traceFile"
    exit 1
fi

echo "PASS: Full trace flow"

echo ""
echo "=== Test: Trace disabled ==="

export ALIBABACLOUD_TRACE="false"
traceDir2="$(mktemp -d)"
export ALIBABACLOUD_TRACE_DIR="$traceDir2"

python3 "$scriptDir/lib/prompt_handler.py" < "$fixturesDir/prompt-basic.json" > /dev/null 2>&1 || true
python3 "$scriptDir/lib/pre_handler.py" < "$fixturesDir/pre-mcp-call.json" > /dev/null 2>&1 || true
python3 "$scriptDir/lib/stop_handler.py" < "$fixturesDir/stop-basic.json" > /dev/null 2>&1 || true

if [ -f "$traceDir2/trace-test-session.jsonl" ]; then
    echo "FAIL: trace file created when ALIBABACLOUD_TRACE=false"
    exit 1
fi
echo "PASS: Trace disabled"
rm -rf "$traceDir2"

echo ""
echo "=== Test: Non-alibabacloud turn produces no trace ==="

export ALIBABACLOUD_TRACE="true"
traceDir3="$(mktemp -d)"
export ALIBABACLOUD_TRACE_DIR="$traceDir3"

# Only prompt + stop (no alibabacloud tool call in between)
python3 "$scriptDir/lib/prompt_handler.py" < "$fixturesDir/prompt-basic.json" > /dev/null 2>&1 || true
python3 "$scriptDir/lib/stop_handler.py" < "$fixturesDir/stop-basic.json" > /dev/null 2>&1 || true

if [ -f "$traceDir3/trace-test-session.jsonl" ]; then
    echo "FAIL: trace file created for non-alibabacloud turn"
    exit 1
fi
echo "PASS: Non-alibabacloud turn produces no trace"
rm -rf "$traceDir3"

echo ""
echo "=== Test: Sanitization ==="

export ALIBABACLOUD_TRACE="true"
traceDir4="$(mktemp -d)"
export ALIBABACLOUD_TRACE_DIR="$traceDir4"

# Prompt with sensitive data
echo '{"session_id":"trace-sanitize","prompt":"用LTAI4GHqKagPvM2abc123xyz这个key查询ECS","hook_event_name":"UserPromptSubmit"}' | \
    python3 "$scriptDir/lib/prompt_handler.py" > /dev/null 2>&1 || true

# Trigger alibabacloud tool to mark turn
echo '{"session_id":"trace-sanitize","tool_name":"mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI","tool_use_id":"toolu_san_001","tool_input":{"command":"aliyun ecs DescribeInstances"},"hook_event_name":"PreToolUse"}' | \
    python3 "$scriptDir/lib/pre_handler.py" > /dev/null 2>&1 || true

# Stop to trigger backfill
echo '{"session_id":"trace-sanitize","hook_event_name":"Stop"}' | \
    python3 "$scriptDir/lib/stop_handler.py" > /dev/null 2>&1 || true

traceFile4="$traceDir4/trace-sanitize.jsonl"
if grep -q "LTAI4GHqKagPvM2abc123xyz" "$traceFile4" 2>/dev/null; then
    echo "FAIL: AK not sanitized in trace"
    cat "$traceFile4"
    exit 1
fi
if grep -q '"\*\*\*"' "$traceFile4" 2>/dev/null || grep -q '"\\*\\*\\*' "$traceFile4" 2>/dev/null; then
    echo "PASS: Sanitization"
else
    # Check for *** in any form
    if grep -q '\*\*\*' "$traceFile4" 2>/dev/null; then
        echo "PASS: Sanitization"
    else
        echo "FAIL: No sanitization markers found"
        cat "$traceFile4"
        exit 1
    fi
fi
rm -rf "$traceDir4"

echo ""
echo "=== All trace tests passed ==="
```

- [ ] **Step 3: Run the integration tests**

Run:
```bash
cd tools/hooks/scripts && chmod +x test-trace.sh && bash test-trace.sh
```
Expected: All tests PASS.

- [ ] **Step 4: Verify existing telemetry dry-run tests still pass**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all
```
Expected: All PASS (no regression).

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/scripts/test-trace.sh tools/hooks/scripts/test-fixtures/trace/
git commit -m "test(trace): add integration tests for local JSONL trace feature"
```

---

### Task 7: Truncation Test

**Files:**
- Modify: `tools/hooks/scripts/test-trace.sh` (add truncation test case)

- [ ] **Step 1: Add truncation test to test-trace.sh**

Append before the final "All trace tests passed" line:

```bash
echo ""
echo "=== Test: Response truncation >64KB ==="

export ALIBABACLOUD_TRACE="true"
traceDir5="$(mktemp -d)"
export ALIBABACLOUD_TRACE_DIR="$traceDir5"

# Generate a fixture with a huge response (>64KB)
bigResponse=$(python3 -c "print('x' * 100000)")
cat > /tmp/trace-big-response.json <<FIXTURE
{
  "session_id": "trace-truncate",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_use_id": "toolu_big_001",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": [{"type": "text", "text": "$bigResponse"}],
  "hook_event_name": "PostToolUse"
}
FIXTURE

# Prompt + pre + post + stop
echo '{"session_id":"trace-truncate","prompt":"big response test","hook_event_name":"UserPromptSubmit"}' | \
    python3 "$scriptDir/lib/prompt_handler.py" > /dev/null 2>&1 || true
echo '{"session_id":"trace-truncate","tool_name":"mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI","tool_use_id":"toolu_big_001","tool_input":{"command":"aliyun ecs DescribeInstances"},"hook_event_name":"PreToolUse"}' | \
    python3 "$scriptDir/lib/pre_handler.py" > /dev/null 2>&1 || true

# Seed start marker
python3 "$scriptDir/lib/state.py" seed-marker --client claude-code --session trace-truncate --key toolu_big_001 --ms 1716100000000

python3 "$scriptDir/lib/post_handler.py" < /tmp/trace-big-response.json > /dev/null 2>&1 || true
echo '{"session_id":"trace-truncate","hook_event_name":"Stop"}' | \
    python3 "$scriptDir/lib/stop_handler.py" > /dev/null 2>&1 || true

traceFile5="$traceDir5/trace-truncate.jsonl"
if ! grep -q '"truncated": true' "$traceFile5" 2>/dev/null && ! grep -q '"truncated":true' "$traceFile5" 2>/dev/null; then
    echo "FAIL: truncated flag not set for >64KB response"
    # Show tool_end event
    python3 -c "
import json
for line in open('$traceFile5'):
    r = json.loads(line)
    if r['event'] == 'tool_end':
        print(json.dumps({k:v for k,v in r.items() if k != 'tool_response'}, indent=2))
        print(f'response length: {len(json.dumps(r.get(\"tool_response\", \"\")))}')
" 2>/dev/null || cat "$traceFile5"
    exit 1
fi
echo "PASS: Response truncation >64KB"
rm -rf "$traceDir5"
rm -f /tmp/trace-big-response.json
```

- [ ] **Step 2: Run updated tests**

Run:
```bash
cd tools/hooks/scripts && bash test-trace.sh
```
Expected: All PASS including truncation test.

- [ ] **Step 3: Commit**

```bash
git add tools/hooks/scripts/test-trace.sh
git commit -m "test(trace): add truncation test for >64KB responses"
```

---

### Task 8: Final Verification — End-to-End

- [ ] **Step 1: Run all tests together**

Run:
```bash
cd tools/hooks/scripts && bash dry-run.sh --all && echo "---" && bash test-trace.sh
```
Expected: All telemetry dry-run tests PASS + all trace tests PASS.

- [ ] **Step 2: Manual smoke test with real data shape**

Run:
```bash
cd tools/hooks/scripts
export ALIBABACLOUD_TRACE_DIR="/tmp/trace-smoke"
export ALIBABACLOUD_TELEMETRY_STATE_DIR="/tmp/trace-smoke-state"
mkdir -p "$ALIBABACLOUD_TRACE_DIR"

# Simulate: prompt → pre → post(success) → stop
echo '{"session_id":"smoke-1","prompt":"list my ECS instances in cn-hangzhou","hook_event_name":"UserPromptSubmit"}' | python3 lib/prompt_handler.py > /dev/null 2>&1 || true

echo '{"session_id":"smoke-1","tool_name":"mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI","tool_use_id":"toolu_smoke_01","tool_input":{"command":"aliyun ecs DescribeInstances --region cn-hangzhou"},"hook_event_name":"PreToolUse"}' | python3 lib/pre_handler.py > /dev/null 2>&1 || true

python3 lib/state.py seed-marker --client claude-code --session smoke-1 --key toolu_smoke_01 --ms $(python3 -c "import time; print(int(time.time()*1000) - 1500)")

echo '{"session_id":"smoke-1","tool_name":"mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI","tool_use_id":"toolu_smoke_01","tool_input":{"command":"aliyun ecs DescribeInstances --region cn-hangzhou"},"tool_response":[{"type":"text","text":"{\"RequestId\":\"DEADBEEF-1234-5678-9ABC-DEF012345678\",\"Instances\":{\"Instance\":[{\"InstanceId\":\"i-bp1xyz\",\"Status\":\"Running\"}]}}"}],"hook_event_name":"PostToolUse"}' | python3 lib/post_handler.py > /dev/null 2>&1 || true

echo '{"session_id":"smoke-1","hook_event_name":"Stop"}' | python3 lib/stop_handler.py > /dev/null 2>&1 || true

echo "--- Trace output ---"
cat /tmp/trace-smoke/smoke-1.jsonl | python3 -m json.tool --no-ensure-ascii 2>/dev/null || cat /tmp/trace-smoke/smoke-1.jsonl
rm -rf /tmp/trace-smoke /tmp/trace-smoke-state
```

Expected: 4 JSONL lines with correct span hierarchy, timestamps, and request_id.

- [ ] **Step 3: Commit all (if any remaining unstaged changes)**

Run:
```bash
git status
```

If clean, done. Otherwise stage and commit remaining changes.
