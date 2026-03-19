#!/bin/bash
#==============================================================================
# YatAIOS - 一键构建与运行脚本
# Yet Another Transformative AI OS
#
# 功能：
#   1. 自动安装依赖
#   2. 配置环境
#   3. 编译Nexa脚本
#   4. 运行测试
#   5. 启动 CLI
#
# 用法：
#   bash build_and_run.sh [选项]
#
# 选项：
#   --init          只初始化环境
#   --nexa          编译Nexa脚本
#   --test          运行测试
#   --cli           启动 CLI (默认)
#   --daemon        启动守护进程
#   --all           运行全部流程
#   --help          显示帮助
#==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} ${BOLD}$1${NC}"; }

# 打印横幅
print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}${BOLD}                                                                  ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ███╗   ███╗███████╗███████╗████████╗ ██████╗██╗      ██╗     ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ████╗ ████║██╔════╝██╔════╝╚══██╔══╝██╔════╝██║      ██║     ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ██╔████╔██║█████╗  █████╗     ██║   ██║     ██║      ██║     ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ██║╚██╔╝██║██╔══╝  ██╔══╝     ██║   ██║     ██║      ██║     ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ██║ ╚═╝ ██║███████╗███████╗   ██║   ╚██████╗███████╗███████╗${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}     ╚═╝     ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝╚══════╝╚══════╝${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}${BOLD}                                                                  ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                    ${BOLD}YatAIOS${NC}                                      ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}         ${BOLD}Yet Another Transformative AI OS${NC}                        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}         ${BOLD}Intent-Driven Operating System${NC}                           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                  ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 显示帮助
show_help() {
    echo "YatAIOS - 构建与运行脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --init          初始化环境 (安装依赖)"
    echo "  --nexa          编译Nexa脚本"
    echo "  --test          运行测试"
    echo "  --cli           启动 CLI 界面 (默认)"
    echo "  --daemon        启动守护进程"
    echo "  --all           运行全部流程"
    echo "  --help          显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 --init        # 初始化环境"
    echo "  $0 --nexa       # 编译Nexa脚本"
    echo "  $0 --test       # 运行测试"
    echo "  $0 --cli        # 启动 CLI"
    echo "  $0 --all        # 运行全部流程"
}

# 检查 Python 环境
check_python() {
    log_step "检查 Python 环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python 版本: $PYTHON_VERSION"
}

# 安装依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3-pip python3-venv python3-dev git curl sqlite3
    fi
    
    log_success "系统依赖安装完成"
}

# 创建虚拟环境并安装 Python 依赖
setup_venv() {
    log_step "设置 Python 虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虚拟环境已创建"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip -q
    
    # 安装依赖
    log_info "安装 Python 依赖..."
    
    pip install \
        langchain==0.1.20 \
        langchain-community==0.0.38 \
        openai==1.30.1 \
        anthropic==0.21.3 \
        requests==2.31.0 \
        psutil==5.9.8 \
        pyyaml==6.0.1 \
        rich==13.7.1 \
        aiofiles==23.2.1 \
        python-dotenv==1.0.1 \
        -q 2>/dev/null || true
    
    log_success "Python 依赖安装完成"
}

# 初始化目录结构
init_directories() {
    log_step "初始化目录结构..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p cache
    mkdir -p pending_tasks
    mkdir -p output
    mkdir -p tools
    mkdir -p agents
    mkdir -p docs
    
    touch logs/.gitkeep
    touch data/.gitkeep
    touch cache/.gitkeep
    touch pending_tasks/.gitkeep
    
    log_success "目录结构初始化完成"
}

# 初始化 Git
init_git() {
    log_step "初始化 Git 仓库..."
    
    if [ ! -d ".git" ]; then
        git init
        git config user.email "agent-os@bianbu.local"
        git config user.name "Bianbu LLM OS Agent"
        log_success "Git 仓库已初始化"
    else
        log_info "Git 仓库已存在"
    fi
}

# 检查配置文件
check_config() {
    log_step "检查配置文件..."
    
    if [ ! -f "config.yaml" ]; then
        log_warn "config.yaml 不存在，使用默认配置"
    else
        log_success "配置文件已就绪"
    fi
}

# 编译Nexa脚本
compile_nexa() {
    log_step "编译 Nexa 脚本..."
    
    if ! command -v nexa &> /dev/null; then
        log_warn "Nexa CLI 未安装，跳过编译"
        return 0
    fi
    
    echo ""
    echo "========================================"
    echo "  编译 Nexa 智能体脚本"
    echo "========================================"
    echo ""
    
    # 编译 YatAIOS 核心模块
    if [ -f "nexa_scripts/yatai_os_core.nx" ]; then
        nexa build nexa_scripts/yatai_os_core.nx && log_success "yatai_os_core.nx 编译成功" || log_error "yatai_os_core.nx 编译失败"
    fi
    
    # 编译 Bianbu 主模块
    if [ -f "nexa_scripts/bianbu_main.nx" ]; then
        nexa build nexa_scripts/bianbu_main.nx && log_success "bianbu_main.nx 编译成功" || log_error "bianbu_main.nx 编译失败"
    fi
    
    echo ""
    log_success "Nexa 脚本编译完成"
}

