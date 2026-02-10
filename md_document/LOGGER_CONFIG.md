# 日志配置说明

本文档说明如何配置和使用项目的日志系统。

## 概述

项目使用统一的日志管理系统，支持通过环境变量配置日志级别，实现灵活的日志输出控制。

## 日志级别

支持以下日志级别（从低到高）：

- **DEBUG**：记录所有详细信息，包括调试信息
- **INFO**：记录一般信息（默认级别）
- **WARNING**：记录警告和错误信息
- **ERROR**：记录错误和严重错误
- **CRITICAL**：只记录严重错误

## 配置方法

### 1. 环境变量配置

在环境配置文件中设置 `LOG_LEVEL` 变量：

```bash
# 在 .env、dev.env、show.env 或 prod.env 中设置
LOG_LEVEL=INFO
```

### 2. 配置示例

**开发环境配置** (dev.env)：
```bash
# 记录所有详细信息，方便调试
LOG_LEVEL=DEBUG
```

**生产环境配置** (prod.env)：
```bash
# 只记录重要信息，减少日志量
LOG_LEVEL=INFO
```

**高负载环境**：
```bash
# 只记录警告和错误
LOG_LEVEL=WARNING
```

## 日志输出

### 控制台输出

- 控制台输出级别由 `LOG_LEVEL` 环境变量控制
- 默认显示 INFO 级别及以上的日志
- 可以通过设置 `LOG_LEVEL` 动态调整

### 文件记录

- 文件记录所有级别的日志（包括 DEBUG）
- 日志文件位置：`logs/inference_YYYYMMDD.log`
- 按日期自动轮转
- 自动清理超过30天的旧日志文件

## 使用方法

### 在代码中使用

```python
from src.utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")      # 开发和调试时使用
logger.info("一般信息")       # 记录重要的业务流程
logger.warning("警告信息")     # 记录需要注意的问题
logger.error("错误信息")      # 记录错误信息
logger.critical("严重错误")   # 记录严重错误
```

### 动态设置日志级别

```python
from src.utils.logger import set_log_level

# 动态设置日志级别
set_log_level('DEBUG')  # 设置为DEBUG级别
```

## 日志格式

日志输出格式为：

```
YYYY-MM-DD HH:MM:SS - 日志记录器名称 - 级别 - 消息内容
```

示例：

```
2026-01-13 14:20:25 - NER_API - INFO - 模型加载成功
2026-01-13 14:20:26 - models.mgeo_geographic_composition_analysis_chinese_base_model - DEBUG - transformers版本: 4.20.1
2026-01-13 14:20:27 - models.mgeo_geographic_composition_analysis_chinese_base_model - WARNING - MGeo模型可能需要transformers 4.20.x或更早版本
```

## 模块中的日志级别使用规范

### DEBUG 级别
- 详细的调试信息
- 版本检查信息
- 路径信息
- 详细的堆栈跟踪

### INFO 级别
- 模型加载成功/失败
- API调用成功/失败
- 数据库连接状态
- 重要的业务流程

### WARNING 级别
- 版本兼容性警告
- 降级处理信息
- 可能的问题提示

### ERROR 级别
- 模型加载失败
- API调用失败
- 数据库连接失败
- 处理过程中的错误

### CRITICAL 级别
- 严重的服务错误
- 导致服务不可用的错误

## 注意事项

1. **日志级别设置**：日志级别会同时影响控制台输出，但文件始终记录所有级别
2. **性能影响**：DEBUG级别会产生大量日志，在高负载环境下建议使用 INFO 或 WARNING
3. **敏感信息**：日志中会自动对敏感信息（如密码、API密钥）进行脱敏处理
4. **日志文件管理**：系统会自动清理超过30天的旧日志文件，不需要手动管理

## 示例代码

### 完整的使用示例

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MyModel:
    def __init__(self):
        logger.debug("开始初始化模型")
        try:
            # 模型初始化代码
            logger.info("模型初始化成功")
        except Exception as e:
            logger.error(f"模型初始化失败: {str(e)}")
            raise
    
    def process(self, text):
        logger.debug(f"开始处理文本: {text[:50]}...")
        try:
            # 处理逻辑
            logger.info(f"处理成功，文本长度: {len(text)}")
            return result
        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            return None
```

## 测试日志配置

运行测试脚本验证日志配置：

```bash
# 使用默认日志级别（INFO）
python test_logger.py

# 使用DEBUG日志级别
LOG_LEVEL=DEBUG python test_logger.py

# 使用WARNING日志级别
LOG_LEVEL=WARNING python test_logger.py
```

## 常见问题

### Q1: 如何查看DEBUG级别的日志？

A: 在环境配置文件中设置 `LOG_LEVEL=DEBUG`，然后重启服务。

### Q2: 为什么控制台看不到DEBUG日志？

A: 默认日志级别是 INFO，需要设置为 DEBUG 才能看到 DEBUG 级别的日志。文件日志会记录所有级别。

### Q3: 如何临时调整日志级别而不修改配置文件？

A: 可以使用 `set_log_level()` 函数在代码中动态设置，或者在启动时设置环境变量：

```bash
LOG_LEVEL=DEBUG python app.py
```

### Q4: 日志文件会无限增长吗？

A: 不会。系统会自动清理超过30天的旧日志文件。如果需要调整保留天数，可以修改 `app.py` 中的 `cleanup_old_logs()` 函数调用参数。

## 相关文件

- `src/utils/logger.py` - 日志管理模块
- `.env`, `dev.env`, `show.env`, `prod.env` - 环境配置文件
- `app.py` - 日志系统初始化
- `logs/` - 日志文件目录
