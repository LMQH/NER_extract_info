"""
NER Demo FastAPI服务
提供RESTful API接口，支持前端传入文本和模型选择进行实体抽取
"""
import sys
import os
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 使用 env_loader 根据域名自动加载对应的环境配置文件
# 如果所有环境文件加载失败，会尝试加载 .env 作为兼容备选
from src.config.env_loader import load_config
config = load_config()
if config:
    # 将配置加载到环境变量中
    for key, value in config.items():
        if value is not None:
            os.environ[key] = str(value)

# 设置 ModelScope 缓存目录（优先使用本地模型，避免重复下载）
# 统一使用 MODEL_PATH 配置，避免重复配置
model_path = os.getenv('MODEL_PATH', 'model/')
model_path = model_path.strip()
if model_path and not model_path.endswith('/') and not model_path.endswith('\\'):
    model_path = model_path + '/'

# 转换为绝对路径
cache_path = Path(model_path)

# 根据 MODEL_EXISTS 决定是否设置 ModelScope 缓存目录
# MODEL_EXISTS=true: 模型存在，不设置MODELSCOPE_CACHE，确保ModelScope直接从本地路径加载
# MODEL_EXISTS=false: 模型可能不存在，设置MODELSCOPE_CACHE，允许ModelScope下载
model_exists = os.getenv('MODEL_EXISTS', 'true').lower() == 'true'

if model_exists:
    # 严格模式：不设置MODELSCOPE_CACHE，确保ModelScope直接从本地路径加载
    pass
else:
    # 允许下载模式：设置MODELSCOPE_CACHE，允许ModelScope下载到缓存目录
    if cache_path.is_absolute():
        modelscope_cache = str(cache_path.resolve())
    else:
        # 相对路径，相对于项目根目录
        modelscope_cache = str((project_root / model_path).resolve())
    
    os.environ['MODELSCOPE_CACHE'] = modelscope_cache

from src.model_manager import ModelManager
from src.config import ConfigManager
from src.database import DatabaseConnection
from src.api.dependencies import init_dependencies
from src.api.routes import system, extract, file


def cleanup_old_logs(log_dir: Path, retention_days: int = 30) -> None:
    """
    清理超过指定天数的日志文件
    
    Args:
        log_dir: 日志目录路径
        retention_days: 保留天数，默认30天
    """
    try:
        if not log_dir.exists():
            return
        
        current_date = datetime.now()
        deleted_count = 0
        deleted_files = []
        
        # 日志文件命名格式：inference_YYYYMMDD.log
        log_pattern = re.compile(r'^inference_(\d{8})\.log$')
        
        for log_file in log_dir.iterdir():
            if not log_file.is_file():
                continue
            
            # 匹配日志文件名格式
            match = log_pattern.match(log_file.name)
            if not match:
                continue
            
            # 解析文件中的日期
            try:
                file_date_str = match.group(1)
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                
                # 计算日期差
                days_diff = (current_date - file_date).days
                
                # 删除超过保留天数的文件
                if days_diff > retention_days:
                    log_file.unlink()
                    deleted_count += 1
                    deleted_files.append(log_file.name)
            except (ValueError, OSError) as e:
                # 日期解析失败或文件删除失败，记录但继续处理其他文件
                logging.getLogger("NER_API").debug(f"处理日志文件 {log_file.name} 时出错: {str(e)}")
                continue
        
        # 记录清理结果
        if deleted_count > 0:
            logger = logging.getLogger("NER_API")
            logger.info(f"日志清理完成: 删除了 {deleted_count} 个超过 {retention_days} 天的日志文件")
            logger.debug(f"已删除的日志文件: {', '.join(deleted_files)}")
        else:
            logger = logging.getLogger("NER_API")
            logger.debug(f"日志清理完成: 没有需要删除的日志文件（保留 {retention_days} 天）")
    
    except Exception as e:
        # 清理失败不应影响应用启动
        logging.getLogger("NER_API").warning(f"日志清理过程中发生错误: {str(e)}")


# 配置日志系统
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# 创建日志文件名（按日期）
log_file = log_dir / f"inference_{datetime.now().strftime('%Y%m%d')}.log"

# 从环境变量读取日志级别,默认为INFO
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# 配置日志格式
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(log_format, date_format)

# 创建文件处理器（记录所有级别，包括DEBUG）
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # 文件始终记录DEBUG级别
file_handler.setFormatter(formatter)

# 创建控制台处理器（根据环境变量设置级别）
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)  # 控制台输出级别由LOG_LEVEL控制
console_handler.setFormatter(formatter)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # 根日志记录器设置为DEBUG，以便文件处理器可以记录DEBUG日志
root_logger.handlers = []  # 清除可能存在的旧处理器
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("NER_API")

# 清理超过30天的旧日志文件
cleanup_old_logs(log_dir, retention_days=30)

# 验证和记录环境变量加载情况（在日志系统初始化后）
logger.debug("=" * 60)
logger.debug("环境变量加载验证")
logger.debug(f"已加载的配置文件数量: {len(config) if config else 0}")

