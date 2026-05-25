# 阿里云云卓越架构（Well-Architected Framework）完整知识库

> 本文件是基于阿里云官方帮助文档 https://help.aliyun.com/zh/document_detail/2362204.html 递归扫描提取的完整知识库。
> 阿里云云卓越架构框架基于多年服务各行各业客户的经验总结，将阿里云上的架构设计最佳实践总结为一系列的方法论和设计原则。

## 一、框架总览

### 1.1 核心定义

阿里云卓越架构框架是"基于多年服务各行各业客户的经验总结，将阿里云上的架构设计最佳实践总结为一系列的方法论和设计原则"。

目标角色包括：首席技术官（CTO）、架构师、运维、安全、研发。

### 1.2 三大核心阶段

| 阶段 | 说明 | 文档链接 |
|------|------|---------|
| **学习** | 发布《云卓越架构白皮书》，提供理论方法和设计原则 | https://help.aliyun.com/zh/document_detail/2882403.html |
| **度量** | 提供免费架构评估工具和度量模型（260+检测指标） | https://help.aliyun.com/zh/document_detail/2882554.html |
| **优化** | 改进指引、线上自助治理、专家咨询服务 | https://help.aliyun.com/zh/document_detail/2882553.html |

### 1.3 五大支柱（非六大）

阿里云云卓越架构采用**五大支柱**（区别于AWS的六大支柱）：

| 支柱 | 核心要点 | 学习文档 | 优化文档 |
|------|---------|---------|---------|
| **安全** | 网络安全、身份安全、主机安全、数据安全等全方位规划和实施 | https://help.aliyun.com/zh/document_detail/2536222.html | https://help.aliyun.com/zh/document_detail/2901215.html |
| **稳定** | 面向失败设计，具备一定容灾性的能力 | https://help.aliyun.com/zh/document_detail/2536221.html | https://help.aliyun.com/zh/document_detail/2901212.html |
| **成本** | 避免资源浪费，减少不必要的云上开支 | https://help.aliyun.com/zh/document_detail/2536195.html | https://help.aliyun.com/zh/document_detail/2901214.html |
| **效率** | 应用研发态、运行态相关工具与系统的构建和使用 | https://help.aliyun.com/zh/document_detail/2536122.html | https://help.aliyun.com/zh/document_detail/2901213.html |
| **性能** | 自动触发弹性伸缩能力，建立完备的可观测性体系 | https://help.aliyun.com/zh/document_detail/2530946.html | - |

## 二、学习阶段（五大支柱详解）

### 2.1 安全支柱

安全支柱遵循完整的安全生命周期：规划 → 设计 → 风险识别 → 防护 → 监控 → 响应。

**子主题**：

- 概述：https://help.aliyun.com/zh/document_detail/2573776.html
- 安全责任模型：https://help.aliyun.com/zh/document_detail/2573777.html
- 云平台数据安全和隐私保障体系：https://help.aliyun.com/zh/document_detail/2573778.html
- 规划和设计：https://help.aliyun.com/zh/document_detail/2573779.html
- 安全设计原则：https://help.aliyun.com/zh/document_detail/2573780.html
- 安全风险识别和检测：https://help.aliyun.com/zh/document_detail/2573781.html
- 安全防护：https://help.aliyun.com/zh/document_detail/2573790.html
- 监控和分析：https://help.aliyun.com/zh/document_detail/2573809.html
- 安全响应：https://help.aliyun.com/zh/document_detail/2573810.html

**核心知识点**：

- 安全责任共享模型：明确阿里云与客户之间的安全责任划分
- 数据安全与隐私保护体系：全面的云端数据保护框架
- 安全生命周期管理：从规划到响应的完整工作流
- 安全设计原则：设计安全云架构的最佳实践
- 安全风险管理：主动识别、检测和缓解安全威胁

### 2.2 稳定支柱

稳定支柱强调高可用架构设计、变更风险控制和故障应急。

**子主题**：

