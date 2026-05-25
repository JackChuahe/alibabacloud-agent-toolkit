# 参考文档索引

本文档是 public-itgov-pdsa-skill 的参考文档索引，包含所有官方文档引用。

## 使用原则

1. **以官方文档为准**——所有产品能力、参数、限制以阿里云帮助文档最新版本为准
2. **实时引用**——通过 WebFetch 工具按需拉取官网页面内容，确保信息时效性
3. **不内嵌大段文档**——SKILL.md 只保留核心逻辑，详细内容通过链接引用
4. **最佳实践补充**——对于详细的实施案例，参考 templates 目录下的模板文件

## 一、官方文档引用索引

### 1. 云采用框架 CAF（完整体系）

> 完整知识库详见 [caf-knowledge-base.md](caf-knowledge-base.md)

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| CAF 总览 | https://help.aliyun.com/zh/caf/what-is-cloud-adoption-framework | 云采用框架整体介绍 |
| 企业上云价值预估 | https://help.aliyun.com/zh/caf/enterprise-cloud-value-estimate | 四维价值评估 |
| 企业上云主要动机 | https://help.aliyun.com/zh/caf/enterprise-motivations-for-cloud-migration | 四大类动机分析 |
| 云战略架构规划 | https://help.aliyun.com/zh/caf/cloud-strategic-architecture-planning | 四维架构规划+CCoE |
| 云计算成本和效益 | https://help.aliyun.com/zh/caf/cloud-computing-costs-and-benefits | CapEx→OpEx 成本框架 |
| 企业组织模型 | https://help.aliyun.com/zh/caf/organizational-model-required-for-cloud-adoption-and-core-responsibilities-of-enterprises | CCoE 三层组织分工 |
| 云战略路线图 | https://help.aliyun.com/zh/caf/cloud-strategy-roadmap | 三阶段演进模型 |
| 云技术采用 | https://help.aliyun.com/zh/caf/cloud-technology-adoption | IaaS/PaaS/SaaS 选型 |

### 2. Landing Zone（CAF 核心章节）

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| LZ 组成部分（八大模块） | https://help.aliyun.com/zh/caf/components-of-a-landing-zone-on-alibaba-cloud/ | Landing Zone 架构全貌 |
| LZ 场景方案（两种路径） | https://help.aliyun.com/zh/caf/options-for-implementation/ | 云治理中心 vs 场景方案 |
| AI Landing Zone | https://help.aliyun.com/zh/caf/ai-lz-definition/ | AI 治理框架 |
| LZ Accelerator | https://help.aliyun.com/zh/caf/landing-zone-accelerator | Terraform 自动化搭建（阿里云官方说明）；GitHub 源码：https://github.com/aliyun/landing-zone-accelerator-on-alibaba-cloud |
| 企业多账号统一架构 | https://help.aliyun.com/zh/caf/enterprise-multi-account-unified-architecture-solution | 五类核心账号 |
| 多账号付款管理 | https://help.aliyun.com/zh/caf/multi-account-enterprise-payment-management-solution | 财务管理方案 |
| 云SSO多账号单点登录 | https://help.aliyun.com/zh/caf/implement-single-sign-on-for-multiple-accounts-based-on-cloudsso | CloudSSO + 资源目录 |
| 操作日志统一归集审计 | https://help.aliyun.com/zh/caf/unified-collection-and-audit-of-multi-account-operation-logs | ActionTrail + SLS + OSS |
| 配置统一合规审计 | https://help.aliyun.com/zh/caf/unified-compliance-audit-for-multi-account-configurations | Config + 资源目录 |
| CEN-TR企业级云上互联 | https://help.aliyun.com/zh/caf/uses-cen-instances-and-transit-routers-to-establish-enterprise-grade-network-connections | 六大分区网络架构 |
| 基于GitLab账号工厂 | https://help.aliyun.com/zh/caf/implement-an-account-factory-based-on-gitlab | 自动化账号开通 |
| AI 资源规划 | https://help.aliyun.com/zh/caf/resource-planning-ai | AI LZ 资源规划 |

