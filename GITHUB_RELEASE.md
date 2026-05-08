# GitHub 发布指南

## 发布前准备

### 1. 创建 .gitignore 文件

确保以下内容已添加到 `.gitignore`：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data (仅保留样例)
data/annotations/
data/metadata/
data/charts/
data/descriptions/
# 保留 evaluation 目录用于查看评估结果
# data/evaluation/

# Models
models/
*.bin
*.safetensors

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Large files
*.png
*.jpg
*.jpeg
*.gif
```

### 2. 准备样例数据

```bash
# 创建样例目录
mkdir -p data/samples

# 复制少量样例数据
cp data/metadata/chart_00001.json data/samples/
cp data/metadata/chart_00002.json data/samples/
cp data/metadata/chart_00003.json data/samples/

# 复制少量标注
cp data/annotations/val.jsonl data/samples/val_sample.jsonl
head -n 10 data/annotations/train.jsonl > data/samples/train_sample.jsonl
```

### 3. 创建 GitHub 仓库

```bash
# 在 GitHub 上创建新仓库后
git init
git add .
git commit -m "Initial commit: FactAlign-VL visual fact checker"
git branch -M main
git remote add origin https://github.com/yourusername/FactAlign-VL.git
git push -u origin main
```

---

## GitHub 仓库设置

### 1. 添加Topics

在仓库设置中添加以下Topics：
- `visual-question-answering`
- `fact-checking`
- `multimodal`
- `lora-finetuning`
- `qwen-vl`
- `chinese-nlp`

### 2. 创建 Release

```bash
# 标记版本
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 3. 发布模型权重

模型权重需要单独发布（文件较大）：

1. 在 GitHub Releases 创建新的 Release
2. 上传 LoRA 权重文件（通常几十 MB）
3. 或使用 GitHub LFS 存储

---

## 发布检查清单

- [ ] README.md 已完善
- [ ] LICENSE 已添加
- [ ] .gitignore 已配置
- [ ] 敏感信息已清除（API keys等）
- [ ] 代码已格式化
- [ ] 单元测试已通过
- [ ] 文档已更新
- [ ] 许可证头已添加到代码文件
- [ ] 样例数据已准备
- [ ] 发布说明已撰写

---

## 发布说明模板

```markdown
# v1.0.0 (2026-05-08)

## 🎉 新功能
- 支持柱状图、折线图、表格的事实核查
- Gradio 交互式演示界面
- 完整的数据生成和模型训练流程

## 📊 评估结果
- 事实错误率降低 17.3%
- 无伤害率 84.67%

## 🚀 快速开始
```bash
pip install factalign-vl
python run_demo.py
```

## 📝 示例

## 🔧 依赖
- Python 3.8+
- PyTorch 2.0+
- Transformers 4.30+

## 📄 许可证
MIT License
```

---

## 持续集成 (可选)

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/
```