# 运行测试
run_tests() {
    log_step "运行测试..."
    
    source venv/bin/activate
    
    echo ""
    echo "========================================"
    echo "  运行自动测试"
    echo "========================================"
    echo ""
    
    python3 tests/auto_test_pipeline.py --verbose --format text --format json
    
    if [ $? -eq 0 ]; then
        log_success "测试完成"
    else
        log_warn "部分测试失败"
    fi
}

# 启动 CLI
start_cli() {
    log_step "启动 CLI 界面..."
    
    source venv/bin/activate
    
    echo ""
    echo "========================================"
    echo "  启动 YatAIOS CLI"
    echo "========================================"
    echo ""
    
    python3 cli/llmos_cli.py --verbose
}

# 启动守护进程
start_daemon() {
    log_step "启动守护进程..."
    
    source venv/bin/activate
    
    echo ""
    echo "========================================"
    echo "  启动 Bianbu LLM OS 守护进程"
    echo "========================================"
    echo ""
    
    # 在后台启动
    nohup python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.agent_daemon import AgentDaemon

agent = AgentDaemon()
print('AgentDaemon 守护进程已启动')
print(f'会话ID: {agent.start_session()}')

# 保持运行
import time
while True:
    time.sleep(1)
" > logs/daemon.log 2>&1 &
    
    DAEMON_PID=$!
    echo $DAEMON_PID > .daemon.pid
    
    log_success "守护进程已启动 (PID: $DAEMON_PID)"
    log_info "日志文件: logs/daemon.log"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    
    # 删除 __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # 删除 .pyc 文件
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "清理完成"
}

# 自检
self_check() {
    log_step "运行自检..."
    
    source venv/bin/activate
    
    echo ""
    echo "========================================"
    echo "  运行自检"
    echo "========================================"
    echo ""
    
    # 检查 Python 模块
    log_info "检查 Python 模块..."
    
    python3 -c "
import sys
modules = [
    'langchain',
    'openai',
    'anthropic',
    'requests',
    'psutil',
    'yaml',
    'rich',
    'sqlite3'
]

failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f'  ✓ {mod}')
    except ImportError as e:
        print(f'  ✗ {mod}: {e}')
        failed.append(mod)

if failed:
    print(f'\n警告: {len(failed)} 个模块导入失败')
    sys.exit(1)
else:
    print('\n所有核心模块检查通过')
" || log_warn "部分模块检查失败"
    
    # 检查项目文件
    log_info "检查项目文件..."
    
    REQUIRED_FILES=(
        "config.yaml"
        "core/agent_daemon.py"
        "tools/system_tools.py"
        "security/security_manager.py"
        "cli/llmos_cli.py"
        "tests/auto_test_pipeline.py"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file (缺失)"
            log_warn "缺少必要文件: $file"
        fi
    done
    
    log_success "自检完成"
}

# 提交代码
git_commit() {
    log_step "提交代码..."
    
    git add -A
    
    if git diff --staged --quiet; then
        log_info "没有需要提交的内容"
    else
        git commit -m "feat: 更新 Bianbu LLM OS - $(date +%Y-%m-%d)"
        log_success "代码已提交"
    fi
}

# 主函数
main() {
    print_banner
    
    MODE="cli"  # 默认模式
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                MODE="init"
                shift
                ;;
            --nexa)
                MODE="nexa"
                shift
                ;;
            --test)
                MODE="test"
                shift
                ;;
            --cli)
                MODE="cli"
                shift
                ;;
            --daemon)
                MODE="daemon"
                shift
                ;;
            --all)
                MODE="all"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "========================================"
    log_info "YatAIOS 构建系统"
    log_info "模式: $MODE"
    echo "========================================"
    echo ""
    
    case $MODE in
        init)
            check_python
            install_dependencies
            setup_venv
            init_directories
            init_git
            check_config
            self_check
            git_commit
            ;;
        nexa)
            compile_nexa
            ;;
        test)
            log_success "初始化完成!"
            ;;
        test)
            source venv/bin/activate
            check_config
            run_tests
            ;;
        cli)
            source venv/bin/activate
            check_config
            self_check
            start_cli
            ;;
        daemon)
            source venv/bin/activate
            check_config
            self_check
            start_daemon
            ;;
        all)
            check_python
            install_dependencies
            setup_venv
            init_directories
            init_git
            check_config
            self_check
            log_success "环境就绪!"
            echo ""
            run_tests
            echo ""
            git_commit
            log_success "全部流程完成!"
            ;;
    esac
    
    echo ""
    log_success "操作完成"
    echo ""
}

# 运行主函数
main "$@"
