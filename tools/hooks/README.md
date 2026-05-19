# Telemetry Hooks

Anonymized usage telemetry shared by all `alibabacloud-*` plugins in this
repository. Captures per-call hook events from agent clients (Claude Code in
Phase 1; Codex / QoderWork / VS Code as Phase 2 stubs) and uploads them via
`uvx alibabacloud.mcp-proxy@latest plugin-telemetry`.

## Quick start

Telemetry is on by default. Three controls:

| Want to                    | Do                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------- |
| Disable for current shell  | `export ALIBABACLOUD_TELEMETRY=false`                                                       |
| Diagnose missing events    | `export ALIBABACLOUD_TELEMETRY_DEBUG=1` then `tail -F <state-dir>/<client>/debug.log`       |
| Verify before sending      | `export ALIBABACLOUD_TELEMETRY_DRY_RUN=1` (logs the would-be command instead of executing)  |

`<state-dir>` defaults to `~/.cache/alibabacloud-agent-toolkit/telemetry`.

## Privacy

We collect:

- Event types (skill invocation, MCP tool use, CLI use, ...)
- Durations (start / end timestamps)
- Sanitized error class names
- Plugin / skill / tool names
- Cloud `RequestId` / `PopRequestId` (when present)

We **never** collect:

- AccessKey ID, AccessKey Secret, SecurityToken, Bearer / OAuth tokens
- Real names, phone numbers, emails, ID numbers
- Database passwords, private keys, certificate bodies
- Internal IPs, hostnames, full file paths under `/Users/<name>` etc.
- Raw user prompts or full tool outputs

Sanitization is a second line of defense. The primary defense is the field
allowlist defined in `telemetry_design.md` — only those fields are ever sent.

### What gets uploaded

Each event becomes a single CLI invocation, run as a detached background
process so the agent never waits:

```
uvx alibabacloud.mcp-proxy@latest plugin-telemetry \
    --client-name <claude-code|codex|qoderwork|vscode> \
    --event-type <skill_invocation|subagent_dispatch|reference_file_read|cli_command_use|mcp_tool_use> \
    --start-timestamp <ISO8601> \
    --end-timestamp <ISO8601> \
    --tool-name <tool> \
    --session-id <session> \
    --status <success|failure> \
    --turn <N> \
    [--mcp-tool ...] [--skill-name ...] [--plugin-name ...] \
    [--tool-request-id ...] [--cli-command ...] [--query-summary ...] \
    [--error-message ...]
```

### Opt out

```bash
export ALIBABACLOUD_TELEMETRY=false
```

## Configuration

| Variable                            | Default                                                | Effect                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `ALIBABACLOUD_TELEMETRY`            | `true`                                                 | Set to `false` to disable all hook uploads (each hook returns immediately)                                                      |
| `ALIBABACLOUD_TELEMETRY_DEBUG`      | `0`                                                    | When `1`, capture every hook fire decision into `<state-dir>/<client>/debug.log`                                                |
| `ALIBABACLOUD_TELEMETRY_DRY_RUN`    | `0`                                                    | When `1`, log the would-be `uvx` command without executing it (still writes to `debug.log`)                                     |
| `ALIBABACLOUD_TELEMETRY_STATE_DIR`  | `~/.cache/alibabacloud-agent-toolkit/telemetry`        | Override state directory; auto-falls back to `/tmp/alibabacloud-agent-toolkit-telemetry-<uid>` if home cache is unwritable      |
| `COPILOT_CLI`                       | unset                                                  | Set to `1` to declare the Copilot CLI client (Phase 2 stub)                                                                     |
| `CODEX_CLI`                         | unset                                                  | Set to `1` to declare the Codex client (Phase 2 stub)                                                                           |
| `QODER_WORK`                        | unset                                                  | Set to `1` to declare the QoderWork client (Phase 2 stub)                                                                       |

## Architecture

`tools/hooks/` is the canonical source. Each plugin under `plugins/` has a
`hooks/` symlink pointing here, so editing one set of scripts is enough.

### Hook lifecycle

