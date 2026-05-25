# 阿里云云采用框架（CAF）完整知识库

> 本文件是基于阿里云官方帮助文档 https://help.aliyun.com/zh/caf/ 递归扫描提取的完整知识库。
> Skill 在回答 CAF 相关问题时，应优先参考本文件，需要最新或更详细信息时通过 WebFetch 实时拉取对应链接。

## 一、CAF 总体框架

### 1.1 什么是云采用框架

云采用框架（Cloud Adoption Framework, CAF）为企业上云提供策略和技术的指导原则和最佳实践。借鉴 ITIL 服务生命周期方法论，映射至云服务四个核心阶段：

| 阶段 | 核心目标 | 对应 CAF 章节 |
|------|---------|--------------|
| 云战略 | 基于企业整体战略规划制定云战略 | 上云战略 |
| 上好云 | 结合云战略的规划及各方面的要求，做好整体解决方案 | 上云准备 + 应用上云 |
| 用好云 | 在持续落地的过程中进行横向和纵向扩展 | 用好云 |
| 管好云 | 发现和解决运维和运营过程中的问题和风险 | 运营治理 |

三大横向基础模块贯穿全生命周期：组织/文化/人才、安全与合规、良好的云架构设计。

**文档链接**：https://help.aliyun.com/zh/caf/what-is-cloud-adoption-framework

### 1.2 完整文档目录树

```
云采用框架 CAF
├── 背景介绍
├── 上云战略
│   ├── 企业上云价值预估
│   ├── 企业上云的主要动机
│   ├── 云战略架构规划
│   ├── 云计算成本和效益
│   ├── 上云所需的企业组织模型及其核心职责
│   └── 云战略路线图
├── 上云准备
│   ├── 云技术采用（IaaS/PaaS/SaaS 选型）
│   ├── Landing Zone 主要组成部分（八大模块）
│   │   ├── 资源规划 → 企业多账号统一架构方案
│   │   ├── 财务管理 → 多账号企业付款管理方案
│   │   ├── 身份权限 → 基于云SSO实现多账号单点登录
│   │   ├── 合规审计 → 多账号操作日志统一归集与审计
│   │   ├── 合规审计 → 多账号配置统一合规审计
│   │   ├── 网络规划 → 基于CEN-TR实现企业级云上互联
│   │   └── 自动化 → 基于GitLab实现账号工厂
│   ├── Landing Zone 场景方案（两种实现路径）
│   ├── AI Landing Zone（三种AI范式 + 八大模块扩展）
│   └── Landing Zone Accelerator（基于Terraform的开源加速器）
├── 应用上云
│   ├── 企业应用上云规划
│   │   ├── 上云评估模型
│   │   ├── 业务调研
│   │   ├── 应用上云策略及决策流程
│   │   └── 应用上云优先级及计划
│   └── 应用上云实施
│       ├── 实施流程 → 应用调研 → 方案设计 → 迁移实施
│       ├── 测试与验证 → 割接与上线
│       ├── 上云典型场景
│       └── 上云工具支持（云迁移中心 CMH）
├── 用好云
│   ├── 云化工具
│   └── 扩展云化成果（五维成熟度评估）
├── 运营治理
│   ├── 日常运维管理
│   ├── 风险管理方法论
│   ├── 治理基线
│   │   ├── 身份权限治理基线
│   │   ├── 数据安全基线
│   │   ├── 通用安全基线
│   │   └── 业务连续性基线
│   ├── 问题解决（五种解决路径）
│   ├── 基础设施自动化（三大自动化范式）
│   └── 成本管理与优化（IPIE闭环）
├── 典型实践案例
├── 结束语
└── 基本概念
```

## 二、上云战略

### 2.1 企业上云价值预估

从四个维度评估上云价值：

- **技术维度**：云原生架构实现跨地域协同，敏捷开发应对业务需求，高可靠性保障业务连续性
- **运营维度**：运维从硬件维护升级为自动化管理，IT服务标准化，财务指标对齐
- **业务维度**：依托"数据"与"在线"重构传统流程，孵化数字化新业务
- **组织维度**：云底座支撑协作数字化，培育数据敏锐度与创新思维

**链接**：https://help.aliyun.com/zh/caf/enterprise-cloud-value-estimate

### 2.2 企业上云的主要动机

四大类动机：

- **追求新机会**：拓展市场与升级技术
- **防范风险**：强化数据保护、合规及业务连续性
- **提升效能**：优化研发运维流程与组织协同
- **控制成本**：削减机房建设、日常运行及大额资本支出

**链接**：https://help.aliyun.com/zh/caf/enterprise-motivations-for-cloud-migration

### 2.3 云战略架构规划

实施前需完成"收集现状、规划未来、制定路径"三步，涵盖四大维度：

