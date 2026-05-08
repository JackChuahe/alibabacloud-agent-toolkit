# alibabacloud-core

The primary plugin scaffold for the Alibaba Cloud Agent Toolkit.

This plugin currently includes:

- Plugin manifests for Codex and Claude Code
- An MCP configuration placeholder
- An empty `skills/` directory for future Alibaba Cloud core skills

## Install

### Claude Code

```text
/plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
/plugin install alibabacloud-core@alibabacloud-agent-toolkit
/reload-plugins
```

### Codex

```text
codex plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
```

Then launch Codex and install the `alibabacloud-core` plugin from `/plugins`.

## Status

This plugin is a scaffold only. Final Alibaba Cloud skills and MCP server definitions have not been added yet.
