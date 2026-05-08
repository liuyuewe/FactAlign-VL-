"""
标注器模块
将描述拆分为原子陈述并与真值对比打标签
"""

import json
import re
import spacy
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DESCRIPTIONS_DIR = PROJECT_ROOT / "data" / "descriptions"
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"

ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

class AtomicFactExtractor:
    """原子事实提取器"""

    def __init__(self, model_name: str = "zh_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"警告: 无法加载 {model_name} 模型，使用空白模型")
            self.nlp = spacy.blank("zh")

    def extract_atomic_facts(self, text: str) -> List[str]:
        """将文本拆分为原子陈述"""
        doc = self.nlp(text)

        sentences = []
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if sent_text and len(sent_text) > 5:
                sentences.append(sent_text)

        if not sentences:
            sentences = [text.strip()]

        atomic_facts = []
        for sent in sentences:
            facts = self._split_compound_fact(sent)
            atomic_facts.extend(facts)

        return atomic_facts

    def _split_compound_fact(self, text: str) -> List[str]:
        """将复合陈述拆分为原子陈述"""
        conjunctions = ['并且', '而且', '同时', '此外', '另外', '还有', '并且', '且', '和', '与']
        comparison_words = ['高于', '低于', '大于', '小于', '等于', '高于', '低于']

        for conj in conjunctions:
            if conj in text and any(comp in text for comp in comparison_words):
                parts = text.split(conj)
                facts = []
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 5:
                        facts.append(part)
                if len(facts) > 1:
                    return facts

        if re.search(r'[。；！]', text):
            sentences = re.split(r'[。；！]', text)
            facts = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
            if facts:
                return facts

        return [text]

class FactLabeler:
    """事实标签器"""

    def __init__(self):
        self.number_pattern = re.compile(r'\d+\.?\d*')

    def extract_numbers_from_text(self, text: str) -> List[Tuple[str, int]]:
        """从文本中提取数字及其上下文"""
        matches = []
        for match in self.number_pattern.finditer(text):
            num_str = match.group()
            num = int(float(num_str))
            start = match.start()
            end = match.end()
            context_before = text[max(0, start-5):start]
            context_after = text[end:min(len(text), end+5)]
            matches.append((num_str, num, context_before, context_after))
        return matches

    def extract_numbers_from_metadata(self, metadata: Dict) -> Dict[int, Any]:
        """从元数据中提取所有数字"""
        numbers = {}

        if metadata.get("chart_type") == "bar":
            data = metadata.get("data", {})
            for label, value in data.items():
                numbers[int(value)] = {"type": "bar_value", "label": label, "value": value}

            for label in data.keys():
                for num in self.number_pattern.findall(label):
                    numbers[int(float(num))] = {"type": "label_number", "label": label}

        elif metadata.get("chart_type") == "line":
            values = metadata.get("values", [])
            for i, val in enumerate(values):
                numbers[int(val)] = {"type": "line_value", "index": i}

            labels = metadata.get("labels", [])
            for label in labels:
                for num in self.number_pattern.findall(label):
                    numbers[int(float(num))] = {"type": "label_number", "label": label}

            numbers[int(metadata.get("min_value", 0))] = {"type": "min_value"}
            numbers[int(metadata.get("max_value", 0))] = {"type": "max_value"}

        elif metadata.get("chart_type") == "table":
            rows = metadata.get("rows", [])
            for row in rows:
                for i, cell in enumerate(row):
                    if isinstance(cell, (int, float)):
                        numbers[int(cell)] = {"type": "table_value", "row": row[0], "col": i}
                    elif isinstance(cell, str):
                        for num in self.number_pattern.findall(cell):
                            numbers[int(float(num))] = {"type": "cell_number", "cell": cell}

        return numbers

    def label_fact(self, fact: str, metadata: Dict) -> Tuple[bool, Dict]:
        """为单个原子陈述打标签"""
        text_numbers = self.extract_numbers_from_text(fact)
        metadata_numbers = self.extract_numbers_from_metadata(metadata)

        if not text_numbers:
            return True, {"reason": "no_numbers", "extracted_numbers": [], "verified": []}

        extracted = []
        verified = []
        unverified = []

        for num_str, num, ctx_before, ctx_after in text_numbers:
            extracted.append(num)

            if num in metadata_numbers:
                verified.append(num)
            elif self._find_similar_number(num, metadata_numbers):
                verified.append(num)
            else:
                unverified.append(num)

        is_correct = len(unverified) == 0

        details = {
            "extracted_numbers": extracted,
            "verified_numbers": verified,
            "unverified_numbers": unverified,
            "total_numbers": len(extracted),
            "verified_count": len(verified),
            "unverified_count": len(unverified)
        }

        return is_correct, details

    def _find_similar_number(self, num: int, metadata_numbers: Dict, threshold: int = 3) -> bool:
        """查找相似数字（允许±threshold的误差）"""
        for metadata_num in metadata_numbers.keys():
            if abs(num - metadata_num) <= threshold:
                return True
        return False

class DatasetAnnotator:
    """数据集标注器"""

    def __init__(self):
        self.extractor = AtomicFactExtractor()
        self.labeler = FactLabeler()

    def annotate_dataset(self, descriptions: List[Dict],
                        output_path: Path = None,
                        use_tqdm: bool = True) -> List[Dict]:
        """标注整个数据集"""
        if output_path is None:
            output_path = ANNOTATIONS_DIR / "annotated_dataset.jsonl"

        annotated_data = []

        iterator = tqdm(descriptions, desc="标注数据") if use_tqdm else descriptions

        for item in iterator:
            chart_id = item["chart_id"]
            description = item["description"]
            metadata = item["metadata"]

            atomic_facts = self.extractor.extract_atomic_facts(description)

            for fact in atomic_facts:
                is_correct, details = self.labeler.label_fact(fact, metadata)

                annotated_item = {
                    "chart_id": chart_id,
                    "image_path": item["image_path"],
                    "description": description,
                    "atomic_fact": fact,
                    "label": is_correct,
                    "details": details,
                    "metadata": metadata
                }

                annotated_data.append(annotated_item)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in annotated_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        return annotated_data

    def annotate_split_datasets(self, descriptions_by_split: Dict[str, List[Dict]],
                               output_dir: Path = None) -> Dict[str, List[Dict]]:
        """为划分后的数据集分别标注"""
        if output_dir is None:
            output_dir = ANNOTATIONS_DIR

        results = {}

        for split_name, descriptions in descriptions_by_split.items():
            print(f"标注 {split_name} 集 ({len(descriptions)} 条)...")

            output_path = output_dir / f"{split_name}.jsonl"
            annotated = self.annotate_dataset(descriptions, output_path, use_tqdm=True)

            true_count = sum(1 for item in annotated if item["label"])
            false_count = len(annotated) - true_count

            print(f"  {split_name} 集: {len(annotated)} 条原子事实")
            print(f"    - 正确: {true_count} ({true_count/len(annotated)*100:.1f}%)")
            print(f"    - 错误: {false_count} ({false_count/len(annotated)*100:.1f}%)")

            results[split_name] = annotated

        return results

def load_descriptions() -> List[Dict]:
    """加载所有描述"""
    descriptions = []

    index_path = DESCRIPTIONS_DIR / "descriptions_index.jsonl"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            for line in f:
                descriptions.append(json.loads(line.strip()))

    return descriptions

def split_descriptions(descriptions: List[Dict],
                      train_ratio: float = 0.8,
                      val_ratio: float = 0.1,
                      test_ratio: float = 0.1) -> Dict[str, List[Dict]]:
    """划分描述数据集"""
    import random
    random.seed(42)
    random.shuffle(descriptions)

    total = len(descriptions)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)

    return {
        "train": descriptions[:train_size],
        "val": descriptions[train_size:train_size + val_size],
        "test": descriptions[train_size + val_size:]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("开始标注数据集")
    print("=" * 60)

    descriptions = load_descriptions()
    print(f"加载了 {len(descriptions)} 条描述")

    if len(descriptions) == 0:
        print("没有找到描述数据，请先运行 description_generator.py 生成描述")
    else:
        splits = split_descriptions(descriptions)

        annotator = DatasetAnnotator()
        results = annotator.annotate_split_datasets(splits)

        print("\n" + "=" * 60)
        print("标注完成！")
        print("=" * 60)
        print(f"数据集保存在: {ANNOTATIONS_DIR}")
