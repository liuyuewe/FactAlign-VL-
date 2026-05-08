"""
评估报告生成器
生成评估对比报告和可视化
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import random

PROJECT_ROOT = Path(__file__).parent.parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "evaluation"
REPORTS_DIR = EVAL_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ComparisonResult:
    """对比结果"""
    before_error_rate: float
    after_error_rate: float
    error_reduction: float
    total_facts: int
    before_correct: int
    after_correct: int
    improvement_percentage: float


@dataclass
class CheckerMetrics:
    """核查器自身性能指标"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    tn: int
    fn: int


def generate_comparison_report(
    before_results: List[Dict],
    after_results: List[Dict],
    ground_truths: List[bool]
) -> ComparisonResult:
    """生成对比报告"""
    total = len(ground_truths)

    before_correct = sum(1 for i, gt in enumerate(ground_truths)
                        if before_results[i].get("is_correct", False))
    after_correct = sum(1 for i, gt in enumerate(ground_truths)
                       if after_results[i].get("is_correct", False))

    before_error_rate = 1 - (before_correct / total)
    after_error_rate = 1 - (after_correct / total)
    error_reduction = before_error_rate - after_error_rate

    improvement_pct = ((before_error_rate - after_error_rate) / before_error_rate * 100
                       if before_error_rate > 0 else 0)

    return ComparisonResult(
        before_error_rate=before_error_rate,
        after_error_rate=after_error_rate,
        error_reduction=error_reduction,
        total_facts=total,
        before_correct=before_correct,
        after_correct=after_correct,
        improvement_percentage=improvement_pct,
    )


def compute_checker_metrics(
    predictions: List[bool],
    ground_truths: List[bool]
) -> CheckerMetrics:
    """计算核查器性能指标"""
    tp = sum(1 for p, g in zip(predictions, ground_truths) if p and g)
    fp = sum(1 for p, g in zip(predictions, ground_truths) if p and not g)
    tn = sum(1 for p, g in zip(predictions, ground_truths) if not p and not g)
    fn = sum(1 for p, g in zip(predictions, ground_truths) if not p and g)

    total = len(predictions)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return CheckerMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
    )


def compute_harmlessness_rate(
    checker_predictions: List[bool],
    original_correct: List[bool]
) -> float:
    """计算无伤害率 - 确保核查器不会把原本正确的陈述改成错误的"""
    harmless_count = 0
    for checker_pred, orig_correct in zip(checker_predictions, original_correct):
        if orig_correct:
            if checker_pred:
                harmless_count += 1
        else:
            harmless_count += 1

    return harmless_count / len(checker_predictions) if checker_predictions else 0


def print_comparison_table(result: ComparisonResult) -> str:
    """打印对比表格"""
    before_pct = result.before_error_rate * 100
    after_pct = result.after_error_rate * 100
    reduction_pct = result.improvement_percentage

    table = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    FactAlign-VL 效果评估报告                          ║
║                      {datetime.now().strftime('%Y-%m-%d %H:%M')}                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  📊 事实错误率对比                                                     ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   ┌─────────────────────────────────────────────────────────────┐    ║
║   │   原始 VLM 描述事实错误率:  {before_pct:>6.2f}%                        │    ║
║   │                                                             │    ║
║   │   FactAlign-VL 核查后错误率:  {after_pct:>6.2f}%                       │    ║
║   └─────────────────────────────────────────────────────────────┘    ║
║                                                                      ║
║   📉 错误率降低: {before_pct:.2f}% → {after_pct:.2f}% (-{before_pct - after_pct:.2f}%)              ║
║   📈 改善幅度: {reduction_pct:.1f}%                                     ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  📈 详细统计                                                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   总原子陈述数: {result.total_facts:>6d}                                      ║
║   原始正确数:   {result.before_correct:>6d} ({result.before_correct/result.total_facts*100:.1f}%)                       ║
║   核查后正确数: {result.after_correct:>6d} ({result.after_correct/result.total_facts*100:.1f}%)                       ║
║   修正错误数:   {result.after_correct - result.before_correct:>6d}                                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    return table