- 概述：https://help.aliyun.com/zh/document_detail/2573816.html
- 设计原则：https://help.aliyun.com/zh/document_detail/2573818.html
- 设计方案：https://help.aliyun.com/zh/document_detail/2573820.html
- 高可用架构设计：https://help.aliyun.com/zh/document_detail/2573823.html
- 变更风控：https://help.aliyun.com/zh/document_detail/2573861.html
- 故障应急：https://help.aliyun.com/zh/document_detail/2573862.html

**核心知识点**：

- 高可用架构设计：构建弹性系统的模式和最佳实践
- 变更管理：管理基础设施和应用变更的风险控制流程
- 容错策略：优雅处理故障的策略
- 应急响应：事件响应和灾难恢复的程序和剧本
- 面向失败设计：将故障视为常态，设计具备容灾能力的系统

### 2.3 成本支柱

成本支柱覆盖整个云采用生命周期的成本管理。

**子主题**：

- 概述：https://help.aliyun.com/zh/document_detail/2536196.html
- 设计原则：https://help.aliyun.com/zh/document_detail/2536197.html
- 云上成本管理框架：https://help.aliyun.com/zh/document_detail/2542911.html
- 用云计划阶段：https://help.aliyun.com/zh/document_detail/2536198.html
- 用云执行阶段：https://help.aliyun.com/zh/document_detail/2536199.html
- 监控分析阶段：https://help.aliyun.com/zh/document_detail/2536200.html
- 成本优化阶段：https://help.aliyun.com/zh/document_detail/2536201.html
- 平衡业务目标与成本：https://help.aliyun.com/zh/document_detail/2536202.html

**核心知识点**：

- 云成本管理框架：管理云费用的结构化方法
- 分阶段成本管理：规划 → 执行 → 监控 → 优化生命周期
- 成本感知规划：从初始规划阶段就纳入成本考虑
- 持续优化：识别和实施成本节约的持续流程
- 业务-成本平衡：将成本优化与业务目标对齐的策略
- 资源合理配置：将资源分配与实际工作负载需求匹配

### 2.4 效率支柱

效率支柱关注通过明确定义的流程和自动化来高效构建和运营云基础设施。

**子主题**：

- 概述：https://help.aliyun.com/zh/document_detail/2536123.html
- 构建运营模型：https://help.aliyun.com/zh/document_detail/2536125.html
- 设计阶段：https://help.aliyun.com/zh/document_detail/2536126.html
- 构建阶段：https://help.aliyun.com/zh/document_detail/2536130.html
- 运营阶段：https://help.aliyun.com/zh/document_detail/2536141.html

**核心知识点**：

- 运营模型开发：建立云运营框架
- 生命周期方法：设计 → 构建 → 运营方法论
- 卓越运营：高效云运营的最佳实践
- 流程自动化：利用自动化提高运营效率
- 持续改进：运营流程的迭代增强
- 运营就绪：为生产运营准备团队和系统

### 2.5 性能支柱

性能支柱覆盖从架构设计到优化的完整性能工程生命周期。

**子主题**：

- 概述：https://help.aliyun.com/zh/document_detail/2536121.html
- 高性能架构设计：https://help.aliyun.com/zh/document_detail/2531100.html
- 性能测试：https://help.aliyun.com/zh/document_detail/2536106.html
- 性能监控：https://help.aliyun.com/zh/document_detail/2536108.html
- 性能优化：https://help.aliyun.com/zh/document_detail/2536112.html

**核心知识点**：

- 高性能架构设计：构建可扩展、高性能系统的模式
- 性能测试：验证系统负载下性能的方法论
- 性能监控：持续性能观察的工具和技术
- 性能优化：识别和解决性能瓶颈的策略
- 端到端性能：从设计到优化的完整性能生命周期
- 主动性能管理：从被动响应转向主动性能优化

## 三、度量阶段

### 3.1 度量双模式

| 模式 | 工具 | 内容 | 适用场景 |
|------|------|------|---------|
| **客观度量** | 云治理中心-治理成熟度检测 | 260多项检测指标，基于阿里云实时数据，输出可视化评估报告 | 快速定位硬性缺陷，降低人工排查成本 |
| **主观度量** | Well-Architected Tool | 架构化问卷，记录关键决策、风险项、改进计划 | 评估架构设计合理性（如最小权限原则、弹性扩展） |

### 3.2 度量工具

