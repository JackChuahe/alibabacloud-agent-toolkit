# 典型客户场景示例

本文档记录了 IT 治理领域最常见的客户问题及标准回答示例，供 Skill 参考。

## 场景 1：Landing Zone — 多账号架构设计

**对应模块**：1. Landing Zone 架构设计 → caf-knowledge-base.md 第三章

### 客户问题

> "我们公司有 5 个业务线，每个业务线有开发、测试、生产三套环境，应该怎么设计阿里云的账号架构？"

### 回答示例

这个问题很典型，你的场景适合用资源目录（Resource Directory）来管理多账号架构。

**推荐方案**：采用 "环境 × 业务线" 的二维资源目录结构。

**账号规划**：

```
管理账号（Management Account）
├── 共享服务账号（Shared Services）
│   ├── DNS / 日志 / 监控 / 安全集中管理
├── 业务线 A
│   ├── 开发环境账号
│   ├── 测试环境账号
│   └── 生产环境账号
├── 业务线 B
│   ├── 开发环境账号
│   ├── 测试环境账号
│   └── 生产环境账号
└── ...（其他业务线同理）
```

**落地步骤**：

1. **启用资源目录**：在管理账号中开启资源目录服务
2. **创建文件夹结构**：按业务线 → 环境创建文件夹
3. **创建成员账号**：每个节点一个阿里云账号
4. **配置网络**：共享服务账号部署共享 VPC，各环境 VPC 通过云企业网 CEN 互联
5. **权限管控**：通过 RAM 角色实现跨账号访问，生产环境设置权限边界

**关键注意事项**：

- 生产账号应该由管理账号统一创建，不允许业务线自行注册
- 各环境之间的网络默认隔离，仅允许明确配置的策略打通
- 建议先在测试环境验证整个架构，再推广到生产

**参考文档**：

- 资源目录快速入门：https://help.aliyun.com/zh/resource-directory/
- 云企业网 CEN：https://help.aliyun.com/zh/cen/

如果需要具体的 Terraform 代码模板，我可以提供。

---

## 场景 2：Well-Architected — 架构评审

**对应模块**：2. 云卓越架构 Well-Architected → wa-knowledge-base.md

### 客户问题

> "我们有一个电商系统跑在阿里云上，最近大促时老是出问题，能不能帮做一次架构评审？"

### 回答示例

好的，我来帮你做一个基于 Well-Architected Framework 的快速评估。先了解几个关键信息：

1. 你的系统主要用了哪些阿里云产品？（ECS、RDS、Redis、SLB、OSS 等）
2. 大促时的流量大约是平时的几倍？
3. 出的问题具体是什么表现？（响应慢、宕机、数据不一致？）

在你提供这些信息的同时，我先从六大支柱中你最可能受影响的角度给出初步分析：

**最可能的风险领域**：

#### 可靠性 — 高概率

- 是否做了多可用区部署？单可用区故障会导致全站不可用
- RDS 是否开启主备切换？Redis 是否集群模式？
- SLB 后端 ECS 是否做了健康检查和自动摘除？

#### 性能效率 — 高概率

- ECS 实例规格是否够用？是否需要更高计算型实例？
- 是否用了 Redis/Memcached 做热点数据缓存？
- 数据库是否有慢查询？索引是否合理？

#### 弹性能力

- 是否配置了弹性伸缩组（ESS）？自动扩容的触发条件是什么？
- 大促前是否做了手动扩容？弹性扩容的冷启动时间能否接受？

#### 成本优化 — 中概率

- 是否用了包年包月 + 按量付费混合模式？
- 预留实例券（RI）或节省计划是否覆盖基础负载？

**下一步建议**：

1. 先确认以上信息，我可以给出更具体的改进方案
2. 如果条件允许，建议做一次完整的 WA 评审（覆盖全部六大支柱）
3. 对于大促场景，建议提前做容量规划和压测

---

## 场景 3：OpenAPI — API 调用与 SDK 集成

**对应模块**：3. OpenAPI 集成方案 → templates/api-examples.md

### 客户问题

> "我们要用 Python SDK 批量创建 ECS 实例，但总是遇到限流错误，怎么处理？"

### 回答示例

限流错误（`Throttling.User`）是因为 API 调用频率超过了阿里云的限制。批量创建 ECS 时很常见。

**解决方案**：

#### 1. 实施指数退避重试

```python
import time
from random import uniform
from alibabacloud_ecs20140526.client import Client
from alibabacloud_tea_openapi.models import Config

def call_with_retry(client, request, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.run_instances(request)
            return response
        except Exception as e:
            if 'Throttling' in str(e) and attempt < max_retries - 1:
                # 指数退避 + 随机抖动
                delay = (2 ** attempt) + uniform(0, 1)
                time.sleep(delay)
                continue
            raise
    return None
```

#### 2. 控制调用频率

- 批量创建时，单次 `RunInstances` 调用的 `MaxCount` 参数最大可设为 100
- 优先使用 `RunInstances` 的批量能力，而非循环调用 `CreateInstance`
- 如果确实需要多次调用，控制 QPS 在 30 以下

#### 3. 使用 SDK 内置重试

```python
config = Config(
    access_key_id='<AK>',
    access_key_secret='<SK>',
    region_id='cn-hangzhou',
    max_attempts=3,        # 最大重试次数
    read_timeout=10000,    # 读超时（毫秒）
    connect_timeout=10000  # 连接超时（毫秒）
)
```

#### 4. 申请提升限流阈值

如果你的业务确实需要更高 QPS，可以提交工单申请提升 API 限流阈值。

**参考文档**：

