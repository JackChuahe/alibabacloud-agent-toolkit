# Terraform 快速上手模板

> 配套 SKILL.md "4. IaC (Terraform)" 章节使用。

## Provider 配置

```hcl
terraform {
  required_providers {
    alicloud = {
      source  = "alicloud/alicloud"
      version = "~> 1.240.0"
    }
  }
}

provider "alicloud" {
  region = "cn-hangzhou"
}
```

## 认证方式

- 长期凭证（仅 dev）：`ALICLOUD_ACCESS_KEY` / `ALICLOUD_SECRET_KEY` 环境变量。
- 推荐生产：使用 STS Token，参考 https://help.aliyun.com/zh/terraform/development-reference/ 中"凭据"章节。

## 状态后端

参考 [terraform-state-backend.md](terraform-state-backend.md)。

## 第三方权威文档（补充阿里云官方文档）

| 主题 | 链接 | 用途 |
| --- | --- | --- |
| Terraform 安装 | https://developer.hashicorp.com/terraform/install | HashiCorp 官方安装包 |
| Alibaba Cloud Provider | https://registry.terraform.io/providers/aliyun/alicloud/latest/docs | Provider 资源/数据源参考（Terraform Registry，规范且可搜索） |
| OSS state 后端语法 | https://developer.hashicorp.com/terraform/language/settings/backends/oss | HashiCorp 语法说明，配合 [terraform-state-backend.md](terraform-state-backend.md) 使用 |
| Module 规范 | https://developer.hashicorp.com/terraform/language/modules | Module 抽象与发布规范 |
| Workspace 管理 | https://developer.hashicorp.com/terraform/language/state/workspaces | 多环境（dev / staging / prod）隔离 |
| LZA 开源仓库 | https://github.com/aliyun/landing-zone-accelerator-on-alibaba-cloud | Alibaba Cloud LZA 完整 Terraform 项目源码 |

阿里云官方文档与第三方权威文档互为补充：阿里云文档把控产品语义与最佳实践，第三方文档（HashiCorp / Registry / GitHub）提供工具层标准与开源生态细节。