- **云治理中心**：https://help.aliyun.com/zh/cgc/product-overview/what-is-cloud-governance-center
- **开通云治理中心**：https://help.aliyun.com/zh/cgc/getting-started/activate-cloud-governance-center
- **治理成熟度检测**：https://help.aliyun.com/zh/cgc/user-guide/governance-maturity-check/
- **Well-Architected Tool**：https://help.aliyun.com/zh/cgc/user-guide/well-architected-tool

### 3.3 核心知识点

- **260+检测指标**：覆盖云治理成熟度的全面检测体系
- **免费工具**：治理成熟度检测 + Well-Architected Tool 均免费提供
- **闭环流程**：学习 → 度量 → 优化
- 客观度量依托阿里云实时数据，输出可视化评估报告
- 主观度量通过架构化问卷记录关键决策和风险项
- 支持团队协作，确保治理目标与业务需求对齐

## 四、优化阶段

### 4.1 优化阶段四大支柱

| 支柱 | 文档链接 | 核心内容 |
|------|---------|---------|
| 安全优化 | https://help.aliyun.com/zh/document_detail/2901215.html | 安全架构基础、身份和访问控制、基础设施防护、威胁检测与响应 |
| 稳定优化 | https://help.aliyun.com/zh/document_detail/2901212.html | 高可用架构、容灾设计、故障应急 |
| 成本优化 | https://help.aliyun.com/zh/document_detail/2901214.html | 成本策略、成本监控、成本优化 |
| 效率优化 | https://help.aliyun.com/zh/document_detail/2901213.html | 闲置资源治理、性能-成本平衡 |

### 4.2 安全优化子主题

- 安全架构基础：https://help.aliyun.com/zh/document_detail/2901216.html
- 身份和访问控制：https://help.aliyun.com/zh/document_detail/2706126.html
- 基础设施防护：https://help.aliyun.com/zh/document_detail/2925033.html
- 威胁检测与响应：https://help.aliyun.com/zh/document_detail/2925034.html
- 附录：解决方案：https://help.aliyun.com/zh/document_detail/2901230.html

### 4.3 稳定优化子主题

- 高可用架构：https://help.aliyun.com/zh/document_detail/3024564.html
- 附录：解决方案：https://help.aliyun.com/zh/document_detail/2929032.html

### 4.4 成本优化子主题

- 成本策略：https://help.aliyun.com/zh/document_detail/3023497.html
- 成本监控：https://help.aliyun.com/zh/document_detail/3023496.html
- 成本优化：https://help.aliyun.com/zh/document_detail/3023495.html
- 附录：解决方案：https://help.aliyun.com/zh/document_detail/2929036.html

### 4.5 效率优化子主题

- 附录：解决方案：https://help.aliyun.com/zh/document_detail/2929037.html

### 4.6 线上自助治理

- 云治理中心支持在线一键修复风险项
- 快速修复风险项功能：https://help.aliyun.com/zh/cgc/user-guide/quickly-fix-risk-items

### 4.7 核心知识点

- 优化阶段特点：短期问题修复 + 长期治理能力构建
- 实现业务目标与技术架构深度协同
- 基于度量阶段发现的问题和风险进行改进
- 提供系统化改进指引、工具化治理手段以及场景化解决方案
- 云治理中心支持在线一键修复功能
- 推动架构向更高成熟度发展

## 五、修订记录

### 5.1 文档演进历史

| 时间 | 更新内容 |
|------|---------|
| 2023-09-25 | 初次发布阿里云卓越架构框架白皮书 |
| 2025-07-07 | 重大文档结构调整，按学习、度量、优化三部分重组，发布100篇解决方案 |
| 2025-07-14 | 安全支柱新增28篇实践（单次最大规模更新） |
| 2026-02-27 | 成本支柱新增4篇网络成本策略实践；性能支柱新增7篇网络资源实践 |
| 2026-03-06 | 稳定支柱新增9篇最佳实践，包括"服务限额与容量规划"、"网络拓扑" |

### 5.2 解决方案汇总

