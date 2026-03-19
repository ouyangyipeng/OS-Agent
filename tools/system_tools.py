#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 系统工具抽象层
System Tools Abstraction Layer

功能：
- 文件操作工具 (读、写、搜索)
- 进程管理工具 (查看状态、杀进程)
- 网络监控工具 (获取IP、ping)
- 包管理工具 (apt-get封装)
- OpenAI Function Calling 格式

Author: Bianbu LLM OS Team
"""

import os
import re
import json
import sqlite3
import hashlib
import datetime
import subprocess
import shlex
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SystemTools')


class ToolCategory(Enum):
    """工具类别"""
    FILE_OPS = "file_ops"
    PROCESS_OPS = "process_ops"
    NETWORK_OPS = "network_ops"
    PACKAGE_OPS = "package_ops"
    SYSTEM_INFO = "system_info"
    WEB_SEARCH = "web_search"


@dataclass
class ToolDefinition:
    """工具定义 (OpenAI Function Calling 格式)"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: ToolCategory
    func: Callable = field(default=None)
    
    def to_openai_format(self) -> Dict:
        """转换为 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str = ""


class SystemTools:
    """
    系统工具抽象层
    
    提供标准化的工具函数，支持 OpenAI Function Calling 格式
    """
    
    def __init__(self, security_manager=None):
        """初始化系统工具"""
        self.security_manager = security_manager
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_all_tools()
        logger.info(f"SystemTools 初始化完成，共注册 {len(self.tools)} 个工具")
    
    def _register_all_tools(self):
        """注册所有工具"""
        # 文件操作工具
        self._register_tool(self._file_read_tool())
        self._register_tool(self._file_write_tool())
        self._register_tool(self._file_search_tool())
        self._register_tool(self._file_list_tool())
        self._register_tool(self._file_info_tool())
        
        # 进程管理工具
        self._register_tool(self._process_list_tool())
        self._register_tool(self._process_info_tool())
        self._register_tool(self._process_kill_tool())
        
        # 网络监控工具
        self._register_tool(self._network_info_tool())
        self._register_tool(self._network_ping_tool())
        self._register_tool(self._network_connections_tool())
        
        # 包管理工具
        self._register_tool(self._package_search_tool())
        self._register_tool(self._package_install_tool())
        self._register_tool(self._package_remove_tool())
        self._register_tool(self._package_list_tool())
        
        # 系统信息工具
        self._register_tool(self._system_info_tool())
        self._register_tool(self._disk_usage_tool())
        self._register_tool(self._memory_usage_tool())
    
    def _register_tool(self, tool: ToolDefinition):
        """注册单个工具"""
        self.tools[tool.name] = tool
    
    def get_tools(self) -> List[Dict]:
        """获取所有工具定义 (OpenAI 格式)"""
        return [tool.to_openai_format() for tool in self.tools.values()]
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取指定工具"""
        return self.tools.get(name)
    
    def execute_tool(self, tool_name: str, parameters: Dict) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        import time
        start_time = time.time()
        
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"工具不存在: {tool_name}",
                execution_time=time.time() - start_time,
                tool_name=tool_name
            )
        
        # 安全检查
        if self.security_manager:
            allowed, msg = self.security_manager.check_operation(tool_name, parameters)
            if not allowed:
                return ToolResult(
                    success=False,
                    result=None,
                    error=msg,
                    execution_time=time.time() - start_time,
                    tool_name=tool_name
                )
        
        # 执行工具
        try:
            result = tool.func(parameters)
            return ToolResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time,
                tool_name=tool_name
            )
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name} - {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start_time,
                tool_name=tool_name
            )
    
    # =========================================================================
    # 文件操作工具
    # =========================================================================
    
    def _file_read_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_read",
            description="读取文件内容。安全读取文本文件，支持指定行数范围。",
            category=ToolCategory.FILE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "起始行号 (从1开始)",
                        "default": 1
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "最大读取行数",
                        "default": 100
                    }
                },
                "required": ["path"]
            },
            func=self._file_read
        )
    
    def _file_read(self, params: Dict) -> Dict:
        """读取文件"""
        path = params['path']
        start_line = params.get('start_line', 1)
        max_lines = params.get('max_lines', 100)
        
        # 安全检查：禁止读取敏感文件
        sensitive_patterns = ['/etc/sudoers', '/etc/shadow', '/root/.ssh/']
        for pattern in sensitive_patterns:
            if path.startswith(pattern):
                return {"error": f"禁止读取敏感文件: {path}"}
        
        if not os.path.exists(path):
            return {"error": f"文件不存在: {path}"}
        
        if not os.path.isfile(path):
            return {"error": f"不是文件: {path}"}
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            content = lines[start_line - 1:start_line - 1 + max_lines]
            
            return {
                "path": path,
                "total_lines": total_lines,
                "start_line": start_line,
                "max_lines": max_lines,
                "content": ''.join(content),
                "truncated": total_lines > max_lines
            }
        except Exception as e:
            return {"error": f"读取失败: {str(e)}"}
    
    def _file_write_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_write",
            description="写入内容到文件。如果文件存在则覆盖，不存在则创建。",
            category=ToolCategory.FILE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "写入内容"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "是否追加模式",
                        "default": False
                    }
                },
                "required": ["path", "content"]
            },
            func=self._file_write
        )
    
    def _file_write(self, params: Dict) -> Dict:
        """写入文件"""
        path = params['path']
        content = params['content']
        append = params.get('append', False)
        
        # 安全检查：禁止写入系统关键文件
        protected_patterns = ['/etc/passwd', '/etc/shadow', '/etc/sudoers', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/']
        for pattern in protected_patterns:
            if path.startswith(pattern):
                return {"error": f"禁止写入受保护文件: {path}"}
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content.encode('utf-8')),
                "mode": "append" if append else "write"
            }
        except Exception as e:
            return {"error": f"写入失败: {str(e)}"}
    
    def _file_search_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_search",
            description="搜索文件。支持按名称模式、修改时间、大小等条件搜索。",
            category=ToolCategory.FILE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "搜索目录",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件名模式 (支持 * 和 ? 通配符)",
                        "default": "*"
                    },
                    "name_contains": {
                        "type": "string",
                        "description": "文件名包含的字符串"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回结果数",
                        "default": 50
                    }
                }
            },
            func=self._file_search
        )
    
    def _file_search(self, params: Dict) -> Dict:
        """搜索文件"""
        directory = params.get('directory', '.')
        pattern = params.get('pattern', '*')
        name_contains = params.get('name_contains')
        max_results = params.get('max_results', 50)
        
        if not os.path.exists(directory):
            return {"error": f"目录不存在: {directory}"}
        
        results = []
        try:
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和系统目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
                
                for filename in files:
                    if filename.startswith('.'):
                        continue
                    
                    # 名称匹配
                    import fnmatch
                    if not fnmatch.fnmatch(filename, pattern):
                        continue
                    
                    if name_contains and name_contains.lower() not in filename.lower():
                        continue
                    
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        results.append({
                            "path": filepath,
                            "name": filename,
                            "size": stat.st_size,
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except:
                        continue
                    
                    if len(results) >= max_results:
                        break
                
                if len(results) >= max_results:
                    break
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}"}
        
        return {
            "directory": directory,
            "pattern": pattern,
            "total_found": len(results),
            "results": results
        }
    
    def _file_list_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_list",
            description="列出目录内容",
            category=ToolCategory.FILE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": "."
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "显示隐藏文件",
                        "default": False
                    }
                }
            },
            func=self._file_list
        )
    
    def _file_list(self, params: Dict) -> Dict:
        """列出目录"""
        path = params.get('path', '.')
        show_hidden = params.get('show_hidden', False)
        
        if not os.path.exists(path):
            return {"error": f"目录不存在: {path}"}
        
        if not os.path.isdir(path):
            return {"error": f"不是目录: {path}"}
        
        try:
            entries = []
            for entry in os.listdir(path):
                if not show_hidden and entry.startswith('.'):
                    continue
                
                full_path = os.path.join(path, entry)
                try:
                    stat = os.stat(full_path)
                    entries.append({
                        "name": entry,
                        "type": "directory" if os.path.isdir(full_path) else "file",
                        "size": stat.st_size,
                        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except:
                    continue
            
            return {
                "path": path,
                "total": len(entries),
                "entries": sorted(entries, key=lambda x: (x['type'] != 'directory', x['name']))
            }
        except Exception as e:
            return {"error": f"列出目录失败: {str(e)}"}
    
    def _file_info_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_info",
            description="获取文件详细信息",
            category=ToolCategory.FILE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["path"]
            },
            func=self._file_info
        )
    
    def _file_info(self, params: Dict) -> Dict:
        """获取文件信息"""
        path = params['path']
        
        if not os.path.exists(path):
            return {"error": f"文件不存在: {path}"}
        
        try:
            stat = os.stat(path)
            return {
                "path": path,
                "name": os.path.basename(path),
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "size_readable": self._format_size(stat.st_size),
                "permissions": oct(stat.st_mode)[-3:],
                "owner": stat.st_uid,
                "group": stat.st_gid,
                "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat()
            }
        except Exception as e:
            return {"error": f"获取信息失败: {str(e)}"}
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    # =========================================================================
    # 进程管理工具
    # =========================================================================
    
    def _process_list_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="process_list",
            description="列出正在运行的进程",
            category=ToolCategory.PROCESS_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "过滤指定用户的进程"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回结果数",
                        "default": 20
                    }
                }
            },
            func=self._process_list
        )
    
    def _process_list(self, params: Dict) -> Dict:
        """列出进程"""
        import psutil
        
        max_results = params.get('max_results', 20)
        user = params.get('user')
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    if user and info.get('username') != user:
                        continue
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "user": info['username'],
                        "cpu_percent": info['cpu_percent'],
                        "memory_percent": info['memory_percent'],
                        "status": info['status']
                    })
                except:
                    continue
            
            # 按 CPU 使用率排序
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return {
                "total": len(processes),
                "showing": min(len(processes), max_results),
                "processes": processes[:max_results]
            }
        except Exception as e:
            return {"error": f"列出进程失败: {str(e)}"}
    
    def _process_info_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="process_info",
            description="获取指定进程的详细信息",
            category=ToolCategory.PROCESS_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "进程ID"
                    }
                },
                "required": ["pid"]
            },
            func=self._process_info
        )
    
    def _process_info(self, params: Dict) -> Dict:
        """获取进程信息"""
        import psutil
        
        pid = params['pid']
        
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "user": proc.username(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "memory_info": proc.memory_info()._asdict(),
                "num_threads": proc.num_threads(),
                "create_time": datetime.datetime.fromtimestamp(proc.create_time()).isoformat(),
                "command": ' '.join(proc.cmdline()),
                "open_files": [f.path for f in proc.open_files()][:10],
                "connections": len(proc.connections())
            }
        except psutil.NoSuchProcess:
            return {"error": f"进程不存在: {pid}"}
        except Exception as e:
            return {"error": f"获取进程信息失败: {str(e)}"}
    
    def _process_kill_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="process_kill",
            description="终止指定进程。此操作需要确认。",
            category=ToolCategory.PROCESS_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "进程ID"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "强制终止 (SIGKILL)",
                        "default": False
                    }
                },
                "required": ["pid"]
            },
            func=self._process_kill
        )
    
    def _process_kill(self, params: Dict) -> Dict:
        """终止进程"""
        import psutil
        import signal
        
        pid = params['pid']
        force = params.get('force', False)
        
        try:
            proc = psutil.Process(pid)
            sig = signal.SIGKILL if force else signal.SIGTERM
            proc.send_signal(sig)
            
            return {
                "success": True,
                "pid": pid,
                "signal": "SIGKILL" if force else "SIGTERM",
                "message": f"进程 {pid} 已终止"
            }
        except psutil.NoSuchProcess:
            return {"error": f"进程不存在: {pid}"}
        except PermissionError:
            return {"error": f"权限不足，无法终止进程: {pid}"}
        except Exception as e:
            return {"error": f"终止进程失败: {str(e)}"}
    
    # =========================================================================
    # 网络监控工具
    # =========================================================================
    
    def _network_info_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="network_info",
            description="获取网络配置信息",
            category=ToolCategory.NETWORK_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "网络接口名称 (如 eth0, wlan0)"
                    }
                }
            },
            func=self._network_info
        )
    
    def _network_info(self, params: Dict) -> Dict:
        """获取网络信息"""
        import psutil
        
        interface = params.get('interface')
        
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            result = {}
            for iface, addr_list in addrs.items():
                if interface and iface != interface:
                    continue
                
                addr_info = {}
                for addr in addr_list:
                    addr_info[addr.family.name] = {
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    }
                
                is_up = iface in stats and stats[iface].isup
                result[iface] = {
                    "addresses": addr_info,
                    "status": "up" if is_up else "down",
                    "speed": stats[iface].speed if iface in stats else None,
                    "mtu": stats[iface].mtu if iface in stats else None
                }
            
            # 获取默认路由
            gateways = psutil.net_if_stats()
            
            return {
                "interfaces": result,
                "total_interfaces": len(result)
            }
        except Exception as e:
            return {"error": f"获取网络信息失败: {str(e)}"}
    
    def _network_ping_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="network_ping",
            description="执行 ping 测试",
            category=ToolCategory.NETWORK_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "目标主机或IP地址"
                    },
                    "count": {
                        "type": "integer",
                        "description": "ping 次数",
                        "default": 4
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间(秒)",
                        "default": 5
                    }
                },
                "required": ["host"]
            },
            func=self._network_ping
        )
    
    def _network_ping(self, params: Dict) -> Dict:
        """执行 ping"""
        host = params['host']
        count = params.get('count', 4)
        timeout = params.get('timeout', 5)
        
        try:
            cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
            
            output = result.stdout
            
            # 解析结果
            match = re.search(r'(\d+) packets transmitted, (\d+) received', output)
            if match:
                transmitted = int(match.group(1))
                received = int(match.group(2))
                loss_rate = (transmitted - received) / transmitted * 100 if transmitted > 0 else 100
                
                return {
                    "host": host,
                    "transmitted": transmitted,
                    "received": received,
                    "loss_rate": f"{loss_rate:.1f}%",
                    "reachable": received > 0,
                    "output": output[:500]
                }
            
            return {
                "host": host,
                "reachable": result.returncode == 0,
                "output": output[:500]
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Ping 超时: {host}"}
        except Exception as e:
            return {"error": f"Ping 失败: {str(e)}"}
    
    def _network_connections_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="network_connections",
            description="获取网络连接列表",
            category=ToolCategory.NETWORK_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "description": "连接类型 (inet, inet6, all)",
                        "default": "inet"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 50
                    }
                }
            },
            func=self._network_connections
        )
    
    def _network_connections(self, params: Dict) -> Dict:
        """获取网络连接"""
        import psutil
        
        kind = params.get('kind', 'inet')
        max_results = params.get('max_results', 50)
        
        try:
            connections = []
            for conn in psutil.net_connections(kind=kind)[:max_results]:
                connections.append({
                    "family": str(conn.family),
                    "type": str(conn.type),
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    "status": conn.status,
                    "pid": conn.pid
                })
            
            return {
                "total": len(connections),
                "connections": connections
            }
        except Exception as e:
            return {"error": f"获取网络连接失败: {str(e)}"}
    
    # =========================================================================
    # 包管理工具
    # =========================================================================
    
    def _package_search_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="package_search",
            description="搜索可安装的软件包",
            category=ToolCategory.PACKAGE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 10
                    }
                },
                "required": ["query"]
            },
            func=self._package_search
        )
    
    def _package_search(self, params: Dict) -> Dict:
        """搜索包"""
        query = params['query']
        max_results = params.get('max_results', 10)
        
        try:
            cmd = ['apt-cache', 'search', query]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')
            packages = []
            for line in lines[:max_results]:
                if line:
                    parts = line.split(' - ', 1)
                    if len(parts) >= 2:
                        packages.append({
                            "name": parts[0].strip(),
                            "description": parts[1].strip()
                        })
            
            return {
                "query": query,
                "total_found": len(lines),
                "showing": len(packages),
                "packages": packages
            }
        except Exception as e:
            return {"error": f"搜索包失败: {str(e)}"}
    
    def _package_install_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="package_install",
            description="安装软件包",
            category=ToolCategory.PACKAGE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "软件包名称"
                    },
                    "update_cache": {
                        "type": "boolean",
                        "description": "是否更新包缓存",
                        "default": True
                    }
                },
                "required": ["package"]
            },
            func=self._package_install
        )
    
    def _package_install(self, params: Dict) -> Dict:
        """安装包"""
        package = params['package']
        update_cache = params.get('update_cache', True)
        
        try:
            commands = []
            if updateCache:
                commands.append(['apt-get', 'update'])
            commands.append(['apt-get', 'install', '-y', package])
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return {
                        "error": f"安装失败: {result.stderr[:500]}",
                        "package": package
                    }
            
            return {
                "success": True,
                "package": package,
                "message": f"包 {package} 已安装"
            }
        except Exception as e:
            return {"error": f"安装包失败: {str(e)}"}
    
    def _package_remove_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="package_remove",
            description="卸载软件包",
            category=ToolCategory.PACKAGE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "软件包名称"
                    },
                    "purge": {
                        "type": "boolean",
                        "description": "是否清除配置",
                        "default": False
                    }
                },
                "required": ["package"]
            },
            func=self._package_remove
        )
    
    def _package_remove(self, params: Dict) -> Dict:
        """卸载包"""
        package = params['package']
        purge = params.get('purge', False)
        
        # 保护系统关键包
        protected = ['apt', 'dpkg', 'python3', 'systemd', 'bash', 'coreutils']
        if package in protected:
            return {"error": f"禁止卸载系统关键包: {package}"}
        
        try:
            cmd = ['apt-get', 'remove', '-y']
            if purge:
                cmd.append('--purge')
            cmd.append(package)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "error": f"卸载失败: {result.stderr[:500]}",
                    "package": package
                }
            
            return {
                "success": True,
                "package": package,
                "purged": purge,
                "message": f"包 {package} 已卸载"
            }
        except Exception as e:
            return {"error": f"卸载包失败: {str(e)}"}
    
    def _package_list_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="package_list",
            description="列出已安装的包",
            category=ToolCategory.PACKAGE_OPS,
            parameters={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "过滤关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 50
                    }
                }
            },
            func=self._package_list
        )
    
    def _package_list(self, params: Dict) -> Dict:
        """列出已安装的包"""
        filter_str = params.get('filter')
        max_results = params.get('max_results', 50)
        
        try:
            result = subprocess.run(['dpkg', '--list'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            
            # 跳过标题行
            packages = []
            for line in lines[5:]:
                if line.startswith('ii '):
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        name = parts[1]
                        version = parts[2]
                        desc = parts[4] if len(parts) > 4 else ''
                        
                        if filter_str and filter_str.lower() not in name.lower():
                            continue
                        
                        packages.append({
                            "name": name,
                            "version": version,
                            "description": desc
                        })
                        
                        if len(packages) >= max_results:
                            break
            
            return {
                "total_shown": len(packages),
                "filter": filter_str,
                "packages": packages
            }
        except Exception as e:
            return {"error": f"列出包失败: {str(e)}"}
    
    # =========================================================================
    # 系统信息工具
    # =========================================================================
    
    def _system_info_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="system_info",
            description="获取系统信息",
            category=ToolCategory.SYSTEM_INFO,
            parameters={
                "type": "object",
                "properties": {}
            },
            func=self._system_info
        )
    
    def _system_info(self, params: Dict) -> Dict:
        """获取系统信息"""
        import platform
        import psutil
        
        try:
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_readable": str(uptime).split('.')[0],
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            }
        except Exception as e:
            return {"error": f"获取系统信息失败: {str(e)}"}
    
    def _disk_usage_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="disk_usage",
            description="获取磁盘使用情况",
            category=ToolCategory.SYSTEM_INFO,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "路径",
                        "default": "/"
                    }
                }
            },
            func=self._disk_usage
        )
    
    def _disk_usage(self, params: Dict) -> Dict:
        """获取磁盘使用情况"""
        import psutil
        
        path = params.get('path', '/')
        
        try:
            usage = psutil.disk_usage(path)
            return {
                "path": path,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            }
        except Exception as e:
            return {"error": f"获取磁盘使用情况失败: {str(e)}"}
    
    def _memory_usage_tool(self) -> ToolDefinition:
        return ToolDefinition(
            name="memory_usage",
            description="获取内存使用情况",
            category=ToolCategory.SYSTEM_INFO,
            parameters={
                "type": "object",
                "properties": {}
            },
            func=self._memory_usage
        )
    
    def _memory_usage(self, params: Dict) -> Dict:
        """获取内存使用情况"""
        import psutil
        
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent,
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "percent": swap.percent
                }
            }
        except Exception as e:
            return {"error": f"获取内存使用情况失败: {str(e)}"}


def create_system_tools(security_manager=None) -> SystemTools:
    """创建系统工具实例"""
    return SystemTools(security_manager)


if __name__ == '__main__':
    # 演示用法
    print("=== SystemTools 演示 ===\n")
    
    tools = SystemTools()
    
    # 打印所有工具
    print(f"已注册 {len(tools.tools)} 个工具:\n")
    for name, tool in tools.tools.items():
        print(f"  - {name}: {tool.description[:50]}...")
    
    # 测试执行
    print("\n=== 测试文件搜索 ===")
    result = tools.execute_tool('file_search', {'directory': '.', 'pattern': '*.py'})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 测试系统信息 ===")
    result = tools.execute_tool('system_info', {})
    print(json.dumps(result, indent=2, ensure_ascii=False))
