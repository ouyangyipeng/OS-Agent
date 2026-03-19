# Bianbu LLM OS 源码分析文档

## 1. 核心文件概览

| 文件 | 职责 | 代码行数 |
|------|------|----------|
| `core/agent_daemon.py` | 核心智能体守护进程 | ~896 |
| `core/persistent_memory.py` | 持久记忆存储 | ~880 |
| `core/nexa_runtime.py` | Nexa语言运行时 | ~450 |
| `cli/llmos_cli.py` | 命令行界面 | ~660 |
| `security/security_manager.py` | 安全管理器 | ~350 |
| `tools/system_tools.py` | 系统工具集 | ~400 |
| `tools/extended_tools.py` | 扩展工具集 | ~350 |

## 2. AgentDaemon 核心分析

### 2.1 类结构

```python
class AgentDaemon:
    """智能体守护进程 - 系统核心组件"""
    
    # 核心属性
    config: Dict              # 配置字典
    status: AgentStatus       # 当前状态
    memory: MemoryStore       # 会话记忆
    llm: LLMBridge            # LLM桥接
    tools: SystemTools        # 工具集
    security_manager: SecurityManager  # 安全管理
    sub_agents: List[SubAgent]         # 子智能体池
    current_session: Optional[ConversationContext]  # 当前会话
```

### 2.2 意图处理流程

```python
def process_intent(self, user_intent: str, session_id: str) -> Dict:
    """
    处理用户意图的核心流程:
    
    1. 状态更新: IDLE -> THINKING
    2. 消息构建: 添加用户消息到上下文
    3. LLM推理: 调用LLM理解意图
    4. 响应处理: 
       - 如果是纯文本响应 -> 直接返回
       - 如果是工具调用 -> 执行工具
    5. 结果保存: 保存助手消息到记忆
    """
    
    # 关键代码段
    self.status = AgentStatus.THINKING
    self.current_session.messages.append(user_message)
    
    # 调用LLM
    response = self.llm.chat(
        messages=self.current_session.messages,
        tools=self.tool_definitions
    )
    
    # 处理工具调用
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = self._execute_tool(tool_call)
            # ...
```

### 2.3 工具执行机制

```python
def _execute_tool(self, tool_call: Dict) -> Dict:
    """执行单个工具调用"""
    
    tool_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments'])
    
    # 安全检查
    risk_level = self.security_manager.assess_risk(tool_name, arguments)
    
    if risk_level == RiskLevel.BLOCKED:
        return {'error': '操作被安全策略阻止'}
    
    # 权限检查
    if not self.security_manager.check_permission(tool_name, arguments):
        return {'error': '权限不足'}
    
    # 执行工具
    tool_method = getattr(self.tools, tool_name, None)
    if tool_method:
        result = tool_method(**arguments)
    
    return {'result': result, 'tool': tool_name}
```

### 2.4 子智能体路由

```python
def _route_to_sub_agent(self, intent: str) -> SubAgent:
    """
    路由到合适的子智能体
    
    算法: 基于关键词匹配的专业领域路由
    
    SubAgent specialties:
    - HardwareOptimizer: [cpu, 内存, 性能, 负载, 硬件, 温度]
    - FileManager: [文件, 文件夹, 文档, 搜索, 查找]
    - NetworkManager: [网络, 连接, IP, 端口, ping]
    - SecurityGuard: [安全, 权限, 加密, 防火墙]
    """
    
    intent_lower = intent.lower()
    scores = {}
    
    for agent in self.sub_agents:
        score = sum(1 for keyword in agent.specialty if keyword in intent_lower)
        scores[agent.name] = score
    
    return max(scores, key=scores.get)
```

## 3. PersistentMemoryStore 深度分析

### 3.1 记忆层级设计

