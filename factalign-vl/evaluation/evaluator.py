"""
事实核查评估器
评估模型的核查性能
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

@dataclass
class EvaluationMetrics:
    """评估指标"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    total_samples: int = 0
    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

@dataclass
class EvaluationReport:
    """评估报告"""
    metrics: EvaluationMetrics
    before_accuracy: float = 0.0
    after_accuracy: float = 0.0
    improvement: float = 0.0
    confusion_matrix: Dict[str, int] = field(default_factory=dict)
    sample_results: List[Dict] = field(default_factory=list)

class FactCheckEvaluator:
    """事实核查评估器"""

    def __init__(self, use_mock_model: bool = True):
        self.use_mock_model = use_mock_model
        self.results = []
        self.metrics_calculator = MetricsCalculator()

    def evaluate_single(
        self,
        fact: str,
        ground_truth: bool,
        metadata: Dict
    ) -> Dict[str, Any]:
        """评估单个陈述"""
        if self.use_mock_model:
            predicted = self._mock_predict(fact)
        else:
            predicted = self._model_predict(fact)

        is_correct = (predicted == ground_truth)

        return {
            "fact": fact,
            "ground_truth": ground_truth,
            "predicted": predicted,
            "is_correct": is_correct,
        }

    def _mock_predict(self, fact: str) -> bool:
        """模拟预测"""
        import random
        random.seed(hash(fact) % 1000000)

        error_rate = 0.25
        has_numbers = any(c.isdigit() for c in fact)

        if has_numbers:
            if random.random() < error_rate:
                return not random.choice([True, False])
            return random.choice([True, False])
        else:
            return random.choice([True, False])

    def _model_predict(self, fact: str) -> bool:
        """使用真实模型预测"""
        raise NotImplementedError("需要加载真实模型")

    def evaluate_batch(
        self,
        facts: List[str],
        ground_truths: List[bool],
        metadata_list: List[Dict] = None
    ) -> Dict[str, Any]:
        """批量评估"""
        if len(facts) != len(ground_truths):
            raise ValueError("facts 和 ground_truths 长度不一致")

        if metadata_list is None:
            metadata_list = [{}] * len(facts)

        self.results = []
        predictions = []
        labels = []

        for fact, gt, meta in zip(facts, ground_truths, metadata_list):
            result = self.evaluate_single(fact, gt, meta)
            self.results.append(result)
            predictions.append(result["predicted"])
            labels.append(result["ground_truth"])

        metrics = self._compute_metrics(predictions, labels)

        return {
            "metrics": metrics,
            "results": self.results,
        }

    def _compute_metrics(
        self,
        predictions: List[bool],
        labels: List[bool]
    ) -> EvaluationMetrics:
        """计算指标"""
        tp = sum(1 for p, l in zip(predictions, labels) if p and l)
        fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
        tn = sum(1 for p, l in zip(predictions, labels) if not p and not l)
        fn = sum(1 for p, l in zip(predictions, labels) if not p and l)

        total = len(predictions)
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            total_samples=total,
            true_positive=tp,
            false_positive=fp,
            true_negative=tn,
            false_negative=fn,
        )

    def evaluate_with_filtering(
        self,
        facts: List[str],
        ground_truths: List[bool],
        filter_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """评估过滤后的结果"""
        results_before = []
        results_after = []

        for fact, gt in zip(facts, ground_truths):
            before_pred = self._mock_predict(fact)
            before_correct = (before_pred == gt)
            results_before.append(before_correct)

            if filter_func and not before_correct:
                after_pred = filter_func(fact)
                after_correct = (after_pred == gt)
            else:
                after_pred = before_pred
                after_correct = before_correct

            results_after.append(after_correct)

        accuracy_before = sum(results_before) / len(results_before) if results_before else 0
        accuracy_after = sum(results_after) / len(results_after) if results_after else 0
        improvement = accuracy_after - accuracy_before

        return {
            "before_accuracy": accuracy_before,
            "after_accuracy": accuracy_after,
            "improvement": improvement,
            "error_rate_before": 1 - accuracy_before,
            "error_rate_after": 1 - accuracy_after,
            "error_reduction": (1 - accuracy_after) / (1 - accuracy_before) if accuracy_before < 1 else 0,
        }


class MetricsCalculator:
    """指标计算器"""

    @staticmethod
    def compute_all_metrics(
        predictions: List[bool],
        labels: List[bool]
    ) -> Dict[str, float]:
        """计算所有指标"""
        tp = sum(1 for p, l in zip(predictions, labels) if p and l)
        fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
        tn = sum(1 for p, l in zip(predictions, labels) if not p and not l)
        fn = sum(1 for p, l in zip(predictions, labels) if not p and l)

        total = len(predictions)

        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
            "total": total,
        }

    @staticmethod
    def compute_harmlessness_rate(
        flagged_as_wrong: List[bool],
        actually_wrong: List[bool]
    ) -> float:
        """计算无伤害率"""
        harmless = sum(1 for fw, aw in zip(flagged_as_wrong, actually_wrong)
                      if not fw or aw)
        total = len(flagged_as_wrong)
        return harmless / total if total > 0 else 0


