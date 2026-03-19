# Bianbu LLM OS - 架构设计文档

## Design Document

---

## 1. 项目概述

### 1.1 项目背景

传统的操作系统以"桌面"和"应用"为中心，用户需主动寻找、启动并操作特定程序完成任务。在大语言模型与智能体技术驱动下，下一代操作系统正经历从"工具操作"到"意图执行"的范式转移。

### 1.2 核心目标

本项目旨在探索 **AI原生操作系统 (LLM OS)** 的雏形，在进迭时空 Bianbu 系统基础上，设计并实现一个全新的智能体调度内核层，重构系统交互逻辑与能力供给方式。

### 1.3 目标成果

以一个大语言模型（LLM）作为系统的"智能内核"与核心交互界面，将传统应用功能封装为标准化"工具"，并由智能体根据用户意图动态调度、协同执行复杂任务。

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Bianbu LLM OS                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      User Interface Layer                        │ │
│  │                    (CLI / GUI / API Interface)                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     Agent Core Layer                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │ │
│  │  │   Router    │  │  Sub-Agents │  │  Memory Store       │    │ │
│  │  │   Agent     │  │  (多智能体) │  │  (SQLite)           │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘    │ │
│  │         │                │                                        │ │
│  │         └────────────────┴────────────────────────────────┐      │ │
│  │                      │                                      │      │ │
│  │              ┌────────▼────────┐                            │      │ │
│  │              │   LLM Bridge   │                            │      │ │
│  │              │ (推理引擎接口) │                            │      │ │
│  │              └────────────────┘                            │      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                  Tool Abstraction Layer                          │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │ │
│  │  │ File   │ │Process │ │Network │ │Package │ │System  │       │ │
│  │  │ Ops    │ │ Ops    │ │ Ops    │ │ Ops    │ │ Info   │       │ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │ │
│  │                                                                   │ │
│  │         OpenAI Function Calling Format (标准化接口)              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                  Security & Permission Layer                      │ │
│  │  • Dynamic Permission Guard  • Audit Log  • Pending Queue        │ │
│  │  • Risk Assessment           • User Confirmation                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                       System Kernel                               │ │
│  │           (Linux Kernel / Bianbu System / K1 RISC-V)            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 分层职责

| 层级 | 组件 | 职责 |
|------|------|------|
| 用户接口层 | CLI, GUI, API | 接收用户输入，展示结果 |
| 智能体核心层 | Router Agent, Sub-Agents | 意图解析，任务规划，多智能体协调 |
| 工具抽象层 | System Tools | 系统能力封装，标准化接口 |
| 安全层 | Security Manager | 权限管控，审计日志 |
| 系统层 | Linux Kernel | 底层系统调用 |

---

## 3. 核心组件设计

### 3.1 Agent Core (智能体核心)

#### 3.1.1 Router Agent (主控智能体)

**职责**：
- 接收并解析用户自然语言意图
- 识别意图类型和复杂度
- 决定是否需要子智能体协助
- 编排任务执行计划
- 调用工具执行任务
- 整合结果并返回响应

**设计决策**：
- 采用 ReAct (Reasoning + Acting) 模式
- 支持多轮对话上下文
- 任务分解后并行/串行执行

#### 3.1.2 Sub-Agents (子智能体)

| 子智能体 | 专业领域 | 职责 |
|---------|---------|------|
| HardwareOptimizer | 硬件/性能 | 监控 CPU、内存、IO，优化性能 |
| FileManager | 文件/文档 | 文件操作、搜索、归档 |
| NetworkManager | 网络 | 网络配置、诊断、监控 |
| SecurityGuard | 安全 | 权限审计、风险评估 |

**协作机制**：
```
用户意图 ──▶ Router Agent
                │
                ├── 简单任务 ──▶ 直接执行
                │
                └── 复杂任务 ──▶ 分发给 Sub-Agent
                                    │
                              子智能体处理 ──▶ 结果返回
                                    │
                              Router 整合 ──▶ 最终响应
```

#### 3.1.3 Memory Store (记忆库)

**设计**：
- SQLite 数据库存储
- 支持对话历史、任务记忆
- 向量搜索接口 (预留)

