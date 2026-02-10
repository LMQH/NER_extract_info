"""
Redis连接测试脚本
测试Redis服务器的连接状态和基本功能
"""
import sys
import time
import logging
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# ==================== Redis配置区域 ====================
# 在此处定义Redis连接配置
REDIS_CONFIG = {
    'host': 'localhost',               # Redis服务器地址
    'port': 6379,                      # Redis端口
    'db': 0,                           # Redis数据库编号
    'password': 'password',            # Redis密码（如果有）
    'connect_timeout': 10,             # 连接超时时间（秒）
    'socket_timeout': 10,              # Socket超时时间（秒）
    'decode_responses': False          # 是否自动解码响应（False表示返回bytes）
}
# ======================================================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("Redis_Test")


def test_redis_import():
    """测试Redis库是否已安装"""
    try:
        import redis
        logger.info(f"✓ Redis库已安装，版本: {redis.__version__}")
        return redis
    except ImportError:
        logger.error("✗ Redis库未安装，请运行: pip install redis")
        return None


def test_redis_connection(redis_module) -> Optional[Any]:
    """测试Redis连接"""
    logger.info("=" * 60)
    logger.info("开始测试Redis连接...")
    logger.info(f"连接配置: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}, DB={REDIS_CONFIG['db']}")
    logger.info("=" * 60)
    
    try:
        # 创建Redis客户端
        redis_client = redis_module.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            db=REDIS_CONFIG['db'],
            password=REDIS_CONFIG['password'],
            decode_responses=REDIS_CONFIG['decode_responses'],
            socket_connect_timeout=REDIS_CONFIG['connect_timeout'],
            socket_timeout=REDIS_CONFIG['socket_timeout']
        )
        
        # 测试连接（ping）
        start_time = time.time()
        result = redis_client.ping()
        connect_time = time.time() - start_time
        
        if result:
            logger.info(f"✓ Redis连接成功！响应时间: {connect_time*1000:.2f}毫秒")
            return redis_client
        else:
            logger.error("✗ Redis连接失败：ping返回False")
            return None
            
    except redis_module.ConnectionError as e:
        logger.error(f"✗ Redis连接错误（ConnectionError）: {str(e)}")
        logger.error("可能的原因：")
        logger.error("  1. Redis服务器未启动")
        logger.error("  2. 网络连接问题（防火墙、端口未开放）")
        logger.error("  3. 主机地址或端口配置错误")
        return None
    except redis_module.TimeoutError as e:
        logger.error(f"✗ Redis连接超时（TimeoutError）: {str(e)}")
        logger.error("可能的原因：")
        logger.error("  1. 网络延迟过高")
        logger.error("  2. 超时时间设置过短")
        logger.error("  3. Redis服务器负载过高")
        return None
    except redis_module.AuthenticationError as e:
        logger.error(f"✗ Redis认证失败（AuthenticationError）: {str(e)}")
        logger.error("可能的原因：")
        logger.error("  1. 密码配置错误")
        logger.error("  2. Redis服务器未设置密码但提供了密码")
        logger.error("  3. Redis服务器设置了密码但未提供密码")
        return None
    except Exception as e:
        logger.error(f"✗ Redis连接失败（未知错误）: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        return None


def test_redis_info(redis_client) -> bool:
    """测试获取Redis服务器信息"""
    logger.info("-" * 60)
    logger.info("测试：获取Redis服务器信息")
    logger.info("-" * 60)
    
    try:
        info = redis_client.info()
        logger.info("✓ 成功获取Redis服务器信息")
        
        # 显示关键信息
        if isinstance(info, dict):
            logger.info(f"  Redis版本: {info.get('redis_version', 'N/A')}")
            logger.info(f"  运行模式: {info.get('redis_mode', 'N/A')}")
            logger.info(f"  操作系统: {info.get('os', 'N/A')}")
            logger.info(f"  已使用内存: {info.get('used_memory_human', 'N/A')}")
            logger.info(f"  连接客户端数: {info.get('connected_clients', 'N/A')}")
            logger.info(f"  总命令数: {info.get('total_commands_processed', 'N/A')}")
        else:
            logger.warning("  Redis信息格式异常")
        
        return True
    except Exception as e:
        logger.error(f"✗ 获取Redis服务器信息失败: {str(e)}")
        return False


def test_redis_basic_operations(redis_client) -> bool:
    """测试Redis基本操作（SET, GET, DELETE）"""
    logger.info("-" * 60)
    logger.info("测试：Redis基本操作（SET, GET, DELETE）")
    logger.info("-" * 60)
    
    test_key = "test:connection:key"
    test_value = "test_value_12345"
    
    try:
        # 测试 SET
        logger.info(f"  1. SET操作: {test_key} = {test_value}")
        result = redis_client.set(test_key, test_value.encode('utf-8'), ex=60)  # 60秒过期
        if result:
            logger.info("     ✓ SET操作成功")
        else:
            logger.error("     ✗ SET操作失败")
            return False
        
        # 测试 GET
        logger.info(f"  2. GET操作: {test_key}")
        result = redis_client.get(test_key)
        if result:
            decoded_value = result.decode('utf-8') if isinstance(result, bytes) else result
            if decoded_value == test_value:
                logger.info(f"     ✓ GET操作成功，值: {decoded_value}")
            else:
                logger.error(f"     ✗ GET操作返回的值不匹配: {decoded_value}")
                return False
        else:
            logger.error("     ✗ GET操作失败：键不存在")
            return False
        
        # 测试 DELETE
        logger.info(f"  3. DELETE操作: {test_key}")
        result = redis_client.delete(test_key)
        if result:
            logger.info("     ✓ DELETE操作成功")
        else:
            logger.warning("     ⚠ DELETE操作返回0（键可能不存在）")
        
        # 验证删除
        result = redis_client.get(test_key)
        if result is None:
            logger.info("     ✓ 验证：键已成功删除")
        else:
            logger.warning("     ⚠ 验证：键仍然存在")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Redis基本操作测试失败: {str(e)}")
        return False


def test_redis_performance(redis_client, iterations: int = 100) -> bool:
    """测试Redis性能（批量操作）"""
    logger.info("-" * 60)
    logger.info(f"测试：Redis性能测试（{iterations}次操作）")
    logger.info("-" * 60)
    
    test_key_prefix = "test:performance:"
    
    try:
        # 批量写入测试
        logger.info(f"  1. 批量写入测试（{iterations}次）")
        start_time = time.time()
        for i in range(iterations):
            key = f"{test_key_prefix}{i}"
            value = f"value_{i}_{time.time()}"
            redis_client.set(key, value.encode('utf-8'), ex=300)  # 5分钟过期
        write_time = time.time() - start_time
        write_ops_per_sec = iterations / write_time
        logger.info(f"     ✓ 写入完成，耗时: {write_time*1000:.2f}毫秒")
        logger.info(f"     ✓ 写入速度: {write_ops_per_sec:.2f} 操作/秒")
        
        # 批量读取测试
        logger.info(f"  2. 批量读取测试（{iterations}次）")
        start_time = time.time()
        for i in range(iterations):
            key = f"{test_key_prefix}{i}"
            redis_client.get(key)
        read_time = time.time() - start_time
        read_ops_per_sec = iterations / read_time
        logger.info(f"     ✓ 读取完成，耗时: {read_time*1000:.2f}毫秒")
        logger.info(f"     ✓ 读取速度: {read_ops_per_sec:.2f} 操作/秒")
        
        # 清理测试数据
        logger.info(f"  3. 清理测试数据")
        keys_to_delete = [f"{test_key_prefix}{i}" for i in range(iterations)]
        deleted_count = redis_client.delete(*keys_to_delete)
        logger.info(f"     ✓ 已删除 {deleted_count} 个测试键")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Redis性能测试失败: {str(e)}")
        return False


def test_redis_region_cache(redis_client) -> bool:
    """测试区域数据缓存功能（模拟实际使用场景）"""
    logger.info("-" * 60)
    logger.info("测试：区域数据缓存功能")
    logger.info("-" * 60)
    
    try:
        # 模拟区域数据
        test_region_data = [
            {
                'id': 1001,
                'parent_id': 0,
                'region_name': '测试省份',
                'region_type': 1001
            },
            {
                'id': 1002,
                'parent_id': 1001,
                'region_name': '测试城市',
                'region_type': 1002
            }
        ]
        
        import json
        cache_key = "region:type:1001"
        cache_value = json.dumps(test_region_data, ensure_ascii=False)
        
        # 写入缓存
        logger.info(f"  1. 写入区域数据缓存: {cache_key}")
        result = redis_client.setex(
            cache_key,
            3600,  # 1小时过期
            cache_value.encode('utf-8')
        )
        if result:
            logger.info("     ✓ 缓存写入成功")
        else:
            logger.error("     ✗ 缓存写入失败")
            return False
        
        # 读取缓存
        logger.info(f"  2. 读取区域数据缓存: {cache_key}")
        result = redis_client.get(cache_key)
        if result:
            decoded_value = result.decode('utf-8') if isinstance(result, bytes) else result
            cached_data = json.loads(decoded_value)
            logger.info(f"     ✓ 缓存读取成功，数据条数: {len(cached_data)}")
            logger.info(f"     ✓ 第一条数据: {cached_data[0].get('region_name', 'N/A')}")
        else:
            logger.error("     ✗ 缓存读取失败")
            return False
        
        # 删除缓存
        logger.info(f"  3. 删除区域数据缓存: {cache_key}")
        result = redis_client.delete(cache_key)
        if result:
            logger.info("     ✓ 缓存删除成功")
        else:
            logger.warning("     ⚠ 缓存删除返回0")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 区域数据缓存测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("Redis连接测试脚本")
    logger.info("=" * 60)
    logger.info("")
    
    # 测试1: 检查Redis库
    redis_module = test_redis_import()
    if not redis_module:
        logger.error("测试终止：Redis库未安装")
        return False
    
    logger.info("")
    
    # 测试2: 测试连接
    redis_client = test_redis_connection(redis_module)
    if not redis_client:
        logger.error("")
        logger.error("=" * 60)
        logger.error("测试终止：无法连接到Redis服务器")
        logger.error("=" * 60)
        return False
    
    logger.info("")
    
    # 测试3: 获取服务器信息
    test_redis_info(redis_client)
    logger.info("")
    
    # 测试4: 基本操作
    basic_ops_success = test_redis_basic_operations(redis_client)
    logger.info("")
    
    # 测试5: 性能测试
    performance_success = test_redis_performance(redis_client, iterations=50)
    logger.info("")
    
    # 测试6: 区域缓存功能
    cache_success = test_redis_region_cache(redis_client)
    logger.info("")
    
    # 测试总结
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"  Redis连接: ✓ 成功")
    logger.info(f"  服务器信息: ✓ 成功")
    logger.info(f"  基本操作: {'✓ 成功' if basic_ops_success else '✗ 失败'}")
    logger.info(f"  性能测试: {'✓ 成功' if performance_success else '✗ 失败'}")
    logger.info(f"  区域缓存: {'✓ 成功' if cache_success else '✗ 失败'}")
    
    all_success = basic_ops_success and performance_success and cache_success
    if all_success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 所有测试通过！Redis连接正常，功能可用。")
        logger.info("=" * 60)
        return True
    else:
        logger.info("")
        logger.info("=" * 60)
        logger.warning("⚠ 部分测试失败，请检查Redis配置和服务器状态。")
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生未预期的错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

