# 此文件由 Nexa v0.5 Code Generator 自动生成
import os
import json
import pydantic
from src.runtime.stdlib import STD_NAMESPACE_MAP
from src.runtime.agent import NexaAgent
from src.runtime.evaluator import nexa_semantic_eval, nexa_intent_routing
from src.runtime.orchestrator import join_agents, nexa_pipeline
from src.runtime.memory import global_memory
from src.runtime.stdlib import STD_TOOLS_SCHEMA, STD_NAMESPACE_MAP
from src.runtime.secrets import nexa_secrets
from src.runtime.core import nexa_fallback, nexa_img_loader

# ==========================================
# [Target Code] 自动生成的编排逻辑
# ==========================================

class TaskResult(pydantic.BaseModel):
    status: str
    result: str
    error: str

class IntentClass(pydantic.BaseModel):
    type: str
    confidence: float
    params: str

__tool_system_execute_schema = {
    "name": "system_execute",
    "description": "Execute system command and return result",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
        "timeout": {"type": "int?"}
        },
        "required": ["command", "timeout"]
    }
}

__tool_memory_store_schema = {
    "name": "memory_store",
    "description": "Store information in persistent memory",
    "parameters": {
        "type": "object",
        "properties": {
            "key": {"type": "string"},
        "value": {"type": "string"},
        "level": {"type": "string?"}
        },
        "required": ["key", "value", "level"]
    }
}

__tool_memory_retrieve_schema = {
    "name": "memory_retrieve",
    "description": "Retrieve information from persistent memory",
    "parameters": {
        "type": "object",
        "properties": {
            "key": {"type": "string"}
        },
        "required": ["key"]
    }
}

__tool_web_search_schema = {
    "name": "web_search",
    "description": "Search the web for information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }
}

IntentRouter = NexaAgent(
    name="IntentRouter",
    prompt="Analyze user input and classify intent type:
    - file_op: file operations (ls, cd, cat, mkdir, rm, cp, mv)
    - system_info: system info (top, free, df, uname, ps, whoami)
    - network: network operations (ping, curl, wget, netstat)
    - security: security operations (chmod, chown, su, sudo)
    - web_search: web search (search, google, bing)
    - ai_chat: general conversation
    Return JSON format with type, confidence and params fields",
    model="minimax-m2.5",
    role="User Intent Classifier",
    memory_scope="local",
    stream=False,
    tools=[]
)

FileManager = NexaAgent(
    name="FileManager",
    prompt="You are a Linux file manager expert. Execute commands like ls, cd, cat, mkdir, rm, cp, mv, touch, chmod using shell.",
    model="glm-5",
    role="File System Manager",
    memory_scope="local",
    stream=False,
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]
)

SystemMonitor = NexaAgent(
    name="SystemMonitor",
    prompt="You are a system monitoring expert. Execute commands like top, free, df, uname, ps, whoami, hostname, uptime to gather system information.",
    model="glm-5",
    role="System Monitor",
    memory_scope="local",
    stream=False,
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]
)

NetworkManager = NexaAgent(
    name="NetworkManager",
    prompt="You are a network management expert. Handle network diagnostics, ping, curl, wget, and network configuration.",
    model="glm-5",
    role="Network Manager",
    memory_scope="local",
    stream=False,
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]
)

SecurityGuard = NexaAgent(
    name="SecurityGuard",
    prompt="You are a security guard for the OS. Assess risk level of commands. Block dangerous operations like rm -rf /, format, fdisk unless explicitly authorized.",
    model="glm-5",
    role="Security Guard",
    memory_scope="local",
    stream=False,
    tools=[]
)

AIChatBot = NexaAgent(
    name="AIChatBot",
    prompt="You are YatAIOS, a friendly and helpful AI assistant. Engage in natural conversation and assist with user queries.",
    model="glm-5",
    role="Conversational AI",
    memory_scope="local",
    stream=False,
    tools=[]
)

MemoryManager = NexaAgent(
    name="MemoryManager",
    prompt="You manage persistent memory for the OS. Store important facts, preferences, and conversation history.",
    model="glm-5",
    role="Memory Manager",
    memory_scope="local",
    stream=False,
    tools=[__tool_memory_store_schema, __tool_memory_retrieve_schema]
)

TaskOrchestrator = NexaAgent(
    name="TaskOrchestrator",
    prompt="You are a task orchestrator. Coordinate multiple agents to complete complex multi-step tasks.",
    model="glm-5",
    role="Task Coordinator",
    memory_scope="local",
    stream=False,
    tools=[]
)

def flow_main():
    user_input = "Show me system status"
    IntentRouter.run(user_input)

def flow_file_operation():
    FileManager.run("ls -la")

def flow_system_check():
    SystemMonitor.run("uname -a && free -h && df -h")

def flow_network_diagnosis():
    NetworkManager.run("ping -c 4 8.8.8.8")

def flow_security_check():
    SecurityGuard.run("assess chmod 644 /etc/passwd")

def flow_multi_agent_task():
    FileManager.run("ls -la")
    SystemMonitor.run("free -h")

def flow_remember():
    MemoryManager.store("user_preference", "dark_mode", "user")

def flow_quick_ls():
    FileManager.run("ls -lah")

def flow_quick_ps():
    SystemMonitor.run("ps aux | head -20")

def flow_quick_df():
    SystemMonitor.run("df -h")

def flow_quick_free():
    SystemMonitor.run("free -h")

def flow_quick_whoami():
    SystemMonitor.run("whoami")

if __name__ == "__main__":
    flow_main()
