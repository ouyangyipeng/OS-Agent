# 迭代记录

## Iteration Log

本文档记录了 Bianbu LLM OS 项目的所有开发迭代过程，详细说明每次迭代的工作内容、技术决策和问题解决。

---

## 迭代概览

| 迭代 | 名称 | 日期 | 提交数 | 主要内容 |
|------|------|------|--------|---------|
| 1 | 项目初始化与文档结构 | 2026-03-19 | 2 | 项目结构、配置、License |
| 2 | 核心模块实现 | 2026-03-19 | 1 | Agent、Tools、Security、CLI |
| 3 | 持久记忆模块 | 2026-03-19 | 1 | PersistentMemoryStore |
| 4 | 核心灵魂文件 | 2026-03-19 | 1 | SKILL/TOOLS/SOUL |
| 5 | Nexa语言集成 | 2026-03-19 | 1 | Nexa运行时接口 |
| 6 | 外部工具扩展 | 2026-03-19 | 1 | WebSearch、CLI执行 |
| 7 | CLI增强 | 2026-03-19 | 1 | 持久记忆命令 |
| 8 | 完整文档 | 2026-03-19 | 1 | 方案设计、源码分析 |
| 9 | Docker容器支持 | 2026-03-19 | 1 | Dockerfile、docker-compose |
| 10 | Nexa扩展与品牌更新 | 2026-03-19 | 1 | Nexa模块、YatAIOS品牌 |
| 11 | 依赖兼容性修复 | 2026-03-23 | 1 | httpx版本修复、requirements.txt |

---

## 迭代 11: 依赖兼容性修复

### 日期
2026-03-23

### 目标
修复 httpx 0.28.x 与 openai 1.30.1 不兼容导致的 CLI 启动失败问题。

### 问题描述
运行 `python3 cli/llmos_cli.py` 时出现错误：
```
File ".../openai/_base_client.py", line 723, in __init__
    super().__init__(**kwargs)
TypeError: __init__() got an unexpected keyword argument 'proxies'
```

### 根本原因
- **httpx 0.28.0** 引入了破坏性 API 变更，移除了 `proxies` 参数
- **openai 1.30.1** 在初始化 `SyncHttpxClientWrapper` 时使用了旧版 httpx 的参数
- 版本不兼容导致 OpenAI 客户端初始化失败

### 解决方案
1. 创建 `requirements.txt` 固定依赖版本
2. 更新 `init_env.sh` 添加 `httpx==0.27.0`
3. 创建 `plans/fix_openai_init_error.md` 详细记录修复过程

### 修改的文件
| 文件 | 变更 |
|------|------|
| `requirements.txt` | 新建，固定所有依赖版本 |
| `init_env.sh` | 添加 `httpx==0.27.0` 依赖 |
| `README.md` | 添加依赖安装说明和故障排除 |
| `PROGRESS.md` | 更新进度记录 |

### 技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| httpx 版本 | 0.27.0 | 与 openai 1.30.1 兼容 |
| 依赖管理 | requirements.txt | 便于版本控制和复现 |

### 验证结果
```bash
$ python3 cli/llmos_cli.py
2026-03-23 21:02:41,617 - AgentDaemon - INFO - OpenAI 客户端初始化完成，模型: glm-5
2026-03-23 21:02:41,618 - AgentDaemon - INFO - AgentDaemon 初始化完成
```

---

## 迭代 1: 项目初始化与文档结构

### 日期
2026-03-19

### 目标
建立项目基础结构，创建必要的目录、配置文件和许可证文件。

### 完成的工作

#### 1.1 创建目录结构
```
agent-os/
├── core/                    # 核心模块
├── tools/                   # 工具抽象层
├── security/               # 安全模块
├── cli/                     # CLI界面
├── tests/                   # 测试
├── docs/                    # 文档
├── logs/                    # 日志
├── data/                    # 数据
├── cache/                   # 缓存
└── pending_tasks/           # 待审核任务
```

#### 1.2 创建配置文件
创建了 [`config.yaml`](config.yaml)，包含：
- 系统基础配置
- LLM 配置（OpenAI/Anthropic/Ollama）
- 智能体配置（Router + 4个子智能体）
- 工具系统配置
- 安全权限等级配置
- CLI 界面配置
- 硬件平台配置
- 测试配置

