"""
数据生成主脚本
执行完整的合成数据生成流程
"""

import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "factalign-vl"))

from synthesizer import (
    ChartGenerator,
    DescriptionGenerator,
    DatasetAnnotator,
    load_all_metadata,
    load_descriptions,
    split_dataset
)

from synthesizer.annotator import ANNOTATIONS_DIR

def main():
    print("=" * 70)
    print("🎯 FactAlign-VL 合成数据工厂")
    print("=" * 70)

    NUM_BAR = 500
    NUM_LINE = 500
    NUM_TABLE = 500

    print(f"\n📊 目标数据量:")
    print(f"   - 柱状图: {NUM_BAR} 张")
    print(f"   - 折线图: {NUM_LINE} 张")
    print(f"   - 表格图: {NUM_TABLE} 张")
    print(f"   - 总计: {NUM_BAR + NUM_LINE + NUM_TABLE} 张")
    print(f"   - 数据划分: 训练集 80% / 验证集 10% / 测试集 10%")

    print("\n" + "=" * 70)
    print("📈 阶段 1: 生成图表和元数据")
    print("=" * 70)

    generator = ChartGenerator(seed=42)

    print(f"\n开始生成图表...")
    results = generator.generate_all(
        num_bar=NUM_BAR,
        num_line=NUM_LINE,
        num_table=NUM_TABLE
    )

    bar_count = len(results["bar"])
    line_count = len(results["line"])
    table_count = len(results["table"])

    print(f"\n✅ 图表生成完成:")
    print(f"   - 柱状图: {bar_count} 张")
    print(f"   - 折线图: {line_count} 张")
    print(f"   - 表格图: {table_count} 张")
    print(f"   - 总计: {bar_count + line_count + table_count} 张")

    all_charts = results["bar"] + results["line"] + results["table"]

    print("\n" + "=" * 70)
    print("📝 阶段 2: 生成图表描述")
    print("=" * 70)

    print(f"\n开始生成描述 (使用模拟描述器)...")
    desc_generator = DescriptionGenerator()
    descriptions = desc_generator.generate_all_descriptions(all_charts)

    print(f"\n✅ 描述生成完成:")
    print(f"   - 生成 {len(descriptions)} 条描述")
    print(f"   - 描述文件保存在: data/descriptions/")

    print("\n" + "=" * 70)
    print("🏷️  阶段 3: 拆分原子事实并自动打标签")
    print("=" * 70)

    print(f"\n开始标注数据...")

    import random
    random.seed(42)
    random.shuffle(descriptions)

    train_size = int(len(descriptions) * 0.8)
    val_size = int(len(descriptions) * 0.1)

    splits = {
        "train": descriptions[:train_size],
        "val": descriptions[train_size:train_size + val_size],
        "test": descriptions[train_size + val_size:]
    }

    annotator = DatasetAnnotator()
    all_annotated = []

    for split_name, split_data in splits.items():
        print(f"\n处理 {split_name} 集 ({len(split_data)} 条)...")

        from factalign_vl.synthesizer.annotator import ANNOTATIONS_DIR

        split_annotated = []
        for item in split_data:
            chart_id = item["chart_id"]
            description = item["description"]
            metadata = item["metadata"]

            atomic_facts = annotator.extractor.extract_atomic_facts(description)

            for fact in atomic_facts:
                is_correct, details = annotator.labeler.label_fact(fact, metadata)

                annotated_item = {
                    "chart_id": chart_id,
                    "image_path": item["image_path"],
                    "description": description,
                    "atomic_fact": fact,
                    "label": is_correct,
                    "details": details,
                    "metadata": metadata
                }

                split_annotated.append(annotated_item)

        output_path = ANNOTATIONS_DIR / f"{split_name}.jsonl"
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in split_annotated:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        true_count = sum(1 for item in split_annotated if item["label"])
        false_count = len(split_annotated) - true_count

        print(f"   {split_name} 集: {len(split_annotated)} 条原子事实")
        print(f"     - 正确 (True): {true_count} ({true_count/len(split_annotated)*100:.1f}%)")
        print(f"     - 错误 (False): {false_count} ({false_count/len(split_annotated)*100:.1f}%)")

        all_annotated.extend(split_annotated)

    print("\n" + "=" * 70)
    print("✅ 数据生成完成！")
    print("=" * 70)

    print(f"\n📁 生成的文件:")
    print(f"   - 图表: data/charts/")
    print(f"   - 元数据: data/metadata/")
    print(f"   - 描述: data/descriptions/")
    print(f"   - 标注: data/annotations/")

    print(f"\n📊 数据统计:")
    total_true = sum(1 for item in all_annotated if item["label"])
    total_false = len(all_annotated) - total_true

    print(f"   - 总原子事实: {len(all_annotated)}")
    print(f"   - 正确: {total_true} ({total_true/len(all_annotated)*100:.1f}%)")
    print(f"   - 错误: {total_false} ({total_false/len(all_annotated)*100:.1f}%)")

    print(f"\n🎯 下一步:")
    print(f"   1. 检查生成的数据质量")
    print(f"   2. 运行第三步: 训练视觉事实核查模型")
    print(f"   3. 运行应用: python run.py")

    return all_annotated

if __name__ == "__main__":
    main()
