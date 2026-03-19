# 此文件由 Nexa v0.5 Code Generator 自动生成
# Bianbu LLM OS - Nexa编译后的主智能体
import os
import json
from src.runtime.agent import NexaAgent
from src.runtime.evaluator import nexa_semantic_eval, nexa_intent_routing
from src.runtime.orchestrator import join_agents, nexa_pipeline
from src.runtime.memory import global_memory

# ==========================================
# [Target Code] 自动生成的编排逻辑
# ==========================================

Router = NexaAgent(
    name="Router",
    prompt="You are Bianbu OS central router.",
    model="gpt-4o-mini",
    role="Router",
    memory_scope="local",
    tools=[]
)

HardwareOptimizer = NexaAgent(
    name="HardwareOptimizer",
    prompt="You are a hardware optimization expert.",
    model="gpt-4o-mini",
    role="HardwareOptimizer",
    memory_scope="local",
    tools=[]
)

FileManager = NexaAgent(
    name="FileManager",
    prompt="You are a file management expert.",
    model="gpt-4o-mini",
    role="FileManager",
    memory_scope="local",
    tools=[]
)

NetworkManager = NexaAgent(
    name="NetworkManager",
    prompt="You are a network management expert.",
    model="gpt-4o-mini",
    role="NetworkManager",
    memory_scope="local",
    tools=[]
)

SecurityGuard = NexaAgent(
    name="SecurityGuard",
    prompt="You are a security guard agent.",
    model="gpt-4o-mini",
    role="SecurityGuard",
    memory_scope="local",
    tools=[]
)

def flow_main():
    """主流程 - 意图路由"""
    result = Router.run("Start Bianbu OS")
    return result

def flow_intent_pipeline(user_input):
    """意图处理管道"""
    routed = nexa_intent_routing(user_input, {
        "hardware": HardwareOptimizer,
        "file": FileManager,
        "network": NetworkManager,
        "security": SecurityGuard,
    })
    return routed.run(user_input)

def flow_pipeline(req):
    """管道处理流程"""
    result = nexa_pipeline(HardwareOptimizer, SecurityGuard, req)
    return result

def flow_review_loop(user_input):
    """语义审查循环"""
    response = Router.run(user_input)
    while True:
        feedback = SecurityGuard.run(response)
        if nexa_semantic_eval("Response is safe", str(locals())):
            break
    return response

if __name__ == "__main__":
    flow_main()
