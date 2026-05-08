"""
数据格式转换模块
将JSONL标注数据转换为Qwen-VL-Chat训练格式
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent.parent
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"
CONVERTED_DIR = PROJECT_ROOT / "data" / "converted"

CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = "你是一个视觉事实核查助手。你的任务是根据图片内容判断用户陈述是否正确。"

def load_annotations(file_path: Path) -> List[Dict]:
    """加载标注数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('\\n', '\n').replace('\\r\\n', '\n')
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    
    return data

def convert_to_qwen_format(annotation: Dict, image_base_path: Optional[str] = None) -> Dict:
    """将单个标注转换为Qwen-VL格式"""
    chart_id = annotation.get("chart_id", "")
    image_path = annotation.get("image_path", "")
    atomic_fact = annotation.get("atomic_fact", "")
    label = annotation.get("label", False)

    if image_base_path:
        image_path = str(Path(image_base_path) / Path(image_path).name)

    answer = "是" if label else "否"

    conversation = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": str(image_path)
                },
                {
                    "type": "text",
                    "text": f"判断以下陈述是否与图片内容完全一致，仅回答'是'或'否'。\n陈述：{atomic_fact}"
                }
            ]
        },
        {
            "role": "assistant",
            "content": answer
        }
    ]

    return {
        "id": f"{chart_id}_{hash(atomic_fact) % 100000}",
        "conversations": conversation
    }

def convert_dataset(split: str, image_base_path: Optional[str] = None) -> List[Dict]:
    """转换整个数据集"""
    input_path = ANNOTATIONS_DIR / f"{split}.jsonl"

    if not input_path.exists():
        print(f"警告: 文件不存在 {input_path}")
        return []

    annotations = load_annotations(input_path)
    print(f"加载了 {len(annotations)} 条 {split} 标注数据")

    converted = []
    for ann in tqdm(annotations, desc=f"转换 {split}"):
        try:
            item = convert_to_qwen_format(ann, image_base_path)
            converted.append(item)
        except Exception as e:
            print(f"转换错误: {e}")
            continue

    output_path = CONVERTED_DIR / f"{split}_qwen_format.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"保存 {len(converted)} 条转换数据到 {output_path}")
    return converted

def convert_all_datasets(image_base_path: Optional[str] = None) -> Dict[str, List[Dict]]:
    """转换所有数据集"""
    results = {}

    for split in ["train", "val", "test"]:
        results[split] = convert_dataset(split, image_base_path)

    summary = {
        "train": len(results["train"]),
        "val": len(results["val"]),
        "test": len(results["test"])
    }

    summary_path = CONVERTED_DIR / "dataset_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n转换完成！总计: {sum(summary.values())} 条")
    print(f"  - 训练集: {summary['train']} 条")
    print(f"  - 验证集: {summary['val']} 条")
    print(f"  - 测试集: {summary['test']} 条")

    return results

def create_mini_dataset(num_samples: int = 100, output_path: Path = None) -> List[Dict]:
    """创建小规模测试数据集"""
    if output_path is None:
        output_path = CONVERTED_DIR / "mini_dataset.json"

    all_annotations = []

    for split in ["train", "val", "test"]:
        input_path = ANNOTATIONS_DIR / f"{split}.jsonl"
        if input_path.exists():
            all_annotations.extend(load_annotations(input_path))

    random.seed(42)
    sampled = random.sample(all_annotations, min(num_samples, len(all_annotations)))

    converted = []
    for ann in sampled:
        try:
            item = convert_to_qwen_format(ann)
            converted.append(item)
        except Exception:
            continue

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"创建小数据集: {len(converted)} 条 -> {output_path}")
    return converted

if __name__ == "__main__":
    print("=" * 60)
    print("数据格式转换")
    print("=" * 60)

    print("\n1. 转换全部数据集...")
    convert_all_datasets()

    print("\n2. 创建小测试数据集...")
    create_mini_dataset(num_samples=50)

    print("\n✅ 转换完成！")
