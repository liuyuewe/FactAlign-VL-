"""
样本平衡模块
处理训练数据中的类别不平衡问题
"""

import random
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

class BalancedSampler:
    """平衡采样器"""

    def __init__(
        self,
        positive_samples: List[Dict],
        negative_samples: List[Dict],
        target_ratio: float = 1.0,
        shuffle: bool = True
    ):
        self.positive_samples = positive_samples
        self.negative_samples = negative_samples
        self.target_ratio = target_ratio
        self.shuffle = shuffle

        self.current_pos_idx = 0
        self.current_neg_idx = 0

        if self.shuffle:
            random.shuffle(self.positive_samples)
            random.shuffle(self.negative_samples)

    def __len__(self) -> int:
        """返回采样器长度"""
        if self.target_ratio >= 1.0:
            return len(self.positive_samples)
        else:
            num_pos = int(len(self.negative_samples) * self.target_ratio)
            return min(num_pos, len(self.positive_samples))

    def __iter__(self):
        """迭代器"""
        if self.target_ratio >= 1.0:
            num_neg = int(len(self.positive_samples) / self.target_ratio)
            num_neg = min(num_neg, len(self.negative_samples))

            combined = []
            combined.extend(self.positive_samples)

            neg_sampled = self.negative_samples[:num_neg]
            combined.extend(neg_sampled)

            if self.shuffle:
                random.shuffle(combined)

            return iter(combined)
        else:
            num_pos = int(len(self.negative_samples) * self.target_ratio)
            num_pos = min(num_pos, len(self.positive_samples))

            combined = []
            combined.extend(self.positive_samples[:num_pos])
            combined.extend(self.negative_samples)

            if self.shuffle:
                random.shuffle(combined)

            return iter(combined)

    def get_stats(self) -> Dict[str, Any]:
        """获取采样器统计"""
        total = len(self.positive_samples) + len(self.negative_samples)
        pos = len(self.positive_samples)
        neg = len(self.negative_samples)

        return {
            "positive_samples": pos,
            "negative_samples": neg,
            "total_samples": total,
            "original_ratio": pos / neg if neg > 0 else float('inf'),
            "target_ratio": self.target_ratio,
            "balanced_pos": pos,
            "balanced_neg": int(pos / self.target_ratio) if self.target_ratio > 0 else neg,
        }


def balance_dataset(
    data: List[Dict],
    target_ratio: float = 1.0,
    seed: int = 42
) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    平衡数据集

    Args:
        data: 原始数据集
        target_ratio: 目标正负样本比例 (正:负)
        seed: 随机种子

    Returns:
        平衡后的数据集和统计信息
    """
    random.seed(seed)

    positive_samples = [item for item in data if item.get("label", False)]
    negative_samples = [item for item in data if not item.get("label", False)]

    original_stats = {
        "total": len(data),
        "positive": len(positive_samples),
        "negative": len(negative_samples),
        "original_ratio": len(positive_samples) / len(negative_samples) if negative_samples else float('inf'),
    }

    if target_ratio == 1.0:
        min_count = min(len(positive_samples), len(negative_samples))
        positive_balanced = random.sample(positive_samples, min_count)
        negative_balanced = random.sample(negative_samples, min_count)
    else:
        num_neg = int(len(positive_samples) / target_ratio)
        num_neg = min(num_neg, len(negative_samples))

        positive_balanced = positive_samples
        negative_balanced = random.sample(negative_samples, num_neg)

    balanced_data = positive_balanced + negative_balanced
    random.shuffle(balanced_data)

    balanced_stats = {
        "total": len(balanced_data),
        "positive": len(positive_balanced),
        "negative": len(negative_balanced),
        "balanced_ratio": len(positive_balanced) / len(negative_balanced) if negative_balanced else float('inf'),
    }

    stats = {
        "original": original_stats,
        "balanced": balanced_stats,
        "target_ratio": target_ratio,
    }

    return balanced_data, stats


def oversample_minority_class(
    data: List[Dict],
    target_ratio: float = 1.0,
    seed: int = 42
) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    过采样少数类

    Args:
        data: 原始数据集
        target_ratio: 目标正负样本比例
        seed: 随机种子

    Returns:
        过采样后的数据集和统计信息
    """
    random.seed(seed)

    positive_samples = [item for item in data if item.get("label", False)]
    negative_samples = [item for item in data if not item.get("label", False)]

    original_stats = {
        "total": len(data),
        "positive": len(positive_samples),
        "negative": len(negative_samples),
    }

    minority_samples = positive_samples if len(positive_samples) < len(negative_samples) else negative_samples
    majority_samples = positive_samples if len(positive_samples) >= len(negative_samples) else negative_samples

    if target_ratio >= 1.0:
        target_minority_count = len(majority_samples)
    else:
        target_minority_count = int(len(majority_samples) * target_ratio)

    oversampled = list(minority_samples)
    while len(oversampled) < target_minority_count:
        oversampled.extend(random.sample(minority_samples, min(len(minority_samples), target_minority_count - len(oversampled))))

    balanced_data = oversampled + majority_samples
    random.shuffle(balanced_data)

    balanced_stats = {
        "total": len(balanced_data),
        "positive": len([d for d in balanced_data if d.get("label", False)]),
        "negative": len([d for d in balanced_data if not d.get("label", False)]),
    }

    stats = {
        "original": original_stats,
        "balanced": balanced_stats,
        "method": "oversample",
    }

    return balanced_data, stats


