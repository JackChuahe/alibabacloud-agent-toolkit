# Terraform 状态后端配置模板

## OSS + Tablestore 远程状态

### 前置条件

1. 创建 OSS Bucket（建议命名为 `terraform-state-{project}-{env}`）
2. 开启 OSS Bucket 版本控制
3. 创建 Tablestore 实例
4. 配置 RAM 策略，限制只有 CI/CD 和授权人员可写入

### Terraform 配置

```hcl
terraform {
  backend "oss" {
    # OSS 配置
    bucket         = "terraform-state-myproject-prod"
    prefix         = "terraform"
    key            = "state.tfstate"
    region         = "cn-hangzhou"
    acl            = "private"

    # Tablestore 分布式锁
    tablestore_endpoint = "https://myproject-tablestore.cn-hangzhou.ots.aliyuncs.com"
    tablestore_table    = "terraform_lock"

    # 加密（可选）
    encrypt = true
  }
}
```

### 初始化状态后端

```bash
# 初始化
terraform init

# 验证状态
terraform state list
```

---

## 多环境目录结构

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   ├── rds/
│   └── slb/
├── environments/
│   ├── dev/
│   │   ├── main.tf          # 包含 backend "oss" 配置
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── providers.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── providers.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── providers.tf
└── .gitignore
```

### 环境变量配置示例（prod/main.tf）

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    alicloud = {
      source  = "alicloud/alicloud"
      version = "~> 1.240.0"
    }
  }

  backend "oss" {
    bucket              = "terraform-state-myproject-prod"
    prefix              = "prod"
    key                 = "terraform.tfstate"
    region              = "cn-hangzhou"
    acl                 = "private"
    encrypt             = true
    tablestore_endpoint = "https://myproject.cn-hangzhou.ots.aliyuncs.com"
    tablestore_table    = "terraform_lock"
  }
}

provider "alicloud" {
  region = "cn-hangzhou"
}

# 引用模块
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr    = "10.0.0.0/16"
  environment = "prod"
}

module "ecs" {
  source = "../../modules/ecs"

  instance_type   = "ecs.g7.xlarge"
  instance_count  = 4
  vpc_id          = module.vpc.vpc_id
  vswitch_ids     = module.vpc.vswitch_ids
  security_group_id = module.vpc.security_group_id
  environment     = "prod"
}
```

### 敏感信息管理

**不要将密码、AK/SK 写入代码**。使用以下方式之一：

#### 方式一：环境变量

```bash
export ALICLOUD_ACCESS_KEY="<access-key>"
export ALICLOUD_SECRET_KEY="<secret-key>"
export ALICLOUD_REGION="cn-hangzhou"

terraform plan
```

#### 方式二：tfvars 文件（不提交到 Git）

```hcl
# terraform.tfvars（加入 .gitignore）
alicloud_access_key = "<access-key>"
alicloud_secret_key = "<secret-key>"
db_password         = "<db-password>"
```

#### 方式三：Vault / 密钥管理服务

```hcl
data "alicloud_kms_secret_versions" "db_password" {
  secret_name = "prod/db-password"
}

resource "alicloud_db_instance" "mysql" {
  # ...
  db_password = data.alicloud_kms_secret_versions.db_password.version
}
```

---

## CI/CD 集成（GitHub Actions 示例）

```yaml
name: Terraform
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Terraform Init
        working-directory: environments/prod
        run: terraform init

      - name: Terraform Plan
        if: github.event_name == 'pull_request'
        working-directory: environments/prod
        env:
          ALICLOUD_ACCESS_KEY: ${{ secrets.ALIYUN_ACCESS_KEY }}
          ALICLOUD_SECRET_KEY: ${{ secrets.ALIYUN_SECRET_KEY }}
        run: terraform plan -no-color -out=tfplan

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        working-directory: environments/prod
        env:
          ALICLOUD_ACCESS_KEY: ${{ secrets.ALIYUN_ACCESS_KEY }}
          ALICLOUD_SECRET_KEY: ${{ secrets.ALIYUN_SECRET_KEY }}
        run: terraform apply -auto-approve tfplan
```
