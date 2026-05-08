"""
事实核查核心模块
包含原子事实拆分、证据检索、验证等核心功能
"""

try:
    from .fact_decomposer import FactDecomposer
    from .evidence_retriever import EvidenceRetriever
    from .claim_verifier import ClaimVerifier
    __all__ = ['FactDecomposer', 'EvidenceRetriever', 'ClaimVerifier']
except ImportError:
    # 直接导入时的备用方案
    pass
