---
name: alibabacloud-executing-plans
description: "Execute validated Terraform plans via Alibaba Cloud IaC Service. Requires explicit user confirmation before any apply operation. WHEN: execute terraform, apply infrastructure, run terraform apply, deploy infrastructure, create cloud resources, execute plan."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.3.0"
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
4. **Inline content** — Read .tf files locally, then pass content as string to `--code` (MCP cannot access local files)
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
2. Concatenate all `.tf` files into a single string and pass it inline via `--code`
3. Escape single quotes in HCL content (replace `'` with `'\''` if needed)
4. Generate a fresh UUID for `--client-token` on every Plan / Apply / Destroy call (idempotency key, format `[0-9a-zA-Z-]{1,64}`)

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

Concatenate all content into one `CODE` string. This will be passed inline via `--code` to MCP commands.

### Step 3: Execute Terraform Plan

**Call MCP tool with inline template content:**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-plan --code '{CODE}' --client-token {CLIENT_TOKEN}"
```

Where:
- `{CODE}` = concatenated .tf content (single quotes properly escaped)
- `{CLIENT_TOKEN}` = fresh UUID (format `[0-9a-zA-Z-]{1,64}`) — required for idempotency

**Response contains a state file ID (typically `StateId`)** — save it as `{STATE_ID}` for subsequent calls.

**Poll for completion** (see Polling Strategy below):

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --state-id {STATE_ID}"
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

Only after user confirms. Reuse `{STATE_ID}` from Step 3's plan and use a **fresh** `--client-token` (different UUID):

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-apply --state-id {STATE_ID} --client-token {CLIENT_TOKEN}"
```

If the HCL changed after plan, also pass `--code '{CODE}'` (mutually included with `--state-id`).
The apply response returns the same `{STATE_ID}` (re-confirm before polling).

**Poll for completion:**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice get-execute-state --state-id {STATE_ID}"
```

### Step 6: Record Results

Write results to `tasks/tf-apply-result.md`:

```markdown
# Terraform Apply Results - {Requirement Name}

## Timestamp
{ISO timestamp}

## State ID
{state-id}

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
| Timeout action | Report "still running" with `{STATE_ID}` for manual check |

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
  command: "aliyun iacservice get-execute-state --state-id {STATE_ID}"
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

Require exact name match before proceeding. Then execute (use a fresh `--client-token`):

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-destroy --state-id {STATE_ID} --client-token {CLIENT_TOKEN}"
```

Poll for completion using same strategy as apply.

---

## IaC Service MCP Command Reference

**All commands use `AlibabaCloud___CallCLI` with the full CLI string:**

| Operation | MCP Command |
|-----------|-------------|
| Plan        | `aliyun iacservice execute-terraform-plan --code '{content}' --client-token {uuid}` |
| Apply       | `aliyun iacservice execute-terraform-apply --state-id {id} --client-token {uuid}` |
| Poll status | `aliyun iacservice get-execute-state --state-id {id}` |
| Destroy     | `aliyun iacservice execute-terraform-destroy --state-id {id} --client-token {uuid}` |

### Command Parameter Reference

**`aliyun iacservice execute-terraform-plan`**

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `--client-token` | yes | string `[0-9a-zA-Z-]{1,64}` | Idempotency key, fresh UUID per call |
| `--code` | conditional | string | Full Terraform HCL content (concatenated from all `.tf` files). Required for first plan; on a follow-up plan with unchanged content you may pass only `--state-id` |
| `--state-id` | conditional | string | When non-empty, continue Plan on top of an existing state file |

**`aliyun iacservice execute-terraform-apply`**

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `--client-token` | yes | string `[0-9a-zA-Z-]{1,64}` | Idempotency key, fresh UUID per call |
| `--code` | conditional | string | Required only if HCL changed since plan; pass the new concatenated content |
| `--state-id` | conditional | string | State ID from the preceding plan; pass it when content is unchanged so Apply continues on the same state |

**`aliyun iacservice execute-terraform-destroy`**

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `--client-token` | yes | string `[0-9a-zA-Z-]{1,64}` | Idempotency key, fresh UUID per call |
| `--state-id` | yes | string | State ID of the deployment to tear down |

**`aliyun iacservice get-execute-state`**

| Param | Required | Type | Notes |
| --- | --- | --- | --- |
| `--state-id` | yes | string | State ID returned by the preceding Plan / Apply / Destroy call |

**⚠️ NEVER:**
- Use `file://` paths (MCP cannot access local filesystem)
- Use `$(cat ...)` shell substitution (MCP doesn't support shell operators)
- Use Bash tool to run `aliyun` commands (always use MCP)
- Pass `--region` — IaC Service derives the region from the HCL `provider "alicloud"` block; the CLI does not accept a `--region` flag here
- Omit `--client-token` from Plan / Apply / Destroy — it is required for idempotency
- Use `--execution-id` or `--template-body` — these are stale names from earlier drafts; the correct parameters are `--state-id` and `--code`

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
