"""
训练监控和样本平衡整合脚本
执行带有完整监控的训练流程
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "factalign-vl"))

from synthesizer.data_converter import CONVERTED_DIR, ANNOTATIONS_DIR
from synthesizer.data_converter import load_annotations, convert_to_qwen_format
from finetune import (
    MetricsCalculator,
    TrainingMonitor,
    analyze_class_balance,
    print_balance_analysis,
    balance_dataset,
    analyze_dataset_balance,
    print_balance_report,
    compute_class_weights,
)

def main():
    print("=" * 70)
    print("🎯 训练监控和样本平衡")
    print("=" * 70)

    print("\n📊 阶段 1: 分析原始数据平衡状态")
    print("-" * 50)

    train_data = load_annotations(ANNOTATIONS_DIR / "train.jsonl")
    val_data = load_annotations(ANNOTATIONS_DIR / "val.jsonl")
    test_data = load_annotations(ANNOTATIONS_DIR / "test.jsonl")

    print(f"\n数据集大小:")
    print(f"  训练集: {len(train_data)} 条")
    print(f"  验证集: {len(val_data)} 条")
    print(f"  测试集: {len(test_data)} 条")

    print_balance_report(train_data, "训练集")
    print_balance_report(val_data, "验证集")
    print_balance_report(test_data, "测试集")

    print("\n📊 阶段 2: 计算类别权重")
    print("-" * 50)

    weights = compute_class_weights(train_data)
    print(f"\n类别权重 (用于损失函数):")
    print(f"  正样本 (是) 权重: {weights['positive']:.4f}")
    print(f"  负样本 (否) 权重: {weights['negative']:.4f}")
    print(f"  权重比例: {weights['ratio']:.4f}")

    print("\n📊 阶段 3: 样本平衡")
    print("-" * 50)

    balanced_train, balance_stats = balance_dataset(train_data, target_ratio=1.0)
    print(f"\n平衡前:")
    print(f"  正样本: {balance_stats['original']['positive']}")
    print(f"  负样本: {balance_stats['original']['negative']}")
    print(f"  比例: {balance_stats['original']['original_ratio']:.2f}")

    print(f"\n平衡后 (1:1):")
    print(f"  正样本: {balance_stats['balanced']['positive']}")
    print(f"  负样本: {balance_stats['balanced']['negative']}")

    print_balance_report(balanced_train, "平衡后训练集")

    print("\n📊 阶段 4: 转换数据格式")
    print("-" * 50)

    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"转换平衡后的训练数据...")
    converted_train = []
    for ann in balanced_train[:100]:
        try:
            item = convert_to_qwen_format(ann)
            converted_train.append(item)
        except Exception:
            continue

    if converted_train:
        output_path = CONVERTED_DIR / "train_balanced_qwen_format.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted_train, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(converted_train)} 条平衡训练数据到 {output_path}")

    print("\n📊 阶段 5: 模拟训练监控")
    print("-" * 50)

    monitor = TrainingMonitor()

    import random
    random.seed(42)

    print("\n模拟训练过程...")

    for step in range(1, 11):
        train_loss = 1.0 - step * 0.08 + random.uniform(-0.05, 0.05)
        train_accuracy = 0.5 + step * 0.04 + random.uniform(-0.02, 0.02)
        train_accuracy = min(0.95, max(0.5, train_accuracy))

        metrics = monitor.update_train_metrics(train_loss, train_accuracy)

        if step % 2 == 0:
            val_metrics = {
                "accuracy": 0.5 + step * 0.04 + random.uniform(-0.03, 0.03),
                "precision": 0.55 + step * 0.03 + random.uniform(-0.02, 0.02),
                "recall": 0.6 + step * 0.02 + random.uniform(-0.02, 0.02),
                "f1": 0.55 + step * 0.03 + random.uniform(-0.02, 0.02),
            }
            val_metrics = {k: min(0.95, max(0.5, v)) for k, v in val_metrics.items()}

            best_info = monitor.update_val_metrics(val_metrics)

            print(f"\nStep {step}:")
            print(f"  训练损失: {metrics['train_loss']:.4f}")
            print(f"  训练准确率: {metrics['train_accuracy']:.4f}")
            print(f"  验证准确率: {val_metrics['accuracy']:.4f}")
            print(f"  验证精确率: {val_metrics['precision']:.4f}")
            print(f"  验证召回率: {val_metrics['recall']:.4f}")
            print(f"  验证F1: {val_metrics['f1']:.4f}")

            if best_info.get("is_best_accuracy"):
                print(f"  ✅ 新的最佳准确率!")
            if best_info.get("is_best_f1"):
                print(f"  ⭐ 新的最佳F1!")

    print("\n" + "=" * 70)
    print("📈 训练监控摘要")
    print("=" * 70)
    monitor.print_summary()

    print("\n✅ 训练监控设置完成！")
    print("\n📋 建议:")
    print("  1. 使用加权损失函数平衡正负样本的影响")
    print("  2. 监控验证集准确率、精确率和召回率")
    print("  3. 确保模型不会偏向预测'是'或'否'")
    print("  4. 使用早停避免过拟合")
    print("  5. 保存最佳模型检查点")

    print("\n📁 输出文件:")
    print(f"  平衡数据: {CONVERTED_DIR / 'train_balanced_qwen_format.json'}")

    return {
        "train_data": len(train_data),
        "val_data": len(val_data),
        "test_data": len(test_data),
        "balanced_train": len(balanced_train),
        "class_weights": weights,
        "best_metrics": monitor.best_metrics,
    }

if __name__ == "__main__":
    results = main()
    print(f"\n最终结果: {json.dumps(results, indent=2)}")
