---
name: alibabacloud-executing-plans
description: "Execute validated Terraform plans via Alibaba Cloud IaC Service. Requires explicit user confirmation before any apply operation. WHEN: execute terraform, apply infrastructure, run terraform apply, deploy infrastructure, create cloud resources, execute plan."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.2.0"
---

# Alibaba Cloud Executing Plans

> **AUTHORITATIVE GUIDANCE — MANDATORY COMPLIANCE**
>
> This skill executes validated Terraform code via Alibaba Cloud IaC Service (remote execution).
> It creates **real cloud resources** that cost money. Safety gates are non-negotiable.
>
> **ALL CLI operations MUST use MCP tool `AlibabaCloud___CallCLI`** — never use Bash to run `aliyun` commands directly.

---

> **PREREQUISITE CHECK — MANDATORY**
>
> Before proceeding, verify BOTH prerequisites:
>
> 1. **Validation passed** — check `tasks/status.json` has `status: "validated"` (internal check, don't expose to user)
> 2. **User explicitly confirmed** they want to execute
>
> If EITHER is missing, **STOP IMMEDIATELY**:
> - Not validated? → Invoke **alibabacloud:validate** first
> - No user confirmation? → Ask user before proceeding

---

## Triggers

Activate when:
- User explicitly asks to execute/apply the Terraform plan
- User confirms they want to proceed after validation passes

**NEVER activate automatically.** This skill requires explicit user intent.

## Rules

1. **User confirmation required** — Never execute without explicit user approval
2. **Plan before apply** — Always run terraform plan first, show results, get confirmation
3. **MCP only** — ALL `aliyun` CLI commands MUST go through `AlibabaCloud___CallCLI`, never through Bash
4. **Inline content** — Read .tf files locally, then pass content as string to `--template-body` (MCP cannot access local files)
5. **Record everything** — All outputs recorded to tasks/
6. **Support rollback** — Provide destroy option if apply fails
7. **Poll for completion** — IaC Service is async; use sequential MCP calls to poll
8. ⚠️ **Destructive operations (destroy) require double confirmation**

---

## MCP Execution Model

**CRITICAL: The `AlibabaCloud___CallCLI` MCP tool runs on a REMOTE server. It CANNOT:**
- Access local files (no `file://`, no `$(cat ...)`, no local paths)
- Use shell operators (`|`, `>`, `&&`, `$()`)
- Use shell variables or environment variables

**Therefore, you MUST:**
1. Use the `Read` tool to read `.tf` file contents into your context
2. Pass the file content as an inline string in the `--template-body` parameter
3. Escape single quotes in HCL content (replace `'` with `'\''` if needed)

---

## Process

### Step 1: Verify Prerequisites

1. Read `tasks/status.json` — must be "validated"
2. Read `tasks/validation-report.md` — must show all stages PASS
3. Confirm user intent one more time:

> "Ready to execute Terraform. This will:
> - Create real cloud resources on Alibaba Cloud
> - Incur costs based on the resources provisioned
>
> Proceed with `terraform plan`?"

### Step 2: Prepare Template Content

**Read all `.tf` files** from the design directory and concatenate them into a single string:

```
# Use Read tool to get content of each .tf file:
Read: .aliyun-ai-ops-spec/{name}/designs/terraform/main.tf
Read: .aliyun-ai-ops-spec/{name}/designs/terraform/variables.tf
Read: .aliyun-ai-ops-spec/{name}/designs/terraform/outputs.tf
# ... any other .tf files
```

Concatenate all content into one `TEMPLATE_BODY` string. This will be passed inline to MCP commands.

### Step 3: Execute Terraform Plan

**Call MCP tool with inline template content:**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-plan --template-body '{TEMPLATE_BODY}' --region {REGION}"
```

Where:
- `{TEMPLATE_BODY}` = concatenated .tf content (with single quotes properly escaped)
- `{REGION}` = region from the design (e.g., `cn-hangzhou`)

**Response contains `ExecutionId`** — save this for subsequent calls.

**Poll for completion** (see Polling Strategy below):

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --execution-id {ExecutionId} --region {REGION}"
```

### Step 4: Present Plan Results

Show the plan output to user:
- Resources to be created/modified/destroyed
- Any potential issues or warnings

Write plan results to `tasks/tf-plan-result.md`.

Ask for explicit confirmation:

> "Terraform plan results:
>
> + {N} resources to create
> ~ {N} resources to modify
> - {N} resources to destroy
>
> {Summary of key resources}
>
> ⚠️ This will create real resources and incur costs.
> Confirm apply? (yes/no)"

**STOP and wait for user confirmation.** Do NOT proceed without explicit "yes".

### Step 5: Execute Terraform Apply

Only after user confirms:

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-apply --execution-id {ExecutionId} --region {REGION}"
```

**Poll for completion:**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --execution-id {ExecutionId} --region {REGION}"
```

### Step 6: Record Results

Write results to `tasks/tf-apply-result.md`:

```markdown
# Terraform Apply Results - {Requirement Name}

## Timestamp
{ISO timestamp}

## Execution ID
{execution-id}

## Status
SUCCESS / FAILED

## Resources Created
| Resource Type | Resource Name | Resource ID |
|---------------|---------------|-------------|
| ... | ... | ... |

## Outputs
| Name | Value |
|------|-------|
| ... | ... |

## Errors (if any)
{error details}
```

### Step 7: Update Internal State

Silently update `tasks/status.json` to `status: "executed"`. **Do NOT mention this to the user.**

---

## Polling Strategy

IaC Service operations are **asynchronous**. After submitting a job, poll using sequential MCP calls:

| Parameter | Value |
|-----------|-------|
| First poll delay | Wait ~5 seconds (inform user "正在执行中...") then call |
| Poll interval | Every 10 seconds, call `get-execute-state` again |
| Max attempts | 60 attempts (≈10 minutes) |
| Timeout action | Report "still running" with ExecutionId for manual check |

**How to poll:**

1. Call `AlibabaCloud___CallCLI` with `get-execute-state`
2. Check `Status` in response:
   - `"Running"` → inform user "执行中..." and call again after brief pause
   - `"Succeeded"` → proceed to next step
   - `"Failed"` → extract `ErrorMessage`, go to Error Handling
3. Repeat until terminal state or max attempts reached

**Important:** Each poll is a separate `AlibabaCloud___CallCLI` call. Do NOT use Bash loops or sleep commands.

---

## Error Handling

### Plan Fails
- Record error in `tasks/tf-plan-result.md`
- Identify root cause from `ErrorMessage`:

| Error Code | Meaning | Action |
|------------|---------|--------|
| InvalidTemplate | TF syntax error | Fix TF files and re-validate |
| QuotaExceeded | Resource quota limit | Inform user to request quota increase |
| AccessDenied | Permission missing | Invoke `alibabacloud-ram-permission-diagnose` |
| ResourceNotFound | Referenced resource missing | Check dependencies |
| InternalError | Service issue | Retry once after informing user |

- Set status back to "plans-written" for re-validation

### Apply Fails
- Record error in `tasks/tf-apply-result.md`
- Check partial state:

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --execution-id {ExecutionId} --region {REGION}"
```

- Offer options:
  1. Fix and retry apply
  2. Destroy partially created resources
  3. Manual intervention guidance

### Destroy Operations

For `terraform destroy` (cleanup or rollback):

> "⚠️ **DESTRUCTIVE OPERATION**
>
> This will destroy ALL resources created by this Terraform configuration.
> This action cannot be undone.
>
> Type the requirement name `{name}` to confirm destruction:"

Require exact name match before proceeding. Then execute:

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-destroy --execution-id {ExecutionId} --region {REGION}"
```

Poll for completion using same strategy as apply.

---

## IaC Service MCP Command Reference

**All commands use `AlibabaCloud___CallCLI` with the full CLI string:**

| Operation | MCP Command |
|-----------|-------------|
| Validate | `aliyun iacservice validate-module --template-body '{content}' --region {region}` |
| Plan | `aliyun iacservice execute-terraform-plan --template-body '{content}' --region {region}` |
| Apply | `aliyun iacservice execute-terraform-apply --execution-id {id} --region {region}` |
| Destroy | `aliyun iacservice execute-terraform-destroy --execution-id {id} --region {region}` |
| Poll status | `aliyun iacservice get-execute-state --execution-id {id} --region {region}` |

**⚠️ NEVER:**
- Use `file://` paths (MCP cannot access local filesystem)
- Use `$(cat ...)` shell substitution (MCP doesn't support shell operators)
- Use Bash tool to run `aliyun` commands (always use MCP)
- Omit `--region` parameter

---

## Safety Principles

- **Never skip plan** — Always plan before apply
- **Never auto-apply** — Always require user confirmation
- **Never silent destroy** — Destroy requires explicit naming confirmation
- **Always use MCP** — Never run aliyun CLI via Bash; always via `AlibabaCloud___CallCLI`
- **Always inline content** — Read files first, pass content as string to MCP
- **Always record** — Every operation logged to tasks/
- **Always poll** — Don't assume completion; verify state via MCP
- **Fail safe** — On error, stop and inform user; don't retry blindly