- **组织架构规划**：组建专职团队，成立云卓越中心（CCoE），统筹技术/业务/财务
- **业务架构规划**：盘点业务层/平台层/数据层/资源层现状，明确实施边界
- **部署架构规划**：依托 Landing Zone 设计未来架构并输出迁移方案
- **技术架构规划**：初期"平迁"以维稳，后期逐步改造释放云价值

**链接**：https://help.aliyun.com/zh/caf/cloud-strategic-architecture-planning

### 2.4 云计算成本和效益

核心财务转型：从资本性支出（CapEx）转变为运营性支出（OpEx）。

四维成本对比框架：直接成本、规模成本、风险成本、其他成本。

五项投资回报：削减采购开销、降低运维人力、高SLA减少故障损失、弹性伸缩捕获高并发利润、费用与业务绑定透明化核算。

上云额外投入：战略规划制定、团队能力培养、存量数据中心迁移。

**链接**：https://help.aliyun.com/zh/caf/cloud-computing-costs-and-benefits

### 2.5 企业组织模型与核心职责

三层组织分工：

- **管理层**：明确云战略定位
- **云卓越中心（CCoE）**：由架构/安全/财务专家组成，负责体系设计/风险预估/成本分摊
- **云管理团队**：侧重后期环境优化、自动化运维及资源交付

四大关键任务：战略规划与预算协调、基础环境测试与小步验证、应用清单梳理与迁移筛选、安全合规规则制定与持续风控。

**链接**：https://help.aliyun.com/zh/caf/organizational-model-required-for-cloud-adoption-and-core-responsibilities-of-enterprises

### 2.6 云战略路线图

三阶段演进模型：

- **初始阶段**：基础设施云化，解决传统IDC问题，业务在线化
- **发展阶段**：借助云原生实现架构敏捷化，运营流程自动化与数字化
- **创新阶段**：融合AI与数据智能，云能力成为业务创新引擎

**链接**：https://help.aliyun.com/zh/caf/cloud-strategy-roadmap

## 三、Landing Zone（核心章节）

### 3.1 Landing Zone 定义与八大模块

Landing Zone 是企业上云前的"顶层设计"，中心IT团队需先行构建集中管控与治理基础，再将环境交付给业务部门。

**八大功能模块**：

| 模块 | 职责 |
|------|------|
| 资源规划 | 设计账户层级与组织形式，依据企业运营模式确立管控边界 |
| 财务管理 | 统筹协议条款、折扣结算、账务明细及企业认证信息 |
| 网络规划 | 设计VPC拓扑与混合云连通方案，优化数据流向并强化架构弹性 |
| 身份权限 | 界定访问主体，依托单点登录SSO和细粒度授权管控 |
| 安全防护 | 部署底层防护设施，加速业务安全部署 |
| 合规审计 | 确立管控指标与执行步骤，借助技术工具跟踪规范落实 |
| 运维管理 | 围绕CMDB建立操作体系，整合变更规范、全栈监控与ITSM |
| 自动化 | 明确执行场景，利用工具链完成环境初始化与持续交付流程 |

**链接**：https://help.aliyun.com/zh/caf/components-of-a-landing-zone-on-alibaba-cloud/

### 3.2 Landing Zone 两种实现路径

| 路径 | 适用场景 | 特点 |
|------|---------|------|
| 云治理中心 | 大部分企业的基础LZ框架 | 步骤式指引，一站式搭建，集成多账号身份/权限/网络/合规/安全管理 |
| 场景实践方案 | 需精细化分领域构建的企业 | 每个方案提供控制台操作和IaC（Terraform）两种实施方式 |

**场景方案对照表**：

| 领域 | 场景方案 | 文档链接 |
|------|---------|---------|
| 资源规划 | 企业多账号统一架构方案 | https://help.aliyun.com/zh/caf/enterprise-multi-account-unified-architecture-solution |
| 财务管理 | 多账号企业付款管理方案 | https://help.aliyun.com/zh/caf/multi-account-enterprise-payment-management-solution |
| 身份权限 | 基于云SSO实现多账号单点登录 | https://help.aliyun.com/zh/caf/implement-single-sign-on-for-multiple-accounts-based-on-cloudsso |
| 合规审计 | 多账号操作日志统一归集与审计 | https://help.aliyun.com/zh/caf/unified-collection-and-audit-of-multi-account-operation-logs |
| 合规审计 | 多账号配置统一合规审计 | https://help.aliyun.com/zh/caf/unified-compliance-audit-for-multi-account-configurations |
| 网络规划 | 基于CEN-TR实现企业级云上互联 | https://help.aliyun.com/zh/caf/uses-cen-instances-and-transit-routers-to-establish-enterprise-grade-network-connections |
| 自动化 | 基于GitLab实现账号工厂 | https://help.aliyun.com/zh/caf/implement-an-account-factory-based-on-gitlab |

**链接**：https://help.aliyun.com/zh/caf/options-for-implementation/

### 3.3 各场景方案详情

#### 3.3.1 企业多账号统一架构方案

五类核心账号：

