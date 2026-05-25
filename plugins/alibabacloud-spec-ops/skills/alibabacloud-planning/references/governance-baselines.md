# Governance Baseline Cross-Check (Phase 3c.5)

Authoritative cross-check list for `alibabacloud-planning` Phase 3c.5.
Mode-aware enforcement:

| Mode + Environment | Behavior | Check set |
|---|---|---|
| **Full Mode + 生产** | 硬闸门(可阻塞 Phase 5 确认) | 12 项核心必查 |
| **Fast Track + 生产** | Advisory(仅标 ⚠️,不阻塞) | 6 项 MVP |
| **Full Mode + dev/test** | Advisory checklist | 12 项核心(标 ⚠️ 不阻塞) |
| **Fast Track + dev/test** | 不查 | — |

## 生产环境判定

设计被视为"生产环境"当满足任一条件:

- 用户在 Phase 1 明示 "生产 / production / prod / 线上"
- Full Mode + 设计含 "HA / 高可用 / 多 AZ / 主备 / DR" 关键字
- 资源数量 ≥ 4 且消息中无 dev/test/个人 反向词

## 12 项核心必查项 (Full Mode 生产硬闸门)

按 4 大治理基线分组,每项给出 pass 条件 + fail 时的依据来源 + 修复建议片段。
依据章节均位于 `alibabacloud-itgov-advisor/caf-knowledge-base.md` 第五章。

### 基线 A: 身份权限(advisor § 5 - 身份权限治理基线)

| # | 必查项 | Pass 条件 | Fail 修复建议 |
|---|---|---|---|
| A1 | 主账号 AK 不出现 | 设计中所有凭证引用走 RAM 角色 / STS / ECS 实例 RAM 角色;无 `LTAI*` 长期 AK 出现在变量或代码片段中 | 改用 `data.alicloud_caller_identity` + RAM role assumption,或 `instance_ram_role_name` 给 ECS 挂角色 |
| A2 | 敏感操作走 RAM 角色 | 跨账号 / 跨服务调用一律用 RAM 角色 + 短期 STS,而非长期 AK | 创建 `alicloud_ram_role` + `alicloud_ram_role_policy_attachment`,trust policy 限制可信主体 |
| A3 | 安全组无 0.0.0.0/0 高危端口 | 入方向 SG 规则中 22 / 3389 / 6379 / 3306 / 1433 不向 0.0.0.0/0 开放 | 缩小 `source_cidr_ip` 到办公网段 / 堡垒机段,或仅 VPC 内 (`source_security_group_id`) |
| A4 | ActionTrail ≥ 180 天 | 设计含 `alicloud_actiontrail_trail` 且 OSS bucket lifecycle 保留 ≥ 180 天 | 加 `alicloud_actiontrail_trail` + `alicloud_oss_bucket_lifecycle_rule` `days = 180+` |

### 基线 B: 数据安全(advisor § 5 - 数据安全基线)

| # | 必查项 | Pass 条件 | Fail 修复建议 |
|---|---|---|---|
| B1 | RDS / Redis 无公网 endpoint | `alicloud_db_instance.connection_string` 不绑定 EIP,`alicloud_db_connection` 无 `connection_prefix` 指向公网 | 删除公网 endpoint 资源块;若必须公网,加 IP 白名单 `alicloud_db_account_privilege` + `security_ips` |
| B2 | 敏感数据加密 | RDS 开启 TDE (`tde_status = "Enabled"`),OSS 启用 SSE-KMS,EBS 用 `encrypted = true` | 加 `tde_status`,OSS 加 `server_side_encryption_rule { sse_algorithm = "KMS" }` |
| B3 | OSS bucket 非 public | `alicloud_oss_bucket.acl` ∈ {`private`},未启用 anonymous access | 改 `acl = "private"`;若需公网读,改走 CDN + 签名 URL |

### 基线 C: 通用安全(advisor § 5 - 通用安全基线)

| # | 必查项 | Pass 条件 | Fail 修复建议 |
|---|---|---|---|
| C1 | 公网入口有 WAF | 有公网 SLB / ALB / EIP 时,设计含 `alicloud_waf_domain` 或 `alicloud_cloud_firewall_*` | 引入 WAF (`alicloud_waf_domain`) 接到公网入口前 |
| C2 | 磁盘加密 | 系统盘 + 数据盘 `encrypted = true`,关键场景用 KMS CMK | 在 `alicloud_disk` / `alicloud_instance.system_disk_encrypted = true` |
| C3 | 高危端口默认封禁 | 默认 SG / 新建 SG 不预开 22 / 3389;运维入口走堡垒机 | 删除默认 22 inbound,引入 `alicloud_bastionhost_instance` |

### 基线 D: 业务连续性(advisor § 5 - 业务连续性基线)

