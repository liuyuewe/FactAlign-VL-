"""
Gradio 交互式演示界面
展示 FactAlign-VL 视觉事实核查功能
"""

import gradio as gr
from typing import Optional, List, Dict, Any, Tuple
import re
import random
import html
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def escape_html(text: str) -> str:
    """HTML 安全转义，防止 XSS 攻击"""
    return html.escape(text, quote=True)


class TextHighlighter:
    """文本高亮渲染器"""

    @staticmethod
    def create_html_output(
        original_text: str,
        fact_results: List[Dict[str, Any]]
    ) -> str:
        """
        创建带高亮的 HTML 输出

        Args:
            original_text: 原始描述文本
            fact_results: 原子事实核查结果列表

        Returns:
            HTML 格式的高亮文本
        """
        if not fact_results:
            return f"<p style='color: gray;'>{original_text}</p>"

        html_parts = []

        for result in fact_results:
            fact_text = result.get("fact", "")
            is_correct = result.get("is_correct", True)

            if is_correct:
                escaped_fact = escape_html(fact_text)
                html_parts.append(
                    f'<span style="background-color: #d4edda; '
                    f'text-decoration: underline; color: #155724; cursor: pointer;" '
                    f'onclick="alert(\'&#10003; 正确\')">{escaped_fact}</span>'
                )
            else:
                escaped_fact = escape_html(fact_text)
                html_parts.append(
                    f'<span style="background-color: #f8d7da; '
                    f'text-decoration: wavy underline red; color: #721c24; cursor: pointer;" '
                    f'onclick="alert(\'&#10007; 错误\')">{escaped_fact}</span>'
                )

        return " ".join(html_parts)

    @staticmethod
    def create_comparison_html(
        original: str,
        corrected: str,
        error_facts: List[str]
    ) -> Tuple[str, str]:
        """创建对比视图 HTML"""
        original_html = f"<p>{original}</p>"

        corrected_html_parts = []
        for fact in error_facts:
            escaped_fact = escape_html(fact)
            highlighted = f'<span style="background-color: #fff3cd; font-weight: bold;">{escaped_fact}</span>'
            corrected_html_parts.append(highlighted)

        corrected_html = " ".join(corrected_html_parts) if corrected_html_parts else f"<p>{corrected}</p>"

        return original_html, corrected_html


class DemoFactChecker:
    """演示用事实核查器"""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self._load_model()

    def _load_model(self):
        """加载模型"""
        if not self.use_mock:
            try:
                from finetune.inference import FactChecker
                self.model = FactChecker()
                self.model.load_model()
            except Exception as e:
                print(f"模型加载失败: {e}")
                self.use_mock = True
                self.model = None
        else:
            self.model = None

    def check(self, image_path: str, statement: str) -> Dict[str, Any]:
        """核查陈述"""
        if self.use_mock or self.model is None:
            return self._mock_check(statement)
        return self.model.check_fact(image_path, statement)

    def _mock_check(self, statement: str) -> Dict[str, Any]:
        """模拟核查"""
        has_numbers = any(c.isdigit() for c in statement)
        has_comparison = any(word in statement for word in ["比", "大于", "小于", "更高", "更低", "最多", "最少"])

        if has_comparison:
            is_correct = random.random() < 0.4
        elif has_numbers:
            is_correct = random.random() < 0.6
        else:
            is_correct = random.random() < 0.8

        return {
            "statement": statement,
            "is_correct": is_correct,
            "answer": "是" if is_correct else "否",
            "mode": "mock"
        }


class SimpleFactDecomposer:
    """简单原子事实拆分器"""

    CHART_PATTERNS = [
        r'([^的]+)的数值是(\d+)',
        r'([^的]+)比([^的]+)(更?[\u4e00-\u9fa5]+)',
        r'([^的]+)是最多的',
        r'([^的]+)是最少的',
        r'(最高|最低|最大|最小|最多|最少)([^，,。]+)',
        r'(\d+)月[^，,。]*?(\d+)',
        r'([^，,。]+)[，,]?(?:总计|平均|总)是?(\d+)',
    ]

    def decompose(self, text: str) -> List[str]:
        """拆分文本为原子事实"""
        facts = []

        text = text.replace("。", ".|").replace(",", ".|").replace("，", ".|")
        sentences = [s.strip() for s in text.split("|") if s.strip()]

        for sent in sentences:
            if len(sent) < 5:
                continue

            if any(keyword in sent for keyword in ["数值", "是", "比", "最高", "最低", "最多", "最少"]):
                facts.append(sent)
            elif re.search(r'\d+', sent):
                facts.append(sent)

        if not facts:
            facts = sentences[:5] if sentences else [text]

        return facts[:8]

    def check_statement(self, text: str, statement: str, image_path: str = None) -> Dict[str, Any]:
        """检查单个陈述"""
        facts = self.decompose(text)
        results = []

        for fact in facts:
            is_match = fact in statement or statement in fact
            if is_match:
                results.append({"fact": fact, "matched": True})
            else:
                results.append({"fact": fact, "matched": False})

        return results


