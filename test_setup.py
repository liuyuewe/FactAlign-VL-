"""
项目设置测试脚本
验证项目骨架是否正确创建
"""

import sys
from pathlib import Path

# 添加项目目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "factalign-vl"))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")

    # 使用直接导入方式（不依赖包安装）
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("fact_decomposer", project_root / "factalign-vl/checker/fact_decomposer.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["fact_decomposer"] = module
        spec.loader.exec_module(module)
        print("✅ fact_decomposer.py 语法正确")
    except Exception as e:
        print(f"❌ fact_decomposer.py 有错误: {e}")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("evidence_retriever", project_root / "factalign-vl/checker/evidence_retriever.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["evidence_retriever"] = module
        spec.loader.exec_module(module)
        print("✅ evidence_retriever.py 语法正确")
    except Exception as e:
        print(f"❌ evidence_retriever.py 有错误: {e}")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("claim_verifier", project_root / "factalign-vl/checker/claim_verifier.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["claim_verifier"] = module
        spec.loader.exec_module(module)
        print("✅ claim_verifier.py 语法正确")
    except Exception as e:
        print(f"❌ claim_verifier.py 有错误: {e}")

def test_directory_structure():
    """测试目录结构"""
    print("\n测试目录结构...")

    dirs_to_check = [
        "factalign-vl/data",
        "factalign-vl/models",
        "factalign-vl/checker",
        "factalign-vl/app",
        "factalign-vl/utils",
        "factalign-vl/configs",
    ]

    all_exist = True
    for dir_path in dirs_to_check:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path} 存在")
        else:
            print(f"❌ {dir_path} 不存在")
            all_exist = False

    return all_exist

def test_files():
    """测试关键文件"""
    print("\n测试关键文件...")

    files_to_check = [
        "requirements.txt",
        "requirements-dev.txt",
        "run.py",
        "setup.py",
        "INSTALL.md",
        "factalign-vl/__init__.py",
        "factalign-vl/checker/__init__.py",
        "factalign-vl/app/__init__.py",
        "factalign-vl/utils/__init__.py",
        "factalign-vl/configs/config.py",
        "factalign-vl/checker/fact_decomposer.py",
        "factalign-vl/checker/evidence_retriever.py",
        "factalign-vl/checker/claim_verifier.py",
        "factalign-vl/utils/text_utils.py",
        "factalign-vl/utils/image_utils.py",
        "factalign-vl/app/main.py",
    ]

    all_exist = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_virtual_environment():
    """测试虚拟环境"""
    print("\n测试虚拟环境...")

    venv_path = project_root / "venv"
    if venv_path.exists():
        print(f"✅ 虚拟环境目录存在: {venv_path}")

        # 检查关键文件
        python_exe = venv_path / "Scripts" / "python.exe"
        if python_exe.exists():
            print(f"✅ Python 解释器存在: {python_exe}")
        else:
            print(f"❌ Python 解释器不存在")

        pyvenv_cfg = venv_path / "pyvenv.cfg"
        if pyvenv_cfg.exists():
            print(f"✅ pyvenv.cfg 存在")
            # 读取配置
            with open(pyvenv_cfg, 'r') as f:
                content = f.read()
                print(f"   配置内容:\n{content}")
        else:
            print(f"❌ pyvenv.cfg 不存在")
    else:
        print(f"❌ 虚拟环境目录不存在")

def main():
    """主函数"""
    print("=" * 60)
    print("FactAlign-VL 项目设置测试")
    print("=" * 60)

    test_imports()
    dir_ok = test_directory_structure()
    files_ok = test_files()
    test_virtual_environment()

    print("\n" + "=" * 60)
    if dir_ok and files_ok:
        print("✅ 项目骨架创建成功！")
        print("\n下一步：")
        print("1. 激活虚拟环境: venv\\Scripts\\activate")
        print("2. 安装依赖: pip install -r requirements.txt")
        print("3. 安装 SpaCy 中文模型: python -m spacy download zh_core_web_sm")
        print("4. 运行应用: python run.py")
    else:
        print("❌ 项目骨架创建不完整，请检查错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main()
