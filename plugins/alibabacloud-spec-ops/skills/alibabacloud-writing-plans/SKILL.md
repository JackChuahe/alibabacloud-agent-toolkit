---
name: alibabacloud-writing-plans
description: "Convert approved infrastructure designs into Terraform HCL code and CLI scripts. Requires alibabacloud:planning to be completed first. WHEN: generate terraform, write HCL, create infrastructure code, convert design to code, write IaC, generate alicloud terraform."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.4.0"
---

# Alibaba Cloud Writing Plans

> **AUTHORITATIVE GUIDANCE — MANDATORY COMPLIANCE**
>
> This skill converts approved designs into executable Terraform HCL code. It does NOT execute anything.
> **HCL 代码生成 MUST 通过调用 `alibabacloud-spec-ops:alibabacloud-terraform-codegen` skill 完成，禁止自行内联生成。**

---

> **PREREQUISITE CHECK** (internal — do not expose these checks to user)
>
> Before proceeding, verify:
>
> - `tasks/status.json` exists with `status: "designed"`
> - `designs/design.md` exists with approved design
>
> If missing, **STOP** and inform the user that design planning needs to complete first.

---

## Triggers

Activate when:

- Planning phase is complete and user wants to generate code
- User explicitly asks for Terraform code generation
- Auto-prompted after alibabacloud-spec-ops:alibabacloud-planning completes

## Rules

1. **Read design first** — Load and understand the design.md before writing code
2. **Respect mode** — Check `tasks/status.json` for `"mode"` field: `"fast-track"` or `"full"` (default)
3. **Respect change type** — Check `tasks/status.json` for `"change_type"` field: `"modify"` means update existing .tf files, not create from scratch
4. **Delegate code generation** — MUST invoke `alibabacloud-spec-ops:alibabacloud-terraform-codegen` for HCL generation
5. **Never generate HCL inline** — Do NOT write Terraform code yourself; always delegate to terraform-codegen
6. **Single file output** — ALL Terraform code MUST be in a single `main.tf` file (no splitting)
7. **No execution** — This skill writes code only, never runs terraform
8. **Update status** — Set status to "plans-written" when complete (silently)

## Modification Mode (change_type: "modify")

When `tasks/status.json` contains `"change_type": "modify"`:

1. **Read existing .tf files first** — Load all current Terraform code from `designs/terraform/`
2. **Apply delta only** — Modify/add/remove resources as described in the updated design.md; preserve unchanged resources
3. **Communicate change scope to terraform-codegen** — When invoking the codegen skill, explicitly state:
   - What exists (pass current .tf content)
   - What to change (the specific modifications from design)
   - What to preserve (everything else)
4. **Terraform plan will show diff** — Downstream validate/execute will naturally show `~ modify` and `+ add` instead of all `+ create`

## Mode-Aware Behavior

| Aspect | Fast Track | Full Mode |
|--------|-----------|-----------|
| Design input | Simplified quick plan | Full design.md |
| Code generation | Same (terraform-codegen) | Same |
| File organization | Single main.tf | Single main.tf |
| User output | Minimal — just list generated files | Include schema verification details |
| Next step | Auto-invoke `alibabacloud-validate` (no user prompt — validation is read-only and risk-free) | Same |

---

## Process

### Step 0: Mark "生成 Terraform 代码" as `in_progress`

The planning skill rendered a 3-task TODO list when the user confirmed
the design. At the very start of this skill's run, update that list
via `TodoWrite` to mark task **"生成 Terraform 代码"** as `in_progress`.
Do this *before* loading the design — the user sees the spinner align
with what's happening.

### Step 1: Load Design

Read `.aliyun-ai-ops-spec/{name}/designs/design.md` and extract:

- Resource list with specifications
- Network topology
- Security requirements
- Dependencies between resources
- Region, AZ, instance type choices

Produce a structured resource manifest (mental model):

```
Resources to generate:
1. VPC (cidr: 10.0.0.0/16, name: xxx)
2. VSwitch x2 (zone_h, zone_i)
3. Security Group + Rules
4. ECS x2 (c6.large)
5. SLB (internet)
6. RDS MySQL 8.0 (HA)
...
```

### Step 2: Invoke terraform-codegen Skill

**CRITICAL: You MUST invoke the `Skill` tool with `alibabacloud-spec-ops:alibabacloud-terraform-codegen` here.**

The terraform-codegen skill will:

1. Query IaCService for supported products and resource type schemas
2. Consult Alibaba Cloud documentation for correct attribute names and values
3. Generate production-quality HCL with proper data sources, variables, and outputs
4. Verify attribute correctness against real API schemas

**How to invoke:**

Use the `Skill` tool:

```
Skill:
  skill: "alibabacloud-spec-ops:alibabacloud-terraform-codegen"
```

Then provide the terraform-codegen skill with a clear instruction based on the design:

> "Based on the following design, generate complete Terraform HCL code for Alibaba Cloud:
>
> [paste the structured resource manifest from Step 1]
>
> Requirements:
>
> - Region: {region from design}
> - Resources: {list all resources with specs}
> - Network: {VPC/subnet topology}
> - Security: {SG rules, encryption, RAM}
> - HA: {multi-AZ, backup configs}
>
> IMPORTANT: Output ALL code in a single main.tf file. Do NOT split into separate files.
> File internal order: terraform {} → provider → variables → locals → data → resources → outputs"

