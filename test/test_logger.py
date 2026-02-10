"""
测试日志配置功能
验证不同日志级别的输出
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入日志模块
from src.utils.logger import get_logger, set_log_level

# 获取日志记录器
logger = get_logger(__name__)

def test_log_levels():
    """测试不同日志级别"""
    print("=" * 60)
    print("测试日志配置功能")
    print("=" * 60)
    
    # 测试不同级别的日志
    logger.debug("这是一条DEBUG级别的日志")
    logger.info("这是一条INFO级别的日志")
    logger.warning("这是一条WARNING级别的日志")
    logger.error("这是一条ERROR级别的日志")
    logger.critical("这是一条CRITICAL级别的日志")
    
    print("\n" + "=" * 60)
    print("当前日志级别设置:", os.getenv('LOG_LEVEL', 'INFO'))
    print("=" * 60)

if __name__ == "__main__":
    test_log_levels()
