#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - Nexa 智能体编程语言运行时
Nexa Agent Programming Language Runtime

功能：
- Nexa 脚本加载和编译
- 工作流定义和执行
- 协议定义 (protocol/implements)
- 多智能体协作

设计理念：
Nexa 是一门为大语言模型和智能体系统设计的智能体原生编程语言，
通过底层的 Transpiler 转换为 Python Runtime。

参考：https://github.com/ouyangyipeng/Nexa

Author: Bianbu LLM OS Team
"""

import os
import re
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NexaRuntime')


class NexaNodeType(Enum):
    """Nexa 节点类型"""
    AGENT = "agent"
    PROTOCOL = "protocol"
    WORKFLOW = "workflow"
    TOOL = "tool"


@dataclass
class NexaProtocol:
    """Nexa 协议定义"""
    name: str
    fields: Dict[str, str]  # field_name: type
    description: str = ""


@dataclass
class NexaAgent:
    """Nexa 智能体定义"""
    name: str
    protocol: Optional[str]
    model: Optional[str]
    prompt: str
    tools: List[str]
    description: str = ""


@dataclass
class NexaWorkflow:
    """Nexa 工作流定义"""
    name: str
    agents: List[str]
    connections: List[Tuple[str, str]]  # (from, to)
    description: str = ""


class NexaParser:
    """
    Nexa 脚本解析器
    
    支持的语法：
    - protocol 定义
    - agent 定义
    - uses 语句
    - model 指定
    """
    
    # 关键字
    KEYWORDS = ['protocol', 'agent', 'uses', 'model', 'prompt', 'implements', 'match', 'intent', 'join', 'loop']
    
    def __init__(self):
        self.protocols: Dict[str, NexaProtocol] = {}
        self.agents: Dict[str, NexaAgent] = {}
        self.workflows: Dict[str, NexaWorkflow] = {}
    
    def parse(self, nexa_script: str) -> bool:
        """
        解析 Nexa 脚本
        
        Args:
            nexa_script: Nexa 脚本内容
            
        Returns:
            bool: 是否解析成功
        """
        try:
            lines = nexa_script.split('\n')
            current_block = None
            current_block_type = None
            block_content = []
            block_indent = 0
            
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 跳过空行和注释
                if not stripped or stripped.startswith('#'):
                    continue
                
                # 检测块开始
                if ' protocol ' in stripped and '{' in stripped:
                    current_block_type = 'protocol'
                    match = re.search(r'protocol\s+(\w+)\s*\{', stripped)
                    if match:
                        current_block = match.group(1)
                        block_indent = len(line) - len(line.lstrip())
                        block_content = []
                    continue
                
                elif ' agent ' in stripped and '{' in stripped:
                    current_block_type = 'agent'
                    match = re.search(r'agent\s+(\w+)(?:\s+implements\s+(\w+))?\s*\{', stripped)
                    if match:
                        current_block = match.group(1)
                        self.agents[current_block] = NexaAgent(
                            name=current_block,
                            protocol=match.group(2),
                            model=None,
                            prompt="",
                            tools=[]
                        )
                        block_indent = len(line) - len(line.lstrip())
                        block_content = []
                    continue
                
                # 检测块结束
                if stripped == '}' and current_block:
                    if current_block_type == 'protocol':
                        self._finalize_protocol(current_block, block_content)
                    elif current_block_type == 'agent':
                        self._finalize_agent(current_block, block_content)
                    
                    current_block = None
                    current_block_type = None
                    block_content = []
                    continue
                
                # 收集块内容
                if current_block and current_block_type:
                    block_content.append(stripped)
            
            return True
            
        except Exception as e:
            logger.error(f"Nexa 脚本解析失败: {e}")
            return False
    
    def _finalize_protocol(self, name: str, content: List[str]):
        """完成协议定义"""
        fields = {}
        for line in content:
            match = re.match(r'(\w+):\s*"(\w+)"', line)
            if match:
                fields[match.group(1)] = match.group(2)
        
        self.protocols[name] = NexaProtocol(name=name, fields=fields)
    
    def _finalize_agent(self, name: str, content: List[str]):
        """完成智能体定义"""
        agent = self.agents.get(name)
        if not agent:
            return
        
        # 解析行内属性
        current_prompt_lines = []
        
        for line in content:
            # model 指定
            if line.startswith('model:'):
                agent.model = line.split(':', 1)[1].strip().strip('"')
            
            # uses 语句
            elif line.startswith('uses ['):
                match = re.search(r'uses\s+\[(.*?)\]', line)
                if match:
                    tools_str = match.group(1)
                    agent.tools = [t.strip() for t in tools_str.split(',')]
            
            # prompt 开始
            elif line.startswith('prompt:'):
                prompt_content = line.split('prompt:', 1)[1].strip().strip('"')
                if prompt_content:
                    current_prompt_lines.append(prompt_content)
            
            # 多行 prompt
            elif current_prompt_lines and line.strip() and not line.startswith('model') and not line.startswith('uses'):
                current_prompt_lines.append(line.strip().strip('"'))
        
        agent.prompt = ' '.join(current_prompt_lines)


class NexaRuntime:
    """
    Nexa 运行时
    
    提供 Nexa 脚本的加载、编译和执行功能。
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.parser = NexaParser()
        self.compiled_workflows: Dict[str, Any] = {}
        self.agent_instances: Dict[str, Any] = {}
        
        # 检查 Nexa CLI 是否可用
        self.nexa_available = self._check_nexa()
        
        logger.info(f"NexaRuntime 初始化完成，Nexa CLI 可用: {self.nexa_available}")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except:
                pass
        return {}
    
    def _check_nexa(self) -> bool:
        """检查 Nexa CLI 是否安装"""
        try:
            result = subprocess.run(['nexa', '--version'],
                                 capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def load_protocol_file(self, protocol_file: str) -> bool:
        """
        加载协议定义文件
        
        Args:
            protocol_file: 协议文件路径
            
        Returns:
            bool: 是否加载成功
        """
        if not os.path.exists(protocol_file):
            logger.error(f"协议文件不存在: {protocol_file}")
            return False
        
        try:
            with open(protocol_file, 'r') as f:
                content = f.read()
            
            return self.parser.parse(content)
            
        except Exception as e:
            logger.error(f"加载协议文件失败: {e}")
            return False
    
    def load_nexa_script(self, script: str) -> bool:
        """
        加载 Nexa 脚本
        
        Args:
            script: Nexa 脚本内容或文件路径
            
        Returns:
            bool: 是否加载成功
        """
        # 如果是文件路径
        if os.path.exists(script):
            return self.load_protocol_file(script)
        
        # 如果是脚本内容
        return self.parser.parse(script)
    
    def compile_workflow(self, workflow_name: str, nexa_script: str = None) -> Optional[str]:
        """
        编译 Nexa 工作流为 Python 代码
        
        Args:
            workflow_name: 工作流名称
            nexa_script: 可选的 Nexa 脚本
            
        Returns:
            str: 编译后的 Python 代码，如果失败返回 None
        """
        try:
            # 如果提供了脚本，先加载
            if nexa_script:
                if not self.load_nexa_script(nexa_script):
                    return None
            
            # 如果 Nexa CLI 可用，使用它编译
            if self.nexa_available and nexa_script and os.path.exists(nexa_script):
                result = subprocess.run(
                    ['nexa', 'build', nexa_script],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    # 假设输出在同名的 .py 文件中
                    py_file = nexa_script.replace('.nx', '.py').replace('.nexa', '.py')
                    if os.path.exists(py_file):
                        with open(py_file, 'r') as f:
                            return f.read()
            
            # 否则，生成 Python 代码
            return self._generate_python_workflow(workflow_name)
            
        except Exception as e:
            logger.error(f"编译工作流失败: {e}")
            return None
    
    def _generate_python_workflow(self, workflow_name: str) -> str:
        """生成 Python 工作流代码"""
        agents = self.parser.agents
        
        if not agents:
            return "# No agents defined"
        
        # 生成 Agent 类
        py_code = f'''"""
Nexa Workflow: {workflow_name}
自动生成代码
"""

from typing import Dict, Any, List

class {workflow_name}Workflow:
    """Nexa 工作流自动生成的执行器"""
    
    def __init__(self, agent_daemon):
        self.agent = agent_daemon
        self.agents = {json.dumps({k: v.name for k, v in agents.items()})}
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        results = {{}}
        
        # 执行顺序可以通过 Nexa 脚本中的连接定义确定
'''
        
        # 为每个 agent 生成执行代码
        for name, agent in agents.items():
            py_code += f'''
        # Agent: {name}
        if "{name}" in context.get("enabled_agents", self.agents.keys()):
            try:
                results["{name}"] = self.agent.process_intent(
                    "{agent.prompt or f"Execute {name} task"}",
                    session_id=context.get("session_id")
                )
            except Exception as e:
                results["{name}"] = {{"error": str(e)}}
'''
        
        py_code += '''
        return results
'''
        
        return py_code
    
    def execute_workflow(self, workflow_name: str, context: Dict[str, Any],
                        agent_daemon=None) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_name: 工作流名称
            context: 执行上下文
            agent_daemon: AgentDaemon 实例
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 编译工作流
        py_code = self.compile_workflow(workflow_name)
        if not py_code:
            return {"error": "工作流编译失败"}
        
        try:
            # 在临时命名空间中执行代码
            namespace = {'agent_daemon': agent_daemon}
            exec(py_code, namespace)
            
            # 创建工作流实例
            workflow_class = namespace.get(f"{workflow_name}Workflow")
            if not workflow_class:
                return {"error": "工作流类未找到"}
            
            workflow = workflow_class(agent_daemon)
            return workflow.execute(context)
            
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            return {"error": str(e)}
    
    def get_defined_protocols(self) -> List[str]:
        """获取定义的协议列表"""
        return list(self.parser.protocols.keys())
    
    def get_defined_agents(self) -> List[str]:
        """获取定义的智能体列表"""
        return list(self.parser.agents.keys())
    
    def get_protocol_definition(self, name: str) -> Optional[NexaProtocol]:
        """获取协议定义"""
        return self.parser.protocols.get(name)
    
    def get_agent_definition(self, name: str) -> Optional[NexaAgent]:
        """获取智能体定义"""
        return self.parser.agents.get(name)


def create_nexa_runtime(config_path: str = "config.yaml") -> NexaRuntime:
    """创建 Nexa 运行时实例"""
    return NexaRuntime(config_path)


# 示例 Nexa 脚本
EXAMPLE_NEXA_SCRIPT = '''
# 示例 Nexa 工作流脚本

protocol TaskResult {
    status: "string"
    output: "any"
    error: "string"
}

agent Router implements TaskResult {
    model: "gpt-4o-mini"
    uses [file_ops, process_ops, network_ops]
    prompt: "路由任务到合适的子智能体"
}

agent FileHandler {
    model: "gpt-4o-mini"
    uses [file_read, file_write, file_search]
    prompt: "处理文件相关任务"
}

agent NetworkHandler {
    uses [network_info, network_ping]
    prompt: "处理网络相关任务"
}
'''


if __name__ == '__main__':
    # 演示用法
    print("=== NexaRuntime 演示 ===\n")
    
    runtime = NexaRuntime()
    
    # 加载示例脚本
    print("1. 加载 Nexa 脚本...")
    success = runtime.load_nexa_script(EXAMPLE_NEXA_SCRIPT)
    print(f"   加载结果: {'成功' if success else '失败'}")
    
    # 获取定义的智能体
    print("\n2. 定义的智能体:")
    for agent_name in runtime.get_defined_agents():
        agent = runtime.get_agent_definition(agent_name)
        print(f"   - {agent_name} (protocol: {agent.protocol}, model: {agent.model})")
    
    # 获取定义的协议
    print("\n3. 定义的协议:")
    for protocol_name in runtime.get_defined_protocols():
        proto = runtime.get_protocol_definition(protocol_name)
        print(f"   - {protocol_name}: {proto.fields}")
    
    # 编译工作流
    print("\n4. 编译工作流...")
    py_code = runtime.compile_workflow("DemoWorkflow", EXAMPLE_NEXA_SCRIPT)
    if py_code:
        print("   编译成功，生成了 Python 代码")
        print(f"   代码长度: {len(py_code)} 字符")
    
    print("\n=== 演示完成 ===")
