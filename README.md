# NER Demo API

基于MGeo模型的中文命名实体识别（NER）和信息抽取API服务，适用于地址解析、实体抽取等多种场景。

## 功能特性

- ✅ **MGeo模型支持**：使用MGeo地理组成分析模型进行实体抽取
- ✅ **智能模型加载**：支持通过 `MODEL_EXISTS` 环境变量控制模型加载策略。当 `MODEL_EXISTS=true` 时，严格禁用 ModelScope 下载，只使用本地模型；当 `MODEL_EXISTS=false` 时，本地模型不存在时自动从 ModelScope 下载
- ✅ **地址信息提取与补全**：自动识别地址、人名、电话信息，支持地址纠错和补全
- ✅ **三阶段处理逻辑**：地址数据匹配、候选结果处理、数据校验三个阶段，支持双向模糊匹配和上下级关系处理
- ✅ **数据库地址补全**：基于MySQL数据库的区域信息进行地址数据补全和验证
- ✅ **Redis缓存优化**：缓存区域数据查询结果，大幅提升匹配性能
- ✅ **API使用统计**：实时统计API调用频次，使用Redis计数+MySQL持久化，定时任务自动同步
- ✅ **接口错误日志**：自动记录接口失败事件的完整上下文，用于追溯、排查、审计和分析
- ✅ **RESTful API服务**：基于FastAPI提供HTTP接口
- ✅ **自动API文档**：Swagger UI和ReDoc交互式文档
- ✅ **完善的日志记录**：自动记录推理时间、数据库匹配时间、模型信息、执行状态等
- ✅ **分级日志输出**：控制台输出INFO级别，文件记录所有级别（包括DEBUG）
- ✅ **细粒度状态码**：100/101/102/103/104状态码体系，精确反映处理结果
- ✅ **自动环境配置管理**：根据服务器IP地址自动匹配并加载对应的环境配置文件（prod.env/show.env/dev.env），支持多环境部署

## 技术栈

- **框架**：FastAPI
- **模型**：MGeo地理组成分析模型（mgeo_geographic_composition_analysis_chinese_base）
- **数据库**：MySQL（地址补全数据库 + 统计数据库，两个独立数据库）
- **缓存**：Redis（用于区域数据缓存和API使用统计，提升性能）
- **Python版本**：3.8+

## 项目结构

```
NER_demo/
├── app.py                      # FastAPI服务入口
├── src/                        # 源代码文件夹
│   ├── api/                    # API相关模块
│   │   ├── routes/             # 路由模块
│   │   │   ├── extract.py      # 实体抽取路由
│   │   │   ├── file.py         # 文件处理路由
│   │   │   └── system.py       # 系统路由
│   │   ├── schemas.py          # API数据模型
│   │   └── dependencies.py     # 依赖注入
│   ├── config/                 # 配置模块
│   │   ├── config_manager.py   # 配置管理器
│   │   ├── env_loader.py       # 环境变量加载器
│   │   ├── constants.py        # 常量定义
│   │   └── entity_mapping_loader.py  # 实体映射加载器
│   ├── database/               # 数据库模块
│   │   ├── db_connection.py    # 地址补全数据库连接
│   │   ├── statistics_db_connection.py  # 统计数据库连接
│   │   ├── api_usage_counter.py  # API使用统计Redis计数器
│   │   ├── api_error_logger.py  # 接口错误日志记录
│   │   └── redis_cache.py      # Redis缓存管理
│   ├── models/                 # 模型模块
│   │   ├── mgeo_geographic_composition_analysis_chinese_base_model.py
│   │   └── qwen_flash_model.py  # 已废弃，但保留代码
│   ├── processor_mgeo/          # MGeo处理模块（地址匹配处理核心）
│   │   ├── address_completer.py  # 地址补全协调器
│   │   ├── stage1_matcher.py     # 第一阶段：地址数据匹配
│   │   ├── stage2_resolver.py    # 第二阶段：候选结果处理
│   │   ├── stage3_validator.py   # 第三阶段：数据校验
│   │   ├── matcher.py            # 区域匹配器（双向模糊匹配）
│   │   ├── input_validator.py    # 输入数据校验
│   │   ├── converters.py         # 格式转换处理
│   │   └── README.md             # 处理逻辑详细说明文档
│   ├── processor_qwen/          # Qwen处理模块
│   │   └── text_preprocessor.py  # 文本预处理
│   ├── processors_old/           # 旧版处理模块（已废弃）
│   ├── utils/                  # 工具模块
│   │   ├── address_parser.py   # 地址解析器
│   │   ├── entity_extractor.py # 实体提取器
│   │   └── exceptions.py       # 异常定义
│   ├── model_manager.py        # 模型管理器
│   ├── tasks/                  # 定时任务模块
│   │   ├── api_usage_sync.py   # API使用统计同步任务
│   │   └── __init__.py
│   └── main.py                 # 主程序入口（已废弃，使用app.py）
├── model/                      # 模型文件夹
│   └── mgeo_geographic_composition_analysis_chinese_base/
├── data/                       # 数据文件夹（区域数据等）
├── logs/                       # 日志文件夹
├── md_document/                # 文档文件夹
│   ├── API_DOC.md              # API文档
│   ├── API_EXTRACT.md          # 实体抽取文档
│   ├── API_STATISTICS_AND_ERROR_LOG.md  # API统计与错误日志文档
│   ├── entity_mapping_README.md # 实体映射配置说明
│   └── candidates.md            # 候选结果处理说明
├── bin/                        # 启动脚本文件夹（Linux/Mac）
├── redis_command/              # Redis命令脚本
├── requirements.txt            # Python依赖
├── postman_collection.json     # Postman测试集合
├── entity_mapping.json         # 实体映射配置
├── start.py                    # Windows启动脚本
├── dev.env                     # 开发环境配置
├── show.env                    # 演示环境配置
├── prod.env                    # 生产环境配置
└── README.md                   # 项目说明文档
```