### 3. 应用上云

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| 企业应用上云规划 | https://help.aliyun.com/zh/caf/cloud-migration-plan-for-enterprise-applications/ | 上云规划全流程 |
| 应用上云实施 | https://help.aliyun.com/zh/caf/implementation-of-application-cloud-migration/ | 八步实施流程 |
| 云迁移中心 CMH | https://help.aliyun.com/zh/caf/cloud-migration-tools | 全生命周期迁移工具 |
| 扩展云化成果 | https://help.aliyun.com/zh/caf/expanding-cloud-to-cloud-results | 五维成熟度评估 |

### 4. 运营治理

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| 日常运维管理 | https://help.aliyun.com/zh/caf/daily-operation-and-maintenance | CCoE 运维流程重构 |
| 风险管理方法论 | https://help.aliyun.com/zh/caf/risk-management-methodology/ | 风险治理理论+实践 |
| 治理基线总览 | https://help.aliyun.com/zh/caf/governance-baselines-on-alibaba-cloud/ | 四大治理基线入口 |
| 身份权限治理基线 | https://help.aliyun.com/zh/caf/governance-baseline-for-identities-and-permissions | MFA/最小权限/审计 |
| 数据安全基线 | https://help.aliyun.com/zh/caf/data-security-baseline | 分级分类/加密/隔离 |
| 通用安全基线 | https://help.aliyun.com/zh/caf/general-security-baseline | DDoS/防火墙/WAF |
| 业务连续性基线 | https://help.aliyun.com/zh/caf/business-continuity-baseline | RTO/RPO/容灾 |
| 问题解决 | https://help.aliyun.com/zh/caf/problem-resolution | 五种解决路径 |
| 基础设施自动化 | https://help.aliyun.com/zh/caf/infrastructure-automation | IaC/OOS/RAM 三大范式 |
| 成本管理与优化 | https://help.aliyun.com/zh/caf/cost-management-and-optimization | IPIE闭环 |

### 5. Landing Zone & 资源目录（产品文档）

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| 资源目录总览 | https://help.aliyun.com/zh/resource-directory/ | 了解资源目录核心概念 |
| 创建资源目录 | https://help.aliyun.com/zh/resource-directory/user-guide/create-a-resource-directory/ | 落地操作指南 |
| 邀请成员 | https://help.aliyun.com/zh/resource-directory/user-guide/invite-member/ | 添加成员账号 |
| 资源共享 | https://help.aliyun.com/zh/resource-directory/user-guide/share-a-resource/ | 跨账号资源共享 |
| 云企业网 CEN | https://help.aliyun.com/zh/cen/ | 跨 VPC / 跨地域互联 |
| 云企业网快速入门 | https://help.aliyun.com/zh/cen/getting-started/ | CEN 快速上手 |
| VPC 对等连接 | https://help.aliyun.com/zh/vpc/developer-reference/connect-vpcs/ | 同地域 VPC 互联 |
| RAM 权限策略 | https://help.aliyun.com/zh/ram/user-guide/overview-4/ | 理解 RAM 策略语法 |
| RAM 角色 | https://help.aliyun.com/zh/ram/user-guide/create-a-ram-role/ | 跨账号/跨服务授权 |
| SSO 单点登录 | https://help.aliyun.com/zh/ram/user-guide/user-based-sso/ | 企业身份对接 |
| 安全组 | https://help.aliyun.com/zh/ecs/user-guide/configure-inbound-rules-for-a-security-group/ | 网络安全策略 |

