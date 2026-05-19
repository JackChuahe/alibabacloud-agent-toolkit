#!/bin/bash
# Post-tool-use hook wrapper. Delegates classification + status detection to
# lib/post_handler.py, then fires `uvx alibabacloud.mcp-proxy@latest
# plugin-telemetry` in the background. Always returns success to the agent.
set +e

return_success() {
    echo '{"continue":true}'
    exit 0
}

debug_log() {
    [ "${ALIBABACLOUD_TELEMETRY_DEBUG}" = "1" ] || return 0
    local stateDir="${ALIBABACLOUD_TELEMETRY_STATE_DIR:-$HOME/.cache/alibabacloud-agent-toolkit/telemetry}"
    mkdir -p "$stateDir" 2>/dev/null
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$stateDir/debug.log" 2>/dev/null
}

# Extract --<key> value from a flat key/value args array. Bash 3.2-safe.
extract_arg() {
    local target="$1"; shift
    local prev=""
    for a in "$@"; do
        if [ "$prev" = "$target" ]; then echo "$a"; return 0; fi
        prev="$a"
    done
}

if [ "${ALIBABACLOUD_TELEMETRY}" = "false" ]; then
    debug_log "decision=opted-out"
    return_success
fi

if [ -t 0 ]; then
    debug_log "decision=no-stdin"
    return_success
fi

scriptDir="$(cd "$(dirname "$0")" && pwd)"

# Buffer stdin so the python handler can read it. Cap at 64 KB to avoid
# bash variable bloat on huge tool_results.
payload=$(head -c 65536)

# Run handler — outputs alternating --key / value lines on success.
# Capture stdout in a variable (avoids bash 3.2 PIPESTATUS quirks with
# process substitution). Empty output means the event was filtered.
output=$(printf '%s' "$payload" | python3 "$scriptDir/lib/post_handler.py" 2>/dev/null)
rc=$?

if [ "$rc" -ne 0 ] || [ -z "$output" ]; then
    debug_log "decision=filtered tool_name=$(printf '%s' "$payload" | head -c 200 | tr '\n' ' ')"
    return_success
fi

# Split output into lines preserving each whole line as one arg.
# Use a while-read loop instead of `mapfile` so this works on bash 3.2 (macOS).
lines=()
while IFS= read -r line; do
    lines+=("$line")
done <<< "$output"

if [ "${#lines[@]}" -eq 0 ]; then
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
    debug_log "decision=dryrun event=$(extract_arg --event-type "${args[@]}") tool=$(extract_arg --tool-name "${args[@]}")"
    return_success
fi

# Fire-and-forget: detach so the agent loop never waits on uvx.
debug_log "decision=upload event=$(extract_arg --event-type "${args[@]}") tool=$(extract_arg --tool-name "${args[@]}")"
( uvx alibabacloud.mcp-proxy@latest plugin-telemetry "${args[@]}" \
    >/dev/null 2>&1 < /dev/null & ) >/dev/null 2>&1
disown 2>/dev/null

return_success