def compute_class_weights(data: List[Dict]) -> Dict[str, float]:
    """
    计算类别权重用于损失函数

    Returns:
        {"positive": weight, "negative": weight}
    """
    total = len(data)
    positive = sum(1 for item in data if item.get("label", False))
    negative = total - positive

    if positive == 0 or negative == 0:
        return {"positive": 1.0, "negative": 1.0}

    weight_positive = total / (2 * positive)
    weight_negative = total / (2 * negative)

    return {
        "positive": weight_positive,
        "negative": weight_negative,
        "ratio": weight_positive / weight_negative if weight_negative > 0 else 1.0
    }


def analyze_dataset_balance(data: List[Dict]) -> Dict[str, Any]:
    """分析数据集平衡状态"""
    positive = sum(1 for item in data if item.get("label", False))
    negative = len(data) - positive

    total = len(data)

    if total == 0:
        return {
            "is_balanced": True,
            "positive_ratio": 0,
            "negative_ratio": 0,
            "imbalance_ratio": 1.0,
            "needs_balancing": False,
        }

    pos_ratio = positive / total
    neg_ratio = negative / total

    imbalance = max(pos_ratio, neg_ratio) / min(pos_ratio, neg_ratio) if min(pos_ratio, neg_ratio) > 0 else float('inf')

    needs_balancing = imbalance > 2.0

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_ratio": pos_ratio,
        "negative_ratio": neg_ratio,
        "imbalance_ratio": imbalance,
        "is_balanced": imbalance <= 2.0,
        "needs_balancing": needs_balancing,
        "recommendation": _get_balance_recommendation(imbalance),
    }


def _get_balance_recommendation(imbalance_ratio: float) -> str:
    """获取平衡建议"""
    if imbalance_ratio <= 1.5:
        return "样本已平衡，无需调整"
    elif imbalance_ratio <= 3.0:
        return "轻微不平衡，建议使用加权损失函数"
    elif imbalance_ratio <= 5.0:
        return "中度不平衡，建议进行过采样或欠采样"
    else:
        return "严重不平衡，建议同时使用过采样和加权损失"


def print_balance_report(data: List[Dict], split_name: str = "数据集"):
    """打印平衡报告"""
    analysis = analyze_dataset_balance(data)

    print(f"\n{split_name} 平衡分析报告:")
    print("=" * 50)
    print(f"总样本数: {analysis['total']}")
    print(f"正样本 (是): {analysis['positive']} ({analysis['positive_ratio']*100:.1f}%)")
    print(f"负样本 (否): {analysis['negative']} ({analysis['negative_ratio']*100:.1f}%)")
    print(f"不平衡比例: {analysis['imbalance_ratio']:.2f}")
    print(f"状态: {'平衡' if analysis['is_balanced'] else '不平衡'}")
    print(f"建议: {analysis['recommendation']}")


if __name__ == "__main__":
    print("=" * 60)
    print("样本平衡模块测试")
    print("=" * 60)

    sample_data = [
        {"id": i, "label": i % 3 != 0}
        for i in range(100)
    ]

    print_balance_report(sample_data, "原始数据")

    balanced_data, stats = balance_dataset(sample_data, target_ratio=1.0)
    print_balance_report(balanced_data, "平衡后数据")

    print("\n统计信息:")
    print(f"原始: {stats['original']}")
    print(f"平衡后: {stats['balanced']}")

    weights = compute_class_weights(sample_data)
    print(f"\n类别权重: {weights}")