- **企业管理账号**：权限统配、账单汇总与审计策略下发
- **安全账号**：部署WAF、高防IP等安全能力
- **日志账号**：集中采集全量成员账号的操作与运行日志
- **运维账号**：统一监控、多云管理平台及CMDB
- **共享服务账号**：集中托管网络等公共组件

支持"单转多"架构升级：以空白主账号作为管控中心，将原有业务账号迁移纳管。

**链接**：https://help.aliyun.com/zh/caf/enterprise-multi-account-unified-architecture-solution

#### 3.3.2 基于云SSO实现多账号单点登录

核心产品：云SSO（CloudSSO），原生结合资源目录（RD）实现统一身份与访问控制。

- 支持SCIM协议同步企业IdP的用户/组
- 集中配置所有用户对RD账号的访问权限及动态调整
- 适配已有企业IdP的SSO集成场景
- 云SSO为免费产品，开通后即可使用

**CloudSSO 两种资源访问方式**：

云SSO用户可以通过 **RAM 角色** 或 **RAM 用户** 两种方式访问 RD 账号的云资源：

| 访问方式 | 描述 | 适用场景 | 相关操作 |
|---------|------|---------|---------|
| **以 RAM 角色登录**（推荐） | 通过"访问配置"和"多账号授权"，用户 SSO 登录到 RD 账号内的 RAM 角色访问云资源。本质上是云SSO用户扮演 RD 账号中的 RAM 角色进行再一次单点登录 | 适用支持 RAM 角色的云服务（绝大部分场景） | 创建访问配置 → 在 RD 账号上授权 |
| **以 RAM 用户登录** | 通过"RAM 用户同步"，将云SSO用户同步为 RD 账号内的 RAM 用户，用户以 RAM 用户身份访问云资源 | 适用不支持 RAM 角色的少数云服务 | 配置 RAM 用户同步 |

**选型建议**：默认使用 RAM 角色方式（访问配置），仅当特定云服务不支持 RAM 角色时才使用 RAM 用户同步。同一个云SSO用户可以同时配置两种方式。

**CloudSSO 与 RAM 的关系**：

- RAM 提供单个阿里云账号内的身份和权限管理，CloudSSO 在 RD 范围内提供多账号统一身份管理和权限管理
- CloudSSO 提供独立于 RAM 的身份目录，但权限管理复用 RAM 的系统策略和自定义策略语法
- 使用 CloudSSO 不会限制 RAM 原有功能，两个服务可以同时使用

**核心功能**：

1. **统一用户管理**：在云SSO身份目录中维护所有需要访问阿里云的用户，支持手动管理或通过 SCIM 协议从企业 IdP 同步
2. **统一单点登录**：基于 SAML 2.0 协议，一次性配置即可完成与企业 IdP 的 SSO 对接
3. **统一权限配置**：借助与 RD 的深度集成，统一配置用户对 RD 内任意成员账号的访问权限
4. **统一用户门户**：员工登录用户门户后，一站式获取有权限的所有 RD 账号列表，可直接登录控制台或在账号间切换
5. **CLI 集成**：通过阿里云 CLI 登录云SSO，选择 RD 账号和权限，通过命令行访问资源

**CAF 场景方案链接**：https://help.aliyun.com/zh/caf/implement-single-sign-on-for-multiple-accounts-based-on-cloudsso

**CloudSSO 产品文档**：

- 产品概述：https://help.aliyun.com/zh/cloudsso/product-overview/what-is-cloudsso
- 操作指南：https://help.aliyun.com/zh/cloudsso/user-guide/
- 创建访问配置：https://help.aliyun.com/zh/cloudsso/user-guide/create-an-access-configuration#task-2091273
- 在 RD 账号上授权：https://help.aliyun.com/zh/cloudsso/user-guide/assign-access-permissions-on-the-accounts-in-a-resource-directory#task-2090971
- 配置 RAM 用户同步：https://help.aliyun.com/zh/cloudsso/user-guide/create-a-ram-user-provisioning#task-2258334
- 访问配置概述：https://help.aliyun.com/zh/cloudsso/user-guide/overview-1#concept-2090837
- 多账号授权概述：https://help.aliyun.com/zh/cloudsso/user-guide/overview-2#concept-2090970
- 开始使用云SSO：https://help.aliyun.com/zh/cloudsso/getting-started/getting-started-with-cloudsso
- Terraform 集成示例：https://help.aliyun.com/zh/cloudsso/developer-reference/create-a-cloud-sso-user-through-terraform
- CLI 集成示例：https://help.aliyun.com/zh/cloudsso/developer-reference/cli-integration-example

#### 3.3.3 基于CEN-TR实现企业级云上互联

利用云企业网（CEN）与转发路由器（TR）构建六大逻辑分区：

- **生产区**：线上运行环境资源
- **测试区**：验证环境资源
- **DMZ区（互联网出口区）**：公网出入口设备及安全防护
- **东西向安全区**：集中部署防火墙或入侵检测
- **内联运维区**：跳板机与堡垒机
- **外联网区**：对接第三方数据中心

