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
