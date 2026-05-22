# alibabacloud-spec-ops

Alibaba Cloud AI Ops plugin — an end-to-end infrastructure operations workflow
covering intelligent planning, code generation, validation, and execution.

This plugin includes:

- Plugin manifests for Codex and Claude Code
- An MCP server named `alibabacloud-spec-ops` for IaC and OpenAPI access
- Skills for the spec-ops workflow (planning → writing → validating → executing)
- Specialist subagents for spec compliance and code-quality review
- A RAM permission diagnosis skill for triaging Alibaba Cloud authorization errors

## Install

### Claude Code

```text
/plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
/plugin install alibabacloud-spec-ops@alibabacloud-agent-toolkit
/reload-plugins
```

### Codex

```text
codex plugin marketplace add acloudlabs-unofficial/alibabacloud-agent-toolkit
```

Then launch Codex and install the `alibabacloud-spec-ops` plugin from `/plugins`.

## MCP

This plugin configures an MCP server named `alibabacloud-spec-ops` without a
safety policy, allowing access to all Alibaba Cloud CLI commands. For
production environments, configure a safety policy to restrict the callable
command set:

```json
{
  "mcpServers": {
    "alibabacloud-spec-ops": {
      "command": "uvx",
      "args": [
        "alibabacloud.mcp-proxy@latest",
        "--safety-policy",
        "iacservice:*=allow,ecs:*=allow,vpc:*=allow,*=deny"
      ]
    }
  }
}
```

The server is named distinctly from `alibabacloud-core` to avoid namespace
collision when both plugins are installed simultaneously.

## Skills

| Skill | Description |
|-------|-------------|
| `alibabacloud-planning` | Clarify requirements and design Alibaba Cloud architectures (Day-1 / Day-2) |
| `alibabacloud-writing-plans` | Convert approved designs into Terraform HCL via the codegen skill |
| `alibabacloud-terraform-codegen` | Generate and modify Alibaba Cloud Terraform HCL code |
| `alibabacloud-validate` | Dual review (spec compliance + code quality) plus remote syntax validation |
| `alibabacloud-executing-plans` | Execute validated Terraform plans through Alibaba Cloud IaC Service |
| `alibabacloud-ram-permission-diagnose` | Diagnose and repair RAM permission errors (403 / NoPermission / etc.) |

## Agents

| Agent | Purpose |
|-------|---------|
| `spec-reviewer` | Verify generated Terraform implements every requirement in `design.md` |
| `code-quality-reviewer` | Evaluate Terraform for quality, security, and best practices |

Both agents are dispatched in parallel by `alibabacloud-validate`.

## Hooks

Telemetry and local trace hooks live at [`./hooks/`](./hooks/) as a real
directory (no symlinks). The implementation is byte-identical to the canonical
copy in
[`plugins/alibabacloud-core/hooks/`](../alibabacloud-core/hooks/), which is
the source of truth across the toolkit. See
[`./hooks/README.md`](./hooks/README.md) for the full event reference,
file structure, and the rationale behind this convention.
