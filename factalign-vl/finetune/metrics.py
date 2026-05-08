"""
训练监控指标模块
计算和监控二元分类任务的各项指标
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict

class MetricsCalculator:
    """指标计算器"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置所有统计"""
        self.predictions = []
        self.labels = []

    def update(self, predictions: List[bool], labels: List[bool]):
        """更新预测和标签"""
        self.predictions.extend(predictions)
        self.labels.extend(labels)

    def compute(self) -> Dict[str, float]:
        """计算所有指标"""
        if not self.predictions or not self.labels:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "true_positive": 0,
                "false_positive": 0,
                "true_negative": 0,
                "false_negative": 0,
            }

        tp = sum(1 for p, l in zip(self.predictions, self.labels) if p and l)
        fp = sum(1 for p, l in zip(self.predictions, self.labels) if p and not l)
        tn = sum(1 for p, l in zip(self.predictions, self.labels) if not p and not l)
        fn = sum(1 for p, l in zip(self.predictions, self.labels) if not p and l)

        accuracy = (tp + tn) / len(self.labels) if len(self.labels) > 0 else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
            "total": len(self.labels),
        }

    def get_confusion_matrix(self) -> Tuple[int, int, int, int]:
        """获取混淆矩阵"""
        metrics = self.compute()
        return (
            metrics["true_positive"],
            metrics["false_positive"],
            metrics["true_negative"],
            metrics["false_negative"]
        )


class TrainingMonitor:
    """训练监控器"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.history = {
            "train_loss": [],
            "train_accuracy": [],
            "val_accuracy": [],
            "val_precision": [],
            "val_recall": [],
            "val_f1": [],
        }
        self.best_metrics = {
            "val_accuracy": 0.0,
            "val_f1": 0.0,
        }

    def update_train_metrics(self, loss: float, accuracy: float):
        """更新训练指标"""
        self.history["train_loss"].append(loss)
        self.history["train_accuracy"].append(accuracy)

        recent_loss = self.history["train_loss"][-self.window_size:]
        avg_loss = sum(recent_loss) / len(recent_loss)

        return {"train_loss": avg_loss, "train_accuracy": accuracy}

    def update_val_metrics(self, metrics: Dict[str, float]):
        """更新验证指标"""
        self.history["val_accuracy"].append(metrics.get("accuracy", 0.0))
        self.history["val_precision"].append(metrics.get("precision", 0.0))
        self.history["val_recall"].append(metrics.get("recall", 0.0))
        self.history["val_f1"].append(metrics.get("f1", 0.0))

        is_best_accuracy = metrics.get("accuracy", 0) > self.best_metrics["val_accuracy"]
        is_best_f1 = metrics.get("f1", 0) > self.best_metrics["val_f1"]

        if is_best_accuracy:
            self.best_metrics["val_accuracy"] = metrics["accuracy"]

        if is_best_f1:
            self.best_metrics["val_f1"] = metrics["f1"]

        return {
            "is_best_accuracy": is_best_accuracy,
            "is_best_f1": is_best_f1,
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取训练摘要"""
        return {
            "current_metrics": {
                "train_loss": self.history["train_loss"][-1] if self.history["train_loss"] else None,
                "train_accuracy": self.history["train_accuracy"][-1] if self.history["train_accuracy"] else None,
                "val_accuracy": self.history["val_accuracy"][-1] if self.history["val_accuracy"] else None,
                "val_precision": self.history["val_precision"][-1] if self.history["val_precision"] else None,
                "val_recall": self.history["val_recall"][-1] if self.history["val_recall"] else None,
                "val_f1": self.history["val_f1"][-1] if self.history["val_f1"] else None,
            },
            "best_metrics": self.best_metrics,
            "total_steps": len(self.history["train_loss"]),
        }

    def print_summary(self):
        """打印训练摘要"""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print("训练监控摘要")
        print("=" * 60)
        print(f"总训练步数: {summary['total_steps']}")
        print(f"\n当前指标:")
        curr = summary['current_metrics']
        if curr['train_loss'] is not None:
            print(f"  训练损失: {curr['train_loss']:.4f}")
        if curr['train_accuracy'] is not None:
            print(f"  训练准确率: {curr['train_accuracy']:.4f}")
        if curr['val_accuracy'] is not None:
            print(f"  验证准确率: {curr['val_accuracy']:.4f}")
        if curr['val_precision'] is not None:
            print(f"  验证精确率: {curr['val_precision']:.4f}")
        if curr['val_recall'] is not None:
            print(f"  验证召回率: {curr['val_recall']:.4f}")
        if curr['val_f1'] is not None:
            print(f"  验证F1: {curr['val_f1']:.4f}")
        print(f"\n最佳指标:")
        print(f"  最佳验证准确率: {summary['best_metrics']['val_accuracy']:.4f}")
        print(f"  最佳验证F1: {summary['best_metrics']['val_f1']:.4f}")


def analyze_class_balance(labels: List[bool]) -> Dict[str, Any]:
    """分析类别平衡"""
    total = len(labels)
    positive = sum(1 for l in labels if l)
    negative = total - positive

    positive_ratio = positive / total if total > 0 else 0
    negative_ratio = negative / total if total > 0 else 0

    imbalance_ratio = max(positive_ratio, negative_ratio) / min(positive_ratio, negative_ratio) if min(positive_ratio, negative_ratio) > 0 else float('inf')

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "imbalance_ratio": imbalance_ratio,
        "is_balanced": imbalance_ratio < 2.0,
        "recommendation": _get_balance_recommendation(imbalance_ratio)
    }


def _get_balance_recommendation(imbalance_ratio: float) -> str:
    """获取平衡建议"""
    if imbalance_ratio < 1.5:
        return "样本已平衡，无需调整"
    elif imbalance_ratio < 3.0:
        return "轻微不平衡，建议在训练时进行加权采样"
    elif imbalance_ratio < 5.0:
        return "中度不平衡，建议使用过采样或欠采样"
    else:
        return "严重不平衡，必须进行重采样以避免模型偏向多数类"


def print_balance_analysis(labels: List[bool], split_name: str = "数据集"):
    """打印类别平衡分析"""
    analysis = analyze_class_balance(labels)

    print(f"\n{split_name} 类别平衡分析:")
    print(f"  总样本数: {analysis['total']}")
    print(f"  正样本 (是): {analysis['positive']} ({analysis['positive_ratio']*100:.1f}%)")
    print(f"  负样本 (否): {analysis['negative']} ({analysis['negative_ratio']*100:.1f}%)")
    print(f"  不平衡比例: {analysis['imbalance_ratio']:.2f}")
    print(f"  状态: {analysis['recommendation']}")


if __name__ == "__main__":
    print("=" * 60)
    print("训练监控模块测试")
    print("=" * 60)

    calculator = MetricsCalculator()

    predictions = [True, True, False, True, False, False, True, False, True, False]
    labels = [True, False, False, True, False, True, True, False, False, True]

    calculator.update(predictions, labels)
    metrics = calculator.compute()

    print("\n混淆矩阵:")
    tp, fp, tn, fn = calculator.get_confusion_matrix()
    print(f"  真阳性 (TP): {tp}")
    print(f"  假阳性 (FP): {fp}")
    print(f"  真阴性 (TN): {tn}")
    print(f"  假阴性 (FN): {fn}")

    print("\n评估指标:")
    print(f"  准确率: {metrics['accuracy']:.4f}")
    print(f"  精确率: {metrics['precision']:.4f}")
    print(f"  召回率: {metrics['recall']:.4f}")
    print(f"  F1分数: {metrics['f1']:.4f}")

    print_balance_analysis(labels, "测试集")
