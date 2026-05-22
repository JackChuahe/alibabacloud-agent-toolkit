---
name: alibabacloud-terraform-codegen
description: "Generate and modify Alibaba Cloud Terraform HCL code. Triggers on phrases like: write Terraform for Alibaba Cloud, create alicloud Terraform config, generate HCL for ECS, Terraform code for VPC, alicloud infrastructure as code, Terraform resource for RDS, modify Terraform configuration, alicloud provider Terraform."
license: MIT
metadata:
  author: Alibaba Cloud
  version: "0.1.0"
compatibility:
  tools:
    - mcp__plugin_alibabacloud-spec-ops_alibabacloud-spec-ops__AlibabaCloud___CallCLI
    - mcp__plugin_alibabacloud-spec-ops_alibabacloud-spec-ops__AlibabaCloud___SearchDocument
    - mcp__plugin_alibabacloud-spec-ops_alibabacloud-spec-ops__AlibabaCloud___ReadDocument
---

# Alibaba Cloud Terraform Code Generator

Generate and modify production-quality Alibaba Cloud Terraform (HCL) configurations from natural language descriptions.

## Safety Rules

1. **ONLY use the `alibabacloud` MCP server tools.** The permitted tools are:
   - `AlibabaCloud___CallCLI` — Execute IaCService CLI commands to query Terraform product/resource metadata
   - `AlibabaCloud___SearchDocument` — Search Alibaba Cloud documentation by keyword to find relevant document URLs
   - `AlibabaCloud___ReadDocument` — Read a specific document by URL (must use URLs obtained from `SearchDocument`)
2. **Do NOT execute `terraform plan`, `terraform apply`, or any other Terraform commands locally.** Generated HCL code is for review. Execution is handled by the `alibabacloud:executing-plans` skill via remote IaC Service.
3. **Always remind the user to review the generated HCL** before execution, especially when resources involve costs, data deletion, or security-sensitive configurations.

## IaCService API Reference

All IaCService APIs are invoked through `AlibabaCloud___CallCLI`:

| API | CLI Command | Purpose |
| --- | ----------- | ------- |
| ListProducts | `aliyun iacservice list-products` | List all Alibaba Cloud products that support Terraform |
| ListResourceTypes | `aliyun iacservice list-resource-types --product <product>` | List Terraform resource types for a specific product |
| GetResourceType | `aliyun iacservice get-resource-type --resource-type <resourceType>` | Get all attributes and schema for a Terraform resource type (e.g., `alicloud_vpc`) |
| ValidateModule | `aliyun iacservice validate-module --template-body <tf-content>` | Validate Terraform syntax without execution |

## Workflow

Follow these steps strictly in order:

### Step 1: Understand the User's Intent

Parse the user's natural language request to identify:
- The target Alibaba Cloud service(s) (e.g., ECS, VPC, RDS, OSS, SLB, ACK)
- The desired infrastructure (e.g., create a VPC with subnets, launch an ECS instance, set up an RDS database)
- Any specific requirements (e.g., region, instance type, CIDR blocks, security group rules)
- Whether this is a new configuration or a modification to existing HCL code

### Step 2: Discover Supported Products and Resource Types

Call `AlibabaCloud___CallCLI` with `aliyun iacservice list-products` to confirm the target product supports Terraform.

Then call `AlibabaCloud___CallCLI` with `aliyun iacservice list-resource-types --product <product>` to discover the correct Terraform resource type names (e.g., `alicloud_vpc`, `alicloud_instance`, `alicloud_db_instance`).

- If the user's request spans multiple products, query each product separately
- Present the matched resource types to the user if there is ambiguity

### Step 3: Get Resource Type Schema

Call `AlibabaCloud___CallCLI` with `aliyun iacservice get-resource-type --resource-type <resourceType>` (e.g., `--resource-type alicloud_vpc`) to retrieve the full attribute schema.

- Identify all required and optional attributes
- Understand attribute types, constraints, and valid values
- Note any attribute dependencies or conflicts

### Step 4: Consult Terraform Documentation

Documentation lookup is a **two-step process**:

1. **Search**: Use `AlibabaCloud___SearchDocument` with the resource type name (e.g., `alicloud_vpc`) as the keyword to find relevant documentation URLs
2. **Read**: Use `AlibabaCloud___ReadDocument` with a URL obtained from the search results to read the full document content

**Important:** You must always search first to get valid document URLs. Do NOT pass arbitrary URLs or resource names directly to `ReadDocument` — it only accepts URLs returned by `SearchDocument`.

