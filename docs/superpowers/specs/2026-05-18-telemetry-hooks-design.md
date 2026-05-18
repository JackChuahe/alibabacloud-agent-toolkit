# Telemetry Hooks for Alibaba Cloud Agent Toolkit

**Status:** Draft for review
**Date:** 2026-05-18
**Owner:** caihe.ch

## Goal

Provide a unified, plugin-shared telemetry collection layer for the
`alibabacloud-agent-toolkit` repository. When a customer agent (Claude Code in
Phase 1; Codex / QoderWork later) loads or invokes any plugin asset (skill,
subagent, MCP tool, reference file, or the `aliyun` CLI), an anonymized event
is emitted via the `uvx alibabacloud.mcp-proxy@latest plugin-telemetry` CLI.

The system MUST:

1. Cover all current plugins (`alibabacloud-core`, `alibabacloud-agent`,
   `alibabacloud-data-analytics`) with a single shared implementation.
2. Use the `plugin-telemetry` CLI as the only upload channel — no HTTP curl
   POST, no local jsonl files in user repos.
3. Hard-code `--client-name` per agent host (claude-code today, codex /
   qoderwork branches reserved as TODO).
4. Provide accurate `--start-timestamp` and `--end-timestamp` for every event.
5. Detect `success` / `failure` precisely using multiple OR-combined signals
   and capture a sanitized `--error-message` whenever a failure is observed.
6. Be opt-out via a single environment variable, never collect sensitive data,
   never block the agent loop.

## Non-Goals

- **Codex / QoderWork hook scripts.** Phase 1 ships only Claude Code support;
  client detection branches are stubbed but not exercised.
- **HITL approval.** Removed from the reference implementation.
- **Local event buffering.** No `events.jsonl` written into user repos.
- **VS Code / Cursor adapters.** Reserved for a later phase.

## Architecture Overview

### Repository layout (canonical source + symlinks)

```
alibabacloud-agent-toolkit/
├── tools/
│   └── hooks/                              # canonical, single source of truth
│       ├── hooks.json                      # Claude Code hook registration
│       ├── codex-hooks.json                # Phase 2 placeholder (TODO header)
│       ├── README.md                       # privacy notice, env vars, debug
│       └── scripts/
│           ├── pre-tool-trace.sh           # PreToolUse → record start_timestamp
│           ├── post-tool-trace.sh          # PostToolUse → upload event
│           ├── stop-turn-increment.sh      # Stop → bump turn, detect session swap
│           ├── lib/
│           │   ├── detect-client.sh        # client identification
│           │   ├── parse-input.py          # bounded stdin parser
│           │   ├── status-detect.py        # 4-signal status detection
│           │   └── sanitize.py             # error / cli / query scrubbing
│           ├── test-fixtures/              # representative hook inputs
│           │   └── claude-code/*.json
│           ├── dry-run.sh                  # exercise scripts against fixtures
│           └── verify-symlinks.sh          # CI sanity check
├── plugins/
│   ├── alibabacloud-core/hooks            → ../../tools/hooks   (symlink)
│   ├── alibabacloud-agent/hooks           → ../../tools/hooks   (symlink)
│   └── alibabacloud-data-analytics/hooks  → ../../tools/hooks   (symlink)
└── .github/workflows/verify-hooks.yml      # CI to enforce symlink + dry-run
```

**Why symlinks:**
single source of truth, zero duplication, edits propagate to every plugin
automatically. macOS / Linux git clones honor symlinks by default. We document
the `git config core.symlinks true` requirement and surface it in CI.

### Hook lifecycle (Claude Code)

`tools/hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/pre-tool-trace.sh",
            "timeout": 3
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/post-tool-trace.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/stop-turn-increment.sh",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

`matcher: *` is used because tool names vary across Skill, MCP, Bash, Read.
Filtering happens inside the script. The HITL `Skill`-matcher block from the
reference implementation is removed.

## Event Classification

Single allowlist rule for "ours":

```python
PLUGIN_PREFIX = "alibabacloud"   # case-insensitive
def is_ours(name: str) -> bool:
    return name.lower().startswith(PLUGIN_PREFIX)
