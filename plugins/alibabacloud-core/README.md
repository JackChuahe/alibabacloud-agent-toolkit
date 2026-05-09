# alibabacloud-core

The primary Alibaba Cloud plugin for OpenAPI SDK code generation.

This plugin currently includes:

- Plugin manifests for Codex and Claude Code
- An SDK usage skill for generating Alibaba Cloud OpenAPI interaction code
- An MCP server named `alibabacloud-core` constrained to OpenAPI Explorer calls

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

## MCP

This plugin configures an MCP server named `alibabacloud-core` with the safety
policy `openapiexplorer:*=allow,*=deny`. The SDK usage skill only calls tools
from that MCP server, so command allow/deny policy stays centralized there.