共享服务账号统一管控CEN/TR/出口VPC/运维VPC，业务账号独立管理生产与测试VPC。支持跨账号TR挂载和专用"数据互通VPC"进行安全路由桥接。

**链接**：https://help.aliyun.com/zh/caf/uses-cen-instances-and-transit-routers-to-establish-enterprise-grade-network-connections

#### 3.3.4 多账号操作日志统一归集与审计

核心产品组合：资源目录 + 操作审计（ActionTrail）+ 云治理中心 + SLS + OSS

- "一次配置，全部成员账号生效"的集中审计模式
- 管控策略可锁定审计跟踪，防止被停止或删除
- 日志投递至SLS或OSS
- 满足网安法180天以上日志留存要求
- 支持操作时间线回溯与异常告警

**链接**：https://help.aliyun.com/zh/caf/unified-collection-and-audit-of-multi-account-operation-logs

#### 3.3.5 多账号配置统一合规审计

核心产品：配置审计（Config）+ 资源目录
四步实施流程：构建账号组织树 → 创建账号组 → 部署合规规则 → 统一合规大盘
支持差异化基线管控，配合等保2.0三级测评预检功能。

**链接**：https://help.aliyun.com/zh/caf/unified-compliance-audit-for-multi-account-configurations

### 3.4 AI Landing Zone

#### 3.4.1 企业AI三种典型范式

| 范式 | 特征 | 阿里云产品 |
|------|------|-----------|
| MaaS | 快速调用预训练大模型API，零代码构建智能体 | 百炼 |
| PaaS | 托管平台进行模型训练、微调、部署与管理 | PAI、AI网关、FC |
| IaaS/自研平台 | 自主搭建高定制化AI系统 | ACK+自定义集群 |

#### 3.4.2 AI Landing Zone 定义

AI LZ 是在通用 Landing Zone 基础上补齐 AI 特有能力的标准化、自动化、可治理的企业级AI基础设施框架。确保AI项目从启动即具备：组织与账号隔离、安全与权限控制、成本分账与监控、可持续演进能力。

AI LZ 延续通用LZ的八个功能模块，每个模块添加面向AI平台的扩展：

| 模块 | AI特有扩展 |
|------|-----------|
| 资源规划 | 规划AI平台项目空间、AI资源标签规范 |
| 财务管理 | AI平台及关联资源的成本分摊规则 |
| 网络规划 | 数据采集→模型训练→推理服务各阶段网络最优方案 |
| 身份权限 | AI平台身份权限 + API Key安全使用规范 |
| 安全防护 | AI基础设施安全、AI模型安全、AI应用安全 |
| 合规审计 | 训练与推理场景合规审计规则、满足等保3及行业审计 |
| 运维管理 | 全链路AI统一可观测、借助MCP实现AIOPS |
| 自动化 | AI LZ平台搭建自动化 + MLOps流水线自动化 |

**链接**：https://help.aliyun.com/zh/caf/ai-lz-definition/

### 3.5 Landing Zone Accelerator (LZA)

阿里云官方开源的基于 Terraform 的 Landing Zone 自动化搭建方案。

**LZA 入口**：https://help.aliyun.com/zh/caf/landing-zone-accelerator （阿里云官方说明）

**LZA GitHub 仓库**：https://github.com/aliyun/landing-zone-accelerator-on-alibaba-cloud （开源代码、Issue 反馈、自定义模块入口）

**核心特性**：

- 免费开源，仅为开通的云资源付费
- 支持同时搭建传统 Landing Zone 和 AI Landing Zone
- 覆盖六大核心模块：资源管理、身份权限、财务管理、网络规划、安全防护、合规审计
- 支持中国站和国际站部署

**工程三层架构**：

- **modules**：细粒度底层模块，负责单个产品创建和配置
- **components**：功能模块封装（account-factory, guardrails, identity, log-archive, network, resource-structure, security）
- **test**：测试模块，覆盖所有 components

**支持能力**：多环境应用（dev/beta/prod）、策略配置与Terraform代码分离

**注意**：LZA不包含CICD流程和多人协作等企业级IaC能力，需企业自行补充。

**链接**：https://help.aliyun.com/zh/caf/landing-zone-accelerator

## 四、应用上云

### 4.1 云技术采用（IaaS/PaaS/SaaS选型）

- IaaS 是云战略落地的基础和兜底方案
- 推荐企业优先评估并使用 PaaS/SaaS 类产品（降低运维负荷、具有SLA承诺、按需付费）
- 云技术还能补足自建IT基础设施的治理能力缺失（监控、审计、安全、多账号规划、计量计费）

**链接**：https://help.aliyun.com/zh/caf/cloud-technology-adoption

### 4.2 企业应用上云规划

标准化流程：上云评估模型 → 业务调研 → 应用上云策略及决策流程 → 应用上云优先级及计划

