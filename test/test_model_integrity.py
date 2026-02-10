"""
检查模型文件完整性
验证mgeo_geographic_composition_analysis_chinese_base模型所需的所有文件是否存在
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def is_modelscope_cache_structure(path):
    """判断路径是否是ModelScope缓存目录结构（包含hub/damo/等）"""
    path = Path(path)
    # ModelScope缓存目录结构通常包含: hub/damo/模型名/revisions/master/
    if (path / "damo").exists() or (path.name == "hub"):
        return True
    # 检查父目录
    if path.parent.name == "hub" and (path.parent.parent / "modelscope").exists():
        return True
    return False

def get_modelscope_cache_dir():
    """获取ModelScope缓存目录"""
    # 1. 检查环境变量 MODELSCOPE_CACHE
    cache_dir = os.getenv('MODELSCOPE_CACHE')
    if cache_dir:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            return cache_path, "环境变量 MODELSCOPE_CACHE"
    
    # 2. 检查项目配置的MODEL_PATH（仅当它是ModelScope缓存结构时）
    model_path = os.getenv('MODEL_PATH', 'model/')
    if model_path:
        model_path = model_path.strip()
        if model_path and not model_path.endswith('/') and not model_path.endswith('\\'):
            model_path = model_path + '/'
        cache_path = Path(model_path)
        if cache_path.is_absolute():
            if cache_path.exists() and is_modelscope_cache_structure(cache_path):
                return cache_path, "MODEL_PATH配置（ModelScope缓存目录）"
        else:
            project_cache = project_root / model_path
            if project_cache.exists() and is_modelscope_cache_structure(project_cache):
                return project_cache.resolve(), "MODEL_PATH配置（ModelScope缓存目录）"
    
    # 3. 检查默认缓存目录 (~/.cache/modelscope/hub 或 C:\Users\<user>\.cache\modelscope\hub)
    home = Path.home()
    if sys.platform == 'win32':
        default_cache = home / '.cache' / 'modelscope' / 'hub'
    else:
        # Linux/Mac 默认缓存目录
        default_cache = home / '.cache' / 'modelscope' / 'hub'
    
    if default_cache.exists():
        return default_cache, f"默认缓存目录 ({default_cache})"
    
    # 即使目录不存在，也返回路径信息（用于提示）
    return default_cache if default_cache.parent.exists() else None, None

def check_modelscope_cache(has_local_model=True):
    """
    检查ModelScope缓存目录中的模型文件
    
    Args:
        has_local_model: 本地模型文件是否完整（如果完整，缓存目录是可选的）
    """
    print("\n【ModelScope缓存目录检查】")
    print("-" * 70)
    
    cache_dir, source = get_modelscope_cache_dir()
    
    # 检查环境变量设置
    modelscope_cache_env = os.getenv('MODELSCOPE_CACHE')
    if modelscope_cache_env:
        print(f"[INFO] MODELSCOPE_CACHE环境变量: {modelscope_cache_env}")
    else:
        print(f"[INFO] MODELSCOPE_CACHE环境变量: 未设置（将使用默认缓存目录）")
    
    if not cache_dir:
        if has_local_model:
            print("[INFO] 未找到ModelScope缓存目录")
            print("       使用本地模型时，缓存目录是可选的（ModelScope会直接从本地路径加载）")
            print("       在Linux服务器上，如果使用模型ID，ModelScope会自动下载到默认缓存目录")
            return False
        else:
            print("[WARNING] 未找到ModelScope缓存目录")
            print("         如果本地模型不完整，可能需要从ModelScope下载模型")
            print("         在Linux服务器上，默认缓存目录为: ~/.cache/modelscope/hub")
            return False
    
    print(f"[INFO] 缓存目录: {cache_dir}")
    print(f"[INFO] 来源: {source}")
    
    if not cache_dir.exists():
        print(f"[WARNING] 缓存目录不存在: {cache_dir}")
        if has_local_model:
            print("         使用本地模型时，此警告可忽略")
        return False
    
    # ModelScope缓存目录结构: hub/damo/mgeo_geographic_composition_analysis_chinese_base/revisions/master/
    model_namespace = "damo"
    model_name = "mgeo_geographic_composition_analysis_chinese_base"
    revision = "master"
    
    cache_model_path = cache_dir / model_namespace / model_name / "revisions" / revision
    
    if cache_model_path.exists():
        print(f"[OK] 找到缓存模型: {cache_model_path}")
        
        # 检查缓存中的关键文件
        cache_files = {
            "config.json": "模型配置",
            "configuration.json": "ModelScope配置",
            "pytorch_model.bin": "模型权重",
            "vocab.txt": "词汇表"
        }
        
        print("\n  缓存文件检查:")
        cache_complete = True
        for filename, desc in cache_files.items():
            file_path = cache_model_path / filename
            if file_path.exists():
                size = file_path.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size / 1024:.2f} KB"
                print(f"    [OK] {filename:30s} ({size_str:>10s}) - {desc}")
            else:
                print(f"    [MISSING] {filename:30s} - {desc}")
                cache_complete = False
        
        if cache_complete:
            print("\n[INFO] 缓存模型文件完整，可以作为本地模型的备选")
        else:
            print("\n[WARNING] 缓存模型文件不完整")
        
        return cache_complete
    else:
        if has_local_model:
            print(f"[INFO] 缓存中未找到模型: {cache_model_path}")
            print(f"       使用本地模型时，这是正常的（ModelScope直接从本地路径加载）")
            print(f"       在Linux服务器上，如果本地模型完整，无需缓存目录")
        else:
            print(f"[WARNING] 缓存中未找到模型: {cache_model_path}")
            print(f"         如果本地模型不完整，可能需要:")
            print(f"         1. 设置MODELSCOPE_CACHE环境变量指向缓存目录")
            print(f"         2. 或让ModelScope自动下载到默认缓存目录 (~/.cache/modelscope/hub)")
        return False

def check_model_files():
    """检查模型文件完整性"""
    model_dir = project_root / "model" / "mgeo_geographic_composition_analysis_chinese_base"
    
    # 必需的文件列表
    required_files = {
        "config.json": "模型配置文件（BERT配置）",
        "configuration.json": "ModelScope配置文件（任务和标签映射）",
        "pytorch_model.bin": "模型权重文件（核心文件，约388MB）",
        "vocab.txt": "词汇表文件（用于tokenizer）",
        "README.md": "模型说明文档",
        "requirements.txt": "依赖要求文件"
    }
    
    # 可选文件
    optional_files = {
        ".gitattributes": "Git LFS配置文件（用于大文件管理）"
    }
    
    print("=" * 70)
    print("模型文件完整性检查")
    print("=" * 70)
    print(f"模型目录: {model_dir}")
    print()
    
    # 检查必需文件
    print("【必需文件检查】")
    print("-" * 70)
    all_required_exist = True
    missing_files = []
    
    for filename, description in required_files.items():
        file_path = model_dir / filename
        exists = file_path.exists()
        status = "[OK]" if exists else "[MISSING]"
        
        if exists:
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            if size_mb >= 1:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_kb = size / 1024
                size_str = f"{size_kb:.2f} KB"
            print(f"{status} {filename:30s} ({size_str:>10s}) - {description}")
        else:
            print(f"{status} {filename:30s} {'MISSING':>10s} - {description}")
            all_required_exist = False
            missing_files.append(filename)
    
    print()
    
    # 检查可选文件
    print("【可选文件检查】")
    print("-" * 70)
    for filename, description in optional_files.items():
        file_path = model_dir / filename
        exists = file_path.exists()
        status = "[OK]" if exists else "[OPTIONAL]"
        if exists:
            size = file_path.stat().st_size
            size_kb = size / 1024
            print(f"{status} {filename:30s} ({size_kb:.2f} KB) - {description}")
        else:
            print(f"{status} {filename:30s} {'可选':>10s} - {description}")
    
    # 检查ModelScope缓存目录（传入本地模型是否完整的状态）
    check_modelscope_cache(has_local_model=all_required_exist)
    
    print()
    print("=" * 70)
    
    # 总结
    if all_required_exist:
        print("[PASS] 所有必需文件都存在，模型文件完整！")
        
        # 验证关键文件内容
        print("\n【文件内容验证】")
        print("-" * 70)
        
        # 检查config.json
        try:
            import json
            config_path = model_dir / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"[OK] config.json 格式正确 (model_type: {config.get('model_type', 'N/A')})")
        except Exception as e:
            print(f"[ERROR] config.json 格式错误: {str(e)}")
        
        # 检查configuration.json
        try:
            config_path = model_dir / "configuration.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            task = config.get('task', 'N/A')
            print(f"[OK] configuration.json 格式正确 (task: {task})")
        except Exception as e:
            print(f"[ERROR] configuration.json 格式错误: {str(e)}")
        
        # 检查vocab.txt
        try:
            vocab_path = model_dir / "vocab.txt"
            with open(vocab_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"[OK] vocab.txt 格式正确 (词汇数量: {len(lines)})")
        except Exception as e:
            print(f"[ERROR] vocab.txt 格式错误: {str(e)}")
        
        # 检查pytorch_model.bin大小
        model_bin_path = model_dir / "pytorch_model.bin"
        if model_bin_path.exists():
            size_mb = model_bin_path.stat().st_size / (1024 * 1024)
            if size_mb < 100:
                print(f"[WARNING] pytorch_model.bin 文件较小 ({size_mb:.2f} MB)，可能不完整")
            else:
                print(f"[OK] pytorch_model.bin 文件大小正常 ({size_mb:.2f} MB)")
        
        return True
    else:
        print(f"[FAIL] 缺少必需文件: {', '.join(missing_files)}")
        print("\n请重新下载模型文件。")
        return False

if __name__ == "__main__":
    try:
        success = check_model_files()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
