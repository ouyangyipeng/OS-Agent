# 修复 OpenAI 客户端初始化错误

## 问题描述

运行 `python3 cli/llmos_cli.py` 时出现以下错误：

```
Traceback (most recent call last):
  File "/root/proj/os-comp/agent-os/cli/llmos_cli.py", line 837, in <module>
    main()
  File "/root/proj/os-comp/agent-os/cli/llmos_cli.py", line 817, in main
    cli = CLI(
  File "/root/proj/os-comp/agent-os/cli/llmos_cli.py", line 89, in __init__
    self.agent = AgentDaemon(config_path)
  File "/root/proj/os-comp/agent-os/core/agent_daemon.py", line 570, in __init__
    self.llm = LLMBridge(self.config)
  File "/root/proj/os-comp/agent-os/core/agent_daemon.py", line 323, in __init__
    self._init_client()
  File "/root/proj/os-comp/agent-os/core/agent_daemon.py", line 340, in _init_client
    self.client = OpenAI(api_key=api_key, base_url=api_base)
  File ".../openai/_client.py", line 122, in __init__
    super().__init__(
  File ".../openai/_base_client.py", line 825, in __init__
    self._client = http_client or SyncHttpxClientWrapper(
  File ".../openai/_base_client.py", line 723, in __init__
    super().__init__(**kwargs)
```

## 根本原因分析

### 版本信息
- **openai**: 1.30.1
- **httpx**: 0.28.1

### 问题原因

**httpx 0.28.0 引入了破坏性变更**：

1. 移除了 `proxies` 参数，改用 `proxy` 参数
2. 移除了 `transport` 参数的某些用法
3. 其他 API 变更

而 **openai 1.30.1** 版本在初始化 `SyncHttpxClientWrapper` 时，可能传递了 httpx 0.28.x 不再支持的参数，导致初始化失败。

### 依赖关系

```
openai 1.30.1 要求: httpx<1,>=0.23.0
当前安装: httpx 0.28.1
```

虽然版本范围满足要求，但 openai 1.30.1 发布时（2024年5月），httpx 0.28.0 尚未发布（2024年11月），因此存在兼容性问题。

## 修复方案

### 方案 A：降级 httpx 版本（推荐）

将 httpx 降级到 0.27.x 版本，这是 openai 1.30.1 官方测试过的版本。

**修改 [`init_env.sh`](init_env.sh:122)**：

```bash
# 核心依赖
pip install \
    langchain==0.1.20 \
    langchain-community==0.0.38 \
    langchain-core==0.1.52 \
    openai==1.30.1 \
    httpx==0.27.0 \          # 添加此行，固定 httpx 版本
    anthropic==0.21.3 \
    ...
```

**执行命令**：
```bash
pip install httpx==0.27.0
```

### 方案 B：升级 openai SDK

升级 openai SDK 到最新版本，以兼容 httpx 0.28.x。

**修改 [`init_env.sh`](init_env.sh:126)**：

```bash
pip install \
    langchain==0.1.20 \
    langchain-community==0.0.38 \
    langchain-core==0.1.52 \
    openai>=1.50.0 \         # 升级到兼容版本
    anthropic==0.21.3 \
    ...
```

**执行命令**：
```bash
pip install --upgrade openai
```

> ⚠️ **注意**: 升级 openai SDK 可能需要调整代码，因为 API 可能有变化。

### 方案 C：创建 requirements.txt（最佳实践）

创建一个 `requirements.txt` 文件来管理依赖版本：

```
# requirements.txt
langchain==0.1.20
langchain-community==0.0.38
langchain-core==0.1.52
openai==1.30.1
httpx==0.27.0
anthropic==0.21.3
requests==2.31.0
psutil==5.9.8
ply==3.11
pyyaml==6.0.1
aiofiles==23.2.1
watchdog==4.0.0
rich==13.7.1
sseclient-py==1.8.0
tiktoken==0.7.0
duckduckgo-search==5.0.1
newspaper3k==0.2.8
wikipedia==1.4.0
duckdb==0.10.2
sqlalchemy==2.0.30
plyvel==1.5.1
python-dotenv==1.0.1
```

## 推荐修复步骤

1. **立即修复**：执行 `pip install httpx==0.27.0`
2. **长期方案**：创建 `requirements.txt` 并更新 `init_env.sh`

## 验证修复

修复后运行以下命令验证：

```bash
source venv/bin/activate
python3 -c "from openai import OpenAI; print('OpenAI SDK 初始化成功')"
python3 cli/llmos_cli.py
```

## 相关文件

- [`core/agent_daemon.py`](core/agent_daemon.py:340) - OpenAI 客户端初始化位置
- [`init_env.sh`](init_env.sh:122) - 依赖安装脚本
- [`config.yaml`](config.yaml:29) - LLM 配置文件