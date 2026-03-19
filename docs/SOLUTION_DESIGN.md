# Bianbu LLM OS 方案设计文档

## 1. 项目概述

### 1.1 项目背景

Bianbu LLM OS 是面向2026年全国大学生计算机系统设计竞赛的创新作品，旨在重构边Bu OS的交互范式，将大语言模型(LLM)作为操作系统的"智能内核"，实现AI原生(AI-Native)的操作系统原型。

### 1.2 项目目标

1. **AI-Native OS**: 将LLM深度集成到操作系统架构中，使其成为系统的核心智能组件
2. **自然语言交互**: 用户可以通过自然语言与系统交互，降低使用门槛
3. **智能任务执行**: LLM理解用户意图后，通过工具调用执行系统操作
4. **长期助手**: 借鉴OpenCLAW理念，使智能体成为用户的长期助手而非短期对话窗口

### 1.3 核心创新点

| 创新点 | 描述 |
|--------|------|
| LLM原生内核 | LLM作为系统智能核心，负责意图理解、任务规划和决策 |
| 多层级记忆系统 | 短期/中期/长期/永久记忆，支持跨会话持久化 |
| 智能体编程 | 集成Nexa语言，支持声明式工作流定义 |
| 安全沙箱 | 五级权限模型 + _pending tasks_机制保障系统安全 |

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Bianbu LLM OS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   CLI/Web   │    │  API Server │    │  Other Interfaces   │ │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘ │
│         │                  │                      │            │
│         └──────────────────┼──────────────────────┘            │
│                            ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Agent Daemon                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │ │
│  │  │ Router Agent│  │ Memory Store│  │  LLMBridge      │   │ │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │ │
│  │         │                 │                  │              │ │
│  │  ┌──────┴─────────────────┴──────────────────┴──────────┐  │ │
│  │  │              Sub-Agents Pool                        │  │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │  │ │
│  │  │  │  Hardware   │ │    File     │ │   Network   │     │  │ │
│  │  │  │  Optimizer  │ │   Manager   │ │   Manager   │     │  │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     │  │ │
│  │  │  ┌─────────────┐                                     │  │ │
│  │  │  │   Security  │                                     │  │ │
│  │  │  │    Guard    │                                     │  │ │
│  │  │  └─────────────┘                                     │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                  │
│         ▼                  ▼                  ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Tools     │  │   Security  │  │   Nexa Runtime         │ │
│  │  System     │  │   Manager   │  │   (Agent Programming)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Persistent Memory Store                       │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐        │ │
│  │  │  Short  │ │ Medium  │ │  Long   │ │Permanent │        │ │
│  │  │  Term   │ │  Term   │ │  Term   │ │          │        │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 Agent Daemon

`AgentDaemon`是系统的核心守护进程，负责：

- **意图理解**: 接收用户自然语言输入，调用LLM理解用户意图
- **任务规划**: 将复杂意图分解为可执行的子任务
- **路由分发**: 根据意图类型将任务分发给合适的子智能体
- **结果聚合**: 汇总各子智能体的执行结果，返回给用户

```python
class AgentDaemon:
    def process_intent(self, user_intent: str, session_id: str) -> Dict:
        """
        处理用户意图
        
        流程:
        1. 意图分类 -> 确定任务类型
        2. 子任务分解 -> 生成执行计划
        3. 工具选择 -> 确定所需工具
        4. 执行监控 -> 调用工具执行
        5. 结果聚合 -> 整合返回
        """
```

#### 2.2.2 LLMBridge

`LLMBridge`封装了与大语言模型的交互逻辑：

- **统一接口**: 屏蔽不同LLM provider的差异
- **模型路由**: 支持GPT-4o-mini、Claude-3-Haiku、Ollama(LLaMA3)等
- **对话管理**: 维护多轮对话上下文
- **流式输出**: 支持SSE流式响应

#### 2.2.3 Memory Store

