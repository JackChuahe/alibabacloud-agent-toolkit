---
name: alibabacloud-executing-plans
description: "Execute validated Terraform plans via Alibaba Cloud IaC Service. Requires explicit user confirmation before any apply operation. WHEN: execute terraform, apply infrastructure, run terraform apply, deploy infrastructure, create cloud resources, execute plan."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.4.0"
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
9. **Persist `state_id`** — IaC Service keeps the Terraform state remotely keyed by `state_id`. This skill MUST write it back to `tasks/status.json` (under `state.state_id`) on every Plan / Apply / Destroy and MUST pass the saved value on every subsequent Day-2 call. Losing the `state_id` orphans the remote state and forces a fresh deploy (potential duplicate resources).

---

## State Persistence (CRITICAL for Day-2)

IaC Service stores each deployment's Terraform state remotely, indexed by
`state_id`. This handle is the contract that lets you iterate on the same
infrastructure across multiple `executing-plans` invocations:

| When | Read | Write |
| --- | --- | --- |
| Step 1 (start) | `tasks/status.json` → `state.state_id` (may be empty on first run) | — |
| Step 3 (after plan response) | — | `state.state_id`, `state.last_plan_at` |
| Step 5/6 (after apply succeeds) | — | `state.state_id` (re-confirm), `state.last_apply_at` |
| Destroy (after success) | — | `state.last_destroy_at`; keep `state_id` as historical record |

**Branching by Day-1 vs Day-2:**

| Scenario | Saved `state_id` | Plan CLI |
| --- | --- | --- |
| Day-1 (first run) | absent / empty | `--code '{CODE}' --client-token <uuid>` |
| Day-2 (iteration) | present | `--code '{CODE}' --state-id {STATE_ID} --client-token <uuid>` |

Apply always passes `--state-id`; pass `--code` too only when the HCL
changed between plan and apply (rare — usually code is already final at
plan time).

**Legacy / migration edge case.** If status is `executed` but `state.state_id`
is absent (status.json predates this schema), STOP before touching the
remote — ask the user whether to:

- (a) treat this as Day-1 and create a fresh state (risks duplicate
  resources alongside the legacy deployment), or
- (b) abort and let the user supply the missing `state_id` manually
  (recommended if they know it).

Never silently start fresh — the user paid for those resources.

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

1. Read `tasks/status.json`:
   - `status` must be `"validated"` (Day-1) OR `"executed"` (Day-2 re-iteration after planning produced new code)
   - Capture `state.state_id` into `{STATE_ID}` (may be empty on first run — that signals Day-1)
   - If `status == "executed"` but `state.state_id` is missing, see the
     legacy edge case in [State Persistence](#state-persistence-critical-for-day-2) before proceeding
2. Read `tasks/validation-report.md` — must show all reviews PASS
3. Confirm user intent one more time, and surface whether this is Day-1 or Day-2:

> "Ready to execute Terraform.
>
> {Day-1: This will create real cloud resources on Alibaba Cloud and incur costs.}
> {Day-2: This will update the existing deployment (state `{STATE_ID}`); changes
>         shown in the next plan output will be applied to the live resources.}
>
> Proceed with `terraform plan`?"

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

**Branch by whether `{STATE_ID}` was loaded in Step 1.**

**Day-1 (no prior `state_id`):**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-plan --code '{CODE}' --client-token {CLIENT_TOKEN}"
```

**Day-2 (continuing on saved `state_id`):**

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-plan --code '{CODE}' --state-id {STATE_ID} --client-token {CLIENT_TOKEN}"
```

Where:
- `{CODE}` = concatenated .tf content (single quotes properly escaped)
- `{CLIENT_TOKEN}` = fresh UUID (format `[0-9a-zA-Z-]{1,64}`) — required for idempotency
- `{STATE_ID}` = value from `tasks/status.json` → `state.state_id` (Day-2 only)

**Response contains a state file ID (typically `StateId`)** — capture it as
`{STATE_ID}`. On Day-2 it will match the value passed in; on Day-1 this is
the freshly minted one.

**PERSIST IMMEDIATELY** — before polling, before showing the plan output to
the user, silently update `tasks/status.json`:

```json
{
  ...,
  "state": {
    "state_id": "{STATE_ID}",
    "last_plan_at": "{ISO timestamp}",
    ...
  }
}
```

Rationale: if the user aborts at the Step 4 confirmation, the next
invocation must still be able to continue on this state. **Never poll or
proceed before this write completes.**

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

Only after user confirms. Reuse `{STATE_ID}` (saved in Step 3) and a
**fresh** `--client-token` (different UUID from the plan call):

```
AlibabaCloud___CallCLI:
  command: "aliyun iacservice execute-terraform-apply --state-id {STATE_ID} --client-token {CLIENT_TOKEN}"
```

If the HCL changed after plan (rare — usually it didn't), also pass
`--code '{CODE}'` (mutually included with `--state-id`).

The apply response returns the same `{STATE_ID}` — re-confirm it matches
the saved value before polling. If for any reason a NEW state_id appears,
treat that as an anomaly: stop, alert the user, and do NOT overwrite the
saved one without explicit confirmation.

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

Silently update `tasks/status.json`. **Do NOT mention this file to the user.**

```json
{
  ...,
  "status": "executed",
  "updated_at": "{ISO timestamp}",
  "state": {
    "state_id": "{STATE_ID}",
    "last_plan_at": "{from Step 3}",
    "last_apply_at": "{ISO timestamp of successful apply}",
    "last_destroy_at": null
  }
}
```

`state.state_id` MUST be retained even on Day-2 transitions (do not clear
it between iterations). Subsequent `executing-plans` invocations will read
it back in Step 1 to continue on the same remote state.

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
- **Keep `state.state_id`** in status.json if one was already saved from a
  prior successful run — never delete it on a plan failure. The remote
  state still exists and the next attempt must continue on it.

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

After destroy succeeds, update `tasks/status.json`:

```json
{
  ...,
  "status": "destroyed",
  "updated_at": "{ISO timestamp}",
  "state": {
    "state_id": "{STATE_ID}",
    "last_plan_at": "{prior}",
    "last_apply_at": "{prior}",
    "last_destroy_at": "{ISO timestamp}"
  }
}
```

**Keep `state.state_id` as a historical record** — do not clear it. If the
user later wants to redeploy fresh (new state), planning will detect
`status == "destroyed"` and prompt for net-new Day-1 vs reuse decision.

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
- **Always persist `state_id`** — Write to `tasks/status.json` → `state.state_id` immediately after every plan response; never proceed without saving
- **Never orphan remote state** — Keep `state.state_id` across re-iterations and even after destroy (historical record); only the user may decide to discard it
- **Fail safe** — On error, stop and inform user; don't retry blindly
