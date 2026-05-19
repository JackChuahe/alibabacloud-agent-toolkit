#!/bin/bash
# Pre-tool-use hook wrapper. Delegates to lib/pre_handler.py.
# Always exits 0 to avoid blocking the agent.
set +e

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

debug_log() {
    [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ] || return 0
    local cdir="$1"
    local msg="$2"
    [ -n "$cdir" ] || return 0
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" >> "$cdir/debug.log" 2>/dev/null
}

clientGuess=$(detect_client_bash "")
cdirGuess=$(state_dir_for_client "$clientGuess")

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    debug_log "$cdirGuess" "decision=opted-out (pre)"
    exit 0
fi

if [ -t 0 ]; then
    debug_log "$cdirGuess" "decision=no-stdin (pre)"
    exit 0
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"

# Buffer stdin so we can sniff client and forward to python.
payload=$(head -c 65536)
client=$(detect_client_bash "$payload")
cdir=$(state_dir_for_client "$client")

if [ "${ALIBABACLOUD_TELEMETRY_TRACE_PAYLOAD}" = "1" ]; then
    payloadDir="$cdir/raw-payloads"
    mkdir -p "$payloadDir" 2>/dev/null
    ts=$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null)
    fname="$payloadDir/pre-${ts}-$$.json"
    printf '%s' "$payload" > "$fname" 2>/dev/null
fi

if [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ]; then
    printf '%s' "$payload" | python3 "$scriptDir/lib/pre_handler.py" >/dev/null 2>>"$cdir/debug.log" || true
else
    printf '%s' "$payload" | python3 "$scriptDir/lib/pre_handler.py" >/dev/null 2>&1 || true
fi

exit 0