After reading the documentation:
- Review usage examples and best practices
- Understand attribute-level details that may not be captured in the schema
- Check for known limitations or caveats
- Look for related data sources that may be useful (e.g., `data.alicloud_zones`, `data.alicloud_instance_types`)

### Step 5: Generate or Modify HCL Code

Based on the gathered information, write HCL following the Code Generation Rules and Common Patterns below.

### Step 6: Present the Code

Present the generated HCL as a **single complete file** with:
- A brief explanation of the infrastructure being created
- A list of resources and their relationships
- Any variables the user needs to customize
- **A reminder to review before execution**
- Warnings for any cost-incurring or destructive resources

**Output format:** One single code block containing ALL terraform code (provider + variables + locals + data + resources + outputs). Do NOT split into separate files or code blocks.

## Error Recovery with Documentation

When you encounter unclear attribute definitions or constraints:

1. Use `AlibabaCloud___SearchDocument` with relevant keywords (resource type name, attribute name, error message) to find documentation URLs
2. Use `AlibabaCloud___ReadDocument` with the URL from search results to read the full documentation
3. Cross-reference the schema from `get-resource-type` (via `AlibabaCloud___CallCLI`) with the documentation
4. Provide the user with links to official documentation for edge cases

---

## Code Generation Rules

1. **Single file only** — ALL generated code MUST be in one file (`main.tf`), never split into multiple files
2. **File internal order** — `terraform {}` → `provider` → `variables` → `locals` → `data sources` → `resources` → `outputs`
3. **Always use data sources** for dynamic values (zones, images, instance types)
4. **Always use variables with defaults** — every variable MUST have a `default` value so the code can deploy without any input
5. **Always tag resources** with project, environment, managed-by
6. **Always output** important values (IDs, IPs, endpoints)
7. **Always encrypt** where supported
8. **Never expose** credentials, use RAM roles
9. **Use MCP** to verify resource attributes via `AlibabaCloud___CallCLI` with IaCService APIs

## Provider Configuration

```hcl
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = ">= 1.220.0"
    }
  }
}

provider "alicloud" {
  region = var.region
}
```

## HCL Best Practices

- **Provider configuration**: Always include `region` in the provider block or as a variable
- **Resource naming**: Use descriptive resource names (e.g., `alicloud_vpc.main`, `alicloud_instance.web_server`)
- **Tags**: Include tags for resource identification and cost tracking
- **Dependencies**: Use `depends_on` only when implicit dependencies are insufficient
- **Security groups**: Default to restrictive rules; only open necessary ports
- **State management**: Suggest remote backend configuration for team usage
- **Single file**: All code in one main.tf — do NOT split into variables.tf, outputs.tf, etc.

## Principles

- **Correctness** — Always verify resource schemas and documentation before generating code; never guess attribute names or valid values
- **Best practices** — Follow Terraform and Alibaba Cloud best practices for security, naming, and structure
- **Completeness** — Include all required attributes and sensible defaults for optional ones
- **Readability** — Write clean, well-commented HCL that is easy to understand and maintain
- **Safety** — Warn about cost implications and destructive operations; never execute Terraform commands directly

---

## Common Patterns

### Networking Foundation
```hcl
data "alicloud_zones" "default" {
  available_resource_creation = "VSwitch"
}

resource "alicloud_vpc" "main" {
  vpc_name   = "${var.project}-${var.env}-vpc"
  cidr_block = var.vpc_cidr
  tags       = local.common_tags
}

resource "alicloud_vswitch" "main" {
  count        = length(var.zone_ids)
  vswitch_name = "${var.project}-${var.env}-vsw-${count.index}"
  vpc_id       = alicloud_vpc.main.id
  cidr_block   = cidrsubnet(var.vpc_cidr, 4, count.index)
  zone_id      = var.zone_ids[count.index]
  tags         = local.common_tags
}

resource "alicloud_security_group" "main" {
  name        = "${var.project}-${var.env}-sg"
  vpc_id      = alicloud_vpc.main.id
  description = "Managed by Terraform"
  tags        = local.common_tags
}
```

### ECS Instance
```hcl
data "alicloud_images" "default" {
  name_regex  = var.image_regex
  most_recent = true
  owners      = "system"
}

resource "alicloud_instance" "main" {
  count                      = var.instance_count
  instance_name              = "${var.project}-${var.env}-${var.role}-${count.index + 1}"
  instance_type              = var.instance_type
  image_id                   = data.alicloud_images.default.images[0].id
  vswitch_id                 = alicloud_vswitch.main[count.index % length(alicloud_vswitch.main)].id
  security_groups            = [alicloud_security_group.main.id]
  system_disk_category       = "cloud_essd"
  system_disk_size           = var.system_disk_size
  internet_max_bandwidth_out = var.public_bandwidth
  tags                       = merge(local.common_tags, { Role = var.role })
}
```

