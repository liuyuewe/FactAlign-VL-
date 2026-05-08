"""完整Bug测试脚本"""
import sys
import json
import random
from pathlib import Path

print("=" * 70)
print("FactAlign-VL 完整Bug测试")
print("=" * 70)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "factalign-vl"))

bugs_found = []
warnings_found = []

# Bug 1: 检查 spaCy 模型是否可用
print("\n[Bug Check 1] SpaCy 模型检查...")
try:
    import spacy
    try:
        nlp = spacy.load("zh_core_web_sm")
        print("  ✅ SpaCy 中文模型已安装")
    except OSError:
        print("  ⚠️ SpaCy 模型未安装，原子事实拆分功能将使用简化版本")
        warnings_found.append("SpaCy 模型未安装")
except ImportError:
    print("  ⚠️ SpaCy 未安装")
    warnings_found.append("SpaCy 未安装")

# Bug 2: 检查 torch 是否安装
print("\n[Bug Check 2] PyTorch 检查...")
try:
    import torch
    print(f"  ✅ PyTorch 版本: {torch.__version__}")
    print(f"  ✅ CUDA 可用: {torch.cuda.is_available()}")
except ImportError:
    print("  ⚠️ PyTorch 未安装，微调功能不可用")
    warnings_found.append("PyTorch 未安装")

# Bug 3: 检查 transformers
print("\n[Bug Check 3] Transformers 检查...")
try:
    import transformers
    print(f"  ✅ Transformers 版本: {transformers.__version__}")
except ImportError:
    print("  ⚠️ Transformers 未安装")
    warnings_found.append("Transformers 未安装")

# Bug 4: 检查 Gradio
print("\n[Bug Check 4] Gradio 检查...")
try:
    import gradio
    print(f"  ✅ Gradio 版本: {gradio.__version__}")
except ImportError:
    print("  ⚠️ Gradio 未安装，Web界面不可用")
    warnings_found.append("Gradio 未安装")

# Bug 5: 检查数据完整性
print("\n[Bug Check 5] 数据完整性检查...")
try:
    annotations_dir = PROJECT_ROOT / "data" / "annotations"

    for split in ["train", "val", "test"]:
        path = annotations_dir / f"{split}.jsonl"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                content = content.replace('\\n', '\n')
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                count = 0
                for line in lines:
                    try:
                        json.loads(line)
                        count += 1
                    except:
                        pass
                print(f"  {split} 集: {count} 条有效数据")
        else:
            print(f"  ⚠️ {split} 集文件不存在")
            bugs_found.append(f"{split} 集文件不存在")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"数据完整性检查失败: {e}")

# Bug 6: 检查 metadata 文件
print("\n[Bug Check 6] Metadata 文件检查...")
try:
    metadata_dir = PROJECT_ROOT / "data" / "metadata"
    if metadata_dir.exists():
        json_files = list(metadata_dir.glob("*.json"))
        print(f"  ✅ 找到 {len(json_files)} 个元数据文件")

        # 抽查前 3 个文件
        sample_files = json_files[:3]
        for f in sample_files:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'chart_id' not in data:
                    bugs_found.append(f"{f.name} 缺少 chart_id 字段")
                    print(f"  ⚠️ {f.name} 缺少 chart_id 字段")
    else:
        print("  ⚠️ 元数据目录不存在")
        warnings_found.append("元数据目录不存在")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"Metadata 检查失败: {e}")

# Bug 7: 测试 safe_resolve_path 函数
print("\n[Bug Check 7] 路径安全函数检查...")
try:
    from evaluation.testset_builder import safe_resolve_path

    base_dir = metadata_dir
    test_cases = [
        ("chart_00001.json", True, "正常文件名"),
        ("../../../etc/passwd", False, "路径遍历攻击"),
        ("chart_<script>.json", False, "特殊字符攻击"),
        ("..%2F..%2Fetc%2Fpasswd", False, "URL编码攻击"),
    ]

    for filename, should_succeed, desc in test_cases:
        try:
            result = safe_resolve_path(base_dir, filename)
            if should_succeed:
                print(f"  ✅ {desc}: 通过")
            else:
                print(f"  ❌ {desc}: 应该失败但成功了")
                bugs_found.append(f"路径安全函数未拦截: {desc}")
        except ValueError:
            if not should_succeed:
                print(f"  ✅ {desc}: 正确拦截")
            else:
                print(f"  ❌ {desc}: 不应该失败")
                bugs_found.append(f"路径安全函数误判: {desc}")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"路径安全测试失败: {e}")