### Step 3: Verify codegen output (codegen already wrote the file)

`terraform-codegen` is the **producer** of the .tf file — it wrote
`main.tf` itself during its Step 6 and reported `Files written: ...` in
its Step 7 summary. Do NOT re-write or duplicate; this step is a
smoke-check on the producer's output:

- Confirm `.aliyun-ai-ops-spec/{name}/designs/terraform/main.tf` exists
- Confirm codegen's Step 7 reported `Validation: iacservice validate-module: ok` (or accepted SKIPPED/FAILED with diagnostics)
- Confirm single-file constraint: no `variables.tf` / `outputs.tf` / `locals.tf` sibling files

If any check fails, surface the issue to the user and stop — do NOT
auto-chain to validate on broken codegen output.

**File contract that codegen enforces** (recap, for verification only):

- All Terraform code in one `main.tf` — never split
- Internal ordering: `terraform {}` → `provider` → `variables` → `locals` → `data sources` → `resources` → `outputs`
- Every `variable` has a `default` value
- Reason: IaC Service remote execution takes a single template body

### Step 4: Generate CLI Scripts (if needed)

For operations not supported by Terraform, create CLI scripts in `.aliyun-ai-ops-spec/{name}/designs/cli/`:

```bash
#!/bin/bash
# Operations that require Alibaba Cloud CLI
# Only for actions that Terraform cannot handle
# Example: DNS record verification, certificate validation, etc.

aliyun <service> <operation> --<args>
```

**When to use CLI scripts (instead of Terraform):**

- One-time setup operations (e.g., enable a service)
- Operations with no Terraform resource support
- Verification commands (e.g., check DNS propagation)

### Step 5: Update Internal State

Silently update `.aliyun-ai-ops-spec/{name}/tasks/status.json` to `status: "plans-written"`. **Do NOT mention this to the user.**

---

## Why Delegate to terraform-codegen?

The `terraform-codegen` skill provides capabilities that inline generation cannot:

| Capability | terraform-codegen | Inline generation |
|-----------|:--:|:--:|
| Query real resource schemas via IaCService | ✅ | ❌ |
| Verify attribute names against API | ✅ | ❌ |
| Consult latest Alibaba Cloud docs | ✅ | ❌ |
| Error recovery with documentation lookup | ✅ | ❌ |
| Correct provider version constraints | ✅ | ⚠️ |
| Data source usage for dynamic values | ✅ | ⚠️ |

**The IaCService schema query ensures generated code uses correct, current attribute names** — avoiding common issues like deprecated attributes, renamed fields, or invalid enum values.

---

## Continuation Contract — MANDATORY, execute IMMEDIATELY when Step 2's Skill call returns

> **TRIGGER**: the moment the `Skill: alibabacloud-spec-ops:alibabacloud-terraform-codegen` call returns to your context. terraform-codegen's Step 7 summary (`Files written: …` + `Validation: …` + implementation notes) is **NOT a stopping point** — it is the cue to continue. Treating it as terminal and waiting for user input is a **bug** (this skill's most common regression).
>
> Execute Steps 3 → 4 → 5 → the items below, in that order, in the same turn, without pausing for user input. The auto-chain to `alibabacloud-validate` is mandatory and unconditional unless Step 3's smoke-check failed.

After Step 3's smoke-check passes:

1. Update the user-facing TODO list via `TodoWrite`:
   - Mark **"生成 Terraform 代码"** → `completed`
   - Mark **"双轨评审：spec compliance + code quality"** → `in_progress`
2. Inform user of the result (one paragraph, no question):

> "Terraform code generated successfully.
>
> Generated: `main.tf` — {N} resources, {M} variables, {K} outputs (all in single file)
>
> Code was generated with resource schemas verified via IaCService API.
>
> Now running review (spec compliance + code quality)..."

1. **Immediately and automatically invoke `alibabacloud-spec-ops:alibabacloud-validate` via the `Skill` tool** — do NOT stop to ask the user. Validation is read-only (no cloud changes, no cost) and the next user-facing decision is whether to deploy, which `alibabacloud-validate` itself gates. **Emitting only the "Now running review…" paragraph without then invoking the Skill is the regression bug — the Skill call MUST happen in the same turn.**

**Do NOT:**

- Ask "Would you like to proceed with validation?" — validation is not a decision the user needs to make
- Mention status.json updates
- Mention internal file paths for state tracking
- Mention the terraform-codegen delegation details (implementation detail)
- Stop after printing the "Now running review…" paragraph — that paragraph is only a user-facing transition note; the actual `Skill` invocation must follow in the same turn
- Treat any `※ recap:` or session-summary line that mentions "next step" as substitute action — it's commentary, not execution

---

## Anti-Patterns (FORBIDDEN)

- ❌ Generating HCL code directly without invoking terraform-codegen
- ❌ Guessing resource attribute names from memory
- ❌ Using hardcoded values instead of variables
- ❌ Skipping IaCService schema verification
- ❌ Splitting code into multiple .tf files (variables.tf, outputs.tf, etc.)
- ❌ Omitting outputs for important resource values
- ❌ Proceeding to validate without completing main.tf
