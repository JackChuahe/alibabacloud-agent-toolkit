---
name: alibabacloud-writing-plans
description: "Convert approved infrastructure designs into Terraform HCL code and CLI scripts. Requires alibabacloud:planning to be completed first. WHEN: generate terraform, write HCL, create infrastructure code, convert design to code, write IaC, generate alicloud terraform."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.5.0"
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

### Step 2: Atomic Two-Skill Sequence — codegen → validate

> **WARNING — REGRESSION SCENARIO (most common spec-ops bug).** Agent
> invokes codegen, sees its polished Step 7 summary (with `Files written: …`,
> `Validation: …`, implementation notes), treats it as a terminal output,
> prints a closing paragraph, and stops. User has to type "继续" to unstick
> the chain. **Sub-step 2.3 below is the single most important instruction
> in this skill — do not skip it.**
>
> Treat Step 2 as ONE atomic compound action of three sub-steps, ALL
> executed in the same turn. Both Skill calls (2.1 codegen, 2.3 validate)
> must happen with no user-input pause between them.

#### Step 2.1 — Invoke terraform-codegen

Use the `Skill` tool:

```
Skill:
  skill: "alibabacloud-spec-ops:alibabacloud-terraform-codegen"
```

Provide the terraform-codegen skill with a clear instruction based on the design:

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

terraform-codegen will:

1. Query IaCService for supported products and resource type schemas
2. Consult Alibaba Cloud documentation for correct attribute names and values
3. Generate production-quality HCL with proper data sources, variables, and outputs
4. Verify attribute correctness against real API schemas
5. Write `main.tf` itself (it is the producer — do NOT re-write in 2.2)
6. Emit a Step 7 summary back to you

#### Step 2.2 — On codegen's return: smoke check + record progress + transition

The moment the Skill call from 2.1 returns to your context:

1. **Smoke-check codegen output** (don't re-write, codegen already did):
   - Confirm `.aliyun-ai-ops-spec/{name}/designs/terraform/main.tf` exists
   - Confirm codegen reported `Validation: iacservice validate-module: ok` (or accepted SKIPPED / FAILED with diagnostics — codegen already retried 3× on FAIL)
   - Confirm single-file constraint: no `variables.tf` / `outputs.tf` / `locals.tf` siblings
   - If smoke-check fails, STOP here — surface the issue and do NOT chain to validate on broken output
2. **Update TODO list via `TodoWrite`** (signals progress to user):
   - Mark **"生成 Terraform 代码"** → `completed`
   - Mark **"双轨评审：spec compliance + code quality"** → `in_progress`
3. **Update `tasks/status.json` to `status: "plans-written"`** — silently, do NOT mention to user
4. **Print exactly ONE short user-facing transition paragraph** (no question, no closing):

   > "Terraform code generated successfully — `main.tf` ({N} resources,
   > {M} variables, {K} outputs).
   >
   > Now running review (spec compliance + code quality)..."

#### Step 2.3 — IMMEDIATELY invoke alibabacloud-validate (REGRESSION-CRITICAL)

**Your very next tool call, right after the transition paragraph from
2.2, MUST be:**

```
Skill:
  skill: "alibabacloud-spec-ops:alibabacloud-validate"
```

**Self-check at this exact moment**: if your next planned action is
anything other than the `Skill` call above — writing another paragraph,
summarizing, pausing for `继续`, "letting the user decide", emitting
`Baked for …` and stopping — **you are inside the regression bug**. The
Skill call is mandatory; the transition paragraph in 2.2 is the only
user-facing text allowed between codegen and validate.

Hard rules:

- DO NOT wait for user input — validate is read-only, no cloud changes, no cost; the user's next real decision is at validate's exit (deploy or not)
- DO NOT write a closing paragraph after the transition
- DO NOT treat codegen's Step 7 summary as a stopping point — it is a mid-pipeline checkpoint, not an endpoint
- DO NOT skip 2.2's transition just to "save a turn" — the user needs to see what's happening
- DO NOT think "the user will type 继续 if they want to proceed" — the previous two regression incidents are exactly this

### Step 3: Generate CLI Scripts (if needed, optional)

This step is independent of the codegen → validate chain and may run
either now (before validate) or after the full pipeline. For operations
not supported by Terraform, create CLI scripts in `.aliyun-ai-ops-spec/{name}/designs/cli/`:

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

In the common case (no extra CLI work needed), skip this step entirely.

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

## After validate returns

validate runs spec-reviewer + code-quality-reviewer in parallel, then
prompts the user for the deploy decision (its own user gate). When
validate's Skill call returns to this skill's context, writing-plans is
**done** — no further action required from this skill. The execute /
deploy chain is owned by `alibabacloud-validate` → `alibabacloud-executing-plans`.

Do NOT add a closing paragraph after validate returns;the conversation
has moved into validate's user-gate dialog and any extra text from this
skill is noise.

---

## Anti-Patterns (FORBIDDEN)

- ❌ Generating HCL code directly without invoking terraform-codegen
- ❌ **Stopping after codegen's Step 7 summary** — this is the most common regression; codegen is a midpoint, the chain MUST continue to validate in the same turn (see Step 2.3)
- ❌ **Asking the user "继续?" / "proceed with validation?" between codegen and validate** — validation is read-only, no user decision needed
- ❌ Guessing resource attribute names from memory
- ❌ Using hardcoded values instead of variables
- ❌ Skipping IaCService schema verification
- ❌ Splitting code into multiple .tf files (variables.tf, outputs.tf, etc.)
- ❌ Omitting outputs for important resource values
- ❌ Proceeding to validate without completing main.tf
