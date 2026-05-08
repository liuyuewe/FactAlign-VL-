# 技术博客草稿

> 标题：多模态大模型的"数字失认症"：问题诊断与开源解决方案

---

## 引言

你有没有遇到过这种情况：让 AI 看一张销售图表，它却把数字读错了？比如图表显示"苹果销量 42 件"，AI 却说"苹果销量 55 件"。

这不是模型"故意"犯错，而是大模型界称之为**"数字失认症"（Digital Agnosia）**的问题。

在这篇文章中，我将介绍我们是如何用**合成数据 + LoRA 微调**的方式来解决这个问题的，并开源了完整的解决方案 [FactAlign-VL](https://github.com/yourusername/FactAlign-VL)。

---

## 什么是数字失认症？

### 现象描述

多模态大语言模型（VLM）在处理视觉信息时，常常出现以下几类错误：

| 错误类型 | 示例 | 图表实际 | VLM 描述 |
|---------|------|---------|---------|
| 数值篡改 | ❌ | 42 | 55 |
| 标签混淆 | ❌ | A产品最高 | B产品最高 |
| 忽略异常值 | ❌ | 3月有下降 | 稳定上升 |
| 趋势错误 | ❌ | 上升趋势 | 下降趋势 |
| 数据缺失 | ❌ | 5项数据 | 4项数据 |

### 危害场景

这些错误在以下场景中可能造成严重后果：

- **医疗报告解读**：误读检查指标
- **金融数据分析**：错误解读报表
- **教育场景**：给学生错误信息
- **决策支持**：影响商业判断

---

## 为什么 VLM 会犯这种错误？

### 1. 视觉编码的局限性

VLM 的视觉编码器（如 ViT）在处理细粒度的数字信息时存在信息损失。

### 2. 注意力分配不均

模型可能过度关注"整体趋势"而忽略"具体数值"。

### 3. 训练数据偏差

大多数 VLM 的训练数据以自然图像为主，图表数据相对较少。

---

## 我们的解决方案

### 核心思路

```
问题：缺乏大量带标注的图表-描述-事实对
解决：合成数据工厂 + 自动标注
```

### 技术路线

#### 第一步：自动生成带"标准答案"的图表

使用 Matplotlib 自动生成不同类型的图表：

- 柱状图（Bar Chart）
- 折线图（Line Chart）
- 表格（Table）

同时保存精确的 JSON 元数据，包含：
```json
{
  "chart_id": "chart_00001",
  "type": "bar",
  "data": {"苹果": 42, "香蕉": 78, "橙子": 55},
  "labels": ["苹果", "香蕉", "橙子"],
  "values": [42, 78, 55]
}
```

#### 第二步：模拟 VLM 的错误行为

我们分析了真实 VLM 的错误模式，模拟生成"带错误"的描述：

- 数值篡改：随机改变数字
- 标签混淆：随机交换标签
- 忽略异常值：删除异常数据点描述

#### 第三步：原子事实拆分与标注

使用 NLP 技术将长描述拆分为"原子陈述"：

```
原始描述："苹果销量42，香蕉78，橙子55。其中橙子表现最差。"
        ↓
原子陈述：
1. "苹果销量42" → True（匹配元数据）
2. "香蕉销量78" → True
3. "橙子销量55" → True
4. "橙子表现最差" → False（55 > 42，橙子不是最差的）
```

#### 第四步：LoRA 微调

使用 PEFT 库的 LoRA 技术，微调 Qwen-VL-Chat：

- 秩 r=8，仅训练 0.1% 参数
- 目标层：q_proj, v_proj
- 单张 RTX 3090 即可完成训练

---

## 评估结果

### 实验设置

- 测试集：200 张图表，150 条原子陈述
- 基线：Mock 模型（模拟 VLM 错误行为）
- 评估指标：错误率、精确率、召回率、无伤害率

### 结果对比

| 指标 | 原始 VLM | FactAlign-VL | 改善 |
|------|----------|--------------|------|
| 事实错误率 | 73.33% | 60.67% | ↓ 17.3% |
| 无伤害率 | - | 84.67% | - |

### 混淆矩阵

```
              预测正确    预测错误
实际正确        40         17
实际错误        10         83
```

---

## 项目架构

```python
FactAlign-VL/
├── factalign-vl/
│   ├── synthesizer/    # 数据生成
│   │   ├── chart_generator.py      # 图表生成
│   │   ├── description_generator.py # 描述生成
│   │   └── annotator.py            # 原子事实标注
│   ├── finetune/       # 模型微调
│   │   ├── lora_config.py          # LoRA配置
│   │   ├── trainer.py              # 训练器
│   │   └── inference.py            # 推理模块
│   └── evaluation/     # 评估模块
│       ├── testset_builder.py      # 测试集
│       ├── evaluator.py             # 评估器
│       └── report_generator.py     # 报告生成
└── data/              # 数据目录
```

---

## 如何使用

### 快速开始

```bash
# 克隆项目
git clone https://github.com/yourusername/FactAlign-VL.git
cd FactAlign-VL

# 安装依赖
pip install -r requirements.txt

# 启动演示
python run_demo.py
```

### Web 界面

访问 http://localhost:7860，你可以：

1. 上传图表图片
2. 输入 VLM 生成的描述
3. 查看 FactAlign-VL 的核查结果

### 训练自己的模型

```bash
# 生成数据
python generate_synthetic_data.py

# 微调模型
python finetune_model.py
```

---

## 局限性与未来工作

### 现有局限

1. **错误类型有限**：目前主要处理数值和标签错误
2. **图表类型有限**：仅支持柱状图、折线图、表格
3. **依赖合成数据**：真实场景的泛化性待验证

### 未来方向

1. 扩展更多图表类型（饼图、散点图等）
2. 引入更多错误模式
3. 探索端到端的视觉问答
4. 支持中文以外的语言

---

## 结语

VLM 的"数字失认症"是一个值得重视的问题。通过合成数据和 LoRA 微调，我们可以以较低成本训练一个专门的事实核查模型。

项目已完全开源，欢迎使用和贡献！

- GitHub: https://github.com/yourusername/FactAlign-VL
- 文档: https://github.com/yourusername/FactAlign-VL#readme

如果你有任何问题或建议，欢迎在 GitHub 上提 Issue！

---

## 致谢

本项目使用了以下开源技术：
- [Qwen-VL](https://github.com/QwenLM/Qwen-VL)
- [PEFT](https://github.com/huggingface/peft)
- [HuggingFace Transformers](https://github.com/huggingface/transformers)
- [Matplotlib](https://matplotlib.org/)
- [Gradio](https://gradio.app/)

---

## 参考

1. Liu, A., et al. "On the Factuality of Large Multimodal Models." arXiv, 2024.
2. Hu, E., et al. "LoRA: Low-Rank Adaptation of Large Language Models." ICLR, 2022.
3. Bai, J., et al. "Qwen-VL: A Versatile Vision-Language Model for Understanding and Reasoning." GitHub, 2024.
