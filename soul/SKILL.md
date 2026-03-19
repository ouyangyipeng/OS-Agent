# Bianbu LLM OS 技能定义

## SKILL.md - 智能体技能库

---

## 1. 技能概述

技能（Skill）是 Bianbu LLM OS 智能体能力的抽象表示，定义了智能体可以执行的操作类型、执行方式和相关参数。

---

## 2. 技能分类

### 2.1 文件管理技能 (File Management)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.file.read | 文件读取 | 读取指定路径的文件内容 | NORMAL |
| skill.file.write | 文件写入 | 创建或覆盖文件内容 | ELEVATED |
| skill.file.append | 文件追加 | 向现有文件追加内容 | NORMAL |
| skill.file.delete | 文件删除 | 删除指定的文件 | CRITICAL |
| skill.file.copy | 文件复制 | 复制文件到目标位置 | NORMAL |
| skill.file.move | 文件移动 | 移动文件到目标位置 | ELEVATED |
| skill.file.search | 文件搜索 | 根据条件搜索文件 | NORMAL |
| skill.file.info | 文件信息 | 获取文件的详细信息 | TRUSTED |
| skill.file.list | 目录列表 | 列出目录内容 | TRUSTED |

### 2.2 进程管理技能 (Process Management)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.process.list | 进程列表 | 列出所有运行中的进程 | NORMAL |
| skill.process.info | 进程信息 | 获取指定进程的详细信息 | NORMAL |
| skill.process.kill | 进程终止 | 终止指定的进程 | CRITICAL |
| skill.process.start | 进程启动 | 启动一个新的进程 | ELEVATED |
| skill.process.restart | 进程重启 | 重启指定的进程 | ELEVATED |

### 2.3 网络管理技能 (Network Management)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.network.info | 网络信息 | 获取网络配置信息 | TRUSTED |
| skill.network.ping | Ping测试 | 测试主机连通性 | TRUSTED |
| skill.network.connections | 连接列表 | 列出当前网络连接 | NORMAL |
| skill.network.scan | 端口扫描 | 扫描指定主机的端口 | ELEVATED |
| skill.network.config | 网络配置 | 修改网络配置 | CRITICAL |

### 2.4 包管理技能 (Package Management)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.package.search | 包搜索 | 搜索可用的软件包 | TRUSTED |
| skill.package.list | 包列表 | 列出已安装的包 | NORMAL |
| skill.package.install | 包安装 | 安装指定的软件包 | ELEVATED |
| skill.package.remove | 包卸载 | 卸载指定的软件包 | CRITICAL |
| skill.package.update | 包更新 | 更新已安装的包 | ELEVATED |

### 2.5 系统信息技能 (System Information)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.system.info | 系统信息 | 获取系统详细信息 | TRUSTED |
| skill.system.uptime | 运行时间 | 获取系统运行时间 | TRUSTED |
| skill.system.disk | 磁盘使用 | 获取磁盘使用情况 | NORMAL |
| skill.system.memory | 内存使用 | 获取内存使用情况 | NORMAL |
| skill.system.cpu | CPU信息 | 获取CPU使用情况 | NORMAL |
| skill.system.users | 用户列表 | 列出系统用户 | NORMAL |

### 2.6 扩展技能 (Extended Skills)

| 技能ID | 名称 | 描述 | 风险等级 |
|--------|------|------|---------|
| skill.web.search | 网页搜索 | 搜索互联网信息 | NORMAL |
| skill.web.fetch | 网页抓取 | 获取网页内容 | NORMAL |
| skill.cli.execute | CLI执行 | 执行Shell命令 | CRITICAL |
| skill.calculator | 计算器 | 执行数学计算 | TRUSTED |
| skill.date_time | 日期时间 | 获取当前日期时间 | TRUSTED |

---

## 3. 技能定义格式

### 3.1 YAML 格式

```yaml
skill:
  id: "skill.file.read"
  name: "文件读取"
  description: "读取指定路径的文件内容"
  category: "file_management"
  risk_level: "NORMAL"
  
  parameters:
    - name: "path"
      type: "string"
      required: true
      description: "文件路径"
    - name: "start_line"
      type: "integer"
      required: false
      default: 1
      description: "起始行号"
    - name: "max_lines"
      type: "integer"
      required: false
      default: 100
      description: "最大读取行数"
  
  returns:
    type: "object"
    properties:
      success: "boolean"
      content: "string"
      error: "string"
  
  examples:
    - description: "读取配置文件"
      params:
        path: "/etc/config.yaml"
    - description: "读取日志文件前100行"
      params:
        path: "/var/log/syslog"
        max_lines: 100
```

---

## 4. 技能依赖关系

### 4.1 技能图

```
skill.file.search
       │
       ├── skill.file.info (需要文件信息)
       └── skill.file.read (需要读取内容)
       
skill.process.kill
       │
       └── skill.process.info (需要先获取进程信息)
       
skill.web.search
       │
       └── skill.web.fetch (搜索后可能需要抓取页面)
```

### 4.2 依赖定义

```yaml
dependencies:
  skill.file.search:
    - skill.file.info
    - skill.file.read
    
  skill.process.kill:
    - skill.process.info
    
  skill.network.config:
    - skill.network.info
```

---

## 5. 技能学习

### 5.1 学习流程

```
用户请求 → 技能识别 → 技能加载 → 技能执行 → 结果返回
              │
              └── 未掌握 → 尝试学习 → 学习成功/失败
```

### 5.2 技能状态

| 状态 | 说明 | 行为 |
|------|------|------|
| KNOWN | 已掌握 | 直接执行 |
| LEARNING | 学习中 | 显示学习进度 |
| UNKNOWN | 未掌握 | 尝试学习或拒绝 |
| FORBIDDEN | 禁止 | 明确拒绝执行 |

---

## 6. 技能权限

### 6.1 权限矩阵

| 用户等级 | 可用技能 |
|---------|---------|
| ADMIN | 所有技能 |
| USER | 文件、网络、系统信息、计算器 |
| GUEST | 系统信息、计算器、日期时间 |
| RESTRICTED | 日期时间、计算器 |

---

## 7. 技能性能指标

| 技能 | 平均执行时间 | 成功率 | 资源消耗 |
|------|------------|--------|---------|
| skill.file.read | 50ms | 99.5% | 低 |
| skill.file.search | 200ms | 98.0% | 中 |
| skill.process.list | 100ms | 99.9% | 低 |
| skill.network.ping | 500ms | 95.0% | 低 |
| skill.web.search | 2000ms | 90.0% | 高 |

---

## 8. 技能扩展接口

### 8.1 注册新技能

```python
from core.skill_registry import SkillRegistry

registry = SkillRegistry()

@registry.register(
    id="skill.custom",
    name="自定义技能",
    category="custom",
    risk_level=PermissionLevel.NORMAL
)
def custom_skill(params):
    """自定义技能实现"""
    pass
```

### 8.2 技能中间件

```python
@registry.middleware
async def auth_middleware(skill_id, params, context):
    """权限验证中间件"""
    if not has_permission(context.user, skill_id):
        raise PermissionDenied(skill_id)
    return True
```

---

*最后更新: 2026-03-19*