**链接**：https://help.aliyun.com/zh/caf/cloud-migration-plan-for-enterprise-applications/

### 4.3 应用上云实施

八步实施流程：实施流程定义 → 应用调研 → 方案设计 → 迁移实施 → 测试与验证 → 割接与上线 → 典型场景 → 工具支持

**链接**：https://help.aliyun.com/zh/caf/implementation-of-application-cloud-migration/

### 4.4 云迁移中心（CMH）

全生命周期迁移辅助平台，四大功能模块：

1. **云架构资源规划**：支持异构云和IDC资源采集、迁移难度预警、TCO计算
2. **搭建云Landing Zone**：配合云治理中心一键初始化环境
3. **应用上云规划**：非侵入式探针抓取负载容量和网络拓扑
4. **上云迁移实施自动化**：IaC模板批量资源开通、24/7编排调度

**链接**：https://help.aliyun.com/zh/caf/cloud-migration-tools

## 五、运营治理

### 5.1 日常运维管理

CCoE 主导云运维流程重构：

- **资源交付治理**：自服务开通 + 审批开通双模式；模板化交付 + IaC防止架构偏移
- **可观测体系**：基础设施层 + 应用层双层可观测
- **巡检机制**：安全、资源、监控、优化、财务五维审计
- **数据备份**：全持久化介质覆盖，分层存储降成本
- **事件与故障管理**：多源监控集成、智能降噪、标准化故障闭环

**链接**：https://help.aliyun.com/zh/caf/daily-operation-and-maintenance

### 5.2 治理基线

四大治理基线：

| 基线 | 核心要求 | 链接 |
|------|---------|------|
| 身份权限 | MFA必选、禁用主账号AK、最小权限、用户组授权、强密码策略、审计日志 | https://help.aliyun.com/zh/caf/governance-baseline-for-identities-and-permissions |
| 数据安全 | 数据分级分类、核心数据网络隔离、敏感数据脱敏、静态加密、禁止匿名/公网访问 | https://help.aliyun.com/zh/caf/data-security-baseline |
| 通用安全 | DDoS高防+云防火墙+WAF+安全中心、高危端口封禁、全量流量日志、磁盘加密 | https://help.aliyun.com/zh/caf/general-security-baseline |
| 业务连续性 | RTO/RPO规划、多可用区部署、容灾演练、备份验证 | https://help.aliyun.com/zh/caf/business-continuity-baseline |

### 5.3 问题解决

三大类问题分类：能力咨询、使用与故障、账号与财务。

五种解决路径：厂商团队、自助服务、在线/热线支持、工单支持（紧急故障必须走工单）、企业支持计划（专属技术经理）。

**链接**：https://help.aliyun.com/zh/caf/problem-resolution

### 5.4 基础设施自动化

三大自动化范式：

- **IaC（资源编排 ROS / Terraform）**：通过代码定义基础设施配置
- **工作流编排（OOS）**：连接复杂运维工作流
- **策略即代码（RAM）**：通过代码统一管理权限和安全

**链接**：https://help.aliyun.com/zh/caf/infrastructure-automation

### 5.5 成本管理与优化

IPIE闭环流程：识别(Identify) → 计划(Plan) → 实施(Implement) → 评估(Evaluate)

四大优化路径：财务策略（计费模式切换）、规格匹配（精准匹配实际负载）、架构升级（云原生/Serverless）、厂商服务（成本管家定制方案）。

平台工具：智能顾问、云治理中心、成本管家、CADT、云监控。

**链接**：https://help.aliyun.com/zh/caf/cost-management-and-optimization

## 六、用好云

### 6.1 持续云化

云化是持续迭代、没有终点的长期工程。深度云化四个维度：

1. 持续深化技术运用以强化云优势
2. 确保历史及新增系统始终对齐顶层规划
3. 横向覆盖更多业务，纵向引入新产品与新技术
4. 一线实践逐级沉淀为可复用的标准指引

### 6.2 云化成熟度评估

五维评估标准：

1. **组织**：建立弹性资源分配的云迁移组织
2. **应用识别**：识别下一批上云应用并与云战略对齐
3. **架构合规**：新部署遵循Landing Zone基线
4. **迁移与验证**：满足安全/可靠性/性能指标
5. **上线后运营**：正常运维，覆盖计费计量和监控告警

通常需要完成3次以上典型系统上云才能建立标准化流程。

**链接**：https://help.aliyun.com/zh/caf/expanding-cloud-to-cloud-results

## 七、全量链接索引

### 上云战略

| 页面 | 链接 |
|------|------|
| 企业上云价值预估 | https://help.aliyun.com/zh/caf/enterprise-cloud-value-estimate |
| 企业上云主要动机 | https://help.aliyun.com/zh/caf/enterprise-motivations-for-cloud-migration |
| 云战略架构规划 | https://help.aliyun.com/zh/caf/cloud-strategic-architecture-planning |
| 云计算成本和效益 | https://help.aliyun.com/zh/caf/cloud-computing-costs-and-benefits |
| 企业组织模型与核心职责 | https://help.aliyun.com/zh/caf/organizational-model-required-for-cloud-adoption-and-core-responsibilities-of-enterprises |
| 云战略路线图 | https://help.aliyun.com/zh/caf/cloud-strategy-roadmap |

