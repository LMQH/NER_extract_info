"""
模型模块
包含所有NER模型相关的类
"""
from .mgeo_geographic_composition_analysis_chinese_base_model import MGeoGeographicCompositionAnalysisModel
# QwenFlashModel 已废弃，但保留代码
from .qwen_flash_model import QwenFlashModel

__all__ = [
    'MGeoGeographicCompositionAnalysisModel',
    'QwenFlashModel'  # 已废弃，但保留代码
]

