# State Directory Structure

## Overview

All artifacts for a single infrastructure requirement are stored under `.aliyun-ai-ops-spec/{requirement-name}/`.

## Structure

```
.aliyun-ai-ops-spec/
├── {requirement-name}/
│   ├── designs/
│   │   ├── design.md              # Full design specification
│   │   ├── architecture.html      # Optional visual diagram
│   │   ├── terraform/
│   │   │   ├── main.tf            # Provider + resources
│   │   │   ├── variables.tf       # Input variables
│   │   │   ├── outputs.tf         # Output values
│   │   │   ├── data.tf            # Data sources (optional)
│   │   │   └── locals.tf          # Local values (optional)
│   │   └── cli/
│   │       └── commands.sh        # Non-TF CLI operations
│   └── tasks/
│       ├── status.json            # Pipeline state tracking
│       ├── validation-report.md   # Validation results
│       ├── tf-plan-result.md      # Terraform plan output
│       └── tf-apply-result.md     # Terraform apply output
├── .telemetry/
│   └── events.jsonl               # Local telemetry log
```

## Naming Convention for Requirements

Use kebab-case derived from the requirement:

- "I need an ECS server" → `ecs-server`
- "Setup a web application with RDS" → `web-app-with-rds`
- "Create VPC network for production" → `production-vpc-network`

## Multiple Requirements

Each requirement gets its own directory. They are independent and can be at different pipeline stages:

```
.aliyun-ai-ops-spec/
├── ecs-web-server/          # status: executed
├── production-database/     # status: validated
└── monitoring-setup/        # status: designing
```

## Status JSON Schema

```json
{
  "name": "requirement-name",
  "status": "pending|designing|designed|writing|plans-written|validating|validated|executing|executed|destroyed|failed",
  "mode": "fast-track|full",
  "environment": "production|dev-test",
  "change_type": "create|modify",
  "created_at": "2026-05-06T10:00:00Z",
  "updated_at": "2026-05-06T12:00:00Z",
  "phases": {
    "planning": "pending|in_progress|completed|failed",
    "writing": "pending|in_progress|completed|failed",
    "validation": "pending|in_progress|completed|failed",
    "execution": "pending|in_progress|completed|failed"
  },
  "state": {
    "state_id": "state-xxxxx",
    "last_plan_at": "2026-05-06T11:00:00Z",
    "last_apply_at": "2026-05-06T11:05:00Z",
    "last_destroy_at": null
  },
  "governance_baseline_check": {
    "mode": "full-12|fast-mvp-6|dev-advisory|skipped",
    "result": "pass|partial|not-run",
    "checked_at": "2026-05-06T10:25:00Z",
    "items": [
      { "id": "A1", "status": "pass|fail|advisory", "note": "..." }
    ]
  },
  "scenario_context": ["等保三级", "AI 应用"],
  "history": [
    {
      "phase": "planning",
      "status": "completed",
      "timestamp": "2026-05-06T10:30:00Z",
      "details": "Design approved by user"
    }
  ],
  "errors": []
}
```

### Field semantics

| Field | Owned by | Notes |
| --- | --- | --- |
| `status` | all skills | Pipeline stage; transitions are linear in Day-1, may loop in Day-2 |
| `mode` | `alibabacloud-planning` | `fast-track` vs `full` (governs validate depth + baseline check size) |
| `environment` | `alibabacloud-planning` | `production` vs `dev-test`; production-environment signal defined in [`planning/SKILL.md` → Mode-Aware Behavior Matrix](../../alibabacloud-planning/SKILL.md#mode-aware-behavior-matrix). Drives whether Phase 3c.5 fires and at what size. |
| `change_type` | `alibabacloud-planning` | `create` (Day-1) or `modify` (Day-2 iteration on existing infra) |
| `state.state_id` | `alibabacloud-executing-plans` | IaC Service remote state handle. **MUST be persisted on every plan response** and reused on every subsequent plan/apply/destroy call. See [`executing-plans/references/iac-service-api.md` → State Persistence](../../alibabacloud-executing-plans/references/iac-service-api.md). |
| `state.last_plan_at` / `last_apply_at` / `last_destroy_at` | `alibabacloud-executing-plans` | ISO timestamps of the most recent successful operation in each category |
| `governance_baseline_check` | `alibabacloud-planning` (Phase 3c.5) | Result of mode-aware governance baseline cross-check. `mode` records which check set ran (12 full / 6 MVP / 12 advisory / skipped); `items[]` lists individual check outcomes. Day-2 sessions overwrite with the new check result;the prior result is preserved only in `history[]`. See [`planning/references/governance-baselines.md`](../../alibabacloud-planning/references/governance-baselines.md) for the full check list and per-item IDs. |
| `scenario_context` | `alibabacloud-planning` (Phase 1) | Array of scenario tags matched in Phase 1 (等保 / AI / 出海 / 加密 / 容灾 / 多账号). Day-2 sessions **append** newly-matched scenarios, never shrink — unless a scenario is explicitly retired in design.md. Used by downstream skills to skip redundant scoping. |

> **Do not delete `state.state_id`** across re-iterations. Losing it
> orphans the remote Terraform state and forces a Day-1 deploy that may
> duplicate already-provisioned resources.
>
> **Do not delete `governance_baseline_check.items[]` entries with
> `status: advisory` during Day-2 overwrites** unless the underlying
> condition was actually fixed — silent disappearance of acknowledged
> risks defeats the audit trail.
