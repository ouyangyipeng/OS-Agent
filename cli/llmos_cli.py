#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 意图驱动 CLI 界面
Intent-Driven CLI Interface

功能：
- 全局自然语言交互入口
- 接收用户任务指令
- 展示任务分解、工具调用过程与最终结果
- 流式输出确保执行过程可解释

Author: Bianbu LLM OS Team
"""

import os
import sys
import json
import time
import signal
import argparse
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 配置
from core.agent_daemon import AgentDaemon
from tools.system_tools import SystemTools
from security.security_manager import SecurityManager


class Colors:
    """ANSI 颜色码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'


class CLI:
    """
    Bianbu LLM OS 命令行界面
    
    提供美观的交互界面，展示 AI 意图理解和执行过程
    """
    
    def __init__(self, config_path: str = "config.yaml", verbose: bool = False,
                 use_rich: bool = True, color: bool = True):
        """初始化 CLI"""
        self.verbose = verbose
        self.use_rich = use_rich and RICH_AVAILABLE
        self.color = color
        self.console = Console() if self.use_rich else None
        
        # 初始化核心组件
        self.agent = AgentDaemon(config_path)
        self.session_id = None
        
        # 初始化持久记忆存储（OpenCLAW风格的长期助手）
        from core.persistent_memory import PersistentMemoryStore
        self.persistent_memory = PersistentMemoryStore()
        
        # 命令历史
        self.history: List[str] = []
        self.history_file = "data/command_history.txt"
        self._load_history()
        
        # 配置
        self.config = self.agent.config
        self.cli_config = self.config.get('cli', {})
        self.prompt_config = self.cli_config.get('prompt', {})
        
        # 退出标志
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理退出信号"""
        self.running = False
        print("\n收到退出信号，正在清理...")
        self._save_history()
        sys.exit(0)
    
    def _load_history(self):
        """加载历史命令"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = [line.strip() for line in f if line.strip()]
            except:
                pass
    
    def _save_history(self):
        """保存历史命令"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                for cmd in self.history[-1000:]:  # 保留最近1000条
                    f.write(cmd + '\n')
        except:
            pass
    
    def print(self, text: str, style: str = "", rich: bool = True):
        """打印文本"""
        if self.use_rich and rich and self.console:
            if style == "error":
                self.console.print(f"[bold red]错误:[/bold red] {text}")
            elif style == "success":
                self.console.print(f"[bold green]成功:[/bold green] {text}")
            elif style == "warning":
                self.console.print(f"[bold yellow]警告:[/bold yellow] {text}")
            elif style == "info":
                self.console.print(f"[bold blue]信息:[/bold blue] {text}")
            elif style == "thinking":
                self.console.print(f"[dim cyan]{text}[/dim cyan]")
            else:
                self.console.print(text)
        else:
            if self.color:
                prefix = ""
                if style == "error":
                    prefix = f"{Colors.RED}{Colors.BOLD}"
                elif style == "success":
                    prefix = f"{Colors.GREEN}{Colors.BOLD}"
                elif style == "warning":
                    prefix = f"{Colors.YELLOW}{Colors.BOLD}"
                elif style == "info":
                    prefix = f"{Colors.CYAN}{Colors.BOLD}"
                elif style == "thinking":
                    prefix = f"{Colors.DIM}{Colors.CYAN}"
                
                if prefix:
                    print(f"{prefix}{text}{Colors.RESET}")
                else:
                    print(text)
            else:
                print(text)
    
    def print_banner(self):
        """打印横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ███╗   ███╗███████╗███████╗████████╗ ██████╗██╗      ██╗     ║
