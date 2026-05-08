"""
描述生成器模块
使用视觉语言模型为图表生成自然语言描述
"""

import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import torch
try:
    from transformers import AutoProcessor, AutoModelForVision2Seq
except ImportError:
    AutoModelForVision2Seq = None
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DESCRIPTIONS_DIR = PROJECT_ROOT / "data" / "descriptions"

for dir_path in [CHARTS_DIR, METADATA_DIR, DESCRIPTIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

DESCRIPTION_PROMPT = """请详细描述这张图表中的所有信息，包括：
1. 图表类型和标题
2. 所有类别的名称和对应数值
3. 颜色信息（如果有）
4. 最大值、最小值等关键数据
5. 任何其他可见的信息

请尽可能详细地描述每一个数据点，不要遗漏任何数字。"""

DESCRIPTION_PROMPT_SIMPLE = """描述这张图片的内容，包括所有可见的文字和数字。"""

class DescriptionGenerator:
    """描述生成器"""

    def __init__(self, model_name: str = "Qwen/Qwen-VL-Chat", device: str = "auto"):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self.processor = None
        self.use_mock = True

    def _get_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def load_model(self):
        """加载视觉语言模型"""
        if AutoModelForVision2Seq is None:
            print("AutoModelForVision2Seq 不可用，使用模拟描述生成器")
            self.use_mock = True
            return
            
        try:
            print(f"正在加载模型: {self.model_name}")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_name,
                device_map=self.device,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True
            )
            self.use_mock = False
            print(f"模型加载成功，使用设备: {self.device}")
        except Exception as e:
            print(f"无法加载模型 {self.model_name}: {e}")
            print("将使用模拟描述生成器")
            self.use_mock = True

    def generate_description(self, image_path: Path, metadata: Dict) -> str:
        """为单个图表生成描述"""
        if self.use_mock:
            return self._generate_mock_description(metadata)

        try:
            image = Image.open(image_path).convert('RGB')

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": DESCRIPTION_PROMPT}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            inputs = self.processor(
                text=[text],
                images=[image],
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False
                )

            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs['input_ids'], generated_ids)
            ]

            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]

            return output_text.strip()

        except Exception as e:
            print(f"生成描述时出错: {e}")
            return self._generate_mock_description(metadata)

    def _generate_mock_description(self, metadata: Dict) -> str:
        """生成模拟描述（包含数字错误）"""
        chart_type = metadata.get("chart_type", "unknown")
        chart_id = metadata.get("chart_id", "unknown")

        if chart_type == "bar":
            data = metadata.get("data", {})
            labels = list(data.keys())
            values = list(data.values())

            if len(labels) == 0:
                return f"这是一个柱状图，显示了某些数据的变化。"

            descriptions = []
            descriptions.append(f"这是一个柱状图{chart_id}。")

            for i, (label, value) in enumerate(data.items()):
                if random.random() < 0.15:
                    value = value + random.randint(-10, 10)
                    value = max(1, value)
                descriptions.append(f"{label}的数值是{value}。")

            max_label = max(data, key=data.get)
            min_label = min(data, key=data.get)
            descriptions.append(f"其中{max_label}的数值最高，{min_label}的数值最低。")

            if random.random() < 0.1:
                wrong_label = random.choice(labels)
                if wrong_label != max_label:
                    descriptions.append(f"看起来{min_label}的值略高于{wrong_label}。")

            return " ".join(descriptions)

        elif chart_type == "line":
            labels = metadata.get("labels", [])
            values = metadata.get("values", [])

            if len(labels) == 0 or len(values) == 0:
                return f"这是一个折线图，显示了数据随时间变化的趋势。"

            descriptions = []
            descriptions.append(f"这是一个折线图{chart_id}。")

            for i, (label, value) in enumerate(zip(labels, values)):
                if random.random() < 0.15:
                    value = value + random.randint(-8, 8)
                    value = max(1, value)
                descriptions.append(f"{label}的数值是{value}。")

            if len(values) >= 2:
                if values[-1] > values[0]:
                    descriptions.append(f"整体呈上升趋势。")
                else:
                    descriptions.append(f"整体呈下降趋势。")

            max_val = max(values)
            min_val = min(values)
            max_idx = values.index(max_val)
            min_idx = values.index(min_val)
            descriptions.append(f"最高点在{labels[max_idx]}，数值为{max_val}。")
            descriptions.append(f"最低点在{labels[min_idx]}，数值为{min_val}。")

            return " ".join(descriptions)

        elif chart_type == "table":
            headers = metadata.get("headers", [])
            rows = metadata.get("rows", [])

            if len(headers) == 0 or len(rows) == 0:
                return f"这是一个表格，展示了相关数据。"

            descriptions = []
            descriptions.append(f"这是一个表格数据{chart_id}。")

            descriptions.append(f"表格包含以下列：{', '.join(headers)}。")

            for row in rows[:3]:
                if len(row) >= 2:
                    item = row[0]
                    if random.random() < 0.2:
                        desc_value = row[1] + random.randint(-5, 5) if len(row) > 1 else 50
                        desc_value = max(1, desc_value)
                    else:
                        desc_value = row[1] if len(row) > 1 else "未知"
                    descriptions.append(f"{item}的相关数据是{desc_value}。")

            if len(rows) > 3:
                descriptions.append(f"共有{len(rows)}行数据。")

            return " ".join(descriptions)

        return f"这是一个{chart_type}类型的图表{chart_id}。"

    def generate_all_descriptions(self, chart_metadata_list: List[Dict],
                                 output_dir: Path = None,
                                 use_tqdm: bool = True) -> List[Dict]:
        """为所有图表生成描述"""
        if output_dir is None:
            output_dir = DESCRIPTIONS_DIR

        results = []

        iterator = tqdm(chart_metadata_list, desc="生成描述") if use_tqdm else chart_metadata_list

        for item in iterator:
            image_path = Path(item["image"])
            metadata = item["metadata"]

            description = self.generate_description(image_path, metadata)

            desc_path = output_dir / f"{metadata['chart_id']}.txt"
            with open(desc_path, 'w', encoding='utf-8') as f:
                f.write(description)

            results.append({
                "chart_id": metadata["chart_id"],
                "image_path": str(image_path),
                "description_path": str(desc_path),
                "description": description,
                "metadata": metadata
            })

        return results

def load_all_metadata() -> List[Dict]:
    """加载所有图表元数据"""
    all_charts = []

    for chart_type in ["bar", "line", "table"]:
        type_dir = CHARTS_DIR / chart_type
        if not type_dir.exists():
            continue

        for img_path in type_dir.glob("*.png"):
            chart_id = img_path.stem
            meta_path = METADATA_DIR / f"{chart_id}.json"

            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                all_charts.append({
                    "image": str(img_path),
                    "metadata": metadata
                })

    return all_charts

def save_descriptions_index(descriptions: List[Dict], output_path: Path):
    """保存描述索引"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in descriptions:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    import random
    random.seed(42)

    print("=" * 60)
    print("开始生成图表描述")
    print("=" * 60)

    all_charts = load_all_metadata()
    print(f"找到 {len(all_charts)} 张图表")

    if len(all_charts) == 0:
        print("没有找到图表数据，请先运行 chart_generator.py 生成图表")
    else:
        generator = DescriptionGenerator()
        descriptions = generator.generate_all_descriptions(all_charts[:10])

        index_path = DESCRIPTIONS_DIR / "descriptions_index.jsonl"
        save_descriptions_index(descriptions, index_path)

        print(f"\n生成完成，共生成 {len(descriptions)} 条描述")
        print(f"描述文件保存在: {DESCRIPTIONS_DIR}")