- RunInstances API：https://next.api.aliyun.com/api/Ecs/2014-05-26/RunInstances
- SDK 限流说明：https://help.aliyun.com/zh/sdk/developer-reference/faq-about-limits/

---

## 场景 4：IaC — Terraform 状态管理

**对应模块**：4. IaC (Terraform) → templates/terraform-state-backend.md

### 客户问题

> "我们团队多人一起用 Terraform 管理阿里云资源，状态文件老是冲突，怎么解决？"

### 回答示例

Terraform 状态冲突是多人协作中最常见的问题。核心原因是每个开发者本地都有一份 `terraform.tfstate`，当多人同时操作时会产生冲突。

#### 解决方案：使用远程状态后端

推荐用阿里云 OSS + Tablestore 作为远程状态后端：

```hcl
terraform {
  backend "oss" {
    bucket         = "your-terraform-state-bucket"
    prefix         = "env/prod"
    key            = "terraform.tfstate"
    region         = "cn-hangzhou"
    tablestore_endpoint = "https://your-instance.cn-hangzhou.ots.aliyuncs.com"
    acl            = "private"
  }
}
```

**为什么需要 Tablestore？**
OSS 本身不支持分布式锁，配合 Tablestore 可以实现 state locking，防止多人同时执行 `terraform apply`。

**团队协作最佳实践**：

1. **状态隔离**：不同环境（dev/staging/prod）用不同的 `prefix` 或 `key`
2. **使用 CI/CD**：所有 apply 通过 CI 流水线执行，禁止本地直接 apply 生产环境
3. **状态锁定**：启用 Tablestore locking，防止并发写入
4. **权限控制**：通过 RAM 限制谁可以执行 apply，谁只能执行 plan
5. **状态备份**：开启 OSS 版本控制，可以回滚到之前的状态版本

**完整的 OSS + Tablestore 状态后端配置模板**，参见 [templates/terraform-state-backend.md](templates/terraform-state-backend.md)

---

## 场景 5：合规 — 等保三级架构

**对应模块**：5. 合规与治理 → caf-knowledge-base.md 第五章

### 客户问题

> "我们的系统需要通过等保三级，阿里云上应该怎么搭建架构？"

### 回答示例

等保三级是多数企业需要满足的合规等级。以下是基于阿里云的标准架构：

**网络安全层**：

- VPC 网络隔离（业务子网、数据库子网、管理子网）
- 安全组（最小权限原则，仅开放必要端口）
- Web 应用防火墙 WAF（防御 Web 攻击）
- DDoS 高防（防大流量攻击）

**主机安全层**：

- 云安全中心（企业版或旗舰版）：入侵检测、漏洞扫描、基线检查
- 堡垒机：运维操作审计
- 主机加固：关闭不必要的服务、定期补丁更新

**数据安全层**：

- KMS 密钥管理：敏感数据加密存储
- RDS 透明数据加密（TDE）：数据库文件加密
- OSS 服务端加密（SSE-KMS）
- 数据库审计：SQL 操作记录与分析

**审计合规层**：

- 操作审计 ActionTrail：全量 API 调用日志，保留 ≥ 6 个月
- 配置审计 Config：资源配置合规检查
- 日志服务 SLS：统一日志收集与分析

**身份安全层**：

- RAM 最小权限原则
- MFA 多因素认证（管理员必须开启）
- SSO 单点登录对接企业 AD/LDAP

**落地建议**：

1. 先确定等保测评机构，确认具体要求细节
2. 按上述架构搭建后，做自评检查
3. 邀请测评机构做正式测评
4. 根据测评结果整改后复测

**参考文档**：

- 阿里云等保合规方案：https://help.aliyun.com/zh/security/
- 云安全中心：https://help.aliyun.com/zh/sas/
- 操作审计：https://help.aliyun.com/zh/actiontrail/

---

## 场景 6：成本优化 — 云资源降本

**对应模块**：5. 合规与治理（成本管理 IPIE 闭环）→ caf-knowledge-base.md

### 客户问题

> "我们每个月阿里云账单太高了，有什么降成本的方法？"

### 回答示例

云资源降本是一个系统性工作，我建议按以下优先级逐步推进：

**第一优先级 — 快速见效（1-2 周）**：

1. **识别闲置资源**
   - 未挂载的 EBS 云盘、未绑定 EIP 的弹性 IP
   - CPU/内存利用率长期 < 5% 的 ECS 实例
   - 未使用的 RDS 实例、Redis 实例

2. **关闭非生产环境的闲置资源**
   - 开发/测试环境可以非工作时间自动关机
   - 使用 ESS 的定时策略实现自动启停

**第二优先级 — 计费模式优化（1-2 周）**：

1. **包年包月覆盖基础负载**
   - 将长期运行的核心服务转为包年包月
   - 购买节省计划（Savings Plan）或预留实例券

2. **按量付费 + 抢占式实例用于弹性负载**
   - 批处理、测试任务用抢占式实例（价格是按量的 10%-20%）
   - 配合弹性伸缩自动切换

**第三优先级 — 架构优化（1-3 月）**：

1. **存储分层**：OSS 使用低频访问 / 归档存储层
2. **数据库优化**：合理选择 RDS 规格，避免过度配置
3. **CDN 加速**：静态资源走 CDN，降低 OSS 流量费用

**工具推荐**：

- 阿里云费用中心：查看用量分析和优化建议
- 成本分析报表：按标签、项目、账号维度分析
- 预算告警：设置月度预算，超支自动通知

**参考文档**：

- 费用中心：https://usercenter2.aliyun.com/
- 节省计划：https://help.aliyun.com/zh/savings-plan/
