"""
MGeo地理组成分析模型调用模块
使用ModelScope的MGeo地理组成分析模型进行地理实体抽取和分析
支持地理组成分析、地理实体识别等任务
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MGeoGeographicCompositionAnalysisModel:
    """MGeo地理组成分析模型封装类，支持地理组成分析任务"""
    
    def __init__(self, model_path: str, use_model_id: bool = False, allow_download: bool = None):
        """
        初始化MGeo地理组成分析模型
        
        Args:
            model_path: 模型路径，可以是本地路径或ModelScope模型ID
                       模型ID格式: 'damo/mgeo_geographic_composition_analysis_chinese_base'
            use_model_id: 是否使用ModelScope模型ID（如果为True，则从ModelScope下载模型）
            allow_download: 是否允许从ModelScope下载（如果为False且本地模型失败，则不允许下载）
        """
        self.use_model_id = use_model_id
        
        # 读取 MODEL_EXISTS 环境变量，判断是否允许从ModelScope下载
        # MODEL_EXISTS=true 表示模型已存在，不允许下载
        # MODEL_EXISTS=false 表示模型可能不存在，允许从ModelScope下载
        import os
        if allow_download is None:
            # 默认根据 MODEL_EXISTS 判断（取反）
            allow_download = not os.getenv('MODEL_EXISTS', 'true').lower() == 'true'
        
        self.allow_download = allow_download
        
        if use_model_id:
            # 使用ModelScope模型ID
            self.model_path = model_path
        else:
            # 使用本地模型路径
            self.model_path = Path(model_path)
            if not self.model_path.exists():
                error_msg = (f"本地模型路径不存在: {model_path}。"
                           f"请检查模型文件是否已下载。")
                if not self.allow_download:
                    # MODEL_EXISTS=true 且不允许下载
                    error_msg += (" 由于 MODEL_EXISTS=true，已禁用ModelScope自动下载。"
                                   f"如需使用ModelScope自动下载，请设置 MODEL_EXISTS=false。")
                raise FileNotFoundError(error_msg)
            
            # 转换为绝对路径
            self.model_path = str(self.model_path.absolute())
        
        # 初始化pipeline
        try:
            # MGeo模型使用token-classification任务
            # 根据README: task = Tasks.token_classification
            task_type = Tasks.token_classification
            
            # 检查transformers版本兼容性
            try:
                import transformers
                major, minor = map(int, transformers.__version__.split('.')[:2])
                if major > 4 or (major == 4 and minor > 20):
                    logger.debug(f"transformers版本: {transformers.__version__},建议4.20.x")
            except Exception:
                pass
            
            # 优先使用ModelScope模型ID（让ModelScope处理版本兼容性）
            model_id = 'damo/mgeo_geographic_composition_analysis_chinese_base'
            
            if self.use_model_id:
                # 直接使用ModelScope模型ID
                self.pipeline = pipeline(
                    task_type,
                    model_id,
                    model_revision='master'
                )
                logger.info("模型加载成功")
            else:
                # 优先使用本地路径，避免重复下载
                try:
                    self.pipeline = pipeline(
                        task_type,
                        self.model_path,
                        model_revision='master'
                    )
                except Exception as e1:
                    # 根据allow_download标志决定是否fallback
                    if self.allow_download:
                        # 允许从ModelScope下载：保留fallback逻辑
                        logger.debug(f"本地路径加载失败,切换ModelScope: {str(e1)}")
                        self.pipeline = pipeline(
                            task_type,
                            model_id,
                            model_revision='master'
                        )
                    else:
                        # 不允许下载：移除fallback逻辑，抛出清晰异常
                        logger.error(f"本地模型加载失败: {str(e1)}")
                        # 构造详细的错误信息
                        error_detail = f"本地路径: {self.model_path}，错误: {str(e1)}"
                        error_msg = (f"本地模型加载失败: {error_detail}。"
                                     f"由于 MODEL_EXISTS=true，已禁用ModelScope自动下载。"
                                     f"请检查模型文件是否完整，或设置 MODEL_EXISTS=false 允许从ModelScope自动下载。")
                        
                        # 如果需要，导入 ModelLoadError 异常类
                        try:
                            from ..utils.exceptions import ModelLoadError
                            raise ModelLoadError(error_msg)
                        except ImportError:
                            # 如果 ModelLoadError 不存在，使用通用异常
                            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"模型加载失败: {str(e)}"
            
            # 检查是否是transformers版本兼容性问题
            if "configuration_bert" in str(e) or "No module named" in str(e):
                logger.debug("检测到transformers版本兼容性问题")
            
            import traceback
            logger.debug(traceback.format_exc())
            raise Exception(error_msg)
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        从文本中抽取地理实体（支持地理组成分析任务）
        
        Args:
            text: 输入文本（地址query，如"浙江省杭州市余杭区阿里巴巴西溪园区"）
            
        Returns:
            抽取结果字典，包含:
            - text: 原始文本
            - entities: 抽取的实体结果，格式为:
              {
                "output": [
                  {"type": "PB", "start": 0, "end": 3, "span": "浙江省"},
                  {"type": "PC", "start": 3, "end": 6, "span": "杭州市"},
                  ...
                ]
              }
            - error: 错误信息（如果有）
        
        示例:
            # 地理组成分析（地址成分分析）
            result = model.extract_entities(
                text='浙江省杭州市余杭区阿里巴巴西溪园区'
            )
            
            # 输出示例:
            # {
            #   "text": "浙江省杭州市余杭区阿里巴巴西溪园区",
            #   "entities": {
            #     "output": [
            #       {"type": "PB", "start": 0, "end": 3, "span": "浙江省"},
            #       {"type": "PC", "start": 3, "end": 6, "span": "杭州市"},
            #       {"type": "PD", "start": 6, "end": 9, "span": "余杭区"},
            #       {"type": "Entity", "start": 9, "end": 17, "span": "阿里巴巴西溪园区"}
            #     ]
            #   }
            # }
        """
        if not text or not text.strip():
            return {"text": text, "entities": {}}
        
        try:
            # MGeo模型使用token-classification任务，只需要input参数
            # 根据README示例：pipeline_ins(input=inputs)
            result = self.pipeline(input=text)
            
            # 将numpy类型转换为Python原生类型（解决Pydantic序列化问题）
            def convert_numpy_types(obj):
                """递归转换numpy类型为Python原生类型"""
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            # 转换结果中的numpy类型
            result = convert_numpy_types(result)
            
            # 确保返回格式一致
            if result and isinstance(result, dict):
                return {
                    "text": text,
                    "entities": result
                }
            else:
                return {
                    "text": text,
                    "entities": {"output": result} if result else {}
                }
        except Exception as e:
            error_msg = f"实体抽取出错: {str(e)}"
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "text": text,
                "entities": {},
                "error": error_msg
            }