| # | 必查项 | Pass 条件 | Fail 修复建议 |
|---|---|---|---|
| D1 | 关键资源多 AZ | ECS 跨 ≥ 2 vswitch (不同 zone),RDS 用高可用版,SLB / ALB 跨 zone | 加 vswitch 跨 zone,RDS `category = "HighAvailability"`,SLB `master_zone_id` + `slave_zone_id` |
| D2 | RDS 主备 + 自动备份 | `category = "HighAvailability"` + `backup_policy` 启用,保留 ≥ 7 天 | 加 `alicloud_db_backup_policy` `preferred_backup_period`/`backup_retention_period >= 7` |
| D3 | design.md 明确 RTO / RPO | design.md "Stability" 段落显式给出 RTO 与 RPO 数字,而非 "尽力而为" | 在 Phase 2 stability deep-dive 追问目标值,落到 design.md `## Five-Pillar Review › Stability` |

## 6 项 MVP Advisory (Fast Track 生产)

Fast Track 生产仅做下列最关键 6 项,仅标 ⚠️ 不阻塞,鼓励用户自行评估:

| # | 检查项 | 对应 12 项中的来源 |
|---|---|---|
| M1 | 主账号 AK 不出现 | = A1 |
| M2 | SG 不开 0.0.0.0/0 上的 22/3389 | = A3 (端口子集) |
| M3 | RDS 无公网 endpoint | = B1 |
| M4 | 单 AZ 必须有自动备份 | = D2 (放宽:允许单 AZ 但要求备份) |
| M5 | OSS bucket 非 public | = B3 |
| M6 | ActionTrail 已配置 (不强制 180 天) | = A4 (放宽) |

## 输出格式

### Pass 全部

> ✅ **治理基线 cross-check 全部通过 (12/12)**
>
> 设计符合阿里云 CAF 四大治理基线。可以进入 Phase 5 确认。

### 部分 Fail (Full Mode 生产)

> ⚠️ **治理基线 cross-check: 9/12 通过**
>
> **未通过项:**
>
> - ❌ **A3 安全组高危端口** — `web-sg` 入方向规则 `0.0.0.0/0:22` 违反基线。依据:[身份权限基线](../../alibabacloud-itgov-advisor/caf-knowledge-base.md#52-治理基线)
>   - 修复建议: `source_cidr_ip = "<your-office-cidr>"` 或走 `alicloud_bastionhost_instance`
> - ❌ **B2 数据加密** — RDS 未启用 TDE。依据:[数据安全基线](../../alibabacloud-itgov-advisor/caf-knowledge-base.md#52-治理基线)
>   - 修复建议: `tde_status = "Enabled"` (cloud_essd PL1+ 已支持,< 3% 性能影响)
> - ❌ **D3 RTO/RPO 缺失** — design.md 未明确目标。依据:[业务连续性基线](../../alibabacloud-itgov-advisor/caf-knowledge-base.md#52-治理基线)
>   - 修复建议: Phase 2 stability 段加入具体数字
>
> **下一步 (使用 `AskUserQuestion`):**
>
> - "调整设计修复 fail 项 (回到 Phase 3b 改方案)" — 推荐
> - "了解风险并按当前设计继续 (在 design.md Decisions Log 留痕)"

### 部分 Fail (Fast Track 生产 / dev test)

仅在 design summary 中列出 ⚠️ 项 + 修复建议,**不**用 `AskUserQuestion` 阻塞:

> ⚠️ **Advisory: 检查到 2 项治理基线建议**
>
> - SG 高危端口开公网,建议改为办公网段或堡垒机
> - RDS 未启用 TDE,生产环境强烈建议开启
>
> 这些不阻塞继续推进,但建议在 design.md Decisions Log 记录决策原因。

## design.md 落痕

Phase 3c.5 的结果必须写入 design.md 的新章节:

```markdown
## Governance Baseline Cross-Check

**Mode**: Full Mode | Fast Track
**Environment**: production | dev/test
**Result**: PASS 9/12 (3 ⚠️ acknowledged)

| # | Baseline | Status | Note |
|---|----------|--------|------|
| A1 | 主账号 AK | ✅ | — |
| A3 | SG 高危端口 | ⚠️ acknowledged | 用户接受风险:仅运维 IP 段访问,后续将引入堡垒机 |
| ... | ... | ... | ... |
```

`status.json` 同步写入 `governance_baseline_check` 字段(详见
`writing-plans/references/directory-structure.md`),以便 Day-2 复审。

## 维护

新增 / 修改基线项:

1. 编辑本文件对应基线分组的表格。
2. 同步更新 `alibabacloud-itgov-advisor/caf-knowledge-base.md` § 5 的依据(如基线本身有调整)。
3. 若新增/移除 12 项核心或 6 项 MVP 的数量,更新 planning SKILL.md Phase 3c.5 段对总数的引用。
