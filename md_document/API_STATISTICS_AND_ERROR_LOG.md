# API使用统计与错误日志系统说明文档

## 概述

本文档说明地址提取接口（`/api/extract`）的两个统计功能模块：

1. **API使用频次统计**：使用Redis实时计数，定时任务同步到MySQL
2. **接口失败事件日志**：直接写入MySQL，记录完整的失败请求与响应上下文

两个功能完全解耦，互不影响。

---

## 一、API使用频次统计

### 1.1 功能说明

对地址提取接口（`/api/extract`）进行使用频次统计，实时记录API调用次数，并通过定时任务将统计数据持久化到MySQL数据库。

### 1.2 架构设计

```
API接口调用 → Redis计数器（实时计数） → 定时任务（每天同步） → MySQL统计表（持久化存储）
```

**数据流程**：
1. 每次API调用时，使用Redis的`INCR`命令增加计数
2. 定时任务（默认每小时执行一次）扫描昨天的Redis Key
3. 将统计数据写入MySQL（UPSERT操作，幂等性保证）
4. 删除/过期已同步的Redis Key

**设计特点**：
- API层只负责写Redis，不直接操作MySQL，保证接口性能
- 定时任务独立运行，不阻塞接口调用
- 使用Redis分布式锁防止重复执行
- MySQL存储使用UPSERT，支持幂等操作

### 1.3 配置说明

**环境配置文件自动加载**：

系统支持自动环境配置加载功能，会根据服务器IP地址自动匹配并加载对应的环境配置文件（`dev.env`、`show.env`、`prod.env`）。匹配优先级：prod > show > dev。

更多详细信息请参考：[README.md](../README.md) 中的"自动环境配置加载"章节。

在对应的环境配置文件中（`dev.env`、`prod.env`、`show.env`）添加以下配置项：

```bash
# MySQL统计数据库配置（用于API使用统计和错误日志，独立于地址补全功能的数据库）
MYSQL_STATS_HOST=localhost
MYSQL_STATS_PORT=3306
MYSQL_STATS_USER=root
MYSQL_STATS_PASSWORD=your_password_here
MYSQL_STATS_DATABASE=api_statistics
MYSQL_STATS_CHARSET=utf8mb4
MYSQL_STATS_MAX_CONNECTIONS=10
MYSQL_STATS_CONNECT_TIMEOUT=10

# API使用统计配置
# 使用统计表名
MYSQL_API_USAGE_TABLE=extract_api_usage
# 错误日志表名（见下方说明）
MYSQL_API_ERROR_LOG_TABLE=extract_api_error_log
# 同步间隔（单位：秒，默认3600，即1小时）
API_USAGE_SYNC_INTERVAL=3600
# 同步日期偏移（默认1，即同步昨天的数据）
API_USAGE_SYNC_DAY_OFFSET=1
```

**重要说明**：
- 统计数据库使用独立的配置项（`MYSQL_STATS_*`），与地址补全数据库（`MYSQL_*`）完全分离
- 如果未配置`MYSQL_STATS_*`配置项，系统会自动使用`MYSQL_*`配置项作为回退（向后兼容）
- 建议在生产环境中使用独立的统计数据库，以确保数据隔离和性能优化

### 1.4 表结构设计

**表名**：`extract_api_usage`（可通过`MYSQL_API_USAGE_TABLE`配置）

**表结构**：
```sql
CREATE TABLE extract_api_usage (
    stat_date DATE NOT NULL,
    api_name VARCHAR(255) NOT NULL,
    call_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (stat_date, api_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='地址提取接口使用统计';
```

**字段说明**：
- `stat_date`：统计日期（DATE类型）
- `api_name`：API名称（例如：`/api/extract`）
- `call_count`：调用次数（INT类型，默认0）

**索引**：主键为`(stat_date, api_name)`，支持快速查询和UPSERT操作

### 1.5 Redis Key设计

**计数Key格式**：`api:count:{api_name}:{yyyyMMdd}`

**示例**：
- `api:count:/api/extract:20260111` - 2026年1月11日的`/api/extract`接口调用计数

**分布式锁Key格式**：`lock:api_usage_daily:{yyyyMMdd}`

**示例**：
- `lock:api_usage_daily:20260111` - 2026年1月11日数据同步的分布式锁

### 1.6 定时任务说明

**执行频率**：默认每小时执行一次（可通过`API_USAGE_SYNC_INTERVAL`配置）

**执行逻辑**：
1. 获取分布式锁（防止多实例重复执行）
2. 扫描昨天的Redis Key（`api:count:*:{yesterday}`）
3. 批量获取计数数据
4. 执行UPSERT SQL，写入MySQL（幂等操作）
5. 删除已同步的Redis Key
6. 释放分布式锁

**UPSERT SQL示例**：
```sql
INSERT INTO extract_api_usage (stat_date, api_name, call_count)
VALUES (?, ?, ?)
ON DUPLICATE KEY UPDATE
    call_count = call_count + VALUES(call_count);
```

