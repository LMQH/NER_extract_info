"""
Redis性能测试脚本
测试/api/extract接口在有redis和无redis情况下的处理时间差异
"""
import os
import sys
import time
import logging
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv

# ==================== 配置区域 ====================
# 测试数据配置（可在此处修改测试数据）
TEST_CONTENT = "广东南山街道南山村 A座 陈华 15812345678"
TEST_MODEL = "mgeo_geographic_composition_analysis_chinese_base"

# 推荐阈值配置
RECOMMENDED_THRESHOLD = 20.0  # 20%的性能提升阈值
# ==================================================

# 根据ENV_TYPE加载对应的环境配置文件
env_type = os.getenv('ENV_TYPE', 'dev_env')
if env_type == 'dev_env':
    env_file = 'dev.env'
elif env_type == 'show_env':
    env_file = 'show.env'
elif env_type == 'prod_env':
    env_file = 'prod.env'
else:
    env_file = 'dev.env'

env_path = os.path.join(project_root, env_file)
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ 已加载环境配置文件: {env_file}")
else:
    print(f"⚠ 警告: 环境配置文件不存在: {env_file}")

# 导入项目模块
from src.database import DatabaseConnection, RegionCache
from src.model_manager import ModelManager
from src.processor_mgeo import AddressCompleter
from src.processor_mgeo.converters import convert_mgeo_to_output_format
from src.processor_mgeo.input_validator import InputValidator
from src.api.schemas import ExtractResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("REDIS_PERFORMANCE_TEST")

# EBusinessID配置
EBusinessID = os.getenv("EBUSINESS_ID", "2223333")


def execute_extract_logic(
    content: str,
    model_name: str,
    model_manager: ModelManager,
    address_completer: AddressCompleter
) -> Dict[str, Any]:
    """
    执行实体抽取的核心逻辑（模拟/api/extract接口）
    
    Args:
        content: 待处理的文本内容
        model_name: 模型名称
        model_manager: 模型管理器
        address_completer: 地址补全器
    
    Returns:
        提取结果字典
    """
    # 验证输入
    if not content or not content.strip():
        return ExtractResponse(
            EBusinessID=EBusinessID,
            Data={},
            Success=False,
            Reason="Content字段不能为空",
            ResultCode="101",
            Warning=[]
        ).dict()
    
    # 验证模型名称
    if model_name not in model_manager.SUPPORTED_MODELS:
        return ExtractResponse(
            EBusinessID=EBusinessID,
            Data={},
            Success=False,
            Reason=f"不支持的模型: {model_name}",
            ResultCode="101",
            Warning=[]
        ).dict()
    
    # 加载模型
    try:
        model = model_manager.load_model(model_name)
    except Exception as e:
        return ExtractResponse(
            EBusinessID=EBusinessID,
            Data={},
            Success=False,
            Reason=f"模型加载失败: {str(e)}",
            ResultCode="102",
            Warning=[]
        ).dict()
    
    # 执行实体抽取
    try:
        result = model.extract_entities(content)
        
        # 格式转换
        if model_name == 'qwen-flash':
            formatted_result = result
        elif model_name == 'mgeo_geographic_composition_analysis_chinese_base':
            formatted_result = convert_mgeo_to_output_format(result, content)
        else:
            formatted_result = result
        
        # 数据校验和清洗
        formatted_result = InputValidator.validate_extract_response(formatted_result)
        
        # 检查模型返回的结果
        if not formatted_result.get('Success', True):
            return formatted_result
        
        # 进行地址补全
        if address_completer:
            try:
                formatted_result = address_completer.complete_extract_response(formatted_result)
            except Exception as e:
                logger.warning(f"地址补全失败: {str(e)}")
                current_code = formatted_result.get('ResultCode', '102')
                if current_code != '101':
                    formatted_result['ResultCode'] = '102'
                    formatted_result['Success'] = False
                    formatted_result['Reason'] = f'地址补全失败: {str(e)}'
        
        return formatted_result
        
    except Exception as e:
        return ExtractResponse(
            EBusinessID=EBusinessID,
            Data={},
            Success=False,
            Reason=f"实体抽取失败: {str(e)}",
            ResultCode="102",
            Warning=[]
        ).dict()


