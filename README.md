# Alibaba Cloud Agent Toolkit

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Build](https://github.com/acloudlabs-unofficial/alibabacloud-agent-toolkit/actions/workflows/build.yml/badge.svg)](https://github.com/acloudlabs-unofficial/alibabacloud-agent-toolkit/actions/workflows/build.yml)
[![Status](https://img.shields.io/badge/status-initializing-yellow.svg)](#current-status)

Help AI coding agents build, deploy, and operate applications on Alibaba Cloud.

This repository provides Alibaba Cloud agent plugins, skills, MCP configuration, and validation tooling.

## Current Status

The repository currently provides:

- A top-level project scaffold for marketplace manifests, validation, CI, rules, and shared skills.
- One active plugin: [`alibabacloud-core`](plugins/alibabacloud-core/).
- Placeholder plugin directories for future agent and data analytics plugins.

The `alibabacloud-core` plugin includes an SDK usage skill that generates Alibaba Cloud OpenAPI interaction code through a constrained MCP server.

## Repository Layout

```text
.
├── plugins/
│   ├── alibabacloud-core/
│   ├── alibabacloud-agent/
│   └── alibabacloud-data-analytics/
├── rules/
├── skills/
└── tools/
```

## Plugins

| Plugin | Status | Description |
|--------|--------|-------------|
| [alibabacloud-core](plugins/alibabacloud-core/) | Active | Alibaba Cloud OpenAPI SDK code generation using the local `alibabacloud-core` MCP server. |
| `alibabacloud-agent` | Placeholder | Reserved for future agent-focused capabilities. |
| `alibabacloud-data-analytics` | Placeholder | Reserved for future analytics and data workflow capabilities. |

## Install `alibabacloud-core`

### Codex

```text
codex plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
```

Then open Codex `/plugins` and install `alibabacloud-core`.

### Claude Code

```text
/plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
/plugin install alibabacloud-core@alibabacloud-agent-toolkit
/reload-plugins
```

## MCP Safety

The plugin defines an MCP server named `alibabacloud-core` with this policy:

```text
openapiexplorer:*=allow,*=deny
```

The SDK skill is restricted to `mcp__alibabacloud-core__AlibabaCloud___CallCLI`, so OpenAPI Explorer metadata is queried through the configured MCP server instead of unrestricted shell execution.

## Skills

The top-level [`skills/`](skills/) directory is initialized for future shared Alibaba Cloud skills. Category directories are present as placeholders only.

## Rules

Recommended agent guidance lives in [`rules/`](rules/). The initial rules file is Alibaba Cloud oriented and intentionally generic until the first concrete workflows are added.

## Validation

This repository keeps the validation and CI skeleton from the reference toolkit structure.

```bash
mise run lint
mise run validate
```

## License

This project is licensed under the Apache-2.0 License. See [LICENSE](LICENSE) for details.
