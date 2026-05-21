# Telemetry Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Claude Code telemetry hooks shared across all `alibabacloud-*` plugins, uploading anonymized events via `uvx alibabacloud.mcp-proxy@latest plugin-telemetry`.

**Architecture:** Canonical scripts live under `tools/hooks/`; each plugin's `hooks/` is a relative symlink. Bash wrappers (`pre-tool-trace.sh`, `post-tool-trace.sh`, `stop-turn-increment.sh`) handle hook lifecycle and invoke Python handlers (`lib/pre_handler.py`, `lib/post_handler.py`) for parsing, status detection, and sanitization. Uploads are fire-and-forget so the agent loop never blocks.

**Tech Stack:** bash, Python 3 (stdlib only), `uvx` (Astral) as CLI launcher, GitHub Actions for CI.

**Spec:** `docs/superpowers/specs/2026-05-18-telemetry-hooks-design.md`

---

## File Structure (final state)

```
tools/hooks/
├── README.md                                  # privacy notice, env vars, debug
├── hooks.json                                 # Claude Code hook registration
├── codex-hooks.json                           # Phase 2 placeholder
└── scripts/
    ├── pre-tool-trace.sh                      # bash wrapper → pre_handler.py
    ├── post-tool-trace.sh                     # bash wrapper → post_handler.py + uvx upload
    ├── stop-turn-increment.sh                 # pure bash
    ├── dry-run.sh                             # test harness
    ├── verify-symlinks.sh                     # CI helper
    ├── lib/
    │   ├── detect_client.sh                   # sourced helper
    │   ├── pre_handler.py                     # extract tool_name, write start file
    │   ├── post_handler.py                    # parse, classify, status, sanitize, emit args
    │   └── sanitize.py                        # importable sanitization module
    └── test-fixtures/
        ├── claude-code/*.json                 # representative hook inputs
        └── expected/*.txt                     # canonical uvx arg lists

plugins/
├── alibabacloud-core/hooks                   → ../../tools/hooks
├── alibabacloud-agent/hooks                  → ../../tools/hooks
└── alibabacloud-data-analytics/hooks         → ../../tools/hooks

.github/workflows/verify-hooks.yml
```

---

## Conventions used in every task

- Scripts always set `set +e` (privacy-first: never crash the agent)
- Python code lives in importable `.py` modules under `lib/` (testable directly with `python3 -m`)
- Bash wrappers are kept under 80 lines each
- Fire-and-forget upload pattern: `( cmd >/dev/null 2>&1 < /dev/null & ) >/dev/null 2>&1; disown 2>/dev/null`
- State directory: `${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}` with `/tmp/alibabacloud-agent-toolkit-telemetry/` fallback
- Test driver invokes Python handlers directly (`python3 lib/post_handler.py < fixture`) — bypasses the bash wrapper for deterministic comparison
- Branch in use: `telemetry-plugin` (already created)
- Each task ends with one commit

---

## Task 1: Project scaffolding

**Files:**
- Create: `tools/hooks/scripts/lib/.gitkeep`
- Create: `tools/hooks/scripts/test-fixtures/claude-code/.gitkeep`
- Create: `tools/hooks/scripts/test-fixtures/expected/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/caihe/projects/github-personal/alibabacloud-agent-toolkit
mkdir -p tools/hooks/scripts/lib
mkdir -p tools/hooks/scripts/test-fixtures/claude-code
mkdir -p tools/hooks/scripts/test-fixtures/expected
touch tools/hooks/scripts/lib/.gitkeep
touch tools/hooks/scripts/test-fixtures/claude-code/.gitkeep
touch tools/hooks/scripts/test-fixtures/expected/.gitkeep
```

- [ ] **Step 2: Add gitignore entries**

Append to `.gitignore`:

```gitignore

# Telemetry hook local state (should never be committed)
/tmp/alibabacloud-agent-toolkit-telemetry/
.aliyun-ai-ops-spec/.telemetry/

# Test scratch
tools/hooks/scripts/test-fixtures/.scratch/
```

- [ ] **Step 3: Verify**

Run: `ls -d tools/hooks/scripts/lib tools/hooks/scripts/test-fixtures/claude-code tools/hooks/scripts/test-fixtures/expected`
Expected: all three paths print without error.

- [ ] **Step 4: Commit**

```bash
git add tools/hooks .gitignore
git commit -m "chore: scaffold tools/hooks directory structure"
```

---

## Task 2: Privacy README

**Files:**
- Create: `tools/hooks/README.md`

- [ ] **Step 1: Write README**

Create `tools/hooks/README.md` with content:

````markdown
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

`detect_client.sh` and `codex-hooks.json` carry TODO branches for Codex /
QoderWork / VS Code support. Phase 1 only ships Claude Code.
````

- [ ] **Step 2: Commit**

```bash
git add tools/hooks/README.md
git commit -m "docs: add telemetry hooks README"
```

---

## Task 3: Test harness (dry-run.sh + verify-symlinks.sh + first fixture)

**Files:**
- Create: `tools/hooks/scripts/dry-run.sh`
- Create: `tools/hooks/scripts/verify-symlinks.sh`
- Create: `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-success.json`
- Create: `tools/hooks/scripts/test-fixtures/expected/post-mcp-success.txt`

This task lays the testing foundation. The harness is needed before we can do
TDD on the actual handlers, so we accept that this first task does not itself
run a "failing → passing" cycle for an existing component — it builds the test
runner that subsequent tasks will use.

- [ ] **Step 1: Write the first fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-success.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-001",
  "tool_use_id": "toolu_001",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {
    "command": "aliyun ecs DescribeInstances --region cn-hangzhou"
  },
  "tool_response": {
    "status": "Success",
    "is_error": false
  },
  "tool_result": "{\"RequestId\":\"REQ-ABC-123\",\"Instances\":{\"Instance\":[]}}"
}
```

- [ ] **Step 2: Write the expected canonical args**

Create `tools/hooks/scripts/test-fixtures/expected/post-mcp-success.txt`:

```
--client-name
claude-code
--event-type
mcp_tool_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI
--session-id
test-session-001
--status
success
--turn
0
--mcp-tool
AlibabaCloud___CallCLI
--plugin-name
alibabacloud-core
--tool-request-id
REQ-ABC-123
--cli-command
aliyun ecs DescribeInstances
```

`<TS>` is a placeholder the harness substitutes before comparison.

- [ ] **Step 3: Write dry-run.sh**

Create `tools/hooks/scripts/dry-run.sh`:

```bash
#!/bin/bash
# Dry-run harness for telemetry hook scripts.
# Usage: dry-run.sh <fixture-stem>
#   - reads tools/hooks/scripts/test-fixtures/claude-code/<stem>.json
#   - runs python3 post_handler.py < fixture (or pre_handler.py for "pre-" stems)
#   - normalizes ISO timestamps to <TS>
#   - diffs against test-fixtures/expected/<stem>.txt
# Returns: 0 on PASS, 1 on FAIL.

