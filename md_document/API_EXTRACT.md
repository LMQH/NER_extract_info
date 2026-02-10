# /api/extract 接口说明文档

## 概述

`/api/extract` 是系统的核心接口，用于从文本中抽取地址、人名、电话等实体信息。该接口使用 MGeo 地理组成分析模型，并自动进行地址补全和数据库匹配，返回结构化的地址信息。

**接口地址**：`POST /api/extract`

**功能特性**：
- ✅ 使用MGeo地理组成分析模型进行实体抽取
- ✅ 自动格式转换和统一输出
- ✅ 三阶段地址匹配和补全（第一阶段匹配、第二阶段处理、第三阶段校验）
- ✅ 数据库验证和ID补全
- ✅ 自动记录推理时间
- ✅ API使用统计和错误日志记录（自动统计调用频次，记录失败事件）
- ✅ 完善的错误处理和状态码机制

---

## 请求格式

### 请求方法
`POST`

### 请求头
```
Content-Type: application/json
```

### 请求体（JSON）

```json
{
  "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
}
```

### 请求参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `Content` | string | 是 | 待处理的文本内容，格式通常为：`地址信息 人名 电话` |

**说明**：接口固定使用 `mgeo_geographic_composition_analysis_chinese_base` 模型（MGeo地理组成分析模型），无需指定模型参数。

---

## 响应格式

### 成功响应（ResultCode: 100）

```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": {
      "id": 440000,
      "parent_id": null,
      "region_name": "广东省",
      "region_type": 1001
    },
    "CityName": {
      "id": 440300,
      "parent_id": 440000,
      "region_name": "深圳市",
      "region_type": 1002
    },
    "ExpAreaName": {
      "id": 440307,
      "parent_id": 440300,
      "region_name": "龙岗区",
      "region_type": 1003
    },
    "StreetName": {
      "id": 440307001,
      "parent_id": 440307,
      "region_name": "坂田街道",
      "region_type": 1004
    },
    "AreasInfo": "长坑路",
    "Address": "西2巷2号202",
    "Mobile": "18273778575",
    "Name": "黄大大",
    "others": ""
  },
  "Success": true,
  "Reason": "解析成功",
  "ResultCode": "100",
  "Warning": []
}
```

### 响应字段说明

#### 顶层字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `EBusinessID` | string | 业务ID，可通过环境变量 `EBUSINESS_ID` 配置，默认值为 "2223333" |
| `Data` | object | 提取的实体数据，包含地址、人名、电话等信息 |
| `Success` | boolean | 是否成功解析 |
| `Reason` | string | 处理结果的原因说明 |
| `ResultCode` | string | 结果状态码，见下方状态码说明 |
| `Warning` | array | 警告信息列表，当存在无法确定的候选值或匹配失败时会有警告提示 |

#### Data 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ProvinceName` | object/string | 省份信息，成功匹配时为对象格式（包含id、parent_id、region_name、region_type），否则为字符串 |
| `CityName` | object/string | 城市信息，格式同ProvinceName |
| `ExpAreaName` | object/string | 区/县信息，格式同ProvinceName |
| `StreetName` | object/string | 街道/镇信息，格式同ProvinceName |
| `AreasInfo` | string | 区域信息（如道路名称） |
| `Address` | string | 详细地址（门牌号等） |
| `Mobile` | string | 手机号码 |
| `Name` | string | 姓名 |
| `others` | string | 其他信息 |

#### 地址字段对象格式

当地址字段成功匹配到数据库记录时，会返回对象格式：

```json
{
  "id": 440000,
  "parent_id": 440000,
  "region_name": "广东省",
  "region_type": 1001
}
```

**字段说明**：
- `id`: 区域ID（数据库主键）
- `parent_id`: 父级区域ID（用于建立层级关系）
- `region_name`: 区域名称
- `region_type`: 区域类型码
  - `1001`: 省
  - `1002`: 市
  - `1003`: 区/县
  - `1004`: 街道/镇

#### 候选值格式

当某个地址字段存在多个候选值无法确定时，会返回候选信息格式：

```json
{
  "ExpAreaName": {
    "candidates": [
      {"id": 111, "parent_id": 100, "region_name": "海淀区"},
      {"id": 222, "parent_id": 100, "region_name": "朝阳区"},
      {"id": 333, "parent_id": 100, "region_name": "丰台区"}
    ],
    "region_type": 1003
  }
}
```

