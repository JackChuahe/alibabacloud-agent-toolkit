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
