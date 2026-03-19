#!/usr/bin/env python3
"""
Bianbu LLM OS - 长期运行服务
后台守护进程，支持持久记忆和智能体交互

使用方法:
    python agent_service.py              # 前台运行
    python agent_service.py --daemon    # 后台守护模式
    python agent_service.py --start      # 启动systemd服务
    python agent_service.py --stop       # 停止systemd服务
"""

import os
import sys
import signal
import argparse
import logging
import time
import socket
from datetime import datetime
from typing import Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
LOG_DIR = "logs"
DATA_DIR = "data"
PID_FILE = f"{DATA_DIR}/agent_service.pid"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/agent_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AgentService')


class AgentService:
    """
    Bianbu LLM OS 长期运行服务
    
    特性:
    - 持久记忆支持 (跨会话)
    - 智能体协作
    - 后台守护模式
    - systemd服务支持
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.running = False
        self.start_time = None
        self.session_count = 0
        
        # 初始化核心组件
        self._init_components()
        
        logger.info("AgentService 初始化完成")
    
    def _init_components(self):
        """初始化核心组件"""
        try:
            from core.agent_daemon import AgentDaemon
            from core.persistent_memory import PersistentMemoryStore
            
            # 初始化智能体守护进程
            self.agent = AgentDaemon(self.config_path)
            logger.info("AgentDaemon 初始化成功")
            
            # 初始化持久记忆存储
            self.memory = PersistentMemoryStore(f"{DATA_DIR}/persistent_memory.db")
            logger.info("PersistentMemoryStore 初始化成功")
            
            # 加载记忆
            self._load_memory()
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _load_memory(self):
        """加载持久记忆"""
        try:
            # 获取长期记忆
            long_term = self.memory.get_long_term_memories()
            logger.info(f"加载了 {len(long_term)} 条长期记忆")
            
            # 获取技能列表
            skills = self.memory.get_skills()
            logger.info(f"加载了 {len(skills)} 个技能")
            
        except Exception as e:
            logger.warning(f"记忆加载失败: {e}")
    
    def start(self):
        """启动服务"""
        if self.running:
            logger.warning("服务已在运行中")
            return
        
        self.running = True
        self.start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("Bianbu LLM OS 服务已启动")
        logger.info(f"启动时间: {self.start_time}")
        logger.info("=" * 50)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 主循环
        self._main_loop()
    
    def _main_loop(self):
        """主循环 - 保持服务运行"""
        while self.running:
            try:
                # 心跳检查
                self._heartbeat()
                
                # 清理过期记忆
                self._cleanup_memory()
                
                # 等待一段时间
                time.sleep(60)  # 1分钟检查一次
                
            except Exception as e:
                logger.error(f"主循环异常: {e}")
                time.sleep(10)
    
    def _heartbeat(self):
        """心跳 - 定期记录服务状态"""
        uptime = datetime.now() - self.start_time if self.start_time else "N/A"
        logger.debug(f"心跳 - 运行时间: {uptime}, 会话数: {self.session_count}")
    
    def _cleanup_memory(self):
        """清理过期记忆"""
        try:
            cleaned = self.memory.cleanup_expired()
            if cleaned > 0:
                logger.info(f"清理了 {cleaned} 条过期记忆")
        except Exception as e:
            logger.warning(f"记忆清理失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """处理退出信号"""
        logger.info(f"收到信号 {signum}，正在停止服务...")
        self.stop()
    
    def stop(self):
        """停止服务"""
        self.running = False
        logger.info("服务已停止")
        sys.exit(0)
    
    def process_request(self, user_input: str, session_id: str = None) -> dict:
        """
        处理用户请求
        
        Args:
            user_input: 用户输入
            session_id: 可选的会话ID
            
        Returns:
            处理结果字典
        """
        self.session_count += 1
        
        try:
            # 使用智能体处理
            result = self.agent.process_intent(user_input, session_id)
            
            # 存储重要交互到记忆
            self._store_interaction(user_input, result)
            
            return result
            
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_interaction(self, user_input: str, result: dict):
        """存储交互到记忆"""
        try:
            # 如果交互成功，存储为中期记忆
            if result.get('success'):
                self.memory.store_medium_term(
                    f"interaction_{self.session_count}",
                    f"User: {user_input[:100]}... | Result: {str(result)[:100]}...",
                    importance=0.5
                )
        except Exception as e:
            logger.warning(f"交互存储失败: {e}")
    
    def get_status(self) -> dict:
        """获取服务状态"""
        uptime = None
        if self.start_time:
            uptime = str(datetime.now() - self.start_time)
        
        return {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': uptime,
            'session_count': self.session_count,
            'version': '1.0.0'
        }


def create_daemon():
    """创建守护进程"""
    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}")
        sys.exit(1)
    
    # 子进程成为新会话领导者
    os.setsid()
    
    # 再次fork防止获得控制终端
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}")
        sys.exit(1)
    
    # 重定向标准文件描述符
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open(f'{LOG_DIR}/daemon.log', 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # 写入PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def start_as_daemon():
    """以后台守护模式启动"""
    create_daemon()
    service = AgentService()
    service.start()


def start_service():
    """启动systemd服务"""
    # 检查root权限
    if os.geteuid() != 0:
        print("错误: 需要root权限来管理systemd服务")
        sys.exit(1)
    
    service_content = """[Unit]
Description=Bianbu LLM OS Agent Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={cwd}
ExecStart=/usr/bin/python3 {cwd}/agent_os/agent_service.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
""".format(cwd=os.getcwd())
    
    service_path = "/etc/systemd/system/bianbu-agent.service"
    
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    os.system("systemctl daemon-reload")
    os.system("systemctl enable bianbu-agent")
    os.system("systemctl start bianbu-agent")
    print(f"服务已安装到 {service_path}")
    print("使用 'systemctl status bianbu-agent' 查看状态")


def stop_service():
    """停止systemd服务"""
    if os.geteuid() != 0:
        print("错误: 需要root权限来管理systemd服务")
        sys.exit(1)
    
    os.system("systemctl stop bianbu-agent")
    os.system("systemctl disable bianbu-agent")
    os.system("rm -f /etc/systemd/system/bianbu-agent.service")
    print("服务已停止并禁用")


def main():
    parser = argparse.ArgumentParser(description='Bianbu LLM OS Agent Service')
    parser.add_argument('--daemon', action='store_true', help='以后台守护模式运行')
    parser.add_argument('--start', action='store_true', help='安装并启动systemd服务')
    parser.add_argument('--stop', action='store_true', help='停止并禁用systemd服务')
    parser.add_argument('--status', action='store_true', help='查看服务状态')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    if args.start:
        start_service()
    elif args.stop:
        stop_service()
    elif args.status:
        # 检查PID文件
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = f.read().strip()
            print(f"服务正在运行, PID: {pid}")
        else:
            print("服务未运行")
    elif args.daemon:
        start_as_daemon()
    else:
        # 前台运行模式
        service = AgentService(args.config)
        service.start()


if __name__ == '__main__':
    main()