**字段说明**：
- `candidates`: 结构化候选列表，每个元素包含：
  - `id`: 区域ID（数据库主键）
  - `parent_id`: 父级区域ID
  - `region_name`: 区域名称
- `region_type`: 区域类型

---

## 状态码说明

| 状态码 | 说明 | Success | 处理结果 |
|--------|------|---------|----------|
| `100` | 解析成功 | true | 地址信息已完全确定，所有地址字段都有有效的ID |
| `101` | 请求参数错误 | false | Content字段为空或模型名称不支持，所有后续流程都无法执行 |
| `102` | 地理模型解析失败 | false | 模型加载失败、模型处理失败、地址信息无法解析或地址补全异常 |
| `103` | 地址无法完全确定 | false | 地址信息缺失或存在多个候选值无法确定 |

### 状态码判断逻辑

状态码按优先级判断（优先级从高到低）：

1. **101 - 请求参数错误**（优先级最高）：
   - Content字段为空或只包含空白字符
   - 模型名称不在支持的模型列表中
   - Success=false
   - 说明：请求参数不符合要求，所有后续流程都无法执行

2. **102 - 地理模型解析失败**：
   - 模型加载失败
   - 模型处理失败
   - 地址补全过程中出现异常
   - Success=false
   - 说明：处理过程中出现错误，无法完成解析

3. **103 - 地址无法完全确定**：
   - 模型处理成功
   - 地址补全过程中存在候选值（某些字段返回候选ID列表）
   - 地址信息缺失或无法完全确定
   - Success=false
   - 说明：存在多个候选值无法确定，需要人工判断

4. **100 - 解析成功**：
   - 模型处理成功
   - 地址补全成功
   - 所有地址字段（ProvinceName, CityName, ExpAreaName, StreetName）都有有效的ID（不是候选ID列表）
   - Success=true
   - 说明：地址信息已完全确定

---

## 处理流程

接口处理流程如下：

```
1. 请求参数验证
   ├─ Content字段验证 → 失败返回101
   └─ 模型名称验证 → 失败返回101

2. 模型加载
   └─ 加载失败 → 返回102

3. 实体抽取
   ├─ 调用模型.extract_entities(Content)
   ├─ 记录推理时间到日志
   └─ 抽取失败 → 返回102

4. 格式转换
   └─ mgeo_geographic_composition_analysis_chinese_base: 转换为统一格式

5. 数据校验和清洗
   └─ InputValidator.validate_extract_response()

6. 地址补全（如果address_completer可用）
   ├─ 三阶段处理流程（第一阶段匹配、第二阶段处理、第三阶段校验）
   ├─ 数据库验证和ID补全
   ├─ 候选值处理
   └─ 补全失败 → 返回102

7. 返回结果
   ├─ 根据匹配结果设置ResultCode
   └─ 返回ExtractResponse
```

### 详细流程说明

#### 1. 请求参数验证

```python
# Content字段验证
if not request.Content or not request.Content.strip():
    return ExtractResponse(ResultCode="101", ...)
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
grep

#### 2. 模型加载和执行

```python
# 固定使用 mgeo_geographic_composition_analysis_chinese_base 模型
model = model_manager.load_model('mgeo_geographic_composition_analysis_chinese_base')

# 执行实体抽取
result = model.extract_entities(request.Content)

