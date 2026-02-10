"""
API 依赖项
用于依赖注入
"""
from fastapi import Depends
from src.model_manager import ModelManager
from src.processor_mgeo import AddressCompleter
from src.config import ConfigManager
from src.database import DatabaseConnection
from pathlib import Path

# 这些将在 app.py 中初始化
_model_manager: ModelManager = None
_config_manager: ConfigManager = None
_db_connection: DatabaseConnection = None
_address_completer: AddressCompleter = None
_project_root: Path = None


def init_dependencies(model_manager: ModelManager, 
                     config_manager: ConfigManager, project_root: Path,
                     db_connection: DatabaseConnection = None):
    """初始化依赖项"""
    global _model_manager, _config_manager, _project_root
    global _db_connection, _address_completer
    
    _model_manager = model_manager
    _config_manager = config_manager
    _project_root = project_root
    
    # 初始化数据库连接和地址补全器
    # 如果提供了db_connection，则使用它；否则创建新的
    try:
        if db_connection is None:
            _db_connection = DatabaseConnection()
        else:
            _db_connection = db_connection
        
        if _db_connection:
            _address_completer = AddressCompleter(_db_connection)
        else:
            _address_completer = None
    except Exception as e:
        import logging
        logger = logging.getLogger("NER_API")
        logger.warning(f"数据库连接初始化失败，地址补全功能将不可用: {str(e)}")
        _db_connection = None
        _address_completer = None


def get_model_manager() -> ModelManager:
    """获取模型管理器"""
    return _model_manager


def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    return _config_manager


def get_project_root() -> Path:
    """获取项目根目录"""
    return _project_root


def get_db_connection() -> DatabaseConnection:
    """获取数据库连接"""
    return _db_connection


def get_address_completer() -> AddressCompleter:
    """获取地址补全器"""
    return _address_completer

