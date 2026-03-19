# YatAIOS - Yet Another Transformative AI OS

## 融合原生AI智能体的意图驱动操作系统

### Intent-Driven Operating System with Native AI Agent Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Platform: RISC-V K1](https://img.shields.io/badge/Platform-K1%20RISC--V-orange)](https://www.spacemit.com)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![Nexa: v0.1](https://img.shields.io/badge/Nexa-v0.1-purple)](https://nexa-lang.org)

---

## 项目简介

本项目是 **2026年全国大学生计算机系统能力大赛-操作系统设计赛** 的参赛作品，赛题为"融合原生AI智能体的Bianbu系统交互范式重构"。

### 核心目标

传统的操作系统以"桌面"和"应用"为中心，用户需主动寻找、启动并操作特定程序完成任务。本项目探索 **AI原生操作系统 (LLM OS)** 的雏形：

> 以一个大语言模型（LLM）作为系统的"智能内核"与核心交互界面，将传统应用功能封装为标准化"工具"，并由智能体根据用户意图动态调度、协同执行复杂任务。

### 关键特性

- 🧠 **智能体核心** - 基于 LLM 的自然语言意图理解和任务规划
- 🔧 **工具抽象层** - 标准化的系统能力封装 (OpenAI Function Calling 格式)
- 🛡️ **安全管控** - 意图级动态权限模型和高危操作拦截
- 💾 **记忆系统** - SQLite 对话历史和任务记忆
- 🔄 **多智能体协作** - 主控 Router + 专用子智能体
- 📊 **自愈机制** - 自动分析错误并尝试修复

---

## 目录结构

```
agent-os/
├── core/                    # 核心模块
│   ├── agent_daemon.py      # 智能体守护进程
│   ├── nexa_runtime.py      # Nexa运行时
│   └── persistent_memory.py # 持久化记忆
├── tools/                   # 工具抽象层
│   ├── system_tools.py      # 系统工具集
│   └── extended_tools.py    # 扩展工具
├── security/                # 安全模块
│   └── security_manager.py  # 权限与审计
├── cli/                     # CLI 界面
│   └── llmos_cli.py         # 意图驱动 CLI
├── soul/                    # 智能体灵魂配置
│   ├── SKILL.md             # 技能定义
│   ├── SOUL.md              # 智能体灵魂
│   └── TOOLS.md             # 工具注册表
├── nexa_scripts/            # Nexa智能体脚本
│   ├── yatai_os_core.nx     # YatAIOS核心模块
│   └── bianbu_main.nx       # Bianbu主智能体
├── tests/                   # 测试
│   └── auto_test_pipeline.py # 自动测试管道
├── docs/                    # 文档
├── logs/                    # 日志目录
├── data/                    # 数据目录
├── config.yaml              # 配置文件
├── init_env.sh              # 环境初始化脚本
├── build_and_run.sh         # 一键构建运行脚本
└── README.md                # 本文档
```

---

## 快速开始

### 方式一：一键部署

```bash
# 克隆项目
git clone <repository-url>
cd agent-os

# 运行构建脚本（自动完成所有步骤）
bash build_and_run.sh --all
```

### 方式二：分步部署

```bash
# 1. 初始化环境
bash init_env.sh

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 配置 API 密钥
export OPENAI_API_KEY="your-api-key"

# 4. 启动 CLI
python3 cli/llmos_cli.py
```

### 方式三：仅运行测试

```bash
bash build_and_run.sh --test
```

---

## 使用方法

### 交互模式

启动 CLI 后，直接输入自然语言指令：

```
YatAIOS:agent-os$ 查看系统信息
YatAIOS:agent-os$ 帮我找一下桌面上昨天下载的PDF文件
YatAIOS:agent-os$ 安装 nginx 服务器
```

### 指令穿透模式

CLI支持直接执行操作系统命令，无需AI介入：

```
YatAIOS:agent-os$ ls -la
YatAIOS:agent-os$ cd /root
YatAIOS:agent-os$ pwd
YatAIOS:agent-os$ ps aux | head -10
```