set -e

stem="$1"
if [ -z "$stem" ]; then
    echo "Usage: $0 <fixture-stem> | --all" >&2
    exit 2
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"
fixturesDir="$scriptDir/test-fixtures/claude-code"
expectedDir="$scriptDir/test-fixtures/expected"

run_one() {
    local stem="$1"
    local fixture="$fixturesDir/$stem.json"
    local expected="$expectedDir/$stem.txt"

    if [ ! -f "$fixture" ]; then
        echo "FAIL: $stem (no fixture at $fixture)"
        return 1
    fi
    if [ ! -f "$expected" ]; then
        echo "FAIL: $stem (no expected at $expected)"
        return 1
    fi

    local handler
    if [[ "$stem" == pre-* ]]; then
        handler="$scriptDir/lib/pre_handler.py"
    else
        handler="$scriptDir/lib/post_handler.py"
    fi

    # Isolated state dir per test
    local stateDir
    stateDir="$(mktemp -d)"
    trap "rm -rf $stateDir" RETURN

    # Pre-populate start file if companion exists, so post tests have a start_ts
    if [ -f "$fixturesDir/$stem.start" ]; then
        cp "$fixturesDir/$stem.start" "$stateDir/"
    fi

    local actual
    actual=$(ALIBABACLOUD_TELEMETRY_STATE_DIR="$stateDir" \
             ALIBABACLOUD_TELEMETRY_DRY_RUN=1 \
             python3 "$handler" < "$fixture" 2>/dev/null) || {
        echo "FAIL: $stem (handler exited non-zero)"
        return 1
    }

    # Normalize ISO timestamps to <TS>
    local actualNorm
    actualNorm=$(echo "$actual" | sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z/<TS>/g')

    if diff -u <(cat "$expected") <(echo "$actualNorm") > /dev/null; then
        echo "PASS: $stem"
        return 0
    else
        echo "FAIL: $stem"
        diff -u <(cat "$expected") <(echo "$actualNorm") || true
        return 1
    fi
}

if [ "$stem" = "--all" ]; then
    fail=0
    for f in "$fixturesDir"/*.json; do
        [ -f "$f" ] || continue
        s="$(basename "$f" .json)"
        run_one "$s" || fail=1
    done
    exit $fail
else
    run_one "$stem"
fi
```

Make executable: `chmod +x tools/hooks/scripts/dry-run.sh`

- [ ] **Step 4: Write verify-symlinks.sh**

Create `tools/hooks/scripts/verify-symlinks.sh`:

```bash
#!/bin/bash
# Verifies each plugin's hooks/ is a symlink resolving to tools/hooks.
# Returns: 0 if all OK, 1 otherwise.
set -e

repoRoot="$(cd "$(dirname "$0")/../../.." && pwd)"
canonical="$repoRoot/tools/hooks"

if [ ! -d "$canonical" ]; then
    echo "FAIL: canonical $canonical missing"
    exit 1
fi

fail=0
for plugin in "$repoRoot"/plugins/*/; do
    [ -d "$plugin" ] || continue
    name=$(basename "$plugin")
    link="$plugin/hooks"
    if [ ! -L "$link" ]; then
        echo "FAIL: $name/hooks is not a symlink"
        fail=1
        continue
    fi
    target=$(cd "$(dirname "$link")" && cd "$(readlink "$link")" && pwd)
    if [ "$target" != "$canonical" ]; then
        echo "FAIL: $name/hooks → $target (expected $canonical)"
        fail=1
        continue
    fi
    echo "PASS: $name/hooks → tools/hooks"
done

exit $fail
```

Make executable: `chmod +x tools/hooks/scripts/verify-symlinks.sh`

- [ ] **Step 5: Confirm harness runs (and reports FAIL because handlers do not yet exist)**

Run: `bash tools/hooks/scripts/dry-run.sh post-mcp-success`
Expected output starts with `FAIL:` (handler missing). This is the desired
state — subsequent tasks will turn it into PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/hooks/scripts/dry-run.sh \
        tools/hooks/scripts/verify-symlinks.sh \
        tools/hooks/scripts/test-fixtures
chmod +x tools/hooks/scripts/dry-run.sh tools/hooks/scripts/verify-symlinks.sh
git commit -m "test: add telemetry hook dry-run harness and first fixture"
```

---

## Task 4: stop-turn-increment.sh

**Files:**
- Create: `tools/hooks/scripts/stop-turn-increment.sh`
- Test: ad-hoc bash assertions in this task (no fixtures needed)

- [ ] **Step 1: Write failing test**

Run:

```bash
bash -c '
set -e
stateDir=$(mktemp -d)
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir bash tools/hooks/scripts/stop-turn-increment.sh
test -f "$stateDir/turn" && [ "$(cat $stateDir/turn)" = "1" ] || { echo "FAIL"; exit 1; }
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir bash tools/hooks/scripts/stop-turn-increment.sh
[ "$(cat $stateDir/turn)" = "2" ] || { echo "FAIL"; exit 1; }
echo "PASS"
'
```

Expected: `bash: tools/hooks/scripts/stop-turn-increment.sh: No such file or directory` (script missing → FAIL).

- [ ] **Step 2: Implement script**

Create `tools/hooks/scripts/stop-turn-increment.sh`:

```bash
#!/bin/bash
# Stop hook — increments the per-session turn counter at end of agent turn.
# Turn number is consumed by post-tool-trace.sh to tag --turn on each event.
set +e

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    exit 0
fi

stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
mkdir -p "$stateDir" 2>/dev/null || stateDir="/tmp/alibabacloud-agent-toolkit-telemetry"
mkdir -p "$stateDir" 2>/dev/null

turnFile="$stateDir/turn"
if [ -f "$turnFile" ]; then
    current=$(cat "$turnFile" 2>/dev/null)
    echo $(( ${current:-0} + 1 )) > "$turnFile" 2>/dev/null
else
    echo "1" > "$turnFile" 2>/dev/null
fi

exit 0
```

Make executable: `chmod +x tools/hooks/scripts/stop-turn-increment.sh`

- [ ] **Step 3: Run test to confirm pass**

Re-run the bash test from Step 1. Expected: `PASS`.

- [ ] **Step 4: Test opt-out**

```bash
stateDir=$(mktemp -d)
ALIBABACLOUD_TELEMETRY=false ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
    bash tools/hooks/scripts/stop-turn-increment.sh
[ ! -f "$stateDir/turn" ] && echo "PASS: opt-out works" || echo "FAIL"
```

Expected: `PASS: opt-out works`.

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/scripts/stop-turn-increment.sh
chmod +x tools/hooks/scripts/stop-turn-increment.sh
git commit -m "feat: add stop-turn-increment hook script"
```

---

## Task 5: pre-tool-trace.sh + pre_handler.py

**Files:**
- Create: `tools/hooks/scripts/pre-tool-trace.sh`
- Create: `tools/hooks/scripts/lib/pre_handler.py`
- Create: `tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json`

`pre_handler.py` reads stdin (≤ 64 KB), extracts `tool_name` and
`session_id`, writes a start-marker file `${state}/<session>-<tool>.start`
containing the current epoch ms, and detects session swaps (resets `turn` to
0 when `session_id` changes).

- [ ] **Step 1: Write fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json`:

```json
{
  "hook_event_name": "PreToolUse",
  "session_id": "test-session-002",
  "tool_use_id": "toolu_002",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {
    "command": "aliyun oss ls"
  }
}
```

- [ ] **Step 2: Write failing assertion**

```bash
stateDir=$(mktemp -d)
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
    python3 tools/hooks/scripts/lib/pre_handler.py \
    < tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json
ls "$stateDir"/test-session-002-*.start && echo PASS || echo FAIL
```

Expected: `python3: can't open file '...pre_handler.py'` (FAIL).

- [ ] **Step 3: Implement pre_handler.py**

Create `tools/hooks/scripts/lib/pre_handler.py`:

```python
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


def main() -> int:
    if os.environ.get("ALIBABACLOUD_TELEMETRY") == "false":
        return 0
    raw = read_stdin_bounded()
    if not raw:
        return 0
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return 0
    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    session_id = data.get("session_id") or ""
    if not is_ours_tool(tool_name, tool_input):
        return 0

    sd = state_dir()
    if not sd:
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Implement bash wrapper**

Create `tools/hooks/scripts/pre-tool-trace.sh`:

```bash
#!/bin/bash
# Pre-tool-use hook wrapper. Delegates to lib/pre_handler.py.
# Always exits 0 to avoid blocking the agent.
set +e

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    exit 0
fi

if [ -t 0 ]; then
    exit 0
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"
python3 "$scriptDir/lib/pre_handler.py" >/dev/null 2>&1 || true

exit 0
```

Make executable: `chmod +x tools/hooks/scripts/pre-tool-trace.sh`

- [ ] **Step 5: Re-run assertion**

```bash
stateDir=$(mktemp -d)
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
    python3 tools/hooks/scripts/lib/pre_handler.py \
    < tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json
ls "$stateDir"/test-session-002-*.start && echo PASS || echo FAIL
```

Expected: `PASS`.

- [ ] **Step 6: Test session swap**

```bash
stateDir=$(mktemp -d)
echo "5" > "$stateDir/turn"
echo "old-session" > "$stateDir/current-session"
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
    python3 tools/hooks/scripts/lib/pre_handler.py \
    < tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json
[ "$(cat $stateDir/turn)" = "0" ] && echo "PASS: turn reset" || echo "FAIL"
[ "$(cat $stateDir/current-session)" = "test-session-002" ] && echo "PASS: session updated" || echo "FAIL"
```

Expected: both PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/hooks/scripts/pre-tool-trace.sh \
        tools/hooks/scripts/lib/pre_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/pre-mcp.json
chmod +x tools/hooks/scripts/pre-tool-trace.sh
git commit -m "feat: add pre-tool-trace hook with start-timestamp tracking"
```

---

## Task 6: detect_client.sh + sanitize.py module

**Files:**
- Create: `tools/hooks/scripts/lib/detect_client.sh`
- Create: `tools/hooks/scripts/lib/sanitize.py`

These are dependencies for `post_handler.py` in subsequent tasks; isolating
them now lets us unit-test sanitization without depending on the full handler.

- [ ] **Step 1: Write detect_client.sh**

Create `tools/hooks/scripts/lib/detect_client.sh`:

```bash
# Sourced helper. Defines detect_client() which writes the client name
# (e.g., "claude-code") to stdout. Phase 1 only the claude-code branch is
# functional; codex/qoderwork/vscode are reserved for Phase 2.
#
# Inputs: optionally $1 = stdin payload (JSON string) for inspection.
# Detection priority:
#   1. COPILOT_CLI=1            → copilot-cli   (TODO Phase 2)
#   2. CODEX_CLI=1              → codex          (TODO Phase 2)
#   3. QODER_WORK=1             → qoderwork      (TODO Phase 2)
#   4. payload.tool_use_id contains __vscode → vscode  (TODO Phase 3)
#   5. default → claude-code

detect_client() {
    local payload="${1:-}"
    if [ "$COPILOT_CLI" = "1" ]; then
        echo "copilot-cli"
        return
    fi
    if [ "$CODEX_CLI" = "1" ]; then
        echo "codex"
        return
    fi
    if [ "$QODER_WORK" = "1" ]; then
        echo "qoderwork"
        return
    fi
    if [ -n "$payload" ]; then
        case "$payload" in
            *'"__vscode"'*|*'__vscode'*)
                echo "vscode"
                return
                ;;
        esac
    fi
    echo "claude-code"
}
```

- [ ] **Step 2: Write sanitize.py with failing tests**

Create `tools/hooks/scripts/lib/sanitize.py`:

```python
#!/usr/bin/env python3
"""Sanitization utilities for telemetry strings.

Public API:
    sanitize_error(msg: str) -> str
    sanitize_cli(cmd: str) -> str

Both truncate to safe lengths and strip credentials, file paths, PII.
"""
from __future__ import annotations

import re

ERROR_MAX_LEN = 200
CLI_MAX_TOKENS = 3
CLI_MAX_LEN = 120

_CRED_PATTERNS = [
    re.compile(r"(?i)(key|secret|password|token|credential|accesskey)\s*=\s*\S+"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]+"),
]
_PATH_PATTERNS = [
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"C:\\Users\\[^\\\s]+\\"),
]
_PII_PATTERNS = [
    re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),         # email
    re.compile(r"\b1[3-9]\d{9}\b"),                              # CN mobile
    re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),       # IPv4
    re.compile(r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b"),  # UUID
]


def sanitize_error(msg) -> str:
    if msg is None:
        return ""
    s = str(msg)[:ERROR_MAX_LEN * 4]  # work on a bounded prefix
    for pat in _CRED_PATTERNS:
        s = pat.sub(lambda m: m.group(0).split("=")[0] + "=***" if "=" in m.group(0) else "***", s)
    for pat in _PATH_PATTERNS:
        s = pat.sub("/<USER>/", s)
    for pat in _PII_PATTERNS:
        s = pat.sub("<REDACTED>", s)
    return s[:ERROR_MAX_LEN]


def sanitize_cli(cmd) -> str:
    """Keep only the first CLI_MAX_TOKENS shell-style tokens."""
    if cmd is None:
        return ""
    s = str(cmd).strip()[:CLI_MAX_LEN * 4]
    parts = s.split()
    return " ".join(parts[:CLI_MAX_TOKENS])[:CLI_MAX_LEN]


if __name__ == "__main__":
    # Self-tests, run manually with: python3 sanitize.py
    cases_err = [
        ("InvalidAccessKeyId: AccessKey ak=ABC123 not found",
         "InvalidAccessKeyId: AccessKey ak=*** not found"),
        ("Error reading /Users/alice/secret.pem",
         "Error reading /<USER>/secret.pem"),
        ("Send to user@example.com failed",
         "Send to <REDACTED> failed"),
        ("Connection to 192.168.1.1 timeout",
         "Connection to <REDACTED> timeout"),
    ]
    for input_, expected in cases_err:
        got = sanitize_error(input_)
        assert got == expected, f"sanitize_error({input_!r}) = {got!r}, expected {expected!r}"

    cases_cli = [
        ("aliyun ecs DescribeInstances --region cn-hangzhou", "aliyun ecs DescribeInstances"),
        ("aliyun oss ls", "aliyun oss ls"),
        ("aliyun", "aliyun"),
    ]
    for input_, expected in cases_cli:
        got = sanitize_cli(input_)
        assert got == expected, f"sanitize_cli({input_!r}) = {got!r}, expected {expected!r}"

    print("sanitize.py: all self-tests passed")
```

- [ ] **Step 3: Run sanitize self-tests**

Run: `python3 tools/hooks/scripts/lib/sanitize.py`
Expected: `sanitize.py: all self-tests passed`

- [ ] **Step 4: Test detect_client.sh**

```bash
( . tools/hooks/scripts/lib/detect_client.sh
  [ "$(detect_client)" = "claude-code" ] && echo "PASS: default" || echo "FAIL"
  COPILOT_CLI=1 [ "$(COPILOT_CLI=1 bash -c '. tools/hooks/scripts/lib/detect_client.sh; detect_client')" = "copilot-cli" ] && echo "PASS: copilot" || echo "FAIL"
  [ "$(detect_client '{"tool_use_id":"__vscode_1"}')" = "vscode" ] && echo "PASS: vscode" || echo "FAIL"
)
```

Expected: three `PASS:` lines.

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/scripts/lib/detect_client.sh tools/hooks/scripts/lib/sanitize.py
git commit -m "feat: add detect_client and sanitize utilities"
```

---

## Task 7: post_handler.py — skeleton + Skill event + first dry-run pass

**Files:**
- Create: `tools/hooks/scripts/lib/post_handler.py` (initial)
- Create: `tools/hooks/scripts/test-fixtures/claude-code/post-skill-success.json`
- Create: `tools/hooks/scripts/test-fixtures/expected/post-skill-success.txt`

This task brings the harness to its first GREEN. We implement the minimum
needed to handle one event type (Skill invocation), prove the dry-run.sh
pipeline end-to-end, and commit. Subsequent tasks extend.

- [ ] **Step 1: Add fixture for Skill invocation**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-skill-success.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-skill",
  "tool_use_id": "toolu_skill",
  "tool_name": "Skill",
  "tool_input": {
    "skill": "alibabacloud-core:mcp-core-best-practices"
  },
  "tool_response": {
    "status": "Success",
    "is_error": false
  },
  "tool_result": "Loaded best-practices guidance"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-skill-success.txt`:

```
--client-name
claude-code
--event-type
skill_invocation
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Skill
--session-id
test-session-skill
--status
success
--turn
0
--skill-name
alibabacloud-core:mcp-core-best-practices
--plugin-name
alibabacloud-core
```

- [ ] **Step 2: Implement minimal post_handler.py**

Create `tools/hooks/scripts/lib/post_handler.py`:

```python
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


def classify(tool_name: str, tool_input: Any) -> Optional[dict]:
    """Return event seed (event_type, plugin_name, skill_name, etc.) or None."""
    if not tool_name:
        return None

    # Case 1: Skill tool
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
        "skill-name": seed.get("skill_name", ""),
        "plugin-name": seed.get("plugin_name", ""),
    }
    emit(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run dry-run for skill fixture**

Run: `bash tools/hooks/scripts/dry-run.sh post-skill-success`
Expected: `PASS: post-skill-success`

- [ ] **Step 4: Run dry-run for the existing MCP fixture (still expected to FAIL)**

Run: `bash tools/hooks/scripts/dry-run.sh post-mcp-success`
Expected: `FAIL: post-mcp-success` — the handler does not yet classify MCP. Subsequent tasks add support.

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/scripts/lib/post_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/post-skill-success.json \
        tools/hooks/scripts/test-fixtures/expected/post-skill-success.txt
git commit -m "feat: add post_handler skeleton with skill_invocation classification"
```

---

## Task 8: post_handler — MCP, Bash/aliyun, Subagent, Read events

Extend the classifier to cover the remaining event types. Each fixture moves
one more `dry-run.sh` test from FAIL to PASS.

**Files:**
- Modify: `tools/hooks/scripts/lib/post_handler.py` (extend `classify` and `main`)
- Create fixtures + expected:
  - `post-bash-aliyun-success.json`
  - `post-subagent-success.json`
  - `post-read-skill-md.json`
  - `post-read-reference-file.json`

(`post-mcp-success.json` was created in Task 3.)

- [ ] **Step 1: Add bash + aliyun fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-bash-aliyun-success.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-bash",
  "tool_use_id": "toolu_bash",
  "tool_name": "Bash",
  "tool_input": {
    "command": "aliyun ecs DescribeInstances --region cn-hangzhou",
    "description": "List ECS"
  },
  "tool_response": {
    "exit_code": 0,
    "stdout": "{\"RequestId\":\"BASH-REQ-001\",\"Instances\":{\"Instance\":[]}}",
    "stderr": ""
  }
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-bash-aliyun-success.txt`:

```
--client-name
claude-code
--event-type
cli_command_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Bash
--session-id
test-session-bash
--status
success
--turn
0
--tool-request-id
BASH-REQ-001
--cli-command
aliyun ecs DescribeInstances
```

- [ ] **Step 2: Add subagent fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-subagent-success.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-agent",
  "tool_use_id": "toolu_agent",
  "tool_name": "Agent",
  "tool_input": {
    "subagent_type": "alibabacloud-spec-ops:code-quality-reviewer",
    "description": "Review terraform"
  },
  "tool_response": {
    "status": "Success",
    "is_error": false
  },
  "tool_result": "Review complete"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-subagent-success.txt`:

```
--client-name
claude-code
--event-type
subagent_dispatch
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Agent
--session-id
test-session-agent
--status
success
--turn
0
--skill-name
alibabacloud-spec-ops:code-quality-reviewer
--plugin-name
alibabacloud-spec-ops
```

- [ ] **Step 3: Add SKILL.md read fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-read-skill-md.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-readskill",
  "tool_use_id": "toolu_readskill",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/Users/dev/.claude/plugins/cache/alibabacloud-core/1.0.6/skills/mcp-core-best-practices/SKILL.md"
  },
  "tool_response": {
    "status": "Success",
    "is_error": false
  },
  "tool_result": "# Best practices content"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-read-skill-md.txt`:

```
--client-name
claude-code
--event-type
skill_invocation
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Read
--session-id
test-session-readskill
--status
success
--turn
0
--skill-name
mcp-core-best-practices
--plugin-name
alibabacloud-core
```

- [ ] **Step 4: Add reference file read fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-read-reference-file.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-readref",
  "tool_use_id": "toolu_readref",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/Users/dev/.claude/plugins/cache/alibabacloud-core/1.0.6/skills/mcp-core-best-practices/references/recipes/README.md"
  },
  "tool_response": {
    "status": "Success",
    "is_error": false
  },
  "tool_result": "Recipe content"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-read-reference-file.txt`:

```
--client-name
claude-code
--event-type
reference_file_read
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Read
--session-id
test-session-readref
--status
success
--turn
0
--skill-name
mcp-core-best-practices
--plugin-name
alibabacloud-core
--query-summary
read:reference-file
```

- [ ] **Step 5: Extend `classify()` in post_handler.py**

Replace the `classify` function in `tools/hooks/scripts/lib/post_handler.py` with:

```python
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
        m2 = re.search(r"mcp__plugin_(alibabacloud[-_a-z0-9]+)_", tool_name, re.IGNORECASE)
        if m2:
            seed["plugin_name"] = m2.group(1)
        # If MCP CallCLI, lift cli_command
        if isinstance(tool_input, dict):
            cmd = tool_input.get("command", "") or ""
            if cmd:
                seed["cli_command"] = sanitize.sanitize_cli(cmd)
        return seed

    return None
```

- [ ] **Step 6: Extend `main()` to copy classifier output into args**

In `main()`, after `seed = classify(...)`, replace the args-build block with:

```python
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
```

- [ ] **Step 7: Run all dry-run tests**

Run: `bash tools/hooks/scripts/dry-run.sh --all`
Expected: every fixture except `post-mcp-success` passes (request-id and
status detection are still pending — see Tasks 9 and 10). MCP fixture currently
prints `--tool-request-id REQ-ABC-123` from expected, but our handler does not
yet extract it. Note: at this stage `post-mcp-success` may FAIL on missing
`--tool-request-id`. That is intentional — the next two tasks fix it.