```python
class MemoryLevel(Enum):
    """四级记忆层级"""
    SHORT_TERM = "short_term"      # 会话级，24小时
    MEDIUM_TERM = "medium_term"    # 周级，7天
    LONG_TERM = "long_term"        # 月级，30天
    PERMANENT = "permanent"        # 永久不过期

class MemoryEntry:
    """记忆条目数据结构"""
    id: str              # 唯一标识符
    level: MemoryLevel   # 所属层级
    key: str             # 记忆键
    value: Any           # 记忆值
    importance: float    # 重要性 (0.0-1.0)
    tags: List[str]      # 标签用于检索
    created_at: str      # 创建时间 ISO格式
    updated_at: str      # 更新时间 ISO格式
```

### 3.2 存储机制

```python
class PersistentMemoryStore:
    """基于SQLite的持久化记忆存储"""
    
    def __init__(self, db_path: str = "data/persistent_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                importance REAL DEFAULT 0.5,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT,
                user_id TEXT DEFAULT "default"
            )
        ''')
        
        # 索引优化查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memories_user_level 
            ON memories(user_id, level)
        ''')
```

### 3.3 自动过期清理

```python
def cleanup_expired(self, user_id: str = "default"):
    """
    清理过期记忆
    
    清理策略:
    - SHORT_TERM: 24小时
    - MEDIUM_TERM: 7天
    - LONG_TERM: 30天
    - PERMANENT: 不清理
    """
    
    now = datetime.datetime.now()
    cutoffs = {
        MemoryLevel.SHORT_TERM: now - timedelta(hours=24),
        MemoryLevel.MEDIUM_TERM: now - timedelta(days=7),
        MemoryLevel.LONG_TERM: now - timedelta(days=30),
        # PERMANENT 不清理
    }
    
    for level, cutoff in cutoffs.items():
        cursor.execute('''
            DELETE FROM memories 
            WHERE level = ? AND user_id = ? AND created_at < ?
        ''', (level.value, user_id, cutoff.isoformat()))
```

### 3.4 技能学习系统

```python
def learn_skill(self, skill_id: str, name: str, description: str,
               category: str, proficiency: float = 0.5):
    """
    学习新技能
    
    技能状态机:
    UNKNOWN -> LEARNING -> KNOWN
                    |
                    v
               FORBIDDEN
    """
    
    cursor.execute('''
        INSERT OR REPLACE INTO skills 
        (skill_id, name, description, category, proficiency, state)
        VALUES (?, ?, ?, ?, ?, 'LEARNING')
    ''', (skill_id, name, description, category, proficiency))

def update_proficiency(self, skill_id: str, delta: float):
    """更新技能熟练度,自动触发状态转换"""
    
    cursor.execute('''
        SELECT proficiency FROM skills WHERE skill_id = ?
    ''', (skill_id,))
    row = cursor.fetchone()
    
    if row:
        new_proficiency = min(1.0, row[0] + delta)
        new_state = 'KNOWN' if new_proficiency >= 0.8 else 'LEARNING'
        
        cursor.execute('''
            UPDATE skills 
            SET proficiency = ?, state = ?
            WHERE skill_id = ?
        ''', (new_proficiency, new_state, skill_id))
```

## 4. SecurityManager 安全模型

### 4.1 五级风险评估