### Landing Zone

| 页面 | 链接 |
|------|------|
| Landing Zone组成部分 | https://help.aliyun.com/zh/caf/components-of-a-landing-zone-on-alibaba-cloud/ |
| Landing Zone场景方案 | https://help.aliyun.com/zh/caf/options-for-implementation/ |
| AI Landing Zone | https://help.aliyun.com/zh/caf/ai-lz-definition/ |
| Landing Zone Accelerator | https://help.aliyun.com/zh/caf/landing-zone-accelerator |
| 企业多账号统一架构方案 | https://help.aliyun.com/zh/caf/enterprise-multi-account-unified-architecture-solution |
| 多账号企业付款管理方案 | https://help.aliyun.com/zh/caf/multi-account-enterprise-payment-management-solution |
| 基于云SSO多账号单点登录 | https://help.aliyun.com/zh/caf/implement-single-sign-on-for-multiple-accounts-based-on-cloudsso |
| 多账号操作日志统一归集与审计 | https://help.aliyun.com/zh/caf/unified-collection-and-audit-of-multi-account-operation-logs |
| 多账号配置统一合规审计 | https://help.aliyun.com/zh/caf/unified-compliance-audit-for-multi-account-configurations |
| 基于CEN-TR企业级云上互联 | https://help.aliyun.com/zh/caf/uses-cen-instances-and-transit-routers-to-establish-enterprise-grade-network-connections |
| 基于GitLab实现账号工厂 | https://help.aliyun.com/zh/caf/implement-an-account-factory-based-on-gitlab |
| AI资源规划 | https://help.aliyun.com/zh/caf/resource-planning-ai |

### 应用上云

| 页面 | 链接 |
|------|------|
| 云技术采用 | https://help.aliyun.com/zh/caf/cloud-technology-adoption |
| 企业应用上云规划 | https://help.aliyun.com/zh/caf/cloud-migration-plan-for-enterprise-applications/ |
| 应用上云实施 | https://help.aliyun.com/zh/caf/implementation-of-application-cloud-migration/ |
| 云化工具（CMH） | https://help.aliyun.com/zh/caf/cloud-migration-tools |
| 扩展云化成果 | https://help.aliyun.com/zh/caf/expanding-cloud-to-cloud-results |

### 运营治理

| 页面 | 链接 |
|------|------|
| 日常运维管理 | https://help.aliyun.com/zh/caf/daily-operation-and-maintenance |
| 风险管理方法论 | https://help.aliyun.com/zh/caf/risk-management-methodology/ |
| 治理基线总览 | https://help.aliyun.com/zh/caf/governance-baselines-on-alibaba-cloud/ |
| 身份权限治理基线 | https://help.aliyun.com/zh/caf/governance-baseline-for-identities-and-permissions |
| 数据安全基线 | https://help.aliyun.com/zh/caf/data-security-baseline |
| 通用安全基线 | https://help.aliyun.com/zh/caf/general-security-baseline |
| 业务连续性基线 | https://help.aliyun.com/zh/caf/business-continuity-baseline |
| 问题解决 | https://help.aliyun.com/zh/caf/problem-resolution |
| 基础设施自动化 | https://help.aliyun.com/zh/caf/infrastructure-automation |
| 成本管理与优化 | https://help.aliyun.com/zh/caf/cost-management-and-optimization |

## CloudSSO 多账号身份权限

> 本节内容承接自 SKILL.md 的"Landing Zone 身份权限（CloudSSO）"，提供完整的决策表与官方文档清单。

CloudSSO（云SSO）是阿里云提供的多账号统一身份管理与访问控制服务（免费），原生结合资源目录（RD）。

### 两种资源访问方式

| 访问方式 | 机制 | 适用场景 | 推荐度 |
|---------|------|---------|--------|
| **RAM 角色**（访问配置） | 通过"访问配置 + 多账号授权"，用户 SSO 登录后扮演 RD 账号内的 RAM 角色访问资源 | 支持 RAM 角色的云服务（绝大部分） | **推荐** |
| **RAM 用户**（用户同步） | 通过"RAM 用户同步"，将云SSO用户同步为 RD 账号内的 RAM 用户 | 不支持 RAM 角色的少数云服务 | 按需补充 |

**选型原则**：默认用 RAM 角色方式，仅当特定服务不支持 RAM 角色时才用 RAM 用户同步。同一用户可同时配置两种方式。

**与 RAM 的关系**：CloudSSO 提供独立身份目录，但权限管理复用 RAM 策略语法。两者可同时使用，互不冲突。

### 关键文档