## 数据库配置

项目使用两个独立的MySQL数据库：

1. **地址补全数据库**：用于存储区域信息，支持地址数据补全和验证
2. **统计数据库**：用于存储API使用统计和错误日志（独立配置，互不影响）

### 地址补全数据库表结构

项目使用MySQL数据库存储区域信息，用于地址补全功能。表结构如下：

#### region_table（区域表）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | bigint | 主键，自增 | 主键ID |
| parent_id | bigint | 索引 | 父级编号 |
| region_name | varchar | 索引，非空 | 区域名称 |
| region_type | int | 索引，非空 | 区域类型（1001=省，1002=市，1003=区/县，1004=街道/镇） |
| creator | varchar | 非空，默认空字符串 | 创建人 |
| creator_id | bigint | 非空，默认0 | 创建人ID |
| create_time | timestamp | 可空 | 创建时间 |
| last_operator | varchar | 非空，默认空字符串 | 最后操作人 |
| last_operator_id | bigint | 非空，默认0 | 最后操作人ID |
| last_modify_time | timestamp | 可空 | 编辑时间 |
| is_deleted | tinyint | 索引，默认0 | 是否删除（0=否，1=是） |

**区域类型说明**：
- 1001：省/直辖市/自治区
- 1002：市
- 1003：区/县
- 1004：街道/镇

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

项目支持**自动环境配置加载**功能，系统会根据服务器IP地址自动匹配并加载对应的环境配置文件。

#### 环境配置文件

项目支持三个环境配置文件：
- `dev.env`：开发环境配置
- `show.env`：演示环境配置
- `prod.env`：生产环境配置

#### 自动环境匹配规则

系统会根据当前服务器的IP地址自动匹配环境，匹配优先级：**prod > show > dev**（生产环境优先级最高）

**环境IP地址映射**（可在 `src/config/env_loader.py` 中修改）：
- **开发环境（dev）**：`localhost`、`127.0.0.1`、`dev.example.com`
- **演示环境（show）**：`<演示环境IP地址1>`、`<演示环境IP地址2>`
- **生产环境（prod）**：`<生产环境IP地址1>`、`<生产环境IP地址2>`、`<生产环境IP地址3>`、`prod.example.com`、`www.example.com`

**匹配逻辑**：
1. 系统启动时自动获取服务器IP地址
2. 根据IP地址匹配对应的环境（prod > show > dev）
3. 加载对应的环境配置文件（prod.env、show.env 或 dev.env）
4. 如果所有环境文件加载失败，会尝试加载 `.env` 作为兼容备选
5. 如果仍失败，将使用系统环境变量或默认值

#### 配置步骤

**方式1：使用环境配置文件（推荐）**

复制环境变量模板文件并创建对应的环境配置文件：

```bash
# Windows
copy .env_template dev.env
copy .env_template show.env
copy .env_template prod.env

# Linux/Mac
cp .env_template dev.env
cp .env_template show.env
cp .env_template prod.env
```

编辑对应的环境配置文件（如 `dev.env`），配置以下内容：