- [ ] **Step 8: Commit**

```bash
git add tools/hooks/scripts/lib/post_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/post-bash-aliyun-success.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-subagent-success.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-read-skill-md.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-read-reference-file.json \
        tools/hooks/scripts/test-fixtures/expected/post-bash-aliyun-success.txt \
        tools/hooks/scripts/test-fixtures/expected/post-subagent-success.txt \
        tools/hooks/scripts/test-fixtures/expected/post-read-skill-md.txt \
        tools/hooks/scripts/test-fixtures/expected/post-read-reference-file.txt
git commit -m "feat: classify MCP / Bash-aliyun / Agent / Read events"
```

---

## Task 9: post_handler — RequestId / PopRequestId extraction

**Files:**
- Modify: `tools/hooks/scripts/lib/post_handler.py`

- [ ] **Step 1: Confirm fixtures already specify expected --tool-request-id**

`post-mcp-success.txt` (Task 3) already expects `REQ-ABC-123`.
`post-bash-aliyun-success.txt` (Task 8) already expects `BASH-REQ-001`.

- [ ] **Step 2: Add fixture demonstrating PopRequestId fallback**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-poprequestid.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-poprid",
  "tool_use_id": "toolu_poprid",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": {"status": "Success", "is_error": false},
  "tool_result": "{\"data\":{\"PopRequestId\":\"POP-XYZ-789\"}}"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-mcp-poprequestid.txt`:

```
--client-name
claude-code
--event-type
mcp_tool_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI
--session-id
test-session-poprid
--status
success
--turn
0
--mcp-tool
AlibabaCloud___CallCLI
--plugin-name
alibabacloud-core
--tool-request-id
POP-XYZ-789
--cli-command
aliyun ecs DescribeInstances
```

- [ ] **Step 3: Add `extract_request_id()` to post_handler.py**

Add this helper before `main()`:

```python
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
    return ""