**注意事项**：
- 使用分布式锁保证同一时间只有一个实例在执行同步
- UPSERT操作保证幂等性，支持重复执行
- 删除Redis Key避免数据重复同步

---

## 二、接口失败事件日志

### 2.1 功能说明

当接口调用失败时，记录一次完整的失败请求与响应上下文，用于追溯、排查、审计或分析。

**触发条件**：当接口返回的`Success=False`或`ResultCode != "100"`时记录错误日志

### 2.2 架构设计

```
API接口调用失败 → 直接写入MySQL（Append-only） → 错误日志表
```

**设计特点**：
- 直接写入MySQL，不需要Redis
- Append-only设计，避免并发冲突
- 与API使用频次统计完全解耦
- 异步写入，不影响接口响应性能

### 2.3 配置说明

错误日志功能使用独立的统计数据库（`MYSQL_STATS_*`配置），详见1.3节配置说明。

**环境配置文件自动加载**：

系统支持自动环境配置加载功能，会根据服务器IP地址自动匹配并加载对应的环境配置文件。更多详细信息请参考：[README.md](../README.md) 中的"自动环境配置加载"章节。

在对应的环境配置文件中需要配置：

```bash
# MySQL统计数据库配置（见1.3节）
MYSQL_STATS_HOST=localhost
MYSQL_STATS_PORT=3306
MYSQL_STATS_USER=root
MYSQL_STATS_PASSWORD=your_password_here
MYSQL_STATS_DATABASE=api_statistics
# ... 其他配置

# 错误日志表名
MYSQL_API_ERROR_LOG_TABLE=extract_api_error_log
```

### 2.4 表结构设计

**表名**：`extract_api_error_log`（可通过`MYSQL_API_ERROR_LOG_TABLE`配置）

**表结构**：
```sql
CREATE TABLE extract_api_error_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) DEFAULT NULL,
    user_name VARCHAR(255) DEFAULT NULL,
    model_type VARCHAR(255) DEFAULT 'mgeo_geographic_composition_analysis_chinese_base',
    content TEXT,
    extract_data JSON,
    result_code VARCHAR(10) DEFAULT NULL,
    reason TEXT DEFAULT NULL,
    warning JSON,
    time DATETIME NOT NULL,
    INDEX idx_time (time),
    INDEX idx_model_type (model_type),
    INDEX idx_result_code (result_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='地址提取接口失败事件日志';
```

**字段说明**：
- `id`：主键（BIGINT，自增）
- `user_id`：用户ID（VARCHAR(255)，默认NULL，当前未使用）
- `user_name`：用户名（VARCHAR(255)，默认NULL，当前未使用）
- `model_type`：模型类型（VARCHAR(255)，默认`mgeo_geographic_composition_analysis_chinese_base`）
- `content`：请求的文本内容（TEXT类型，存储原始请求文本）
- `extract_data`：提取的数据（JSON类型，存储接口返回的Data字段，字段顺序与接口返回格式一致）
- `result_code`：结果状态码（VARCHAR(10)，对应接口返回的ResultCode字段）
- `reason`：原因说明（TEXT类型，对应接口返回的Reason字段）
- `warning`：警告信息列表（JSON类型，存储Warning字段，元素为字符串）
- `time`：失败时间（DATETIME类型，NOT NULL）

**字段顺序说明**：
- `extract_data` 字段的JSON数据中，字段顺序与接口返回的 `Data` 字段顺序完全一致：
  1. `ProvinceName`（省份信息）
  2. `CityName`（城市信息）
  3. `ExpAreaName`（区/县信息）
  4. `StreetName`（街道/镇信息）
  5. `AreasInfo`（区域信息）
  6. `Address`（详细地址）
  7. `others`（其他信息）
  8. `Mobile`（手机号码）
  9. `Name`（姓名）

**索引**：
- 主键索引：`id`
- 时间索引：`idx_time (time)` - 用于按时间查询
- 模型类型索引：`idx_model_type (model_type)` - 用于按模型类型查询
- 状态码索引：`idx_result_code (result_code)` - 用于按状态码查询

### 2.5 数据示例

**示例记录**：
```json
{
    "id": 1,
    "user_id": null,
    "user_name": null,
    "model_type": "mgeo_geographic_composition_analysis_chinese_base",
    "content": "广东省深圳市龙岗区坂田街道",
    "extract_data": {
        "ProvinceName": {
            "id": 1000,
            "parent_id": null,
            "region_name": "广东省",
            "region_type": 1001
        },
        "CityName": {
            "id": 440300,
            "parent_id": 1000,
            "region_name": "深圳市",
            "region_type": 1002
        },
        "ExpAreaName": {},
        "StreetName": {},
        "AreasInfo": "",
        "Address": "",
        "others": "",
        "Mobile": "",
        "Name": ""
    },
    "result_code": "102",
    "reason": "地址信息无法完全确定",
    "warning": ["地址信息不完整"],
    "time": "2026-01-11 10:30:00"
}
```

