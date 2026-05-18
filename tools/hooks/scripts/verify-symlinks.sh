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
