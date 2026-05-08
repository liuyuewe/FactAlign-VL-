"""
模型训练模块
使用HuggingFace Trainer进行LoRA微调
"""

import os
import sys
import json
import torch
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from transformers import (
        AutoProcessor,
        AutoModelForVision2Seq,
        TrainingArguments,
        Trainer,
        set_seed
    )
    from peft import get_peft_model, LoraConfig
except ImportError:
    AutoModelForVision2Seq = None
    AutoProcessor = None
    TrainingArguments = None
    Trainer = None
    get_peft_model = None
    LoraConfig = None

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONVERTED_DIR = PROJECT_ROOT / "data" / "converted"
MODELS_DIR = PROJECT_ROOT / "models"
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"

sys.path.insert(0, str(PROJECT_ROOT / "factalign-vl"))

from finetune.dataset import QwenVLFactCheckDataset, DataCollatorForVisionLanguageModeling
from finetune.lora_config import LoRAConfigManager, get_trainable_parameters

DEFAULT_MODEL_NAME = "Qwen/Qwen-VL-Chat"

class FactCheckTrainer:
    """事实核查模型训练器"""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        output_dir: str = None,
        device: str = "auto"
    ):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.processor = None
        self.model = None
        self.trainer = None

        if output_dir is None:
            output_dir = str(MODELS_DIR / "factcheck_lora")

        self.output_dir = output_dir
        self.lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=["q_proj", "v_proj"],
            bias="none",
            task_type=None
        )

    def _get_device(self, device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device

    def load_model(self, load_in_4bit: bool = False):
        """加载模型和处理器"""
        print("=" * 60)
        print("加载模型")
        print("=" * 60)
        print(f"模型: {self.model_name}")
        print(f"设备: {self.device}")

        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_name,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                load_in_4bit=load_in_4bit,
                trust_remote_code=True
            )

            print("应用LoRA适配器...")
            self.model = get_peft_model(self.model, self.lora_config)

            info = get_trainable_parameters(self.model)
            print(f"\n可训练参数: {info['trainable_params']:,} ({info['trainable_percentage']:.2f}%)")

            return self.model, self.processor

        except Exception as e:
            print(f"加载失败: {e}")
            raise

    def prepare_datasets(
        self,
        train_path: str or Path,
        val_path: Optional[str or Path] = None,
        max_length: int = 512,
        image_folder: Optional[str] = None
    ):
        """准备训练数据集"""
        print("\n准备数据集...")

        self.train_dataset = QwenVLFactCheckDataset(
            data_path=train_path,
            processor=self.processor,
            max_length=max_length,
            image_folder=image_folder
        )

        self.val_dataset = None
        if val_path and Path(val_path).exists():
            self.val_dataset = QwenVLFactCheckDataset(
                data_path=val_path,
                processor=self.processor,
                max_length=max_length,
                image_folder=image_folder
            )

        print(f"训练集: {len(self.train_dataset)} 条")
        if self.val_dataset:
            print(f"验证集: {len(self.val_dataset)} 条")

        self.data_collator = DataCollatorForVisionLanguageModeling(
            processor=self.processor,
            max_length=max_length
        )

    def train(
        self,
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 1,
        gradient_accumulation_steps: int = 8,
        learning_rate: float = 2e-4,
        warmup_ratio: float = 0.1,
        logging_steps: int = 10,
        save_steps: int = 100,
        eval_steps: int = 100,
        fp16: bool = True,
        **kwargs
    ):
        """开始训练"""
        if self.model is None or self.train_dataset is None:
            raise ValueError("需要先加载模型和数据集")

        print("\n" + "=" * 60)
        print("开始训练")
        print("=" * 60)

        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_ratio=warmup_ratio,
            lr_scheduler_type="cosine",
            logging_steps=logging_steps,
            save_steps=save_steps,
            eval_steps=eval_steps,
            evaluation_strategy="steps" if self.val_dataset else "no",
            save_total_limit=2,
            fp16=fp16 and self.device == "cuda",
            bf16=False,
            report_to="none",
            remove_unused_columns=False,
            optim="adamw_torch",
            **kwargs
        )

        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            data_collator=self.data_collator,
        )

        train_result = self.trainer.train()

        self.trainer.save_model(self.output_dir)

        metrics = train_result.metrics
        self.trainer.log_metrics("train", metrics)
        self.trainer.save_metrics("train", metrics)

        print("\n训练完成！")
        print(f"模型保存到: {self.output_dir}")

        return train_result

    def evaluate(self):
        """评估模型"""
        if self.trainer is None or self.val_dataset is None:
            print("没有验证集或训练器未初始化")
            return None

        print("\n评估模型...")
        metrics = self.trainer.evaluate()
        self.trainer.log_metrics("eval", metrics)
        self.trainer.save_metrics("eval", metrics)

        return metrics

    def save_model(self, output_dir: str = None):
        """保存模型"""
        if output_dir is None:
            output_dir = self.output_dir

        if self.model is not None:
            self.model.save_pretrained(output_dir)
            print(f"模型已保存: {output_dir}")

            config_path = Path(output_dir) / "training_config.json"
            config = {
                "model_name": self.model_name,
                "lora_r": self.lora_config.r,
                "lora_alpha": self.lora_config.lora_alpha,
                "lora_dropout": self.lora_config.lora_dropout
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)


def train_with_default_config(
    model_name: str = DEFAULT_MODEL_NAME,
    train_data_path: str = None,
    val_data_path: str = None,
    output_dir: str = None,
    use_small_dataset: bool = False
):
    """使用默认配置训练"""
    set_seed(42)

    if output_dir is None:
        output_dir = str(MODELS_DIR / "factcheck_lora")

    if train_data_path is None:
        train_data_path = CONVERTED_DIR / "train_qwen_format.json"

    if val_data_path is None:
        val_data_path = CONVERTED_DIR / "val_qwen_format.json"

    if not Path(train_data_path).exists():
        print(f"训练数据不存在: {train_data_path}")
        print("请先运行数据转换")
        return None

    trainer = FactCheckTrainer(
        model_name=model_name,
        output_dir=output_dir
    )

    try:
        trainer.load_model(load_in_4bit=True)
    except Exception as e:
        print(f"模型加载失败: {e}")
        print("将创建模拟训练流程用于演示")
        return None

    trainer.prepare_datasets(
        train_path=train_data_path,
        val_path=val_data_path if Path(val_data_path).exists() else None
    )

    trainer.train(
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4
    )

    return trainer


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="训练事实核查模型")
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME)
    parser.add_argument("--train_data", type=str, default=None)
    parser.add_argument("--val_data", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=2e-4)

    args = parser.parse_args()

    print("=" * 60)
    print("FactAlign-VL 训练脚本")
    print("=" * 60)

    trainer = train_with_default_config(
        model_name=args.model_name,
        train_data_path=args.train_data,
        val_data_path=args.val_data,
        output_dir=args.output_dir
    )

    if trainer is not None:
        print("\n✅ 训练完成！")
        print(f"模型位置: {trainer.output_dir}")
