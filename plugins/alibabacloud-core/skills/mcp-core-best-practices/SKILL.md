---
name: mcp-core-best-practices
description: >
  Shared reference for using Alibaba Cloud OpenAPI MCP Server Core effectively.
  Covers tool usage patterns, API exploration workflow, CLI command generation,
  cross-account access, and safety policy configuration. Referenced by other
  alibabacloud-core skills as the canonical guide for MCP Core interactions.
allowed-tools: "mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___CallCLI,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___SearchApis,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___GetApiDefinition,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___ListApis,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___ListProductRegions,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___GenerateCLICommand,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___ListProducts,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___SearchDocument,mcp__plugin_alibabacloud-core_alibabacloud-core__AlibabaCloud___ReadDocument"
---

# Alibaba Cloud MCP Core Best Practices

This skill documents the canonical patterns for using the `alibabacloud-core` MCP
server — the generalized OpenAPI MCP Server Core that covers all Alibaba Cloud
APIs without requiring pre-selection of specific operations.

## Available Tools

| Tool | Purpose |
|------|---------|
| `AlibabaCloud___SearchApis` | Natural language search for APIs matching a requirement |
| `AlibabaCloud___CallCLI` | Execute a single CLI command remotely |
| `AlibabaCloud___GetApiDefinition` | Get full API definition (params, response, errors) by product/version/name |
| `AlibabaCloud___ListApis` | List all APIs for a product, optionally filtered |
| `AlibabaCloud___ListProductRegions` | List regions where a product is available |
| `AlibabaCloud___GenerateCLICommand` | Generate a CLI command from API definition + parameters |
| `AlibabaCloud___ListProducts` | List all Alibaba Cloud products |
| `AlibabaCloud___SearchDocument` | Search Alibaba Cloud documentation by keyword |
| `AlibabaCloud___ReadDocument` | Read a specific documentation page by URL |

## Standard Workflow

### 1. API Discovery

When the target API is unknown, use `AlibabaCloud___SearchApis` with a natural
language description of the requirement. Each query should be granular enough to
map to a single API call.

For known products, use `AlibabaCloud___ListApis` with a filter keyword to browse
available operations.

### 2. API Inspection

Once the target API is identified, use `AlibabaCloud___GetApiDefinition` to
retrieve the full definition including:

- Required and optional parameters
- Request/response schemas
- Authentication requirements
- Error codes

### 3. Command Generation

Use `AlibabaCloud___GenerateCLICommand` to produce a correct CLI command from the
API definition and user-provided parameters. This avoids manual CLI syntax errors.

### 4. Execution

Use `AlibabaCloud___CallCLI` to execute the generated command. Key constraints:

- Commands must start with `aliyun`
- No shell pipes, redirections, or operators
- No shell variables or command substitution
- No local file path references (MCP server is remote)

### 5. Cross-Account Execution

For Resource Directory member accounts, pass additional parameters to
`AlibabaCloud___CallCLI`:

| Parameter | Usage |
|-----------|-------|
| `x_assume_account_id` | Target member account UID |
| `x_assume_role_name` | Custom role name (default: `ResourceDirectoryAccountAccessRole`) |
| `x_assume_role_arn` | Full role ARN (highest priority) |

Priority: `x_assume_role_arn` > `x_assume_account_id` + `x_assume_role_name` >
default configuration.

## CLI Command Constraints

When using `AlibabaCloud___CallCLI`, the following are NOT supported:

- Bash/zsh pipes (`|`) or shell operators
- `grep`, `awk`, `sed`, or other shell tools
- Shell redirection (`>`, `>>`, `<`)
- Command substitution (`$()`)
- Shell variables or environment variables
- Local file paths (`file://`, `fileb://`)

For commands that need local file access (e.g., `ossutil cp`), use the Bash tool
directly instead of MCP.

## Region Handling

- Use `AlibabaCloud___ListProductRegions` to check product availability in a
  specific region before making calls.
- Always include `--region` when operating across regions or when the default
  region may not match the target.

## Documentation Access

- `AlibabaCloud___SearchDocument`: Find relevant docs by keyword.
- `AlibabaCloud___ReadDocument`: Read full content of a known documentation URL.

Use these to verify behavior, understand quotas, or find configuration guides
that are not captured in API definitions alone.

## Error Handling Patterns

- **InvalidParameter**: Check parameter names and values against
  `GetApiDefinition` output.
- **AccessDenied / Forbidden**: Verify RAM permissions for the current identity.
- **Throttling**: Retry with backoff; do not loop aggressively.
- **RegionNotSupported**: Use `ListProductRegions` to find valid regions.

## Integration Guidance

When building stable workflows:

1. Use `SearchApis` to identify the correct API during development.
2. Use `GenerateCLICommand` to produce validated commands.
3. Capture the stable command patterns into a dedicated Skill.
4. Configure a safety policy to restrict the MCP connection to only the commands
   the Skill needs (for production use).

This progression — explore, validate, codify, restrict — ensures both flexibility
during development and safety in production.
