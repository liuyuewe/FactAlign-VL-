"""
专用测试集构建器
为评估构建包含VLM描述的测试集
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent.parent
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
DESCRIPTIONS_DIR = PROJECT_ROOT / "data" / "descriptions"
EVAL_DIR = PROJECT_ROOT / "data" / "evaluation"

EVAL_DIR.mkdir(parents=True, exist_ok=True)


def safe_resolve_path(base_dir: Path, filename: str) -> Path:
    """安全路径解析，防止路径遍历攻击"""
    base_dir = base_dir.resolve()
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
    if not all(c in safe_chars for c in filename):
        raise ValueError(f"文件名包含非法字符: {filename}")
    requested_path = (base_dir / filename).resolve()
    if not requested_path.is_relative_to(base_dir):
        raise ValueError(f"非法路径访问: {filename}")
    return requested_path

@dataclass
class EvaluationSample:
    """评估样本"""
    chart_id: str
    image_path: str
    metadata_path: str
    vlm_description: str
    ground_truth: bool
    atomic_facts: List[Dict[str, Any]]

class TestsetBuilder:
    """测试集构建器"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def load_test_annotations(self) -> List[Dict]:
        """加载测试集标注"""
        test_path = ANNOTATIONS_DIR / "test.jsonl"

        if not test_path.exists():
            print(f"警告: 测试集标注不存在 {test_path}")
            return []

        data = []
        with open(test_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.replace('\\n', '\n')

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return data

    def sample_charts(self, data: List[Dict], num_samples: int = 200) -> List[Dict]:
        """采样图表"""
        unique_charts = {}
        for item in data:
            chart_id = item.get("chart_id")
            if chart_id not in unique_charts:
                unique_charts[chart_id] = item

        chart_ids = list(unique_charts.keys())
        sampled_ids = random.sample(chart_ids, min(num_samples, len(chart_ids)))

        sampled = [unique_charts[cid] for cid in sampled_ids]
        return sampled

    def build_evaluation_samples(self, sampled_data: List[Dict]) -> List[EvaluationSample]:
        """构建评估样本"""
        samples = []

        for item in tqdm(sampled_data, desc="构建评估样本"):
            chart_id = item.get("chart_id", "")
            image_path = item.get("image_path", "")
            atomic_fact = item.get("atomic_fact", "")
            ground_truth = item.get("label", False)

            try:
                metadata_path = safe_resolve_path(METADATA_DIR, f"{chart_id}.json")
            except ValueError:
                metadata_path = METADATA_DIR / f"{chart_id}.json"

            vlm_description = ""
            try:
                desc_path = safe_resolve_path(DESCRIPTIONS_DIR, f"{chart_id}.txt")
                if desc_path.exists():
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        vlm_description = f.read()
            except ValueError:
                pass

            sample = EvaluationSample(
                chart_id=chart_id,
                image_path=image_path,
                metadata_path=str(metadata_path),
                vlm_description=vlm_description,
                ground_truth=ground_truth,
                atomic_facts=[{
                    "fact": atomic_fact,
                    "ground_truth": ground_truth,
                    "details": item.get("details", {})
                }]
            )

            samples.append(sample)

        return samples

    def save_testset(self, samples: List[EvaluationSample], output_path: Path):
        """保存测试集"""
        data = []
        for sample in samples:
            data.append({
                "chart_id": sample.chart_id,
                "image_path": sample.image_path,
                "metadata_path": sample.metadata_path,
                "vlm_description": sample.vlm_description,
                "ground_truth": sample.ground_truth,
                "atomic_facts": sample.atomic_facts,
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"测试集已保存: {output_path}")
        print(f"  样本数量: {len(samples)}")

    def load_testset(self, input_path: Path) -> List[EvaluationSample]:
        """加载测试集"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        samples = []
        for item in data:
            sample = EvaluationSample(
                chart_id=item["chart_id"],
                image_path=item["image_path"],
                metadata_path=item["metadata_path"],
                vlm_description=item["vlm_description"],
                ground_truth=item["ground_truth"],
                atomic_facts=item["atomic_facts"],
            )
            samples.append(sample)

        return samples


def build_evaluation_testset(
    num_samples: int = 200,
    output_path: Path = None,
    seed: int = 42
) -> List[EvaluationSample]:
    """构建评估测试集"""
    if output_path is None:
        output_path = EVAL_DIR / "evaluation_testset.json"

    print("=" * 60)
    print("构建专用评估测试集")
    print("=" * 60)
    print(f"目标样本数: {num_samples}")

    builder = TestsetBuilder(seed=seed)

    print("\n加载测试集标注...")
    test_data = builder.load_test_annotations()
    print(f"  加载了 {len(test_data)} 条标注")

    print("\n采样图表...")
    sampled_data = builder.sample_charts(test_data, num_samples)
    print(f"  采样了 {len(sampled_data)} 张图表")

    print("\n构建评估样本...")
    samples = builder.build_evaluation_samples(sampled_data)

    print("\n保存测试集...")
    builder.save_testset(samples, output_path)

    return samples


def create_dedicated_testset(
    source: str = "test",
    num_samples: int = 200,
    output_path: Path = None
) -> Tuple[List[Dict], Dict[str, Any]]:
    """创建专用测试集"""
    if output_path is None:
        output_path = EVAL_DIR / f"{source}_dedicated_testset.json"

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    builder = TestsetBuilder()

    source_path = ANNOTATIONS_DIR / f"{source}.jsonl"

    if not source_path.exists():
        print(f"错误: 源文件不存在 {source_path}")
        return [], {}

    print(f"从 {source_path} 加载数据...")
    data = builder.load_test_annotations()

    unique_charts = {}
    for item in data:
        chart_id = item.get("chart_id")
        if chart_id not in unique_charts:
            unique_charts[chart_id] = item

    chart_ids = list(unique_charts.keys())
    sampled_ids = random.sample(chart_ids, min(num_samples, len(chart_ids)))

    dedicated_data = []
    for chart_id in sampled_ids:
        chart_items = [item for item in data if item.get("chart_id") == chart_id]

        vlm_desc = ""
        try:
            desc_path = safe_resolve_path(DESCRIPTIONS_DIR, f"{chart_id}.txt")
            if desc_path.exists():
                with open(desc_path, 'r', encoding='utf-8') as f:
                    vlm_desc = f.read()
        except ValueError:
            pass

        metadata = {}
        try:
            metadata_path = safe_resolve_path(METADATA_DIR, f"{chart_id}.json")
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
        except (ValueError, json.JSONDecodeError):
            pass

        chart_data = {
            "chart_id": chart_id,
            "image_path": unique_charts[chart_id].get("image_path"),
            "metadata": metadata,
            "vlm_description": vlm_desc,
            "atomic_facts": chart_items,
        }

        dedicated_data.append(chart_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dedicated_data, f, ensure_ascii=False, indent=2)

    stats = {
        "total_charts": len(dedicated_data),
        "source": source,
        "output_path": str(output_path),
    }

    return dedicated_data, stats


if __name__ == "__main__":
    print("=" * 60)
    print("构建专用评估测试集")
    print("=" * 60)

    samples = build_evaluation_testset(num_samples=200)

    print("\n测试集统计:")
    print(f"  总样本数: {len(samples)}")

    if samples:
        sample = samples[0]
        print(f"\n示例样本:")
        print(f"  Chart ID: {sample.chart_id}")
        print(f"  原子事实数: {len(sample.atomic_facts)}")
        print(f"  VLM描述长度: {len(sample.vlm_description)} 字符")
