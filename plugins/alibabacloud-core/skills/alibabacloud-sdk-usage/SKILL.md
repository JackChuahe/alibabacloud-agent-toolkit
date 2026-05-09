---
name: alibabacloud-sdk-usage
description: >
  Generate or modify code that calls Alibaba Cloud OpenAPIs. Use when the
  user asks for Alibaba Cloud SDK code, API parameters, endpoints, SDK
  dependencies, typed product SDK calls, or generic OpenAPI calls.
allowed-tools: "mcp__alibabacloud-core__AlibabaCloud___CallCLI"
---

# Alibaba Cloud SDK Usage

Use the user's local `alibabacloud-core` MCP server before writing Alibaba
Cloud interaction code. Do not start another MCP server, call `aliyun`
directly from the shell, or bypass the local MCP safety policy.

The only allowed tool for OpenAPI Explorer access is:

- `mcp__alibabacloud-core__AlibabaCloud___CallCLI`

All metadata commands below must be executed through that tool as
`aliyun openapiexplorer ...` commands. Do not guess product codes, SDK
packages, request models, endpoints, or parameter casing.

## Workflow

1. Inspect the local project first.
   - Detect the target language from project files (`pyproject.toml`,
     `requirements*.txt`, `package.json`, `go.mod`, `pom.xml`, `build.gradle`,
     `.csproj`, `composer.json`, `Package.swift`, etc.).
   - Check whether Alibaba Cloud SDK dependencies are already installed or
     declared.
   - Check existing Alibaba Cloud call style. If the project uses generic
     `call_api` / common OpenAPI calls, continue with `callType=generic`.
     If it uses product-specific clients and request models, continue with
     `callType=typed`.
   - Match local naming, formatting, async style, error handling, and dependency
     manager. Do not paste standalone samples into application code unchanged.

2. Resolve metadata with OpenAPI Explorer through local MCP.
   - `list-products`: resolve the exact product code and default API version
     when the user did not provide them.
   - `get-product-endpoints`: choose the endpoint for the target region. Use
     VPC endpoints only when the code will run inside the same Alibaba Cloud
     VPC; otherwise use the public endpoint.
   - `get-api-definition`: read required parameters, pagination fields, response
     shape, error codes, and RAM actions.
   - `get-sdk-dependencies`: get the exact dependency and version for the
     selected language and `callType`.
   - `get-code-sample`: get the official sample for the same product, API
     version, language, region, params, and `callType`.

3. Install or update dependencies only when needed.
   - If the required dependency is already present and compatible, do not add a
     duplicate.
   - If the project already uses a dependency manager, update that manager's
     manifest instead of issuing an unrelated install command.
   - Use the install command or dependency coordinates returned by
     `get-sdk-dependencies` / `get-code-sample`.

4. Adapt the sample into local code.
   - Keep credentials on the default Alibaba Cloud credential provider chain.
     Do not hardcode access keys.
   - Set the endpoint and region consistently.
   - Populate request parameters from the user's inputs and
     `get-api-definition`.
   - Add pagination only when the API definition exposes pagination parameters.
     Prefer token pagination (`NextToken` + `MaxResults` / `MaxItems`) over
     page-number pagination when both are available.
   - Preserve local code style and existing typed/generic SDK approach.

5. Verify.
   - Run the project's normal format, lint, type-check, compile, or test command
     when available.
   - For a live smoke test, prefer a cheap read-only `Describe*` / `List*` call
     with narrow parameters.

## MCP Commands

Invoke these commands only through
`mcp__alibabacloud-core__AlibabaCloud___CallCLI`:

```bash
aliyun openapiexplorer list-products --filter Ecs
aliyun openapiexplorer get-product-endpoints --product Ecs
aliyun openapiexplorer get-api-definition --product Ecs --biz-api-version 2014-05-26 --api DescribeInstances
aliyun openapiexplorer get-sdk-dependencies --product Ecs --biz-language python --biz-version 2014-05-26 --call-type typed
aliyun openapiexplorer get-code-sample --product Ecs --api-name DescribeInstances --biz-language python --biz-api-version 2014-05-26 --biz-region-id cn-hangzhou --call-type typed --params '{"RegionId":"cn-hangzhou"}'
```

Important CLI parameter names:

- `get-api-definition` uses `--api` and `--biz-api-version`.
- `get-sdk-dependencies` uses `--biz-language`, `--biz-version`, and
  `--call-type`.
- `get-code-sample` uses `--api-name`, `--biz-language`,
  `--biz-api-version`, `--biz-region-id`, `--call-type`, and `--params`.

If the local MCP tool is unavailable or denies a command, stop and report the
denial. Do not fall back to shell execution or another MCP server.

## Guardrails

- Do not switch a local project from generic calls to typed SDK calls, or the
  reverse, unless the user asks for that migration.
- Do not run `aliyun` directly from the terminal for this workflow.
- Do not use any MCP server except the local `alibabacloud-core` server.
- Do not invent SDK versions, package names, request classes, or field casing.
- Do not add verbose tutorial text to generated code.
- Do not use OSS or Tablestore data-plane SDKs through this workflow; use those
  product SDKs directly.
