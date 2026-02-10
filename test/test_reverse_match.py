"""
测试反向匹配逻辑
测试 region_name in field_value 的匹配情况
"""
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv
import os

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
    print(f"已加载环境配置文件: {env_file}")
else:
    print(f"警告: 环境配置文件不存在: {env_file}")

from src.database import DatabaseConnection

def test_reverse_match():
    """测试反向匹配逻辑"""
    print("=" * 60)
    print("测试反向匹配逻辑")
    print("=" * 60)
    
    field_value = "6409兵工厂3栋313"
    region_name = "6409兵工厂"
    
    print(f"\n测试值:")
    print(f"  field_value = '{field_value}'")
    print(f"  region_name = '{region_name}'")
    
    print(f"\n原始值检查 (repr):")
    print(f"  repr(region_name) = {repr(region_name)}")
    print(f"  repr(field_value) = {repr(field_value)}")
    
    # 测试 strip 后的匹配
    region_name_stripped = region_name.strip()
    field_value_stripped = field_value.strip()
    
    print(f"\nstrip() 后:")
    print(f"  repr(region_name.strip()) = {repr(region_name_stripped)}")
    print(f"  repr(field_value.strip()) = {repr(field_value_stripped)}")
    
    # 测试匹配
    print(f"\n匹配测试:")
    result_before_strip = region_name in field_value
    result_after_strip = region_name_stripped in field_value_stripped
    
    print(f"  region_name in field_value (strip前) = {result_before_strip}")
    print(f"  region_name.strip() in field_value.strip() = {result_after_strip}")
    
    if result_after_strip:
        print(f"\n✓ 匹配成功！")
    else:
        print(f"\n✗ 匹配失败！")
    
    # 从数据库查询实际的region_name
    print(f"\n" + "=" * 60)
    print("从数据库查询实际的region_name")
    print("=" * 60)
    
    try:
        db = DatabaseConnection()
        table_name = os.getenv('MYSQL_REGION_TABLE', 'regional_info')
        region_type = 1004
        
        # 查询region_name包含"6409兵工厂"的记录
        sql = f"""
            SELECT id, parent_id, region_name, region_type
            FROM {table_name}
            WHERE region_type = %s 
              AND region_name LIKE %s
              AND is_deleted = 0
            LIMIT 10
        """
        like_pattern = "%6409兵工厂%"
        
        with db.get_cursor() as cursor:
            cursor.execute(sql, (region_type, like_pattern))
            results = cursor.fetchall()
        
        print(f"\n数据库查询 (region_name LIKE '%6409兵工厂%'):")
        print(f"找到 {len(results)} 条记录")
        
        for idx, record in enumerate(results, 1):
            db_region_name = record.get('region_name', '')
            db_region_name_stripped = db_region_name.strip()
            
            print(f"\n记录 {idx}:")
            print(f"  id = {record.get('id')}")
            print(f"  region_name = '{db_region_name}'")
            print(f"  repr(region_name) = {repr(db_region_name)}")
            print(f"  region_name.strip() = '{db_region_name_stripped}'")
            print(f"  repr(region_name.strip()) = {repr(db_region_name_stripped)}")
            print(f"  len(region_name) = {len(db_region_name)}")
            print(f"  len(region_name.strip()) = {len(db_region_name_stripped)}")
            
            # 测试匹配
            match_result = db_region_name_stripped in field_value_stripped
            print(f"  region_name.strip() in field_value.strip() = {match_result}")
            
            if match_result:
                print(f"  ✓ 匹配成功！")
            else:
                print(f"  ✗ 匹配失败！")
            
            # 详细比较
            if db_region_name_stripped == "6409兵工厂":
                print(f"  → 这是目标记录 '6409兵工厂'")
                if not match_result:
                    print(f"  → 但匹配失败了，需要进一步检查")
                    
                    # 检查字符编码
                    print(f"  → 字符编码检查:")
                    for i, char in enumerate(db_region_name_stripped):
                        print(f"    [{i}] '{char}' (U+{ord(char):04X})")
                    print(f"  → field_value中的对应部分:")
                    start_idx = field_value_stripped.find(db_region_name_stripped[:3])
                    if start_idx >= 0:
                        for i in range(start_idx, min(start_idx + len(db_region_name_stripped), len(field_value_stripped))):
                            print(f"    [{i}] '{field_value_stripped[i]}' (U+{ord(field_value_stripped[i]):04X})")
    
    except Exception as e:
        print(f"\n数据库查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reverse_match()