**数据模型**：
```sql
-- 对话表
conversations (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TIMESTAMP,
    last_activity TIMESTAMP,
    metadata JSON
)

-- 消息表
messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,  -- system/user/assistant/tool
    content TEXT,
    tool_calls JSON,
    created_at TIMESTAMP
)

-- 任务历史表
task_history (
    task_id TEXT PRIMARY KEY,
    session_id TEXT,
    user_intent TEXT,
    parsed_plan JSON,
    status TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSON,
    error TEXT
)
```

### 3.2 Tool System (工具系统)

#### 3.2.1 设计原则

1. **标准化接口** - 采用 OpenAI Function Calling 格式
2. **单一职责** - 每个工具只做一件事
3. **可组合性** - 工具可组合完成复杂任务
4. **安全优先** - 所有工具调用经过安全审核

#### 3.2.2 工具定义格式

```json
{
    "name": "file_search",
    "description": "搜索文件，支持按名称、修改时间等条件",
    "parameters": {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "搜索目录"
            },
            "pattern": {
                "type": "string", 
                "description": "文件名模式"
            },
            "max_results": {
                "type": "integer",
                "description": "最大结果数"
            }
        },
        "required": ["directory"]
    }
}
```

#### 3.2.3 工具分类

| 类别 | 工具 | 风险等级 |
|------|------|---------|
| 文件操作 | file_read, file_write, file_search, file_list, file_info | NORMAL-ELEVATED |
| 进程管理 | process_list, process_info, process_kill | NORMAL-CRITICAL |
| 网络监控 | network_info, network_ping, network_connections | TRUSTED |
| 包管理 | package_search, package_install, package_remove | ELEVATED-CRITICAL |
| 系统信息 | system_info, disk_usage, memory_usage | TRUSTED |

### 3.3 Security Manager (安全管理器)

#### 3.3.1 安全架构

```
                    ┌──────────────────┐
                    │   User Intent    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Risk Assessment  │
                    │   (风险评估)      │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  BLOCKED  │    │ CRITICAL │    │  NORMAL  │
    │  (拦截)   │    │ (挂起)   │    │  (执行)   │
    └───────────┘    └────┬─────┘    └───────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Pending Queue     │
                 │ (待审核队列)      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ User Confirm     │
                 │ (用户确认)        │
                 └────────┬─────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
        ┌───────────┐           ┌───────────┐
        │ Approved │           │ Rejected  │
        │ (执行)   │           │ (拒绝)    │
        └───────────┘           └───────────┘
```

#### 3.3.2 权限等级

| 等级 | 名称 | 行为 | 示例 |
|------|------|------|------|
| 0 | BLOCKED | 绝对禁止 | rm -rf /, mkfs |
| 1 | CRITICAL | 挂起等待确认 | kill -9, drop table |
| 2 | ELEVATED | 记录日志 | file_write, package_install |
| 3 | NORMAL | 正常执行 | file_read, process_list |
| 4 | TRUSTED | 可信执行 | system_info, ping |

#### 3.3.3 高危操作识别

**基于正则表达式模式匹配**：
```python
HIGH_RISK_PATTERNS = [
    (r'rm\s+-rf\s+[/"]?\s*$', BLOCKED, "递归删除根目录"),
    (r'kill\s+-9\s*(-1|$)', CRITICAL, "强制终止进程"),
    (r'drop\s+database', BLOCKED, "删除数据库"),
    (r'curl\s+.*\|\s*sh', CRITICAL, "下载并执行"),
    # ... 更多模式
]
```

**基于操作类型映射**：
```python
OPERATION_RISK_MAP = {
    'file_read': NORMAL,
    'file_write': ELEVATED,
    'file_delete': CRITICAL,
    'process_kill': CRITICAL,
    'package_remove': CRITICAL,
    # ...
}
```

#### 3.3.4 审计日志

```sql
audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP,
    task_id TEXT,
    action TEXT,
    risk_level INTEGER,
    result TEXT,
    user_confirm TEXT,
    details TEXT
)
```

### 3.4 LLM Bridge (大模型桥接器)

#### 3.4.1 多后端支持

| 提供商 | 模型 | 用途 | 延迟 | 成本 |
|--------|------|------|------|------|
| OpenAI | GPT-4o-mini | 主选 | 低 | 中 |
| Anthropic | Claude-3-Haiku | 备选 | 低 | 中 |
| Ollama | Llama3 | 本地边缘 | 极低 | 极低 |

#### 3.4.2 端云协同策略

```python
EDGE_CLOUD_STRATEGY = {
    "auto": "根据任务复杂度自动选择",
    "prefer_local": "优先使用本地模型",
    "prefer_cloud": "优先使用云端模型",
    "force_cloud": "强制使用云端模型"
}
```

