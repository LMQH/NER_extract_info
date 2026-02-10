"""
Windows启动脚本
启动FastAPI API服务
"""
import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

# 切换到项目根目录
os.chdir(project_root)

# 添加项目根目录到Python路径
sys.path.insert(0, str(project_root))

# 启动FastAPI服务
if __name__ == "__main__":
    import uvicorn
    from src.utils.logger import get_logger
    
    logger = get_logger("StartUp")
    
    logger.info("=" * 60)
    logger.info("NER Demo API服务启动 (FastAPI)")
    logger.info("=" * 60)
    logger.info("正在启动服务...")
    logger.info("API文档: http://localhost:13110/docs")
    logger.info("API文档 (ReDoc): http://localhost:13110/redoc")
    logger.info("=" * 60)
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 60)
    
    # 启动FastAPI服务
    # 使用 reload=True 支持热重载（开发模式）
    uvicorn.run("app:app", host="0.0.0.0", port=13110, reload=True)

