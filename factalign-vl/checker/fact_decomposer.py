"""
原子事实拆分模块
使用 SpaCy 进行中文句子拆分和实体提取
"""

import spacy
from typing import List, Dict, Any

# 默认 SpaCy 模型
SPACY_MODEL = "zh_core_web_sm"


class FactDecomposer:
    """原子事实拆分器"""

    def __init__(self, model_name: str = None):
        """
        初始化事实拆分器

        Args:
            model_name: SpaCy 模型名称，默认使用 zh_core_web_sm
        """
        self.model_name = model_name or SPACY_MODEL
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """加载 SpaCy 模型"""
        try:
            self.nlp = spacy.load(self.model_name)
        except OSError:
            print(f"正在下载 SpaCy 模型: {self.model_name}")
            spacy.cli.download(self.model_name)
            self.nlp = spacy.load(self.model_name)

    def decompose(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本拆分为原子事实

        Args:
            text: 输入文本

        Returns:
            原子事实列表，每个事实包含文本、实体、关系等信息
        """
        doc = self.nlp(text)
        atomic_facts = []

        # 按句子拆分
        for sent in doc.sents:
            fact = {
                "text": sent.text.strip(),
                "entities": [(ent.text, ent.label_) for ent in sent.ents],
                "root": sent.root.text if sent.root else None,
                "dependencies": [
                    (token.text, token.dep_, token.head.text)
                    for token in sent
                ],
            }
            atomic_facts.append(fact)

        return atomic_facts

    def extract_claims(self, text: str) -> List[str]:
        """
        从文本中提取主张/声明

        Args:
            text: 输入文本

        Returns:
            主张列表
        """
        doc = self.nlp(text)
        claims = []

        for sent in doc.sents:
            # 简单的启发式规则：包含特定动词的句子可能是主张
            if any(token.pos_ == "VERB" for token in sent):
                claims.append(sent.text.strip())

        return claims
