# Local Audit Trace (JSONL) — Design Spec

## Overview

A local-only, comprehensive JSONL trace log recording all Alibaba Cloud tool interactions for user self-audit. Records prompts, tool inputs, full responses, and errors per-session. Never uploaded — local data only.

## User Story

As a user of Alibaba Cloud agent plugins, I want a complete local trace of all interactions so I can audit the process, verify correctness, and investigate anomalies after a session.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Activation | Default ON, `ALIBABACLOUD_TRACE=false` to disable | Zero-config audit trail |
| Directory | `ALIBABACLOUD_TRACE_DIR` override, else `<state-root>/<client>/traces/` | Follows existing telemetry dir pattern |
| File org | Per-session: `<session-id>.jsonl` | Easy to audit one conversation |
| Response cap | Truncate at 64KB, mark `truncated: true` | Balance completeness vs disk |
| Cleanup | Never auto-clean | User manages their own data |
| Sanitization | Light: AK/SK, STS, JWT, PEM, phone, email | Local data but still protect obvious secrets |
| Prompt capture | Deferred to Stop event; backfilled only if turn used alibabacloud tools | Avoids noise from non-alibabacloud turns |

## JSONL Record Schema

Each line is a self-contained JSON object. Events form a **parent-child span hierarchy** within each turn: the `prompt` event is the root span, and all `tool_start`/`tool_end` events are child spans nested under it.

### Span Hierarchy

```
span_id=<prompt_span> [prompt] "帮我查看ECS实例"  10:00:00 → 10:00:05
  ├─ span_id=toolu_01 [tool_start/tool_end] CallCLI DescribeInstances  10:00:01 → 10:00:02
  └─ span_id=toolu_02 [tool_start/tool_end] CallCLI DescribeRegions    10:00:03 → 10:00:04
span_id=<prompt_span> [turn_end]  10:00:05
```

### Span ID Strategy

| Event | `span_id` | `parent_span_id` |
|-------|-----------|------------------|
| prompt | Generated UUID (stored in state) | `null` (root span) |
| tool_start / tool_end | `tool_use_id` (from Claude) | prompt's `span_id` |
| turn_end | Own generated UUID | prompt's `span_id` |

### Full Schema

```jsonc
{
  "start_timestamp": "2026-05-19T10:00:00.123Z",  // ISO with ms
  "end_timestamp": "2026-05-19T10:00:01.456Z",    // completion time
  "session_id": "abc123",
  "client": "claude-code",
  "turn": 0,
  "event": "prompt | tool_start | tool_end | turn_end",
  "span_id": "a1b2c3d4",                          // unique span identifier
  "parent_span_id": null,                          // null for root, prompt's span_id for children

  // --- prompt event (root span) ---
  "prompt": "帮我查看ECS实例列表",
  // span_id = generated UUID, parent_span_id = null
  // start_timestamp = original UserPromptSubmit time
  // end_timestamp = Stop time (full request lifecycle)

  // --- tool_start event (child span open) ---
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_use_id": "toolu_xxx",
  "tool_input": { "command": "aliyun ecs DescribeInstances --region cn-hangzhou" },
  // span_id = tool_use_id, parent_span_id = prompt's span_id
  // end_timestamp = same as start_timestamp (span not yet closed)

  // --- tool_end event (child span close) ---
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_use_id": "toolu_xxx",
  "status": "success | failure",
  "error_message": "InvalidParameter: RegionId is required",
  "request_id": "A09A8DD7-...",
  "duration_ms": 1234,
  "tool_response": { ... },
  "truncated": false,
  // span_id = tool_use_id, parent_span_id = prompt's span_id
  // start_timestamp = tool invocation time (from pre_handler)
  // end_timestamp = response received time (from post_handler)

  // --- turn_end event (child of prompt span) ---
  "stop_reason": "end_turn | api_error"
  // span_id = own generated UUID, parent_span_id = prompt's span_id
  // start_timestamp = end_timestamp = Stop event time
}
```

## Architecture

### New Module: `tools/hooks/scripts/lib/trace_writer.py`

Single module (~100 lines) with:

```python
def trace_enabled() -> bool
    # ALIBABACLOUD_TRACE != "false" (default: enabled)

def trace_dir(client: str) -> str
    # ALIBABACLOUD_TRACE_DIR or <state_root>/<client>/traces/
    # Creates with 0700 if needed

def append_trace(client: str, session_id: str, record: dict) -> None
    # Appends one JSON line to <trace_dir>/<session_id>.jsonl
    # Uses os.open with O_APPEND for atomic writes
    # Applies light sanitization
    # Adds start_timestamp if not present (now)

def sanitize_trace_value(value) -> value
    # Recursively sanitize strings in dicts/lists
    # Patterns: LTAI*, STS.*, JWT (eyJ...), PEM blocks, phone, email
    # Replace with "***"

def truncate_response(obj, max_bytes=65536) -> (obj, bool)
    # JSON-serialize, check length, truncate if > max_bytes
    # Returns (possibly_truncated_obj, was_truncated)
```

### Modified Handlers

**`prompt_handler.py`** — Store prompt + timestamp + span_id in session state (no trace write yet):

```python
# Always store prompt for potential backfill at Stop
if trace_writer.trace_enabled() and session_id and prompt:
    import uuid
    with SessionState(client, session_id) as st:
        st.data["pending_prompt"] = prompt
        st.data["pending_prompt_ts"] = int(time.time() * 1000)
        st.data["prompt_span_id"] = uuid.uuid4().hex[:16]
```

**`pre_handler.py`** — Write `tool_start`, mark turn active, attach parent span:

