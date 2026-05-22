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
  "status": "pending|designing|designed|writing|plans-written|validating|validated|executing|executed|failed",
  "created_at": "2026-05-06T10:00:00Z",
  "updated_at": "2026-05-06T12:00:00Z",
  "phases": {
    "planning": "pending|in_progress|completed|failed",
    "writing": "pending|in_progress|completed|failed",
    "validation": "pending|in_progress|completed|failed",
    "execution": "pending|in_progress|completed|failed"
  },
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
