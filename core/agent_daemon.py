#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 智能体核心守护进程
Agent Core Daemon

功能：
- 作为系统"智能内核"的守护进程
- 集成 LLM 推理引擎，解析用户自然语言意图
- 生成可执行的任务规划
- SQLite 记忆库存储对话历史
- 多智能体协调机制
- 完整日志记录

Author: Bianbu LLM OS Team
"""

import os
import re
import json
import time
import sqlite3
import datetime
import threading
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from queue import Queue, Empty
from collections import defaultdict
import traceback

# 尝试导入可选依赖
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# 配置日志
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AgentDaemon')


class AgentStatus(Enum):
    """智能体状态"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    ERROR = "error"


@dataclass
class Message:
    """对话消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class TaskStep:
    """任务步骤"""
    step_id: int
    action: str
    tool_name: Optional[str]
    parameters: Dict
    result: Any
    status: str  # pending, running, success, failed, skipped
    error: Optional[str] = None


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str]
    messages: List[Message]
    created_at: str
    last_activity: str
    metadata: Dict = field(default_factory=dict)


class MemoryStore:
    """
    SQLite 记忆库
    
    存储对话历史和任务记忆
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
        logger.info(f"MemoryStore 初始化，数据库: {db_path}")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 对话历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT,
                last_activity TEXT,
                metadata TEXT,
                summary TEXT
            )
        ''')
        
        # 消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                name TEXT,
                tool_calls TEXT,
                tool_call_id TEXT,
                created_at TEXT,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )
        ''')
        
        # 任务历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                task_id TEXT PRIMARY KEY,
                session_id TEXT,
                user_intent TEXT,
                parsed_plan TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_session ON task_history(session_id)')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, context: ConversationContext):
        """保存对话上下文"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversations 
            (session_id, user_id, created_at, last_activity, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            context.session_id,
            context.user_id,
            context.created_at,
            context.last_activity,
            json.dumps(context.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def save_message(self, session_id: str, message: Message):
        """保存消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (session_id, role, content, name, tool_calls, tool_call_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            message.role,
            message.content,
            message.name,
            json.dumps(message.tool_calls) if message.tool_calls else None,
            message.tool_call_id,
            datetime.datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Message]:
        """获取对话历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, name, tool_calls, tool_call_id
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 倒序返回（从旧到新）
        messages = []
        for row in reversed(rows):
            messages.append(Message(
                role=row[0],
                content=row[1],
                name=row[2],
                tool_calls=json.loads(row[3]) if row[3] else None,
                tool_call_id=row[4]
            ))
        
        return messages
    
    def save_task(self, task_id: str, session_id: str, user_intent: str, 
                  parsed_plan: List[Dict], status: str = "running"):
        """保存任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_history 
            (task_id, session_id, user_intent, parsed_plan, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            session_id,
            user_intent,
            json.dumps(parsed_plan, ensure_ascii=False),
            status,
            datetime.datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def update_task(self, task_id: str, status: str, result: Any = None, error: str = None):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE task_history
            SET status = ?, result = ?, error = ?, completed_at = ?
            WHERE task_id = ?
        ''', (
            status,
            json.dumps(result) if result else None,
            error,
            datetime.datetime.now().isoformat(),
            task_id
        ))
        
        conn.commit()
        conn.close()
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, user_intent, result, created_at
            FROM task_history
            WHERE user_intent LIKE ? OR result LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "task_id": row[0],
                "user_intent": row[1],
                "result": json.loads(row[2]) if row[2] else None,
                "created_at": row[3]
            }
            for row in rows
        ]


class LLMBridge:
    """
    LLM 推理引擎桥接器
    
    支持多种 LLM 提供商：OpenAI、Anthropic、Ollama
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.llm_config = config.get('llm', {}).get('primary', {})
        self.provider = self.llm_config.get('provider', 'openai')
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.provider == 'openai':
            if not OPENAI_AVAILABLE:
                logger.error("OpenAI SDK 不可用")
                return
            
            api_key = os.environ.get('OPENAI_API_KEY') or self.llm_config.get('api_key')
            if not api_key:
                logger.warning("未设置 OPENAI_API_KEY")
            
            # 支持自定义API URL（如 aihub.arcsysu.cn）
            api_base = self.llm_config.get('api_base', 'https://api.openai.com/v1')
            # 优先使用配置文件中的API Key（避免环境变量覆盖）
            api_key = self.llm_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
            self.client = OpenAI(api_key=api_key, base_url=api_base)
            self.model = self.llm_config.get('model', 'gpt-4o-mini')
            logger.info(f"OpenAI 客户端初始化完成，模型: {self.model}，URL: {api_base}")
        
        elif self.provider == 'anthropic':
            try:
                from anthropic import Anthropic
                api_key = os.environ.get('ANTHROPIC_API_KEY') or self.config.get('fallback', {}).get('api_key')
                self.client = Anthropic(api_key=api_key)
                self.model = self.config.get('fallback', {}).get('model', 'claude-3-haiku-20240307')
                logger.info(f"Anthropic 客户端初始化完成，模型: {self.model}")
            except ImportError:
                logger.error("Anthropic SDK 不可用")
        
        elif self.provider == 'ollama':
            self.base_url = self.config.get('local', {}).get('api_base', 'http://localhost:11434')
            self.model = self.config.get('local', {}).get('model', 'llama3')
            logger.info(f"Ollama 客户端初始化完成，URL: {self.base_url}")
    
    def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, 
             stream: bool = False) -> Dict:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            tools: 工具定义列表 (OpenAI 格式)
            stream: 是否流式输出
            
        Returns:
            响应字典
        """
        if not self.client:
            return {"error": "LLM 客户端未初始化"}
        
        if self.provider == 'openai':
            return self._chat_openai(messages, tools, stream)
        elif self.provider == 'anthropic':
            return self._chat_anthropic(messages, tools)
        elif self.provider == 'ollama':
            return self._chat_ollama(messages, tools)
        
        return {"error": f"不支持的提供商: {self.provider}"}
    
    def _chat_openai(self, messages: List[Dict], tools: Optional[List[Dict]], stream: bool) -> Dict:
        """OpenAI 聊天接口"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.llm_config.get('temperature', 0.7),
                "max_tokens": self.llm_config.get('max_tokens', 2048),
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            if stream:
                params["stream"] = True
            
            response = self.client.chat.completions.create(**params)
            
            if stream:
                return {"streaming": True, "response": response}
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (response.choices[0].message.tool_calls or [])
                ]
            }
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            return {"error": str(e)}
    
    def _chat_anthropic(self, messages: List[Dict], tools: Optional[List[Dict]]) -> Dict:
        """Anthropic 聊天接口"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.config.get('fallback', {}).get('temperature', 0.7),
                "max_tokens": self.config.get('fallback', {}).get('max_tokens', 1024),
            }
            
            if tools:
                params["tools"] = tools
            
            response = self.client.messages.create(**params)
            
            return {
                "content": response.content[0].text if response.content else "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.name,
                            "arguments": tc.input
                        }
                    }
                    for tc in response.content if hasattr(tc, 'type') and tc.type == 'tool_use'
                ]
            }
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            return {"error": str(e)}
    
    def _chat_ollama(self, messages: List[Dict], tools: Optional[List[Dict]]) -> Dict:
        """Ollama 本地模型接口"""
        try:
            import requests
            
            # Ollama 聊天格式
            ollama_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    ollama_messages.append({"role": "system", "content": msg['content']})
                elif msg['role'] == 'user':
                    ollama_messages.append({"role": "user", "content": msg['content']})
                elif msg['role'] == 'assistant' and msg.get('content'):
                    ollama_messages.append({"role": "assistant", "content": msg['content']})
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            result = response.json()
            
            return {
                "content": result.get('message', {}).get('content', ''),
                "tool_calls": []
            }
        except Exception as e:
            logger.error(f"Ollama API 调用失败: {e}")
            return {"error": str(e)}


class SubAgent:
    """
    子智能体
    
    专门负责特定领域的任务
    """
    
    def __init__(self, name: str, specialty: List[str], system_prompt: str = ""):
        self.name = name
        self.specialty = specialty
        self.system_prompt = system_prompt or f"You are {name}, a specialized agent."
    
    def matches(self, intent: str) -> float:
        """
        判断意图是否匹配此智能体
        
        Returns:
            匹配分数 0-1
        """
        intent_lower = intent.lower()
        score = 0.0
        
        for spec in self.specialty:
            if spec.lower() in intent_lower:
                score += 0.3
        
        return min(score, 1.0)


class AgentDaemon:
    """
    智能体核心守护进程
    
    主要功能：
    1. 意图解析和任务规划
    2. 工具调用和执行
    3. 多智能体协调
    4. 记忆管理
    """
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个运行在 Bianbu LLM OS 上的智能助手。你的角色是系统的"智能内核"，负责：
1. 理解用户的自然语言意图
2. 将复杂任务分解为可执行的步骤
3. 调用适当的工具完成任务
4. 用中文回复用户

可用工具（通过 Function Calling 调用）：
- file_read: 读取文件
- file_write: 写入文件
- file_search: 搜索文件
- file_list: 列出目录
- file_info: 获取文件信息
- process_list: 列出进程
- process_info: 获取进程信息
- process_kill: 终止进程
- network_info: 获取网络信息
- network_ping: Ping 测试
- network_connections: 获取网络连接
- package_search: 搜索软件包
- package_install: 安装软件包
- package_remove: 卸载软件包
- package_list: 列出已安装包
- system_info: 获取系统信息
- disk_usage: 磁盘使用情况
- memory_usage: 内存使用情况

执行规则：
1. 先理解用户意图，再规划执行步骤
2. 优先使用工具解决问题，不要只是描述
3. 涉及高危操作会触发安全审核
4. 保持回复简洁但信息完整

记住：你就是系统，用户通过你与计算机交互。"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化智能体守护进程"""
        self.config = self._load_config(config_path)
        self.status = AgentStatus.IDLE
        self.memory = MemoryStore(self.config.get('agent', {}).get('memory', {}).get('db_path', 'data/memory.db'))
        self.llm = LLMBridge(self.config)
        
        # 初始化工具和子智能体
        from tools.system_tools import SystemTools
        from security.security_manager import SecurityManager
        
        self.security_manager = SecurityManager(self.config.get('security', {}))
        self.tools = SystemTools(self.security_manager)
        self.tool_definitions = self.tools.get_tools()
        
        # 初始化子智能体
        self.sub_agents = self._init_sub_agents()
        
        # 当前会话
        self.current_session: Optional[ConversationContext] = None
        
        # 任务队列
        self.task_queue = Queue()
        self.result_cache: Dict[str, Any] = {}
        
        logger.info("AgentDaemon 初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        if YAML_AVAILABLE and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}")
        
        return {}
    
    def _init_sub_agents(self) -> List[SubAgent]:
        """初始化子智能体"""
        return [
            SubAgent(
                name="HardwareOptimizer",
                specialty=["cpu", "内存", "性能", "负载", "硬件", "温度", "进程", "资源"],
                system_prompt="你是硬件优化专家，负责监控系统性能并提供优化建议。"
            ),
            SubAgent(
                name="FileManager",
                specialty=["文件", "文件夹", "文档", "搜索", "查找", "下载"],
                system_prompt="你是文件管理专家，负责帮助用户处理文件和文档操作。"
            ),
            SubAgent(
                name="NetworkManager",
                specialty=["网络", "连接", "IP", "端口", "ping", "网络诊断"],
                system_prompt="你是网络管理专家，负责网络配置和故障排查。"
            ),
            SubAgent(
                name="SecurityGuard",
                specialty=["安全", "权限", "加密", "防火墙", "审计"],
                system_prompt="你是安全卫士，负责评估操作风险并保护系统安全。"
            ),
        ]
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        """开始新会话"""
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        
        self.current_session = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            created_at=now,
            last_activity=now
        )
        
        # 添加系统提示
        self.current_session.messages.append(Message(
            role="system",
            content=self.SYSTEM_PROMPT
        ))
        
        self.memory.save_conversation(self.current_session)
        logger.info(f"新会话开始: {session_id}")
        
        return session_id
    
    def process_intent(self, user_intent: str, session_id: Optional[str] = None) -> Dict:
        """
        处理用户意图
        
        Args:
            user_intent: 用户的自然语言输入
            session_id: 可选的会话ID
            
        Returns:
            处理结果字典
        """
        self.status = AgentStatus.THINKING
        
        # 获取或创建会话
        if session_id:
            self.current_session = ConversationContext(
                session_id=session_id,
                user_id=None,
                messages=[],
                created_at=datetime.datetime.now().isoformat(),
                last_activity=datetime.datetime.now().isoformat()
            )
            # 加载历史消息
            history = self.memory.get_conversation_history(session_id)
            for msg in history:
                self.current_session.messages.append(msg)
            self.current_session.messages.insert(0, Message(role="system", content=self.SYSTEM_PROMPT))
        elif not self.current_session:
            session_id = self.start_session()
        else:
            session_id = self.current_session.session_id
        
        # 添加用户消息
        user_message = Message(role="user", content=user_intent)
        self.current_session.messages.append(user_message)
        self.memory.save_message(session_id, user_message)
        
        try:
            # 调用 LLM 获取响应
            messages = [
                {"role": m.role, "content": m.content}
                for m in self.current_session.messages
            ]
            
            llm_response = self.llm.chat(messages, self.tool_definitions)
            
            if "error" in llm_response:
                self.status = AgentStatus.ERROR
                return {
                    "success": False,
                    "error": llm_response["error"],
                    "session_id": session_id
                }
            
            response_content = llm_response.get("content", "")
            tool_calls = llm_response.get("tool_calls", [])
            
            # 保存助手响应
            assistant_message = Message(
                role="assistant",
                content=response_content,
                tool_calls=tool_calls if tool_calls else None
            )
            self.current_session.messages.append(assistant_message)
            self.memory.save_message(session_id, assistant_message)
            
            # 执行工具调用
            execution_results = []
            if tool_calls:
                self.status = AgentStatus.EXECUTING
                for tool_call in tool_calls:
                    result = self._execute_tool_call(tool_call)
                    execution_results.append(result)
                    
                    # 添加工具结果消息
                    tool_message = Message(
                        role="tool",
                        content=json.dumps(result, ensure_ascii=False),
                        name=tool_call.get('function', {}).get('name'),
                        tool_call_id=tool_call.get('id')
                    )
                    self.current_session.messages.append(tool_message)
                    self.memory.save_message(session_id, tool_message)
                
                # 再次调用 LLM 整合结果
                messages = [
                    {"role": m.role, "content": m.content}
                    for m in self.current_session.messages
                ]
                
                final_response = self.llm.chat(messages, None)
                response_content = final_response.get("content", response_content)
            
            self.status = AgentStatus.IDLE
            
            return {
                "success": True,
                "response": response_content,
                "session_id": session_id,
                "tool_results": execution_results,
                "steps": self._build_steps_description(tool_calls, execution_results)
            }
            
        except Exception as e:
            logger.error(f"处理意图失败: {e}\n{traceback.format_exc()}")
            self.status = AgentStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def _execute_tool_call(self, tool_call: Dict) -> Dict:
        """执行单个工具调用"""
        function = tool_call.get('function', {})
        tool_name = function.get('name')
        arguments = function.get('arguments', '{}')
        
        # 解析参数
        if isinstance(arguments, str):
            try:
                parameters = json.loads(arguments)
            except:
                parameters = {}
        else:
            parameters = arguments
        
        logger.info(f"执行工具: {tool_name}，参数: {parameters}")
        
        # 安全检查
        allowed, msg = self.security_manager.check_operation(tool_name, parameters)
        if not allowed:
            return {
                "tool": tool_name,
                "success": False,
                "error": msg,
                "blocked": True
            }
        
        # 执行工具
        result = self.tools.execute_tool(tool_name, parameters)
        
        return {
            "tool": tool_name,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    def _build_steps_description(self, tool_calls: List[Dict], results: List[Dict]) -> List[Dict]:
        """构建步骤描述"""
        steps = []
        for i, (tool_call, result) in enumerate(zip(tool_calls, results)):
            function = tool_call.get('function', {})
            steps.append({
                "step": i + 1,
                "tool": function.get('name'),
                "parameters": function.get('arguments'),
                "success": result.get('success', False),
                "summary": self._summarize_result(function.get('name'), result)
            })
        return steps
    
    def _summarize_result(self, tool_name: str, result: Dict) -> str:
        """总结工具执行结果"""
        if not result.get('success', False):
            return f"执行失败: {result.get('error', '未知错误')}"
        
        if tool_name == 'file_search':
            total = result.get('result', {}).get('total_found', 0)
            return f"找到 {total} 个文件"
        elif tool_name == 'system_info':
            return "系统信息已获取"
        elif tool_name == 'process_list':
            total = result.get('result', {}).get('total', 0)
            return f"列出 {total} 个进程"
        elif tool_name == 'network_ping':
            reachable = result.get('result', {}).get('reachable', False)
            return "主机可达" if reachable else "主机不可达"
        
        return "执行成功"
    
    def process_stream(self, user_intent: str, session_id: Optional[str] = None,
                       callback: Optional[Callable] = None) -> Dict:
        """
        流式处理意图
        
        Args:
            user_intent: 用户输入
            session_id: 会话ID
            callback: 进度回调函数
            
        Returns:
            最终结果
        """
        if callback:
            callback({"stage": "thinking", "message": "正在分析您的意图..."})
        
        result = self.process_intent(user_intent, session_id)
        
        if callback:
            if result.get("steps"):
                for step in result["steps"]:
                    callback({"stage": "tool", "message": f"执行工具: {step['tool']}"})
        
        return result
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待审核任务"""
        return self.security_manager.get_pending_tasks()
    
    def confirm_task(self, task_id: str) -> bool:
        """确认任务执行"""
        return self.security_manager.confirm_task(task_id)
    
    def reject_task(self, task_id: str) -> bool:
        """拒绝任务"""
        return self.security_manager.reject_task(task_id)
    
    def search_memory(self, query: str) -> List[Dict]:
        """搜索记忆"""
        return self.memory.search_memory(query)


def create_agent_daemon(config_path: str = "config.yaml") -> AgentDaemon:
    """创建智能体守护进程实例"""
    return AgentDaemon(config_path)


if __name__ == '__main__':
    # 演示用法
    print("=== AgentDaemon 演示 ===\n")
    
    # 创建智能体
    agent = AgentDaemon()
    
    # 处理测试意图
    test_intents = [
        "查看一下当前系统信息",
        "列出当前目录的文件",
    ]
    
    for intent in test_intents:
        print(f"\n>>> 用户: {intent}")
        result = agent.process_intent(intent)
        print(f"<<< 助手: {result.get('response', '')[:200]}...")
        if result.get('steps'):
            print(f"    执行步骤: {len(result['steps'])}")