# 记录推理时间
logger.info(f"推理时间记录 - 方法: extract_entities | 模型: {model} | ...")
```

#### 3. 格式转换

MGeo地理组成分析模型的输出格式会被转换为统一的格式：

- **mgeo_geographic_composition_analysis_chinese_base**: 调用 `convert_mgeo_to_output_format()`

#### 4. 数据校验和清洗

在格式转换之后、地址补全之前进行数据校验：

```python
formatted_result = InputValidator.validate_extract_response(formatted_result)
```

确保进入数据库匹配阶段的数据是干净、安全的。

#### 5. 地址补全

如果 `address_completer` 可用，会进行三阶段地址匹配和补全处理：

**三阶段处理流程**：

1. **第一阶段：地址数据匹配**
   - 执行四个匹配任务，收集所有候选结果：
     - 任务1: StreetName匹配（region_type=1004）
     - 任务2: ExpAreaName匹配（region_type=1003）
     - 任务3: CityName匹配（region_type=1002）
     - 任务4: ProvinceName匹配（region_type=1001）
   - 生成四个候选表

2. **第二阶段：候选结果处理**
   - 按优先级处理四个字段的候选表（ProvinceName → CityName → ExpAreaName → StreetName）
   - 通过parent_id关系确定唯一结果
   - 包含多种处理策略：向下过滤、中间层级补全、级联匹配、向上追溯等

3. **第三阶段：数据校验**
   - 检查空字段、候选值、未匹配字段
   - 设置状态码和警告信息

**匹配机制**：
- 精确匹配 → 双向模糊匹配（LIKE匹配）
- 唯一结果：向上追溯补全所有字段
- 多个结果：存入候选表，等待上级确定后再筛选
- 无结果：记录匹配失败字段，继续下一阶段

详细说明请参考：[processor_mgeo/README.md](../src/processor_mgeo/README.md)

---

## 地址补全机制

### 三阶段处理流程

地址补全采用三阶段处理流程，确保地址信息的准确匹配和补全：

#### 第一阶段：地址数据匹配

执行四个匹配任务，收集所有候选结果：
1. **任务1**：StreetName匹配（region_type=1004）
2. **任务2**：ExpAreaName匹配（region_type=1003）
3. **任务3**：CityName匹配（region_type=1002）
4. **任务4**：ProvinceName匹配（region_type=1001）

#### 第二阶段：候选结果处理

按优先级处理候选表，通过多种策略确定唯一结果：
- 向下过滤：根据上级id筛选下级候选表
- 中间层级补全：使用上级id从缓存过滤本级数据
- 级联匹配：通过上下级关系筛选候选
- 向上追溯：从唯一值递归追溯上级

#### 第三阶段：数据校验

检查空字段、候选值、未匹配字段，设置状态码和警告信息。

### 匹配策略

每个匹配任务使用以下匹配策略：

1. **精确匹配**：`region_name = field_value`
2. **双向模糊匹配**（精确匹配失败时）：
   - 正向匹配：`field_value in region_name`
   - 反向匹配：`region_name in field_value`

### 候选值处理

当匹配到多个可能的区域记录时：

1. 存入候选表，等待上级确定
2. 上级确定后，使用 `parent_id` 过滤候选表
3. 如果过滤后仍有多个候选，返回候选信息对象
4. 如果过滤后找到唯一匹配，确定该字段

### Redis缓存

系统使用Redis缓存区域数据，减少数据库查询：

- 缓存键格式：`region:type:{region_type}`
- 缓存TTL：1小时（可通过环境变量 `REDIS_CACHE_TTL` 配置）
- 降级机制：Redis不可用时自动降级为直接查询数据库

详细说明请参考：[processor_mgeo/README.md](../src/processor_mgeo/README.md)

---

## 警告信息

当存在以下情况时，会在 `Warning` 字段中返回警告信息：

1. **候选值警告**：`"{field}存在{count}个无法确定的候选值"`
   - 当某个地址字段存在多个候选值无法确定时

2. **匹配失败警告**：`"{field}在数据库中匹配失败，不存在于数据库中"`
   - 当某个字段在数据库中完全匹配失败时

### 警告示例

```json
{
  "Success": false,
  "ResultCode": "103",
  "Warning": [
    "ExpAreaName存在3个无法确定的候选值",
    "AreasInfo在数据库中匹配失败，不存在于数据库中"
  ]
}
```

---

## 错误处理

### 请求参数错误（101）

**场景**：
- Content字段为空或只包含空白字符
- 模型名称不在支持的模型列表中

**响应示例**：
```json
{
  "EBusinessID": "1279441",
  "Data": {},
  "Success": false,
  "Reason": "Content字段不能为空",
  "ResultCode": "101",
  "Warning": []
}
```

### 模型加载失败（102）

**场景**：
- 模型文件不存在
- 模型加载过程中出现异常

**响应示例**：
```json
{
  "EBusinessID": "1279441",
  "Data": {},
  "Success": false,
  "Reason": "模型加载失败: ...",
  "ResultCode": "102",
  "Warning": []
}
```

### 实体抽取失败（102）

**场景**：
- 模型处理过程中出现异常
- 模型返回失败状态

**响应示例**：
```json
{
  "EBusinessID": "1279441",
  "Data": {},
  "Success": false,
  "Reason": "实体抽取失败: ...",
  "ResultCode": "102",
  "Warning": []
}
```

### 地址补全失败（102）

**场景**：
- 地址补全过程中出现异常
- 地址补全过程中发生错误

**响应示例**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": "广东省",
    "CityName": "深圳市",
    ...
  },
  "Success": false,
  "Reason": "地址补全失败: ...",
  "ResultCode": "102",
  "Warning": []
}
```