```

- [ ] **Step 4: Wire into `main()`**

In `main()`, just before `args = {...}`, also handle `tool_result` from
Bash's `tool_response.stdout`:

```python
    tool_result = data.get("tool_result", "")
    tool_response = data.get("tool_response") or {}
    if not tool_result and isinstance(tool_response, dict):
        tool_result = tool_response.get("stdout", "") or ""

    request_id = extract_request_id(tool_result)
```

Then add `"tool-request-id": request_id` into the `args` dict (between
`plugin-name` and `cli-command` to match canonical order).

- [ ] **Step 5: Run all dry-run tests**

Run: `bash tools/hooks/scripts/dry-run.sh --all`
Expected: `post-mcp-success`, `post-bash-aliyun-success`, and
`post-mcp-poprequestid` all PASS. (Earlier-passing fixtures still PASS.)

- [ ] **Step 6: Commit**

```bash
git add tools/hooks/scripts/lib/post_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/post-mcp-poprequestid.json \
        tools/hooks/scripts/test-fixtures/expected/post-mcp-poprequestid.txt
git commit -m "feat: extract cloud RequestId/PopRequestId into --tool-request-id"
```

---

## Task 10: post_handler — full status detection + error sanitization

**Files:**
- Modify: `tools/hooks/scripts/lib/post_handler.py` (replace `status = "success"` placeholder)
- Create fixtures + expected:
  - `post-mcp-failure-isError.json`
  - `post-mcp-failure-aliyun-code.json`
  - `post-bash-aliyun-exit1.json`
  - `post-mcp-failure-clienterr.json` (parse fails)

- [ ] **Step 1: Fixtures — failure cases**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-isError.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-iserr",
  "tool_use_id": "toolu_iserr",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": {"status": "Errored", "is_error": true},
  "tool_result": "{\"isError\":true,\"error\":{\"Code\":\"InvalidParameter\",\"Message\":\"region required\"}}"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-isError.txt`:

```
--client-name
claude-code
--event-type
mcp_tool_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI
--session-id
test-session-iserr
--status
failure
--turn
0
--mcp-tool
AlibabaCloud___CallCLI
--plugin-name
alibabacloud-core
--cli-command
aliyun ecs DescribeInstances
--error-message
region required
```

Create `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-aliyun-code.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-aliyuncode",
  "tool_use_id": "toolu_aliyuncode",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": {"status": "Success", "is_error": false},
  "tool_result": "{\"Code\":\"NoPermission\",\"Message\":\"User AK=AK1234567890ABC not authorized\",\"RequestId\":\"REQ-NOPERM\"}"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-aliyun-code.txt`:

```
--client-name
claude-code
--event-type
mcp_tool_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI
--session-id
test-session-aliyuncode
--status
failure
--turn
0
--mcp-tool
AlibabaCloud___CallCLI
--plugin-name
alibabacloud-core
--tool-request-id
REQ-NOPERM
--cli-command
aliyun ecs DescribeInstances
--error-message
User AK=*** not authorized
```

Create `tools/hooks/scripts/test-fixtures/claude-code/post-bash-aliyun-exit1.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-bashfail",
  "tool_use_id": "toolu_bashfail",
  "tool_name": "Bash",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": {
    "exit_code": 1,
    "stdout": "",
    "stderr": "Connection refused"
  }
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-bash-aliyun-exit1.txt`:

```
--client-name
claude-code
--event-type
cli_command_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Bash
--session-id
test-session-bashfail
--status
failure
--turn
0
--cli-command
aliyun ecs DescribeInstances
--error-message
Connection refused
```

Create `tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-clienterr.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-clienterr",
  "tool_use_id": "toolu_clienterr",
  "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
  "tool_input": {"command": "aliyun ecs DescribeInstances"},
  "tool_response": {"status": "Success", "is_error": false},
  "tool_result": "Connection refused: failed to dial tcp 169.254.0.1:443"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-clienterr.txt`:

```
--client-name
claude-code
--event-type
mcp_tool_use
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI
--session-id
test-session-clienterr
--status
failure
--turn
0
--mcp-tool
AlibabaCloud___CallCLI
--plugin-name
alibabacloud-core
--cli-command
aliyun ecs DescribeInstances
--error-message
Connection refused: failed to dial tcp <REDACTED>:443
```

- [ ] **Step 2: Add `detect_status()` to post_handler.py**

Add this helper before `main()`:

```python
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

    # Signal 1: tool_response.is_error / status
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") is True:
            msg = (
                tool_response.get("error")
                or tool_response.get("stderr")
                or "tool_response.is_error=true"
            )
            return "failure", sanitize.sanitize_error(msg)
        if str(tool_response.get("status", "")).lower() == "errored":
            return "failure", sanitize.sanitize_error("tool_response.status=Errored")

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
    tool_result = data.get("tool_result", "")
    if not tool_result and isinstance(tool_response, dict):
        tool_result = tool_response.get("stdout", "") or ""

    if isinstance(tool_result, dict):
        msg = _scan_dict_for_error(tool_result)
        if msg:
            return "failure", sanitize.sanitize_error(msg)
        return "success", ""

    if isinstance(tool_result, str) and tool_result:
        head = tool_result[:JSON_PARSE_WINDOW]
        parsed = None
        try:
            parsed = json.loads(head)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            msg = _scan_dict_for_error(parsed)
            if msg:
                return "failure", sanitize.sanitize_error(msg)
            # Aliyun OpenAPI error code regex on the parsed text
            if ALIYUN_ERROR_CODES_RE.search(head[:ERROR_REGEX_WINDOW]):
                return "failure", sanitize.sanitize_error(head.split("\n", 1)[0])
            return "success", ""
        # JSON parse failed — client error keyword check
        if CLIENT_ERROR_RE.search(tool_result[:ERROR_REGEX_WINDOW]):
            first_line = tool_result.split("\n", 1)[0]
            return "failure", sanitize.sanitize_error(first_line)

    return "success", ""
```

- [ ] **Step 3: Wire into `main()`**

Replace the `status = "success"` line with:

```python
    status, error_message = detect_status(data)
```

And in `args = {...}`, add `"error-message": error_message`.

- [ ] **Step 4: Run all dry-run tests**

Run: `bash tools/hooks/scripts/dry-run.sh --all`
Expected: every fixture passes.

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/scripts/lib/post_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-isError.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-aliyun-code.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-bash-aliyun-exit1.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-mcp-failure-clienterr.json \
        tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-isError.txt \
        tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-aliyun-code.txt \
        tools/hooks/scripts/test-fixtures/expected/post-bash-aliyun-exit1.txt \
        tools/hooks/scripts/test-fixtures/expected/post-mcp-failure-clienterr.txt
git commit -m "feat: 4-signal status detection with sanitized error messages"
```

---

## Task 11: post_handler — start fallback fixture + huge-response safety

**Files:**
- Create fixtures + expected:
  - `post-no-pre-fallback.json` (no `.start` companion → start_ts fallback)
  - `post-huge-response-10mb.json` (giant tool_result, must not block)
- Modify: `tools/hooks/scripts/dry-run.sh` to set a per-test timeout

- [ ] **Step 1: Fallback fixture**

Create `tools/hooks/scripts/test-fixtures/claude-code/post-no-pre-fallback.json`:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "test-session-fallback",
  "tool_use_id": "toolu_fb",
  "tool_name": "Skill",
  "tool_input": {"skill": "alibabacloud-core:mcp-core-best-practices"},
  "tool_response": {"status": "Success", "is_error": false},
  "tool_result": "OK"
}
```

Create `tools/hooks/scripts/test-fixtures/expected/post-no-pre-fallback.txt`:

```
--client-name
claude-code
--event-type
skill_invocation
--start-timestamp
<TS>
--end-timestamp
<TS>
--tool-name
Skill
--session-id
test-session-fallback
--status
success
--turn
0
--skill-name
alibabacloud-core:mcp-core-best-practices
--plugin-name
alibabacloud-core
--query-summary
start-fallback
```

- [ ] **Step 2: Update fallback path in post_handler.py**