**说明**：
- `extract_data` 字段存储完整的接口返回 `Data` 数据，字段顺序与接口返回格式一致
- `result_code` 和 `reason` 字段单独存储，便于查询和统计
- 字段顺序：ProvinceName → CityName → ExpAreaName → StreetName → AreasInfo → Address → others → Mobile → Name

---

## 三、使用说明

### 3.1 表自动创建

系统启动时会自动检查并创建统计表和错误日志表。如果表已存在，则跳过创建；如果表不存在，则自动创建。

**初始化位置**：`app.py`启动时执行

```python
# 初始化统计数据库连接（独立的数据库）
stats_db_connection = StatisticsDatabaseConnection()

# 初始化统计表（检查并创建）
if stats_db_connection:
    stats_db_connection.init_statistics_tables()
```

**说明**：使用独立的统计数据库连接（`StatisticsDatabaseConnection`），与地址补全数据库（`DatabaseConnection`）完全分离。

### 3.2 定时任务启动

定时任务在应用启动时自动启动（使用FastAPI的`startup`事件）。

**启动位置**：`app.py`的`startup_event`函数

```python
@app.on_event("startup")
async def startup_event():
    if sync_task and sync_task.enabled:
        asyncio.create_task(sync_task.run_periodic())
```

### 3.3 查询统计信息

**查询指定日期的API调用次数**：
```sql
SELECT stat_date, api_name, call_count
FROM extract_api_usage
WHERE stat_date = '2026-01-11'
  AND api_name = '/api/extract';
```

**查询最近7天的统计信息**：
```sql
SELECT stat_date, api_name, call_count
FROM extract_api_usage
WHERE stat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY stat_date DESC, api_name;
```

### 3.4 查询错误日志

**查询指定时间段的错误日志**：
```sql
SELECT id, model_type, content, extract_data, result_code, reason, warning, time
FROM extract_api_error_log
WHERE time >= '2026-01-11 00:00:00'
  AND time < '2026-01-12 00:00:00'
ORDER BY time DESC;
```

**查询指定模型类型的错误日志**：
```sql
SELECT id, model_type, content, extract_data, result_code, reason, warning, time
FROM extract_api_error_log
WHERE model_type = 'mgeo_geographic_composition_analysis_chinese_base'
ORDER BY time DESC
LIMIT 100;
```

**查询指定状态码的错误日志**：
```sql
SELECT id, model_type, content, result_code, reason, warning, time
FROM extract_api_error_log
WHERE result_code = '102'
ORDER BY time DESC
LIMIT 100;
```

**按状态码统计错误数量**：
```sql
SELECT result_code, COUNT(*) as error_count
FROM extract_api_error_log
WHERE time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY result_code
ORDER BY error_count DESC;
```

---

## 四、技术要点

### 4.1 幂等性

- **UPSERT操作**：使用`ON DUPLICATE KEY UPDATE`确保幂等性
- **分布式锁**：使用Redis SET NX EX实现分布式锁，防止重复执行
- **支持重复执行**：定时任务支持重复执行，不会导致数据重复或错误

### 4.2 性能优化

- **Redis实时计数**：使用INCR命令，性能高，不阻塞接口
- **批量同步**：定时任务批量处理数据，减少数据库操作
- **异步写入**：错误日志写入不影响接口响应时间

### 4.3 异常处理

- **Redis不可用**：统计功能自动禁用，不影响接口功能
- **MySQL不可用**：错误日志记录失败不影响接口响应
- **定时任务失败**：记录错误日志，下次继续执行

### 4.4 解耦设计

- **使用统计和错误日志完全独立**：两个功能互不影响
- **配置化设计**：表名、同步间隔等均可配置
- **模块化实现**：各个模块职责清晰，易于维护

---

## 五、注意事项

1. **Redis连接**：确保Redis服务正常运行，否则统计功能将不可用
2. **MySQL连接**：确保MySQL服务正常运行，否则表创建和错误日志记录将失败
3. **时区设置**：确保应用服务器和数据库服务器的时区设置一致
4. **数据清理**：建议定期清理过期的错误日志数据（根据业务需求）
5. **监控告警**：建议监控定时任务的执行状态，确保数据正常同步

---

## 六、相关文件

- **配置文件**：`dev.env`、`prod.env`、`show.env`、`.env_template`
- **地址补全数据库连接**：`src/database/db_connection.py`
- **统计数据库连接**：`src/database/statistics_db_connection.py`（独立数据库）
- **Redis计数器**：`src/database/api_usage_counter.py`
- **错误日志记录**：`src/database/api_error_logger.py`
- **定时任务**：`src/tasks/api_usage_sync.py`
- **接口集成**：`src/api/routes/extract.py`
- **应用启动**：`app.py`

**数据库分离说明**：
- 地址补全功能使用`DatabaseConnection`（`MYSQL_*`配置）
- API统计功能使用`StatisticsDatabaseConnection`（`MYSQL_STATS_*`配置）
- 两个数据库完全独立，互不影响

