# YatAIOS 项目进度跟踪
## (Yet Another Transformative AI OS)

## 项目概述
- **项目名称**: YatAIOS - Yet Another Transformative AI OS
- **中文名称**: 融合原生AI智能体的Bianbu系统交互范式重构
- **英文名称**: Reconstructing Bianbu OS Interaction Paradigm with Native AI Agent Integration
- **目标**: 实现一个 AI 原生操作系统 (LLM OS) 原型
- **硬件平台**: 进迭时空 K1 RISC-V AI 开发平台 (MUSE BOOK)
- **基础系统**: Ubuntu 22.04 (Bianbu 系统)
- **赛道**: 2026年全国大学生计算机系统能力大赛-操作系统设计赛

---

## 总体任务清单

### 阶段一：环境初始化与信息搜集 ✅
- [x] 创建项目目录结构
- [x] `init_env.sh` - 自动环境检测和依赖安装脚本
- [x] `config.yaml` - 系统配置文件
- [ ] `PROGRESS.md` - 进度跟踪文档 (当前)
- [ ] Git 仓库初始化和初始提交

### 阶段二：核心模块实现 🚧
- [ ] `agent_daemon.py` - 智能体核心守护进程
  - LLM 推理引擎集成
  - SQLite 记忆库
  - 多智能体协调机制
- [ ] `system_tools.py` - 工具抽象层
  - 文件操作工具
  - 进程管理工具
  - 网络监控工具
  - 包管理工具
- [ ] `llmos_cli.py` - 意图驱动 CLI 界面
  - 自然语言输入
  - 流式输出
  - 任务分解展示
- [ ] `security_manager.py` - 安全权限管控
  - 动态权限拦截器
  - 高危操作识别
  - 待审核任务队列

### 阶段三：测试流
- [ ] `auto_test_pipeline.py` - 自动测试管道
  - 复杂意图测例
  - 自动验证
  - 自愈机制

### 阶段四：终极交付
- [ ] `build_and_run.sh` - 总控脚本
- [ ] `README.md` - 项目说明文档
- [ ] `DESIGN_DOC.md` - 架构设计文档

---

## 已完成的工作

### 2026-03-23 (依赖兼容性修复)

#### httpx 版本兼容性问题修复
- **问题**: `httpx 0.28.x` 与 `openai 1.30.1` 不兼容，导致 CLI 启动失败
- **原因**: httpx 0.28.0 引入破坏性 API 变更（移除 `proxies` 参数等）
- **修复**:
  - 创建 `requirements.txt` 固定依赖版本
  - 更新 `init_env.sh` 添加 `httpx==0.27.0`
  - 创建 `plans/fix_openai_init_error.md` 详细记录修复过程
- **验证**: CLI 启动成功，OpenAI 客户端初始化正常

---

### 2026-03-19 (迭代14-15)

#### Docker 容器支持
- 创建 `Dockerfile`: Ubuntu 22.04 基础镜像，772MB
- 创建 `docker-compose.yml`: 本地开发配置
- 创建 `bianbu/docker-compose.bianbu.yml`: Bianbu K1 RISC-V 平台配置
- 修复 OpenAI SDK 兼容性: `openai>=1.12.0` + `httpx==0.27.0`
- 容器测试验证通过

#### Nexa 智能体脚本扩展
- 创建 `nexa_scripts/yatai_os_core.nx`: 核心 Nexa 模块
  - 协议定义: TaskResult, IntentType, AgentCapability
  - 智能体: IntentRouter, FileManager, ProcessManager, NetworkManager, PackageManager
  - 工作流: user_onboarding, file_operation, system_monitor
- Nexa 运行时集成: `core/nexa_runtime.py`

#### CLI 增强
- 指令穿透模式: 支持 ls, cd, pwd, cat 等基础命令
- YatAIOS 品牌提示符: `YatAIOS:path$`
- Rich 终端格式化: 修复 cyan/blue 控制符渲染

#### 项目重构
- 项目正式命名为 **YatAIOS** (Yet Another Transformative AI OS)
- API 配置更新: glm-5 模型, aihub.arcsysu.cn 端点
- 文档全面更新: README, PROGRESS, docs/

---

### 历史记录 (2026-03-18)

#### 项目初始化
- 创建目录结构:
  ```
  agent_os/
  ├── core/          # 核心模块
  ├── tools/         # 工具抽象层
  ├── cli/           # CLI界面
  ├── security/      # 安全模块
  ├── tests/         # 测试用例
  ├── docs/          # 文档
  ├── logs/          # 日志
  ├── data/          # 数据
  ├── cache/         # 缓存
  └── pending_tasks/ # 待审核任务
  ```