def run_single_test(
    content: str,
    model_name: str,
    model_manager: ModelManager,
    address_completer: AddressCompleter,
    use_redis: bool
) -> float:
    """
    执行单次测试并返回耗时
    
    Args:
        content: 测试内容
        model_name: 模型名称
        model_manager: 模型管理器
        address_completer: 地址补全器
        use_redis: 是否使用redis
    
    Returns:
        耗时（秒）
    """
    # 控制redis启用/禁用
    original_enabled = address_completer.region_cache.enabled
    address_completer.region_cache.enabled = use_redis
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 执行提取逻辑
        result = execute_extract_logic(content, model_name, model_manager, address_completer)
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算耗时
        duration = end_time - start_time
        
        # 验证结果
        if not result.get('Success', False):
            logger.warning(f"测试返回失败: {result.get('Reason', '未知错误')}")
        
        return duration
        
    finally:
        # 恢复原始状态
        address_completer.region_cache.enabled = original_enabled


def main():
    """主测试函数"""
    print("=" * 80)
    print("Redis性能测试脚本")
    print("=" * 80)
    print(f"\n测试数据: {TEST_CONTENT}")
    print(f"测试模型: {TEST_MODEL}")
    print(f"推荐阈值: {RECOMMENDED_THRESHOLD}%")
    print("\n" + "=" * 80)
    
    # 初始化组件
    print("\n[1/4] 初始化数据库连接...")
    try:
        db_connection = DatabaseConnection()
        if db_connection.test_connection():
            print("✓ 数据库连接成功")
        else:
            print("✗ 数据库连接失败")
            return
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return
    
    print("\n[2/4] 初始化Redis连接...")
    try:
        region_cache = RegionCache()
        if region_cache.enabled:
            print("✓ Redis连接成功")
        else:
            print("⚠ Redis连接失败，将使用无redis模式进行对比测试")
    except Exception as e:
        print(f"⚠ Redis连接失败: {str(e)}")
        region_cache = RegionCache()
    
    print("\n[3/4] 加载模型...")
    try:
        model_manager = ModelManager(base_path=str(project_root))
        model = model_manager.load_model(TEST_MODEL)
        print(f"✓ 模型加载成功: {TEST_MODEL}")
    except Exception as e:
        print(f"✗ 模型加载失败: {str(e)}")
        return
    
    print("\n[4/4] 初始化地址补全器...")
    try:
        address_completer = AddressCompleter(db_connection)
        print("✓ 地址补全器初始化成功")
    except Exception as e:
        print(f"✗ 地址补全器初始化失败: {str(e)}")
        return
    
    print("\n" + "=" * 80)
    print("开始性能测试...")
    print("=" * 80)
    
    # 存储测试结果
    test_results = []
    
    # 第一次测试：清除缓存（模拟首次使用）
    print("\n【第一次测试】（缓存未加载）")
    print("-" * 80)
    
    # 清除redis缓存
    if region_cache.enabled:
        print("清除Redis缓存...")
        region_cache.clear_cache()
        print("✓ 缓存已清除")
    
    # 测试有redis
    print("\n测试1-1: 使用Redis...")
    duration_with_redis_1 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=True
    )
    print(f"  耗时: {duration_with_redis_1:.4f}秒 ({duration_with_redis_1*1000:.2f}毫秒)")
    
    # 测试无redis
    print("\n测试1-2: 不使用Redis...")
    duration_without_redis_1 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=False
    )
    print(f"  耗时: {duration_without_redis_1:.4f}秒 ({duration_without_redis_1*1000:.2f}毫秒)")
    
    # 计算提升
    improvement_1 = ((duration_without_redis_1 - duration_with_redis_1) / duration_without_redis_1 * 100) if duration_without_redis_1 > 0 else 0
    print(f"  性能提升: {improvement_1:.2f}%")
    
    test_results.append({
        'test_num': 1,
        'with_redis': duration_with_redis_1,
        'without_redis': duration_without_redis_1,
        'improvement': improvement_1
    })
    
    # 第二次测试：不清除缓存（缓存已加载）
    print("\n【第二次测试】（缓存已加载）")
    print("-" * 80)
    print("保持缓存状态（不清除）...")
    
    # 测试有redis
    print("\n测试2-1: 使用Redis...")
    duration_with_redis_2 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=True
    )
    print(f"  耗时: {duration_with_redis_2:.4f}秒 ({duration_with_redis_2*1000:.2f}毫秒)")
    
    # 测试无redis
    print("\n测试2-2: 不使用Redis...")
    duration_without_redis_2 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=False
    )
    print(f"  耗时: {duration_without_redis_2:.4f}秒 ({duration_without_redis_2*1000:.2f}毫秒)")
    
    # 计算提升
    improvement_2 = ((duration_without_redis_2 - duration_with_redis_2) / duration_without_redis_2 * 100) if duration_without_redis_2 > 0 else 0
    print(f"  性能提升: {improvement_2:.2f}%")
    
    test_results.append({
        'test_num': 2,
        'with_redis': duration_with_redis_2,
        'without_redis': duration_without_redis_2,
        'improvement': improvement_2
    })
    
    # 第三次测试：不清除缓存（缓存完全稳定）
    print("\n【第三次测试】（缓存完全稳定）")
    print("-" * 80)
    print("保持缓存状态（不清除）...")
    
    # 测试有redis
    print("\n测试3-1: 使用Redis...")
    duration_with_redis_3 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=True
    )
    print(f"  耗时: {duration_with_redis_3:.4f}秒 ({duration_with_redis_3*1000:.2f}毫秒)")
    
    # 测试无redis
    print("\n测试3-2: 不使用Redis...")
    duration_without_redis_3 = run_single_test(
        TEST_CONTENT, TEST_MODEL, model_manager, address_completer, use_redis=False
    )
    print(f"  耗时: {duration_without_redis_3:.4f}秒 ({duration_without_redis_3*1000:.2f}毫秒)")
    
    # 计算提升
    improvement_3 = ((duration_without_redis_3 - duration_with_redis_3) / duration_without_redis_3 * 100) if duration_without_redis_3 > 0 else 0
    print(f"  性能提升: {improvement_3:.2f}%")
    
    test_results.append({
        'test_num': 3,
        'with_redis': duration_with_redis_3,
        'without_redis': duration_without_redis_3,
        'improvement': improvement_3
    })
    
    # 计算平均提升
    avg_improvement = (improvement_1 + improvement_2 + improvement_3) / 3
    
    # 输出测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    print("\n第一次测试结果：")
    print(f"  使用redis总耗时：{duration_with_redis_1:.4f}秒（{duration_with_redis_1*1000:.2f}毫秒）")
    print(f"  不使用redis总耗时：{duration_without_redis_1:.4f}秒（{duration_without_redis_1*1000:.2f}毫秒）")
    print(f"  性能提升：{improvement_1:.2f}%")
    
    print("\n第二次测试结果：")
    print(f"  使用redis总耗时：{duration_with_redis_2:.4f}秒（{duration_with_redis_2*1000:.2f}毫秒）")
    print(f"  不使用redis总耗时：{duration_without_redis_2:.4f}秒（{duration_without_redis_2*1000:.2f}毫秒）")
    print(f"  性能提升：{improvement_2:.2f}%")
    
    print("\n第三次测试结果：")
    print(f"  使用redis总耗时：{duration_with_redis_3:.4f}秒（{duration_with_redis_3*1000:.2f}毫秒）")
    print(f"  不使用redis总耗时：{duration_without_redis_3:.4f}秒（{duration_without_redis_3*1000:.2f}毫秒）")
    print(f"  性能提升：{improvement_3:.2f}%")
    
    print("\n" + "=" * 80)
    print("总结：")
    print("=" * 80)
    print(f"  平均性能提升：{avg_improvement:.2f}%")
    print(f"  推荐阈值：{RECOMMENDED_THRESHOLD:.2f}%")
    
    if avg_improvement >= RECOMMENDED_THRESHOLD:
        print(f"  建议：使用redis的提升是{avg_improvement:.2f}%，高于推荐阈值{RECOMMENDED_THRESHOLD:.2f}%，建议启用。")
    else:
        print(f"  建议：使用redis的提升是{avg_improvement:.2f}%，低于推荐阈值{RECOMMENDED_THRESHOLD:.2f}%，建议评估是否需要启用。")
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