```env
# 模型基础路径（相对于项目根目录）
MODEL_PATH=model/

# 模型是否已存在（true/false）
# MODEL_EXISTS=true: 模型已存在，严格禁用ModelScope下载，只使用本地模型（推荐生产环境）
# MODEL_EXISTS=false: 模型可能不存在，允许从ModelScope自动下载（适合开发环境）
MODEL_EXISTS=true

# DashScope API密钥（已废弃，qwen-flash模型不再使用，但保留配置项）
# DASHSCOPE_API_KEY=your_api_key_here

# MySQL数据库配置（用于地址补全功能）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_CHARSET=utf8mb4
MYSQL_REGION_TABLE=region_table

# Redis缓存配置（可选，用于提升性能）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600

# 区域类型映射配置（可选，使用默认值）
REGION_TYPE_PROVINCE=1001
REGION_TYPE_CITY=1002
REGION_TYPE_EXP_AREA=1003
REGION_TYPE_STREET=1004

## 启动服务

### 方式1：直接运行（推荐）

```bash
python app.py
# 或者 python start.py
```

### 方式2：使用uvicorn

```bash
uvicorn app:app --host 0.0.0.0 --port 13110 --reload
```

服务启动后，默认运行在：`http://localhost:13110`

## API接口文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:13110/docs（如果配置了ROOT_PATH，则为 http://localhost:13110/ner_extract_info/docs）
- **ReDoc**: http://localhost:13110/redoc（如果配置了ROOT_PATH，则为 http://localhost:13110/ner_extract_info/redoc）

**注意**：默认情况下，API路径前缀为 `/ner_extract_info`，可通过环境变量 `ROOT_PATH` 配置。如果设置为空字符串，则无路径前缀。

## API接口说明

**注意**：以下接口路径为相对路径。如果配置了 `ROOT_PATH` 环境变量（默认为 `/ner_extract_info`），实际路径为 `{ROOT_PATH}/api/...`。例如：`/ner_extract_info/api/health`。

### 1. 健康检查

**GET** `/api/health`

检查服务运行状态。

**响应示例**：
```json
{
  "status": "ok",
  "message": "NER API服务运行正常",
  "timestamp": "2025-12-25T10:00:00"
}
```

### 2. 获取支持的模型列表

**GET** `/api/models`

获取系统支持的所有模型列表。

**响应示例**：
```json
{
  "status": "success",
  "models": [
    "mgeo_geographic_composition_analysis_chinese_base"
  ],
  "count": 1
}
```

### 3. 实体抽取

**POST** `/api/extract`

从文本中抽取实体，使用 MGeo 地理组成分析模型。

**注意**：此接口会自动记录使用统计和错误日志：
- **使用统计**：每次调用时使用Redis实时计数，定时任务同步到MySQL
- **错误日志**：当接口失败时（Success=False或ResultCode != "100"），自动记录完整的请求和响应上下文
- 详细说明请参考：[API统计与错误日志文档](md_document/API_STATISTICS_AND_ERROR_LOG.md)

**请求体**：
```json
{
  "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
}
```

**参数说明**：
- `Content`（必需）：待处理的文本，格式：地址信息 人名 电话

**响应示例（成功）**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": {
      "id": 1000,
      "parent_id": null,
      "region_name": "广东省",
      "region_type": 1001
    },
    "CityName": {
      "id": 4567,
      "parent_id": 1000,
      "region_name": "深圳市",
      "region_type": 1002
    },
    "ExpAreaName": {
      "id": 6789,
      "parent_id": 4567,
      "region_name": "龙岗区",
      "region_type": 1003
    },
    "StreetName": {
      "id": 12345,
      "parent_id": 6789,
      "region_name": "坂田街道",
      "region_type": 1004
    },
    "Address": "长坑路西2巷2号202",
    "Mobile": "18273778575",
    "Name": "黄大大"
  },
  "Success": true,
  "Reason": "解析成功",
  "ResultCode": "100",
  "Warning": []
}
```

**响应示例（有候选值）**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": {
      "id": 1000,
      "parent_id": null,
      "region_name": "北京市",
      "region_type": 1001
    },
    "CityName": {
      "id": 4567,
      "parent_id": 1000,
      "region_name": "北京市",
      "region_type": 1002
    },
    "ExpAreaName": {
      "id": [111, 222],
      "parent_id": [4567, 4567],
      "candidates": [
        {"id": 111, "parent_id": 4567},
        {"id": 222, "parent_id": 4567}
      ],
      "region_name": "三环以内",
      "region_type": 1003
    },
    "StreetName": {
      "id": null,
      "parent_id": null,
      "region_name": "",
      "region_type": 1004
    }
  },
  "Success": true,
  "Reason": "地址信息无法完全确定，ExpAreaName存在多个候选值",
  "ResultCode": "102",
  "Warning": ["ExpAreaName存在2个无法确定的候选值"]
}
```