```
┌────────────────────────────────────────────┐
│           PersistentMemoryStore             │
├────────────────────────────────────────────┤
│                                            │
│  SHORT_TERM (会话级, 24小时过期)            │
│  ├── 当前会话上下文                         │
│  ├── 临时计算结果                           │
│  └── 草稿数据                               │
│                                            │
│  MEDIUM_TERM (7天过期)                      │
│  ├── 用户偏好                               │
│  ├── 最近任务历史                           │
│  └── 学习中的技能                           │
│                                            │
│  LONG_TERM (30天过期)                       │
│  ├── 重要事实                               │
│  ├── 技能熟练度                             │
│  └── 项目上下文                             │
│                                            │
│  PERMANENT (永不过期)                        │
│  ├── 用户身份信息                           │
│  ├── 核心偏好设置                           │
│  └── 关键技能认证                           │
│                                            │
└────────────────────────────────────────────┘
```

#### 2.2.4 Security Manager

五级权限模型：

| 等级 | 名称 | 风险 | 操作示例 | 处理方式 |
|------|------|------|----------|----------|
| 0 | BLOCKED | 极高 | `rm -rf /` | 直接拒绝 |
| 1 | CRITICAL | 高 | 删除系统文件 | 需要确认 |
| 2 | ELEVATED | 中 | 安装软件 | 需要确认 |
| 3 | NORMAL | 低 | 查看文件 | 自动执行 |
| 4 | TRUSTED | 极低 | 查询状态 | 自动执行 |

### 2.3 数据流

```
用户输入 -> CLI -> AgentDaemon
                    │
                    ▼
            ┌───────────────┐
            │  意图理解(LLM) │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │   意图分类     │
            │  (路由选择)    │
            └───────┬───────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Hardware │ │  File   │ │Network  │
   │SubAgent │ │ SubAgent│ │SubAgent │
   └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │
        └───────────┴───────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Security Check │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  工具执行      │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  结果聚合      │
            └───────┬───────┘
                    │
                    ▼
                 用户
```

## 3. 功能模块设计

### 3.1 工具系统

工具系统基于OpenAI Function Calling格式定义：

```yaml
# 工具定义示例
tool:
  name: read_file
  description: 读取文件内容
  parameters:
    type: object
    properties:
      path:
        type: string
        description: 文件路径
    required: [path]
```

**已实现工具**:

| 类别 | 工具 | 功能 |
|------|------|------|
| 文件 | read_file | 读取文件 |
| 文件 | write_file | 写入文件 |
| 文件 | list_directory | 列出目录 |
| 文件 | search_files | 搜索文件 |
| 进程 | get_process_list | 进程列表 |
| 进程 | kill_process | 终止进程 |
| 网络 | check_port | 端口检测 |
| 网络 | fetch_url | URL获取 |
| 包 | install_package | 安装包 |
| 系统 | system_info | 系统信息 |

### 3.2 扩展工具

#### 3.2.1 WebSearchTool

```python
class WebSearchTool:
    """网页搜索工具"""
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜索网页
        
        - 集成DuckDuckGo
        - 结果缓存30分钟
        - 支持按来源过滤
        """
    
    def fetch_page(self, url: str, timeout: int = 10) -> str:
        """获取页面内容"""
```

#### 3.2.2 CLIExecutionTool

```python
class CLIExecutionTool:
    """CLI命令执行工具"""
    
    # 安全机制
    BLOCKED_PATTERNS = [
        "rm -rf /",
        "> /dev/sd",
        ":(){:|:&};:",  # fork bomb
    ]
    
    WHITELIST = ["ls", "cat", "echo", "ps", "git"]
    
    def execute(self, command: str, timeout: int = 30) -> Dict:
        """
        安全执行CLI命令
        
        1. 模式检查 - 拦截危险命令
        2. 白名单验证 - 仅允许白名单命令
        3. 超时控制 - 防止挂起
        """
```

### 3.3 Nexa语言运行时

Nexa是一种面向智能体的声明式编程语言，用于定义工作流程：

```nexa
// Nexa工作流示例
protocol Assistant {
    agent chat {
        model: "gpt-4o-mini"
        temperature: 0.7
    }
    
    workflow greeting {
        step1: chat.complete("你好，请介绍自己")
        step2: memory.store("last_greeting", step1.result)
        return step2
    }
}
```

**Nexa核心概念**:

| 概念 | 说明 |
|------|------|
| Protocol | 协议定义，声明智能体能力 |
| Agent | 智能体实例，配置模型参数 |
| Workflow | 工作流，定义执行步骤 |
| Implements | 实现外部接口 |
| Step | 执行步骤，可嵌套 |

