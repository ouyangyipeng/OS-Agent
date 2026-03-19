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

__tool_web_search_schema = {
    "name": "web_search",
    "description": "Search the web for a given query string.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }
}

Researcher = NexaAgent(
    name="Researcher",
    prompt="You are a brilliant researcher. Answer the query context based on the web search results.",
    model="minimax-m2.5",
    role="",
    memory_scope="local",
    stream=False,
    tools=[__tool_web_search_schema]
)

def flow_main():
    result = Researcher.run("Search the latest news about the new 'Nexa' programming language.")
    if nexa_semantic_eval("The result explicitly mentions 'agent-native' or 'transpiler'", result):
        Researcher.run("Provide a 50-word technical summary based on the result.", result)
    else:
        Researcher.run("Just reply: 'No relevant Nexa logic found in search results.'")

if __name__ == "__main__":
    flow_main()
