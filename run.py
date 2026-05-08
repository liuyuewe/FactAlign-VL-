"""
FactAlign-VL 启动脚本
"""

import sys
from pathlib import Path

# 添加项目目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "factalign-vl"))

from factalign_vl.app.main import main

if __name__ == "__main__":
    main()