```python
class RiskLevel(Enum):
    """风险等级枚举"""
    BLOCKED = 0   # 直接拒绝
    CRITICAL = 1  # 高风险需确认
    ELEVATED = 2  # 中风险需确认
    NORMAL = 3    # 低风险自动执行
    TRUSTED = 4   # 极低风险自动执行

class SecurityManager:
    """
    安全管理器
    
    风险评估算法:
    1. 模式匹配 -> BLOCKED
    2. 命令白名单 -> TRUSTED
    3. 权限等级判断 -> 对应风险等级
    """
    
    BLOCKED_PATTERNS = [
        r'rm\s+-rf\s+/\s*\*?',           # 递归删除根目录
        r'mkfs\s+.*',                     # 格式化文件系统
        r'dd\s+if=.*of=/dev/sd[a-z]',   # 直接写磁盘
        r':\(\)\{.*\|.*&.*\};:',         # Fork炸弹
    ]
    
    ELEVATED_COMMANDS = [
        'apt-get install',
        'yum install',
        'systemctl stop',
        'service stop',
    ]
    
    def assess_risk(self, tool_name: str, arguments: Dict) -> RiskLevel:
        """评估操作风险等级"""
        
        # 1. 危险模式检查
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, str(arguments)):
                return RiskLevel.BLOCKED
        
        # 2. 白名单检查
        if tool_name in self.TRUSTED_TOOLS:
            return RiskLevel.TRUSTED
        
        # 3. 权限等级判断
        if tool_name in self.ELEVATED_COMMANDS:
            return RiskLevel.ELEVATED
        
        return RiskLevel.NORMAL
```

### 4.2 Pending Task 机制

```python
class PendingTask:
    """待审核任务"""
    task_id: str
    user_intent: str
    risk_level: RiskLevel
    tool_calls: List[Dict]
    created_at: str
    status: str  # PENDING/APPROVED/REJECTED/EXPIRED

class SecurityManager:
    def create_pending_task(self, task: PendingTask) -> str:
        """创建待审核任务"""
        cursor.execute('''
            INSERT INTO pending_tasks 
            (task_id, user_intent, risk_level, tool_calls, status, created_at)
            VALUES (?, ?, ?, ?, 'PENDING', ?)
        ''', (task.task_id, task.user_intent, task.risk_level.value,
              json.dumps(task.tool_calls), task.created_at))
        return task.task_id
    
    def approve_task(self, task_id: str) -> bool:
        """批准任务"""
        cursor.execute('''
            UPDATE pending_tasks 
            SET status = 'APPROVED', approved_at = ?
            WHERE task_id = ? AND status = 'PENDING'
        ''', (datetime.datetime.now().isoformat(), task_id))
        return cursor.rowcount > 0
```

## 5. LLMBridge 架构

### 5.1 多模型支持

```python
class LLMBridge:
    """
    LLM桥接器 - 统一接口封装
    
    支持的Provider:
    - openai: GPT-4o-mini, GPT-4
    - anthropic: Claude-3-Haiku, Claude-3-Sonnet
    - ollama: LLaMA3, Mistral (本地部署)
    """
    
    PROVIDERS = {
        'openai': OpenAIClient,
        'anthropic': AnthropicClient,
        'ollama': OllamaClient,
    }
    
    def __init__(self, config: Dict):
        provider = config.get('provider', 'openai')
        self.client = self.PROVIDERS[provider](config)
    
    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> LLMResponse:
        """统一的聊天接口"""
        return self.client.complete(messages, tools)
```

### 5.2 对话上下文管理

```python
class ConversationContext:
    """会话上下文"""
    session_id: str
    user_id: Optional[str]
    messages: List[Message]  # 消息历史
    created_at: str
    last_activity: str
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append(Message(role=role, content=content))
        self.last_activity = datetime.datetime.now().isoformat()
    
    def get_context_window(self, max_turns: int = 10) -> List[Message]:
        """获取最近的上下文窗口"""
        return self.messages[-max_turns*2:]  # 每轮2条消息(user+assistant)
```

## 6. NexaRuntime 语言运行时

### 6.1 Nexa语言概述

Nexa是一种**专为智能体编程设计的领域特定语言(DSL)**，具有以下特点：

| 特性 | 描述 |
|------|------|
| 声明式语法 | 通过声明式方式定义智能体和工作流 |
| 编译时检查 | 提前发现语法和类型错误 |
| 运行时优化 | 编译后代码执行效率更高 |
| 标准工具库 | 内置std.shell等常用工具支持 |

### 6.2 Nexa源文件分析 ([`nexa_scripts/bianbu_main.nx`](nexa_scripts/bianbu_main.nx))