**复杂度判断**：
- 简单任务 (如"查看时间"): 使用本地模型
- 中等任务 (如"搜索文件"): 云端优先
- 复杂任务 (如"多步骤规划"): 云端模型

### 3.5 CLI Interface (命令行界面)

#### 3.5.1 设计目标

- **简洁性** - 极简交互，快速上手
- **可解释性** - 展示 AI 思考过程
- **流式输出** - 实时显示执行状态
- **美观性** - Rich 库美化输出

#### 3.5.2 输出示例

```
╔══════════════════════════════════════════════════════════════════╗
║     ███╗   ███╗███████╗███████╗████████╗ ██████╗██╗      ██╗     ║
║     Bianbu LLM OS - Intent-Driven Operating System              ║
╚══════════════════════════════════════════════════════════════════╝

🏠 Bianbu > 查看系统信息
💭 思考中...

[STEP 1] 调用工具: system_info
  ✓ 执行成功

[AI 响应]
系统信息如下:
  • 平台: Linux
  • 版本: 6.6.0-riscv64
  • 架构: riscv64
  • CPU: 8 cores
  • 内存: 16 GB
  • 启动时间: 2026-03-19 10:00:00

🏠 Bianbu > _
```

---

## 4. 数据流设计

### 4.1 意图处理流程

```
用户输入
    │
    ▼
┌─────────────────┐
│ 意图理解 (LLM)   │
│  - 解析用户意图  │
│  - 识别关键实体  │
│  - 判断操作类型  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 任务规划 (LLM)   │
│  - 分解子任务   │
│  - 确定工具调用 │
│  - 编排执行顺序 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 安全审核         │
│  - 风险评估     │
│  - 权限检查     │
│  - 拦截/放行    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  拦截      执行
    │         │
    ▼         ▼
待审核    ┌─────────────────┐
队列      │ 工具执行        │
          │  - 并行/串行    │
          │  - 结果收集     │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ 结果整合 (LLM)   │
          │  - 格式化输出   │
          │  - 添加说明     │
          └────────┬────────┘
                   │
                   ▼
              用户响应
```

### 4.2 多轮对话流程

```
┌──────────────────────────────────────────────────────────────┐
│ Session: sess_abc123                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Turn 1:                                                     │
│  User: "帮我找一下昨天下载的PDF"                              │
│  Assistant: 分析意图 → 调用 file_search → 返回文件列表        │
│                                                              │
│  Turn 2:                                                     │
│  User: "把第一个文件的名称存到桌面的txt里"                     │
│  Assistant: 理解"第一个文件"=上一轮结果 → file_write → 完成  │
│                                                              │
│  Turn 3:                                                     │
│  User: "刚才存的是什么内容"                                   │
│  Assistant: 查询历史 → 读取文件 → 返回内容                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. 安全模型

### 5.1 威胁模型

| 威胁类型 | 描述 | 防护措施 |
|---------|------|---------|
| 恶意删除 | 用户意图或 LLM 误判导致 rm -rf | 高危模式匹配，BLOCKED 级别 |
| 权限提升 | 尝试修改系统关键配置 | 写操作风险评估，需确认 |
| 数据泄露 | 读取敏感文件 | 路径白名单/黑名单 |
| 资源耗尽 | Fork 炸弹等 | 操作频率限制 |
| 社会工程 | 诱导执行危险命令 | 用户确认机制 |

### 5.2 安全边界

**禁止操作**：
- `rm -rf /` 或任何递归删除根目录操作
- 直接写入设备文件 (`dd of=/dev/sda`)
- 格式化操作 (`mkfs.*`)
- 修改 /etc/passwd, /etc/shadow

**需要确认的操作**：
- 进程终止 (`kill -9`)
- 包卸载 (`apt-get remove`)
- 系统重启/关机
- 网络配置修改

### 5.3 纵深防御

```
Layer 1: 输入层 - 用户意图合法性检查
Layer 2: 解析层 - LLM 输出 Tool Call 验证  
Layer 3: 决策层 - Security Manager 风险评估
Layer 4: 执行层 - 工具执行前的最终检查
Layer 5: 审计层 - 所有操作的完整记录
```

---

## 6. 端云协同架构

### 6.1 设计原则

1. **隐私优先** - 敏感操作本地处理
2. **性能优先** - 低延迟任务本地执行
3. **能力优先** - 复杂推理云端处理
4. **容错优先** - 云端故障自动切换本地

### 6.2 任务分类决策

```python
def classify_task(intent: str) -> TaskCategory:
    """
    分类任务到本地或云端
    """
    # 简单信息查询 → 本地
    if any(kw in intent for kw in ['时间', '日期', '当前', '查看']):
        if '系统信息' in intent or '配置' not in intent:
            return TaskCategory.LOCAL_ONLY
    
    # 复杂推理/生成 → 云端
    if any(kw in intent for kw in ['分析', '比较', '推荐', '规划']):
        return TaskCategory.CLOUD_ONLY
    
    # 中等复杂度 → 混合
    return TaskCategory.HYBRID