- 产品概述：https://help.aliyun.com/zh/cloudsso/product-overview/what-is-cloudsso
- 创建访问配置：https://help.aliyun.com/zh/cloudsso/user-guide/create-an-access-configuration#task-2091273
- 配置 RAM 用户同步：https://help.aliyun.com/zh/cloudsso/user-guide/create-a-ram-user-provisioning#task-2258334
- 开始使用云SSO：https://help.aliyun.com/zh/cloudsso/getting-started/getting-started-with-cloudsso

## AI Landing Zone 治理详解

> 内容承接自 SKILL.md "AI Landing Zone" 段。

AI LZ 是在通用 Landing Zone 基础上补齐 AI 特有能力的治理框架。

### 三种 AI 范式

| 范式 | 平台/产品 |
| --- | --- |
| MaaS | 百炼 |
| PaaS | PAI、AI 网关、函数计算（FC） |
| IaaS | ACK、客户自建集群 |

### AI 特有扩展模块

1. **AI 资源标签规范**：以业务/项目/模型版本维度组织。
2. **API Key 安全规范**：集中托管，与 RAM 解耦。
3. **AI 安全三层防护**：网络层、平台层、内容/合规层。
4. **训推场景合规审计**：与 ActionTrail / Config 联动。
5. **全链路 AI 可观测 + MCP AIOPS**。
6. **MLOps 流水线自动化**。

**官方入口**：https://help.aliyun.com/zh/caf/ai-lz-definition/

## 云治理中心 完整功能矩阵

> 内容承接自 SKILL.md "云治理中心（WA 官方治理工具）" 段。

云治理中心是阿里云上进行**多账号集中 IT 治理**的官方平台，也是云卓越架构 WA 的核心治理工具。

### 产品定位

> "云治理中心是企业在阿里云上进行多账号集中IT治理的平台。通过步骤式向导和自动化流程帮助企业快速搭建 Landing Zone，建立安全合规的多账号环境，并对企业在云上的多账号环境进行持续治理。"

### 核心功能（5项）

1. **资源结构搭建**：构建企业多账号资源架构
2. **商业结算关系建立**：配置账号间财务结算关系
3. **企业统一身份权限管理**：集中管控身份与访问权限
4. **资源成本优化**：优化云上资源成本支出
5. **合规审计**：满足安全合规要求

### 三大产品优势

- **快速搭建 Landing Zone**：步骤式设计，一步步了解 Landing Zone 的作用和规范
- **企业治理现状可视化**：统一汇总治理数据，无需登录各成员账号即可掌握账号结构、权限配置和合规状况
- **持续治理和优化**：自动提示治理风险，并提供优化建议

### 核心工具链接

- **云治理中心控制台**：https://governance.console.aliyun.com
- **官方文档首页**：https://help.aliyun.com/zh/cgc
- **产品概述**：https://help.aliyun.com/zh/cgc/product-overview/what-is-cloud-governance-center
- **快速入门**：https://help.aliyun.com/zh/cgc/getting-started/
- **Landing Zone 搭建**：https://help.aliyun.com/zh/cgc/getting-started/build-a-landing-zone-2

### 治理成熟度检测（客观度量）

- 文档：https://help.aliyun.com/zh/cgc/user-guide/governance-maturity-check
- 检测项：260+ 项检测指标（支持 2.0 和 3.0 模型）
- 功能：评估云上 IT 治理水平、识别风险项、生成检测报告、快速修复

### Well-Architected Tool（主观度量）

- 文档：https://help.aliyun.com/zh/cgc/user-guide/well-architected-tool
- 功能：架构化问卷评估、记录关键决策、识别风险、生成改进建议、里程碑管理
- 评估维度：安全合规、稳定性、成本优化、卓越运营、高效性能

### 账号工厂

- 配置账号基线：https://help.aliyun.com/zh/cgc/user-guide/configure-the-account-baseline
- 创建账号：https://help.aliyun.com/zh/cgc/user-guide/create-an-account
- 为已有账号应用基线：https://help.aliyun.com/zh/cgc/user-guide/apply-the-account-baseline-to-an-existing-account

## Landing Zone 服务模式与购买方式

> 内容承接自 SKILL.md "Landing Zone 服务模式与购买方式" 段。

**解决方案免费，咨询服务按需购买**：Landing Zone（含 AI Landing Zone）的**官方解决方案本身是免费的**，客户可根据文档自行搭建。如需咨询或咨询+实施服务，需单独购买，按人天报价。

| 实施方式 | 说明 | 费用 | 适用场景 |
|---------|------|------|---------|
| **客户自服务** | 根据官方解决方案自行搭建 | **免费** | 有技术能力、有运维团队的企业 |
| **阿里云原厂服务** | 与阿里云签约，按人天评估费用 | 按人天报价 | 需要专业咨询和实施支持 |
| **认证合作伙伴** | 与阿里云认证伙伴直签，不经过阿里云 | 按人天报价 | 希望本地化服务或有特定伙伴偏好的企业 |
| **PdSA 免费快速实施** | 阿里云 PdSA 协助一天内完成核心架构搭建 | **免费** | 需要快速启动、需求标准化的企业 |