```nexa
agent SysAdminBot uses std.shell {
    prompt: "You are a Linux system administrator bot for Bianbu OS.
             Answer questions about the OS by executing commands like
             `uname -a`, `free -m`, `ls -la`, etc."
}

flow main {
    SysAdminBot.run("Please run `ls -a` in the current project root,
                     and check the ram usage. Then summarize what's in
                     the repo and how much memory is free.");
}
```

**源文件结构解析：**

| 语法 | 作用 |
|------|------|
| `agent SysAdminBot` | 定义名为SysAdminBot的智能体 |
| `uses std.shell` | 声明使用标准shell工具库 |
| `prompt: "..."` | 设定智能体系统提示词 |
| `flow main { ... }` | 定义名为main的工作流 |
| `SysAdminBot.run(...)` | 调用智能体的run方法执行任务 |

### 6.3 编译后的Python代码分析 ([`nexa_scripts/bianbu_main.py`](nexa_scripts/bianbu_main.py))

```python
# 此文件由 Nexa v0.5 Code Generator 自动生成
from src.runtime.stdlib import STD_NAMESPACE_MAP
from src.runtime.agent import NexaAgent
from src.runtime.evaluator import nexa_semantic_eval, nexa_intent_routing
from src.runtime.orchestrator import join_agents, nexa_pipeline
from src.runtime.memory import global_memory
from src.runtime.stdlib import STD_TOOLS_SCHEMA, STD_NAMESPACE_MAP

SysAdminBot = NexaAgent(
    name="SysAdminBot",
    prompt="You are a Linux system administrator bot for Bianbu OS...",
    model="minimax-m2.5",           # 默认模型
    role="",
    memory_scope="local",           # 记忆范围
    stream=False,                   # 非流式输出
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]  # 工具配置
)

def flow_main():
    SysAdminBot.run("Please run `ls -a` in the current project root...")

if __name__ == "__main__":
    flow_main()
```

**编译产物特点：**

| 元素 | 说明 |
|------|------|
| `NexaAgent` | Nexa运行时提供的Agent基类 |
| `STD_TOOLS_SCHEMA` | 标准工具模式注册表 |
| `flow_main()` | 工作流编译为可调用函数 |
| 依赖注入 | 通过import获取运行时组件 |

### 6.4 为什么用Nexa更好

#### 6.4.1 对比传统Python方式

**传统Python方式（手写）：**
```python
from agent_daemon import AgentDaemon

agent = AgentDaemon()
result = agent.process_intent(
    "请运行ls -a命令并检查内存使用情况"
)
```

**Nexa方式（声明式）：**
```nexa
agent SysAdminBot uses std.shell {
    prompt: "You are a Linux system administrator bot..."
}

flow main {
    SysAdminBot.run("Please run `ls -a`...");
}
```

#### 6.4.2 Nexa优势分析

| 维度 | 传统Python | Nexa | 优势 |
|------|-----------|------|------|
| **代码简洁度** | 50+行 | 8行 | Nexa减少80%代码量 |
| **类型安全** | 运行时检查 | 编译时检查 | 提前发现错误 |
| **工具集成** | 手动注册 | `uses std.shell` | 一行声明即可 |
| **工作流定义** | 硬编码 | `flow main` | 声明式，意图清晰 |
| **可维护性** | 散落各处 | 集中定义 | 易于管理和修改 |
| **学习曲线** | 需了解框架 | DSL语法 | 更符合业务逻辑 |

#### 6.4.3 Nexa编译流程

```
bianbu_main.nx (源文件)
        │
        ▼ [nexa build]
bianbu_main.py (编译产物)
        │
        ├── NexaAgent实例化
        ├── STD_TOOLS_SCHEMA加载
        ├── flow_main函数定义
        │
        ▼ [Python执行]
    API调用 → LLM响应 → 工具执行
```

#### 6.4.4 适用场景