#### 1.3 创建许可证
采用 **Apache License 2.0**，在 [`LICENSE`](LICENSE) 中详细声明。

### 技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| License | Apache 2.0 | 商业友好，允许闭源使用 |
| 配置格式 | YAML | 易于阅读和编辑 |
| 目录结构 | 分层模块化 | 便于维护和扩展 |

### 提交记录
```
4f11706 feat: 初始化 Bianbu LLM OS 项目结构
338888f feat: 完成 Bianbu LLM OS 核心模块实现
```

---

## 迭代 2: 核心模块实现

### 日期
2026-03-19

### 目标
实现智能体核心、系统工具、安全管理和CLI界面的完整功能。

### 完成的工作

#### 2.1 Agent Core ([`core/agent_daemon.py`](core/agent_daemon.py))
- **LLMBridge**: 支持 OpenAI、Anthropic、Ollama 三个后端
- **MemoryStore**: SQLite 记忆库，存储对话历史和任务记忆
- **SubAgent**: 4个子智能体（HardwareOptimizer、FileManager、NetworkManager、SecurityGuard）
- **意图处理**: 完整的意图解析→任务规划→工具调用→结果整合流程

```python
# 核心类结构
class AgentDaemon:
    ├── llm: LLMBridge           # LLM推理引擎
    ├── memory: MemoryStore       # 记忆存储
    ├── tools: SystemTools       # 系统工具
    ├── security_manager: SecurityManager  # 安全管理
    └── sub_agents: List[SubAgent]  # 子智能体列表
```

#### 2.2 系统工具 ([`tools/system_tools.py`](tools/system_tools.py))
实现 17 个系统工具，采用 OpenAI Function Calling 格式：

| 类别 | 工具 | 风险等级 |
|------|------|---------|
| 文件操作 | file_read, file_write, file_search, file_list, file_info | NORMAL-ELEVATED |
| 进程管理 | process_list, process_info, process_kill | NORMAL-CRITICAL |
| 网络监控 | network_info, network_ping, network_connections | TRUSTED |
| 包管理 | package_search, package_install, package_remove, package_list | ELEVATED-CRITICAL |
| 系统信息 | system_info, disk_usage, memory_usage | TRUSTED |

#### 2.3 安全管理 ([`security/security_manager.py`](security/security_manager.py))
- **5级权限模型**: BLOCKED → CRITICAL → ELEVATED → NORMAL → TRUSTED
- **高危操作识别**: 正则表达式模式匹配
- **待审核任务队列**: SQLite 存储，72小时过期
- **完整审计日志**: 所有操作可追溯

#### 2.4 CLI 界面 ([`cli/llmos_cli.py`](cli/llmos_cli.py))
- Rich 美化输出
- 命令历史管理
- 待审核任务管理
- 多会话支持

### 技术亮点

1. **ReAct 模式**: Reasoning + Acting，思考后执行
2. **标准化接口**: OpenAI Function Calling 格式，易于扩展
3. **安全优先**: 所有工具调用经过风险评估

---

## 迭代 3: 持久记忆模块

### 日期
2026-03-19

### 目标
为智能体添加持久记忆能力，使其成为长期助手而非短期对话窗口。

### 完成的工作

#### 3.1 PersistentMemoryStore
扩展 MemoryStore 实现跨会话持久记忆：

```python
class PersistentMemoryStore:
    """持久记忆存储"""
    
    # 短期记忆：当前会话
    conversation_history: List[Message]
    
    # 中期记忆：最近任务
    recent_tasks: List[Task]
    
    # 长期记忆：重要事实
    long_term_memory: Dict[str, Fact]
    
    # 技能记忆：学会的技能
    skill_memory: List[Skill]
```

#### 3.2 记忆分级

| 级别 | 内容 | 保留时间 | 存储方式 |
|------|------|---------|---------|
| 短期 | 当前会话消息 | 会话结束 | 内存 |
| 中期 | 最近任务 | 7天 | SQLite |
| 长期 | 重要事实 | 永久 | SQLite |
| 技能 | 学到的技能 | 永久 | 文件 |

#### 3.3 记忆索引
- 按时间索引
- 按实体索引
- 按重要性索引

### 技术决策
使用 SQLite 而非 Redis，是为了减少外部依赖，便于在 K1 边缘设备运行。