```

The script applies this rule to skill names, subagent_type, MCP tool names, and
file path segments.

### Event matrix (PostToolUse output)

| Input | event_type | Required fields | Notes |
|-------|-----------|-----------------|-------|
| `Skill` tool with `skill` matching `alibabacloud*` | `skill_invocation` | `--skill-name`, `--plugin-name` | covers `alibabacloud-core:foo` and bare `alibabacloud-foo` |
| `Read` / `view` / `read_file` whose path lands in `.../skills/<name>/SKILL.md` and contains `alibabacloud` plugin segment | `skill_invocation` | `--skill-name`, `--plugin-name` | parity with Azure Copilot Skills' SKILL.md detection |
| Same as above but file is **not** SKILL.md | `reference_file_read` | `--skill-name`, `--plugin-name`, `--query-summary=read:reference-file` | dedup vs SKILL.md case |
| `Agent` tool with `subagent_type` matching `alibabacloud*` | `subagent_dispatch` | `--skill-name` (= agent name), `--plugin-name` | |
| `Bash` tool whose `command` first token is `aliyun` | `cli_command_use` | `--cli-command` (sanitized prefix) | only first 3 tokens of the command kept |
| MCP tool name matching `(?i)alibabacloud` (covers `mcp__plugin_alibabacloud-*` and `AlibabaCloud___*`) | `mcp_tool_use` | `--tool-name`, `--mcp-tool` (short) | If MCP tool is `CallCLI`, also extract `--cli-command` from `tool_input.command` |
| Anything else | (silent exit) | — | `exit 0` without writing any output |

### `--plugin-name` resolution

Order:

1. From skill / subagent name colon prefix: `alibabacloud-core:foo` → `alibabacloud-core`.
2. From file path containing `plugins/<plugin>/skills/...` or installed-plugin
   cache path.
3. From MCP tool name pattern `mcp__plugin_<plugin>_*`.
4. None matched → omit `--plugin-name` (event still uploaded).

### Session and turn tracking

State directory: `~/.cache/alibabacloud-agent-toolkit/telemetry/`
(falls back to `/tmp/alibabacloud-agent-toolkit-telemetry/` if `~/.cache` is
unwritable).

- `current-session` — last seen `session_id`. When `session_id` changes,
  reset `turn` to `0`.
- `turn` — integer counter, incremented by `stop-turn-increment.sh`.
- `<session>-<tool>-start` — millisecond epoch written by `pre-tool-trace.sh`,
  consumed and unlinked by `post-tool-trace.sh`.

## Status Detection (post-tool-trace.sh)

Four signals OR-combined, short-circuit on first failure indicator:

```
1. tool_response.is_error == true            → failure
   tool_response.status   == "Errored"       → failure
2. tool_error / error (top-level) non-empty  → failure  (client-layer crash/timeout)
3. tool_response.exit_code != 0              → failure  (Bash tool)
4. JSON parse on first 16 KB of tool_result:
   4a. parse OK:
       - isError == true                     → failure
       - top-level Code / error / Error      → failure
       - status ∈ {Errored, Failed, Error}   → failure
       - data.* / body.* same checks         → failure
       - regex match on common Aliyun OpenAPI codes:
           InvalidParameter | NoPermission | Forbidden |
           AccessDenied | InvalidAccessKey | Unauthorized |
           RequestTimeout | ServiceUnavailable | InternalError |
           Throttling | QuotaExceeded
   4b. parse fails AND first-500-char regex hits
       client error keywords:
           Connection refused | EOF | timeout | failed to | unreachable
                                              → failure
   4c. otherwise                              → success
```

### Performance bounds

| Knob | Value | Rationale |
|------|------:|-----------|
| stdin read cap | 64 KB | bash variables / Python `read(N)` ceiling |
| JSON parse window | 16 KB | covers ~100% of error responses, <2 ms parse |
| Error regex window | 500 chars | catches first error line, no quadratic blowup |
| Python script timeout (post) | 9 s | well under hook 15s ceiling |
| Bash hook timeout | 15 s | fire-and-forget upload doesn't count toward this |

### Error message extraction

```
1. JSON Message / message / error.message  (top-level → data → body)
2. fall back to first non-empty line of tool_result
3. truncate to 200 characters
4. sanitize:
   - replace (key|secret|password|token|credential|accesskey)=<value>  with =***
   - replace /Users/<name>/, C:\Users\<name>\, /home/<name>/  with /Users/***/
   - replace email addresses, phone-like sequences, IP addresses
   - replace UUID-like strings with <UUID>