```

### 6.3 边缘端 (K1 RISC-V) 优化

- 使用 Ollama 运行轻量模型 (Llama3-8B)
- 本地工具执行，减少网络延迟
- 离线能力支持
- 资源受限环境适配 (512MB RAM limit)

---

## 7. 测试策略

### 7.1 测试类型

| 类型 | 覆盖范围 | 自动化 |
|------|---------|--------|
| 单元测试 | 各模块独立功能 | ✓ |
| 集成测试 | 模块间协作 | ✓ |
| 端到端测试 | 完整用户场景 | ✓ |
| 安全测试 | 高危操作拦截 | ✓ |
| 性能测试 | 响应时间、并发 | ○ |

### 7.2 测试用例设计

**复杂意图测例**：

1. **文件搜索场景**
   ```
   意图: "帮我找一下昨天下载的带有'RISC-V'字样的PDF文件，并把它的名字提取出来存到桌面的txt里"
   验证: file_search → 文件读取 → file_write → 验证目标文件存在
   ```

2. **多步骤编排场景**
   ```
   意图: "先查看系统信息，然后列出当前目录的文件，最后搜索名为'test'的文件"
   验证: system_info → file_list → file_search → 整合结果
   ```

3. **安全拦截场景**
   ```
   意图: "执行 rm -rf /tmp/test"
   验证: 操作被拦截，加入 pending_tasks，等待确认
   ```

### 7.3 自愈机制

```python
class SelfHealingEngine:
    """
    错误自动修复引擎
    """
    
    def analyze_and_fix(self, error: Exception, context: Dict) -> bool:
        """
        分析错误类型，尝试自动修复
        """
        if isinstance(error, ImportError):
            # 自动安装缺失模块
            return self._fix_import_error(error)
        
        elif isinstance(error, TimeoutError):
            # 增加超时时间重试
            return self._fix_timeout_error(error)
        
        elif isinstance(error, PermissionError):
            # 修复文件权限
            return self._fix_permission_error(error)
        
        return False
```

---

## 8. 性能考量

### 8.1 延迟优化

| 环节 | 优化措施 |
|------|---------|
| LLM 调用 | 流式输出，减少感知延迟 |
| 工具执行 | 并行执行独立工具 |
| 网络 | 本地模型处理简单任务 |
| 缓存 | 热门查询结果缓存 |

### 8.2 资源限制 (K1 平台)

```yaml
resource_limits:
  max_memory_mb: 512
  max_cpu_percent: 80
  max_tool_execution_time: 30s
  max_session_history: 1000 messages
```

---

## 9. 未来扩展

### 9.1 规划中的功能

- [ ] Web UI 界面
- [ ] REST API 暴露
- [ ] 多用户支持
- [ ] 向量记忆存储
- [ ] 视觉理解集成
- [ ] 语音交互

### 9.2 架构演进

```
Phase 1: 单机 CLI 原型 (当前)
Phase 2: Web UI + 多用户
Phase 3: 分布式智能体协作
Phase 4: 自主学习与适应
```

---

## 10. 附录

### A. 配置项参考

详见 [config.yaml](../config.yaml)

### B. API 参考

详见各模块 docstring

### C. 术语表

| 术语 | 定义 |
|------|------|
| LLM | Large Language Model，大语言模型 |
| Agent | 智能体，能够自主决策和执行任务的实体 |
| Function Calling | 函数调用，LLM 生成结构化输出的机制 |
| ReAct | Reasoning + Acting，推理与行动结合的模式 |
| Tool | 工具，系统能力的抽象封装 |

---

*文档版本: 1.0*
*最后更新: 2026-03-19*
*作者: Bianbu LLM OS Team*