║     ████╗ ████║██╔════╝██╔════╝╚══██╔══╝██╔════╝██║      ██║     ║
║     ██╔████╔██║█████╗  █████╗     ██║   ██║     ██║      ██║     ║
║     ██║╚██╔╝██║██╔══╝  ██╔══╝     ██║   ██║     ██║      ██║     ║
║     ██║ ╚═╝ ██║███████╗███████╗   ██║   ╚██████╗███████╗███████╗║
║     ╚═╝     ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝╚══════╝╚══════╝║
║                                                                  ║
║         融合原生AI智能体的Bianbu系统交互范式重构                   ║
║         LLM OS - Intent-Driven Operating System                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        if self.use_rich and self.console:
            self.console.print(banner, style="cyan")
        else:
            print(banner)
    
    def print_status(self):
        """打印状态信息"""
        if self.use_rich and self.console:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column(style="dim")
            table.add_column()
            
            status = self.agent.status.value if hasattr(self.agent.status, 'value') else str(self.agent.status)
            table.add_row("状态", f"[green]{status}[/green]")
            table.add_row("会话", f"[blue]{self.session_id[:8]}...[/blue]" if self.session_id else "[red]未建立[/red]")
            
            self.console.print(table)
        else:
            status = self.agent.status.value if hasattr(self.agent.status, 'value') else str(self.agent.status)
            print(f"状态: {status}")
            print(f"会话: {self.session_id[:8]}..." if self.session_id else "会话: 未建立")
    
    def print_help(self):
        """打印帮助信息"""
        help_text = """
可用命令:
  help              显示此帮助信息
  clear / cls       清除屏幕
  history           显示命令历史
  status            显示当前状态
  pending           显示待审核任务
  confirm <id>      确认执行待审核任务
  reject <id>       拒绝待审核任务
  search <query>    搜索记忆中的相关任务
  exit / quit       退出程序
  
  [持久记忆命令]
  memory list       列出所有记忆
  memory add <k> <v> 添加短期记忆
  memory get <key>  获取指定记忆
  memory stats      显示记忆统计
  memory clear     清除短期记忆
  
  [技能管理命令]
  skill list        列出已学习技能
  skill add <name> <desc> <category> 学习新技能
  skill forget <name> 遗忘技能
  
直接输入自然语言即可与 AI 交互，例如:
  "查看系统信息"
  "帮我找一下桌面上昨天下载的 PDF 文件"
  "安装 nginx 服务器"
"""
        if self.use_rich and self.console:
            self.console.print(Panel(help_text.strip(), title="帮助", border_style="blue"))
        else:
            print(help_text)
    
    def print_thinking(self):
        """打印思考中状态"""
        if self.use_rich and self.console:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
        return None
    
    def print_result(self, result: Dict):
        """打印执行结果"""
        if not result.get('success'):
            self.print(f"执行失败: {result.get('error', '未知错误')}", "error")
            return
        
        response = result.get('response', '')
        
        # 打印 AI 响应
        if self.use_rich and self.console:
            self.console.print(Panel(
                Markdown(response),
                title="AI 响应",
                border_style="green",
                padding=(1, 2)
            ))
        else:
            print("\n" + "=" * 60)
            print("AI 响应:")
            print("=" * 60)
            print(response)
            print()
        
        # 打印执行步骤
        if self.verbose and result.get('steps'):
            self._print_steps(result['steps'])
        
        # 打印工具结果摘要
        if result.get('tool_results'):
            self._print_tool_results(result['tool_results'])
    
    def _print_steps(self, steps: List[Dict]):
        """打印执行步骤"""
        if self.use_rich and self.console:
            table = Table(title="执行步骤", show_header=True)
            table.add_column("步骤", style="cyan", width=4)
            table.add_column("工具", style="yellow")
            table.add_column("状态", width=10)
            table.add_column("摘要", style="dim")
            
            for step in steps:
                status = "[green]✓[/green]" if step.get('success') else "[red]✗[/red]"
                table.add_row(
                    str(step.get('step', '')),
                    step.get('tool', ''),
                    status,
                    step.get('summary', '')
                )
            
            self.console.print(table)
        else:
            print("\n执行步骤:")
            print("-" * 60)
            for step in steps:
                status = "✓" if step.get('success') else "✗"
                print(f"  {step.get('step')}. [{status}] {step.get('tool')}: {step.get('summary', '')}")
            print()
    
    def _print_tool_results(self, results: List[Dict]):
        """打印工具执行结果"""
        if not self.verbose:
            return
        
        if self.use_rich and self.console:
            for i, res in enumerate(results):
                tool_name = res.get('tool', 'unknown')
                success = res.get('success', False)
                status_str = "[green]成功[/green]" if success else "[red]失败[/red]"
                
                self.console.print(f"\n[cyan]工具 {i+1}:[/cyan] {tool_name} - {status_str}")
                
                if res.get('error'):
                    self.console.print(f"  [red]错误:[/red] {res['error']}")
                elif res.get('result'):
                    result_str = json.dumps(res['result'], indent=2, ensure_ascii=False)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    self.console.print(Syntax(result_str, "json", theme="monokai", line_numbers=False))
        else:
            print("\n工具执行结果:")
            print("-" * 60)
            for i, res in enumerate(results):
                status = "成功" if res.get('success') else "失败"
                print(f"  {i+1}. {res.get('tool')}: {status}")
                if res.get('error'):
                    print(f"     错误: {res['error']}")
            print()
    
    def print_pending_tasks(self):
        """打印待审核任务"""
        tasks = self.agent.get_pending_tasks()
        
        if not tasks:
            self.print("没有待审核的任务", "info")
            return
        
        if self.use_rich and self.console:
            table = Table(title="待审核任务", show_header=True)
            table.add_column("ID", style="cyan", width=16)
            table.add_column("意图", style="white")
            table.add_column("风险等级", width=10)
            table.add_column("创建时间", style="dim")
            
            for task in tasks:
                risk = task.risk_level.name if hasattr(task, 'risk_level') else 'UNKNOWN'
                risk_color = "red" if risk == "CRITICAL" else "yellow"
                
                table.add_row(
                    task.task_id[:16],
                    task.user_intent[:50] + "..." if len(task.user_intent) > 50 else task.user_intent,
                    f"[{risk_color}]{risk}[/{risk_color}]",
                    task.created_at[:19]
                )
            
            self.console.print(table)
        else:
            print("\n待审核任务:")
            print("=" * 60)
            for task in tasks:
                risk = task.risk_level.name if hasattr(task, 'risk_level') else 'UNKNOWN'
                print(f"ID: {task.task_id[:16]}")
                print(f"意图: {task.user_intent[:50]}...")
                print(f"风险等级: {risk}")
                print(f"创建时间: {task.created_at[:19]}")
                print("-" * 60)
            print()
    
    def run_interactive(self):
        """运行交互式会话"""
        self.print_banner()
        
        # 开始新会话
        self.session_id = self.agent.start_session()
        
        self.print(f"会话已建立: {self.session_id[:16]}...", "info")
        self.print("输入 'help' 查看可用命令，输入 'exit' 退出\n", "dim")
        
        while self.running:
            try:
                # 获取用户输入
                prompt = self.prompt_config.get('main', '🏠 Bianbu > ')
                if not self.use_rich:
                    prompt = "Bianbu > "
                
                user_input = input(prompt).strip()
                
                # 空输入处理
                if not user_input:
                    continue
                
                # 添加到历史
                self.history.append(user_input)
                self._save_history()
                
                # 处理命令
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.print("正在退出...", "info")
                    break
                
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                elif user_input.lower() in ['clear', 'cls']:
                    if self.use_rich and self.console:
                        self.console.clear()
                    else:
                        print("\033[2J\033[H")
                    continue
                
                elif user_input.lower() == 'history':
                    self._show_history()
                    continue
                
                elif user_input.lower() == 'status':
                    self.print_status()
                    continue
                
                elif user_input.lower() == 'pending':
                    self.print_pending_tasks()
                    continue
                
                elif user_input.lower().startswith('confirm '):
                    task_id = user_input[8:].strip()
                    if self.agent.confirm_task(task_id):
                        self.print(f"任务 {task_id[:16]} 已确认执行", "success")
                    else:
                        self.print(f"任务确认失败", "error")
                    continue
                
                elif user_input.lower().startswith('reject '):
                    task_id = user_input[7:].strip()
                    if self.agent.reject_task(task_id):
                        self.print(f"任务 {task_id[:16]} 已拒绝", "warning")
                    else:
                        self.print(f"任务拒绝失败", "error")
                    continue
                
                elif user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    results = self.agent.search_memory(query)
                    self._print_search_results(results)
                    continue
                
                # ========== 持久记忆命令 ==========
                elif user_input.lower().startswith('memory '):
                    self._handle_memory_command(user_input[7:].strip())
                    continue
                
                # ========== 技能管理命令 ==========
                elif user_input.lower().startswith('skill '):
                    self._handle_skill_command(user_input[6:].strip())
                    continue
                
                # 处理 AI 意图
                self.print("正在分析您的意图...", "thinking")
                
                result = self.agent.process_intent(user_input, self.session_id)
                self.print_result(result)
                
            except KeyboardInterrupt:
                print("\n(使用 'exit' 命令退出)")
                continue
            except EOFError:
                break
            except Exception as e:
                self.print(f"发生错误: {e}", "error")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
        
        self._save_history()
        self.print("再见!", "info")
    
    def _show_history(self):
        """显示历史记录"""
        if not self.history:
            self.print("没有历史记录", "info")
            return
        
        if self.use_rich and self.console:
            for i, cmd in enumerate(self.history[-20:], 1):
                self.console.print(f"[dim]{i}.[/dim] {cmd}")
        else:
            for i, cmd in enumerate(self.history[-20:], 1):
                print(f"  {i}. {cmd}")
    
    def _print_search_results(self, results: List[Dict]):
        """打印搜索结果"""
        if not results:
            self.print("没有找到相关记录", "info")
            return
        
        if self.use_rich and self.console:
            table = Table(title="搜索结果", show_header=True)
            table.add_column("任务ID", style="cyan")
            table.add_column("用户意图", style="white")
            table.add_column("时间", style="dim")
            
            for r in results:
                table.add_row(
                    r.get('task_id', '')[:16],
                    r.get('user_intent', '')[:50],
                    r.get('created_at', '')[:10]
                )
            
            self.console.print(table)
        else:
            print("\n搜索结果:")
            for r in results:
                print(f"  - {r.get('user_intent', '')[:50]}...")
    
    def _handle_memory_command(self, args: str):
        """
        处理持久记忆命令
        
        Args:
            args: 命令参数 (list|add <key> <value>|get <key>|stats|clear)
        """
        parts = args.split(maxsplit=1)
        sub_cmd = parts[0].lower() if parts else ''
        
        if sub_cmd == 'list':
            # 列出所有记忆
            recent = self.persistent_memory.get_recent_memories(limit=20)
            long_term = self.persistent_memory.get_long_term_memories()
            
            if self.use_rich and self.console:
                table = Table(title="记忆列表", show_header=True)
                table.add_column("层级", style="cyan", width=12)
                table.add_column("键", style="yellow")
                table.add_column("值", style="white")
                table.add_column("重要性", style="dim", width=8)
                
                for m in recent:
                    table.add_row(
                        m.level.name,
                        m.key[:30],
                        str(m.value)[:40] if m.value else "",
                        f"{m.importance:.1f}"
                    )
                for m in long_term:
                    table.add_row(
                        m.level.name,
                        m.key[:30],
                        str(m.value)[:40] if m.value else "",
                        f"{m.importance:.1f}"
                    )
                self.console.print(table)
            else:
                print("\n=== 记忆列表 ===")
                for m in recent + long_term:
                    print(f"[{m.level.name}] {m.key}: {str(m.value)[:40]}")
        
        elif sub_cmd == 'add':
            # 添加记忆: memory add <key> <value>
            if len(parts) < 2 or ' ' not in parts[1]:
                self.print("用法: memory add <key> <value>", "warning")
                return
            key_val = parts[1].split(maxsplit=1)
            if len(key_val) < 2:
                self.print("用法: memory add <key> <value>", "warning")
                return
            key, value = key_val[0], key_val[1]
            self.persistent_memory.store_short_term(key, value)
            self.print(f"已添加短期记忆: {key}", "success")
        
        elif sub_cmd == 'get':
            # 获取记忆: memory get <key>
            if len(parts) < 2:
                self.print("用法: memory get <key>", "warning")
                return
            key = parts[1]
            value = self.persistent_memory.retrieve(key)
            if value:
                self.print(f"{key}: {value}", "info")
            else:
                self.print(f"未找到记忆: {key}", "warning")
        
        elif sub_cmd == 'stats':
            # 显示记忆统计
            stats = self.persistent_memory.get_memory_stats()
            if self.use_rich and self.console:
                table = Table(title="记忆统计", show_header=False)
                table.add_column("指标", style="cyan")
                table.add_column("值", style="white")
                for level_name, count in stats.get('by_level', {}).items():
                    table.add_row(level_name, str(count))
                self.console.print(table)
            else:
                print("\n=== 记忆统计 ===")
                for level_name, count in stats.get('by_level', {}).items():
                    print(f"  {level_name}: {count}")
        
        elif sub_cmd == 'clear':
            # 清除短期记忆
            self.persistent_memory.cleanup_expired()
            self.print("已清除过期记忆", "success")
        
        else:
            self.print(f"未知子命令: {sub_cmd}", "error")
            self.print("可用: list|add|get|stats|clear", "info")
    
    def _handle_skill_command(self, args: str):
        """
        处理技能管理命令
        
        Args:
            args: 命令参数 (list|add <name> <desc> <category>|forget <name>)
        """
        parts = args.split(maxsplit=1)
        sub_cmd = parts[0].lower() if parts else ''
        
        if sub_cmd == 'list':
            # 列出已学习技能
            skills = self.persistent_memory.get_skills()
            if not skills:
                self.print("还没有学习任何技能", "info")
                return
            
            if self.use_rich and self.console:
                table = Table(title="已学习技能", show_header=True)
                table.add_column("技能ID", style="cyan")
                table.add_column("名称", style="yellow")
                table.add_column("类别", style="green")
                table.add_column("熟练度", style="magenta", width=8)
                table.add_column("状态", style="white", width=10)
                
                for s in skills:
                    table.add_row(
                        s.get('skill_id', '')[:20],
                        s.get('name', ''),
                        s.get('category', ''),
                        f"{s.get('proficiency', 0):.1f}",
                        s.get('state', 'UNKNOWN')
                    )
                self.console.print(table)
            else:
                print("\n=== 已学习技能 ===")
                for s in skills:
                    print(f"  [{s.get('category', '')}] {s.get('name', '')} - 熟练度: {s.get('proficiency', 0):.1f}")
        
        elif sub_cmd == 'add':
            # 学习新技能: skill add <name> <desc> <category>
            if len(parts) < 2:
                self.print("用法: skill add <name> <desc> <category>", "warning")
                return
            # 解析: name|desc|category
            parts_all = parts[1].split('|')
            if len(parts_all) < 3:
                self.print("用法: skill add <name>|<desc>|<category>", "warning")
                return
            name, desc, category = [p.strip() for p in parts_all[:3]]
            skill_id = f"skill.{category.lower()}.{name.lower().replace(' ', '_')}"
            self.persistent_memory.learn_skill(skill_id, name, desc, category)
            self.print(f"已学习新技能: {name}", "success")
        
        elif sub_cmd == 'forget':
            # 遗忘技能: skill forget <name>
            if len(parts) < 2:
                self.print("用法: skill forget <name>", "warning")
                return
            skill_name = parts[1]
            self.persistent_memory.forget_skill(skill_name)
            self.print(f"已遗忘技能: {skill_name}", "success")
        
        else:
            self.print(f"未知子命令: {sub_cmd}", "error")
            self.print("可用: list|add|forget", "info")
    
    def run_single(self, intent: str) -> Dict:
        """
        执行单次意图
        
        Args:
            intent: 用户意图
            
        Returns:
            执行结果
        """
        if not self.session_id:
            self.session_id = self.agent.start_session()
        
        return self.agent.process_intent(intent, self.session_id)


