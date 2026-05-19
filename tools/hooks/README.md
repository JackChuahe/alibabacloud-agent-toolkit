# Telemetry Hooks

Anonymized usage telemetry shared by all `alibabacloud-*` plugins in this
repository.

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

## Opt out

```bash
export ALIBABACLOUD_TELEMETRY=false
```

## Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `ALIBABACLOUD_TELEMETRY` | `true` | Set to `false` to disable all hook uploads |
| `ALIBABACLOUD_TELEMETRY_DEBUG` | `0` | When `1`, capture decisions from all four hook scripts (pre / post / post-failure / stop) into `<state-dir>/<client>/debug.log` |
| `ALIBABACLOUD_TELEMETRY_DRY_RUN` | `0` | When `1`, log the would-be `uvx` command without executing it |
| `ALIBABACLOUD_TELEMETRY_STATE_DIR` | `~/.cache/alibabacloud-agent-toolkit/telemetry` | Override state directory |

## Architecture

`tools/hooks/` is the canonical source. Each plugin under `plugins/` has a
`hooks/` symlink pointing here, so editing one set of scripts is enough.

| Lifecycle | Script | Responsibility |
|-----------|--------|----------------|
| `PreToolUse` | `scripts/pre-tool-trace.sh` | Record start timestamp |
| `PostToolUse` | `scripts/post-tool-trace.sh` | Classify, detect status, upload event |
| `PostToolUseFailure` | `scripts/post-tool-trace.sh` | Same script; forces `status=failure` for tool errors that Claude Code routes to a separate failure event (e.g. MCP `isError=true`) |
| `Stop` | `scripts/stop-turn-increment.sh` | Increment turn counter |
| `StopFailure` | `scripts/stop-turn-increment.sh` | Same script — applied symmetrically when a turn aborts with an error |

## State Files

State is bucketed per client and per session for safe multi-process and
multi-client operation:

```
<state-dir>/
└── <client-name>/                  # claude-code | codex | qoderwork | vscode
    ├── debug.log
    └── sessions/
        ├── <session-id>.state.json
        └── <session-id>.lock        # fcntl exclusive lock
```

`<state-dir>` defaults to `~/.cache/alibabacloud-agent-toolkit/telemetry`,
falling back to `/tmp/alibabacloud-agent-toolkit-telemetry-<uid>` when the
home cache is unwritable. Each per-session JSON consolidates the turn
counter and pending tool-start markers (keyed by `tool_use_id`, with
sanitized `tool_name` as fallback) into one file guarded by an
`fcntl.flock` exclusive lock and written atomically via `os.replace`.
Sessions older than 7 days are auto-cleaned by the Stop hook.

## Troubleshooting

If telemetry events appear to be missing for a tool call, enable debug
mode and re-run the agent:

```bash
export ALIBABACLOUD_TELEMETRY_DEBUG=1
# (optional) export ALIBABACLOUD_TELEMETRY_DRY_RUN=1   # don't actually upload
```

Then inspect the merged trace from all four hook scripts (debug logs are
bucketed per client):

```bash
tail -F ~/.cache/alibabacloud-agent-toolkit/telemetry/claude-code/debug.log
```

You will see one structured line per hook fire. Common patterns:

- `[pre] tool=Skill skill=alibabacloud-core:foo decision=track session=...` —
  pre-hook captured the start timestamp.
- `[pre] tool=Read decision=skip reason=not-ours` — pre-hook ignored a
  tool call that doesn't concern any `alibabacloud-*` plugin.
- `[post] event_name=PostToolUse tool=Skill decision=upload event=skill_invocation status=success`
  — post-hook classified the call and queued an upload.
- `[post] event_name=PostToolUseFailure tool=mcp__... decision=upload event=mcp_tool_use status=failure`
  — Claude Code routed an MCP tool error to the failure event; the hook
  still uploads it.
- `[post] event_name=PostToolUse tool=Bash decision=reject reason=bash-not-aliyun cmd_head=ls`
  — post-hook rejected the call because it's not an `aliyun` command.
- `[stop] turn=3 session=<id> client=claude-code` — turn counter advanced.

Reject reasons recognised by `post_handler.py`:
`opted-out`, `empty-stdin`, `invalid-json`, `empty-tool-name`,
`non-alibabacloud-skill`, `non-alibabacloud-subagent`,
`read-no-alibabacloud-segment`, `read-not-in-skills-path`,
`bash-not-aliyun`, `unknown-tool`.

## Phase 2 stubs

`codex-hooks.json` and `lib/post_handler.py:detect_client()` carry TODO
branches for Codex / QoderWork / VS Code support. Phase 1 only ships
Claude Code.