---

## 使用示例

### Python示例

```python
import requests

# API基础URL
BASE_URL = "http://localhost:13110"

# 请求数据
data = {
    "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
}

# 发送请求
response = requests.post(
    f"{BASE_URL}/api/extract",
    json=data,
    headers={"Content-Type": "application/json"}
)

# 处理响应
result = response.json()

if result["Success"]:
    print(f"解析成功: {result['Reason']}")
    print(f"省份: {result['Data']['ProvinceName']}")
    print(f"城市: {result['Data']['CityName']}")
    print(f"区县: {result['Data']['ExpAreaName']}")
    print(f"街道: {result['Data']['StreetName']}")
    print(f"姓名: {result['Data']['Name']}")
    print(f"电话: {result['Data']['Mobile']}")
    
    if result["Warning"]:
        print(f"警告: {', '.join(result['Warning'])}")
else:
    print(f"解析失败: {result['Reason']} (状态码: {result['ResultCode']})")
```

### JavaScript示例

```javascript
// 使用fetch API
fetch('http://localhost:13110/api/extract', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    Content: '广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575'
  })
})
.then(response => response.json())
.then(data => {
  if (data.Success) {
    console.log('解析成功:', data.Reason);
    console.log('省份:', data.Data.ProvinceName);
    console.log('城市:', data.Data.CityName);
    console.log('区县:', data.Data.ExpAreaName);
    console.log('街道:', data.Data.StreetName);
    console.log('姓名:', data.Data.Name);
    console.log('电话:', data.Data.Mobile);
    
    if (data.Warning && data.Warning.length > 0) {
      console.log('警告:', data.Warning.join(', '));
    }
  } else {
    console.error('解析失败:', data.Reason, '(状态码:', data.ResultCode + ')');
  }
})
.catch(error => console.error('请求错误:', error));
```

### cURL示例

```bash
curl -X POST http://localhost:13110/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
  }'
```

---

## 响应示例

### 示例1：完全成功（ResultCode: 100）

**请求**：
```json
{
  "Content": "广东省深圳市龙岗区坂田街道长坑路西2巷2号202 黄大大 18273778575"
}
```

**响应**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": {
      "id": 440000,
      "parent_id": null,
      "region_name": "广东省",
      "region_type": 1001
    },
    "CityName": {
      "id": 440300,
      "parent_id": 440000,
      "region_name": "深圳市",
      "region_type": 1002
    },
    "ExpAreaName": {
      "id": 440307,
      "parent_id": 440300,
      "region_name": "龙岗区",
      "region_type": 1003
    },
    "StreetName": {
      "id": 440307001,
      "parent_id": 440307,
      "region_name": "坂田街道",
      "region_type": 1004
    },
    "AreasInfo": "长坑路",
    "Address": "西2巷2号202",
    "Mobile": "18273778575",
    "Name": "黄大大",
    "others": ""
  },
  "Success": true,
  "Reason": "解析成功",
  "ResultCode": "100",
  "Warning": []
}
```

### 示例2：存在候选值（ResultCode: 103）

**请求**：
```json
{
  "Content": "北京市海淀区三环以内 张三 13800138000"
}
```

**响应**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": {
      "id": 110000,
      "parent_id": null,
      "region_name": "北京市",
      "region_type": 1001
    },
    "CityName": {
      "id": 110100,
      "parent_id": 110000,
      "region_name": "北京市",
      "region_type": 1002
    },
    "ExpAreaName": {
      "candidates": [
        {"id": 110108, "parent_id": 110100, "region_name": "海淀区"},
        {"id": 110109, "parent_id": 110100, "region_name": "朝阳区"},
        {"id": 110110, "parent_id": 110100, "region_name": "丰台区"}
      ],
      "region_type": 1003
    },
    "StreetName": "",
    "AreasInfo": "三环以内",
    "Address": "",
    "Mobile": "13800138000",
    "Name": "张三",
    "others": ""
  },
  "Success": false,
  "Reason": "地址信息无法完全确定，ExpAreaName存在多个候选值",
  "ResultCode": "103",
  "Warning": [
    "ExpAreaName存在3个无法确定的候选值"
  ]
}
```

