# OpenAPI 调用示例

## 凭证选择（开始之前必读）

| 场景 | 推荐凭证 | 文档 |
| --- | --- | --- |
| 服务端长期运行 | STS Token（通过 RAM 角色 STS::AssumeRole 获取） | https://help.aliyun.com/zh/ram/user-guide/use-an-sts-token-to-access-resources |
| 本地开发 / 调试 | AccessKey（环境变量），且必须是子账号 AK，不得是主账号 AK | https://help.aliyun.com/zh/ram/user-guide/create-an-accesskey-pair |
| 运行在 ECS 上的应用 | ECS RAM Role，无需任何长期凭证 | https://help.aliyun.com/zh/ecs/user-guide/use-an-instance-ram-role |

下方所有示例**默认假设环境变量已注入临时 STS 三件套**：

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=...
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=...
export ALIBABA_CLOUD_SECURITY_TOKEN=...
```

如果你只是在 dev 环境跑通 demo，可以临时落地子账号 AK/SK；但**禁止**将其提交到代码仓库或日志。

## Python SDK 示例

### 基础调用

```python
from alibabacloud_ecs20140526.client import Client
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi.models import Config

# 初始化客户端
import os
config = Config(
    access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
    access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'],
    security_token=os.environ.get('ALIBABA_CLOUD_SECURITY_TOKEN'),  # STS 凭证；无则视为长期 AK/SK
    region_id='cn-hangzhou',
    endpoint='ecs.cn-hangzhou.aliyuncs.com'
)
client = Client(config)

# 查询 ECS 实例
request = ecs_models.DescribeInstancesRequest(
    region_id='cn-hangzhou',
    page_number=1,
    page_size=10
)
response = client.describe_instances(request)
for instance in response.body.instances.instance:
    print(f"ID: {instance.instance_id}, Name: {instance.instance_name}, Status: {instance.status}")
```

### 批量创建实例

```python
request = ecs_models.RunInstancesRequest(
    region_id='cn-hangzhou',
    image_id='ubuntu_22_04_x64_20G_alibase_20240101.vhd',
    instance_type='ecs.g7.large',
    security_group_id='sg-xxx',
    v_switch_id='vsw-xxx',
    instance_name='my-batch-instance',
    internet_max_bandwidth_out=5,
    system_disk_category='cloud_essd',
    system_disk_size=40,
    max_count=10,  # 批量创建 10 台
    min_count=10
)
response = client.run_instances(request)
```

### STS 临时凭证

```python
from alibabacloud_sts20150401.client import Client as StsClient
from alibabacloud_sts20150401 import models as sts_models
from alibabacloud_tea_openapi.models import Config

# 使用长期 AK 获取 STS Token
sts_config = Config(
    access_key_id='<ACCESS_KEY_ID>',
    access_key_secret='<ACCESS_KEY_SECRET>',
    endpoint='sts.cn-hangzhou.aliyuncs.com'
)
sts_client = StsClient(sts_config)

request = sts_models.AssumeRoleRequest(
    role_arn='acs:ram::123456789:role/MyAppRole',
    role_session_name='session-001',
    duration_seconds=3600
)
response = sts_client.assume_role(request)

# 使用 STS Token 调用 API
app_config = Config(
    access_key_id=response.body.credentials.access_key_id,
    access_key_secret=response.body.credentials.access_key_secret,
    security_token=response.body.credentials.security_token,
    region_id='cn-hangzhou'
)
app_client = Client(app_config)
```

## Java SDK 示例

### 基础调用

```java
import com.aliyun.ecs20140526.Client;
import com.aliyun.ecs20140526.models.DescribeInstancesRequest;
import com.aliyun.ecs20140526.models.DescribeInstancesResponse;
import com.aliyun.teaopenapi.models.Config;

Config config = new Config()
    .setAccessKeyId("<YOUR_ACCESS_KEY_ID>")
    .setAccessKeySecret("<YOUR_ACCESS_KEY_SECRET>")
    .setRegionId("cn-hangzhou")
    .setEndpoint("ecs.cn-hangzhou.aliyuncs.com");

Client client = new Client(config);

DescribeInstancesRequest request = new DescribeInstancesRequest()
    .setRegionId("cn-hangzhou")
    .setPageSize(10);

DescribeInstancesResponse response = client.describeInstances(request);
```

## 错误处理通用模式

```python
import time
from random import uniform

def call_api_with_retry(func, max_retries=5, *args, **kwargs):
    """带指数退避重试的 API 调用"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if 'Throttling' in error_msg and attempt < max_retries - 1:
                delay = (2 ** attempt) + uniform(0, 1)
                time.sleep(delay)
                continue
            elif 'SignatureDoesNotMatch' in error_msg:
                raise ValueError(f"签名不匹配，请检查 AK/SK 配置: {error_msg}")
            elif 'InvalidAccessKeyId' in error_msg:
                raise ValueError(f"AccessKey ID 不存在: {error_msg}")
            elif 'Forbidden.RAM' in error_msg:
                raise PermissionError(f"权限不足: {error_msg}")
            raise
```

## CLI 命令示例

### 使用 aliyun CLI 查询实例

```bash
# 查询某地域下所有 ECS 实例
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --PageSize 50

# 按标签过滤
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --Tag.1.Key "env" \
  --Tag.1.Value "production"

# 查询实例状态并输出 JSON
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --OutputCols Instances.Instance[].InstanceId,Instances.Instance[].InstanceName,Instances.Instance[].Status
```

### 创建安全组规则

```bash
aliyun ecs AuthorizeSecurityGroup \
  --RegionId cn-hangzhou \
  --SecurityGroupId sg-xxx \
  --IpProtocol tcp \
  --PortRange 443/443 \
  --SourceCidrIp 0.0.0.0/0 \
  --Policy Accept
```