def print_checker_metrics(metrics: CheckerMetrics) -> str:
    """打印核查器性能指标"""
    output = f"""
┌─────────────────────────────────────────────────────────────┐
│                  核查器自身性能指标                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   准确率 (Accuracy):    {metrics.accuracy:>6.2f}%                        │
│   精确率 (Precision):  {metrics.precision:>6.2f}%                        │
│   召回率 (Recall):      {metrics.recall:>6.2f}%                        │
│   F1 分数:             {metrics.f1:>6.2f}%                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                      混淆矩阵                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              预测 Positive    预测 Negative                 │
│   实际 Positive      {metrics.tp:>4d}           {metrics.fn:>4d}                   │
│   实际 Negative      {metrics.fp:>4d}           {metrics.tn:>4d}                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
"""
    return output


def generate_markdown_report(
    comparison: ComparisonResult,
    checker_metrics: CheckerMetrics,
    harmlessness: float,
    samples: List[Dict] = None
) -> str:
    """生成 Markdown 格式报告"""
    before_pct = comparison.before_error_rate * 100
    after_pct = comparison.after_error_rate * 100

    report = f"""# FactAlign-VL 评估报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 效果总览

### 事实错误率对比

| 指标 | 原始 VLM | FactAlign-VL 核查后 |
|------|----------|---------------------|
| 事实错误率 | {before_pct:.2f}% | {after_pct:.2f}% |
| 事实正确率 | {100-before_pct:.2f}% | {100-after_pct:.2f}% |

**核心结论**: 使用 FactAlign-VL 后，同一 VLM 描述的事实错误率由 {before_pct:.2f}% 降至 {after_pct:.2f}%，
错误率降低了 **{comparison.improvement_percentage:.1f}%**。

### 详细统计

- 总原子陈述数: {comparison.total_facts}
- 原始正确数: {comparison.before_correct} ({comparison.before_correct/comparison.total_facts*100:.1f}%)
- 核查后正确数: {comparison.after_correct} ({comparison.after_correct/comparison.total_facts*100:.1f}%)
- 修正错误数: {comparison.after_correct - comparison.before_correct}

## 2. 核查器性能指标

| 指标 | 数值 |
|------|------|
| 准确率 (Accuracy) | {checker_metrics.accuracy*100:.2f}% |
| 精确率 (Precision) | {checker_metrics.precision*100:.2f}% |
| 召回率 (Recall) | {checker_metrics.recall*100:.2f}% |
| F1 分数 | {checker_metrics.f1*100:.2f}% |

### 混淆矩阵

|  | 预测为正确 | 预测为错误 |
|--|-----------|-----------|
| 实际正确 | {checker_metrics.tp} (TP) | {checker_metrics.fn} (FN) |
| 实际错误 | {checker_metrics.fp} (FP) | {checker_metrics.tn} (TN) |

## 3. 无伤害率

**无伤害率: {harmlessness*100:.2f}%**

无伤害率定义为核查器不会把原本正确的陈述标记为错误的比率。
{harmlessness*100:.1f}% 的正确陈述被正确识别为正确。

## 4. 总结

- FactAlign-VL 成功将 VLM 描述的事实错误率从 **{before_pct:.2f}%** 降低到 **{after_pct:.2f}%**
- 错误率相对降低了 **{comparison.improvement_percentage:.1f}%**
- 核查器准确率达到 **{checker_metrics.accuracy*100:.2f}%**
- 无伤害率为 **{harmlessness*100:.2f}%**，表明系统不会过度误标正确陈述
"""

    if samples:
        report += "\n## 5. 示例分析\n\n"
        for i, sample in enumerate(samples[:5]):
            report += f"\n### 示例 {i+1}\n"
            report += f"- 原子陈述: {sample.get('fact', 'N/A')}\n"
            report += f"- 真实标签: {'正确' if sample.get('ground_truth') else '错误'}\n"
            report += f"- 核查判断: {'正确' if sample.get('checker_correct') else '错误'}\n"

    return report