def evaluate_vlm_improvement(
    vlm_predictions: List[bool],
    checker_predictions: List[bool],
    ground_truths: List[bool]
) -> Dict[str, Any]:
    """评估VLM改进效果"""
    vlm_accuracy = sum(p == g for p, g in zip(vlm_predictions, ground_truths)) / len(ground_truths)
    checker_accuracy = sum(p == g for p, g in zip(checker_predictions, ground_truths)) / len(ground_truths)

    improvement = checker_accuracy - vlm_accuracy

    vlm_errors = [i for i, (p, g) in enumerate(zip(vlm_predictions, ground_truths)) if p != g]
    checker_errors = [i for i, (p, g) in enumerate(zip(checker_predictions, ground_truths)) if p != g]

    errors_fixed = len(set(vlm_errors) - set(checker_errors))
    errors_introduced = len(set(checker_errors) - set(vlm_errors))

    return {
        "vlm_accuracy": vlm_accuracy,
        "checker_accuracy": checker_accuracy,
        "improvement": improvement,
        "errors_fixed": errors_fixed,
        "errors_introduced": errors_introduced,
        "net_improvement": errors_fixed - errors_introduced,
    }


def analyze_class_distribution(predictions: List[bool], labels: List[bool]) -> Dict[str, Any]:
    """分析类别分布"""
    total = len(predictions)
    predicted_positive = sum(predictions)
    actual_positive = sum(labels)

    return {
        "total": total,
        "predicted_positive": predicted_positive,
        "predicted_negative": total - predicted_positive,
        "actual_positive": actual_positive,
        "actual_negative": total - actual_positive,
        "predicted_positive_ratio": predicted_positive / total,
        "actual_positive_ratio": actual_positive / total,
        "bias": abs(predicted_positive / total - actual_positive / total),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("事实核查评估器测试")
    print("=" * 60)

    evaluator = FactCheckEvaluator(use_mock_model=True)

    test_facts = [
        "苹果的数值是42",
        "香蕉的数值是78",
        "橙子的数值是65",
    ]
    test_truths = [True, True, False]

    results = evaluator.evaluate_batch(test_facts, test_truths)

    print("\n评估结果:")
    print(f"  准确率: {results['metrics'].accuracy:.4f}")
    print(f"  精确率: {results['metrics'].precision:.4f}")
    print(f"  召回率: {results['metrics'].recall:.4f}")
    print(f"  F1: {results['metrics'].f1:.4f}")

    print("\n混淆矩阵:")
    print(f"  TP: {results['metrics'].true_positive}")
    print(f"  FP: {results['metrics'].false_positive}")
    print(f"  TN: {results['metrics'].true_negative}")
    print(f"  FN: {results['metrics'].false_negative}")