---

## 迭代 4: 核心灵魂文件

### 日期
2026-03-19

### 目标
创建赋予智能体"灵魂"的核心配置文件。

### 完成的工作

#### 4.1 SKILL.md - 技能定义
定义智能体可以学习和执行的技能：

```markdown
# Bianbu LLM OS 技能库

## 核心技能

### 文件管理
- skill.file.read: 读取文件
- skill.file.write: 写入文件
- skill.file.search: 搜索文件

### 进程管理
- skill.process.list: 列出进程
- skill.process.kill: 终止进程
```

#### 4.2 TOOLS.md - 工具注册表
系统工具的完整注册表：

```markdown
# 工具注册表

## 文件操作工具
| 工具名 | 描述 | 风险等级 | 必需参数 |
|--------|------|---------|---------|
| file_read | 读取文件 | NORMAL | path |
```

#### 4.3 SOUL.md - 智能体灵魂配置
定义智能体的性格、价值观和行为准则：

```markdown
# Bianbu LLM OS 灵魂配置

## 核心属性
- name: "Bianbu"
- personality: helpful, careful, precise
- values: 用户至上、安全第一、持续学习

## 行为准则
1. 永远不执行未经用户确认的高危操作
2. 优先使用本地工具保护用户隐私
3. 主动学习用户的偏好和习惯
```

---

## 迭代 5: Nexa 语言集成

### 日期
2026-03-19

### 目标
集成 Nexa 智能体编程语言，增强智能体的任务编排能力。

### 完成的工作

#### 5.1 Nexa 简介
Nexa 是一门为大语言模型和智能体系统设计的智能体原生编程语言，核心特性：
- **Agent-Native**: 专为智能体设计
- **类型安全**: Pydantic 动态编译
- **并发组装**: 多智能体协同
- **管道流传输**: 数据流式处理

#### 5.2 NexaRuntime 接口
创建 Nexa 运行时接口：

```python
class NexaRuntime:
    """Nexa 运行时接口"""
    
    def load_protocol(self, protocol_file: str):
        """加载协议定义"""
        
    def compile_workflow(self, nexa_script: str) -> str:
        """编译 Nexa 脚本为 Python"""
        
    def execute_workflow(self, workflow_name: str, context: Dict):
        """执行工作流"""
```

#### 5.3 工作流集成
支持使用 Nexa 定义复杂工作流：

```nexa
protocol TaskResult {
    status: "string"
    output: "any"
}

agent TaskRouter implements TaskResult {
    uses [file_ops, process_ops, network_ops]
    prompt: "路由任务到合适的工具"
}
```

---

## 迭代 6: 外部工具扩展

### 日期
2026-03-19

### 目标
扩展工具集，支持 Web 搜索和 CLI 执行等外部能力。

### 完成的工作

#### 6.1 WebSearch 工具
集成网络搜索能力：

```python
class WebSearchTool:
    """网络搜索工具"""
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        搜索网页
        """
        # 使用 DuckDuckGo 搜索
        # 返回标题、URL、摘要
```

#### 6.2 CLIExecution 工具
允许智能体执行 Shell 命令：

```python
class CLIExecutionTool:
    """CLI 命令执行工具"""
    
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        """
        执行 Shell 命令
        """
        # 严格的安全检查
        # 超时控制
        # 输出捕获
```

#### 6.3 工具安全性
- WebSearch: 限制搜索范围，避免恶意内容
- CLIExecution: 高危命令拦截，敏感操作需确认

---

## 迭代 7: CLI 增强

### 日期
2026-03-19

### 目标
增强 CLI 功能，支持持久记忆查看和技能管理。

### 完成的工作

#### 7.1 新增 CLI 命令

| 命令 | 功能 |
|------|------|
| `memory` | 查看当前记忆状态 |
| `memory search <query>` | 搜索记忆内容 |
| `skills` | 列出可用技能 |
| `learn <skill>` | 学习新技能 |
| `forget <skill>` | 遗忘技能 |
| `profile` | 查看/编辑用户画像 |
| `context` | 查看当前上下文 |

