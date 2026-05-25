# Scenario-Driven Expert Context Loading (Phase 1)

Authoritative trigger → advisor-chapter map for `alibabacloud-planning`
Phase 1. When the user's clarification answers reveal one of the scenarios
below, planning **reads** the corresponding section of `alibabacloud-itgov-advisor`
as inline context, uses it to refine the next questions, AND surfaces a
**soft mode-upgrade suggestion** during Mode Decision (the user can still
choose Fast Track).

## Scenario → advisor section mapping

| 触发措辞 | 加载 advisor 章节 | Phase 1 应额外追问的维度 |
|---|---|---|
| 等保 / 等级保护 / 等保三级 / 等保二级 | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 5 (等保架构要点) + `alibabacloud-itgov-advisor/SKILL.md` § 5 (合规与治理) | 五层逐项:网络(VPC + SG + WAF + DDoS) / 主机(云安全中心 + 堡垒机) / 数据(KMS + RDS TDE + OSS 加密) / 审计(ActionTrail ≥ 180 天 + Config) / 身份(RAM 最小权限 + MFA + SSO) |
| AI 应用 / 大模型 / 训练 / 推理 / MaaS / PAI | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 3.4 (AI Landing Zone 治理详解) | AI 范式选型(MaaS = 百炼 / PaaS = PAI/AI 网关/FC / IaaS = ACK+自建) + API Key 安全 + AI 安全三层 + 训推合规审计 + MLOps |
| 出海 / 海外业务 / 国际 / 跨境 / 全球化 | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 国内站 vs 国际站 站点选型详解 | 海外企业实体 / 美元结算 / 数据驻留 (GDPR / HIPAA / APAC) / 国际客户支持 → 国内站 vs 国际站决策 |
| 数据加密 / 敏感数据 / 密钥管理 / KMS / TDE | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 5 (数据安全基线) | 数据分级分类 / 静态加密(TDE / KMS / OSS SSE-KMS) / 传输加密(SSL/TLS) / 密钥托管(服务托管 vs 客户托管) |
| 容灾 / DR / RPO / RTO / 业务连续性 / 多活 | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 5 (业务连续性基线) | RTO / RPO 量化目标 / 多 AZ vs 多 Region / 备份频率 + 跨域备份 / 容灾演练频率 |
| 多账号(单 workload 内提及) / 跨账号资源 | `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 3 (Landing Zone) | 软提示:planning 本身只做单 workload,跨账号资源建议先用 itgov-advisor 厘清 LZ;若用户坚持,要求其提供已有账号 ID + RAM 角色 ARN |

## Loading workflow

For each matched scenario:

1. **Read advisor section**: use the `Read` tool on the path listed above
   (use targeted `offset`/`limit` if the chapter is large — typically <
   200 lines is enough).
2. **Internalize**: extract the "决策表 / 推荐 / 客户场景示例" — these
   become the structure for Phase 1's next round of questions.
3. **Refine questions**: instead of the generic Phase 1 dimensions, ask
   the scenario-specific ones from the table above. Each question must
   reference advisor's recommended option as a default and ask the user
   to confirm / override.
4. **Surface in Mode Decision**: when later presenting the mode choice,
   add a 软提示:

   > "你的需求涉及 **{matched scenario}**,该场景通常需要完整规划
   > (覆盖 {scenario-specific dimensions})。**建议走 Full Mode**,但
   > 你仍可坚持 Fast Track —— 我会保留 advisor 章节作为提问框架,
   > 但跳过 deep-dive。"

5. **Persist in design.md**: when the design is finalized, the matched
   scenarios + the advisor sections referenced must appear in the
   `## Scenario Context` block of design.md so future iteration sessions can pick
   up the prior context without re-detecting.

## Multiple-scenario handling

If the message hits ≥ 2 scenarios (e.g. "等保三级 + AI 应用"),load all
matched sections and merge their additional dimensions — do NOT pick one.
The mode-upgrade suggestion language stacks the scenarios:

> "你的需求同时涉及 **{scenario A}** 和 **{scenario B}**,跨多个治理领域。
> **强烈建议走 Full Mode**,Fast Track 在多场景叠加下覆盖不全。"

## Boundary: scenario triggers do NOT bypass Phase 0.0

Phase 0.0 (战略层意图分流) fires first. If it routes the user to advisor
for upstream LZ scoping, the scenario triggers in this file only apply
after the user returns and elects to proceed into the single-workload
design. This ordering prevents redundant prompting.

## Maintenance

When adding / removing a scenario:

1. Edit the table here.
2. Verify the advisor chapter / heading anchor still exists at the
   referenced path (advisor content is verbatim from upstream — anchor
   drift requires cherry-pick sync).
3. planning SKILL.md Phase 1 段 references this file as authoritative
   for the trigger map — do not duplicate the mapping there.
