# YatAIOS on Bianbu OS

本文档说明如何在Bianbu操作系统上运行YatAIOS。

## 赛题信息

- **大赛名称**: 2026年全国大学生计算机系统能力大赛-操作系统设计赛
- **赛道**: OS功能挑战赛道
- **难度等级**: A (学术型)
- **维护单位**: 进迭时空（杭州）科技有限公司

## 目标平台

### 进迭时空 K1 RISC-V AI 开发平台 (MUSE BOOK)

- 架构: RISC-V 64位
- 特性: AI 加速
- 系统: Bianbu (基于 Ubuntu 优化)

### 系统获取

从进迭时空官网获取Bianbu系统镜像和文档：
- https://www.spacemit.com/community/document

## 在Bianbu上运行YatAIOS

### 方式一：直接在Bianbu系统上运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd agent-os

# 2. 初始化环境
bash init_env.sh

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 配置API密钥（如果使用远程API）
export OPENAI_API_KEY="your-api-key"
# 或直接编辑 config.yaml

# 5. 启动CLI
python3 -m cli.llmos_cli
```

### 方式二：使用一键构建脚本

```bash
# 初始化并运行
bash build_and_run.sh --all

# 或分步执行
bash build_and_run.sh --init    # 初始化环境
bash build_and_run.sh --nexa    # 编译Nexa脚本
bash build_and_run.sh --cli     # 启动CLI
```

### 方式三：使用Docker（模拟环境）

如果暂时无法访问K1 RISC-V硬件，可以使用Docker容器在x86_64平台上模拟：

```bash
# 进入项目根目录
cd agent-os

# 构建Docker镜像（基于Ubuntu 22.04 x86_64）
docker build -t yataios .

# 运行容器
docker run -it yataios

# 带API密钥运行
docker run -it -e YATAIOS_API_KEY="sk-..." yataios
```

### 方式四：使用docker-compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## RISC-V 交叉编译 Docker 镜像

当前 buildx 默认驱动不支持 RISC-V 平台交叉编译。可选方案：

### 方案一：使用 QEMU user-mode（需要 Docker Hub 访问）

```bash
# 启用 binfmt_misc 支持
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# 拉取 RISC-V 镜像并运行
docker pull ubuntu:24.04/riscv64
docker run -it ubuntu:24.04/riscv64 uname -m
```

### 方案二：使用进迭时空提供的交叉编译环境

参考 Bianbu 官方文档搭建 RISC-V 交叉编译环境。

## 交叉编译（可选）

如需在x86_64平台上交叉编译适用于RISC-V的代码：

```bash
# 安装RISC-V工具链（需在Bianbu系统上执行）
sudo apt-get install gcc-riscv64-linux-gnu

# 交叉编译
riscv64-linux-gnu-gcc -o program program.c
```

## 硬件访问

在容器中运行时，如需访问宿主机的硬件资源（如AI加速器）：

```bash
# 映射设备文件
docker run --device=/dev/k1 -it yataios
```

## 文档链接

- [Bianbu 系统文档](https://www.spacemit.com/community/document)
- [MUSE BOOK 手册](https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/eco/k1_muse_book)
- [K1 芯片介绍](https://www.spacemit.com/community/document/info?lang=zh&nodepath=hardware/key_stone/k1)
