#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 安全与权限管控模块
Security and Permission Manager

功能：
- 动态权限拦截器
- 高危操作识别与拦截
- 待审核任务队列
- 完整审计日志

Author: Bianbu LLM OS Team
"""

import os
import re
import sqlite3
import json
import hashlib
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import IntEnum
from pathlib import Path
import threading
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SecurityManager')


class PermissionLevel(IntEnum):
    """权限等级枚举"""
    BLOCKED = 0    # 完全禁止
    CRITICAL = 1   # 高危操作
    ELEVATED = 2   # 特权操作
    NORMAL = 3    # 普通操作
    TRUSTED = 4   # 可信操作


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    user_intent: str
    parsed_actions: List[Dict]
    risk_level: PermissionLevel
    requires_confirmation: bool
    confirmed: bool
    created_at: str
    status: str  # pending, approved, rejected, executed, expired


@dataclass
class AuditEntry:
    """审计日志条目"""
    timestamp: str
    task_id: str
    action: str
    risk_level: PermissionLevel
    result: str
    user确认: Optional[str] = None
    details: Optional[str] = None


class SecurityManager:
    """
    安全与权限管控中心
    
    职责：
    1. 评估操作风险等级
    2. 拦截高危操作
    3. 管理待审核任务队列
    4. 记录完整审计日志
    """
    
    # 高危操作关键词模式
    HIGH_RISK_PATTERNS = [
        (r'rm\s+-rf\s+[/"]?\s*$', PermissionLevel.BLOCKED, "递归删除根目录"),
        (r'rm\s+-rf\s+/\s', PermissionLevel.BLOCKED, "递归删除根目录"),
        (r'mkfs', PermissionLevel.BLOCKED, "格式化文件系统"),
        (r'dd\s+if=.*of=/dev/', PermissionLevel.BLOCKED, "直接写入设备"),
        (r'kill\s+-9\s*(-1|$)', PermissionLevel.CRITICAL, "强制终止关键进程"),
        (r'killall\s+-9', PermissionLevel.CRITICAL, "强制终止所有进程"),
        (r'drop\s+database', PermissionLevel.BLOCKED, "删除数据库"),
        (r'drop\s+table', PermissionLevel.CRITICAL, "删除数据表"),
        (r'truncate\s+table', PermissionLevel.CRITICAL, "清空数据表"),
        (r'shutdown\s+-h', PermissionLevel.CRITICAL, "关闭系统"),
        (r'reboot', PermissionLevel.CRITICAL, "重启系统"),
        (r'init\s+0', PermissionLevel.CRITICAL, "关闭系统"),
        (r'chmod\s+777', PermissionLevel.ELEVATED, "设置最高权限"),
        (r'chmod\s+000', PermissionLevel.CRITICAL, "移除所有权限"),
        (r'passwd\s+root', PermissionLevel.CRITICAL, "修改root密码"),
        (r'sudo\s+su', PermissionLevel.ELEVATED, "切换到root"),
        (r'eval\s+\$\(', PermissionLevel.CRITICAL, "执行动态命令"),
        (r'curl\s+.*\|\s*sh', PermissionLevel.CRITICAL, "下载并执行脚本"),
        (r'wget\s+.*\|\s*sh', PermissionLevel.CRITICAL, "下载并执行脚本"),
        (r':\(\)\{.*\}\:;', PermissionLevel.CRITICAL, "Fork炸弹"),
        (r'mount\s+--bind', PermissionLevel.ELEVATED, "绑定挂载"),
        (r'umount\s+-f', PermissionLevel.ELEVATED, "强制卸载"),
        (r'remote\s+rm', PermissionLevel.CRITICAL, "远程删除"),
        (r'format\s+\w+', PermissionLevel.BLOCKED, "格式化操作"),
    ]
    
    # 操作类型到风险等级的映射
    OPERATION_RISK_MAP = {
        # 文件操作
        'file_read': PermissionLevel.NORMAL,
        'file_write': PermissionLevel.ELEVATED,
        'file_delete': PermissionLevel.CRITICAL,
        'file_search': PermissionLevel.NORMAL,
        'file_copy': PermissionLevel.NORMAL,
        'file_move': PermissionLevel.ELEVATED,
        'file_create': PermissionLevel.NORMAL,
        'file_append': PermissionLevel.NORMAL,
        
        # 进程操作
        'process_list': PermissionLevel.NORMAL,
        'process_info': PermissionLevel.NORMAL,
        'process_kill': PermissionLevel.CRITICAL,
        'process_restart': PermissionLevel.ELEVATED,
        
        # 网络操作
        'network_info': PermissionLevel.TRUSTED,
        'network_ping': PermissionLevel.TRUSTED,
        'network_scan': PermissionLevel.ELEVATED,
        'network_config': PermissionLevel.ELEVATED,
        'firewall_rule': PermissionLevel.CRITICAL,
        
        # 包管理
        'package_install': PermissionLevel.ELEVATED,
        'package_remove': PermissionLevel.CRITICAL,
        'package_update': PermissionLevel.ELEVATED,
        'package_search': PermissionLevel.TRUSTED,
        
        # 系统操作
        'system_info': PermissionLevel.TRUSTED,
        'system_reboot': PermissionLevel.CRITICAL,
        'system_shutdown': PermissionLevel.CRITICAL,
        'user_create': PermissionLevel.ELEVATED,
        'user_delete': PermissionLevel.CRITICAL,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化安全管理器"""
        self.config = config or {}
        self.pending_db_path = self.config.get('pending_tasks', {}).get('db_path', 'data/pending_tasks.db')
        self.audit_log_path = self.config.get('audit', {}).get('log_path', 'logs/security_audit.log')
        self._lock = threading.Lock()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.pending_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        logger.info("SecurityManager 初始化完成")
    
    def _init_database(self):
        """初始化待审核任务数据库"""
        with self._lock:
            conn = sqlite3.connect(self.pending_db_path)
            cursor = conn.cursor()
            
            # 创建待审核任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_tasks (
                    task_id TEXT PRIMARY KEY,
                    user_intent TEXT NOT NULL,
                    parsed_actions TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    requires_confirmation INTEGER NOT NULL,
                    confirmed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    user_id TEXT,
                    session_id TEXT
                )
            ''')
            
            # 创建审计日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    task_id TEXT,
                    action TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    user_confirm TEXT,
                    details TEXT,
                    session_id TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def assess_risk(self, action: str, params: Optional[Dict] = None) -> Tuple[PermissionLevel, str]:
        """
        评估操作风险等级
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            (风险等级, 风险描述)
        """
        params = params or {}
        params_str = json.dumps(params, ensure_ascii=False).lower()
        full_text = f"{action} {params_str}"
        
        # 检查高危关键词模式
        for pattern, level, description in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                logger.warning(f"检测到高危操作: {action} - {description}")
                return level, description
        
        # 检查操作类型映射
        if action in self.OPERATION_RISK_MAP:
            return self.OPERATION_RISK_MAP[action], f"操作类型: {action}"
        
        # 默认普通操作
        return PermissionLevel.NORMAL, "标准操作"
    
    def evaluate_task(self, user_intent: str, parsed_actions: List[Dict]) -> TaskContext:
        """
        评估任务是否需要拦截
        
        Args:
            user_intent: 用户原始意图
            parsed_actions: 解析后的操作列表
            
        Returns:
            TaskContext: 任务上下文
        """
        task_id = self._generate_task_id(user_intent)
        max_risk = PermissionLevel.TRUSTED
        risk_descriptions = []
        
        for action_item in parsed_actions:
            action = action_item.get('action', action_item.get('name', ''))
            params = action_item.get('params', {})
            risk_level, description = self.assess_risk(action, params)
            
            if risk_level < max_risk:
                max_risk = risk_level
            risk_descriptions.append(description)
        
        requires_confirmation = max_risk <= PermissionLevel.CRITICAL
        
        context = TaskContext(
            task_id=task_id,
            user_intent=user_intent,
            parsed_actions=parsed_actions,
            risk_level=max_risk,
            requires_confirmation=requires_confirmation,
            confirmed=False,
            created_at=datetime.datetime.now().isoformat(),
            status='pending' if requires_confirmation else 'executed'
        )
        
        # 记录审计日志
        self._log_audit(
            task_id=task_id,
            action=f"任务评估: {user_intent}",
            risk_level=max_risk,
            result='需要确认' if requires_confirmation else '直接执行',
            details='; '.join(risk_descriptions)
        )
        
        return context
    
    def should_block(self, task_context: TaskContext) -> bool:
        """
        判断任务是否应该被拦截
        
        Args:
            task_context: 任务上下文
            
        Returns:
            bool: 是否拦截
        """
        # BLOCKED 级别必须拦截
        if task_context.risk_level == PermissionLevel.BLOCKED:
            return True
        
        # CRITICAL 级别需要用户确认
        if task_context.risk_level == PermissionLevel.CRITICAL:
            return not task_context.confirmed
        
        return False
    
    def add_to_pending(self, task_context: TaskContext, session_id: Optional[str] = None) -> bool:
        """
        将任务添加到待审核队列
        
        Args:
            task_context: 任务上下文
            session_id: 会话ID
            
        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO pending_tasks 
                    (task_id, user_intent, parsed_actions, risk_level, 
                     requires_confirmation, created_at, status, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_context.task_id,
                    task_context.user_intent,
                    json.dumps(task_context.parsed_actions, ensure_ascii=False),
                    int(task_context.risk_level),
                    1 if task_context.requires_confirmation else 0,
                    task_context.created_at,
                    'pending',
                    session_id
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"任务 {task_context.task_id} 已加入待审核队列")
                return True
                
            except Exception as e:
                logger.error(f"添加待审核任务失败: {e}")
                return False
    
    def confirm_task(self, task_id: str) -> bool:
        """
        确认执行待审核任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否确认成功
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE pending_tasks 
                    SET confirmed = 1, status = 'approved'
                    WHERE task_id = ?
                ''', (task_id,))
                
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                
                if affected > 0:
                    self._log_audit(
                        task_id=task_id,
                        action="任务确认",
                        risk_level=PermissionLevel.CRITICAL,
                        result="用户已确认"
                    )
                    logger.info(f"任务 {task_id} 已确认执行")
                    return True
                return False
                
            except Exception as e:
                logger.error(f"确认任务失败: {e}")
                return False
    
    def reject_task(self, task_id: str) -> bool:
        """
        拒绝待审核任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否拒绝成功
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE pending_tasks 
                    SET status = 'rejected'
                    WHERE task_id = ?
                ''', (task_id,))
                
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                
                if affected > 0:
                    self._log_audit(
                        task_id=task_id,
                        action="任务拒绝",
                        risk_level=PermissionLevel.CRITICAL,
                        result="用户已拒绝"
                    )
                    logger.info(f"任务 {task_id} 已拒绝")
                    return True
                return False
                
            except Exception as e:
                logger.error(f"拒绝任务失败: {e}")
                return False
    
    def get_pending_tasks(self, session_id: Optional[str] = None) -> List[TaskContext]:
        """
        获取待审核任务列表
        
        Args:
            session_id: 可选的会话ID过滤
            
        Returns:
            List[TaskContext]: 待审核任务列表
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                if session_id:
                    cursor.execute('''
                        SELECT task_id, user_intent, parsed_actions, risk_level,
                               requires_confirmation, confirmed, created_at, status
                        FROM pending_tasks
                        WHERE status = 'pending' AND session_id = ?
                        ORDER BY created_at DESC
                    ''', (session_id,))
                else:
                    cursor.execute('''
                        SELECT task_id, user_intent, parsed_actions, risk_level,
                               requires_confirmation, confirmed, created_at, status
                        FROM pending_tasks
                        WHERE status = 'pending'
                        ORDER BY created_at DESC
                    ''')
                
                rows = cursor.fetchall()
                conn.close()
                
                tasks = []
                for row in rows:
                    tasks.append(TaskContext(
                        task_id=row[0],
                        user_intent=row[1],
                        parsed_actions=json.loads(row[2]),
                        risk_level=PermissionLevel(row[3]),
                        requires_confirmation=bool(row[4]),
                        confirmed=bool(row[5]),
                        created_at=row[6],
                        status=row[7]
                    ))
                
                return tasks
                
            except Exception as e:
                logger.error(f"获取待审核任务失败: {e}")
                return []
    
    def cleanup_expired_tasks(self, hours: int = 72) -> int:
        """
        清理过期任务
        
        Args:
            hours: 过期小时数
            
        Returns:
            int: 清理的任务数量
        """
        with self._lock:
            try:
                cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
                
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE pending_tasks
                    SET status = 'expired'
                    WHERE status = 'pending' AND created_at < ?
                ''', (cutoff.isoformat(),))
                
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                
                if affected > 0:
                    logger.info(f"已清理 {affected} 个过期任务")
                
                return affected
                
            except Exception as e:
                logger.error(f"清理过期任务失败: {e}")
                return 0
    
    def _generate_task_id(self, intent: str) -> str:
        """生成任务ID"""
        timestamp = datetime.datetime.now().isoformat()
        hash_input = f"{intent}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def _log_audit(self, task_id: str, action: str, risk_level: PermissionLevel,
                   result: str, user_confirm: Optional[str] = None,
                   details: Optional[str] = None, session_id: Optional[str] = None):
        """记录审计日志"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_log 
                    (timestamp, task_id, action, risk_level, result, user_confirm, details, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now().isoformat(),
                    task_id,
                    action,
                    int(risk_level),
                    result,
                    user_confirm,
                    details,
                    session_id
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"记录审计日志失败: {e}")
    
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        """
        获取审计日志
        
        Args:
            limit: 返回条数限制
            
        Returns:
            List[AuditEntry]: 审计日志列表
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.pending_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, task_id, action, risk_level, result, 
                           user_confirm, details
                    FROM audit_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                entries = []
                for row in rows:
                    entries.append(AuditEntry(
                        timestamp=row[0],
                        task_id=row[1],
                        action=row[2],
                        risk_level=PermissionLevel(row[3]),
                        result=row[4],
                        user确认=row[5],
                        details=row[6]
                    ))
                
                return entries
                
            except Exception as e:
                logger.error(f"获取审计日志失败: {e}")
                return []
    
    def check_operation(self, operation: str, params: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        检查操作是否可以执行
        
        Args:
            operation: 操作名称
            params: 操作参数
            
        Returns:
            (是否允许, 消息)
        """
        risk_level, description = self.assess_risk(operation, params)
        
        if risk_level == PermissionLevel.BLOCKED:
            return False, f"操作被禁止: {description}"
        
        if risk_level == PermissionLevel.CRITICAL:
            task_context = TaskContext(
                task_id=self._generate_task_id(f"{operation}_{params}"),
                user_intent=f"{operation} {params}",
                parsed_actions=[{'action': operation, 'params': params}],
                risk_level=risk_level,
                requires_confirmation=True,
                confirmed=False,
                created_at=datetime.datetime.now().isoformat(),
                status='pending'
            )
            self.add_to_pending(task_context)
            return False, f"高危操作已挂起，等待确认: {description}"
        
        return True, f"操作允许 (风险等级: {risk_level.name})"


class PermissionGuard:
    """
    权限守卫 - 装饰器模式
    
    用法:
        @PermissionGuard.check
        def dangerous_operation(self, param):
            pass
    """
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
    
    def check(self, func):
        """装饰器：检查操作权限"""
        def wrapper(*args, **kwargs):
            operation = func.__name__
            allowed, message = self.security_manager.check_operation(operation, kwargs)
            
            if not allowed:
                logger.warning(f"操作 {operation} 被拦截: {message}")
                raise PermissionError(message)
            
            return func(*args, **kwargs)
        return wrapper


# 便捷函数
def create_security_manager(config_path: str = 'config.yaml') -> SecurityManager:
    """创建安全管理器实例"""
    import yaml
    
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    
    security_config = config.get('security', {})
    return SecurityManager(security_config)


if __name__ == '__main__':
    # 演示用法
    sm = SecurityManager()
    
    # 测试风险评估
    test_cases = [
        ('file_read', {'path': '/home/user/doc.txt'}),
        ('process_kill', {'pid': 1234}),
        ('file_delete', {'path': '/tmp/test.txt'}),
    ]
    
    print("\n=== 风险评估测试 ===")
    for op, params in test_cases:
        level, desc = sm.assess_risk(op, params)
        print(f"{op}: {level.name} - {desc}")
    
    print("\n=== 待审核任务列表 ===")
    for task in sm.get_pending_tasks():
        print(f"  {task.task_id}: {task.user_intent[:50]}...")
    
    print("\n=== 安全检查 ===")
    allowed, msg = sm.check_operation('file_read', {'path': '/etc/passwd'})
    print(f"file_read: {allowed} - {msg}")
    
    allowed, msg = sm.check_operation('process_kill', {'pid': -1})
    print(f"process_kill: {allowed} - {msg}")
