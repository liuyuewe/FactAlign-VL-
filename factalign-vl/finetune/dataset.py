"""
数据集处理模块
为Qwen-VL模型准备训练数据
"""

import json
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from torch.utils.data import Dataset
from PIL import Image
import transformers
from transformers import AutoProcessor

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONVERTED_DIR = PROJECT_ROOT / "data" / "converted"

class QwenVLFactCheckDataset(Dataset):
    """Qwen-VL事实核查数据集"""

    def __init__(
        self,
        data_path: str or Path,
        processor: AutoProcessor,
        max_length: int = 512,
        image_folder: Optional[str] = None
    ):
        self.data_path = Path(data_path)
        self.processor = processor
        self.max_length = max_length
        self.image_folder = image_folder

        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        print(f"加载数据集: {len(self.data)} 条")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        conversations = item.get("conversations", [])

        if len(conversations) < 2:
            return self._get_empty_sample()

        user_msg = conversations[0]
        assistant_msg = conversations[1]

        image_path = None
        text_content = ""

        for content in user_msg.get("content", []):
            if content.get("type") == "image":
                image_path = content.get("image", "")
            elif content.get("type") == "text":
                text_content = content.get("text", "")

        if self.image_folder and image_path:
            image_path = str(Path(self.image_folder) / Path(image_path).name)

        try:
            if image_path and Path(image_path).exists():
                image = Image.open(image_path).convert("RGB")
            else:
                image = Image.new("RGB", (224, 224), color="white")
        except Exception:
            image = Image.new("RGB", (224, 224), color="white")

        prompt_text = text_content

        answer_text = assistant_msg.get("content", "")

        full_text = f"{prompt_text}\n{answer_text}"

        inputs = self.processor(
            text=[full_text],
            images=[image],
            return_tensors="pt",
            padding="max_length",
            max_length=self.max_length,
            truncation=True
        )

        input_ids = inputs["input_ids"].squeeze(0)
        pixel_values = inputs["pixel_values"].squeeze(0) if "pixel_values" in inputs else None

        labels = input_ids.clone()

        inputs["labels"] = labels
        inputs["input_ids"] = input_ids

        if pixel_values is not None:
            inputs["pixel_values"] = pixel_values

        return {
            "input_ids": input_ids,
            "labels": labels,
            "pixel_values": pixel_values if pixel_values is not None else torch.zeros(1),
            "attention_mask": torch.ones_like(input_ids),
        }

    def _get_empty_sample(self):
        return {
            "input_ids": torch.zeros(self.max_length, dtype=torch.long),
            "labels": torch.zeros(self.max_length, dtype=torch.long),
            "pixel_values": torch.zeros(1),
            "attention_mask": torch.zeros(self.max_length, dtype=torch.long),
        }

def load_datasets(
    train_path: str or Path,
    val_path: str or Path,
    processor: AutoProcessor,
    max_length: int = 512,
    image_folder: Optional[str] = None
) -> tuple[QwenVLFactCheckDataset, Optional[QwenVLFactCheckDataset]]:
    """加载训练和验证数据集"""
    train_dataset = QwenVLFactCheckDataset(
        data_path=train_path,
        processor=processor,
        max_length=max_length,
        image_folder=image_folder
    )

    val_dataset = None
    if val_path and Path(val_path).exists():
        val_dataset = QwenVLFactCheckDataset(
            data_path=val_path,
            processor=processor,
            max_length=max_length,
            image_folder=image_folder
        )

    return train_dataset, val_dataset

def create_small_test_dataset(
    data_path: str or Path,
    processor: AutoProcessor,
    num_samples: int = 10,
    max_length: int = 512
) -> QwenVLFactCheckDataset:
    """创建小规模测试数据集"""
    data_path = Path(data_path)

    with open(data_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    small_data = all_data[:num_samples]

    temp_path = data_path.parent / f"temp_small_{data_path.name}"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(small_data, f, ensure_ascii=False, indent=2)

    dataset = QwenVLFactCheckDataset(
        data_path=temp_path,
        processor=processor,
        max_length=max_length
    )

    return dataset

class DataCollatorForVisionLanguageModeling:
    """视觉语言建模数据整理器"""

    def __init__(self, processor: AutoProcessor, max_length: int = 512):
        self.processor = processor
        self.max_length = max_length

    def __call__(self, features: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        batch = {
            "input_ids": torch.stack([f["input_ids"] for f in features]),
            "labels": torch.stack([f["labels"] for f in features]),
            "attention_mask": torch.stack([f["attention_mask"] for f in features]),
        }

        if "pixel_values" in features[0]:
            batch["pixel_values"] = torch.stack([f["pixel_values"] for f in features])

        return batch

def prepare_dataset_for_training(
    data_path: str or Path,
    processor: AutoProcessor,
    max_length: int = 512,
    image_folder: Optional[str] = None
) -> QwenVLFactCheckDataset:
    """准备训练数据集"""
    return QwenVLFactCheckDataset(
        data_path=data_path,
        processor=processor,
        max_length=max_length,
        image_folder=image_folder
    )

if __name__ == "__main__":
    print("=" * 60)
    print("数据集处理模块测试")
    print("=" * 60)

    print("\n此模块需要配合AutoProcessor使用")
    print("示例:")
    print("  processor = AutoProcessor.from_pretrained('Qwen/Qwen-VL-Chat')")
    print("  dataset = QwenVLFactCheckDataset('data.json', processor)")
