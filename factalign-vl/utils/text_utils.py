"""
文本处理工具函数
"""

import re
from typing import List


def clean_text(text: str) -> str:
    """
    清洗文本

    Args:
        text: 原始文本

    Returns:
        清洗后的文本
    """
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    text = text.strip()
    return text


def split_sentences(text: str) -> List[str]:
    """
    将文本拆分为句子

    Args:
        text: 输入文本

    Returns:
        句子列表
    """
    # 中文句子分隔符
    sentence_delimiters = r'[。！？；\n]'
    sentences = re.split(sentence_delimiters, text)
    # 过滤空句子并清洗
    sentences = [clean_text(s) for s in sentences if clean_text(s)]
    return sentences


def extract_keywords(text: str, top_k: int = 5) -> List[str]:
    """
    提取关键词（简单实现）

    Args:
        text: 输入文本
        top_k: 返回的关键词数量

    Returns:
        关键词列表
    """
    # TODO: 使用更复杂的关键词提取算法（如 TF-IDF 或 TextRank）
    # 这里使用简单的词频作为占位符

    # 简单的分词（按字符）
    words = list(text)

    # 统计词频
    word_freq = {}
    for word in words:
        if len(word.strip()) > 0 and not word.isdigit():
            word_freq[word] = word_freq.get(word, 0) + 1

    # 返回频率最高的词
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:top_k]]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（简单实现）

    Args:
        text1: 第一段文本
        text2: 第二段文本

    Returns:
        相似度分数 [0, 1]
    """
    # TODO: 使用更复杂的相似度计算方法（如余弦相似度）
    # 这里使用简单的 Jaccard 相似度作为占位符

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)