**说明**：
- 如果配置了MySQL数据库连接，系统会自动进行地址补全
- 地址补全功能会根据数据库中的区域信息验证和补全地址数据
- 响应中包含 `ResultCode` 和 `Success` 字段，表示处理结果状态
- 如果存在无法确定的候选值，会在 `Warning` 字段中提供警告信息

**状态码说明**：
- `100`：解析成功（所有地址字段都有有效的ID，Success=true）
- `101`：请求参数错误（Content为空、包含危险字符或模型名称不支持，Success=false）
- `102`：地理模型解析失败（模型加载失败、模型处理失败或地址补全异常，Success=false）
  - 当 `MODEL_EXISTS=true` 且本地模型不存在或加载失败时，会返回此状态码
  - 异常信息会清晰说明：模型应该存在但不允许从 ModelScope 下载，并提供解决建议
- `103`：地址无法完全确定（地址信息缺失或存在多个候选值无法确定，Success=false）

**注意**：此接口会自动记录使用统计和错误日志：
- **使用统计**：每次调用时使用Redis实时计数，定时任务同步到MySQL
- **错误日志**：当接口失败时（Success=False或ResultCode != "100"），自动记录完整的请求和响应上下文
- 详细说明请参考：[API统计与错误日志文档](md_document/API_STATISTICS_AND_ERROR_LOG.md)

## API使用统计与错误日志

项目提供完整的API使用统计和错误日志记录功能，帮助监控和分析接口使用情况。

### 功能概述

1. **API使用频次统计**：
   - 使用Redis实时计数，每次API调用时自动增加计数
   - 定时任务（默认每小时）将统计数据同步到MySQL
   - 支持按日期和API名称查询统计信息

2. **接口错误日志**：
   - 当接口失败时（Success=False或ResultCode != "100"），自动记录完整的请求和响应上下文
   - 直接写入MySQL，用于追溯、排查、审计和分析
   - 记录内容包括：请求文本、提取数据、状态码、原因说明、警告信息等

### 配置说明

**统计数据库配置**（独立于地址补全数据库）：
```env
# MySQL统计数据库配置
MYSQL_STATS_HOST=localhost
MYSQL_STATS_PORT=3306
MYSQL_STATS_USER=root
MYSQL_STATS_PASSWORD=your_password
MYSQL_STATS_DATABASE=api_statistics
MYSQL_STATS_CHARSET=utf8mb4

# API使用统计配置
MYSQL_API_USAGE_TABLE=extract_api_usage
MYSQL_API_ERROR_LOG_TABLE=extract_api_error_log
API_USAGE_SYNC_INTERVAL=3600  # 同步间隔（秒），默认1小时
API_USAGE_SYNC_DAY_OFFSET=1   # 同步日期偏移，默认同步昨天的数据
```

**说明**：
- 统计数据库与地址补全数据库完全独立，互不影响
- 如果未配置`MYSQL_STATS_*`配置项，系统会自动使用`MYSQL_*`配置项作为回退（向后兼容）
- 建议在生产环境中使用独立的统计数据库，以确保数据隔离和性能优化

### 表结构

**使用统计表**（`extract_api_usage`）：
- `stat_date`：统计日期
- `api_name`：API名称（如：`/api/extract`）
- `call_count`：调用次数

**错误日志表**（`extract_api_error_log`）：
- `id`：主键（自增）
- `model_type`：模型类型
- `content`：请求的文本内容
- `extract_data`：提取的数据（JSON格式）
- `result_code`：结果状态码
- `reason`：原因说明
- `warning`：警告信息列表（JSON格式）
- `time`：失败时间

### 自动初始化

系统启动时会自动检查并创建统计表和错误日志表。如果表已存在，则跳过创建；如果表不存在，则自动创建。

### 详细文档

更多详细信息，包括表结构、查询示例、技术要点等，请参考：[API统计与错误日志文档](md_document/API_STATISTICS_AND_ERROR_LOG.md)

## 支持的模型

### MGeo地理组成分析模型

> MGeo地址Query成分分析要素识别-中文-地址领域-base

- **模型标识**：`mgeo_geographic_composition_analysis_chinese_base`
- **用途**：地理实体识别和地址成分分析
- **特点**：
  - 自动识别地址成分
  - 支持地址纠错和补全
  - 返回统一格式的结构化数据
- **适用场景**：地址解析、地理实体识别等

## 地址补全功能

项目支持基于MySQL数据库的三阶段地址数据匹配处理系统，用于将模型提取的地址信息与数据库中的标准地址数据进行匹配、补全和校验。

### 三阶段处理流程