#### 环境配置
- `init_env.sh`: 自动检测 Ubuntu 22.04，安装 Python 3.8+、pip、虚拟环境
- 安装核心依赖: langchain, openai, anthropic, requests, psutil, pyyaml, rich 等
- 自动验证模块导入

#### 配置文件
- `config.yaml`: 完整系统配置
  - LLM 配置 (OpenAI/Anthropic/Ollama)
  - 端云协同策略
  - 智能体配置 (Router + 4个子智能体)
  - 工具系统配置
  - 安全权限等级 (5级)
  - 高危操作关键词库

---

## 进行中的工作

### 智能体核心 (Agent Core)
**文件**: `core/agent_daemon.py` (待实现)

**功能规划**:
1. 守护进程模式运行
2. 集成 OpenAI Function Calling 格式
3. SQLite 记忆库存储对话历史
4. 主控 Router Agent + 专用子 Agent
5. 任务分解与工具调度
6. 完整日志记录

**架构设计**:
```
┌─────────────────────────────────────────────────────────┐
│                    Agent Core                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Router    │───▶│ Sub-Agent 1 │    │ Sub-Agent 2 │  │
│  │  (主控)     │    │ HardwareOpt │    │  FileManager│  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                   │        │
│         ▼                  ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Function Calling Interface             ││
│  └─────────────────────────────────────────────────────┘│
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Tool Registry (系统工具)               ││
│  │  file_ops | process_ops | network_ops | package_ops ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## 待实现功能详情

### 1. 系统工具层 (Tools)

| 工具名称 | 功能描述 | 风险等级 |
|---------|---------|---------|
| `file_read` | 读取文件内容 | NORMAL |
| `file_write` | 写入文件内容 | ELEVATED |
| `file_search` | 搜索文件 | NORMAL |
| `process_list` | 列出进程 | NORMAL |
| `process_kill` | 终止进程 | CRITICAL |
| `network_info` | 获取网络信息 | NORMAL |
| `network_ping` | Ping 测试 | NORMAL |
| `package_install` | 安装软件包 | ELEVATED |
| `package_remove` | 卸载软件包 | CRITICAL |
| `system_info` | 获取系统信息 | NORMAL |

### 2. 安全权限模型

```
权限等级:
  0 - BLOCKED:   完全禁止 (rm -rf /, mkfs, etc.)
  1 - CRITICAL:  高危操作 (kill -9, package remove, etc.)
  2 - ELEVATED:  特权操作 (file write, package install)
  3 - NORMAL:    普通操作 (file read, process list)
  4 - TRUSTED:   可信操作 (system info, ping)
```

### 3. 待审核任务队列

高危操作自动进入 `pending_tasks.db`:
- 用户确认后执行
- 72小时后自动清理
- 完整的审计日志

---

## 技术决策记录

### 决策 1: LLM 提供商选择
- **决定**: 支持 OpenAI GPT-4o-mini 作为主选
- **备选**: Anthropic Claude 作为云端fallback
- **边缘**: Ollama 本地模型 (K1 平台)
- **原因**: 平衡成本、性能和隐私

### 决策 2: 工具调用格式
- **决定**: 采用 OpenAI Function Calling 格式
- **原因**: 标准化、成熟、社区支持广泛

### 决策 3: 记忆存储
- **决定**: SQLite 作为默认记忆库
- **原因**: 轻量、无外部依赖、易于备份

### 决策 4: 安全策略
- **决定**: 默发拦截，高危操作需用户确认
- **原因**: AIOS 安全至关重要，不能自动执行危险操作

---

## 下一步计划

### 优先级 1: 核心模块实现
1. [ ] 实现 `agent_daemon.py` - Agent Core
2. [ ] 实现 `system_tools.py` - 工具层
3. [ ] 实现 `security_manager.py` - 安全层

### 优先级 2: 用户界面
4. [ ] 实现 `llmos_cli.py` - CLI 界面

### 优先级 3: 测试与部署
5. [ ] 实现 `auto_test_pipeline.py` - 自动测试
6. [ ] 实现 `build_and_run.sh` - 部署脚本
7. [ ] 完善文档 (README, DESIGN_DOC)

---

## 已知限制与风险

1. **API 密钥**: 需要用户提供 OpenAI/Anthropic API 密钥
2. **K1 平台**: 代码设计支持 K1，但测试在 x86_64 模拟环境
3. **网络依赖**: 云端 LLM 需要网络连接
4. **安全**: 仍需用户审慎评估拦截策略

---

## 参考资源

- Bianbu 系统文档: https://www.spacemit.com/community/document
- MUSE BOOK 手册: https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/eco/k1_muse_book
- K1 芯片介绍: https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/key_stone/k1

---

*最后更新: 2026-03-19 15:10 UTC*