# Bug 8: 测试 HTML 转义
print("\n[Bug Check 8] HTML 转义检查...")
try:
    from app.demo import escape_html

    xss_attempts = [
        '<script>alert(1)</script>',
        '"><img src=x onerror=alert(1)>',
        "javascript:alert('xss')",
        '<svg onload=alert(1)>',
    ]

    all_protected = True
    for attempt in xss_attempts:
        escaped = escape_html(attempt)
        if '<' in escaped or '>' in escaped:
            all_protected = False
            print(f"  ❌ XSS 测试失败: {attempt[:30]} 未转义")
            bugs_found.append(f"HTML 转义失败: {attempt[:20]}")
        else:
            print(f"  ✅ XSS 防护: {attempt[:20]}... 已转义")

    if all_protected:
        print("  ✅ 所有 XSS 攻击已被转义")

except ImportError as e:
    print(f"  ⚠️ 跳过 (依赖未安装): {e}")
    warnings_found.append(f"HTML 转义依赖未安装")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"HTML 转义测试失败: {e}")

# Bug 9: 测试评估模块
print("\n[Bug Check 9] 评估模块检查...")
try:
    from evaluation.evaluator import FactCheckEvaluator, MetricsCalculator

    evaluator = FactCheckEvaluator(use_mock_model=True)
    calculator = MetricsCalculator()

    # 测试指标计算
    predictions = [True, False, True, True, False]
    labels = [True, False, False, True, False]

    metrics = calculator.compute_all_metrics(predictions, labels)

    print(f"  ✅ 准确率: {metrics['accuracy']:.2f}")
    print(f"  ✅ 精确率: {metrics['precision']:.2f}")
    print(f"  ✅ 召回率: {metrics['recall']:.2f}")

    # 验证计算是否正确
    # predictions = [True, False, True, True, False]
    # labels = [True, False, False, True, False]
    # TP=2, FP=1, TN=2, FN=0
    # Accuracy = (2+2)/5 = 0.8
    expected_accuracy = 0.8
    expected_precision = 2/3  # TP/(TP+FP) = 2/3

    if abs(metrics['accuracy'] - expected_accuracy) > 0.01:
        bugs_found.append(f"指标计算错误: 期望 {expected_accuracy}, 得到 {metrics['accuracy']}")
        print(f"  ❌ 准确率计算错误")
    else:
        print(f"  ✅ 准确率计算正确: {metrics['accuracy']}")

    if abs(metrics['precision'] - expected_precision) > 0.01:
        bugs_found.append(f"精确率计算错误: 期望 {expected_precision:.2f}, 得到 {metrics['precision']:.2f}")
        print(f"  ❌ 精确率计算错误")
    else:
        print(f"  ✅ 精确率计算正确: {metrics['precision']:.2f}")

except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"评估模块测试失败: {e}")

# Bug 10: 检查配置文件
print("\n[Bug Check 10] 配置文件检查...")
try:
    from configs.config import MODEL_CONFIG, SPACY_MODEL, GRADIO_CONFIG

    print(f"  ✅ 模型名称: {MODEL_CONFIG.get('vl_model', 'N/A')}")
    print(f"  ✅ SpaCy 模型: {SPACY_MODEL}")
    print(f"  ✅ Gradio 端口: {GRADIO_CONFIG.get('server_port', 'N/A')}")
except Exception as e:
    print(f"  ❌ 错误: {e}")
    bugs_found.append(f"配置加载失败: {e}")

# 总结
print("\n" + "=" * 70)
print("测试结果总结")
print("=" * 70)

if bugs_found:
    print(f"\n🔴 发现 {len(bugs_found)} 个 Bug:")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("\n✅ 未发现阻塞性 Bug")

if warnings_found:
    print(f"\n⚠️ 发现 {len(warnings_found)} 个警告:")
    for i, warning in enumerate(warnings_found, 1):
        print(f"  {i}. {warning}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