5. write into --error-message
```

### `--tool-request-id` extraction

Take **the first non-empty value** of:

1. `RequestId` / `requestId` / `request_id` (top-level → `data` → `body`)
2. `PopRequestId` / `popRequestId` / `pop_request_id` (top-level → `data` → `body`)

If neither is present, omit `--tool-request-id` entirely. Do not generate a
caller-side UUID.

> Note on `telemetry_design.md`: that doc describes `--tool-request-id` as
> "Caller-generated UUID". This design overrides that to use the cloud-side
> `RequestId` / `PopRequestId` because it has higher diagnostic value. We will
> propose a documentation update to the telemetry design doc to reflect this.

## Upload (post-tool-trace.sh)

Replaces the curl-to-endpoint approach. Single CLI invocation:

```bash
( uvx alibabacloud.mcp-proxy@latest plugin-telemetry "${args[@]}" \
    >/dev/null 2>&1 < /dev/null & ) >/dev/null 2>&1
disown 2>/dev/null
```

Args are built using a bash array (no string interpolation, no shell
injection). Optional flags are appended only when their values are non-empty.

### Field mapping

| CLI flag | Source | Sanitization |
|----------|--------|--------------|
| `--client-name` | `detect-client.sh` (claude-code in Phase 1) | safe |
| `--event-type` | event matrix above | safe |
| `--start-timestamp` | `<state-dir>/<session>-<tool>-start` → ISO8601 UTC | safe |
| `--end-timestamp` | `time.time()` in post hook → ISO8601 UTC | safe |
| `--tool-name` | `tool_name` from hook payload | safe |
| `--session-id` | `session_id` from hook payload | already UUID |
| `--status` | status detection result | safe |
| `--turn` | `<state-dir>/turn` (default 0) | safe |
| `--mcp-tool` | regex extract `AlibabaCloud___\w+` from tool_name | safe |
| `--skill-name` | tool_input.skill / subagent_type / extracted from path | safe |
| `--plugin-name` | resolution rules above | safe |
| `--tool-request-id` | RequestId / PopRequestId extraction | safe (cloud-generated) |
| `--cli-command` | first 3 tokens of `aliyun ...` or MCP `command` | strip args/values |
| `--query-summary` | intent category only (e.g., `read:reference-file`) | never raw user prompt |
| `--error-message` | extracted + sanitized error string | see sanitization above |

### Start-timestamp fallback

If `pre-tool-trace.sh` did not run (e.g., process timing race), the start
file is missing. The post hook then sets:

- `start_timestamp = end_timestamp - 1ms` (minimum valid value)
- Append `start-fallback` marker to `--query-summary` so server-side analytics
  can filter these events.

## Client Detection (`detect-client.sh`)

```bash
detect_client() {
    if [ "$COPILOT_CLI" = "1" ]; then
        echo "copilot-cli"        # TODO Phase 2
    elif [ "$CODEX_CLI" = "1" ]; then
        echo "codex"              # TODO Phase 2
    elif [ "$QODER_WORK" = "1" ]; then
        echo "qoderwork"          # TODO Phase 2
    elif <input has "hook_event_name"> && <tool_use_id contains __vscode>; then
        echo "vscode"             # TODO Phase 3
    else
        echo "claude-code"        # Phase 1 default
    fi
}
```

Phase 1 only the `claude-code` branch is functional; the others are present so
extending later does not require touching `hooks.json` or the upload code.

## Privacy and Configuration

### Environment variables

| Name | Default | Effect |
|------|---------|--------|
| `ALIBABACLOUD_TELEMETRY` | `true` | Set to `false` to disable all hook uploads — hooks return `{"continue":true}` immediately |
| `ALIBABACLOUD_TELEMETRY_DEBUG` | `0` | When `1`, write raw stdin and decision trace to `~/.cache/alibabacloud-agent-toolkit/telemetry/debug.log` |
| `ALIBABACLOUD_TELEMETRY_DRY_RUN` | `0` | When `1`, log the would-be `uvx ... plugin-telemetry` command to debug log without executing it |

> Older `ALICLOUD_OPS_*` variables from the reference impl are deprecated;
> README documents the rename.

### Privacy guarantees

We **never** collect:

- AccessKey ID, AccessKey Secret, SecurityToken, Bearer / OAuth tokens
- Real names, phone numbers, emails, ID numbers (RAM sub-account or otherwise)
- Database passwords, private keys, certificate bodies
- Internal IPs, hostnames, full file paths under `/Users/<name>` etc.
- Raw user prompts or full tool outputs

Sanitization is a **second line of defense** — primary defense is the field
allowlist (we only ever pass schema fields defined by `telemetry_design.md`).

No local `events.jsonl` is written. The reference implementation's
`.aliyun-ai-ops-spec/.telemetry/events.jsonl` behavior is intentionally removed
to avoid accidental commits of telemetry into user repositories.

## Testing & CI

### Test fixtures (`tools/hooks/scripts/test-fixtures/claude-code/`)

Representative inputs we will validate against:

- `pre-skill-success.json` — Skill PreToolUse, alibabacloud-core skill
- `post-skill-success.json` — Skill PostToolUse, success
- `post-mcp-success.json` — `AlibabaCloud___CallCLI` returning a normal response
- `post-mcp-failure-isError.json` — MCP response with `isError: true`
- `post-mcp-failure-aliyun-code.json` — MCP response with `Code: NoPermission`
- `post-bash-aliyun-success.json` — Bash with `aliyun ecs DescribeInstances ...` exit 0
- `post-bash-aliyun-exit1.json` — Bash with non-zero exit_code
- `post-read-skill-md.json` — Read tool reading a SKILL.md
- `post-read-reference-file.json` — Read tool reading a reference file
- `post-huge-response-10mb.json` — 10 MB tool_result, must not block

Each fixture has a paired expected `*.cli` file in `expected/` showing the
expected `uvx alibabacloud.mcp-proxy@latest plugin-telemetry ...` command line.

### `dry-run.sh`

```
ALIBABACLOUD_TELEMETRY_DRY_RUN=1 ALIBABACLOUD_TELEMETRY_DEBUG=1 \
    bash post-tool-trace.sh < fixtures/claude-code/<name>.json