系统采用三阶段处理逻辑，确保地址数据的准确性和完整性：

1. **第一阶段：地址数据匹配（Stage1Matcher）**
   - 执行四个匹配任务，收集所有候选结果
   - **任务1**: StreetName匹配（region_type=1004）
   - **任务2**: ExpAreaName匹配（region_type=1003）
   - **任务3**: CityName匹配（region_type=1002）
   - **任务4**: ProvinceName匹配（region_type=1001）
   - 使用双向模糊匹配算法（精确匹配 + 正向/反向LIKE匹配）
   - 匹配成功后，从AreasInfo或Address中清除已匹配的region_name

2. **第二阶段：候选结果处理（Stage2Resolver）**
   - 从最高级别向下筛选，通过parent_id关系确定唯一结果
   - **向下过滤**：根据上级的id筛选下级候选表中的parent_id
   - **上下层级补全**：从下级候选表的parent_id向上查找本级数据
   - **向上追溯**：从唯一确定的字段递归向上追溯所有上级
   - **去除重复**：检查并清除上下级重复的region_name

3. **第三阶段：数据校验（Stage3Validator）**
   - 检查空字段、候选值、未匹配字段
   - 转换单候选格式为唯一值格式
   - 设置状态码（ResultCode）和警告信息（Warning）

### 核心特性

- **双向模糊匹配**：支持精确匹配、正向匹配（field_value in region_name）和反向匹配（region_name in field_value）
- **匹配质量评分**：根据匹配类型、长度相似度、覆盖率计算匹配得分
- **候选表管理**：保存多个可能的匹配结果，通过上下级关系筛选确定唯一值
- **上下级关系处理**：通过parent_id维护地址层级关系，支持向上追溯和向下过滤
- **直辖市处理**：自动识别并处理直辖市数据（北京市、天津市、上海市、重庆市）
- **特别行政区处理**：支持香港、澳门特别行政区的特殊处理
- **Redis缓存**：缓存region_type查询结果，大幅减少数据库查询，提升性能

### 处理层级

系统处理四个层级的地址信息：
- **ProvinceName** (省域级, region_type=1001)
- **CityName** (城市级, region_type=1002)
- **ExpAreaName** (区县级, region_type=1003)
- **StreetName** (街道乡镇级, region_type=1004)

### 补全逻辑

- 预处理：处理直辖市数据调整
- 第一阶段：执行四个匹配任务，生成候选表
- 第二阶段：按优先级（ProvinceName > CityName > ExpAreaName > StreetName）处理候选表
- 第三阶段：数据校验，设置状态码和警告信息
- 所有地址字段最终转换为对象格式（包含id、parent_id、region_name、region_type）或候选表格式

详细处理逻辑请参考：[MGeo数据匹配处理逻辑说明文档](src/processor_mgeo/README.md)

## 日志记录

系统自动记录以下信息到日志文件：

- **推理时间**：每个方法调用的推理耗时（模型处理时间）
- **数据库匹配时间**：三阶段数据库匹配修正的总耗时和阶段信息
- **模型信息**：使用的模型名称
- **文本长度**：处理的文本长度
- **执行状态**：成功或失败
- **错误信息**：详细的错误堆栈
- **匹配详情**：各阶段的匹配结果、候选表信息等（DEBUG级别）

### 日志配置

- **控制台输出**：只显示INFO级别及以上的日志（可通过环境变量调整）
- **文件记录**：记录所有级别（包括DEBUG）的日志
- **日志文件位置**：`logs/inference_YYYYMMDD.log`（按日期命名）
- **日志格式**：`YYYY-MM-DD HH:MM:SS - 日志记录器名称 - 级别 - 消息内容`

#### 日志级别配置

可在环境配置文件中设置日志级别，控制输出的详细程度：

