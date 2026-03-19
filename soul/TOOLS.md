# Bianbu LLM OS 工具注册表

## TOOLS.md - System Tools Registry

---

## 1. 工具注册表概述

本文档是 Bianbu LLM OS 的完整工具注册表，定义了所有可供智能体调用的系统工具。

---

## 2. 工具分类总览

| 类别 | 工具数量 | 风险范围 |
|------|---------|---------|
| 文件操作 (file_ops) | 5 | NORMAL - ELEVATED |
| 进程管理 (process_ops) | 3 | NORMAL - CRITICAL |
| 网络监控 (network_ops) | 3 | TRUSTED - NORMAL |
| 包管理 (package_ops) | 4 | ELEVATED - CRITICAL |
| 系统信息 (system_info) | 3 | TRUSTED - NORMAL |
| 扩展工具 (extended) | 3 | NORMAL - CRITICAL |

---

## 3. 文件操作工具 (file_ops)

### 3.1 file_read

```yaml
tool:
  name: "file_read"
  category: "file_ops"
  description: "读取文件内容。支持指定行数范围，适合读取大文件的局部内容。"
  
  parameters:
    path:
      type: "string"
      required: true
      description: "文件的完整路径"
    start_line:
      type: "integer"
      required: false
      default: 1
      description: "起始行号，从1开始计数"
    max_lines:
      type: "integer"
      required: false
      default: 100
      description: "最多读取的行数"
  
  returns:
    type: "object"
    properties:
      path: "string"
      total_lines: "integer"
      content: "string"
      truncated: "boolean"
  
  risk_level: "NORMAL"
  examples:
    - "读取配置文件: path=/etc/config.yaml"
    - "读取日志前100行: path=/var/log/syslog, max_lines=100"
```

### 3.2 file_write

```yaml
tool:
  name: "file_write"
  category: "file_ops"
  description: "写入内容到文件。如果文件存在则覆盖，不存在则创建。"
  
  parameters:
    path:
      type: "string"
      required: true
      description: "目标文件路径"
    content:
      type: "string"
      required: true
      description: "写入的内容"
    append:
      type: "boolean"
      required: false
      default: false
      description: "是否使用追加模式"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      path: "string"
      bytes_written: "integer"
  
  risk_level: "ELEVATED"
  protection:
    blocked_paths:
      - "/etc/passwd"
      - "/etc/shadow"
      - "/etc/sudoers"
      - "/bin/*"
      - "/sbin/*"
```

### 3.3 file_search

```yaml
tool:
  name: "file_search"
  category: "file_ops"
  description: "搜索文件。支持按名称模式、修改时间、大小等条件搜索。"
  
  parameters:
    directory:
      type: "string"
      required: false
      default: "."
      description: "搜索的起始目录"
    pattern:
      type: "string"
      required: false
      default: "*"
      description: "文件名匹配模式，支持*和?通配符"
    name_contains:
      type: "string"
      required: false
      description: "文件名包含的字符串（不区分大小写）"
    max_results:
      type: "integer"
      required: false
      default: 50
      description: "最大返回结果数"
  
  returns:
    type: "object"
    properties:
      directory: "string"
      pattern: "string"
      total_found: "integer"
      results:
        type: "array"
        items:
          - path: "string"
            name: "string"
            size: "integer"
            modified: "string"
  
  risk_level: "NORMAL"
```

### 3.4 file_list

```yaml
tool:
  name: "file_list"
  category: "file_ops"
  description: "列出指定目录的内容。"
  
  parameters:
    path:
      type: "string"
      required: false
      default: "."
      description: "目录路径"
    show_hidden:
      type: "boolean"
      required: false
      default: false
      description: "是否显示隐藏文件"
  
  returns:
    type: "object"
    properties:
      path: "string"
      total: "integer"
      entries:
        type: "array"
        items:
          - name: "string"
            type: "string"  # "file" or "directory"
            size: "integer"
            modified: "string"
  
  risk_level: "NORMAL"
```

### 3.5 file_info

```yaml
tool:
  name: "file_info"
  category: "file_ops"
  description: "获取文件的详细信息。"
  
  parameters:
    path:
      type: "string"
      required: true
      description: "文件路径"
  
  returns:
    type: "object"
    properties:
      path: "string"
      name: "string"
      type: "string"
      size: "integer"
      size_readable: "string"
      permissions: "string"
      owner: "integer"
      group: "integer"
      created: "string"
      modified: "string"
      accessed: "string"
  
  risk_level: "NORMAL"
```

---

## 4. 进程管理工具 (process_ops)

### 4.1 process_list

