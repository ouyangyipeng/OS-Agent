#!/bin/bash
#==============================================================================
# Bianbu LLM OS - 环境初始化脚本
# 自动检测 Ubuntu 22.04 环境并安装所有依赖
#==============================================================================

set -e  # 遇到错误立即退出

echo "═══════════════════════════════════════════════════════════════"
echo "  Bianbu LLM OS - 环境初始化工具 v1.0"
echo "═══════════════════════════════════════════════════════════════"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

#==============================================================================
# 1. 系统检测
#==============================================================================
log_info "检测操作系统..."

if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=$VERSION_ID
    log_info "检测到系统: $OS_NAME $OS_VERSION"
else
    log_warn "无法检测操作系统，假设为 Ubuntu/Debian 系"
    OS_NAME="Unknown"
    OS_VERSION="Unknown"
fi

# 检查是否为 Ubuntu 22.04 或兼容系统
if [[ "$OS_NAME" == "Ubuntu" ]] || [[ -f /etc/debian_version ]]; then
    log_success "系统兼容性检查通过"
else
    log_warn "非 Ubuntu 系统，某些功能可能受限"
fi

#==============================================================================
# 2. 更新软件包列表
#==============================================================================
log_info "更新软件包列表..."
sudo apt-get update -qq || log_warn "apt-get update 失败，尝试继续..."

#==============================================================================
# 3. 安装基础依赖
#==============================================================================
log_info "安装基础依赖..."

BASE_PACKAGES=(
    python3
    python3-pip
    python3-venv
    python3-dev
    git
    curl
    wget
    vim
    htop
    net-tools
    iputils-ping
    sqlite3
    build-essential
)

for pkg in "${BASE_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $pkg "; then
        log_success "$pkg 已安装"
    else
        log_info "安装 $pkg..."
        sudo apt-get install -y -qq "$pkg" 2>/dev/null || log_warn "$pkg 安装失败"
    fi
done

#==============================================================================
# 4. Python 版本检测与虚拟环境创建
#==============================================================================
log_info "检测 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

log_info "Python 版本: $PYTHON_VERSION"

if [[ $PYTHON_MAJOR -eq 3 ]] && [[ $PYTHON_MINOR -ge 8 ]]; then
    log_success "Python 版本满足要求 (>= 3.8)"
else
    log_warn "Python 版本较低，建议升级到 3.10+"
fi

# 创建虚拟环境
log_info "创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "虚拟环境创建完成"
else
    log_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
log_info "升级 pip..."
pip install --upgrade pip -q

#==============================================================================
# 5. 安装 Python 依赖包
#==============================================================================
log_info "安装 Python 依赖包..."

# 核心依赖
pip install \
    langchain==0.1.20 \
    langchain-community==0.0.38 \
    langchain-core==0.1.52 \
    openai==1.30.1 \
    httpx==0.27.0 \
    anthropic==0.21.3 \
    requests==2.31.0 \
    psutil==5.9.8 \
    ply==3.11 \
    pyyaml==6.0.1 \
    aiofiles==23.2.1 \
    watchdog==4.0.0 \
    rich==13.7.1 \
    sseclient-py==1.8.0 \
    tiktoken==0.7.0 \
    duckduckgo-search==5.0.1 \
    newspaper3k==0.2.8 \
    wikipedia==1.4.0 \
    duckdb==0.10.2 \
    sqlalchemy==2.0.30 \
    plyvel==1.5.1 \
    python-dotenv==1.0.1 \
    -q

# 安装 streamlit 用于可选的 Web UI
pip install streamlit==0.32.0 -q 2>/dev/null || log_warn "streamlit 安装失败（可选）"

log_success "所有 Python 依赖安装完成"

#==============================================================================
# 6. 创建必要目录
#==============================================================================
log_info "创建运行时目录..."
mkdir -p logs
mkdir -p data
mkdir -p cache
mkdir -p pending_tasks
mkdir -p tools
mkdir -p agents
mkdir -p output
touch logs/.gitkeep
touch data/.gitkeep
touch cache/.gitkeep
touch pending_tasks/.gitkeep
log_success "目录结构创建完成"

#==============================================================================
# 7. 验证安装
#==============================================================================
log_info "验证安装..."
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
    except ImportError:
        print(f'  ✗ {mod}')
        failed.append(mod)
if failed:
    print(f'警告: {len(failed)} 个模块导入失败')
    sys.exit(1)
print('所有核心模块验证通过')
"

if [ $? -eq 0 ]; then
    log_success "环境验证通过"
else
    log_warn "部分模块验证失败，但将继续安装"
fi

#==============================================================================
# 8. 配置 Git
#==============================================================================
log_info "配置 Git..."
if [ ! -f .git/config ]; then
    git init
    git config user.email "agent-os@bianbu.local"
    git config user.name "Bianbu LLM OS Agent"
    log_success "Git 仓库初始化完成"
fi

#==============================================================================
# 9. 创建配置文件
#==============================================================================
log_info "检查配置文件..."
if [ ! -f config.yaml ]; then
    log_warn "config.yaml 不存在，将在首次运行时自动创建"
fi

#==============================================================================
# 完成
#==============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════"
log_success "环境初始化完成!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "下一步操作:"
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 配置 LLM API 密钥: 编辑 config.yaml"
echo "  3. 启动 CLI: python3 llmos_cli.py"
echo "  4. 或运行完整测试: bash build_and_run.sh"
echo ""

# 自动进行初始 Git 提交
if [ -d .git ]; then
    log_info "进行初始 Git 提交..."
    git add -A
    git commit -m "feat: 初始化 Bianbu LLM OS 项目结构

- 创建项目目录结构 (core/tools/cli/security/tests/docs)
- 添加环境初始化脚本 init_env.sh
- 配置 Python 虚拟环境和依赖
- 创建运行时目录 (logs/data/cache/pending_tasks)

Initial commit for Bianbu LLM OS - AI Native Operating System Prototype"
    log_success "初始提交完成"
fi

exit 0