```python
if trace_writer.trace_enabled():
    with SessionState(client, session_id) as st:
        st.data["turn_has_trace"] = True
        parent_span = st.data.get("prompt_span_id")
    trace_writer.append_trace(client, session_id, {
        "event": "tool_start",
        "span_id": tool_use_id,
        "parent_span_id": parent_span,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "tool_input": trace_writer.sanitize_trace_value(tool_input),
        "turn": turn,
    })
```

**`post_handler.py`** — Write `tool_end` with full response, error, and span linkage:

```python
if trace_writer.trace_enabled():
    response_data, was_truncated = trace_writer.truncate_response(tool_response or tool_result)
    now_ms = int(time.time() * 1000)
    with SessionState(client, session_id) as st:
        parent_span = st.data.get("prompt_span_id")
    trace_writer.append_trace(client, session_id, {
        "event": "tool_end",
        "span_id": tool_use_id,
        "parent_span_id": parent_span,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "status": status,
        "error_message": error_message or None,
        "request_id": request_id or None,
        "duration_ms": now_ms - start_ms,
        "tool_response": trace_writer.sanitize_trace_value(response_data),
        "truncated": was_truncated,
        "turn": turn,
        "start_timestamp": start_ms,   # from pre_handler marker
        "end_timestamp": now_ms,
    })
```

**`stop_handler.py`** — Backfill prompt as root span, write `turn_end` as root span close:

```python
if trace_writer.trace_enabled() and session_id:
    with SessionState(client, session_id) as st:
        turn_has_trace = st.data.get("turn_has_trace", False)
        if turn_has_trace:
            prompt_span = st.data.get("prompt_span_id")
            # Backfill prompt (root span open)
            pending = st.data.get("pending_prompt")
            prompt_ts = st.data.get("pending_prompt_ts")
            stop_ts = int(time.time() * 1000)
            if pending:
                trace_writer.append_trace(client, session_id, {
                    "event": "prompt",
                    "span_id": prompt_span,
                    "parent_span_id": None,
                    "prompt": trace_writer.sanitize_trace_value(pending),
                    "turn": turn,
                    "start_timestamp": prompt_ts,
                    "end_timestamp": stop_ts,
                })
            # Write turn_end (root span close)
            trace_writer.append_trace(client, session_id, {
                "event": "turn_end",
                "span_id": prompt_span,
                "parent_span_id": None,
                "stop_reason": hook_event_name,
                "turn": turn,
            })
        # Reset for next turn
        st.data.pop("turn_has_trace", None)
        st.data.pop("pending_prompt", None)
        st.data.pop("pending_prompt_ts", None)
        st.data.pop("prompt_span_id", None)
```

## File Layout

```
~/.cache/alibabacloud-agent-toolkit/telemetry/
  claude-code/
    sessions/           # existing state files
    traces/             # NEW: audit trace JSONL
      <session-id>.jsonl
    debug.log           # existing
  vscode/
    traces/
      <session-id>.jsonl
  copilot-cli/
    traces/
      <session-id>.jsonl
```

## Error Capture

| Error Source | How Captured | Event |
|-------------|--------------|-------|
| MCP tool returns error (API error) | PostToolUse with isError/error in response | `tool_end` status=failure |
| MCP server unreachable / init failure | PostToolUseFailure hook fires | `tool_end` status=failure |
| aliyun CLI non-zero exit | PostToolUse/Failure for Bash tool | `tool_end` status=failure |
| Tool timeout | PostToolUseFailure | `tool_end` status=failure |
| StopFailure (API error ending turn) | StopFailure hook fires | `turn_end` stop_reason=StopFailure |

All failure cases include `error_message` with the classified or raw error text.

## Sanitization (Light)

Patterns masked with `***`:
- Access Key IDs: `LTAI[A-Za-z0-9]{12,}`
- Access Key Secrets: 30+ char alnum strings adjacent to key-like context
- STS tokens: `STS\.[A-Za-z0-9+/=]{20,}`
- JWT: `eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}`
- PEM blocks: `-----BEGIN.*?-----END.*?-----`
- Phone numbers: `\b1[3-9]\d{9}\b`
- Email addresses: `\b[\w.-]+@[\w.-]+\.\w+\b`

NOT masked (differs from remote telemetry sanitization):
- File paths, UUIDs, FQDNs, IP addresses — these are useful for local debugging

## Activation

| Env Var | Effect |
|---------|--------|
| (unset) | Trace ON (default) |
| `ALIBABACLOUD_TRACE=false` | Trace OFF |
| `ALIBABACLOUD_TRACE_DIR=/custom/path` | Override trace directory |

## Risk Analysis

| Risk | Mitigation |
|------|-----------|
| Disk growth | No auto-cleanup (user requirement). Document location for manual cleanup |
| Write contention | O_APPEND atomic for lines < PIPE_BUF. Truncation caps at 64KB per write |
| Performance | File append ~µs. JSON bounded by 64KB. No agent latency impact |
| Crash resilience | JSONL: partial last line detectable, doesn't corrupt file |
| Prompt ordering | Backfilled at Stop, so appears after tool events in file. Consumers should sort by `start_timestamp` |
| Multi-turn prompt loss | If Stop doesn't fire (crash/kill), prompt is lost. Acceptable — same as tool events |

## Verification Plan

1. Run a session calling alibabacloud MCP tools → check JSONL has prompt + tool_start + tool_end + turn_end
2. Prompt doesn't mention alibabacloud but triggers alibabacloud tools → verify prompt is backfilled
3. Non-alibabacloud turn → verify no trace written
4. MCP connection failure → verify tool_end with error_message
5. Response >64KB → verify truncated=true
6. AK/SK in prompt → verify masked in trace
7. `ALIBABACLOUD_TRACE=false` → verify no trace file created
8. Existing telemetry dry-run tests still pass (no regression)