```yaml
tool:
  name: "process_list"
  category: "process_ops"
  description: "列出正在运行的进程。"
  
  parameters:
    user:
      type: "string"
      required: false
      description: "过滤指定用户的进程"
    max_results:
      type: "integer"
      required: false
      default: 20
      description: "最大返回结果数"
  
  returns:
    type: "object"
    properties:
      total: "integer"
      showing: "integer"
      processes:
        type: "array"
        items:
          - pid: "integer"
            name: "string"
            user: "string"
            cpu_percent: "float"
            memory_percent: "float"
            status: "string"
  
  risk_level: "NORMAL"
```

### 4.2 process_info

```yaml
tool:
  name: "process_info"
  category: "process_ops"
  description: "获取指定进程的详细信息。"
  
  parameters:
    pid:
      type: "integer"
      required: true
      description: "进程ID"
  
  returns:
    type: "object"
    properties:
      pid: "integer"
      name: "string"
      status: "string"
      user: "string"
      cpu_percent: "float"
      memory_percent: "float"
      num_threads: "integer"
      create_time: "string"
      command: "string"
  
  risk_level: "NORMAL"
```

### 4.3 process_kill

```yaml
tool:
  name: "process_kill"
  category: "process_ops"
  description: "终止指定的进程。此操作需要用户确认。"
  
  parameters:
    pid:
      type: "integer"
      required: true
      description: "要终止的进程ID"
    force:
      type: "boolean"
      required: false
      default: false
      description: "是否使用SIGKILL强制终止"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      pid: "integer"
      signal: "string"
      message: "string"
  
  risk_level: "CRITICAL"
  requires_confirmation: true
```

---

## 5. 网络监控工具 (network_ops)

### 5.1 network_info

```yaml
tool:
  name: "network_info"
  category: "network_ops"
  description: "获取网络配置信息，包括所有网络接口的地址、状态等。"
  
  parameters:
    interface:
      type: "string"
      required: false
      description: "指定网络接口名称（如eth0），不指定则返回所有接口"
  
  returns:
    type: "object"
    properties:
      interfaces:
        type: "object"
        description: "网络接口字典"
      total_interfaces: "integer"
  
  risk_level: "TRUSTED"
```

### 5.2 network_ping

```yaml
tool:
  name: "network_ping"
  category: "network_ops"
  description: "执行 ping 测试，检测主机连通性。"
  
  parameters:
    host:
      type: "string"
      required: true
      description: "目标主机名或IP地址"
    count:
      type: "integer"
      required: false
      default: 4
      description: "ping 的次数"
    timeout:
      type: "integer"
      required: false
      default: 5
      description: "超时时间（秒）"
  
  returns:
    type: "object"
    properties:
      host: "string"
      transmitted: "integer"
      received: "integer"
      loss_rate: "string"
      reachable: "boolean"
  
  risk_level: "TRUSTED"
```

### 5.3 network_connections

```yaml
tool:
  name: "network_connections"
  category: "network_ops"
  description: "获取当前的网络连接列表。"
  
  parameters:
    kind:
      type: "string"
      required: false
      default: "inet"
      description: "连接类型（inet, inet6, all）"
    max_results:
      type: "integer"
      required: false
      default: 50
      description: "最大返回结果数"
  
  returns:
    type: "object"
    properties:
      total: "integer"
      connections:
        type: "array"
        items:
          - family: "string"
            type: "string"
            local_address: "string"
            remote_address: "string"
            status: "string"
            pid: "integer"
  
  risk_level: "NORMAL"
```

---

## 6. 包管理工具 (package_ops)

### 6.1 package_search

```yaml
tool:
  name: "package_search"
  category: "package_ops"
  description: "搜索可安装的软件包。"
  
  parameters:
    query:
      type: "string"
      required: true
      description: "搜索关键词"
    max_results:
      type: "integer"
      required: false
      default: 10
      description: "最大返回结果数"
  
  returns:
    type: "object"
    properties:
      query: "string"
      total_found: "integer"
      showing: "integer"
      packages:
        type: "array"
        items:
          - name: "string"
            description: "string"
  
  risk_level: "TRUSTED"
```

### 6.2 package_install

```yaml
tool:
  name: "package_install"
  category: "package_ops"
  description: "安装指定的软件包。"
  
  parameters:
    package:
      type: "string"
      required: true
      description: "软件包名称"
    update_cache:
      type: "boolean"
      required: false
      default: true
      description: "安装前是否更新包缓存"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      package: "string"
      message: "string"
  
  risk_level: "ELEVATED"
```

### 6.3 package_remove