### 可用命令

| 命令 | 说明 |
|------|------|
| `help` | 显示帮助信息 |
| `clear` | 清除屏幕 |
| `history` | 显示命令历史 |
| `status` | 显示当前状态 |
| `pending` | 显示待审核任务 |
| `confirm <id>` | 确认执行待审核任务 |
| `reject <id>` | 拒绝待审核任务 |
| `search <query>` | 搜索记忆中的相关任务 |
| `exit` | 退出程序 |

### 单次执行模式

```bash
# 直接执行单条指令
python3 cli/llmos_cli.py -i "查看系统信息"
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        YatAIOS                               │
│              Intent-Driven Operating System                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐│
│  │   CLI User   │ ───▶ │    Router    │ ───▶ │  Sub      ││
│  │   Interface  │      │   Agent      │      │  Agents   ││
│  │  (YatAIOS)   │      │  (Intent)     │      │ (Nexa)    ││
│  └──────────────┘      └──────────────┘      └───────────┘│
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Nexa Agent Runtime                          ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       ││
│  │  │ File    │ │Process  │ │Network  │ │Memory   │       ││
│  │  │Manager  │ │Monitor  │ │Manager  │ │Manager  │       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       ││
│  └──────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Function Calling Interface                  ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       ││
│  │  │ File    │ │Process  │ │Network  │ │Package  │       ││
│  │  │ Tools   │ │ Tools   │ │ Tools   │ │ Tools   │       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       ││
│  └──────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Security Manager                            ││
│  │  • Permission Guard  • Audit Log  • Pending Queue       ││
│  └──────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Memory Store (SQLite)                       ││
│  │  • Conversation History  • Task Memory  • Skills        ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 工具系统

### 已实现的系统工具

| 工具名称 | 功能描述 | 风险等级 |
|---------|---------|---------|
| `file_read` | 读取文件内容 | NORMAL |
| `file_write` | 写入文件内容 | ELEVATED |
| `file_search` | 搜索文件 | NORMAL |
| `file_list` | 列出目录内容 | NORMAL |
| `file_info` | 获取文件信息 | NORMAL |
| `process_list` | 列出运行中的进程 | NORMAL |
| `process_info` | 获取进程详细信息 | NORMAL |
| `process_kill` | 终止进程 | CRITICAL |
| `network_info` | 获取网络配置 | TRUSTED |
| `network_ping` | 执行 ping 测试 | TRUSTED |
| `network_connections` | 获取网络连接列表 | NORMAL |
| `package_search` | 搜索软件包 | TRUSTED |
| `package_install` | 安装软件包 | ELEVATED |
| `package_remove` | 卸载软件包 | CRITICAL |
| `package_list` | 列出已安装包 | NORMAL |
| `system_info` | 获取系统信息 | TRUSTED |
| `disk_usage` | 获取磁盘使用情况 | NORMAL |
| `memory_usage` | 获取内存使用情况 | NORMAL |

### 权限等级

| 等级 | 名称 | 说明 |
|------|------|------|
| 0 | BLOCKED | 完全禁止 |
| 1 | CRITICAL | 高危操作，需确认 |
| 2 | ELEVATED | 特权操作 |
| 3 | NORMAL | 普通操作 |
| 4 | TRUSTED | 可信操作 |

---

## 安全特性

### 高危操作拦截

系统会自动识别并拦截以下高危操作：

- `rm -rf /` - 递归删除
- `kill -9 -1` - 强制终止所有进程
- `drop database` - 删除数据库
- `chmod 777` - 设置最高权限
- `curl | sh` - 下载并执行脚本
- Fork 炸弹等

### 待审核任务队列

高危操作会被挂起到 `pending_tasks.db`，等待用户确认：

```
🏠 Bianbu > 删除 /tmp/test.txt
⚠️ 检测到高危操作：文件删除
📋 任务已加入待审核队列 (ID: a1b2c3d4)
🏠 Bianbu > pending
当前待审核任务:
  ID: a1b2c3d4
  操作: file_delete
  参数: /tmp/test.txt
  风险: CRITICAL
  