```

Compares logged command line to `expected/<name>.cli`; CI fails on mismatch.

### `verify-symlinks.sh`

Asserts each `plugins/*/hooks` is a symlink resolving to `tools/hooks` from
the repo root. Runs in `.github/workflows/verify-hooks.yml`.

## Phased Rollout

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Claude Code hook scripts, three plugin symlinks, dry-run + symlink CI | this design |
| 2 | Codex / QoderWork client branches activated, `codex-hooks.json` populated | TODO |
| 3 | VS Code / Cursor adapters | TODO |

## Open Items / Risks

1. **Symlink portability on Windows.** `git config core.symlinks=true` is
   required; some users running Git Bash without admin may receive plain text
   files. Mitigation: README warning, CI enforcement, and a fallback resolution
   in `pre-tool-trace.sh` that detects "hooks/ is not a symlink → log warning,
   continue with degraded behavior".
2. **`uvx` cold start latency.** First invocation after a fresh shell can take
   2–4 seconds. Fire-and-forget execution means user does not wait, but bursty
   hooks could spawn many `uvx` processes. Mitigation: the `plugin-telemetry`
   subcommand should be quick; we measure during Phase 1 implementation and
   add coalescing in Phase 2 if needed.
3. **`--tool-request-id` semantic mismatch with telemetry_design.md.** This
   design uses the cloud `RequestId` instead of caller-generated UUIDs. We
   will submit a doc PR to `telemetry_design.md` to clarify before merging.

## Acceptance Criteria

A PR implementing this design is mergeable when:

- [ ] `tools/hooks/` exists with all scripts, hooks.json, README
- [ ] Three `plugins/*/hooks` symlinks resolve to `tools/hooks`
- [ ] `verify-symlinks.sh` passes
- [ ] `dry-run.sh` against every fixture produces the expected CLI command line
- [ ] HITL script and HITL hook entry are not present
- [ ] No HTTP curl POST or `events.jsonl` write remains in scripts
- [ ] `ALIBABACLOUD_TELEMETRY=false` short-circuits all three hooks within 10 ms
- [ ] `--start-timestamp` and `--end-timestamp` are present on every emitted
      event (with documented fallback when pre hook is missing)
- [ ] `--error-message` is populated on every `failure` event after sanitization
- [ ] CI workflow `verify-hooks.yml` runs on PRs touching `tools/hooks/**` or
      `plugins/*/hooks`
