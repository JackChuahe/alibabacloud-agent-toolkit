# Alibaba Cloud Agent Toolkit

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Build](https://github.com/acloudlabs-unofficial/alibabacloud-agent-toolkit/actions/workflows/build.yml/badge.svg)](https://github.com/acloudlabs-unofficial/alibabacloud-agent-toolkit/actions/workflows/build.yml)
[![Status](https://img.shields.io/badge/status-initializing-yellow.svg)](#current-status)

Help AI coding agents build, deploy, and operate applications on Alibaba Cloud.

This repository is initialized from a reference agent-toolkit structure, but reduced to a minimal Alibaba Cloud scaffold so it can evolve with Alibaba Cloud specific skills, plugins, and guidance.

## Current Status

The repository currently provides:

- A top-level project scaffold for marketplace manifests, validation, CI, rules, and shared skills.
- One active plugin scaffold: [`alibabacloud-core`](plugins/alibabacloud-core/).
- Placeholder plugin directories for future agent and data analytics plugins.

The repository does not yet include finalized Alibaba Cloud skills or MCP server integration.

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
| [alibabacloud-core](plugins/alibabacloud-core/) | Scaffolded | Core Alibaba Cloud plugin metadata, MCP config placeholder, and skill directory scaffold. |
| `alibabacloud-agent` | Placeholder | Reserved for future agent-focused capabilities. |
| `alibabacloud-data-analytics` | Placeholder | Reserved for future analytics and data workflow capabilities. |

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
