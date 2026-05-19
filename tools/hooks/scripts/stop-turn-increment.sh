#!/bin/bash
# Stop hook — increments the per-session turn counter at end of agent turn.
# Turn number is consumed by post-tool-trace.sh to tag --turn on each event.
# Also bound to StopFailure for symmetry; both paths log identically.
set +e

debug_log() {
    [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ] || return 0
    local stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    mkdir -p "$stateDir" 2>/dev/null
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$stateDir/debug.log" 2>/dev/null
}

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    debug_log "decision=opted-out (stop)"
    exit 0
fi

stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
mkdir -p "$stateDir" 2>/dev/null || stateDir="/tmp/alibabacloud-agent-toolkit-telemetry"
mkdir -p "$stateDir" 2>/dev/null

turnFile="$stateDir/turn"
if [ -f "$turnFile" ]; then
    current=$(cat "$turnFile" 2>/dev/null)
    newTurn=$(( ${current:-0} + 1 ))
    echo "$newTurn" > "$turnFile" 2>/dev/null
else
    newTurn=1
    echo "1" > "$turnFile" 2>/dev/null
fi

debug_log "[stop] turn=${newTurn} (post-increment)"

exit 0
