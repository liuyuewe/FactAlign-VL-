"""
自定义评估回调
用于在训练过程中监控模型性能
"""

import json
import torch
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

try:
    from transformers import TrainerCallback, TrainerControl, TrainerState
    from transformers.trainer_callback import TrainerCallback
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    TrainerCallback = object

@dataclass
class EvaluationResult:
    """评估结果"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    total_samples: int
    positive_samples: int
    negative_samples: int
    confusion_matrix: tuple

class EvaluationCallback(TrainerCallback if TRANSFORMERS_AVAILABLE else object):
    """评估回调"""

    def __init__(
        self,
        eval_func: Callable,
        eval_steps: int = 100,
        log_file: Optional[str] = None,
        save_best: bool = True,
        metric_for_best: str = "accuracy",
        greater_is_better: bool = True
    ):
        self.eval_func = eval_func
        self.eval_steps = eval_steps
        self.log_file = log_file
        self.save_best = save_best
        self.metric_for_best = metric_for_best
        self.greater_is_better = greater_is_better

        self.best_metric = float('-inf') if greater_is_better else float('inf')
        self.eval_history = []

        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    def on_step_end(
        self,
        args,
        state: TrainerState,
        control: TrainerControl,
        **kwargs
    ):
        """在每个训练步骤结束时调用"""
        if state.global_step % self.eval_steps == 0 and state.global_step > 0:
            print(f"\n[Step {state.global_step}] 开始评估...")

            try:
                eval_result = self.eval_func()

                self.eval_history.append({
                    "step": state.global_step,
                    "metrics": eval_result
                })

                self._log_metrics(eval_result, state.global_step)

                if self.save_best:
                    current_metric = eval_result.get(self.metric_for_best, 0)
                    is_better = (
                        current_metric > self.best_metric if self.greater_is_better
                        else current_metric < self.best_metric
                    )

                    if is_better:
                        self.best_metric = current_metric
                        print(f"  ✅ 新的最佳 {self.metric_for_best}: {current_metric:.4f}")

                if self.log_file:
                    self._save_to_file(eval_result, state.global_step)

            except Exception as e:
                print(f"  ❌ 评估失败: {e}")

    def _log_metrics(self, metrics: Dict, step: int):
        """记录指标"""
        print(f"\n评估结果 [Step {step}]:")
        print(f"  准确率: {metrics.get('accuracy', 0):.4f}")
        print(f"  精确率: {metrics.get('precision', 0):.4f}")
        print(f"  召回率: {metrics.get('recall', 0):.4f}")
        print(f"  F1分数: {metrics.get('f1', 0):.4f}")

        if 'total_samples' in metrics:
            print(f"  样本数: {metrics['total_samples']}")
            print(f"  正样本: {metrics.get('positive_samples', 0)}")
            print(f"  负样本: {metrics.get('negative_samples', 0)}")

        if 'confusion_matrix' in metrics:
            cm = metrics['confusion_matrix']
            print(f"  混淆矩阵:")
            print(f"    TP={cm[0]}, FP={cm[1]}")
            print(f"    FN={cm[2]}, TN={cm[3]}")

    def _save_to_file(self, metrics: Dict, step: int):
        """保存到文件"""
        record = {
            "step": step,
            "metrics": metrics
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    def get_best_metrics(self) -> Dict[str, float]:
        """获取最佳指标"""
        return {"best_metric": self.best_metric, "metric_name": self.metric_for_best}

    def get_eval_history(self) -> List[Dict]:
        """获取评估历史"""
        return self.eval_history


class PredictionMonitorCallback(TrainerCallback if TRANSFORMERS_AVAILABLE else object):
    """预测监控回调 - 监控模型是否偏向某个类别"""

    def __init__(
        self,
        prediction_log_file: Optional[str] = None,
        window_size: int = 500
    ):
        self.prediction_log_file = prediction_log_file
        self.window_size = window_size
        self.recent_predictions = []
        self.recent_labels = []

        if prediction_log_file:
            Path(prediction_log_file).parent.mkdir(parents=True, exist_ok=True)

    def on_evaluate(
        self,
        args,
        state: TrainerState,
        control: TrainerControl,
        metrics: Dict[str, float],
        **kwargs
    ):
        """在评估后调用"""
        if 'eval_predictions' in metrics and 'eval_labels' in metrics:
            predictions = metrics['eval_predictions']
            labels = metrics['eval_labels']

            self._analyze_predictions(predictions, labels, state.global_step)

    def _analyze_predictions(
        self,
        predictions: List[bool],
        labels: List[bool],
        step: int
    ):
        """分析预测结果"""
        if not predictions or not labels:
            return

        total = len(predictions)
        predicted_positive = sum(1 for p in predictions if p)
        actual_positive = sum(1 for l in labels if l)

        pred_pos_ratio = predicted_positive / total
        actual_pos_ratio = actual_positive / total

        bias = abs(pred_pos_ratio - actual_pos_ratio)

        warning = ""
        if bias > 0.2:
            warning = "⚠️ 严重偏向"
        elif bias > 0.1:
            warning = "⚡ 轻微偏向"

        if predicted_positive / total > 0.9:
            warning += " [模型倾向预测'是']"
        elif predicted_positive / total < 0.1:
            warning += " [模型倾向预测'否']"

        print(f"\n预测分析 [Step {step}]:")
        print(f"  预测正样本比例: {pred_pos_ratio:.2%}")
        print(f"  实际正样本比例: {actual_pos_ratio:.2%}")
        print(f"  偏向程度: {bias:.2%}")
        if warning:
            print(f"  {warning}")

        if self.prediction_log_file:
            record = {
                "step": step,
                "pred_pos_ratio": pred_pos_ratio,
                "actual_pos_ratio": actual_pos_ratio,
                "bias": bias,
                "warning": warning
            }
            with open(self.prediction_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')


def create_evaluation_function(
    model,
    val_dataset,
    processor,
    device: str = "cuda"
) -> callable:
    """创建评估函数"""
    def eval_func() -> Dict[str, Any]:
        from .metrics import MetricsCalculator

        calculator = MetricsCalculator()
        model.eval()

        predictions = []
        labels = []

        batch_size = 4
        for i in range(0, len(val_dataset), batch_size):
            batch = val_dataset[i:i + batch_size]

            for item in batch:
                try:
                    result = model.generate(item)
                    pred = "是" in result.lower()
                    label = item.get("label", False)

                    predictions.append(pred)
                    labels.append(label)
                except Exception as e:
                    continue

        calculator.update(predictions, labels)
        metrics = calculator.compute()

        return metrics

    return eval_func


class EarlyStoppingCallback(TrainerCallback if TRANSFORMERS_AVAILABLE else object):
    """早停回调"""

    def __init__(
        self,
        metric: str = "accuracy",
        patience: int = 3,
        min_delta: float = 0.001,
        greater_is_better: bool = True
    ):
        self.metric = metric
        self.patience = patience
        self.min_delta = min_delta
        self.greater_is_better = greater_is_better

        self.best_metric = float('-inf') if greater_is_better else float('inf')
        self.no_improve_count = 0

    def on_evaluate(
        self,
        args,
        state: TrainerState,
        control: TrainerControl,
        metrics: Dict[str, float],
        **kwargs
    ):
        """在评估后调用"""
        current_metric = metrics.get(f"eval_{self.metric}", None)

        if current_metric is None:
            return

        if self.greater_is_better:
            improved = current_metric > self.best_metric + self.min_delta
        else:
            improved = current_metric < self.best_metric - self.min_delta

        if improved:
            self.best_metric = current_metric
            self.no_improve_count = 0
        else:
            self.no_improve_count += 1

            if self.no_improve_count >= self.patience:
                print(f"\n早停: {self.metric} 在 {self.patience} 个评估周期内没有改善")
                control.should_training_stop = True


if __name__ == "__main__":
    print("=" * 60)
    print("评估回调模块测试")
    print("=" * 60)

    print("\n可用回调:")
    print("  1. EvaluationCallback - 定期评估并记录指标")
    print("  2. PredictionMonitorCallback - 监控预测偏向")
    print("  3. EarlyStoppingCallback - 早停")
    print("  4. create_evaluation_function - 创建评估函数")