### 5.1 CloudSSO 云SSO（产品文档）

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| 云SSO 产品概述 | https://help.aliyun.com/zh/cloudsso/product-overview/what-is-cloudsso | CloudSSO 功能特性、产品架构、与 RAM 关系 |
| 基本概念 | https://help.aliyun.com/zh/cloudsso/product-overview/terms | 云SSO 核心术语定义 |
| 使用限制 | https://help.aliyun.com/zh/cloudsso/product-overview/limits | 配额、限制条件 |
| 开始使用云SSO | https://help.aliyun.com/zh/cloudsso/getting-started/getting-started-with-cloudsso | 快速入门完整步骤 |
| 操作指南总览 | https://help.aliyun.com/zh/cloudsso/user-guide/ | 全部操作指南目录 |
| 访问配置概述 | https://help.aliyun.com/zh/cloudsso/user-guide/overview-1#concept-2090837 | 什么是访问配置、权限策略类型 |
| 创建访问配置 | https://help.aliyun.com/zh/cloudsso/user-guide/create-an-access-configuration#task-2091273 | 创建 RAM 角色方式的访问配置 |
| 多账号授权概述 | https://help.aliyun.com/zh/cloudsso/user-guide/overview-2#concept-2090970 | 多账号授权机制说明 |
| 在 RD 账号上授权 | https://help.aliyun.com/zh/cloudsso/user-guide/assign-access-permissions-on-the-accounts-in-a-resource-directory#task-2090971 | 将访问配置部署到 RD 账号 |
| 配置 RAM 用户同步 | https://help.aliyun.com/zh/cloudsso/user-guide/create-a-ram-user-provisioning#task-2258334 | RAM 用户方式的同步配置 |
| SCIM 密钥过期报警 | https://help.aliyun.com/zh/cloudsso/use-cases/configure-alert-notifications-of-scim-credential-expiration-and-saml-signing-certificate-expiration | SCIM/SAML 证书过期监控 |
| 分级授权管理 | https://help.aliyun.com/zh/cloudsso/use-cases/cloudsso-hierarchical-authorization-management | 分级授权实践教程 |
| Terraform 集成 | https://help.aliyun.com/zh/cloudsso/developer-reference/create-a-cloud-sso-user-through-terraform | 用 Terraform 管理云SSO |
| CLI 集成 | https://help.aliyun.com/zh/cloudsso/developer-reference/cli-integration-example | 用 CLI 登录云SSO |

### 6. 云卓越架构（Well-Architected Framework）

> 完整知识库详见 [wa-knowledge-base.md](wa-knowledge-base.md)

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| **框架总览** | | |
| 前言（框架介绍） | https://help.aliyun.com/zh/document_detail/2362204.html | 云卓越架构框架总览 |
| 学习 | https://help.aliyun.com/zh/document_detail/2882403.html | 理论方法和设计原则 |
| 度量 | https://help.aliyun.com/zh/document_detail/2882554.html | 260+检测指标和评估工具 |
| 优化 | https://help.aliyun.com/zh/document_detail/2882553.html | 改进指引和线上治理 |
| 修订记录 | https://help.aliyun.com/zh/document_detail/2901217.html | 文档更新历史 |
| 结束语 | https://help.aliyun.com/zh/document_detail/2362209.html | 核心理念 |
| **五大支柱（学习阶段）** | | |
| 安全支柱 | https://help.aliyun.com/zh/document_detail/2536222.html | 安全生命周期管理 |
| 稳定支柱 | https://help.aliyun.com/zh/document_detail/2536221.html | 高可用和容灾设计 |
| 成本支柱 | https://help.aliyun.com/zh/document_detail/2536195.html | 成本管理框架 |
| 效率支柱 | https://help.aliyun.com/zh/document_detail/2536122.html | 运营卓越 |
| 性能支柱 | https://help.aliyun.com/zh/document_detail/2530946.html | 性能工程生命周期 |
| **四大支柱（优化阶段）** | | |
| 安全优化 | https://help.aliyun.com/zh/document_detail/2901215.html | 安全架构优化 |
| 稳定优化 | https://help.aliyun.com/zh/document_detail/2901212.html | 高可用架构优化 |
| 成本优化 | https://help.aliyun.com/zh/document_detail/2901214.html | 成本策略/监控/优化 |
| 效率优化 | https://help.aliyun.com/zh/document_detail/2901213.html | 资源利用率优化 |
| **度量工具** | | |
| 云治理中心概览 | https://help.aliyun.com/zh/cgc/product-overview/what-is-cloud-governance-center | 云治理中心介绍 |
| 治理成熟度检测 | https://help.aliyun.com/zh/cgc/user-guide/governance-maturity-check/ | 260+指标客观度量 |
| Well-Architected Tool | https://help.aliyun.com/zh/cgc/user-guide/well-architected-tool | 架构化问卷主观度量 |
| 快速修复风险项 | https://help.aliyun.com/zh/cgc/user-guide/quickly-fix-risk-items | 线上自助治理 |
| **解决方案汇总** | | |
| 安全解决方案 | https://help.aliyun.com/zh/document_detail/2901230.html | 安全最佳实践方案 |
| 稳定解决方案 | https://help.aliyun.com/zh/document_detail/2929032.html | 稳定最佳实践方案 |
| 成本解决方案 | https://help.aliyun.com/zh/document_detail/2929036.html | 成本最佳实践方案 |
| 效率解决方案 | https://help.aliyun.com/zh/document_detail/2929037.html | 效率最佳实践方案 |
| **信任中心** | | |
| 阿里云信任中心 | https://security.aliyun.com/trust-center | 安全合规信任中心 |