Nexa特别适合：
- **复杂工作流**：多步骤、多智能体协作
- **快速原型**：声明式定义，迭代开发
- **跨项目复用**：标准化智能体定义
- **团队协作**：业务人员可读，易于review

---

### 6.5 Workflow执行

```python
class NexaRuntime:
    def execute_workflow(self, workflow_name: str, context: Dict,
                        agent_daemon: AgentDaemon = None) -> Any:
        """
        执行Nexa工作流
        
        执行流程:
        1. 获取工作流AST
        2. 按顺序执行每个步骤
        3. 步骤结果存入context
        4. 返回最终结果
        """
        
        workflow = self.workflows.get(workflow_name)
        result = None
        
        for step in workflow.steps:
            # 解析步骤: step_name: agent.action(args)
            agent_name, action, args = self._parse_step(step)
            
            # 执行步骤
            if action == 'complete':
                # 调用LLM生成
                result = self._execute_llm_call(agent_name, args, context)
            elif action == 'memory.store':
                # 存储记忆
                result = self._store_memory(args, context)
            
            context[step.name] = result
        
        return result
```

## 7. Tools 系统架构

### 7.1 OpenAI Function Calling 格式

```python
# tools/system_tools.py
class SystemTools:
    """系统工具集 - 基于OpenAI Function Calling格式"""
    
    def get_tools(self) -> List[Dict]:
        """
        返回工具定义列表
        
        格式遵循 OpenAI Function Calling 规范:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "工具描述",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
        """
        
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            # ... 更多工具定义
        ]
```

### 7.2 工具实现示例

```python
def read_file(self, path: str) -> Dict:
    """
    读取文件工具
    
    Args:
        path: 文件绝对路径
        
    Returns:
        {"success": True, "content": "...", "lines": 100}
        {"success": False, "error": "File not found"}
    """
    
    try:
        if not os.path.exists(path):
            return {'success': False, 'error': '文件不存在'}
        
        if not os.path.isfile(path):
            return {'success': False, 'error': '路径不是文件'}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'success': True,
            'content': content,
            'lines': len(content.splitlines()),
            'size': len(content)
        }
    
    except PermissionError:
        return {'success': False, 'error': '权限不足'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## 8. CLI 交互解析

### 8.1 命令路由

```python
class CLI:
    """命令行界面"""
    
    def run_interactive(self):
        """交互式命令循环"""
        
        while self.running:
            user_input = input("Bianbu > ").strip()
            
            # 内置命令路由
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'help':
                self.print_help()
            elif user_input.lower().startswith('memory '):
                self._handle_memory_command(user_input[7:])
            elif user_input.lower().startswith('skill '):
                self._handle_skill_command(user_input[6:])
            else:
                # AI意图处理
                result = self.agent.process_intent(user_input, self.session_id)
                self.print_result(result)
```

### 8.2 持久记忆集成

```python
def _handle_memory_command(self, args: str):
    """
    处理记忆命令
    
    命令格式:
    - memory list        # 列出所有记忆
    - memory add <k> <v> # 添加记忆
    - memory get <key>   # 获取记忆
    - memory stats       # 记忆统计
    - memory clear       # 清除过期
    """
    
    parts = args.split(maxsplit=1)
    sub_cmd = parts[0].lower()
    
    if sub_cmd == 'list':
        memories = self.persistent_memory.get_recent_memories()
        # 格式化输出...
    elif sub_cmd == 'add':
        key, value = parts[1].split(maxsplit=1)
        self.persistent_memory.store_short_term(key, value)
```

## 9. 关键设计模式

### 9.1 策略模式 - 风险评估

```python
# 不同的安全策略可以独立替换
class SecurityStrategy(ABC):
    @abstractmethod
    def assess(self, tool_name: str, args: Dict) -> RiskLevel:
        pass

class PromptSecurityStrategy(SecurityStrategy):
    """基于提示的安全策略"""
    def assess(self, tool_name: str, args: Dict) -> RiskLevel:
        # LLM判断风险
        return self.llm.judge_risk(tool_name, args)