## 4. 持久记忆系统

### 4.1 设计理念

借鉴OpenCLAW概念，让智能体成为用户的**长期助手**：

> 传统对话窗口：每次对话都是独立的，关闭后记忆消失
> OpenCLAW模式：智能体持续学习，跨会话记住用户偏好和上下文

### 4.2 记忆层级

| 层级 | TTL | 用途 | 示例 |
|------|-----|------|------|
| SHORT_TERM | 24h | 会话临时数据 | 草稿、计算中间结果 |
| MEDIUM_TERM | 7d | 用户偏好 | 界面语言、常用命令 |
| LONG_TERM | 30d | 重要事实 | 项目结构、关键配置 |
| PERMANENT | ∞ | 核心信息 | 身份、已认证技能 |

### 4.3 技能学习

```python
class PersistentMemoryStore:
    def learn_skill(self, skill_id: str, name: str, description: str, 
                   category: str, proficiency: float = 0.5):
        """
        学习新技能
        
        技能状态:
        - UNKNOWN: 未学习
        - LEARNING: 学习中
        - KNOWN: 已掌握
        - FORBIDDEN: 禁用
        """
    
    def get_skills(self, category: str = None) -> List[Dict]:
        """获取技能列表"""
    
    def update_proficiency(self, skill_id: str, delta: float):
        """更新技能熟练度"""
```

## 5. 安全架构

### 5.1 风险评估流程

```
用户意图
    │
    ▼
┌───────────────┐
│  风险模式匹配  │ ──> BLOCKED (直接拒绝)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  命令白名单   │ ──> TRUSTED (自动执行)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  权限等级判断 │
└───────┬───────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
NORMAL    ELEVATED
(自动)    (需确认)
```

### 5.2 Pending Tasks机制

对于需要用户确认的高风险操作：

```python
@dataclass
class PendingTask:
    task_id: str
    user_intent: str
    risk_level: RiskLevel
    tool_calls: List[Dict]
    created_at: str
    status: TaskStatus  # PENDING/APPROVED/REJECTED/EXPIRED
```

**处理流程**:

1. 用户输入高风险操作
2. 系统创建PendingTask，进入待审核队列
3. 展示操作详情给用户
4. 用户 confirm/reject 决策
5. 批准则执行，拒绝则丢弃

## 6. CLI交互设计

### 6.1 命令结构

```
Bianbu > [command] [subcommand] [arguments]
```

### 6.2 内置命令

| 命令 | 说明 |
|------|------|
| help | 显示帮助 |
| clear/cls | 清屏 |
| history | 命令历史 |
| status | 当前状态 |
| pending | 待审核任务 |
| confirm \<id\> | 确认任务 |
| reject \<id\> | 拒绝任务 |
| search \<query\> | 搜索记忆 |
| memory \<sub\> | 记忆管理 |
| skill \<sub\> | 技能管理 |

### 6.3 记忆命令

| 子命令 | 说明 |
|--------|------|
| memory list | 列出所有记忆 |
| memory add \<k\> \<v\> | 添加短期记忆 |
| memory get \<key\> | 获取记忆 |
| memory stats | 记忆统计 |
| memory clear | 清除过期记忆 |

### 6.4 技能命令

| 子命令 | 说明 |
|--------|------|
| skill list | 列出已学技能 |
| skill add \<n\>|\<d\>|\<c\> | 学习新技能 |
| skill forget \<name\> | 遗忘技能 |

## 7. 配置管理

### 7.1 配置文件结构

```yaml
# config.yaml
llm:
  provider: "openai"  # openai/claude/ollama
  model: "gpt-4o-mini"
  api_key: "${OPENAI_API_KEY}"
  base_url: "https://api.openai.com/v1"

agent:
  memory:
    db_path: "data/memory.db"
  persistent_memory:
    db_path: "data/persistent_memory.db"

security:
  mode: "prompt"  # prompt/pending_tasks/auto_approve
  max_retries: 3

cli:
  prompt:
    main: "🏠 Bianbu > "
  verbose: false
```

### 7.2 环境变量

