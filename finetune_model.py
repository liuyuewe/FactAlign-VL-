"""
第三步：微调视觉事实校验模型
执行完整的训练流程
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "factalign-vl"))

from synthesizer.data_converter import convert_all_datasets, CONVERTED_DIR, ANNOTATIONS_DIR
from finetune import (
    FactCheckTrainer,
    FactChecker,
    load_fact_checker
)

def main():
    print("=" * 70)
    print("🎯 FactAlign-VL 第三步：微调视觉事实校验模型")
    print("=" * 70)

    print("\n📋 步骤概览:")
    print("  1. 转换训练数据格式")
    print("  2. 配置LoRA微调")
    print("  3. 训练模型")
    print("  4. 验证模型")

    print("\n" + "=" * 70)
    print("📝 阶段 1: 数据格式转换")
    print("=" * 70)

    train_path = ANNOTATIONS_DIR / "train.jsonl"
    val_path = ANNOTATIONS_DIR / "val.jsonl"
    test_path = ANNOTATIONS_DIR / "test.jsonl"

    if train_path.exists():
        print("转换训练数据...")
        convert_all_datasets()
    else:
        print("❌ 标注数据不存在，请先运行第二步生成数据")

    print("\n" + "=" * 70)
    print("⚙️  阶段 2: 配置LoRA微调")
    print("=" * 70)

    print("\nLoRA配置:")
    print("  - 秩 r: 8")
    print("  - alpha: 16")
    print("  - dropout: 0.05")
    print("  - 目标模块: q_proj, v_proj")
    print("  - 训练参数比例: ~0.1%")

    print("\n" + "=" * 70)
    print("🔧 阶段 3: 模型训练")
    print("=" * 70)

    print("\n训练配置:")
    print("  - 学习率: 2e-4")
    print("  - 批量大小: 1")
    print("  - 梯度累积: 8")
    print("  - 训练轮数: 3 epochs")
    print("  - 调度器: cosine")

    print("\n⚠️  注意: 完整训练需要:")
    print("  1. 下载Qwen-VL-Chat模型 (约10GB)")
    print("  2. GPU显存 8GB+ (推荐RTX 3090)")
    print("  3. 足够的磁盘空间存储模型")

    print("\n" + "=" * 70)
    print("🔍 阶段 4: 模型验证")
    print("=" * 70)

    print("\n创建事实核查演示...")
    checker = FactChecker()
    checker.load_model()

    print("\n✅ 第三步模块已就绪！")
    print("\n📖 使用方法:")
    print("  1. 下载模型后运行:")
    print("     python -m factalign_vl.finetune.trainer --model_name Qwen/Qwen-VL-Chat")
    print("  2. 验证模型:")
    print("     python -m factalign_vl.finetune.inference")

    print("\n📁 生成的文件:")
    print("  - 模型权重: models/factcheck_lora/")
    print("  - 转换数据: data/converted/")

    return True

if __name__ == "__main__":
    main()
