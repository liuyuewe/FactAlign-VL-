"""
FactAlign-VL 评估模块
"""

from .testset_builder import build_evaluation_testset, create_dedicated_testset, TestsetBuilder
from .evaluator import FactCheckEvaluator, EvaluationMetrics, EvaluationReport, MetricsCalculator
from .report_generator import generate_evaluation_report, print_comparison_table, print_checker_metrics, generate_markdown_report, run_full_evaluation

__all__ = [
    'build_evaluation_testset',
    'create_dedicated_testset',
    'TestsetBuilder',
    'FactCheckEvaluator',
    'EvaluationMetrics',
    'EvaluationReport',
    'MetricsCalculator',
    'generate_evaluation_report',
    'print_comparison_table',
    'print_checker_metrics',
    'generate_markdown_report',
    'run_full_evaluation',
]
