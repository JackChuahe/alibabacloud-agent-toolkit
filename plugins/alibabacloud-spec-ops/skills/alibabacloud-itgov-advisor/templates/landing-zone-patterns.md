# Landing Zone 架构模式模板

## 模式 A：单账号多 VPC（中小企业）

### 适用场景

- 单业务线，团队规模 < 50 人
- 无严格合规要求
- 预算有限

### 架构

```
单阿里云账号
├── VPC-1（生产）
│   ├── vSwitch-1a（可用区 A）→ ECS + SLB
│   ├── vSwitch-1b（可用区 B）→ ECS + SLB
│   └── RDS（多可用区部署）
├── VPC-2（测试/开发）
│   ├── vSwitch → ECS（按量付费）
│   └── RDS（单节点）
└── VPC-3（管理）
    ├── 堡垒机
    ├── 监控（SLS + 云监控）
    └── 日志（ActionTrail + 日志服务）
```

### 权限隔离

- 生产环境：仅运维角色可访问
- 测试环境：开发角色可访问
- 管理环境：仅管理员可访问

---

## 模式 B：多账号资源目录（中大型企业）

### 适用场景

- 多业务线或多部门
- 需要环境隔离和成本分摊
- 有合规审计要求

### 资源目录结构

```
Management Account（管理账号）
│
├── Core/（核心共享服务）
│   ├── core-network（网络账号：CEN、共享 VPC）
│   ├── core-identity（身份账号：SSO、RAM）
│   └── core-security（安全账号：WAF、安全中心）
│
├── Shared/（共享工具）
│   ├── shared-log（日志账号：ActionTrail 集中存储）
│   ├── shared-monitor（监控账号：云监控集中管理）
│   └── shared-ci（CI/CD 账号：DevOps 工具链）
│
├── BU-A/（业务线 A）
│   ├── bua-dev
│   ├── bua-staging
│   └── bua-prod
│
└── BU-B/（业务线 B）
    ├── bub-dev
    ├── bub-staging
    └── bub-prod
```

### 网络架构

```
core-network 账号
├── CEN（云企业网，转发路由器 Transit Router）
│   ├── VPC-A（生产，跨可用区）
│   ├── VPC-B（测试）
│   └── VPC-C（共享服务）
│
└── VPN Gateway / 专线接入（混合云场景）
```

### 关键 Terraform 资源

```hcl
# 启用资源目录
resource "alicloud_resource_manager_resource_directory" "this" {
  enabled = true
}

# 创建文件夹
resource "alicloud_resource_manager_folder" "core" {
  folder_name       = "Core"
  parent_folder_id  = alicloud_resource_manager_resource_directory.this.root_folder_id
}

# 创建成员账号
resource "alicloud_resource_manager_account" "network" {
  account_name      = "core-network"
  display_name      = "Core Network Account"
  folder_id         = alicloud_resource_manager_folder.core.id
  payer_account_id  = alicloud_resource_manager_resource_directory.this.management_account_id
}
```

---

## 模式 C：混合云架构

### 适用场景

- 已有自建 IDC
- 部分业务上云、部分保留本地
- 需要云与本地网络互通

### 架构

```
IDC ───── 专线 / VPN ────── CEN ────── 云上多 VPC
                                    ├── 生产 VPC
                                    ├── 测试 VPC
                                    └── 共享服务 VPC
```

### 关键配置

1. **专线接入**：通过阿里云合作伙伴接入物理专线
2. **边界路由器（VBR）**：连接专线与 CEN
3. **CEN 转发路由器**：实现 VPC 与 VBR 的全互联
4. **路由传播**：自动学习本地 IDC 路由
