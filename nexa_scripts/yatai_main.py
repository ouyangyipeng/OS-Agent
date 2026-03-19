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

IntentRouter = NexaAgent(
    name="IntentRouter",
    prompt="",
    model="minimax-m2.5",
    role="User Intent Router",
    memory_scope="local",
    stream=False,
    tools=[]
)

FileManager = NexaAgent(
    name="FileManager",
    prompt="You manage files. Execute ls, cd, cat, mkdir, rm etc.",
    model="glm-5",
    role="File Manager",
    memory_scope="local",
    stream=False,
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]
)

SystemMonitor = NexaAgent(
    name="SystemMonitor",
    prompt="You monitor systems. Execute top, free, df, uname etc.",
    model="glm-5",
    role="System Monitor",
    memory_scope="local",
    stream=False,
    tools=[STD_TOOLS_SCHEMA['std_shell_execute']]
)

AIChatBot = NexaAgent(
    name="AIChatBot",
    prompt="You are a friendly AI assistant.",
    model="glm-5",
    role="AI Chatbot",
    memory_scope="local",
    stream=False,
    tools=[]
)

def flow_main():
    req = "Check current directory and memory usage"
    __matched_intent = nexa_intent_routing([ "file operation", "system info"], req)
    if __matched_intent == "file operation":
        FileManager.run(req)
    elif __matched_intent == "system info":
        SystemMonitor.run(req)
    else:
        AIChatBot.run(req)

def flow_file_operation():
    FileManager.run("ls -la")

def flow_system_check():
    SystemMonitor.run("uname -a && free -h")

if __name__ == "__main__":
    flow_main()
