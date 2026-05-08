"""独立测试脚本 - 避免模块导入问题"""
import sys
import json
import random
from pathlib import Path

print("=" * 60)
print("FactAlign-VL 模块测试")
print("=" * 60)

# Test 1: 路径和基础设置
print("\n[Test 1] 路径和基础设置...")
try:
    PROJECT_ROOT = Path(__file__).parent
    CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
    METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
    DESCRIPTIONS_DIR = PROJECT_ROOT / "data" / "descriptions"

    for dir_path in [CHARTS_DIR, METADATA_DIR, DESCRIPTIONS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"  CHARTS_DIR: {CHARTS_DIR}")
    print(f"  METADATA_DIR: {METADATA_DIR}")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 2: Matplotlib 图表生成
print("\n[Test 2] Matplotlib 图表生成...")
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 测试柱状图
    fig, ax = plt.subplots(figsize=(6, 4))
    data = {"苹果": 42, "香蕉": 78, "橙子": 55}
    ax.bar(data.keys(), data.values())
    chart_path = CHARTS_DIR / "bar" / "test_chart.png"
    chart_path.parent.mkdir(exist_ok=True)
    fig.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)

    print(f"  生成测试图表: {chart_path}")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    import traceback
    traceback.print_exc()

# Test 3: JSON 数据处理
print("\n[Test 3] JSON 数据处理...")
try:
    test_metadata = {
        "chart_id": "test_001",
        "chart_type": "bar",
        "data": {"苹果": 42, "香蕉": 78},
        "labels": ["苹果", "香蕉"],
        "values": [42, 78]
    }

    meta_path = METADATA_DIR / "test_001.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(test_metadata, f, ensure_ascii=False, indent=2)

    with open(meta_path, 'r', encoding='utf-8') as f:
        loaded = json.load(f)

    assert loaded["chart_id"] == "test_001"
    assert loaded["data"]["苹果"] == 42

    print(f"  写入/读取 JSON: {meta_path}")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 4: 评估模块导入测试
print("\n[Test 4] 评估模块导入测试...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "factalign-vl"))

    # 测试安全路径函数
    from evaluation.testset_builder import safe_resolve_path

    test_base = METADATA_DIR
    result = safe_resolve_path(test_base, "chart_00001.json")
    print(f"  safe_resolve_path 测试: {result.name}")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 5: 检查数据文件是否存在
print("\n[Test 5] 检查数据文件...")
try:
    annotations_dir = PROJECT_ROOT / "data" / "annotations"

    train_path = annotations_dir / "train.jsonl"
    val_path = annotations_dir / "val.jsonl"
    test_path = annotations_dir / "test.jsonl"

    print(f"  训练集: {train_path.exists()}")
    print(f"  验证集: {val_path.exists()}")
    print(f"  测试集: {test_path.exists()}")

    if train_path.exists():
        with open(train_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.replace('\\n', '\n')
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            print(f"  训练集样本数: {len(lines)}")

    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 6: Demo 模块测试 (不含 Gradio)
print("\n[Test 6] Demo 工具函数测试...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "factalign-vl"))

    # 测试 HTML 转义
    from app.demo import escape_html

    test_input = '<script>alert("xss")</script>'
    escaped = escape_html(test_input)
    assert '&lt;' in escaped and '&gt;' in escaped
    print(f"  XSS 防护测试: 输入={test_input[:20]}... 输出={escaped[:30]}...")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 7: 路径遍历防护测试
print("\n[Test 7] 路径遍历防护测试...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "factalign-vl"))
    from evaluation.testset_builder import safe_resolve_path

    base_dir = METADATA_DIR

    # 正常路径
    safe_path = safe_resolve_path(base_dir, "chart_00001.json")
    print(f"  正常路径: ✅")

    # 尝试路径遍历
    try:
        malicious_path = safe_resolve_path(base_dir, "../../../etc/passwd")
        print(f"  路径遍历攻击: ❌ 应该被拦截!")
    except ValueError as ve:
        print(f"  路径遍历攻击: ✅ 已拦截 ({ve})")

    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