In `main()`, change the start_ms fallback handling to also set a marker:

```python
    start_ms = read_start_ts(sd, session_id, tool_name)
    end_ms = int(time.time() * 1000)
    fallback_used = start_ms is None
    if fallback_used:
        start_ms = end_ms - 1
```

Then after building `args`, append the fallback marker only when no
`query_summary` already came from the classifier:

```python
    if fallback_used and not args.get("query-summary"):
        args["query-summary"] = "start-fallback"
```

- [ ] **Step 3: Huge-response fixture**

Generate `tools/hooks/scripts/test-fixtures/claude-code/post-huge-response-10mb.json`:

```bash
python3 - <<'PY'
import json
big = "x" * (10 * 1024 * 1024)
payload = {
    "hook_event_name": "PostToolUse",
    "session_id": "test-session-huge",
    "tool_use_id": "toolu_huge",
    "tool_name": "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI",
    "tool_input": {"command": "aliyun oss ls"},
    "tool_response": {"status": "Success", "is_error": False},
    "tool_result": '{"RequestId":"HUGE-REQ","data":"' + big + '"}',
}
with open("tools/hooks/scripts/test-fixtures/claude-code/post-huge-response-10mb.json", "w") as f:
    json.dump(payload, f)
PY
```

For this fixture we only assert that the handler **completes within 5 seconds**.
Output may vary based on stdin truncation. Create
`tools/hooks/scripts/test-fixtures/expected/post-huge-response-10mb.txt`:

```
TIMING_ONLY
```

- [ ] **Step 4: Update dry-run.sh to honor TIMING_ONLY**

In `dry-run.sh`, after computing `actualNorm`, before the diff, add:

```bash
    if [ "$(cat "$expected")" = "TIMING_ONLY" ]; then
        # We only assert the handler completes within 5 seconds
        # (already enforced by `timeout 5` below). Skip diff.
        echo "PASS: $stem (timing-only)"
        return 0
    fi
```

And wrap the python invocation with `timeout 5`:

```bash
    actual=$(ALIBABACLOUD_TELEMETRY_STATE_DIR="$stateDir" \
             ALIBABACLOUD_TELEMETRY_DRY_RUN=1 \
             timeout 5 python3 "$handler" < "$fixture" 2>/dev/null) || {
        echo "FAIL: $stem (handler exited non-zero or timed out)"
        return 1
    }
```

- [ ] **Step 5: Run all tests**

Run: `bash tools/hooks/scripts/dry-run.sh --all`
Expected: every fixture (including huge-response) passes.

- [ ] **Step 6: Commit**

```bash
git add tools/hooks/scripts/dry-run.sh \
        tools/hooks/scripts/lib/post_handler.py \
        tools/hooks/scripts/test-fixtures/claude-code/post-no-pre-fallback.json \
        tools/hooks/scripts/test-fixtures/claude-code/post-huge-response-10mb.json \
        tools/hooks/scripts/test-fixtures/expected/post-no-pre-fallback.txt \
        tools/hooks/scripts/test-fixtures/expected/post-huge-response-10mb.txt
git commit -m "feat: start-timestamp fallback marker and huge-response timing test"
```

---

## Task 12: post-tool-trace.sh wrapper + fire-and-forget upload

**Files:**
- Create: `tools/hooks/scripts/post-tool-trace.sh`

- [ ] **Step 1: Implement bash wrapper**

Create `tools/hooks/scripts/post-tool-trace.sh`:

```bash
#!/bin/bash
# Post-tool-use hook wrapper. Delegates classification + status detection to
# lib/post_handler.py, then fires `uvx alibabacloud.mcp-proxy@latest
# plugin-telemetry` in the background. Always returns success to the agent.
set +e

return_success() {
    echo '{"continue":true}'
    exit 0
}

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    return_success
fi

if [ -t 0 ]; then
    return_success
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"

# Buffer stdin so the python handler can read it. Cap at 64 KB to avoid
# bash variable bloat on huge tool_results.
payload=$(head -c 65536)

# Run handler — outputs alternating --key / value lines on success
mapfile -t lines < <(echo -n "$payload" | python3 "$scriptDir/lib/post_handler.py" 2>/dev/null)
rc=$?

if [ "$rc" -ne 0 ] || [ "${#lines[@]}" -eq 0 ]; then
    return_success
fi

# Build argv array (preserves quoting, no eval)
args=()
for line in "${lines[@]}"; do
    args+=("$line")
done

# Dry-run mode: log instead of upload
if [ "${ALIBABACLOUD_TELEMETRY_DRY_RUN}" = "1" ]; then
    stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    mkdir -p "$stateDir" 2>/dev/null
    {
        printf 'DRYRUN: uvx alibabacloud.mcp-proxy@latest plugin-telemetry'
        for a in "${args[@]}"; do
            printf ' %q' "$a"
        done
        printf '\n'
    } >> "$stateDir/debug.log" 2>/dev/null
    return_success
fi

# Fire-and-forget: detach so the agent loop never waits on uvx.
( uvx alibabacloud.mcp-proxy@latest plugin-telemetry "${args[@]}" \
    >/dev/null 2>&1 < /dev/null & ) >/dev/null 2>&1
disown 2>/dev/null

return_success
```

Make executable: `chmod +x tools/hooks/scripts/post-tool-trace.sh`

- [ ] **Step 2: Smoke test the bash wrapper end-to-end (dry-run mode)**

```bash
stateDir=$(mktemp -d)
ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
ALIBABACLOUD_TELEMETRY_DRY_RUN=1 \
    bash tools/hooks/scripts/post-tool-trace.sh \
    < tools/hooks/scripts/test-fixtures/claude-code/post-skill-success.json
grep -q "^DRYRUN: uvx alibabacloud.mcp-proxy@latest plugin-telemetry --client-name claude-code --event-type skill_invocation" "$stateDir/debug.log" \
    && echo PASS || echo FAIL
```

Expected: `PASS`.

- [ ] **Step 3: Verify opt-out short-circuits**

```bash
ALIBABACLOUD_TELEMETRY=false \
    timeout 1 bash tools/hooks/scripts/post-tool-trace.sh < /dev/null
