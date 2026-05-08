# FactAlign-VL 安装指南

## 环境要求

- Python 3.10+
- 至少 8GB RAM
- 磁盘空间：基础安装约 2GB，完整安装（含 PyTorch）约 10GB

## 安装步骤

### 1. 创建虚拟环境

```bash
# 使用 venv（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

#### 方式一：完整安装（推荐，需要充足磁盘空间）

```bash
pip install -r requirements.txt
```

#### 方式二：开发安装（轻量级，不含 PyTorch）

```bash
pip install -r requirements-dev.txt
```

然后单独安装 PyTorch（CPU 版本）：
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

或 GPU 版本（CUDA 11.8）：
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 3. 安装 SpaCy 中文模型

```bash
python -m spacy download zh_core_web_sm
```

### 4. 验证安装

```bash
python -c "import factalign_vl; print('安装成功！')"
```

## 启动应用

```bash
python run.py
```

应用将在 http://localhost:7860 启动

## 常见问题

### 磁盘空间不足

如果遇到 `No space left on device` 错误：
1. 清理临时文件：`pip cache purge`
2. 使用 `--no-cache-dir` 参数安装：`pip install --no-cache-dir <package>`
3. 考虑使用轻量级依赖文件 `requirements-dev.txt`

### SpaCy 模型下载失败

如果自动下载失败，可以手动下载：
```bash
pip install https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.6.0/zh_core_web_sm-3.6.0-py3-none-any.whl
```

### 内存不足

如果运行时内存不足：
1. 减少批处理大小
2. 使用更小的模型
3. 关闭其他应用程序