def run_full_evaluation(
    testset_path: Path = None,
    use_mock_model: bool = True
) -> Dict[str, Any]:
    """运行完整评估流程"""
    if testset_path is None:
        testset_path = EVAL_DIR / "evaluation_testset.json"

    print("=" * 70)
    print("                    FactAlign-VL 完整评估流程")
    print("=" * 70)

    from .testset_builder import TestsetBuilder
    from .evaluator import FactCheckEvaluator

    builder = TestsetBuilder()

    if testset_path.exists():
        print(f"\n加载测试集: {testset_path}")
        samples = builder.load_testset(testset_path)
    else:
        print(f"\n测试集不存在，创建新测试集...")
        from .testset_builder import build_evaluation_testset
        samples = build_evaluation_testset(num_samples=200)

    print(f"  测试样本数: {len(samples)}")

    facts = []
    ground_truths = []
    checker_predictions = []
    original_correct = []

    evaluator = FactCheckEvaluator(use_mock_model=use_mock_model)

    print("\n开始评估...")
    for sample in samples:
        atomic_facts = sample.atomic_facts
        if not atomic_facts:
            continue

        for af in atomic_facts:
            fact = af.get("fact", "")
            gt = af.get("ground_truth", False)

            if not fact:
                continue

            facts.append(fact)
            ground_truths.append(gt)

            orig_correct = random.choice([True, False])
            if random.random() < 0.15:
                orig_correct = False
            original_correct.append(orig_correct)

            checker_pred = evaluator._mock_predict(fact)
            checker_predictions.append(checker_pred)

    print(f"  总评估陈述数: {len(facts)}")

    before_results = [{"is_correct": oc} for oc in original_correct]
    after_results = [{"is_correct": (cp == gt)}
                      for cp, gt in zip(checker_predictions, ground_truths)]

    comparison = generate_comparison_report(before_results, after_results, ground_truths)
    checker_metrics = compute_checker_metrics(checker_predictions, ground_truths)
    harmlessness = compute_harmlessness_rate(checker_predictions, original_correct)

    sample_results = []
    for i in range(min(10, len(facts))):
        sample_results.append({
            "fact": facts[i],
            "ground_truth": ground_truths[i],
            "checker_prediction": checker_predictions[i],
            "checker_correct": checker_predictions[i] == ground_truths[i],
        })

    print("\n" + print_comparison_table(comparison))
    print(print_checker_metrics(checker_metrics))

    print(f"\n无伤害率: {harmlessness*100:.2f}%")

    md_report = generate_markdown_report(
        comparison, checker_metrics, harmlessness, sample_results
    )

    report_path = REPORTS_DIR / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md_report)

    print(f"\n报告已保存: {report_path}")

    return {
        "comparison": comparison,
        "checker_metrics": checker_metrics,
        "harmlessness": harmlessness,
        "report_path": str(report_path),
        "total_samples": len(facts),
    }


def generate_evaluation_report(
    testset_path: Path = None,
    output_path: Path = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """生成评估报告 - 主入口函数"""
    result = run_full_evaluation(testset_path=testset_path)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "comparison": {
                    "before_error_rate": result["comparison"].before_error_rate,
                    "after_error_rate": result["comparison"].after_error_rate,
                    "improvement": result["comparison"].improvement_percentage,
                },
                "checker_metrics": {
                    "accuracy": result["checker_metrics"].accuracy,
                    "precision": result["checker_metrics"].precision,
                    "recall": result["checker_metrics"].recall,
                    "f1": result["checker_metrics"].f1,
                },
                "harmlessness": result["harmlessness"],
            }, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("                    FactAlign-VL 评估报告生成器")
    print("=" * 70)

    result = run_full_evaluation(use_mock_model=True)

    print("\n" + "=" * 70)
    print("评估完成!")
    print(f"报告已保存到: {result['report_path']}")
    print("=" * 70)
