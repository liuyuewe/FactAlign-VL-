"""
合成数据工厂模块
用于生成带"绝对真值"的图表数据集
"""

from .chart_generator import ChartGenerator, generate_random_data, generate_time_series_data, generate_table_data, split_dataset
from .description_generator import DescriptionGenerator, load_all_metadata, save_descriptions_index
from .annotator import AtomicFactExtractor, FactLabeler, DatasetAnnotator, load_descriptions, split_descriptions

__all__ = [
    'ChartGenerator',
    'generate_random_data',
    'generate_time_series_data',
    'generate_table_data',
    'split_dataset',
    'DescriptionGenerator',
    'load_all_metadata',
    'save_descriptions_index',
    'AtomicFactExtractor',
    'FactLabeler',
    'DatasetAnnotator',
    'load_descriptions',
    'split_descriptions',
]