🏠 Bianbu > confirm a1b2c3d4
✅ 任务已确认执行
```

### 完整审计日志

所有操作都会被记录到审计日志：

- 时间戳
- 操作类型
- 风险等级
- 执行结果
- 用户确认状态

---

## 配置说明

配置文件 `config.yaml` 主要配置项：

### LLM 配置

```yaml
llm:
  primary:
    provider: "openai"        # openai, anthropic, ollama
    model: "glm-5"            # 默认模型
    api_base: "https://aihub.arcsysu.cn/v1"  # API端点
    api_key: "${OPENAI_API_KEY}"  # 或直接配置在config.yaml中
```

### 端云协同策略

```yaml
llm:
  edge_cloud:
    strategy: "auto"          # auto, prefer_local, prefer_cloud
    local_threshold: 0.3     # 复杂度阈值
```

### 子智能体配置

```yaml
agent:
  sub_agents:
    - name: "HardwareOptimizer"
      specialty: ["cpu", "memory", "process"]
```

---

## 测试

### 运行全部测试

```bash
python3 tests/auto_test_pipeline.py
```

### 列出测试用例

```bash
python3 tests/auto_test_pipeline.py --list
```

### 运行指定测试

```bash
python3 tests/auto_test_pipeline.py --test file_001
```

### 生成报告

```bash
python3 tests/auto_test_pipeline.py --format text --format json --format html
```

---

## 开发指南

### 添加新工具

1. 在 `tools/system_tools.py` 中添加工具定义：

```python
def _my_tool_tool(self) -> ToolDefinition:
    return ToolDefinition(
        name="my_tool",
        description="工具描述",
        parameters={
            "type": "object",
            "properties": {...}
        },
        func=self._my_tool
    )
```

2. 在 `_register_all_tools` 中注册：

```python
self._register_tool(self._my_tool_tool())
```

### 添加新子智能体

1. 在 `core/agent_daemon.py` 的 `_init_sub_agents` 中添加：

```python
SubAgent(
    name="MyAgent",
    specialty=["关键词1", "关键词2"],
    system_prompt="你的系统提示词"
)
```

---

## Nexa智能体脚本

YatAIOS使用[Nexa语言](https://nexa-lang.org)定义核心智能体和工作流。

### 核心Nexa模块

[`nexa_scripts/yatai_os_core.nx`](nexa_scripts/yatai_os_core.nx) 包含：

- **协议定义**：TaskResult, IntentClass
- **工具定义**：system_execute, memory_store, memory_retrieve, web_search
- **核心智能体**：IntentRouter, FileManager, SystemMonitor, NetworkManager, SecurityGuard, AIChatBot, MemoryManager, TaskOrchestrator
- **工作流**：main, file_operation, system_check, network_diagnosis, security_check

### 编译Nexa脚本

```bash
nexa build nexa_scripts/yatai_os_core.nx
```

### 编译并运行

```bash
nexa run nexa_scripts/yatai_os_core.nx
```

---

## 硬件平台

本项目设计运行于 **进迭时空 K1 RISC-V AI 开发平台 (MUSE BOOK)**：

- 架构: RISC-V 64位
- 特性: AI 加速
- 系统: Bianbu (基于 Ubuntu 优化)

---

## 参考资源

- [Bianbu 系统文档](https://www.spacemit.com/community/document)
- [MUSE BOOK 手册](https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/eco/k1_muse_book)
- [K1 芯片介绍](https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/key_stone/k1)

---

## 赛题信息

- **大赛名称**: 2026年全国大学生计算机系统能力大赛-操作系统设计赛
- **赛道**: OS功能挑战赛道
- **难度等级**: A (学术型)
- **维护单位**: 进迭时空（杭州）科技有限公司

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 作者

YatAIOS / Bianbu LLM OS Team

---

*最后更新: 2026-03-19*