#### 7.2 持久记忆查看
```bash
🏠 Bianbu > memory
=== 记忆状态 ===
短期记忆: 3 条消息
中期记忆: 12 条任务
长期记忆: 5 个事实
技能: 17 个

🏠 Bianbu > memory search "文件"
找到 3 条相关记忆:
1. 2026-03-18: 用户搜索过 "PDF文件"
2. 2026-03-17: 用户查找过 "下载目录"
3. 2026-03-15: 用户创建过 "report.txt"
```

#### 7.3 技能管理
```bash
🏠 Bianbu > skills
=== 可用技能 ===
[文件管理]
  ✓ file.read (已掌握)
  ✓ file.write (已掌握)
  ○ file.archive (未掌握)

[系统管理]
  ✓ system.info (已掌握)
  ○ system.optimize (未掌握)
```

---

## 迭代 8: 完整文档

### 日期
2026-03-19

### 目标
完成方案设计文档和源码分析文档。

### 完成的工作

#### 8.1 方案设计文档 ([`docs/DESIGN_DOC.md`](docs/DESIGN_DOC.md))
详细描述：
- 系统架构设计
- 核心组件设计
- 数据流设计
- 安全模型
- 端云协同架构
- 测试策略

#### 8.2 源码分析文档 ([`docs/SOURCE_ANALYSIS.md`](docs/SOURCE_ANALYSIS.md))
分析：
- Agent Daemon 核心逻辑
- Tool System 实现机制
- Security Manager 算法
- Memory Store 数据结构
- CLI 交互流程

---

## 迭代 9: Docker容器支持

### 日期
2026-03-19

### 目标
为 YatAIOS 添加 Docker 容器化支持，方便在不同平台上部署和测试。

### 完成的工作

#### 9.1 Dockerfile 创建
创建基于 Ubuntu 22.04 的 Docker 镜像：
- 包含 Python 3.10、pip、git、curl 等基础工具
- 自动安装所有 Python 依赖
- 编译 Nexa 脚本（如果 nexac 可用）
- 暴露 8080 端口
- 默认启动 CLI

#### 9.2 docker-compose.yml
- 本地开发配置
- yataios-dev 服务定义

#### 9.3 bianbu/docker-compose.bianbu.yml
Bianbu K1 RISC-V 平台专用配置：
- yataios-dev: 开发环境
- bianbu-qemu: QEMU 模拟器
- yataiosd: 后台守护进程

#### 9.4 OpenAI SDK 兼容性修复
- 将 `openai==1.30.1` 改为 `openai>=1.12.0`
- 添加 `httpx==0.27.0` 解决 proxies 参数问题

#### 9.5 bianbu/README.md
创建 Bianbu 平台专用部署文档

---

## 迭代 10: Nexa扩展与品牌更新

### 日期
2026-03-19

### 目标
扩展 Nexa 智能体模块，更新项目品牌为 YatAIOS。

### 完成的工作

#### 10.1 Nexa 核心模块扩展
创建 [`nexa_scripts/yatai_os_core.nx`](nexa_scripts/yatai_os_core.nx)：
- 协议定义: TaskResult, IntentType, AgentCapability
- 智能体: IntentRouter, FileManager, ProcessManager, NetworkManager, PackageManager
- 工作流: user_onboarding, file_operation, system_monitor

#### 10.2 CLI 品牌更新
- 项目正式命名为 **YatAIOS** (Yet Another Transformative AI OS)
- 提示符更新为 `YatAIOS:path$`
- Rich 终端格式化修复 cyan/blue 控制符

#### 10.3 API 配置更新
- 模型: glm-5
- 端点: https://aihub.arcsysu.cn/v1
- API Key: sk-N9GlFtqrrVB6OsJ51O8Kyg

#### 10.4 文档更新
- PROGRESS.md: 添加迭代 14-15 记录
- bianbu/README.md: 更新 Docker 部署说明
- docs/CHANGELOG.md: 添加迭代 9-10

---

## 未来迭代规划

### 计划中的迭代

| 迭代 | 名称 | 目标 |
|------|------|------|
| 11 | RISC-V 交叉编译 | Docker buildx 交叉编译支持 |
| 12 | Web UI | 添加 Web 界面 |
| 13 | REST API | 暴露 REST 接口 |
| 14 | 多用户 | 支持多用户隔离 |
| 15 | 向量记忆 | 集成向量数据库 |

---

*最后更新: 2026-03-19 15:12 UTC*