### RDS Database
```hcl
resource "alicloud_db_instance" "main" {
  engine               = var.db_engine
  engine_version       = var.db_engine_version
  instance_type        = var.db_instance_type
  instance_storage     = var.db_storage
  instance_name        = "${var.project}-${var.env}-db"
  vswitch_id           = alicloud_vswitch.main[0].id
  security_ips         = [var.vpc_cidr]
  category             = "HighAvailability"
  zone_id              = var.zone_ids[0]
  zone_id_slave_a      = var.zone_ids[1]
  tags                 = local.common_tags
}

resource "alicloud_db_database" "main" {
  instance_id = alicloud_db_instance.main.id
  name        = var.db_name
  character_set = "utf8mb4"
}

resource "alicloud_db_account" "main" {
  db_instance_id   = alicloud_db_instance.main.id
  account_name     = var.db_account_name
  account_password = var.db_account_password
  account_type     = "Super"
}
```

### SLB Load Balancer
```hcl
resource "alicloud_slb_load_balancer" "main" {
  load_balancer_name = "${var.project}-${var.env}-slb"
  address_type       = "internet"
  load_balancer_spec = var.slb_spec
  vswitch_id         = alicloud_vswitch.main[0].id
  tags               = local.common_tags
}

resource "alicloud_slb_listener" "http" {
  load_balancer_id = alicloud_slb_load_balancer.main.id
  frontend_port    = 80
  backend_port     = var.app_port
  protocol         = "http"
  bandwidth        = -1
  health_check     = "on"
  health_check_uri = var.health_check_path
}

resource "alicloud_slb_server_group" "main" {
  load_balancer_id = alicloud_slb_load_balancer.main.id
  name             = "${var.project}-${var.env}-sg"
}

resource "alicloud_slb_server_group_server_attachment" "main" {
  count           = var.instance_count
  server_group_id = alicloud_slb_server_group.main.id
  server_id       = alicloud_instance.main[count.index].id
  port            = var.app_port
}
```

### OSS Bucket
```hcl
resource "alicloud_oss_bucket" "main" {
  bucket = "${var.project}-${var.env}-${var.bucket_purpose}"
  acl    = "private"

  server_side_encryption_rule {
    sse_algorithm = "KMS"
  }

  versioning {
    status = "Enabled"
  }

  lifecycle_rule {
    enabled = true
    prefix  = "logs/"
    expiration {
      days = 90
    }
  }

  tags = local.common_tags
}
```

### NAT Gateway (Internet Access for Private Subnets)
```hcl
resource "alicloud_nat_gateway" "main" {
  vpc_id           = alicloud_vpc.main.id
  nat_gateway_name = "${var.project}-${var.env}-nat"
  payment_type     = "PayAsYouGo"
  vswitch_id       = alicloud_vswitch.main[0].id
  nat_type         = "Enhanced"
  tags             = local.common_tags
}

resource "alicloud_eip_address" "nat" {
  address_name = "${var.project}-${var.env}-nat-eip"
  payment_type = "PayAsYouGo"
  bandwidth    = "20"
  tags         = local.common_tags
}

resource "alicloud_eip_association" "nat" {
  allocation_id = alicloud_eip_address.nat.id
  instance_id   = alicloud_nat_gateway.main.id
  instance_type = "Nat"
}

resource "alicloud_snat_entry" "main" {
  snat_table_id     = alicloud_nat_gateway.main.snat_table_ids
  source_vswitch_id = alicloud_vswitch.main[0].id
  snat_ip           = alicloud_eip_address.nat.ip_address
}
```

## Locals Template

```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.env
    ManagedBy   = "terraform"
    CreatedBy   = "alibabacloud-spec-ops"
  }
}
```

## Variables Template

**RULE: Every variable MUST have a `default` value.** This ensures the code can be deployed directly without requiring any manual input. No exceptions.

```hcl
variable "project" {
  description = "Project name for resource naming"
  type        = string
  default     = "myproject"
}

variable "env" {
  description = "Environment (production, staging, development)"
  type        = string
  default     = "production"
}

variable "region" {
  description = "Alibaba Cloud region"
  type        = string
  default     = "cn-hangzhou"
}

variable "zone_ids" {
  description = "Availability zone IDs"
  type        = list(string)
  default     = ["cn-hangzhou-h", "cn-hangzhou-i"]
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}
```

**Forbidden:**
```hcl
# ❌ WRONG — no default, will block deployment
variable "project" {
  type = string
}
```
