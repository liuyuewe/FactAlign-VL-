"""
环境验证脚本
验证所有依赖是否正确安装
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "factalign-vl"))

def test_basic_imports():
    """测试基础库导入"""
    print("测试基础库导入...")
    packages = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("requests", "requests"),
        ("PIL", "Pillow"),
        ("cv2", "opencv-python"),
        ("matplotlib", "matplotlib"),
    ]

    for module, package in packages:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")

def test_deep_learning():
    """测试深度学习库"""
    print("\n测试深度学习库...")

    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
    except ImportError:
        print("❌ PyTorch - 未安装")

    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
    except ImportError:
        print("❌ Transformers - 未安装")

    try:
        import peft
        print(f"✅ PEFT {peft.__version__}")
    except ImportError:
        print("❌ PEFT - 未安装")

    try:
        import accelerate
        print(f"✅ Accelerate {accelerate.__version__}")
    except ImportError:
        print("❌ Accelerate - 未安装")

def test_nlp():
    """测试 NLP 库"""
    print("\n测试 NLP 库...")

    try:
        import spacy
        try:
            nlp = spacy.load("zh_core_web_sm")
            print("✅ SpaCy 中文模型 (zh_core_web_sm)")
        except:
            print("⚠️ SpaCy 已安装但中文模型未下载")
    except ImportError:
        print("❌ SpaCy - 未安装")

def test_web():
    """测试 Web 库"""
    print("\n测试 Web 库...")

    try:
        import gradio
        print(f"✅ Gradio {gradio.__version__}")
    except ImportError:
        print("❌ Gradio - 未安装")

def test_project_modules():
    """测试项目模块"""
    print("\n测试项目模块...")

    try:
        from checker.fact_decomposer import FactDecomposer
        print("✅ FactDecomposer")
    except Exception as e:
        print(f"❌ FactDecomposer: {e}")

    try:
        from checker.evidence_retriever import EvidenceRetriever
        print("✅ EvidenceRetriever")
    except Exception as e:
        print(f"❌ EvidenceRetriever: {e}")

    try:
        from checker.claim_verifier import ClaimVerifier
        print("✅ ClaimVerifier")
    except Exception as e:
        print(f"❌ ClaimVerifier: {e}")

def test_functionality():
    """测试功能"""
    print("\n测试功能...")

    try:
        from checker.fact_decomposer import FactDecomposer
        decomposer = FactDecomposer()
        text = "北京是中国的首都。"
        facts = decomposer.decompose(text)
        print(f"✅ 原子事实拆分功能正常 ({len(facts)} 个事实)")
    except Exception as e:
        print(f"❌ 原子事实拆分失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("FactAlign-VL 环境验证")
    print("=" * 60)

    test_basic_imports()
    test_deep_learning()
    test_nlp()
    test_web()
    test_project_modules()
    test_functionality()

    print("\n" + "=" * 60)
    print("✅ 环境验证完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
