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
