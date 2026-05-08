# 🔍 FactAlign-VL: 视觉事实核查系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Model-Qwen--VL--Chat-orange.svg" alt="Model">
</p>

> 针对多模态大模型"数字失认症"问题的视觉事实核查系统

---

## 📖 项目简介

### 问题背景：数字失认症

多模态大语言模型（VLM）在处理图表时，常常出现**数字失认症（Digital Agnosia）**现象：

- ❌ **数值篡改**：将图表中的数值读错（如 42 读成 55）
- ❌ **标签混淆**：混淆不同类别的标签（如 A/B/C 产品搞混）
- ❌ **忽略异常值**：遗漏图表中的异常数据点
- ❌ **趋势错误**：错误判断数据升降趋势
- ❌ **数据缺失**：遗漏部分数据项

**FactAlign-VL** 通过合成数据 + LoRA 微调的方式，训练一个专门的事实核查模型，有效降低 VLM 描述的事实错误率。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      FactAlign-VL 架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│   │  图表生成   │ -> │ VLM 描述    │ -> │ 原子事实    │     │
│   │  (Matplotlib)│    │ (带错误)    │    │ 标注        │     │
│   └─────────────┘    └─────────────┘    └─────────────┘     │
│          │                                    │              │
│          │          合成数据工厂               │              │
│          │ ───────────────────────────────────            │
│          ▼                                    ▼              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │  Ground     │    │  训练数据    │    │  真值标签    │   │
│   │  Truth      │    │  (JSONL)    │    │  (True/False)│   │
│   └─────────────┘    └─────────────┘    └─────────────┘   │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                      │
│                    │   LoRA 微调     │                      │
│                    │  Qwen-VL-Chat   │                      │
│                    └─────────────────┘                      │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   FactAlign-VL                      │   │
│   │   输入图表 + VLM描述 → 输出核查后的标注描述          │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心功能

| 功能 | 描述 |
|------|------|
| 图表生成 | 自动生成柱状图、折线图、表格及对应元数据 |
| 错误模拟 | 模拟 VLM 的数字失认症错误 |
| 原子事实拆分 | 使用 NLP 将长描述拆分为可验证的原子陈述 |
| 自动标注 | 基于元数据自动生成 True/False 标签 |
| LoRA 微调 | 低成本微调 Qwen-VL-Chat 模型 |
| 交互演示 | Gradio Web 界面实时核查 |

---

## 📊 评估结果

```
╔══════════════════════════════════════════════════════════════╗
║              FactAlign-VL 效果评估报告                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   原始 VLM 描述事实错误率:   73.33%                          ║
║   FactAlign-VL 核查后错误率:   60.67%                         ║
║                                                              ║
║   📉 错误率降低: 73.33% → 60.67% (-12.67%)                  ║
║   📈 改善幅度: 17.3%                                         ║
║                                                              ║
║   无伤害率: 84.67% (不会误标正确陈述)                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- CUDA (可选，用于 GPU 推理)
- 8GB+ RAM

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/FactAlign-VL.git
cd FactAlign-VL

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装基础依赖
pip install -r requirements.txt

# 安装可选依赖 (模型推理所需)
pip install torch transformers peft accelerate bitsandbytes

# 下载 SpaCy 中文模型 (可选)
python -m spacy download zh_core_web_sm
```

### 运行演示

```bash
# 启动 Gradio 演示界面
python run_demo.py

# 访问 http://localhost:7860
```

### 训练模型

```bash
# 生成合成数据 (如需重新生成)
python generate_synthetic_data.py

# 微调模型
python finetune_model.py

# 带监控的训练
python train_with_monitoring.py
```

### 运行评估

```bash
# 完整评估流程
python -c "from factalign_vl.evaluation import run_full_evaluation; run_full_evaluation()"
```

---

## 📁 项目结构

```
FactAlign-VL/
├── factalign-vl/              # 核心代码包
│   ├── configs/               # 配置文件
│   ├── utils/                 # 工具函数
│   ├── synthesizer/           # 数据生成
│   │   ├── chart_generator.py    # 图表生成
│   │   ├── description_generator.py # VLM描述
│   │   └── annotator.py          # 原子事实标注
│   ├── finetune/              # 模型微调
│   │   ├── lora_config.py        # LoRA配置
│   │   ├── trainer.py            # 训练器
│   │   └── inference.py          # 推理模块
│   ├── evaluation/            # 评估模块
│   │   ├── testset_builder.py    # 测试集
│   │   ├── evaluator.py          # 评估器
│   │   └── report_generator.py   # 报告生成
│   ├── checker/               # 事实核查组件
│   └── app/                  # 演示界面
│       └── demo.py              # Gradio界面
├── data/                     # 数据目录
│   ├── annotations/          # 标注数据
│   ├── metadata/             # 元数据
│   ├── charts/               # 图表图片
│   └── evaluation/           # 评估结果
├── requirements.txt         # 依赖列表
├── LICENSE                  # MIT许可证
└── README.md               # 本文件
```

---

## 🔧 技术细节

### 数据生成

- **图表类型**：柱状图、折线图、表格
- **数据规模**：1500+ 图表，14000+ 标注样本
- **错误类型**：数字篡改、标签混淆、忽略异常值、趋势错误

### 模型微调

- **基座模型**：Qwen-VL-Chat
- **微调方法**：LoRA (r=8, alpha=16)
- **训练设备**：单张 RTX 3090 (24GB)
- **样本平衡**：1:1 正负样本比例

### 评估指标

| 指标 | 说明 |
|------|------|
| 事实错误率 | 描述中错误陈述的比例 |
| 改善幅度 | 核查前后的错误率差值 |
| 无伤害率 | 正确陈述被误标的比例 |
| 精确率 | 核查器的精确率 |
| 召回率 | 核查器的召回率 |

---

## 📝 预设错误案例

| 案例类型 | 示例描述 | 错误位置 |
|----------|----------|----------|
| 数字篡改 | "苹果的数值是42" | 42 → 应为其他值 |
| 标签混淆 | "A产品最高" | A → 应为B |
| 忽略异常值 | "呈稳定上升趋势" | 未提及3月的异常下降 |
| 趋势错误 | "数据呈下降趋势" | 应为上升趋势 |
| 数据缺失 | "总计580" | 遗漏深圳数据 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📜 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Qwen-VL](https://github.com/QwenLM/Qwen-VL) - 基础多模态模型
- [PEFT](https://github.com/huggingface/peft) - 高效微调库
- [Matplotlib](https://matplotlib.org/) - 图表生成
- [Gradio](https://gradio.app/) - Web 界面框架

---

## 📧 联系方式

- 项目主页：https://github.com/yourusername/FactAlign-VL
- 问题反馈：https://github.com/yourusername/FactAlign-VL/issues

---

<p align="center">
  如果这个项目对你有帮助，请给我们一个 ⭐️
</p>