| 变量 | 说明 |
|------|------|
| OPENAI_API_KEY | OpenAI API密钥 |
| ANTHROPIC_API_KEY | Anthropic API密钥 |
| OLLAMA_BASE_URL | Ollama服务地址 |

## 8. 测试策略

### 8.1 自动化测试

```python
class AutoTestPipeline:
    """
    自动化测试管道
    
    测试类型:
    - 单元测试: 核心组件功能
    - 集成测试: 多组件协作
    - 端到端测试: 完整用户流程
    """
    
    def run_all(self) -> TestReport:
        """运行全部测试"""
    
    def run_category(self, category: str) -> TestReport:
        """按类别运行测试"""
```

### 8.2 测试覆盖

| 模块 | 测试用例数 | 覆盖率目标 |
|------|-----------|-----------|
| Agent Daemon | 50+ | 80%+ |
| Tools | 100+ | 90%+ |
| Security | 30+ | 85%+ |
| Memory | 40+ | 80%+ |

## 9. 部署架构

### 9.1 边缘-云端协同

```
┌─────────────────┐      ┌─────────────────┐
│    Edge (本地)   │      │    Cloud (云端)  │
├─────────────────┤      ├─────────────────┤
│                 │      │                 │
│  ┌───────────┐  │      │  ┌───────────┐  │
│  │ Bianbu OS │◄─┼──────┼─►│   LLM     │  │
│  └───────────┘  │      │  │  (GPT-4)  │  │
│                 │      │  └───────────┘  │
│  本地推理:      │      │                 │
│  ┌───────────┐  │      │  云端推理:      │
│  │  Ollama   │  │      │  GPT-4o-mini   │
│  │ (LLaMA3)  │  │      │  Claude-3      │
│  └───────────┘  │      │                 │
│                 │      │                 │
└─────────────────┘      └─────────────────┘
         │                        │
         └────────┬───────────────┘
                  ▼
           智能路由选择
           (本地/云端)
```

### 9.2 运行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| local | 纯本地，使用Ollama | 离线、低延迟 |
| cloud | 纯云端，使用OpenAI/Claude | 高质量、强算力 |
| hybrid | 智能路由 | 平衡质量和延迟 |

## 10. 未来展望

### 10.1 短期规划

- [ ] 完善Nexa语言编译器
- [ ] 增加更多工具集成
- [ ] 优化LLM路由策略
- [ ] 完善测试用例

### 10.2 长期愿景

- [ ] 多模态交互支持
- [ ] 分布式智能体协作
- [ ] 自主学习能力
- [ ] 硬件加速集成

## 附录

### A. 文件结构

```
agent-os/
├── cli/
│   └── llmos_cli.py          # 命令行界面
├── core/
│   ├── agent_daemon.py        # 核心智能体守护进程
│   ├── persistent_memory.py   # 持久记忆模块
│   └── nexa_runtime.py        # Nexa语言运行时
├── security/
│   └── security_manager.py    # 安全管理器
├── tools/
│   ├── system_tools.py        # 系统工具
│   └── extended_tools.py      # 扩展工具
├── soul/
│   ├── SOUL.md               # 智能体灵魂
│   ├── SKILL.md              # 技能定义
│   └── TOOLS.md              # 工具注册表
├── docs/
│   ├── DESIGN_DOC.md         # 设计文档
│   ├── SOLUTION_DESIGN.md    # 方案设计
│   ├── SOURCE_ANALYSIS.md    # 源码分析
│   ├── CHANGELOG.md          # 更新日志
│   └── LLM_DECLARATION.md    # LLM使用声明
├── tests/
│   └── auto_test_pipeline.py # 自动测试
├── data/                      # 数据目录
├── config.yaml               # 配置文件
├── LICENSE                  # Apache 2.0
└── README.md                # 项目说明
```

### B. 参考资料

- OpenAI Function Calling: https://platform.openai.com/docs/guides/gpt/function-calling
- Anthropic Claude API: https://docs.anthropic.com/
- Ollama: https://github.com/ollama/ollama
- Nexa Language: https://github.com/ouyangyipeng/Nexa
- OpenCLAW Concept: Long-term AI Assistant paradigm

### C. 许可证

本项目采用 Apache License 2.0 开源许可证。详见 [LICENSE](../LICENSE) 文件。