```bash
# 在 .env、dev.env、show.env 或 prod.env 中设置
LOG_LEVEL=INFO  # 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**日志级别说明**：
- **DEBUG**：记录所有详细信息，包括调试信息（适合开发和问题排查）
- **INFO**：记录一般信息（默认级别，适合生产环境）
- **WARNING**：只记录警告和错误
- **ERROR**：只记录错误和严重错误
- **CRITICAL**：只记录严重错误

**使用建议**：
- 开发环境：设置为 `LOG_LEVEL=DEBUG` 查看详细日志
- 生产环境：设置为 `LOG_LEVEL=INFO` 或 `LOG_LEVEL=WARNING` 减少日志量

### 日志示例

```
2025-12-30 14:20:25 - NER_API - INFO - 推理时间记录 - 方法: extract_entities | 模型: mgeo_geographic_composition_analysis_chinese_base | 文本长度: 31 | 推理耗时: 0.4103秒 (410.34毫秒) | 状态: 成功
2025-12-30 14:20:25 - NER_API - INFO - 开始进行数据库匹配修正处理
2025-12-30 14:20:25 - NER_API - DEBUG - 从缓存获取region_type=1004的记录，共44629条
2025-12-30 14:20:25 - NER_API - INFO - 第一阶段匹配完成: StreetName=2个候选, ExpAreaName=1个候选, CityName=1个候选, ProvinceName=1个候选
2025-12-30 14:20:25 - NER_API - INFO - 第二阶段处理完成: ProvinceName=已确定, CityName=已确定, ExpAreaName=已确定, StreetName=已确定
2025-12-30 14:20:25 - NER_API - INFO - 第三阶段结果校验完成：状态码100 解析成功
2025-12-30 14:20:25 - NER_API - INFO - 数据库匹配修正耗时: 0.0130秒 (13.00毫秒)
2025-12-30 14:20:25 - NER_API - INFO - 数据库匹配修正时间记录 - 方法: complete_extract_response | 匹配耗时: 0.0130秒 (13.00毫秒) | 状态: 成功
```

## 环境变量配置

### 自动环境配置加载

项目使用 `src/config/env_loader.py` 模块实现自动环境配置加载功能。

**工作原理**：
1. **IP地址获取**：系统启动时通过 socket 连接获取服务器IP地址
2. **环境匹配**：根据IP地址在预定义的域名/IP列表中匹配（prod > show > dev）
3. **配置文件加载**：自动加载匹配的环境配置文件（prod.env、show.env 或 dev.env）
4. **容错机制**：如果所有环境文件加载失败，会尝试加载 `.env` 作为兼容备选

**自定义环境映射**：

如需修改环境IP地址映射，可编辑 `src/config/env_loader.py` 文件中的 `ENV_DOMAIN_MAPPING` 配置：

```python
ENV_DOMAIN_MAPPING: Dict[str, List[str]] = {
    'dev': [
        'localhost',
        '127.0.0.1',
        'dev.example.com',
        # 添加更多开发环境IP/域名
    ],
    'show': [
        '<演示环境IP地址1>',
        '<演示环境IP地址2>',
        # 添加更多演示环境IP/域名
    ],
    'prod': [
        '<生产环境IP地址1>',
        '<生产环境IP地址2>',
        '<生产环境IP地址3>',
        'prod.example.com',
        'www.example.com',
        # 添加更多生产环境IP/域名
    ]
}
```

**日志输出**：

系统会在启动时输出环境配置加载日志，例如：
```
INFO - 当前域名: <服务器IP地址>
INFO - 当前域名/IP <服务器IP地址> 在生产环境域名列表中，加载 prod.env
INFO - ✓ 已加载环境变量文件: prod.env
INFO -   已加载配置项: 总计45个, Redis相关5个, MySQL相关10个
```

### 模型加载配置

- `MODEL_EXISTS`：模型是否已存在（true/false，默认：true）
  - **`MODEL_EXISTS=true`**（推荐生产环境）：
    - 模型已存在，严格禁用 ModelScope 自动下载
    - 只使用本地模型文件
    - 如果本地模型不存在或加载失败，会抛出异常并返回状态码 102
    - 确保生产环境只使用已验证的本地模型，避免意外下载
  - **`MODEL_EXISTS=false`**（适合开发环境）：
    - 模型可能不存在，允许从 ModelScope 自动下载
    - 优先使用本地模型，如果本地模型不存在或加载失败，自动切换到 ModelScope 下载
    - 适合首次部署或模型文件未下载的场景

**配置示例**：
```env
# 生产环境：严格使用本地模型
MODEL_EXISTS=true

