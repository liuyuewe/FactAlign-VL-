"""运行完整评估流程"""
import sys
sys.path.insert(0, 'factalign-vl')
from evaluation.report_generator import run_full_evaluation

if __name__ == "__main__":
    result = run_full_evaluation(use_mock_model=True)
    print("\n" + "=" * 70)
    print("评估完成!")
    print(f"报告已保存到: {result['report_path']}")
    print("=" * 70)