| Event                | Script                                                | Responsibility                                                                                                                                       |
| -------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PreToolUse`         | `pre-tool-trace.sh` → `lib/pre_handler.py`            | Record start timestamp under `tool_starts[<key>]` in per-session state                                                                               |
| `PostToolUse`        | `post-tool-trace.sh` → `lib/post_handler.py`          | Classify tool, detect status, sanitize, upload event                                                                                                 |
| `PostToolUseFailure` | `post-tool-trace.sh` → `lib/post_handler.py`          | Same script; forces `status=failure`. Claude Code routes failed tool calls (including MCP `isError: true`) to this distinct event from successes.   |
| `Stop`               | `stop-turn-increment.sh` → `lib/stop_handler.py`      | Increment per-session turn counter; opportunistically clean stale state                                                                              |
| `StopFailure`        | `stop-turn-increment.sh` → `lib/stop_handler.py`      | Same script — applied symmetrically when an API error aborts a turn                                                                                  |

### Why subscribe to both `PostToolUse` and `PostToolUseFailure`

Claude Code dispatches tool failures to a separate event from successes. A
hook subscribed only to `PostToolUse` silently misses every failed cloud
call (`NoPermission`, `IncorrectVSwitchId`, `Throttling`, ...). Subscribing
to both events with the same script guarantees coverage regardless of how
Claude Code classifies the result.

### Event classification

`lib/post_handler.py:classify()` filters tool calls to events we care
about. The filter rule is a single allowlist — any name (skill, subagent,
MCP tool, file path segment) starting with `alibabacloud` (case-insensitive)
is "ours":

| Tool input                       | Conditions                                                         | Output `event_type`        |
| -------------------------------- | ------------------------------------------------------------------ | -------------------------- |
| `Skill`                          | `tool_input.skill` starts with `alibabacloud`                      | `skill_invocation`         |
| `Read` / `view` / `read_file`    | path contains `alibabacloud` segment AND ends with `SKILL.md`      | `skill_invocation`         |
| `Read` / `view` / `read_file`    | same path pattern, file is not `SKILL.md`                          | `reference_file_read`      |
| `Agent`                          | `tool_input.subagent_type` starts with `alibabacloud`              | `subagent_dispatch`        |
| `Bash`                           | `tool_input.command` first token is `aliyun`                       | `cli_command_use`          |
| MCP tool name                    | name contains `alibabacloud` (case-insensitive) or `AlibabaCloud___` | `mcp_tool_use`           |
| anything else                    | —                                                                  | dropped (no upload)        |

`--plugin-name` resolution priority:

1. `<plugin>:` prefix in skill / subagent name (e.g. `alibabacloud-core:foo` → `alibabacloud-core`)
2. File path segment matching `plugins/<plugin>/skills/...`
3. MCP tool name pattern `mcp__plugin_<plugin>_*`
4. Otherwise omitted

### Status detection (4-signal OR)

`lib/post_handler.py:detect_status()` short-circuits in priority order:

1. **`tool_response.is_error == true` OR `tool_response.status == "Errored"`** → failure. Tries to extract the deeper error message from `tool_result` (parses up to 16 KB of JSON) before falling back to `tool_response.error / stderr / stdout`.
2. **Top-level `tool_error` / `error` non-empty** → failure (client-layer crash, timeout).
3. **`tool_response.exit_code != 0`** → failure (Bash tool path).
4. **JSON parse on `tool_result[:16384]`**:
   - `isError`, `Code`, `error`, `Error`, or `status ∈ {errored, error, failed, failure}` → failure
   - regex match on Aliyun OpenAPI error codes (`InvalidParameter`, `NoPermission`, `Forbidden`, `AccessDenied`, `InvalidAccessKey*`, `Unauthorized`, `RequestTimeout`, `ServiceUnavailable`, `InternalError`, `Throttling`, `QuotaExceeded`) → failure
   - parse failure + first 500 chars match client-error keywords (`Connection refused`, `EOF`, `timeout`, `failed to`, `unreachable`, `connection reset`, `no route to host`) → failure

Plus an explicit override: when `hook_event_name == "PostToolUseFailure"`,
status is forced to `failure`.

When status is `failure`, an `error_message` is extracted (Message / first
non-empty line, sanitized, truncated to 200 chars) and emitted as
`--error-message`.

### `--tool-request-id` extraction

Looked up in `tool_result` (or Bash `tool_response.stdout` if `tool_result`
is empty), in priority order:

1. `RequestId` / `requestId` / `request_id` (top-level → `data` → `body` → `error`)
2. `PopRequestId` / `popRequestId` / `pop_request_id` (top-level → `data` → `body`)

First non-empty value wins. If neither family is present, the field is
omitted (we never generate a caller-side UUID).

### Sanitization (`lib/sanitize.py`)

Two functions, both bounded:

- `sanitize_error(msg)` — caps prefix at `200 * 4` chars for regex safety, then truncates output to `200` chars. Rules:
  - Credentials: `(ak|sk|pk|key|secret|password|token|credential|accesskey)\s*=\s*\S+` → `<keyword>=***`
  - `Bearer <token>` → `***`
  - `/Users/<name>/`, `/home/<name>/`, `C:\Users\<name>\` → `/<USER>/`
  - Email, CN mobile, IPv4, UUID v4 → `<REDACTED>`
- `sanitize_cli(cmd)` — keeps the first 3 whitespace-separated tokens, capped at 120 chars (drops args / values that may carry IDs)

### Bounds

| Limit                        | Value                | Rationale                                                                              |
| ---------------------------- | -------------------- | -------------------------------------------------------------------------------------- |
| stdin read cap               | 64 KB                | bash variable / Python `read(N)` ceiling — large `tool_result` truncated, never blocks |
| JSON parse window            | 16 KB                | covers ~100% of real error responses; <2 ms parse                                      |
| Error regex window           | 500 chars            | first error line; avoids catastrophic backtracking                                     |
| `--error-message` length     | 200 chars            | post-sanitization                                                                      |
| `--cli-command` length       | 120 chars / 3 tokens | safe command shape only                                                                |
| `pre` / `stop` hook timeout  | 3 s                  | configured in `hooks.json`                                                             |
| `post` / `post-failure` timeout | 15 s              | upload is fire-and-forget, doesn't count toward this                                   |
| Lock acquisition timeout     | 2 s                  | `_try_flock_exclusive` in `state.py`                                                   |
| Session state TTL            | 7 days               | auto-cleaned by Stop hook                                                              |

### Fire-and-forget upload

The `post-tool-trace.sh` wrapper detaches the upload as a background subshell
so the agent never blocks:

```bash
( uvx alibabacloud.mcp-proxy@latest plugin-telemetry "${args[@]}" \
    >/dev/null 2>&1 < /dev/null & ) >/dev/null 2>&1
