# YatAIOS - Docker构建文件
# 用于在容器中运行YatAIOS (Bianbu LLM OS)
#
# 赛题：2026年全国大学生计算机系统能力大赛-操作系统设计赛
# 平台：进迭时空 K1 RISC-V AI 开发平台 (MUSE BOOK)
# 系统：Bianbu (基于Ubuntu优化的RISC-V系统)
#
# 本Dockerfile构建适用于以下场景：
# 1. 本地开发测试（在Ubuntu上模拟Bianbu环境）
# 2. CI/CD自动化测试
# 3. 容器化部署

FROM ubuntu:22.04

# 维护者信息
LABEL maintainer="YatAIOS Team"
LABEL description="YatAIOS - Intent-Driven OS for Bianbu K1 RISC-V Platform"
LABEL platform="RISC-V K1"
LABEL system="Bianbu OS"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    sqlite3 \
    htop \
    tree \
    net-tools \
    iputils-ping \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 创建虚拟环境
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install \
    langchain==0.1.20 \
    langchain-community==0.0.38 \
    openai>=1.12.0 \
    anthropic==0.21.3 \
    requests==2.31.0 \
    psutil==5.9.8 \
    pyyaml==6.0.1 \
    rich==13.7.1 \
    aiofiles==23.2.1 \
    python-dotenv==1.0.1 \
    httpx==0.27.0

# 编译Nexa脚本（如果nexa可用）
RUN if command -v nexa &> /dev/null; then \
    nexa build /app/nexa_scripts/yatai_os_core.nx || true; \
    nexa build /app/nexa_scripts/bianbu_main.nx || true; \
    fi

# 创建必要的目录
RUN mkdir -p /app/logs /app/data

# 暴露端口（如果需要远程访问）
EXPOSE 8080

# 默认命令：启动CLI
CMD ["/app/venv/bin/python3", "-m", "cli.llmos_cli"]
