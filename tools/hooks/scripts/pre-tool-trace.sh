#!/bin/bash
# Pre-tool-use hook wrapper. Delegates to lib/pre_handler.py.
# Always exits 0 to avoid blocking the agent.
set +e

debug_log() {
    [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ] || return 0
    local stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    mkdir -p "$stateDir" 2>/dev/null
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$stateDir/debug.log" 2>/dev/null
}

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    debug_log "decision=opted-out (pre)"
    exit 0
fi

if [ -t 0 ]; then
    debug_log "decision=no-stdin (pre)"
    exit 0
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"

if [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ]; then
    stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    mkdir -p "$stateDir" 2>/dev/null
    python3 "$scriptDir/lib/pre_handler.py" >/dev/null 2>>"$stateDir/debug.log" || true
else
    python3 "$scriptDir/lib/pre_handler.py" >/dev/null 2>&1 || true
fi

exit 0