### 7. OpenAPI & SDK

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| OpenAPI 开发者门户 | https://next.api.aliyun.com/ | API 搜索、在线调试 |
| API 签名机制 | https://help.aliyun.com/zh/sdk/developer-reference/v3-signing-mechanism | V3 签名算法 |
| SDK 安装与使用 | https://help.aliyun.com/zh/sdk/developer-reference/installation/ | SDK 安装指南 |
| 凭证管理 | https://help.aliyun.com/zh/sdk/developer-reference/v3-configuration/ | 凭证配置方式 |
| STS 临时授权 | https://help.aliyun.com/zh/sts/developer-reference/assume-role/ | STS Token 获取 |
| ECS RAM Role | https://help.aliyun.com/zh/ram/user-guide/attach-a-ram-role-to-an-ecs-instance/ | ECS 实例角色 |
| API 限流说明 | https://help.aliyun.com/zh/sdk/developer-reference/faq-about-limits/ | 限流策略与应对 |
| 错误中心 | https://next.api.aliyun.com/api/Ecs/2014-05-26/DescribeInstances | 常见错误码 |

### 8. Terraform & IaC

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| Terraform 总览（阿里云） | https://help.aliyun.com/zh/terraform/ | 阿里云 Terraform 文档体系入口 |
| Terraform 是什么 | https://help.aliyun.com/zh/terraform/what-is-terraform | 阿里云对 Terraform 的介绍 |
| 快速入门 | https://help.aliyun.com/zh/terraform/quick-start-1/ | Provider 安装 + 第一个资源 |
| 开发参考 | https://help.aliyun.com/zh/terraform/development-reference/ | Provider 资源参考、状态管理 |
| 实践教程 | https://help.aliyun.com/zh/terraform/practice-tutorial/ | 23+ 云服务的端到端示例 |
| 解决方案 | https://help.aliyun.com/zh/terraform/solution/ | 状态后端、模块化、多环境工程 |
| Terraform 官方安装 | https://developer.hashicorp.com/terraform/install | HashiCorp 官方安装包与版本说明 |
| Alibaba Cloud Provider（Registry） | https://registry.terraform.io/providers/aliyun/alicloud/latest/docs | Provider 资源/数据源参考（Terraform Registry，规范且可搜索） |
| Terraform State 远程后端语法 | https://developer.hashicorp.com/terraform/language/settings/backends/oss | OSS state 后端的 HashiCorp 语法说明 |
| Terraform Modules | https://developer.hashicorp.com/terraform/language/modules | Module 抽象与发布规范 |
| Terraform Workspaces | https://developer.hashicorp.com/terraform/language/state/workspaces | 多环境管理（dev/staging/prod） |
| LZA GitHub 仓库 | https://github.com/aliyun/landing-zone-accelerator-on-alibaba-cloud | Alibaba Cloud LZA 开源代码（issue / 示例 / 模块） |