# 开发环境：允许自动下载
MODEL_EXISTS=false
```

**说明**：
- 默认值为 `true`，确保生产环境的安全性
- 当 `MODEL_EXISTS=true` 时，系统不会设置 `MODELSCOPE_CACHE` 环境变量，确保 ModelScope 直接从本地路径加载
- 当 `MODEL_EXISTS=false` 时，系统会设置 `MODELSCOPE_CACHE` 环境变量，允许 ModelScope 下载到缓存目录
- 模型加载失败时的异常信息会包含清晰的错误说明和解决建议，便于排查问题

### MySQL数据库配置

#### 地址补全数据库配置

- `MYSQL_HOST`：数据库主机（默认：localhost）
- `MYSQL_PORT`：数据库端口（默认：3306）
- `MYSQL_USER`：数据库用户名（默认：root）
- `MYSQL_PASSWORD`：数据库密码
- `MYSQL_DATABASE`：数据库名称
- `MYSQL_CHARSET`：字符集（默认：utf8mb4）
- `MYSQL_REGION_TABLE`：区域表名（默认：region_table）

#### 统计数据库配置（API使用统计和错误日志）

- `MYSQL_STATS_HOST`：统计数据库主机（默认：localhost，如果未配置则使用`MYSQL_HOST`）
- `MYSQL_STATS_PORT`：统计数据库端口（默认：3306，如果未配置则使用`MYSQL_PORT`）
- `MYSQL_STATS_USER`：统计数据库用户名（默认：root，如果未配置则使用`MYSQL_USER`）
- `MYSQL_STATS_PASSWORD`：统计数据库密码（如果未配置则使用`MYSQL_PASSWORD`）
- `MYSQL_STATS_DATABASE`：统计数据库名称（如果未配置则使用`MYSQL_DATABASE`）
- `MYSQL_STATS_CHARSET`：字符集（默认：utf8mb4）
- `MYSQL_STATS_MAX_CONNECTIONS`：最大连接数（默认：10）
- `MYSQL_STATS_CONNECT_TIMEOUT`：连接超时时间（默认：10秒）

#### API使用统计配置

- `MYSQL_API_USAGE_TABLE`：使用统计表名（默认：extract_api_usage）
- `MYSQL_API_ERROR_LOG_TABLE`：错误日志表名（默认：extract_api_error_log）
- `API_USAGE_SYNC_INTERVAL`：同步间隔，单位秒（默认：3600，即1小时）
- `API_USAGE_SYNC_DAY_OFFSET`：同步日期偏移（默认：1，即同步昨天的数据）

**说明**：
- 统计数据库与地址补全数据库完全独立，互不影响
- 如果未配置`MYSQL_STATS_*`配置项，系统会自动使用`MYSQL_*`配置项作为回退（向后兼容）
- 建议在生产环境中使用独立的统计数据库，以确保数据隔离和性能优化

### Redis缓存配置（可选，用于提升性能）

- `REDIS_HOST`：Redis主机（默认：localhost）
- `REDIS_PORT`：Redis端口（默认：6379）
- `REDIS_DB`：Redis数据库编号（默认：0）
- `REDIS_PASSWORD`：Redis密码（可选）
- `REDIS_CACHE_TTL`：缓存TTL，单位秒（默认：3600，即1小时）

**说明**：
- Redis缓存用于两个用途：
  1. **区域数据缓存**：存储region_type粗筛选结果，大幅减少数据库查询
  2. **API使用统计**：实时计数API调用次数，定时任务同步到MySQL
- 如果Redis不可用，区域数据缓存会自动降级为直接查询数据库，不影响功能
- API使用统计功能会禁用，但不影响接口正常使用
- 区域数据缓存只存储关键字段：id、parent_id、region_name、region_type

### 模型路径配置

- `MODEL_PATH`：模型基础路径（默认：`model/`）
  - 用于存储本地模型文件和 ModelScope 缓存
  - 可以配置相对路径（相对于项目根目录）或绝对路径
  - 如果不配置，默认使用项目根目录下的 `model/` 目录

### 可选配置

- `REGION_TYPE_PROVINCE`：省份类型代码（默认：1001）
- `REGION_TYPE_CITY`：城市类型代码（默认：1002）
- `REGION_TYPE_EXP_AREA`：区县类型代码（默认：1003）
- `REGION_TYPE_STREET`：街道类型代码（默认：1004）

## 常见问题

### Q: 需要配置DashScope API密钥吗？

A: 不需要。系统使用MGeo本地模型，无需配置DashScope API密钥。qwen-flash模型已废弃。

### Q: 数据库连接失败怎么办？

A: 检查以下配置：
1. MySQL服务是否启动
2. 数据库连接配置（主机、端口、用户名、密码）是否正确
3. 数据库是否存在
4. 用户是否有访问权限
5. 区域表（region_table）是否存在

### Q: 地址补全功能如何工作？

A: 系统采用三阶段处理逻辑：
1. **第一阶段**：执行四个匹配任务（StreetName、ExpAreaName、CityName、ProvinceName），使用双向模糊匹配算法收集候选结果
2. **第二阶段**：通过上下级关系（parent_id）处理候选表，确定唯一结果。支持向下过滤、上下层级补全、向上追溯、去除重复等机制
3. **第三阶段**：数据校验，检查空字段、候选值、未匹配字段，设置状态码和警告信息
4. 使用Redis缓存区域数据，大幅提升查询性能
5. 支持直辖市和特别行政区的特殊处理

详细逻辑请参考：[MGeo数据匹配处理逻辑说明文档](src/processor_mgeo/README.md)

### Q: 状态码的含义是什么？

A: 系统使用细粒度的状态码体系：
- **100**：解析成功，所有地址信息都已确定
- **101**：地址解析失败，模型处理失败或模型加载失败（Success=false）
- **102**：地址信息无法完全确定，存在多个候选值（Success=true，有Warning信息）
- **103**：地址无法完全确定（存在空字段或候选值，Success=false）
- **104**：具体地址不在数据库中（第一阶段匹配失败但继续执行后续阶段，Success=true）

### Q: Redis缓存是必需的吗？

A: 不是必需的。Redis缓存用于提升性能，如果Redis不可用，系统会自动降级为直接查询数据库，功能完全正常。建议在生产环境中启用Redis缓存以提升性能。

### Q: 系统使用哪个模型？

A: 系统固定使用 `mgeo_geographic_composition_analysis_chinese_base` 模型（MGeo地址Query成分分析要素识别模型），无需选择。该模型配合MySQL表查询补全，延迟低，效果好。

### Q: MODEL_EXISTS 环境变量的作用是什么？

A: `MODEL_EXISTS` 环境变量用于控制模型加载策略，确保生产环境的安全性：

- **`MODEL_EXISTS=true`**（默认，推荐生产环境）：
  - 严格模式：只使用本地模型，禁用 ModelScope 自动下载
  - 如果本地模型不存在或加载失败，会抛出异常并返回状态码 102
  - 异常信息会清晰说明：模型应该存在但不允许下载，并提供解决建议
  - 确保生产环境只使用已验证的本地模型，避免意外下载或使用缓存中的模型

- **`MODEL_EXISTS=false`**（适合开发环境）：
  - 允许模式：允许从 ModelScope 自动下载
  - 优先使用本地模型，如果本地模型不存在或加载失败，自动切换到 ModelScope 下载
  - 适合首次部署或模型文件未下载的场景

**使用建议**：
- 生产环境：设置为 `MODEL_EXISTS=true`，确保只使用本地模型
- 开发环境：可以设置为 `MODEL_EXISTS=false`，方便自动下载模型
- 首次部署：可以先设置为 `MODEL_EXISTS=false` 下载模型，然后改为 `MODEL_EXISTS=true`

### Q: API使用统计功能如何工作？

A: 系统提供API使用频次统计和错误日志记录功能：
1. **使用统计**：每次API调用时使用Redis INCR命令实时计数，定时任务每小时同步到MySQL
2. **错误日志**：当接口失败时（Success=False或ResultCode != "100"），自动记录完整的请求和响应上下文
3. **独立数据库**：使用独立的统计数据库（`MYSQL_STATS_*`配置），与地址补全数据库完全分离
4. **定时任务**：使用Redis分布式锁防止重复执行，支持幂等操作

详细说明请参考：[API统计与错误日志文档](md_document/API_STATISTICS_AND_ERROR_LOG.md)

### Q: 环境配置文件如何自动加载？

A: 系统使用 `env_loader.py` 模块实现自动环境配置加载：
1. **自动识别**：系统启动时自动获取服务器IP地址
2. **自动匹配**：根据IP地址匹配对应的环境（prod > show > dev）
3. **自动加载**：加载匹配的环境配置文件（prod.env、show.env 或 dev.env）
4. **容错处理**：如果所有环境文件加载失败，会尝试加载 `.env` 作为兼容备选
5. **日志记录**：启动时会输出环境配置加载日志，便于排查问题

**如何修改环境IP映射**：
- 编辑 `src/config/env_loader.py` 文件中的 `ENV_DOMAIN_MAPPING` 配置
- 添加或修改对应环境的IP地址或域名列表
- 重启服务后生效

### Q: 如何测试API接口？

A: 
1. 启动服务：`python app.py `  或 `python start.py`
2. 访问 http://localhost:13110/docs 查看Swagger UI文档
3. 在文档中直接测试API接口
4. 或使用Postman、curl等工具发送HTTP请求

**使用 Postman Collection：**
- 项目根目录提供了 `postman_collection.json` 文件，可以直接导入到 Postman 中使用
- Collection 中已配置了变量，方便切换不同环境：
  - `addr`: 完整的API基础地址（默认：`<API网关地址>/ner_extract_info`）
- 如需修改服务器地址，可以在 Postman 中编辑 Collection 变量 `addr`，所有请求会自动使用新的配置
- 例如：本地开发环境可设置为 `http://localhost:13110/ner_extract_info`

## 许可证

本项目使用 Apache License 2.0 许可证。