```yaml
tool:
  name: "package_remove"
  category: "package_ops"
  description: "卸载指定的软件包。此操作需要用户确认。"
  
  parameters:
    package:
      type: "string"
      required: true
      description: "软件包名称"
    purge:
      type: "boolean"
      required: false
      default: false
      description: "是否同时清除配置文件"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      package: "string"
      purged: "boolean"
      message: "string"
  
  risk_level: "CRITICAL"
  requires_confirmation: true
  protected_packages:
    - "apt"
    - "dpkg"
    - "python3"
    - "systemd"
    - "bash"
```

### 6.4 package_list

```yaml
tool:
  name: "package_list"
  category: "package_ops"
  description: "列出已安装的软件包。"
  
  parameters:
    filter:
      type: "string"
      required: false
      description: "过滤关键词"
    max_results:
      type: "integer"
      required: false
      default: 50
      description: "最大返回结果数"
  
  returns:
    type: "object"
    properties:
      total_shown: "integer"
      filter: "string"
      packages:
        type: "array"
        items:
          - name: "string"
            version: "string"
            description: "string"
  
  risk_level: "NORMAL"
```

---

## 7. 系统信息工具 (system_info)

### 7.1 system_info

```yaml
tool:
  name: "system_info"
  category: "system_info"
  description: "获取系统详细信息。"
  
  parameters: {}
  
  returns:
    type: "object"
    properties:
      platform: "string"
      platform_release: "string"
      platform_version: "string"
      architecture: "string"
      processor: "string"
      python_version: "string"
      hostname: "string"
      boot_time: "string"
      uptime_seconds: "integer"
      cpu_count: "integer"
      total_memory_gb: "float"
  
  risk_level: "TRUSTED"
```

### 7.2 disk_usage

```yaml
tool:
  name: "disk_usage"
  category: "system_info"
  description: "获取磁盘使用情况。"
  
  parameters:
    path:
      type: "string"
      required: false
      default: "/"
      description: "要查询的路径"
  
  returns:
    type: "object"
    properties:
      path: "string"
      total_gb: "float"
      used_gb: "float"
      free_gb: "float"
      percent: "float"
  
  risk_level: "NORMAL"
```

### 7.3 memory_usage

```yaml
tool:
  name: "memory_usage"
  category: "system_info"
  description: "获取内存使用情况。"
  
  parameters: {}
  
  returns:
    type: "object"
    properties:
      total_gb: "float"
      available_gb: "float"
      used_gb: "float"
      percent: "float"
      swap:
        type: "object"
        properties:
          total_gb: "float"
          used_gb: "float"
          percent: "float"
  
  risk_level: "NORMAL"
```

---

## 8. 扩展工具 (extended)

### 8.1 web_search

```yaml
tool:
  name: "web_search"
  category: "extended"
  description: "在互联网上搜索信息。"
  
  parameters:
    query:
      type: "string"
      required: true
      description: "搜索查询"
    max_results:
      type: "integer"
      required: false
      default: 5
      description: "最大结果数"
  
  returns:
    type: "object"
    properties:
      query: "string"
      results:
        type: "array"
        items:
          - title: "string"
            url: "string"
            snippet: "string"
  
  risk_level: "NORMAL"
  requires_network: true
```

### 8.2 cli_execute

```yaml
tool:
  name: "cli_execute"
  category: "extended"
  description: "执行 Shell 命令。"
  
  parameters:
    command:
      type: "string"
      required: true
      description: "要执行的命令"
    timeout:
      type: "integer"
      required: false
      default: 30
      description: "超时时间（秒）"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      stdout: "string"
      stderr: "string"
      return_code: "integer"
  
  risk_level: "CRITICAL"
  requires_confirmation: true
  blocked_commands:
    - "rm -rf /"
    - "dd if=.*of=/dev/"
    - "mkfs"
    - ":(){ :|:& };:"  # Fork bomb
```

### 8.3 calculator

```yaml
tool:
  name: "calculator"
  category: "extended"
  description: "执行数学计算。"
  
  parameters:
    expression:
      type: "string"
      required: true
      description: "数学表达式"
  
  returns:
    type: "object"
    properties:
      expression: "string"
      result: "float"
      success: "boolean"
  
  risk_level: "TRUSTED"
```

---

## 9. 工具版本管理

### 9.1 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-19 | 初始版本，包含17个基础工具 |
| 1.1.0 | 计划中 | 添加 web_search, cli_execute |

### 9.2 工具注册接口

```python
class ToolRegistry:
    """工具注册表"""
    
    def register(self, tool: ToolDefinition) -> bool:
        """注册新工具"""
        
    def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        
    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        """列出工具"""
        
    def validate_call(self, tool_name: str, params: Dict) -> Tuple[bool, str]:
        """验证工具调用参数"""
```

---

*最后更新: 2026-03-19*