echo "Exit: $?"
```

Expected: `Exit: 0` within milliseconds.

- [ ] **Step 4: Commit**

```bash
git add tools/hooks/scripts/post-tool-trace.sh
chmod +x tools/hooks/scripts/post-tool-trace.sh
git commit -m "feat: post-tool-trace bash wrapper with fire-and-forget upload"
```

---

## Task 13: Plugin symlinks + hooks.json + codex placeholder

**Files:**
- Create: `tools/hooks/hooks.json`
- Create: `tools/hooks/codex-hooks.json`
- Create: symlinks `plugins/{alibabacloud-core,alibabacloud-agent,alibabacloud-data-analytics}/hooks → ../../tools/hooks`

- [ ] **Step 1: Write Claude Code hooks.json**

Create `tools/hooks/hooks.json`:

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

- [ ] **Step 2: Write codex-hooks.json placeholder**

Create `tools/hooks/codex-hooks.json`:

```json
{
  "_comment": "TODO Phase 2: Codex hook registration. Codex hook payload format and lifecycle event names differ from Claude Code; this file is intentionally inert until Codex client support is implemented. Track scope here so Phase 2 only needs to fill in this file.",
  "_phase2_todo": [
    "Activate CODEX_CLI=1 branch in lib/detect_client.sh",
    "Add codex-specific event-name → tool-name mapping in lib/post_handler.py classify()",
    "Update tools/hooks/README.md to mention Codex support"
  ]
}
```

- [ ] **Step 3: Create symlinks**

```bash
cd /Users/caihe/projects/github-personal/alibabacloud-agent-toolkit

ln -s ../../tools/hooks plugins/alibabacloud-core/hooks
ln -s ../../tools/hooks plugins/alibabacloud-agent/hooks
ln -s ../../tools/hooks plugins/alibabacloud-data-analytics/hooks

# Make sure git records them as symlinks
git config core.symlinks true
```

- [ ] **Step 4: Verify symlinks resolve**

Run: `bash tools/hooks/scripts/verify-symlinks.sh`
Expected:

```
PASS: alibabacloud-core/hooks → tools/hooks
PASS: alibabacloud-agent/hooks → tools/hooks
PASS: alibabacloud-data-analytics/hooks → tools/hooks
```

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/hooks.json tools/hooks/codex-hooks.json
git add plugins/alibabacloud-core/hooks plugins/alibabacloud-agent/hooks plugins/alibabacloud-data-analytics/hooks
git commit -m "feat: register Claude Code hooks and symlink plugins to tools/hooks"
```

---

## Task 14: GitHub Actions CI

**Files:**
- Create: `.github/workflows/verify-hooks.yml`

- [ ] **Step 1: Write workflow**

Create `.github/workflows/verify-hooks.yml`:

```yaml
name: verify-hooks

on:
  pull_request:
    paths:
      - "tools/hooks/**"
      - "plugins/*/hooks"
      - ".github/workflows/verify-hooks.yml"
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          # Preserve symlinks
          fetch-depth: 1
      - name: Configure git symlinks
        run: git config --global core.symlinks true
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Verify symlinks
        run: bash tools/hooks/scripts/verify-symlinks.sh
      - name: Run sanitize self-tests
        run: python3 tools/hooks/scripts/lib/sanitize.py
      - name: Run dry-run fixtures
        run: bash tools/hooks/scripts/dry-run.sh --all
      - name: Smoke-test post-tool-trace.sh wrapper
        run: |
          stateDir=$(mktemp -d)
          ALIBABACLOUD_TELEMETRY_STATE_DIR=$stateDir \
          ALIBABACLOUD_TELEMETRY_DRY_RUN=1 \
            bash tools/hooks/scripts/post-tool-trace.sh \
            < tools/hooks/scripts/test-fixtures/claude-code/post-skill-success.json
          grep -q "^DRYRUN: uvx alibabacloud.mcp-proxy@latest plugin-telemetry --client-name claude-code --event-type skill_invocation" \
            "$stateDir/debug.log"
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/verify-hooks.yml
git commit -m "ci: add verify-hooks workflow"
```

- [ ] **Step 3: Push branch and open PR**

```bash
git push -u origin telemetry-plugin
# Open PR via GitHub UI or `gh pr create`
```

---

## Acceptance Criteria (mirrors spec)

After all 14 tasks:

- [ ] `tools/hooks/` exists with all scripts, `hooks.json`, `README.md`
- [ ] Three `plugins/*/hooks` symlinks resolve to `tools/hooks`
- [ ] `bash tools/hooks/scripts/verify-symlinks.sh` exits 0 with three PASS lines
- [ ] `bash tools/hooks/scripts/dry-run.sh --all` reports PASS for every fixture
- [ ] HITL script and HITL hook entry are absent
- [ ] No HTTP curl POST or `events.jsonl` write remains
- [ ] `ALIBABACLOUD_TELEMETRY=false bash tools/hooks/scripts/post-tool-trace.sh < /dev/null` returns within 100 ms
- [ ] Every emitted event includes `--start-timestamp` and `--end-timestamp` (with fallback marker for missing pre)
- [ ] Every `failure` event includes `--error-message` after sanitization
- [ ] `.github/workflows/verify-hooks.yml` runs on PRs touching `tools/hooks/**` or `plugins/*/hooks`

---

## Self-Review Checklist (filled out)

**Spec coverage:**

| Spec section | Implementing task |
|--------------|-------------------|
| File structure (canonical + symlinks) | Tasks 1, 13 |
| Privacy README + env vars | Task 2 |
| Test harness (dry-run + verify-symlinks) | Task 3, 11 |
| Hook lifecycle (Pre/Post/Stop) | Tasks 4, 5, 12, 13 |
| Event matrix (Skill, Read SKILL.md, Read ref, Agent, Bash aliyun, MCP) | Tasks 7, 8 |
| `--plugin-name` resolution | Tasks 7, 8 |
| Status detection (4 signals) | Task 10 |
| Error message sanitization | Task 6 (utility) + Task 10 (wiring) |
| `--tool-request-id` extraction | Task 9 |
| `--start-timestamp` fallback | Task 11 |
| Upload (`uvx ... plugin-telemetry` fire-and-forget) | Task 12 |
| Client detection (Phase 1 = claude-code only) | Task 6 (utility) + Task 7 (wiring) |
| Phase 2 codex placeholder | Task 13 |
| CI workflow | Task 14 |

**Placeholder scan:** every task contains real code blocks; "TODO Phase 2"
markers are intentional design decisions, not unresolved spec gaps.

**Type / name consistency:** `args` keys use kebab-case (`tool-request-id`)
matching `telemetry_design.md` flag names. `seed` keys use snake_case
(`tool_request_id`) internally. The `emit()` order list and the `args` dict
literals use the same key set in Tasks 7, 8, 9, 10. `state_dir()`,
`detect_client()`, `read_start_ts()`, `read_turn()`, `extract_request_id()`,
`detect_status()` are referenced consistently. `sanitize.sanitize_error` and
`sanitize.sanitize_cli` import paths match the file we create in Task 6.