class RuleBasedSecurityStrategy(SecurityStrategy):
    """基于规则的安全策略"""
    def assess(self, tool_name: str, args: Dict) -> RiskLevel:
        # 规则匹配
        for pattern in self.blocked:
            if re.match(pattern, str(args)):
                return RiskLevel.BLOCKED
        return RiskLevel.NORMAL
```

### 9.2 观察者模式 - 任务状态

```python
class TaskObserver(ABC):
    @abstractmethod
    def on_task_created(self, task: PendingTask): pass
    @abstractmethod
    def on_task_approved(self, task: PendingTask): pass
    @abstractmethod
    def on_task_rejected(self, task: PendingTask): pass

class TaskNotifier(TaskObserver):
    """任务通知器"""
    def on_task_approved(self, task: PendingTask):
        # 发送通知
        self.notify_user(f"任务 {task.task_id} 已批准")
```

### 9.3 工厂模式 - LLM客户端

```python
class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create(provider: str, config: Dict) -> LLMClient:
        providers = {
            'openai': OpenAIClient,
            'anthropic': AnthropicClient,
            'ollama': OllamaClient,
        }
        
        client_class = providers.get(provider)
        if not client_class:
            raise ValueError(f"Unknown provider: {provider}")
        
        return client_class(**config)
```

## 10. 性能优化

### 10.1 数据库索引

```python
# persistent_memory.py
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_user_level 
    ON memories(user_id, level)
''')

cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_key 
    ON memories(key)
''')
```

### 10.2 连接池

```python
# 复用数据库连接
class PersistentMemoryStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
```

### 10.3 记忆缓存

```python
class PersistentMemoryStore:
    def __init__(self, ...):
        self._cache = LRUCache(maxsize=1000)  # 最近使用的记忆缓存
    
    def retrieve(self, key: str, user_id: str = "default"):
        cache_key = f"{user_id}:{key}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 数据库查询
        result = self._db_get(key, user_id)
        
        if result:
            self._cache[cache_key] = result
        
        return result
```

## 11. 错误处理

### 11.1 异常层次

```python
class BianbuException(Exception):
    """基础异常类"""
    pass

class SecurityException(BianbuException):
    """安全相关异常"""
    pass

class ToolExecutionException(BianbuException):
    """工具执行异常"""
    pass

class LLMException(BianbuException):
    """LLM调用异常"""
    pass
```

### 11.2 重试机制

```python
def execute_with_retry(func, max_retries: int = 3, delay: float = 1.0):
    """带重试的函数执行"""
    
    for attempt in range(max_retries):
        try:
            return func()
        except TemporaryError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
```

## 12. 总结

### 12.1 架构亮点

| 特性 | 实现 | 优势 |
|------|------|------|
| 模块化设计 | 核心组件独立，可替换 | 易于扩展和维护 |
| 安全优先 | 五级权限+Pending机制 | 保障系统安全 |
| 持久记忆 | SQLite+四级层次 | OpenCLAW长期助手 |
| 多模型支持 | Provider抽象 | 灵活切换LLM |
| 声明式工作流 | Nexa语言 | 简化复杂任务 |

### 12.2 改进建议

1. **异步优化**: 将同步工具调用改为异步执行
2. **流式输出**: 支持SSE实时显示执行进度
3. **分布式**: 支持多Agent协作
4. **持久化存储**: 从SQLite迁移到分布式数据库
5. **监控指标**: 添加性能监控和告警

### 12.3 依赖关系图

```
cli/llmos_cli.py
    └── core/agent_daemon.py
            ├── core/llm_bridge.py (可选)
            ├── tools/system_tools.py
            │       └── security/security_manager.py
            ├── tools/extended_tools.py
            ├── core/persistent_memory.py
            ├── core/nexa_runtime.py
            └── security/security_manager.py
                    └── data/pending_tasks.db
```
