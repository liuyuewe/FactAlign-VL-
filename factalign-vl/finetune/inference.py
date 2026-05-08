"""
模型推理和验证模块
加载微调后的模型进行事实核查
"""

import torch
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"


def safe_resolve_path(base_dir: Path, filename: str) -> Path:
    """安全路径解析，防止路径遍历攻击"""
    base_dir = base_dir.resolve()
    requested_path = (base_dir / filename).resolve()
    if not requested_path.is_relative_to(base_dir):
        raise ValueError(f"非法路径访问: {filename}")
    return requested_path

class FactChecker:
    """事实核查器"""

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen-VL-Chat",
        lora_path: Optional[str] = None,
        device: str = "auto"
    ):
        self.base_model_name = base_model_name
        self.lora_path = lora_path
        self.device = self._get_device(device)
        self.processor = None
        self.model = None
        self.use_mock = True

    def _get_device(self, device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device

    def load_model(self):
        """加载模型"""
        print("=" * 60)
        print("加载模型")
        print("=" * 60)

        try:
            from transformers import AutoProcessor, AutoModelForVision2Seq
            from peft import PeftModel

            self.processor = AutoProcessor.from_pretrained(
                self.base_model_name,
                trust_remote_code=True
            )

            self.model = AutoModelForVision2Seq.from_pretrained(
                self.base_model_name,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True
            )

            if self.lora_path and Path(self.lora_path).exists():
                print(f"加载LoRA权重: {self.lora_path}")
                self.model = PeftModel.from_pretrained(self.model, self.lora_path)

            self.model.eval()
            self.use_mock = False

            print(f"模型加载成功，使用设备: {self.device}")
            return True

        except Exception as e:
            print(f"模型加载失败: {e}")
            print("将使用模拟模式")
            self.use_mock = True
            return False

    def check_fact(self, image_path: str, statement: str) -> Dict[str, Any]:
        """核查单个事实"""
        if self.use_mock:
            return self._mock_check(image_path, statement)

        try:
            if image_path:
                try:
                    safe_image_path = safe_resolve_path(DATA_DIR, image_path)
                except ValueError:
                    return {
                        "statement": statement,
                        "answer": "非法路径",
                        "is_correct": False,
                        "image_path": image_path,
                        "error": "非法路径访问"
                    }
                image = Image.open(safe_image_path).convert("RGB")

            prompt = f"判断以下陈述是否与图片内容完全一致，仅回答'是'或'否'。\n陈述：{statement}"

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            inputs = self.processor(
                text=[text],
                images=[image],
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    do_sample=False
                )

            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs['input_ids'], generated_ids)
            ]

            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0].strip()

            is_correct = "是" in output_text

            return {
                "statement": statement,
                "answer": output_text,
                "is_correct": is_correct,
                "image_path": image_path
            }

        except Exception as e:
            print(f"核查错误: {e}")
            return {
                "statement": statement,
                "answer": "错误",
                "is_correct": False,
                "image_path": image_path,
                "error": str(e)
            }

    def _mock_check(self, image_path: str, statement: str) -> Dict[str, Any]:
        """模拟核查"""
        import random
        answer = random.choice(["是", "否"])
        is_correct = random.random() > 0.3

        return {
            "statement": statement,
            "answer": answer,
            "is_correct": is_correct,
            "image_path": image_path,
            "mode": "mock"
        }

    def batch_check(
        self,
        image_paths: List[str],
        statements: List[str]
    ) -> List[Dict[str, Any]]:
        """批量核查"""
        results = []
        for image_path, statement in zip(image_paths, statements):
            result = self.check_fact(image_path, statement)
            results.append(result)
        return results

    def evaluate_on_dataset(
        self,
        data_path: str or Path,
        image_folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """在数据集上评估"""
        data_path = Path(data_path)

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        correct = 0
        total = 0
        results = []

        print(f"评估数据集: {len(data)} 条")

        for item in data:
            conversations = item.get("conversations", [])
            if len(conversations) < 2:
                continue

            user_msg = conversations[0]
            assistant_msg = conversations[1]

            image_path = None
            statement = ""
            for content in user_msg.get("content", []):
                if content.get("type") == "image":
                    image_path = content.get("image", "")
                elif content.get("type") == "text":
                    text = content.get("text", "")
                    if "陈述：" in text:
                        statement = text.split("陈述：")[-1].strip()

            expected_answer = assistant_msg.get("content", "")
            expected_is_correct = "是" in expected_answer

            if image_path and image_folder:
                image_path = str(Path(image_folder) / Path(image_path).name)

            if image_path:
                result = self.check_fact(image_path, statement)
                predicted_is_correct = result.get("is_correct", False)

                is_correct = (predicted_is_correct == expected_is_correct)
                correct += int(is_correct)
                total += 1

                results.append({
                    "statement": statement,
                    "expected": expected_is_correct,
                    "predicted": predicted_is_correct,
                    "is_correct": is_correct
                })

        accuracy = correct / total if total > 0 else 0

        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "results": results
        }


def load_fact_checker(
    base_model: str = "Qwen/Qwen-VL-Chat",
    lora_path: str = None,
    device: str = "auto"
) -> FactChecker:
    """加载事实核查器"""
    checker = FactChecker(
        base_model_name=base_model,
        lora_path=lora_path,
        device=device
    )
    checker.load_model()
    return checker


def demo_fact_check():
    """演示事实核查"""
    print("=" * 60)
    print("FactAlign-VL 事实核查演示")
    print("=" * 60)

    checker = FactChecker()

    print("\n使用模拟模式进行演示...")
    print("-" * 60)

    test_cases = [
        ("data/charts/bar/chart_00001.png", "苹果的数值是42"),
        ("data/charts/line/chart_00002.png", "6月的数值是75"),
        ("data/charts/table/chart_00003.png", "北京的总计是250"),
    ]

    for image_path, statement in test_cases:
        result = checker.check_fact(image_path, statement)
        print(f"\n陈述: {statement}")
        print(f"回答: {result['answer']}")
        print(f"正确: {'✅' if result['is_correct'] else '❌'}")

    print("\n" + "-" * 60)
    print("提示: 加载真实模型后将进行准确的事实核查")


if __name__ == "__main__":
    demo_fact_check()
