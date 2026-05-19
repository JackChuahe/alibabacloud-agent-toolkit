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
| `ALIBABACLOUD_TELEMETRY_DEBUG` | `0` | When `1`, write decision trace to `<state-dir>/debug.log` |
| `ALIBABACLOUD_TELEMETRY_DRY_RUN` | `0` | When `1`, log the would-be `uvx` command without executing it |
| `ALIBABACLOUD_TELEMETRY_STATE_DIR` | `~/.cache/alibabacloud-agent-toolkit/telemetry` | Override state directory |

## Architecture

`tools/hooks/` is the canonical source. Each plugin under `plugins/` has a
`hooks/` symlink pointing here, so editing one set of scripts is enough.

| Lifecycle | Script | Responsibility |
|-----------|--------|----------------|
| `PreToolUse` | `scripts/pre-tool-trace.sh` | Record start timestamp |
| `PostToolUse` | `scripts/post-tool-trace.sh` | Classify, detect status, upload event |
| `Stop` | `scripts/stop-turn-increment.sh` | Increment turn counter, detect session swap |

## Phase 2 stubs

`codex-hooks.json` and `lib/post_handler.py:detect_client()` carry TODO
branches for Codex / QoderWork / VS Code support. Phase 1 only ships
Claude Code.
