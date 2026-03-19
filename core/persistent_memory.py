#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bianbu LLM OS - 持久记忆模块
Persistent Memory Store

功能：
- 跨会话持久记忆存储
- 记忆分级（短期/中期/长期/技能）
- 用户偏好学习
- 记忆搜索和检索

设计理念：
参考 OpenCLAW 的长期助手概念，让智能体具备持续学习和记忆的能力。

Author: Bianbu LLM OS Team
"""

import os
import json
import sqlite3
import threading
import datetime
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PersistentMemory')


class MemoryLevel(Enum):
    """记忆层级"""
    SHORT_TERM = "short_term"      # 当前会话
    MEDIUM_TERM = "medium_term"    # 最近任务 (7天)
    LONG_TERM = "long_term"        # 重要事实 (永久)
    SKILL = "skill"                # 学会的技能


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    level: MemoryLevel
    key: str
    value: str
    created_at: str
    last_accessed: str
    access_count: int
    importance: float  # 0.0 - 1.0
    tags: List[str]
    metadata: Dict


@dataclass
class UserPreference:
    """用户偏好"""
    user_id: str
    name: Optional[str] = None
    language: str = "中文"
    timezone: str = "Asia/Shanghai"
    favorite_dirs: List[str] = field(default_factory=list)
    preferred_response_length: str = "medium"  # short, medium, long
    command_style: str = "natural"  # natural, concise, verbose
    created_at: str = ""
    updated_at: str = ""


class PersistentMemoryStore:
    """
    持久记忆存储
    
    实现跨会话的记忆持久化，使智能体成为真正的长期助手。
    
    记忆层级：
    1. 短期记忆 (Short-term): 当前会话的消息，高频访问
    2. 中期记忆 (Medium-term): 最近7天的任务和上下文
    3. 长期记忆 (Long-term): 重要的用户事实和偏好
    4. 技能记忆 (Skill): 学会的技能和使用经验
    """
    
    def __init__(self, db_path: str = "data/persistent_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.RLock()
        
        # 初始化数据库
        self._init_database()
        
        # 加载用户偏好
        self.user_preferences: Dict[str, UserPreference] = {}
        self._load_user_preferences()
        
        logger.info(f"PersistentMemoryStore 初始化完成，数据库: {db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 记忆主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    importance REAL DEFAULT 0.5,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    user_id TEXT DEFAULT 'default'
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_level ON memories(level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)')
            
            # 用户偏好表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    language TEXT DEFAULT '中文',
                    timezone TEXT DEFAULT 'Asia/Shanghai',
                    favorite_dirs TEXT DEFAULT '[]',
                    preferred_response_length TEXT DEFAULT 'medium',
                    command_style TEXT DEFAULT 'natural',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 技能表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT 'default',
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    proficiency REAL DEFAULT 0.5,
                    last_used TEXT,
                    use_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # 重要事实表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS important_facts (
                    fact_id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT 'default',
                    fact_type TEXT,
                    subject TEXT,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    last_verified TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
    
    # =========================================================================
    # 记忆基础操作
    # =========================================================================
    
    def store(self, key: str, value: Any, level: MemoryLevel = MemoryLevel.MEDIUM_TERM,
              importance: float = 0.5, tags: List[str] = None,
              user_id: str = "default") -> bool:
        """
        存储记忆
        
        Args:
            key: 记忆键
            value: 记忆值
            level: 记忆层级
            importance: 重要性 (0.0-1.0)
            tags: 标签列表
            user_id: 用户ID
            
        Returns:
            bool: 是否存储成功
        """
        with self._lock:
            try:
                memory_id = self._generate_id(key, user_id)
                now = datetime.datetime.now().isoformat()
                tags = tags or []
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO memories
                    (id, level, key, value, created_at, last_accessed, access_count,
                     importance, tags, metadata, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    memory_id,
                    level.value,
                    key,
                    json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
                    now, now, 0, importance,
                    json.dumps(tags),
                    '{}',
                    user_id
                ))
                
                conn.commit()
                conn.close()
                
                logger.debug(f"记忆存储成功: {key} ({level.value})")
                return True
                
            except Exception as e:
                logger.error(f"存储记忆失败: {e}")
                return False
    
    def retrieve(self, key: str, user_id: str = "default") -> Optional[Any]:
        """
        检索记忆
        
        Args:
            key: 记忆键
            user_id: 用户ID
            
        Returns:
            记忆值，如果不存在返回 None
        """
        with self._lock:
            try:
                memory_id = self._generate_id(key, user_id)
                now = datetime.datetime.now().isoformat()
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE memories
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id = ? AND user_id = ?
                ''', (now, memory_id, user_id))
                
                cursor.execute('''
                    SELECT value FROM memories
                    WHERE id = ? AND user_id = ?
                ''', (memory_id, user_id))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    try:
                        return json.loads(row[0])
                    except:
                        return row[0]
                
                return None
                
            except Exception as e:
                logger.error(f"检索记忆失败: {e}")
                return None
    
    def search(self, query: str, level: MemoryLevel = None,
               user_id: str = "default", limit: int = 10) -> List[MemoryEntry]:
        """
        搜索记忆
        
        Args:
            query: 搜索关键词
            level: 可选的层级过滤
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            List[MemoryEntry]: 匹配的记忆条目列表
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                sql = '''
                    SELECT id, level, key, value, created_at, last_accessed,
                           access_count, importance, tags, metadata
                    FROM memories
                    WHERE user_id = ? AND (key LIKE ? OR value LIKE ?)
                '''
                params = [user_id, f'%{query}%', f'%{query}%']
                
                if level:
                    sql += ' AND level = ?'
                    params.append(level.value)
                
                sql += ' ORDER BY importance DESC, access_count DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    results.append(MemoryEntry(
                        id=row[0],
                        level=MemoryLevel(row[1]),
                        key=row[2],
                        value=row[3],
                        created_at=row[4],
                        last_accessed=row[5],
                        access_count=row[6],
                        importance=row[7],
                        tags=json.loads(row[8]),
                        metadata=json.loads(row[9])
                    ))
                
                return results
                
            except Exception as e:
                logger.error(f"搜索记忆失败: {e}")
                return []
    
    def delete(self, key: str, user_id: str = "default") -> bool:
        """删除记忆"""
        with self._lock:
            try:
                memory_id = self._generate_id(key, user_id)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memories WHERE id = ? AND user_id = ?',
                             (memory_id, user_id))
                conn.commit()
                conn.close()
                
                return True
                
            except Exception as e:
                logger.error(f"删除记忆失败: {e}")
                return False
    
    # =========================================================================
    # 记忆层级管理
    # =========================================================================
    
    def store_short_term(self, key: str, value: Any, user_id: str = "default") -> bool:
        """存储短期记忆（会话级）"""
        return self.store(key, value, MemoryLevel.SHORT_TERM, importance=0.3,
                         user_id=user_id)
    
    def store_medium_term(self, key: str, value: Any, importance: float = 0.5,
                          user_id: str = "default") -> bool:
        """存储中期记忆（7天）"""
        return self.store(key, value, MemoryLevel.MEDIUM_TERM, importance=importance,
                         user_id=user_id)
    
    def store_long_term(self, key: str, value: Any, importance: float = 0.8,
                        tags: List[str] = None, user_id: str = "default") -> bool:
        """存储长期记忆（永久）"""
        return self.store(key, value, MemoryLevel.LONG_TERM, importance=importance,
                         tags=tags, user_id=user_id)
    
    def get_recent_memories(self, user_id: str = "default", limit: int = 20) -> List[MemoryEntry]:
        """获取最近的中期记忆"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, level, key, value, created_at, last_accessed,
                           access_count, importance, tags, metadata
                    FROM memories
                    WHERE user_id = ? AND level = ?
                    ORDER BY last_accessed DESC
                    LIMIT ?
                ''', (user_id, MemoryLevel.MEDIUM_TERM.value, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    results.append(MemoryEntry(
                        id=row[0],
                        level=MemoryLevel(row[1]),
                        key=row[2],
                        value=row[3],
                        created_at=row[4],
                        last_accessed=row[5],
                        access_count=row[6],
                        importance=row[7],
                        tags=json.loads(row[8]),
                        metadata=json.loads(row[9])
                    ))
                
                return results
                
            except Exception as e:
                logger.error(f"获取最近记忆失败: {e}")
                return []
    
    def get_long_term_memories(self, user_id: str = "default") -> List[MemoryEntry]:
        """获取所有长期记忆"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, level, key, value, created_at, last_accessed,
                           access_count, importance, tags, metadata
                    FROM memories
                    WHERE user_id = ? AND level = ?
                    ORDER BY importance DESC
                ''', (user_id, MemoryLevel.LONG_TERM.value))
                
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    results.append(MemoryEntry(
                        id=row[0],
                        level=MemoryLevel(row[1]),
                        key=row[2],
                        value=row[3],
                        created_at=row[4],
                        last_accessed=row[5],
                        access_count=row[6],
                        importance=row[7],
                        tags=json.loads(row[8]),
                        metadata=json.loads(row[9])
                    ))
                
                return results
                
            except Exception as e:
                logger.error(f"获取长期记忆失败: {e}")
                return []
    
    # =========================================================================
    # 记忆清理
    # =========================================================================
    
    def cleanup_medium_term(self, days: int = 7) -> int:
        """
        清理过期中期记忆
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的记忆数量
        """
        with self._lock:
            try:
                cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM memories
                    WHERE level = ? AND created_at < ?
                ''', (MemoryLevel.MEDIUM_TERM.value, cutoff.isoformat()))
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                if deleted > 0:
                    logger.info(f"已清理 {deleted} 条过期中期记忆")
                
                return deleted
                
            except Exception as e:
                logger.error(f"清理过期记忆失败: {e}")
                return 0
    
    def cleanup_low_importance(self, threshold: float = 0.1) -> int:
        """清理低重要性记忆"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM memories
                    WHERE importance < ? AND access_count < 3
                ''', (threshold,))
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                if deleted > 0:
                    logger.info(f"已清理 {deleted} 条低重要性记忆")
                
                return deleted
                
            except Exception as e:
                logger.error(f"清理低重要性记忆失败: {e}")
                return 0
    
    # =========================================================================
    # 用户偏好
    # =========================================================================
    
    def _load_user_preferences(self):
        """加载用户偏好"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_preferences')
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                self.user_preferences[row[0]] = UserPreference(
                    user_id=row[0],
                    name=row[1],
                    language=row[2],
                    timezone=row[3],
                    favorite_dirs=json.loads(row[4]),
                    preferred_response_length=row[5],
                    command_style=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                
        except Exception as e:
            logger.error(f"加载用户偏好失败: {e}")
    
    def get_user_preference(self, user_id: str = "default") -> UserPreference:
        """获取用户偏好"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreference(
                user_id=user_id,
                created_at=datetime.datetime.now().isoformat(),
                updated_at=datetime.datetime.now().isoformat()
            )
            self._save_user_preference(self.user_preferences[user_id])
        
        return self.user_preferences[user_id]
    
    def update_user_preference(self, user_id: str = "default", **kwargs) -> bool:
        """更新用户偏好"""
        pref = self.get_user_preference(user_id)
        
        for key, value in kwargs.items():
            if hasattr(pref, key):
                setattr(pref, key, value)
        
        pref.updated_at = datetime.datetime.now().isoformat()
        return self._save_user_preference(pref)
    
    def _save_user_preference(self, pref: UserPreference) -> bool:
        """保存用户偏好"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (user_id, name, language, timezone, favorite_dirs,
                 preferred_response_length, command_style, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pref.user_id, pref.name, pref.language, pref.timezone,
                json.dumps(pref.favorite_dirs),
                pref.preferred_response_length, pref.command_style,
                pref.created_at, pref.updated_at
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")
            return False
    
    # =========================================================================
    # 技能管理
    # =========================================================================
    
    def learn_skill(self, skill_id: str, name: str, description: str = "",
                    category: str = "general", metadata: Dict = None,
                    user_id: str = "default") -> bool:
        """学习新技能"""
        try:
            now = datetime.datetime.now().isoformat()
            metadata = metadata or {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO skills
                (skill_id, user_id, name, description, category, proficiency,
                 last_used, use_count, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (skill_id, user_id, name, description, category, 0.5,
                  now, 0, now, json.dumps(metadata)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"技能已学习: {name}")
            return True
            
        except Exception as e:
            logger.error(f"学习技能失败: {e}")
            return False
    
    def update_skill_proficiency(self, skill_id: str, proficiency_delta: float,
                                user_id: str = "default") -> bool:
        """更新技能熟练度"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE skills
                SET proficiency = MIN(1.0, MAX(0.0, proficiency + ?)),
                    use_count = use_count + 1,
                    last_used = ?
                WHERE skill_id = ? AND user_id = ?
            ''', (proficiency_delta, datetime.datetime.now().isoformat(),
                  skill_id, user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"更新技能熟练度失败: {e}")
            return False
    
    def get_skills(self, user_id: str = "default", category: str = None) -> List[Dict]:
        """获取用户技能列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT skill_id, name, description, category, proficiency,
                           last_used, use_count
                    FROM skills
                    WHERE user_id = ? AND category = ?
                    ORDER BY proficiency DESC
                ''', (user_id, category))
            else:
                cursor.execute('''
                    SELECT skill_id, name, description, category, proficiency,
                           last_used, use_count
                    FROM skills
                    WHERE user_id = ?
                    ORDER BY proficiency DESC
                ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "skill_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "proficiency": row[4],
                    "last_used": row[5],
                    "use_count": row[6]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"获取技能列表失败: {e}")
            return []
    
    # =========================================================================
    # 重要事实
    # =========================================================================
    
    def store_fact(self, fact_type: str, subject: str, content: str,
                   confidence: float = 1.0, source: str = "",
                   user_id: str = "default") -> bool:
        """存储重要事实"""
        try:
            fact_id = self._generate_id(f"fact_{subject}", user_id)
            now = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO important_facts
                (fact_id, user_id, fact_type, subject, content, confidence,
                 source, created_at, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fact_id, user_id, fact_type, subject, content, confidence,
                  source, now, now))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"存储重要事实失败: {e}")
            return False
    
    def get_facts(self, user_id: str = "default", fact_type: str = None) -> List[Dict]:
        """获取重要事实"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if fact_type:
                cursor.execute('''
                    SELECT fact_id, fact_type, subject, content, confidence, source, created_at
                    FROM important_facts
                    WHERE user_id = ? AND fact_type = ?
                    ORDER BY confidence DESC
                ''', (user_id, fact_type))
            else:
                cursor.execute('''
                    SELECT fact_id, fact_type, subject, content, confidence, source, created_at
                    FROM important_facts
                    WHERE user_id = ?
                    ORDER BY confidence DESC
                ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "fact_id": row[0],
                    "fact_type": row[1],
                    "subject": row[2],
                    "content": row[3],
                    "confidence": row[4],
                    "source": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"获取重要事实失败: {e}")
            return []
    
    # =========================================================================
    # 工具方法
    # =========================================================================
    
    def _generate_id(self, key: str, user_id: str) -> str:
        """生成记忆ID"""
        hash_input = f"{user_id}:{key}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def get_memory_stats(self, user_id: str = "default") -> Dict:
        """获取记忆统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            for level in MemoryLevel:
                cursor.execute('''
                    SELECT COUNT(*) FROM memories
                    WHERE user_id = ? AND level = ?
                ''', (user_id, level.value))
                stats[level.value] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM skills WHERE user_id = ?', (user_id,))
            stats['skills_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM important_facts WHERE user_id = ?', (user_id,))
            stats['facts_count'] = cursor.fetchone()[0]
            
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {}
    
    def export_memories(self, user_id: str = "default") -> Dict:
        """导出所有记忆数据"""
        return {
            "user_id": user_id,
            "exported_at": datetime.datetime.now().isoformat(),
            "memories": {
                "short_term": self.get_memory_stats(user_id).get("short_term", 0),
                "medium_term": self.get_recent_memories(user_id, limit=1000),
                "long_term": self.get_long_term_memories(user_id)
            },
            "skills": self.get_skills(user_id),
            "facts": self.get_facts(user_id),
            "preferences": asdict(self.get_user_preference(user_id))
        }


