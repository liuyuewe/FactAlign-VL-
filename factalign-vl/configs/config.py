"""
项目配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# 模型配置
MODEL_CONFIG = {
    "vl_model": "Qwen/Qwen-VL-Chat",
    "text_model": "Qwen/Qwen-7B-Chat",
    "device": "auto",
}

# SpaCy 配置
SPACY_MODEL = "zh_core_web_sm"

# 证据检索配置
EVIDENCE_CONFIG = {
    "top_k": 5,
    "similarity_threshold": 0.7,
}

# Gradio 配置
GRADIO_CONFIG = {
    "server_name": "0.0.0.0",
    "server_port": 7860,
    "share": False,
}
