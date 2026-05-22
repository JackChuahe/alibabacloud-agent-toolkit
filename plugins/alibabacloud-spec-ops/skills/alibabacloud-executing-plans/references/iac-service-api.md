# Alibaba Cloud IaC Service API Reference

## Overview

IaC Service provides remote Terraform execution through the Alibaba Cloud CLI. All operations are asynchronous — you submit a job and poll for completion.

**ALL commands are executed via MCP tool `AlibabaCloud___CallCLI`** — never via Bash.

## Authentication

Requires configured Alibaba Cloud CLI (`aliyun configure`) with permissions for:
- `iacservice:ExecuteTerraformPlan`
- `iacservice:ExecuteTerraformApply`
- `iacservice:ExecuteTerraformDestroy`
- `iacservice:GetExecuteState`
- `iacservice:ValidateModule`

## Critical Constraint: No Local File Access

The `AlibabaCloud___CallCLI` MCP tool executes on a **remote server**. It cannot:
- Access the local filesystem
- Use `file://` or `fileb://` prefixes
- Use shell substitutions like `$(cat ...)`
- Use shell pipes, redirects, or variables

**You MUST read file content locally (via Read tool) and pass it inline as a string.**

## Commands

### validate-module

Validates Terraform module syntax without executing.

**MCP call:**
```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice validate-module --template-body '<HCL_CONTENT>' --region cn-hangzhou"
```

**Response:**
```json
{
  "RequestId": "xxx",
  "Valid": true,
  "Errors": []
}
```

### execute-terraform-plan

Submits a Terraform plan job.

**MCP call:**
```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-plan --template-body '<HCL_CONTENT>' --region cn-hangzhou"
```

**Response:**
```json
{
  "RequestId": "xxx",
  "ExecutionId": "exec-xxxxx"
}
```

### execute-terraform-apply

Submits a Terraform apply job (requires prior successful plan).

**MCP call:**
```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-apply --execution-id exec-xxxxx --region cn-hangzhou"
```

**Response:**
```json
{
  "RequestId": "xxx",
  "ExecutionId": "exec-xxxxx"
}
```

### execute-terraform-destroy

Submits a Terraform destroy job.

**MCP call:**
```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-destroy --execution-id exec-xxxxx --region cn-hangzhou"
```

### get-execute-state

Polls execution status.

**MCP call:**
```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --execution-id exec-xxxxx --region cn-hangzhou"
```

**Response:**
```json
{
  "RequestId": "xxx",
  "Status": "Running|Succeeded|Failed",
  "Output": "...",
  "ErrorMessage": "..."
}
```

## Polling Strategy

1. Initial wait: ~5 seconds (inform user execution is in progress)
2. Poll interval: 10 seconds between each `get-execute-state` call
3. Max attempts: 60 (≈10 minutes total)
4. On timeout: Report as "still running" with execution ID for manual check

Each poll is a **separate** `AlibabaCloud___CallCLI` call. Do NOT use loops in Bash.

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| InvalidTemplate | TF syntax error | Fix and re-validate |
| QuotaExceeded | Resource quota limit | Request quota increase |
| AccessDenied | Permission missing | Check RAM policy |
| ResourceNotFound | Referenced resource missing | Check dependencies |
| InternalError | Service issue | Retry after delay |