def create_persistent_memory(db_path: str = "data/persistent_memory.db") -> PersistentMemoryStore:
    """创建持久记忆存储实例"""
    return PersistentMemoryStore(db_path)


if __name__ == '__main__':
    # 演示用法
    print("=== PersistentMemory 演示 ===\n")
    
    memory = PersistentMemoryStore()
    
    # 存储测试
    print("1. 存储测试记忆...")
    memory.store_short_term("test_key", "test_value")
    memory.store_medium_term("user_name", "张三", importance=0.8)
    memory.store_long_term("user_company", "进迭时空", importance=0.9,
                          tags=["工作", "公司"])
    
    # 检索测试
    print("2. 检索测试...")
    value = memory.retrieve("test_key")
    print(f"   检索结果: {value}")
    
    # 搜索测试
    print("3. 搜索测试...")
    results = memory.search("张三")
    print(f"   找到 {len(results)} 条相关记忆")
    
    # 统计信息
    print("4. 记忆统计...")
    stats = memory.get_memory_stats()
    print(f"   短期记忆: {stats.get('short_term', 0)}")
    print(f"   中期记忆: {stats.get('medium_term', 0)}")
    print(f"   长期记忆: {stats.get('long_term', 0)}")
    
    # 学习技能
    print("5. 技能学习...")
    memory.learn_skill("skill.file.search", "文件搜索", "搜索文件和文件夹", "文件管理")
    
    skills = memory.get_skills()
    print(f"   已学习 {len(skills)} 个技能")
    
    print("\n=== 演示完成 ===")
