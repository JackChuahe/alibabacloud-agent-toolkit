#!/bin/bash
# Stop hook — increments the per-session turn counter at end of agent turn.
# Turn number is consumed by post-tool-trace.sh to tag --turn on each event.
# Also bound to StopFailure for symmetry; both paths log identically.
# Delegates to lib/stop_handler.py which uses fcntl-locked per-session state.
set +e

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    exit 0
fi

if [ -t 0 ]; then
    # No piped stdin (e.g. manual run from terminal) — nothing to do.
    exit 0
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"

# Resolve client (mirrors detect_client_bash in pre/post wrappers) so the
# debug log lands in the right per-client bucket. Payload is read from
# stdin once and passed to python; sniff a small prefix here for client
# detection without consuming stdin twice.
detect_client_bash() {
    if [ "$COPILOT_CLI" = "1" ]; then echo "copilot-cli"; return; fi
    if [ "$CODEX_CLI" = "1" ]; then echo "codex"; return; fi
    if [ "$QODER_WORK" = "1" ]; then echo "qoderwork"; return; fi
    case "${1:-}" in *__vscode*) echo "vscode"; return ;; esac
    echo "claude-code"
}

state_dir_for_client() {
    local base="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    if mkdir -p "$base" 2>/dev/null && touch "$base/.probe" 2>/dev/null; then
        rm -f "$base/.probe"
    else
        local uid
        uid=$(id -u 2>/dev/null || echo 0)
        base="/tmp/alibabacloud-agent-toolkit-telemetry-$uid"
        mkdir -p "$base" 2>/dev/null
    fi
    local client="${1:-claude-code}"
    local safe_client
    safe_client=$(printf '%s' "$client" | LC_ALL=C tr -c 'A-Za-z0-9_-' '_' | head -c 64)
    local cdir="$base/$safe_client"
    mkdir -p "$cdir" 2>/dev/null
    printf '%s' "$cdir"
}

# Buffer stdin so we can sniff client and forward to python.
payload=$(head -c 65536)

client=$(detect_client_bash "$payload")

if [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ]; then
    cdir=$(state_dir_for_client "$client")
    printf '%s' "$payload" | python3 "$scriptDir/lib/stop_handler.py" 2>>"$cdir/debug.log"
else
    printf '%s' "$payload" | python3 "$scriptDir/lib/stop_handler.py" 2>/dev/null
fi

exit 0
