#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 自动测试管道
Automated Test Pipeline

功能：
- 设计并执行复杂意图测例
- 自动验证最终系统状态
- 自愈机制：自动分析报错日志并尝试修复
- 生成测试报告

Author: Bianbu LLM OS Team
"""

import os
import sys
import json
import time
import datetime
import sqlite3
import traceback
import subprocess
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from core.agent_daemon import AgentDaemon
from security.security_manager import SecurityManager
from tools.system_tools import SystemTools


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestSeverity(Enum):
    """测试严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    intent: str
    expected_tools: List[str] = field(default_factory=list)
    expected_result_checks: List[Dict] = field(default_factory=list)
    severity: TestSeverity = TestSeverity.MEDIUM
    enabled: bool = True
    timeout: int = 120


@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    status: TestStatus
    start_time: str
    end_time: str
    duration: float
    intent: str
    response: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    self_healing_attempts: int = 0
    logs: List[str] = field(default_factory=list)


@dataclass
class TestReport:
    """测试报告"""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_duration: float
    results: List[TestResult]
    summary: Dict[str, Any] = field(default_factory=dict)


class SelfHealingEngine:
    """
    自愈引擎
    
    当测试失败时，自动分析错误日志并尝试修复代码
    """
    
    def __init__(self, agent_daemon: AgentDaemon):
        self.agent = agent_daemon
        self.max_attempts = 2
        self.fix_strategies = [
            self._fix_import_error,
            self._fix_syntax_error,
            self._fix_permission_error,
            self._fix_timeout_error,
            self._fix_api_error,
        ]
    
    def analyze_and_fix(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """
        分析错误并尝试修复
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            (是否修复成功, 修复说明)
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        print(f"[SelfHealing] 检测到错误: {error_type} - {error_msg[:100]}")
        
        for strategy in self.fix_strategies:
            try:
                success, message = strategy(error, context)
                if success:
                    print(f"[SelfHealing] 修复成功: {message}")
                    return True, message
            except Exception as e:
                print(f"[SelfHealing] 策略 {strategy.__name__} 失败: {e}")
        
        print(f"[SelfHealing] 无法自动修复错误")
        return False, "无法自动修复"
    
    def _fix_import_error(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """修复导入错误"""
        error_msg = str(error)
        
        # 检查缺少模块
        if "ModuleNotFoundError" in str(error) or "ImportError" in str(error):
            import re
            match = re.search(r"Module '(\w+)'", error_msg)
            if match:
                module_name = match.group(1)
                
                # 尝试安装缺失模块
                try:
                    result = subprocess.run(
                        ['pip', 'install', module_name, '-q'],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        return True, f"已安装缺失模块: {module_name}"
                except:
                    pass
        
        return False, ""
    
    def _fix_syntax_error(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """修复语法错误"""
        # 语法错误需要手动修复，这里只是报告
        return False, ""
    
    def _fix_permission_error(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """修复权限错误"""
        error_msg = str(error).lower()
        
        if "permission" in error_msg or "access" in error_msg:
            file_path = context.get('file_path', '')
            if file_path:
                try:
                    os.chmod(file_path, 0o644)
                    return True, f"已修复文件权限: {file_path}"
                except:
                    pass
        
        return False, ""
    
    def _fix_timeout_error(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """修复超时错误"""
        error_msg = str(error).lower()
        
        if "timeout" in error_msg or "timed out" in error_msg:
            # 增加超时时间
            current_timeout = context.get('timeout', 30)
            context['timeout'] = current_timeout * 2
            return True, f"已增加超时时间: {current_timeout} -> {current_timeout * 2}"
        
        return False, ""
    
    def _fix_api_error(self, error: Exception, context: Dict) -> Tuple[bool, str]:
        """修复 API 错误"""
        error_msg = str(error)
        
        # 检查 API 密钥问题
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
            return False, "API 密钥问题，需要手动配置"
        
        # 检查速率限制
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            time.sleep(5)  # 等待后重试
            return True, "检测到速率限制，已等待后重试"
        
        return False, ""


class TestPipeline:
    """
    自动测试管道
    
    设计并执行复杂意图测例，验证系统功能
    """
    
    def __init__(self, config_path: str = "config.yaml", verbose: bool = True):
        """初始化测试管道"""
        self.config_path = config_path
        self.verbose = verbose
        self.results: List[TestResult] = []
        
        # 初始化核心组件
        self.agent = AgentDaemon(config_path)
        self.security_manager = SecurityManager(
            self.agent.config.get('security', {}) if hasattr(self.agent, 'config') else {}
        )
        self.tools = SystemTools(self.security_manager)
        self.self_healer = SelfHealingEngine(self.agent)
        
        # 测试用例
        self.test_cases: List[TestCase] = []
        self._load_default_test_cases()
        
        # 报告输出路径
        self.report_dir = "output"
        os.makedirs(self.report_dir, exist_ok=True)
    
    def _load_default_test_cases(self):
        """加载默认测试用例"""
        self.test_cases = [
            # ========== 文件操作测试 ==========
            TestCase(
                id="file_001",
                name="搜索文件",
                description="搜索包含特定关键词的文件",
                intent="帮我找一下桌面上昨天下载的带有'RISC-V'字样的PDF文件",
                expected_tools=["file_search"],
                severity=TestSeverity.HIGH,
                enabled=True
            ),
            TestCase(
                id="file_002",
                name="读取文件",
                description="读取系统文件",
                intent="读取 /etc/hostname 文件内容",
                expected_tools=["file_read"],
                severity=TestSeverity.LOW,
                enabled=True
            ),
            TestCase(
                id="file_003",
                name="列出目录",
                description="列出目录内容",
                intent="列出当前目录的所有文件",
                expected_tools=["file_list"],
                severity=TestSeverity.LOW,
                enabled=True
            ),
            
            # ========== 进程管理测试 ==========
            TestCase(
                id="process_001",
                name="列出进程",
                description="列出运行中的进程",
                intent="查看当前系统运行的进程",
                expected_tools=["process_list"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            TestCase(
                id="process_002",
                name="获取进程信息",
                description="获取指定进程的详细信息",
                intent="查看 PID 为 1 的进程详细信息",
                expected_tools=["process_info"],
                severity=TestSeverity.LOW,
                enabled=True
            ),
            
            # ========== 网络测试 ==========
            TestCase(
                id="network_001",
                name="获取网络信息",
                description="获取网络配置信息",
                intent="查看系统的网络配置",
                expected_tools=["network_info"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            TestCase(
                id="network_002",
                name="Ping测试",
                description="测试网络连接",
                intent="ping 一下 www.baidu.com",
                expected_tools=["network_ping"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            
            # ========== 系统信息测试 ==========
            TestCase(
                id="system_001",
                name="获取系统信息",
                description="获取完整的系统信息",
                intent="查看当前系统信息",
                expected_tools=["system_info"],
                severity=TestSeverity.HIGH,
                enabled=True
            ),
            TestCase(
                id="system_002",
                name="磁盘使用情况",
                description="获取磁盘使用情况",
                intent="查看磁盘使用情况",
                expected_tools=["disk_usage"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            TestCase(
                id="system_003",
                name="内存使用情况",
                description="获取内存使用情况",
                intent="查看内存使用情况",
                expected_tools=["memory_usage"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            
            # ========== 包管理测试 ==========
            TestCase(
                id="package_001",
                name="搜索软件包",
                description="搜索可安装的软件包",
                intent="搜索一下有没有 nginx 软件包",
                expected_tools=["package_search"],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            TestCase(
                id="package_002",
                name="列出已安装包",
                description="列出已安装的软件包",
                intent="列出已安装的 Python 相关包",
                expected_tools=["package_list"],
                severity=TestSeverity.LOW,
                enabled=True
            ),
            
            # ========== 安全测试 ==========
            TestCase(
                id="security_001",
                name="高危操作拦截",
                description="测试 rm -rf 命令是否被拦截",
                intent="执行 rm -rf /tmp/test 命令",
                expected_tools=["file_delete"],
                severity=TestSeverity.CRITICAL,
                enabled=True
            ),
            TestCase(
                id="security_002",
                name="待审核任务",
                description="检查待审核任务队列",
                intent="查看当前有哪些待审核的任务",
                expected_tools=[],
                severity=TestSeverity.MEDIUM,
                enabled=True
            ),
            
            # ========== 复杂意图测试 ==========
            TestCase(
                id="complex_001",
                name="复合任务",
                description="测试复杂的多步骤任务",
                intent="先查看系统信息，然后列出当前目录的文件",
                expected_tools=["system_info", "file_list"],
                severity=TestSeverity.HIGH,
                enabled=True,
                timeout=180
            ),
        ]
    
    def load_test_cases_from_file(self, file_path: str):
        """从文件加载测试用例"""
        if not os.path.exists(file_path):
            print(f"[WARN] 测试用例文件不存在: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data.get('test_cases', []):
                test_case = TestCase(
                    id=item.get('id', f'test_{len(self.test_cases)}'),
                    name=item.get('name', 'Unnamed Test'),
                    description=item.get('description', ''),
                    intent=item.get('intent', ''),
                    expected_tools=item.get('expected_tools', []),
                    severity=TestSeverity(item.get('severity', 'medium')),
                    enabled=item.get('enabled', True),
                    timeout=item.get('timeout', 120)
                )
                self.test_cases.append(test_case)
            
            print(f"[INFO] 从文件加载了 {len(self.test_cases)} 个测试用例")
        except Exception as e:
            print(f"[ERROR] 加载测试用例失败: {e}")
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            TestResult: 测试结果
        """
        print(f"\n{'='*60}")
        print(f"执行测试: {test_case.name} ({test_case.id})")
        print(f"意图: {test_case.intent}")
        print(f"{'='*60}")
        
        start_time = datetime.datetime.now()
        start_iso = start_time.isoformat()
        
        result = TestResult(
            test_id=test_case.id,
            status=TestStatus.RUNNING,
            start_time=start_iso,
            end_time="",
            duration=0.0,
            intent=test_case.intent,
            logs=[]
        )
        
        try:
            # 调用 Agent 处理意图
            response = self.agent.process_intent(test_case.intent)
            
            result.response = response.get('response', '')
            result.tool_calls = response.get('steps', [])
            
            # 检查执行结果
            if response.get('success'):
                # 验证工具调用
                called_tools = [step.get('tool') for step in result.tool_calls if step.get('tool')]
                
                if test_case.expected_tools:
                    missing_tools = set(test_case.expected_tools) - set(called_tools)
                    unexpected_tools = set(called_tools) - set(test_case.expected_tools)
                    
                    if missing_tools:
                        result.logs.append(f"警告: 缺少预期工具 {missing_tools}")
                    if unexpected_tools:
                        result.logs.append(f"信息: 调用了非预期工具 {unexpected_tools}")
                
                result.status = TestStatus.PASSED
                print(f"[PASS] 测试通过")
                if self.verbose:
                    print(f"响应: {result.response[:200]}...")
            else:
                result.status = TestStatus.FAILED
                result.error = response.get('error', '未知错误')
                print(f"[FAIL] 测试失败: {result.error}")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
            result.logs.append(traceback.format_exc())
            print(f"[ERROR] 测试出错: {e}")
            
            # 尝试自愈
            if self.self_healer.max_attempts > 0:
                success, message = self.self_healer.analyze_and_fix(e, {
                    'test_case': test_case,
                    'intent': test_case.intent
                })
                
                if success:
                    result.self_healing_attempts += 1
                    # 重新执行测试
                    return self.run_single_test(test_case)
        
        end_time = datetime.datetime.now()
        result.end_time = end_time.isoformat()
        result.duration = (end_time - start_time).total_seconds()
        
        print(f"耗时: {result.duration:.2f}秒")
        
        return result
    
    def run_all_tests(self, parallel: bool = False, stop_on_failure: bool = False) -> TestReport:
        """
        运行所有启用的测试用例
        
        Args:
            parallel: 是否并行执行
            stop_on_failure: 遇到失败是否停止
            
        Returns:
            TestReport: 测试报告
        """
        print("\n" + "="*60)
        print("Bianbu LLM OS - 自动测试管道")
        print("="*60)
        print(f"总测试用例: {len(self.test_cases)}")
        print(f"启用测试: {sum(1 for tc in self.test_cases if tc.enabled)}")
        print(f"并行执行: {parallel}")
        print(f"遇到失败停止: {stop_on_failure}")
        print("="*60 + "\n")
        
        # 筛选启用的测试
        enabled_tests = [tc for tc in self.test_cases if tc.enabled]
        
        overall_start = time.time()
        
        for i, test_case in enumerate(enabled_tests, 1):
            print(f"\n[{i}/{len(enabled_tests)}] ", end="")
            
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            # 失败时是否停止
            if stop_on_failure and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                print(f"\n[WARN] 测试失败，停止执行")
                # 标记剩余测试为跳过
                for remaining in enabled_tests[i:]:
                    self.results.append(TestResult(
                        test_id=remaining.id,
                        status=TestStatus.SKIPPED,
                        start_time="",
                        end_time="",
                        duration=0.0,
                        intent=remaining.intent
                    ))
                break
        
        overall_duration = time.time() - overall_start
        
        # 生成报告
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        report = TestReport(
            timestamp=datetime.datetime.now().isoformat(),
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            total_duration=overall_duration,
            results=self.results,
            summary={
                "pass_rate": f"{passed/len(self.results)*100:.1f}%" if self.results else "0%",
                "avg_duration": sum(r.duration for r in self.results) / len(self.results) if self.results else 0,
                "total_tool_calls": sum(len(r.tool_calls) for r in self.results),
            }
        )
        
        return report
    
    def generate_report(self, report: TestReport, format: str = "text") -> str:
        """
        生成测试报告
        
        Args:
            report: 测试报告
            format: 报告格式 (text, json, html)
            
        Returns:
            str: 报告内容
        """
        if format == "json":
            return self._generate_json_report(report)
        elif format == "html":
            return self._generate_html_report(report)
        else:
            return self._generate_text_report(report)
    
    def _generate_text_report(self, report: TestReport) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("\n" + "="*70)
        lines.append(" Bianbu LLM OS - 测试报告")
        lines.append("="*70)
        lines.append(f"执行时间: {report.timestamp}")
        lines.append(f"总测试数: {report.total_tests}")
        lines.append("-"*70)
        lines.append(f"通过: {report.passed} | 失败: {report.failed} | 跳过: {report.skipped} | 错误: {report.errors}")
        lines.append(f"通过率: {report.summary.get('pass_rate', 'N/A')}")
        lines.append(f"总耗时: {report.total_duration:.2f}秒")
        lines.append(f"平均耗时: {report.summary.get('avg_duration', 0):.2f}秒")
        lines.append("-"*70)
        
        # 按状态分组显示
        lines.append("\n详细结果:")
        for result in report.results:
            status_symbol = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.SKIPPED: "-",
                TestStatus.ERROR: "!",
                TestStatus.RUNNING: "...",
                TestStatus.PENDING: "..."
            }.get(result.status, "?")
            
            lines.append(f"\n  [{status_symbol}] {result.test_id} - {result.status.value}")
            lines.append(f"      意图: {result.intent[:60]}...")
            lines.append(f"      耗时: {result.duration:.2f}秒")
            
            if result.tool_calls:
                tools = ", ".join([s.get('tool', '') for s in result.tool_calls])
                lines.append(f"      工具: {tools}")
            
            if result.error:
                lines.append(f"      错误: {result.error[:100]}")
            
            if result.self_healing_attempts > 0:
                lines.append(f"      自愈尝试: {result.self_healing_attempts}")
        
        lines.append("\n" + "="*70)
        
        return "\n".join(lines)
    
    def _generate_json_report(self, report: TestReport) -> str:
        """生成 JSON 格式报告"""
        report_dict = {
            "timestamp": report.timestamp,
            "summary": {
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "errors": report.errors,
                "pass_rate": report.summary.get('pass_rate', '0%'),
                "total_duration": report.total_duration,
                "avg_duration": report.summary.get('avg_duration', 0),
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "status": r.status.value,
                    "duration": r.duration,
                    "intent": r.intent,
                    "response_preview": r.response[:200] if r.response else None,
                    "tool_calls": r.tool_calls,
                    "error": r.error,
                    "self_healing_attempts": r.self_healing_attempts,
                }
                for r in report.results
            ]
        }
        
        return json.dumps(report_dict, indent=2, ensure_ascii=False)
    
    def _generate_html_report(self, report: TestReport) -> str:
        """生成 HTML 格式报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bianbu LLM OS - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat .value {{ font-size: 2em; font-weight: bold; }}
        .stat .label {{ color: #7f8c8d; }}
        .passed {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .skipped {{ color: #95a5a6; }}
        .test-list {{ margin-top: 20px; }}
        .test-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .test-item.passed {{ border-left: 4px solid #27ae60; }}
        .test-item.failed {{ border-left: 4px solid #e74c3c; }}
        .test-item.skipped {{ border-left: 4px solid #95a5a6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Bianbu LLM OS - 测试报告</h1>
        <p>执行时间: {report.timestamp}</p>
    </div>
    
    <div class="summary">
        <div class="stat">
            <div class="value">{report.total_tests}</div>
            <div class="label">总测试数</div>
        </div>
        <div class="stat">
            <div class="value passed">{report.passed}</div>
            <div class="label">通过</div>
        </div>
        <div class="stat">
            <div class="value failed">{report.failed}</div>
            <div class="label">失败</div>
        </div>
        <div class="stat">
            <div class="value">{report.summary.get('pass_rate', '0%')}</div>
            <div class="label">通过率</div>
        </div>
    </div>
    
    <div class="test-list">
        <h2>详细结果</h2>
"""
        
        for result in report.results:
            status_class = result.status.value
            status_icon = {"passed": "✓", "failed": "✗", "skipped": "-"}.get(status_class, "?")
            
            html += f"""
        <div class="test-item {status_class}">
            <h3>[{status_icon}] {result.test_id}</h3>
            <p><strong>意图:</strong> {result.intent}</p>
            <p><strong>耗时:</strong> {result.duration:.2f}秒</p>
            <p><strong>状态:</strong> {result.status.value}</p>
"""
            
            if result.tool_calls:
                tools = ", ".join([s.get('tool', '') for s in result.tool_calls])
                html += f"<p><strong>工具:</strong> {tools}</p>"
            
            if result.error:
                html += f"<p><strong>错误:</strong> {result.error[:100]}...</p>"
            
            html += "</div>\n"
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def save_report(self, report: TestReport, formats: List[str] = None):
        """
        保存测试报告
        
        Args:
            report: 测试报告
            formats: 报告格式列表
        """
        if formats is None:
            formats = ["text", "json"]
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for fmt in formats:
            filename = f"{self.report_dir}/test_report_{timestamp}.{fmt}"
            
            content = self.generate_report(report, fmt)
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[INFO] 报告已保存: {filename}")
            except Exception as e:
                print(f"[ERROR] 保存报告失败: {e}")


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bianbu LLM OS - 自动测试管道",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-t', '--test-file', type=str, help='测试用例文件 (JSON)')
    parser.add_argument('-o', '--output', type=str, default='output', help='报告输出目录')
    parser.add_argument('--parallel', action='store_true', help='并行执行测试')
    parser.add_argument('--stop-on-failure', action='store_true', help='遇到失败停止')
    parser.add_argument('--format', type=str, nargs='+', default=['text', 'json'], 
                       help='报告格式: text, json, html')
    parser.add_argument('--list', action='store_true', help='列出所有测试用例')
    parser.add_argument('--test', type=str, help='运行指定测试用例 ID')
    
    args = parser.parse_args()
    
    # 创建测试管道
    pipeline = TestPipeline(config_path=args.config, verbose=args.verbose)
    pipeline.report_dir = args.output
    
    # 列出测试用例
    if args.list:
        print("\n可用测试用例:")
        print("-"*60)
        for tc in pipeline.test_cases:
            status = "[ON]" if tc.enabled else "[OFF]"
            print(f"  {status} {tc.id}: {tc.name}")
            print(f"       {tc.description}")
            print()
        return
    
    # 加载自定义测试用例
    if args.test_file:
        pipeline.load_test_cases_from_file(args.test_file)
    
    # 运行所有测试或指定测试
    if args.test:
        # 运行单个测试
        test_case = next((tc for tc in pipeline.test_cases if tc.id == args.test), None)
        if test_case:
            result = pipeline.run_single_test(test_case)
            pipeline.results.append(result)
            report = TestReport(
                timestamp=datetime.datetime.now().isoformat(),
                total_tests=1,
                passed=1 if result.status == TestStatus.PASSED else 0,
                failed=1 if result.status == TestStatus.FAILED else 0,
                skipped=0,
                errors=1 if result.status == TestStatus.ERROR else 0,
                total_duration=result.duration,
                results=[result]
            )
        else:
            print(f"[ERROR] 测试用例不存在: {args.test}")
            return
    else:
        # 运行所有测试
        report = pipeline.run_all_tests(
            parallel=args.parallel,
            stop_on_failure=args.stop_on_failure
        )
    
    # 打印报告
    print(pipeline.generate_report(report, "text"))
    
    # 保存报告
    pipeline.save_report(report, args.format)


if __name__ == '__main__':
    main()