- 安全解决方案：https://help.aliyun.com/zh/document_detail/2901230.html
- 稳定解决方案：https://help.aliyun.com/zh/document_detail/2929032.html
- 成本解决方案：https://help.aliyun.com/zh/document_detail/2929036.html
- 效率解决方案：https://help.aliyun.com/zh/document_detail/2929037.html

## 六、核心理念（结束语摘录）

> "在云上落地卓越架构并非一蹴而就，需要不断迭代并持续演进。企业使用云技术是一个动态的过程，大部分情况下的良好架构都是基于一个时点的'共时性'设计，但企业IT既有自身的历史，也有未来的发展，云产品和最佳实践也在不断迭代，因此架构的演进需要有更多的'历时性'观点，始终关注架构的演进和变化。"
>
> "在使用云技术的过程中，有大量企业的认知和实践停留在上云最初的那一刻，从而导致技术固化后无法达成对业务的有效支撑。"
>
> "企业的业务团队、CCoE团队、技术相关职能人员等必须要保持对新技术的洞悉，并勇于进行必要的实践，卓越架构不能成为一成不变的'完美架构'，而是时刻伴随业务和技术发展的'当前最优'架构。"
>
> "对于追求卓越架构的企业而言，构建基于或包含云技术的卓越架构指南，形成自身战略规划以及上云、用云、管云的最佳实践，将使企业能够持续发挥云计算的最大价值。"

## 七、全量链接索引

### 框架核心页面

| 页面 | 链接 |
|------|------|
| 前言（框架总览） | https://help.aliyun.com/zh/document_detail/2362204.html |
| 学习 | https://help.aliyun.com/zh/document_detail/2882403.html |
| 度量 | https://help.aliyun.com/zh/document_detail/2882554.html |
| 优化 | https://help.aliyun.com/zh/document_detail/2882553.html |
| 修订记录 | https://help.aliyun.com/zh/document_detail/2901217.html |
| 结束语 | https://help.aliyun.com/zh/document_detail/2362209.html |
| 卓越架构产品页 | https://help.aliyun.com/zh/product/2362200.html |

### 五大支柱（学习阶段）

| 支柱 | 主页面 | 概述 | 设计原则 |
|------|--------|------|---------|
| 安全 | https://help.aliyun.com/zh/document_detail/2536222.html | https://help.aliyun.com/zh/document_detail/2573776.html | https://help.aliyun.com/zh/document_detail/2573780.html |
| 稳定 | https://help.aliyun.com/zh/document_detail/2536221.html | https://help.aliyun.com/zh/document_detail/2573816.html | https://help.aliyun.com/zh/document_detail/2573818.html |
| 成本 | https://help.aliyun.com/zh/document_detail/2536195.html | https://help.aliyun.com/zh/document_detail/2536196.html | https://help.aliyun.com/zh/document_detail/2536197.html |
| 效率 | https://help.aliyun.com/zh/document_detail/2536122.html | https://help.aliyun.com/zh/document_detail/2536123.html | - |
| 性能 | https://help.aliyun.com/zh/document_detail/2530946.html | https://help.aliyun.com/zh/document_detail/2536121.html | - |

### 四大支柱（优化阶段）

| 支柱 | 文档链接 |
|------|---------|
| 安全优化 | https://help.aliyun.com/zh/document_detail/2901215.html |
| 稳定优化 | https://help.aliyun.com/zh/document_detail/2901212.html |
| 成本优化 | https://help.aliyun.com/zh/document_detail/2901214.html |
| 效率优化 | https://help.aliyun.com/zh/document_detail/2901213.html |

### 云治理中心相关

| 页面 | 链接 |
|------|------|
| 云治理中心概览 | https://help.aliyun.com/zh/cgc/product-overview/what-is-cloud-governance-center |
| 开通云治理中心 | https://help.aliyun.com/zh/cgc/getting-started/activate-cloud-governance-center |
| 治理成熟度检测 | https://help.aliyun.com/zh/cgc/user-guide/governance-maturity-check/ |
| Well-Architected Tool | https://help.aliyun.com/zh/cgc/user-guide/well-architected-tool |
| 快速修复风险项 | https://help.aliyun.com/zh/cgc/user-guide/quickly-fix-risk-items |

### 阿里云信任中心

- 信任中心：https://security.aliyun.com/trust-center
