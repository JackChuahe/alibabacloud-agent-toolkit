# 模板索引

本目录收纳 SKILL.md 各章节引用的可复用片段。每个模板都自带场景说明，可直接拷贝到客户文档/工程项目里。

| 模板 | 关联 SKILL.md 章节 | 场景 |
| --- | --- | --- |
| [api-examples.md](api-examples.md) | 3. OpenAPI 集成方案 | Python / Java / Go SDK 调用、签名、错误处理示例 |
| [landing-zone-patterns.md](landing-zone-patterns.md) | 1. Landing Zone | 多账号架构典型模式（环境×业务线、共享服务、混合云） |
| [terraform-quickstart.md](terraform-quickstart.md) | 4. IaC (Terraform) | Provider 配置 + 凭证 + 状态后端入口 |
| [terraform-state-backend.md](terraform-state-backend.md) | 4. IaC (Terraform) | OSS + Tablestore 远程 state 后端模板 |

## 使用约定

- 所有模板中的链接必须是 `*.aliyun.com` 子域，与 SKILL.md 自身约束一致。
- AccessKey 等示例值统一用 `<占位符>`；生产凭证应使用 STS Token，参考 [api-examples.md](api-examples.md) 的“STS 凭证示例”段。