> 阿里云相关 Provider 与最佳实践以 `help.aliyun.com/zh/terraform/` 子树为主线；HashiCorp 官方文档、Terraform Registry、阿里云在 GitHub 上的开源仓库可作为细节补充直接引用。

### 9. 合规与治理（产品文档）

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| 配置审计 Config | https://help.aliyun.com/zh/config/ | 资源合规检查 |
| Config Rule 列表 | https://help.aliyun.com/zh/config/developer-reference/rules/ | 可用规则参考 |
| 操作审计 ActionTrail | https://help.aliyun.com/zh/actiontrail/ | API 调用日志 |
| 创建跟踪 | https://help.aliyun.com/zh/actiontrail/user-guide/create-a-multi-account-trail/ | 多账号审计跟踪 |
| 密钥管理 KMS | https://help.aliyun.com/zh/kms/ | 数据加密 |
| 云安全中心 | https://help.aliyun.com/zh/sas/ | 主机安全 |
| 标签管理 | https://help.aliyun.com/zh/tag/ | 资源标签策略 |
| 费用预算 | https://help.aliyun.com/zh/budget/ | 成本预算与告警 |

### 10. 阿里云 Agent Skills 门户

| 主题 | 文档链接 | 用途 |
|------|---------|------|
| Skills 门户首页 | https://skills.aliyun.com/ | 发现、搜索和安装阿里云官方 Agent Skills |
| 了解阿里云 Skills | https://help.aliyun.com/zh/document_detail/3026637.html | Skills 产品介绍和使用指南 |
| HITL 安全指南 | https://help.aliyun.com/zh/skillsportal/aliyun-hitl-agent-security-guide | HITL 人机协同安全机制说明 |

## 二、模板与示例

Skill 提供的模板和示例文件位于 `templates/` 目录下，供参考使用：

### 模板文件结构

```
public-itgov-pdsa-skill/
├── SKILL.md
├── reference.md          ← 本文件
├── examples.md           # 典型客户场景示例
├── templates/            # 模板目录
│   ├── landing-zone-patterns.md   # Landing Zone 架构模式
│   ├── api-examples.md            # OpenAPI 调用示例
│   └── terraform-state-backend.md # Terraform 状态后端配置
└── scripts/
```

### 模板使用方式

在 SKILL.md 或回答客户问题时，通过相对路径引用模板：

```markdown
参考 Landing Zone 架构模式 [landing-zone-patterns.md](templates/landing-zone-patterns.md) 了解更多实现方案。
```

**注意**：所有内容均基于阿里云官方公开文档，确保信息的可移植性和时效性。

## 三、实时引用策略

当客户问题涉及以下情况时，使用 WebFetch 工具实时拉取官网内容：

1. **产品更新**——官网有新功能或参数变更
2. **具体参数确认**——如 API 的入参/出参、限制条件
3. **价格信息**——计费模式、套餐价格（以官网实时价格为准）
4. **最新最佳实践**——阿里云官方发布的最新方案

实时引用示例流程：

```
客户问具体参数 → WebFetch 拉取官网对应 API 文档页面 → 提取关键信息 → 回答并附文档链接
```

## 四、文档更新检查清单

定期（建议每月）检查以下事项：

- [ ] 所有官方文档链接可正常访问
- [ ] 产品版本号已更新到最新（如 Terraform Provider 版本）
- [ ] 新增的阿里云产品是否补充到索引中
- [ ] 示例和模板是否需要更新
- [ ] 是否有过时的最佳实践需要调整
