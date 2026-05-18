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
    trap 'rm -rf "$stateDir"' RETURN

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