class StreamingCLI(CLI):
    """
    流式输出 CLI
    
    支持实时显示思考过程和执行状态
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thinking_progress = None
    
    def _create_callback(self) -> Callable:
        """创建进度回调函数"""
        def callback(event: Dict):
            stage = event.get('stage', '')
            message = event.get('message', '')
            
            if stage == 'thinking':
                if self.use_rich and self.console:
                    if not self.thinking_progress:
                        self.thinking_progress = self.console.status("[cyan]思考中...", spinner="dots")
                    # 状态已在别处处理
                else:
                    print(f"\r💭 {message}", end='', flush=True)
            
            elif stage == 'tool':
                if self.use_rich and self.console:
                    self.console.print(f"[yellow]⚙[/yellow] {message}")
                else:
                    print(f"\r⚙ {message}")
            
            elif stage == 'done':
                if self.use_rich and self.console:
                    pass
                else:
                    print()  # 换行
                
        return callback
    
    def run_single_stream(self, intent: str) -> Dict:
        """流式执行单次意图"""
        if not self.session_id:
            self.session_id = self.agent.start_session()
        
        callback = self._create_callback()
        return self.agent.process_stream(intent, self.session_id, callback)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Bianbu LLM OS - 意图驱动 CLI 界面",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--no-color', action='store_true', help='禁用颜色')
    parser.add_argument('--no-rich', action='store_true', help='禁用 Rich 美化输出')
    parser.add_argument('-i', '--intent', type=str, help='单次执行意图并退出')
    parser.add_argument('--interactive', action='store_true', default=True, help='交互模式')
    
    args = parser.parse_args()
    
    # 创建 CLI
    cli = CLI(
        config_path=args.config,
        verbose=args.verbose,
        use_rich=not args.no_rich,
        color=not args.no_color
    )
    
    # 单次执行模式
    if args.intent:
        result = cli.run_single(args.intent)
        cli.print_result(result)
        
        # 返回退出码
        sys.exit(0 if result.get('success') else 1)
    
    # 交互模式
    cli.run_interactive()


if __name__ == '__main__':
    main()
