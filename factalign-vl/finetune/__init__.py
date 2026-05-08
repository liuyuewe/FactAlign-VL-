"""
微调模块初始化
"""

from .lora_config import LoRAConfigManager, get_trainable_parameters, create_training_arguments
from .dataset import QwenVLFactCheckDataset, DataCollatorForVisionLanguageModeling, load_datasets
from .trainer import FactCheckTrainer, train_with_default_config
from .inference import FactChecker, load_fact_checker, demo_fact_check
from .metrics import MetricsCalculator, TrainingMonitor, analyze_class_balance, print_balance_analysis
from .sampler import BalancedSampler, balance_dataset, oversample_minority_class, compute_class_weights, analyze_dataset_balance, print_balance_report
from .callbacks import EvaluationCallback, PredictionMonitorCallback, EarlyStoppingCallback, create_evaluation_function

__all__ = [
    'LoRAConfigManager',
    'get_trainable_parameters',
    'create_training_arguments',
    'QwenVLFactCheckDataset',
    'DataCollatorForVisionLanguageModeling',
    'load_datasets',
    'FactCheckTrainer',
    'train_with_default_config',
    'FactChecker',
    'load_fact_checker',
    'demo_fact_check',
    'MetricsCalculator',
    'TrainingMonitor',
    'analyze_class_balance',
    'print_balance_analysis',
    'BalancedSampler',
    'balance_dataset',
    'oversample_minority_class',
    'compute_class_weights',
    'analyze_dataset_balance',
    'print_balance_report',
    'EvaluationCallback',
    'PredictionMonitorCallback',
    'EarlyStoppingCallback',
    'create_evaluation_function',
]
