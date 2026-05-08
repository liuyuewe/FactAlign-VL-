"""
LoRA微调配置模块
使用PEFT库配置Qwen-VL-Chat的LoRA微调
"""

import os
import torch
from pathlib import Path
from typing import Optional, Dict, Any
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

try:
    from transformers import (
        AutoProcessor,
        TrainingArguments,
        Trainer,
    )
    from transformers import AutoModelForVision2Seq
except ImportError:
    AutoModelForVision2Seq = None
    AutoProcessor = None
    TrainingArguments = None
    Trainer = None

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

DEFAULT_MODEL_NAME = "Qwen/Qwen-VL-Chat"

LORA_CONFIG = {
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "bias": "none",
    "task_type": TaskType.CAUSAL_LM,
}

TRAINING_CONFIG = {
    "output_dir": str(MODELS_DIR / "factcheck_lora"),
    "num_train_epochs": 3,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 8,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "lr_scheduler_type": "cosine",
    "logging_steps": 10,
    "save_steps": 100,
    "eval_steps": 100,
    "evaluation_strategy": "steps",
    "save_total_limit": 2,
    "bf16": False,
    "fp16": True,
    "report_to": "none",
    "remove_unused_columns": False,
    "optim": "adamw_torch",
}

class LoRAConfigManager:
    """LoRA配置管理器"""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        device: str = "auto"
    ):
        self.model_name = model_name
        self.lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=LORA_CONFIG["target_modules"],
            bias=LORA_CONFIG["bias"],
            task_type=LORA_CONFIG["task_type"],
        )

        self.device = self._get_device(device)
        self.processor = None
        self.model = None

    def _get_device(self, device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device

    def load_base_model(self, load_in_8bit: bool = False, load_in_4bit: bool = False):
        """加载基座模型"""
        print(f"加载基座模型: {self.model_name}")

        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_name,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                load_in_8bit=load_in_8bit,
                load_in_4bit=load_in_4bit,
                trust_remote_code=True
            )

            print(f"模型加载成功，使用设备: {self.device}")
            return self.model, self.processor

        except Exception as e:
            print(f"模型加载失败: {e}")
            raise

    def apply_lora(self, model=None):
        """应用LoRA适配器"""
        if model is None:
            model = self.model

        if model is None:
            raise ValueError("需要先加载模型")

        print("应用LoRA适配器...")
        print(f"LoRA配置: r={self.lora_config.r}, alpha={self.lora_config.lora_alpha}")

        model = get_peft_model(model, self.lora_config)
        model.print_trainable_parameters()

        return model

    def save_lora(self, output_dir: str = None):
        """保存LoRA权重"""
        if output_dir is None:
            output_dir = str(MODELS_DIR / "factcheck_lora")

        if self.model is None:
            raise ValueError("需要先加载模型")

        os.makedirs(output_dir, exist_ok=True)

        self.model.save_pretrained(output_dir)
        print(f"LoRA权重已保存到: {output_dir}")

        config_path = Path(output_dir) / "lora_config.json"
        config_dict = {
            "model_name": self.model_name,
            "lora_r": self.lora_config.r,
            "lora_alpha": self.lora_config.lora_alpha,
            "lora_dropout": self.lora_config.lora_dropout,
            "target_modules": self.lora_config.target_modules,
        }

        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        return output_dir

    def load_lora(self, lora_path: str, base_model=None):
        """加载LoRA权重"""
        if base_model is None:
            base_model = self.model

        if base_model is None:
            raise ValueError("需要先加载基座模型")

        print(f"加载LoRA权重: {lora_path}")

        self.model = PeftModel.from_pretrained(base_model, lora_path)
        print("LoRA权重加载成功")

        return self.model

def create_training_arguments(**kwargs) -> TrainingArguments:
    """创建训练参数"""
    config = TRAINING_CONFIG.copy()
    config.update(kwargs)

    output_dir = config.pop("output_dir")

    return TrainingArguments(
        output_dir=output_dir,
        **config
    )

def get_trainable_parameters(model) -> Dict[str, int]:
    """获取可训练参数统计"""
    trainable_params = 0
    all_params = 0

    for _, param in model.named_parameters():
        all_params += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()

    return {
        "trainable_params": trainable_params,
        "all_params": all_params,
        "trainable_percentage": 100 * trainable_params / all_params if all_params > 0 else 0
    }

def print_model_info(model):
    """打印模型信息"""
    info = get_trainable_parameters(model)
    print("\n模型参数统计:")
    print(f"  可训练参数: {info['trainable_params']:,}")
    print(f"  总参数: {info['all_params']:,}")
    print(f"  可训练比例: {info['trainable_percentage']:.2f}%")

if __name__ == "__main__":
    print("=" * 60)
    print("LoRA配置测试")
    print("=" * 60)

    config_manager = LoRAConfigManager(
        lora_r=8,
        lora_alpha=16,
        lora_dropout=0.05
    )

    print("\nLoRA配置:")
    print(f"  r (秩): {config_manager.lora_config.r}")
    print(f"  alpha: {config_manager.lora_config.lora_alpha}")
    print(f"  dropout: {config_manager.lora_config.lora_dropout}")
    print(f"  target_modules: {config_manager.lora_config.target_modules}")

    print("\n注意: 需要加载模型才能测试完整功能")