disown 2>/dev/null
```

Failures of `uvx` (network down, package not installed, etc.) do not surface
to the agent. They are visible in the host shell environment if you trace
with `strace` / `dtruss`, but never in the user-facing transcript.

## State Files

State is bucketed per client and per session for safe multi-process and
multi-client operation:

```
<state-dir>/
├── claude-code/                       # one bucket per client
│   ├── debug.log                      # client-scoped diagnostic log
│   └── sessions/
│       ├── <safe-session>.state.json  # per-session state (turn + tool_starts)
│       └── <safe-session>.lock        # fcntl exclusive lock file
├── codex/                             # (Phase 2 stub)
└── qoderwork/                         # (Phase 2 stub)
```

### Path resolution

- `<state-dir>` priority:
  1. `$ALIBABACLOUD_TELEMETRY_STATE_DIR` (if writable)
  2. `$HOME/.cache/alibabacloud-agent-toolkit/telemetry` (if writable)
  3. `/tmp/alibabacloud-agent-toolkit-telemetry-<uid>` (last-resort fallback)
  4. If none writable, telemetry silently no-ops
- `<client-name>` is sanitized via `[^A-Za-z0-9_-]` → `_`, capped at 64 chars
- `<safe-session>` = `re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:120]`

We do **not** SHA-256 the session_id. Claude Code session IDs are UUIDv4 so
collision probability is negligible (~10⁻²⁵ at realistic volumes); the
character filter exists only to defend against future format changes or
non-UUID clients.

### Per-session state schema

```json
{
  "session_id": "abc-123-…",
  "turn": 3,
  "tool_starts": {
    "<tool_use_id-or-fallback>": 1763500800123
  },
  "updated_ts": "2026-05-19T11:07:42Z"
}
```

`tool_starts` is keyed by `tool_use_id` from the hook payload (a UUID
guaranteed unique by Claude Code per tool call) with sanitized `tool_name`
as fallback when `tool_use_id` is missing.

### Marker key resolution

Both `pre_handler.py` and `post_handler.py` compute the marker key as:

```python
marker_key = data.get("tool_use_id") or sanitize(tool_name)
```

`tool_use_id` is the robust choice because it can never be clobbered by a
parallel tool of the same name. The sanitized `tool_name` fallback works
for the common single-tool-per-pre/post case when an older client doesn't
include the ID.

### Concurrency model

| Concern                                                              | Handling                                                                                                                                                  |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Multiple Claude Code windows sharing the same `<state-dir>`          | Per-session files. Different sessions never touch each other's state.                                                                                     |
| Stop hook fires concurrently for the same session                    | `fcntl.flock(LOCK_EX)` on `<safe-session>.lock` serializes critical sections. Atomic write via `os.replace(tmp, state)` prevents partial state.            |
| Pre / Post overlap inside the same session                           | Same lock; `tool_starts[<tool_use_id>]` lets each tool call carry its own marker that can't be clobbered by another tool call's Pre.                       |
| Multiple clients (Claude Code + Codex + QoderWork) on one machine    | Top-level `<client>` directory keeps state, locks, and debug logs fully isolated.                                                                          |
| Multiple OS users on a shared host                                   | `/tmp` fallback path includes `<uid>` suffix.                                                                                                              |
| `fcntl` not available (Windows / non-POSIX)                          | `_try_flock_exclusive` is best-effort with 2 s timeout; on failure we proceed without lock (lossy but never blocks the agent).                            |
| State file corruption                                                | All loads wrapped in try/except; corrupt JSON → fresh empty state.                                                                                         |
| Stale state accumulation                                             | Stop hook runs `cleanup_stale_sessions(client, max_age_days=7)` opportunistically; files older than 7 days are removed.                                    |

Verified: `scripts/test-fixtures/stress-test.sh` forks N concurrent Stop
hook invocations against the same session and asserts the final turn
counter equals N (zero lost increments). Tested up to N=200.

### Lock primitive (`lib/state.py:SessionState`)

```python
with SessionState(client, session_id) as st:
    st.data["turn"] = st.data.get("turn", 0) + 1
    st.data["tool_starts"][marker_key] = epoch_ms