**下单地址**：

- 阿里云原厂服务：https://www.aliyun.com/service/alibaba-cloud-landing-zone
- 认证合作伙伴列表：https://open.aliyun.com/landing-zone（动态查询最新伙伴列表）

**PdSA 免费快速实施服务说明**：

- 服务内容：核心架构搭建（资源目录、基础网络、身份权限框架）
- 服务范围：**不包含**面向企业实际业务的深度定制，如：
  - 人员身份权限设计与迁移
  - 网络规划与详细搭建
  - 合规审计规则明细制定
- 交付时间：1天内完成

## 云卓越架构服务模式与购买方式

> 内容承接自 SKILL.md "云卓越架构服务模式与购买方式" 段。

**解决方案免费，咨询服务按需购买**：云卓越架构 WA（含 AI WA）的**官方解决方案和评估工具本身是免费的**（治理成熟度检测、Well-Architected Tool 均免费提供）。如需专家咨询或深度优化服务，需单独购买。

| 实施方式 | 说明 | 费用 | 适用场景 |
|---------|------|------|---------|
| **客户自评估** | 使用云治理中心免费工具自行评估和优化 | **免费** | 有技术能力、能自主优化的企业 |
| **阿里云原厂服务** | 与阿里云签约，获取专家咨询和深度优化 | 按人天报价 | 需要专业架构评审和优化建议 |
| **认证合作伙伴** | 与阿里云认证伙伴直签 | 按人天报价 | 希望本地化服务的企业 |
| **PdSA 免费咨询** | 阿里云 PdSA 提供架构评估建议 | **免费** | 需要初步评估指导的企业 |

**免费工具入口**：

- 治理成熟度检测：https://help.aliyun.com/zh/cgc/user-guide/governance-maturity-check/
- Well-Architected Tool：https://help.aliyun.com/zh/cgc/user-guide/well-architected-tool

## 国内站 vs 国际站 站点选型详解

> 本节内容承接自 SKILL.md 第 1 章 "国内站 vs 国际站" 子节，提供完整的站点对比与场景化选型决策表。

### 两个完全隔离的站点

| 维度 | 国内站 | 国际站 |
| --- | --- | --- |
| 主体 | 阿里云中国 | Alibaba Cloud International |
| 域名 | aliyun.com / aliyuncs.com | alibabacloud.com |
| 账号体系 | 独立 | 独立（与国内站不通） |
| 资源、API、控制台 | 完全独立 | 完全独立 |
| 计费币种 | 人民币 | 美元（含部分多币种） |
| 主要面向 | 中国大陆业务、人民币结算 | 海外业务、跨境合规、出海企业 |
| 全球 Region 购买 | 可（含港澳台与海外 Region） | 可 |

两站点资源、账号、API 全互不相通，**可类比为两朵不同的云**——任何 RAM、CloudSSO、资源目录、CEN 等多账号能力都不能跨站接入。

### Landing Zone 选站决策树

```
是否需要海外企业实体 / 美元结算 / 海外合规驻留？
├── 否（中国大陆业务为主） → 国内站，建一套基于多账号的 LZ
├── 是（仅出海，无大陆业务） → 国际站，建一套基于多账号的 LZ
└── 同时需要（大陆 + 海外业务并存）
    ├── 国内站建一套 LZ（统一纳管国内业务）
    └── 国际站建一套 LZ（统一纳管海外业务）
        — 两套 LZ 之间不能跨站纳管，需各自独立治理
```

### 选型原则

1. **每站一套**：同一站点内不要按 Region 或国家拆分多套多账号架构。一套基于多账号的 Landing Zone 统一纳管该站点下的所有资源即可。
2. **不跨站纳管**：站点之间完全隔离，多账号体系不能跨站。需要双站点时各搭一套独立 LZ。
3. **拆分例外**：仅在业务组织有强管控要求（不同法人主体独立运营、强合规边界等）时，才在同一站点内拆出多套独立的多账号架构。

### 何时选国际站

最常见触发条件：

- **企业出海**：海外子公司、海外销售渠道。
- **海外企业实体**：注册地在境外，需要本地化合同 / 本地法人。
- **美元结算**：财务流程要求美元（或其他外币）账单。
- **海外合规与数据驻留**：欧盟 GDPR、美国 HIPAA、APAC 个人信息保护等当地法规要求数据驻留在指定 Region。
- **国际客户对接**：客户群体主要在海外，使用国际站可获得更直接的本地支持。

其余场景（中国大陆业务、人民币结算）默认使用国内站。

### 关键文档

- 国内站官网：https://www.aliyun.com/
- 国际站官网：https://www.alibabacloud.com/
- 国内站帮助：https://help.aliyun.com/
- 国际站帮助：https://www.alibabacloud.com/help
