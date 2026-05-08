"""启动交互式演示界面"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.demo import launch_demo

if __name__ == "__main__":
    print("=" * 60)
    print("启动 FactAlign-VL 交互式演示")
    print("=" * 60)
    print("\n访问地址: http://localhost:7860")
    print("=" * 60)

    launch_demo()
