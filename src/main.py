"""
NER Demo核心业务逻辑模块

本模块提供NERDemo类，包含实体抽取的核心业务逻辑。
现在项目使用FastAPI服务模式（app.py），不再使用命令行脚本模式。
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .config import ConfigManager
from .utils.logger import get_logger

logger = get_logger(__name__)


class NERDemo:
    """
    NER Demo核心业务类
    
    提供文件处理和实体抽取的核心功能。
    注意：现在推荐使用FastAPI服务（app.py）进行API调用，而不是直接使用此类。
    """
    
    def __init__(self):
        """初始化NER Demo"""
        self.config_manager = ConfigManager()
    
    def save_results(self, results: Dict[str, Any], output_path: str = None) -> str:
        """
        保存结果到指定路径或返回JSON字符串
        
        Args:
            results: 处理结果字典
            output_path: 输出文件路径，如果为None则返回JSON字符串
            
        Returns:
            输出文件路径或JSON字符串
        """
        # 生成输出数据结构
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_data = {
            "timestamp": timestamp,
            "files_count": len(results),
            "results": results
        }
        
        if output_path:
            # 保存到文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存: {output_file}")
            return str(output_file)
        else:
            # 返回JSON字符串
            return json.dumps(output_data, ensure_ascii=False, indent=2)