# 记录关键环境变量（不显示敏感信息）
key_env_vars = [
    'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB',
    'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE',
    'ENV_TYPE'
]
for key in key_env_vars:
    value = os.getenv(key)
    if value:
        logger.debug(f"  {key}: {value}")
    else:
        logger.debug(f"  {key}: 未设置")

# 记录Redis配置
redis_host = os.getenv('REDIS_HOST', 'NOT_SET')
redis_port = os.getenv('REDIS_PORT', 'NOT_SET')
if redis_host == 'localhost' or redis_host == 'NOT_SET':
    logger.warning(f"Redis配置未正确加载: {redis_host}:{redis_port}")
else:
    logger.debug(f"Redis配置: {redis_host}:{redis_port}")

# 创建FastAPI应用
# 如果通过反向代理访问，需要设置路由前缀来匹配反向代理的路径前缀
# 可以通过环境变量 ROOT_PATH 配置，默认为 /ner_extract_info
# 如果设置为空字符串，则不添加前缀（用于直接访问）
# 注意：如果反向代理保留了完整路径（如 /ner_extract_info/api/health），
# 我们需要在路由注册时添加 prefix 来匹配完整路径
# root_path 参数仅用于 OpenAPI 文档生成，不影响路由匹配
router_prefix = os.getenv("ROOT_PATH", "/ner_extract_info").strip()
if not router_prefix:
    router_prefix = None

# 注意：不设置 root_path，因为反向代理保留了完整路径
# root_path 主要用于反向代理去掉路径前缀的情况
# 如果反向代理保留了完整路径，我们只需要在路由注册时添加 prefix
app = FastAPI(
    title="NER Demo API",
    description="基于ModelScope的中文命名实体识别（NER）API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # 允许所有来源（开发环境）
        "<系统域名>",  # 系统域名，请根据实际部署环境修改
        "http://localhost:13110",
        "http://127.0.0.1:13110",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 初始化模型管理器
model_manager = ModelManager(base_path=str(project_root))
config_manager = ConfigManager()

# 测试MySQL数据库连接
db_connection = None
db_status = "未配置"
try:
    db_connection = DatabaseConnection()
    if db_connection.test_connection():
        db_status = "✓ 连接成功"
    else:
        db_status = "✗ 连接失败"
        logger.warning("MySQL数据库连接测试失败")
except Exception as e:
    db_status = f"✗ 连接失败"
    logger.error(f"MySQL数据库连接初始化失败: {str(e)}")

# 初始化依赖项（传入已测试的数据库连接）
init_dependencies(model_manager, config_manager, project_root, db_connection)

# 初始化统计数据库连接（独立的数据库，用于API使用统计和错误日志）
stats_db_connection = None
stats_db_status = "未配置"
try:
    from src.database.statistics_db_connection import StatisticsDatabaseConnection
    stats_db_connection = StatisticsDatabaseConnection()
    if stats_db_connection.test_connection():
        stats_db_status = "✓ 连接成功"
    else:
        stats_db_status = "✗ 连接失败"
        logger.warning("统计数据库连接测试失败")
except Exception as e:
    stats_db_status = f"✗ 连接失败"
    logger.error(f"统计数据库连接初始化失败: {str(e)}")

# 初始化统计表（检查并创建）
if stats_db_connection:
    try:
        stats_db_connection.init_statistics_tables()
    except Exception as e:
        logger.error(f"统计表初始化失败: {str(e)}")

# 导入定时任务模块
sync_task = None
try:
    from src.tasks.api_usage_sync import ApiUsageSyncTask
    if stats_db_connection:
        sync_task = ApiUsageSyncTask(db_connection=stats_db_connection)
except Exception as e:
    logger.warning(f"初始化API使用统计同步任务失败: {str(e)}")
    sync_task = None

# 注册路由
# 如果反向代理保留了完整路径（如 /ner_extract_info/api/health），
# 需要在注册路由时添加 prefix 来匹配完整路径
# 如果 router_prefix 为 None，则不添加前缀（用于直接访问，如 /api/health）
if router_prefix:
    app.include_router(system.router, prefix=router_prefix)
    app.include_router(extract.router, prefix=router_prefix)
    app.include_router(file.router, prefix=router_prefix)
    logger.info(f"路由已注册，前缀: {router_prefix}")
    
    # 打印所有注册的路由（用于调试）
    logger.debug("已注册的路由列表:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            logger.debug(f"  {methods} {route.path}")
else:
    app.include_router(system.router)
    app.include_router(extract.router)
    app.include_router(file.router)
    logger.info("路由已注册，直接访问模式")

# 启动定时任务（使用FastAPI的startup事件）
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    if sync_task and sync_task.enabled:
        import asyncio
        # 启动后台任务
        asyncio.create_task(sync_task.run_periodic())

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的清理操作"""
    if sync_task:
        sync_task.stop()

if __name__ == "__main__":
    import uvicorn
    
    logger.info("服务启动: http://0.0.0.0:13110")
    logger.info(f"MySQL数据库: {db_status}")
    logger.info(f"统计数据库: {stats_db_status}")
    
    # 启动FastAPI服务
    uvicorn.run(app, host="0.0.0.0", port=13110, reload=True)