# On exit: atomic write of state, lock released.
```

Properties:

- Exclusive `fcntl.flock` with 2-second timeout
- State loaded inside the lock to avoid lost updates
- Atomic write via temp file + `os.replace`
- Best-effort: if locking is unavailable or write fails, the agent is never
  blocked or crashed — telemetry simply degrades silently
- Same primitive used by `pre_handler.py`, `post_handler.py`, and
  `stop_handler.py` so contention is consistent across all three hooks

### Client detection

The client identity is determined in priority order:

1. `COPILOT_CLI=1` env var → `copilot-cli`
2. `CODEX_CLI=1` env var → `codex`
3. `QODER_WORK=1` env var → `qoderwork`
4. Hook payload contains the literal substring `__vscode` → `vscode`
5. Default → `claude-code`

The same logic appears in the bash wrappers (for picking
`<client>/debug.log` path) and in `lib/post_handler.py` (for the
`--client-name` flag value), so both stay in sync.

## Diagnostics

### Enable debug mode

```bash
export ALIBABACLOUD_TELEMETRY_DEBUG=1
# (optional) export ALIBABACLOUD_TELEMETRY_DRY_RUN=1   # don't actually upload
```

Tail the per-client log (paths are split per client, so the right one to
watch depends on which agent host you're using):

```bash
tail -F ~/.cache/alibabacloud-agent-toolkit/telemetry/claude-code/debug.log
```

### Reading the log

One structured line per hook fire. Common patterns:

| Line                                                                                                | Meaning                                                                  |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `[pre] tool=Skill skill=alibabacloud-core:foo decision=track session=…`                             | Pre captured a start timestamp                                           |
| `[pre] tool=Read decision=skip reason=not-ours`                                                     | Pre ignored a non-`alibabacloud` tool call                               |
| `[post] event_name=PostToolUse tool=Skill decision=upload event=skill_invocation status=success`    | Post classified and queued an upload                                     |
| `[post] event_name=PostToolUseFailure tool=mcp__... decision=upload event=mcp_tool_use status=failure` | Post handled a failed MCP call routed to `PostToolUseFailure`         |
| `[post] event_name=PostToolUse tool=Bash decision=reject reason=bash-not-aliyun cmd_head=ls`        | Post rejected a non-`aliyun` Bash call (with sanitized command head)     |
| `[stop] turn=3 session=<id> client=claude-code`                                                     | Stop hook advanced the per-session turn counter                          |
| `DRYRUN: uvx alibabacloud.mcp-proxy@latest plugin-telemetry --…`                                    | The exact upload command (DRY_RUN mode only)                             |
| `decision=opted-out`                                                                                | `ALIBABACLOUD_TELEMETRY=false` short-circuited the hook                  |

### Reject reason vocabulary

Recognised by `post_handler.py`:

| Reason                          | Meaning                                                                                       |
| ------------------------------- | --------------------------------------------------------------------------------------------- |
| `opted-out`                     | `ALIBABACLOUD_TELEMETRY=false` set                                                            |
| `empty-stdin`                   | hook fired with no payload (TTY or empty pipe)                                                |
| `invalid-json`                  | stdin couldn't parse as JSON                                                                  |
| `empty-tool-name`               | payload missing `tool_name`                                                                   |
| `non-alibabacloud-skill`        | `Skill` tool but skill name doesn't start with `alibabacloud`                                 |
| `non-alibabacloud-subagent`     | `Agent` tool but `subagent_type` doesn't start with `alibabacloud`                            |
| `read-no-alibabacloud-segment`  | `Read` / `view` / `read_file` but file path doesn't contain `alibabacloud`                    |
| `read-not-in-skills-path`       | `Read` etc. and path has `alibabacloud` segment but doesn't match the skills directory shape  |
| `bash-not-aliyun`               | `Bash` tool but command doesn't start with `aliyun`                                           |
| `unknown-tool`                  | tool name didn't match any case                                                               |

### Diagnosing "events seem missing"

1. Confirm the hook is registered: run `/hooks` in Claude Code; it should
   list 5 entries (Pre, Post, PostFailure, Stop, StopFailure).
2. Enable `ALIBABACLOUD_TELEMETRY_DEBUG=1`, reproduce, check the relevant
   `debug.log`:
   - **No lines at all for the call** → hook didn't fire. Check plugin
     install / symlink (`bash tools/hooks/scripts/verify-symlinks.sh`).
   - **`[pre]` but no `[post]`** → tool call still in flight, OR
     `PostToolUseFailure` registration missing in `hooks.json`.
   - **`[post] decision=reject reason=…`** → our filter intentionally
     dropped this. The reason tells you why.
   - **`[post] decision=upload` but nothing visible at the sink** → check
     `uvx` is on PATH; turn on `ALIBABACLOUD_TELEMETRY_DRY_RUN=1` to see the
     exact command we tried to run.
3. Inspect per-session state directly:
   ```bash
   python3 tools/hooks/scripts/lib/state.py show \
       --client claude-code --session <session-id>
   ```

## Test harness

| Script                                                | Purpose                                                                                                                                                        |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/dry-run.sh <fixture> \| --all`               | Run a fixture (or all) through `lib/post_handler.py` (or `pre_handler.py` for `pre-*` stems), normalize timestamps, diff against `expected/<stem>.txt`. Used by CI. |
| `scripts/verify-symlinks.sh`                          | Assert `plugins/*/hooks` resolve to `tools/hooks`.                                                                                                              |
| `scripts/test-fixtures/stress-test.sh [N]`            | Fork N concurrent Stop hook invocations and assert the turn counter ends at exactly N (no lost increments). Default N=50.                                       |
| `lib/sanitize.py` (run as script)                     | Execute self-tests for sanitization rules.                                                                                                                      |
| `lib/state.py` (run as script)                        | CLI: `seed-marker --client X --session Y --key Z --ms N` (used by `dry-run.sh`), `cleanup --client X --max-age-days 7`, `show --client X --session Y`           |

Fixtures live under `test-fixtures/claude-code/<stem>.json` paired with
`test-fixtures/expected/<stem>.txt`. Fixtures whose stem starts with `pre-`
route to `lib/pre_handler.py`; everything else to `lib/post_handler.py`. A
fixture may have a sibling `<stem>.start` containing an integer epoch ms —
when present, `dry-run.sh` seeds it as a `tool_starts[<key>]` marker before
running the handler, so the handler computes a non-fallback duration.

A `TIMING_ONLY` expected file means: pass if the handler exits within 5 s
(no output diff). Used to validate the 64 KB stdin cap protects against
pathological large payloads.

## Phase 2 stubs

`codex-hooks.json` and `lib/post_handler.py:detect_client()` carry TODO
branches for Codex / QoderWork / VS Code support. Phase 1 only ships
Claude Code.
