"""
Gradio Web 应用主文件
提供视觉事实核查的用户界面
"""

import gradio as gr
from typing import Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from checker.fact_decomposer import FactDecomposer
from checker.evidence_retriever import EvidenceRetriever
from checker.claim_verifier import ClaimVerifier


def create_app() -> gr.Blocks:
    """
    创建 Gradio 应用

    Returns:
        Gradio Blocks 应用
    """
    # 初始化组件
    decomposer = FactDecomposer()
    retriever = EvidenceRetriever()
    verifier = ClaimVerifier()

    def process_claim(
        image: Optional[str],
        text: str,
        evidence_text: str
    ):
        """
        处理用户输入的主张

        Args:
            image: 上传的图像路径
            text: 文本主张
            evidence_text: 参考证据文本

        Returns:
            验证结果
        """
        if not text.strip():
            return "请输入需要验证的文本主张", ""

        # 1. 原子事实拆分
        atomic_facts = decomposer.decompose(text)
        claims = decomposer.extract_claims(text)

        # 2. 准备证据语料
        evidence_corpus = []
        if evidence_text.strip():
            evidence_corpus = [s.strip() for s in evidence_text.split('\n') if s.strip()]

        # 3. 对每个主张进行验证
        results = []
        for claim in claims[:3]:  # 限制处理前3个主张
            # 检索证据
            evidence = retriever.retrieve_text_evidence(claim, evidence_corpus)

            # 验证主张
            verification = verifier.verify(claim, evidence)

            results.append({
                "claim": claim,
                "verdict": verification["verdict"],
                "confidence": verification["confidence"],
                "reasoning": verification["reasoning"]
            })

        # 格式化输出
        output_text = "## 事实核查结果\n\n"
        for i, result in enumerate(results, 1):
            verdict_emoji = {
                "supported": "✅",
                "refuted": "❌",
                "not_enough_info": "⚠️"
            }.get(result["verdict"], "❓")

            output_text += f"### 主张 {i}: {result['claim']}\n"
            output_text += f"**判决**: {verdict_emoji} {result['verdict']}\n"
            output_text += f"**置信度**: {result['confidence']:.2%}\n"
            output_text += f"**理由**: {result['reasoning']}\n\n"

        # 原子事实信息
        facts_text = "## 原子事实拆分\n\n"
        for i, fact in enumerate(atomic_facts[:5], 1):
            facts_text += f"**{i}.** {fact['text']}\n"
            if fact['entities']:
                entities_str = ", ".join([f"{ent[0]}({ent[1]})" for ent in fact['entities'][:3]])
                facts_text += f"   - 实体: {entities_str}\n"
            facts_text += "\n"

        return output_text, facts_text

    # 创建界面
    with gr.Blocks(title="FactAlign-VL 视觉事实核查器") as app:
        gr.Markdown("""
        # 🔍 FactAlign-VL 视觉事实核查器

        上传图像并输入文本主张，系统将自动核查其真实性。
        """)

        with gr.Row():
            with gr.Column(scale=1):
                # 输入区域
                image_input = gr.Image(
                    label="上传图像（可选）",
                    type="filepath"
                )
                text_input = gr.Textbox(
                    label="输入主张文本",
                    placeholder="请输入需要验证的文本主张...",
                    lines=3
                )
                evidence_input = gr.Textbox(
                    label="参考证据文本（可选）",
                    placeholder="输入参考证据，每行一条...",
                    lines=5
                )
                submit_btn = gr.Button("开始核查", variant="primary")

            with gr.Column(scale=1):
                # 输出区域
                result_output = gr.Markdown(label="核查结果")
                facts_output = gr.Markdown(label="原子事实拆分")

        # 绑定事件
        submit_btn.click(
            fn=process_claim,
            inputs=[image_input, text_input, evidence_input],
            outputs=[result_output, facts_output]
        )

        # 示例
        gr.Examples(
            examples=[
                [None, "北京是中国的首都，位于华北平原。", ""],
                [None, "上海是中国最大的城市，人口超过3000万。", ""],
            ],
            inputs=[image_input, text_input, evidence_input],
            label="示例输入"
        )

    return app


def main():
    """启动应用"""
    import os
    server_name = os.environ.get("GRADIO_SERVER_HOST", "127.0.0.1")
    server_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    share = os.environ.get("GRADIO_SHARE", "false").lower() == "true"

    app = create_app()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    main()