### 示例3：解析失败（ResultCode: 102）

**请求**：
```json
{
  "Content": "无效地址信息"
}
```

**响应**：
```json
{
  "EBusinessID": "1279441",
  "Data": {
    "ProvinceName": "",
    "CityName": "",
    "ExpAreaName": "",
    "StreetName": "",
    "AreasInfo": "",
    "Address": "",
    "Mobile": "",
    "Name": "",
    "others": ""
  },
  "Success": false,
  "Reason": "无法解析",
  "ResultCode": "102",
  "Warning": [
    "ProvinceName在数据库中匹配失败，不存在于数据库中",
    "CityName在数据库中匹配失败，不存在于数据库中"
  ]
}
```

### 示例4：参数错误（ResultCode: 101）

**请求**：
```json
{
  "Content": ""
}
```

**响应**：
```json
{
  "EBusinessID": "1279441",
  "Data": {},
  "Success": false,
  "Reason": "Content字段不能为空",
  "ResultCode": "101",
  "Warning": []
}
```

---

## 注意事项

1. **模型加载时间**：首次使用时，需要加载模型到内存，可能需要几秒到几十秒的时间。模型加载后会缓存，后续请求会更快。

2. **内存占用**：MGeo模型会占用一定的内存，建议确保服务器有足够的内存。

3. **模型配置**：系统固定使用 `mgeo_geographic_composition_analysis_chinese_base` 模型，无需额外配置。模型文件会自动从 ModelScope 下载到项目的 `model/` 目录。

4. **文本长度**：建议单次处理的文本长度不超过模型的最大输入长度限制。

5. **地址字段格式**：
   - 成功匹配时：返回对象格式（包含id、parent_id、region_name、region_type）
   - 存在候选值时：返回候选信息格式（包含id列表、candidates等）
   - 匹配失败时：返回字符串格式（原始值或空字符串）

6. **日志记录**：系统会自动记录推理时间到日志文件（`logs/inference_YYYYMMDD.log`），无需额外配置。

7. **Redis缓存**：如果Redis连接失败，系统会自动降级为直接查询数据库，不影响功能正常运行。

8. **API使用统计**：系统会自动统计接口调用频次（使用Redis实时计数，定时任务同步到MySQL）和记录错误日志（直接写入MySQL）。详细说明请参考：[API统计与错误日志文档](./API_STATISTICS_AND_ERROR_LOG.md)

9. **并发处理**：当前版本为单线程处理，如需支持高并发，建议使用生产级WSGI服务器（如gunicorn）。

---

## 相关文档

- [API_DOC.md](./API_DOC.md) - 完整的API使用文档
- [API_STATISTICS_AND_ERROR_LOG.md](./API_STATISTICS_AND_ERROR_LOG.md) - API使用统计与错误日志说明
- [processor_mgeo/README.md](../src/processor_mgeo/README.md) - 地址补全的详细处理逻辑
- [映射关系说明.md](./映射关系说明.md) - 字段映射关系说明

---

## 更新日志

**最后更新**：2025-01-XX

**版本历史**：
- v1.3.0 (2025-01-06): 修正候选值格式说明（candidates列表中的元素应包含region_name字段），更新地址补全机制说明（三阶段处理流程），更新处理流程描述和状态码说明，修正文档链接
- v1.4.0 (2025-01-XX): 简化接口，移除model参数，固定使用mgeo_geographic_composition_analysis_chinese_base模型；移除mgeo_geographic_elements_tagging模型支持；废弃qwen-flash模型（保留代码）
- v1.2.0 (2025-01-XX): 更新状态码说明，修正状态码定义（101-请求参数错误，102-地理模型解析失败，103-地址无法完全确定），修正默认模型为mgeo_geographic_composition_analysis_chinese_base，修正EBusinessID说明，删除104状态码相关说明
- v1.1.0 (2025-12-30): 更新状态码说明，添加104状态码（第一阶段匹配失败但后续阶段成功），修正"降级"为"升级"描述
- v1.0.0 (2025-12-30): 初始版本，支持三种模型和地址匹配