DEMO_CASES = {
    "数字篡改": {
        "image_path": "data/charts/bar/chart_00001.png",
        "description": "根据图表显示，苹果的数值是42，香蕉的数值是78，橙子的数值是55。其中橙子的表现最差。",
        "correct_answer": "苹果42，香蕉78，橙子应该是65（非55）"
    },
    "标签混淆": {
        "image_path": "data/charts/bar/chart_00002.png",
        "description": "从条形图中可以看出，A产品的销量最高达到120，B产品次之为95，C产品最低为45。",
        "correct_answer": "A最高，B其次，C最低"
    },
    "忽略异常值": {
        "image_path": "data/charts/line/chart_00003.png",
        "description": "折线图显示数据呈稳定上升趋势，从1月的30增长到6月的80，月均增长约8。",
        "correct_answer": "应指出3月存在异常下降"
    },
    "趋势错误": {
        "image_path": "data/charts/line/chart_00004.png",
        "description": "该折线图展示了下降趋势，数值从期初的100下降到期末的20。",
        "correct_answer": "实际是上升趋势"
    },
    "数据缺失": {
        "image_path": "data/charts/table/chart_00005.png",
        "description": "表格数据显示北京250，上海180，广州150，总计580。",
        "correct_answer": "表格未显示深圳数据"
    }
}


def create_demo_app() -> gr.Blocks:
    """创建演示应用"""

    checker = DemoFactChecker(use_mock=True)
    decomposer = SimpleFactDecomposer()
    highlighter = TextHighlighter()

    with gr.Blocks(
        title="FactAlign-VL 交互式演示",
        theme=gr.themes.Soft()
    ) as demo:

        gr.Markdown("""
        # 🔍 FactAlign-VL 视觉事实核查演示

        上传图表图像并输入 VLM 生成的描述，系统将自动核查其中的事实错误。
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 输入区域")

                image_input = gr.Image(
                    label="上传图表图像",
                    type="filepath",
                    height=300
                )

                description_input = gr.Textbox(
                    label="VLM 生成的描述文本",
                    placeholder="请输入需要核查的描述文本...",
                    lines=4
                )

                with gr.Row():
                    analyze_btn = gr.Button("🔍 开始核查", variant="primary")
                    clear_btn = gr.Button("🗑️ 清空", variant="secondary")

                gr.Markdown("### 📚 预设案例")

                case_dropdown = gr.Dropdown(
                    choices=list(DEMO_CASES.keys()),
                    label="选择预设错误案例",
                    value=None
                )

                load_case_btn = gr.Button("加载案例", variant="secondary")

            with gr.Column(scale=1):
                gr.Markdown("### 📊 核查结果")

                result_html = gr.HTML(
                    label="高亮核查结果",
                    value="<p style='color: gray;'>等待输入...</p>"
                )

                facts_accordion = gr.Accordion("📋 详细原子事实分析", open=False)
                with facts_accordion:
                    facts_output = gr.JSON(label="原子事实列表")

                confidence_gauge = gr.Number(label="整体置信度", value=0)

        def load_demo_case(case_name: str) -> Tuple[Any, str]:
            """加载预设案例"""
            if case_name and case_name in DEMO_CASES:
                case = DEMO_CASES[case_name]
                return case["image_path"], case["description"]
            return None, ""

        def process_image_and_text(
            image: Optional[str],
            text: str
        ) -> Tuple[str, Dict[str, Any], float]:
            """处理图像和文本"""
            if not text.strip():
                return (
                    "<p style='color: red;'>请输入需要核查的描述文本</p>",
                    {},
                    0.0
                )

            facts = decomposer.decompose(text)
            fact_results = []

            for fact in facts:
                check_result = checker.check(image or "", fact)
                fact_results.append({
                    "fact": fact,
                    "is_correct": check_result.get("is_correct", True),
                    "verdict": "✅ 正确" if check_result.get("is_correct", True) else "❌ 错误",
                    "answer": check_result.get("answer", "未知")
                })

            html_output = highlighter.create_html_output(text, fact_results)

            correct_count = sum(1 for r in fact_results if r["is_correct"])
            total_count = len(fact_results)
            confidence = correct_count / total_count if total_count > 0 else 0

            facts_dict = {
                "total_facts": total_count,
                "correct_count": correct_count,
                "error_count": total_count - correct_count,
                "facts": fact_results
            }

            return html_output, facts_dict, confidence

        def clear_all():
            """清空所有输入"""
            return None, "", "<p style='color: gray;'>等待输入...</p>", {}, 0.0

        load_case_btn.click(
            fn=load_demo_case,
            inputs=[case_dropdown],
            outputs=[image_input, description_input]
        )

        analyze_btn.click(
            fn=process_image_and_text,
            inputs=[image_input, description_input],
            outputs=[result_html, facts_output, confidence_gauge]
        )

        clear_btn.click(
            fn=clear_all,
            outputs=[image_input, description_input, result_html, facts_output, confidence_gauge]
        )

        gr.Markdown("""
        ---
        ### 📖 使用说明

        1. **上传图像**: 上传包含图表的图像文件（支持 PNG、JPG）
        2. **输入描述**: 输入 VLM 模型生成的图表描述文本
        3. **开始核查**: 点击按钮进行分析
        4. **查看结果**: 
           - 绿色下划线表示正确的陈述
           - 红色波浪线表示存在错误的陈述
        5. **预设案例**: 选择预设的错误案例进行演示

        ---
        ### 🎯 典型错误类型

        | 错误类型 | 描述 |
        |---------|------|
        | 数字篡改 | VLM 错误读取了数值（如42写成55）|
        | 标签混淆 | 混淆了不同类别的标签 |
        | 忽略异常值 | 未注意到图表中的异常数据点 |
        | 趋势错误 | 错误判断数据升降趋势 |
        | 数据缺失 | 遗漏了部分数据项 |
        """)

    return demo


def launch_demo():
    """启动演示应用"""
    import os
    server_name = os.environ.get("GRADIO_SERVER_HOST", "127.0.0.1")
    server_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    share = os.environ.get("GRADIO_SHARE", "false").lower() == "true"

    demo = create_demo_app()
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    launch_demo()
