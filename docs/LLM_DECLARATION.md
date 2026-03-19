# 大模型使用声明

## LLM Usage Declaration

---

## 1. 声明概述

本文档声明本项目 **Bianbu LLM OS** 在开发过程中使用的大语言模型（LLM）及其具体用途。

---

## 2. 使用的大模型

### 2.1 OpenAI GPT-4o-mini

| 项目 | 说明 |
|------|------|
| **模型名称** | GPT-4o-mini |
| **提供商** | OpenAI |
| **API 端点** | https://api.openai.com/v1 |
| **使用方式** | 主要推理引擎，用于意图解析、任务规划、响应生成 |

**用途**：
- 作为智能体的核心推理引擎
- 解析用户自然语言意图
- 生成任务执行计划
- 整合工具执行结果
- 多轮对话上下文理解

### 2.2 Anthropic Claude-3-Haiku

| 项目 | 说明 |
|------|------|
| **模型名称** | Claude-3-Haiku-20240307 |
| **提供商** | Anthropic |
| **API 端点** | https://api.anthropic.com |
| **使用方式** | 备选推理引擎，云端fallback |

**用途**：
- 当 OpenAI API 不可用时的备选方案
- 复杂推理任务的协同处理

### 2.3 Ollama (Llama3)

| 项目 | 说明 |
|------|------|
| **模型名称** | Llama3 |
| **提供商** | Ollama (本地) |
| **API 端点** | http://localhost:11434 |
| **使用方式** | 边缘端本地推理 |

**用途**：
- K1 RISC-V 平台的本地推理
- 简单查询的快速响应
- 离线环境支持
- 隐私敏感操作

---

## 3. LLM 在系统中的角色

### 3.1 智能内核

本系统的核心设计理念是将 LLM 作为操作系统的"智能内核"：

```
┌─────────────────────────────────────────┐
│           User (用户)                    │
└─────────────────┬───────────────────────┘
                  │ 自然语言
                  ▼
┌─────────────────────────────────────────┐
│         LLM (智能内核)                    │
│  ┌─────────────────────────────────┐   │
│  │ 意图理解 → 任务规划 → 工具调度     │   │
│  │ 结果整合 → 响应生成               │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │ Function Calling
                  ▼
┌─────────────────────────────────────────┐
│       System Tools (系统工具)             │
│  文件/进程/网络/包管理/系统信息          │
└─────────────────────────────────────────┘
```

### 3.2 功能分解

| LLM 功能 | 具体应用 |
|---------|---------|
| **意图理解** | 解析用户自然语言输入，识别真实意图 |
| **任务分解** | 将复杂任务拆分为可执行的子任务 |
| **工具选择** | 根据任务需求选择合适的系统工具 |
| **参数生成** | 生成工具调用的参数 |
| **结果整合** | 整合多个工具的执行结果 |
| **响应生成** | 生成人类可读的响应 |
| **安全评估** | 协同 Security Manager 评估风险 |

---

## 4. API 密钥配置

### 4.1 环境变量

```bash
# OpenAI API Key
export OPENAI_API_KEY="sk-..."

# Anthropic API Key (可选)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 4.2 配置文件

在 `config.yaml` 中配置：

```yaml
llm:
  primary:
    provider: "openai"
    model: "gpt-4o-mini"
    api_key: "${OPENAI_API_KEY}"
  
  fallback:
    provider: "anthropic"
    model: "claude-3-haiku-20240307"
    api_key: "${ANTHROPIC_API_KEY}"
  
  local:
    enabled: true
    provider: "ollama"
    model: "llama3"
    api_base: "http://localhost:11434"
```

---

## 5. 提示词工程

### 5.1 系统提示词

智能体使用精心设计的系统提示词：

```python
SYSTEM_PROMPT = """你是一个运行在 Bianbu LLM OS 上的智能助手。你的角色是系统的"智能内核"，负责：
1. 理解用户的自然语言意图
2. 将复杂任务分解为可执行的步骤
3. 调用适当的工具完成任务
4. 用中文回复用户

可用工具（通过 Function Calling 调用）：
- file_read: 读取文件
- file_write: 写入文件
- file_search: 搜索文件
...
"""
```

### 5.2 工具描述

每个工具都有详细的描述，帮助 LLM 理解何时以及如何调用：

```python
def _file_read_tool(self) -> ToolDefinition:
    return ToolDefinition(
        name="file_read",
        description="读取文件内容。安全读取文本文件，支持指定行数范围。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "start_line": {"type": "integer", "description": "起始行号"},
                "max_lines": {"type": "integer", "description": "最大读取行数"}
            },
            "required": ["path"]
        }
    )
```

---

## 6. 端云协同策略

### 6.1 决策逻辑

```python
def select_llm_endpoint(intent: str) -> str:
    """
    根据任务复杂度选择 LLM 端点
    """
    simple_keywords = ['时间', '日期', '当前', '查看', '列出']
    complex_keywords = ['分析', '比较', '推荐', '规划', '设计']
    
    if any(kw in intent for kw in simple_keywords):
        return "local"  # 使用 Ollama 本地模型
    
    if any(kw in intent for kw in complex_keywords):
        return "cloud"  # 使用云端 GPT-4
    
    return "auto"  # 根据情况自动选择
```

### 6.2 资源考虑

| 场景 | 模型选择 | 原因 |
|------|---------|------|
| K1 边缘设备 | Ollama (Llama3) | 资源受限，需本地处理 |
| 隐私敏感操作 | Ollama (Llama3) | 数据不出设备 |
| 复杂推理任务 | GPT-4o-mini | 强大的推理能力 |
| 快速简单查询 | Ollama (Llama3) | 低延迟 |
| API 不可用 | Claude-3-Haiku | 容错备份 |

---

## 7. 成本考虑

### 7.1 API 调用成本

| 模型 | 输入成本 | 输出成本 | 适用场景 |
|------|---------|---------|---------|
| GPT-4o-mini | $0.15/1M tokens | $0.60/1M tokens | 主要推理 |
| Claude-3-Haiku | $0.25/1M tokens | $1.25/1M tokens | 备选方案 |

### 7.2 优化策略

1. **缓存常用查询**：简单系统查询结果缓存
2. **本地优先**：简单任务使用 Ollama
3. **批量处理**：合并多个相似请求
4. **令牌优化**：精简提示词，避免冗余

---

## 8. 负责任的 AI 使用

### 8.1 安全措施

- 所有 LLM 生成的工具调用都经过 Security Manager 审核
- 高危操作需要用户明确确认
- 完整的审计日志记录所有交互
- 禁止 LLM 直接执行危险命令

### 8.2 局限性声明

LLM 作为系统内核存在以下局限性：

1. **幻觉问题**：LLM 可能生成不准确的信息
2. **延迟问题**：云端 API 调用有网络延迟
3. **可用性问题**：依赖外部 API 服务
4. **上下文限制**：单次对话有令牌上限

---

## 9. 未来规划

### 9.1 模型升级

- 支持更多 LLM 提供商（Google Gemini, Cohere, 等）
- 微调专属模型适应系统操作场景
- 探索多模态模型（视觉理解）

### 9.2 边缘优化

- 针对 K1 RISC-V 架构优化模型推理
- 探索模型量化技术降低资源占用
- 实现模型动态切换

---

## 10. 声明签署

| 项目 | 信息 |
|------|------|
| 项目名称 | Bianbu LLM OS |
| 版本 | v1.0.0 |
| 声明日期 | 2026-03-19 |
| 维护团队 | Bianbu LLM OS Team |

---

*本声明将随项目发展持续更新。*
