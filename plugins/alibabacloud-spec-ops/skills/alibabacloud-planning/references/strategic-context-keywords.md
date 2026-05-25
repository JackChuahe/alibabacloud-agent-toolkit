# Strategic-Context Keywords (Phase 0.0)

Authoritative keyword reference for `alibabacloud-planning` Phase 0.0 战略层意图分流.
When the user's first message hits **any** keyword in the trigger groups below
**AND** does NOT hit any reverse keyword, Phase 0.0 fires and offers to
delegate to `alibabacloud-itgov-advisor` for upstream LZ / governance scoping
before continuing.

## Trigger keyword groups

The 5 groups below identify enterprise-grade / multi-account / governance
scope — situations where attempting a single-workload design in spec-ops
planning alone would miss the upstream architectural decision that has to
happen first.

| Group | Keywords | Why trigger |
|---|---|---|
| **多账号体系** | 多账号, 资源目录, RD, Landing Zone, LZ, AI LZ, LZA, 账号工厂, CloudSSO | 涉及账号结构 / 资源目录拓扑 / 跨账号身份,planning 的 `.aliyun-ai-ops-spec/{name}/` 单 workload 状态目录无法承载 |
| **战略治理** | CCoE, 云卓越中心, CAF, 上云战略, 云治理中心, 治理基线, 治理成熟度 | 战略层决策(组织模型、上云路线图、治理框架),与单 workload 落地两个尺度 |
| **合规** | 等保, 等级保护, 合规审计, GDPR, HIPAA, 行业合规 | 合规要求往往牵动 LZ 全局基线(日志归集、加密策略、网络分区),不是单 workload 设计能闭环的 |
| **国际化** | 出海, 国际站, 海外业务, 跨境 | 国内站 vs 国际站是 LZ 级决策,选错会重做整套架构 |
| **网络规划** | CEN, TR, 转发路由器, 六大分区, 共享 VPC, DMZ | 企业级网络拓扑(共享服务账号 + 业务账号 + 六大分区)是 LZ 主题,不是单 VPC 设计 |

## Reverse keywords (skip Phase 0.0)

If the user's message **also** contains any of the following, Phase 0.0 is
skipped — these signal the request is genuinely single-workload despite
brushing past an enterprise keyword:

| Reverse signal | Keywords |
|---|---|
| 数量限定 | 一台, 一个, 单台, 单个, just one, single, a, an |
| 个人 / 小团队 | 我自己, 个人, 自用, my own, personal, side project, hobby |
| 非生产 | 测试, 开发, dev, test, sandbox, POC, demo, 试用, 学习 |

### Example matching

| User message | Triggered? | Why |
|---|---|---|
| "我要在多账号架构里搭一个 web app" | ❌ skip | "一个" 是反向数量限定 |
| "帮我设计企业级 Landing Zone" | ✅ trigger | "企业级" + "LZ",无反向词 |
| "我想个人学习一下 CAF,搭个测试 VPC" | ❌ skip | "个人" + "学习" + "测试" 多个反向词 |
| "我们公司要做出海,需要规划阿里云架构" | ✅ trigger | "公司" + "出海",无反向词 |
| "一台 ECS 跑 dev 环境" | ❌ skip | "一台" + "dev" |

## Phase 0.0 firing behavior

When triggered:

1. `AskUserQuestion`:
   - "先做战略规划 (调用 alibabacloud-itgov-advisor)" → 调起 advisor,完成后回到 Phase 0
   - "已有 LZ,直接进入工作负载设计" → 进入 Phase 0,但 Phase 1 加问 LZ 上下文(目标账号、VPC ID、CEN 拓扑、SG 基线)
   - "暂不考虑 LZ,先做工作负载" → 直接进入现有 Phase 0,不再追问

When skipped (no enterprise keywords OR reverse keyword hit): proceed
directly to Phase 0 as before — Phase 0.0 is invisible to the user.

## Maintenance

This file is the single source of truth for Phase 0.0 keyword routing.
When adding/removing a keyword:

1. Edit the table here.
2. Ensure planning SKILL.md Phase 0.0 section references this file as
   authoritative — do not duplicate the lists.
3. If a keyword change affects user-facing copy in planning, update the
   example AskUserQuestion strings there too.
