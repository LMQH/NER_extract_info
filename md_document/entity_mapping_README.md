# 实体映射配置文件说明

## 概述

`entity_mapping.json` 文件用于管理 MGeo 模型标签到输出字段的映射关系。通过修改此配置文件，可以灵活调整实体类型与输出字段的对应关系，无需修改代码。

## 文件位置

- **默认位置**: 项目根目录下的 `entity_mapping.json`
- **自定义位置**: 可通过环境变量 `ENTITY_MAPPING_CONFIG` 指定配置文件路径

## 配置文件结构

```json
{
  "version": "1.0",
  "description": "MGeo模型标签到输出字段的映射关系配置",
  "mappings": {
    "字段名": {
      "entity_types": ["标签1", "标签2", ...],
      "description": "字段说明",
      "is_single_value": true/false,
      "default_for_unmapped": true/false  // 仅用于others字段
    }
  },
  "special_types": {
    "phone_extraction": {
      "entity_types": ["ZZ"],
      "description": "用于提取电话号码的未知类型"
    },
    "name_extraction": {
      "entity_types": ["ZZ"],
      "description": "用于提取姓名的未知类型"
    }
  },
  "address_range_types": {
    "description": "用于确定地址范围，排除这些范围后提取姓名",
    "entity_types": ["PB", "PC", ...]
  }
}
```

## 字段说明

### mappings（映射关系）

定义实体类型到输出字段的映射关系。

#### 字段属性

- **entity_types** (必需): 字符串数组，列出映射到此字段的所有实体类型标签
- **description** (可选): 字段描述说明
- **is_single_value** (必需): 布尔值
  - `true`: 单值字段，只取第一个匹配的实体（如 ProvinceName, CityName, ExpAreaName）
  - `false`: 多值字段，按位置顺序拼接所有匹配的实体（如 StreetName, AreasInfo, Address）
- **default_for_unmapped** (可选): 布尔值，仅用于 `others` 字段
  - `true`: 未映射的实体类型将归入此字段

#### 支持的输出字段

| 字段名 | 说明 | 单值/多值 |
|--------|------|----------|
| ProvinceName | 省份名称 | 单值 |
| CityName | 城市名称 | 单值 |
| ExpAreaName | 区县名称 | 单值 |
| StreetName | 街道名称 | 多值 |
| AreasInfo | 区域信息 | 多值 |
| Address | 详细地址 | 多值 |
| others | 其他信息 | 多值 |

### special_types（特殊类型）

定义用于特殊处理的实体类型。

- **phone_extraction**: 用于提取电话号码的实体类型（默认：ZZ）
- **name_extraction**: 用于提取姓名的实体类型（默认：ZZ）

### address_range_types（地址范围类型）

定义用于确定地址范围的实体类型列表。这些类型用于排除地址范围后提取姓名。

## 常用实体类型标签

### 省份/城市/区县
- `PB`: 省
- `PC`: 城市
- `PD`: 区县

### 街道相关
- `PF`: 街道
- `PG`: 村庄
- `PH`: 行政俗称/商圈
- `PS`: 其它行政

### 区域信息
- `BS`: 公交地铁站
- `BL`: 公交地铁线路
- `RD`: 道路
- `Brand`: 著名品牌
- `CategorySuffix`: 类别后缀词
- `SS`: 分支词
- `SA`: 方位修饰词
- `UD`: 门址附属描述
- `UE`: 门址东口、南门
- `YA`: 语义连接词

### 详细地址
- `UA`: 门址 道路xx号/xx弄
- `UB`: 门址 xx座楼/xx区
- `UC`: 门址 xx号楼/xx棟/xx幢
- `Entity`: POI一般名称
- `NumEng`: 数字英文串

### 其他
- `Yewu`: 业务词
- `Desc`: 修饰词
- `BD`: 标点符号
- `ZZ`: 未知类型（用于提取电话和姓名）

## 使用示例

### 示例1: 修改映射关系

将 `YA` 标签从 `AreasInfo` 移到 `Address`：

```json
{
  "mappings": {
    "AreasInfo": {
      "entity_types": ["BS", "BL", "RD", "Brand", "CategorySuffix", "SS", "SA", "UD", "UE"],
      "is_single_value": false
    },
    "Address": {
      "entity_types": ["UA", "UB", "UC", "Entity", "NumEng", "YA"],
      "is_single_value": false
    }
  }
}
```

### 示例2: 添加新的实体类型

将新的实体类型 `NEW_TYPE` 添加到 `AreasInfo`：

```json
{
  "mappings": {
    "AreasInfo": {
      "entity_types": ["BS", "BL", "RD", "Brand", "CategorySuffix", "SS", "SA", "UD", "UE", "YA", "NEW_TYPE"],
      "is_single_value": false
    }
  }
}
```

### 示例3: 自定义配置文件路径

通过环境变量指定配置文件路径：

```bash
# Linux/macOS
export ENTITY_MAPPING_CONFIG=/path/to/custom_mapping.json

# Windows
set ENTITY_MAPPING_CONFIG=C:\path\to\custom_mapping.json
```

## 配置验证

系统在启动时会自动验证配置文件：

1. **文件不存在**: 使用默认配置，记录信息日志
2. **JSON格式错误**: 使用默认配置，记录错误日志
3. **缺少必需字段**: 使用默认配置，记录警告日志
4. **配置有效**: 使用JSON配置，记录成功日志

## 默认配置

如果配置文件不存在或格式错误，系统将使用以下默认配置：

- **ProvinceName**: `["PB"]`
- **CityName**: `["PC"]`
- **ExpAreaName**: `["PD"]`
- **StreetName**: `["PF", "PG", "PH", "PS"]`
- **AreasInfo**: `["BS", "BL", "RD", "Brand", "CategorySuffix", "SS", "SA", "UD", "UE", "YA"]`
- **Address**: `["UA", "UB", "UC", "Entity", "NumEng"]`
- **others**: `["Yewu", "Desc", "BD"]` (default_for_unmapped: true)

## 注意事项

1. **配置文件格式**: 必须是有效的JSON格式
2. **字段顺序**: 多值字段会按实体在文本中的位置顺序（`start`字段）拼接
3. **单值字段**: 只取第一个匹配的实体，后续同类型实体会被忽略
4. **未映射类型**: 如果 `others` 字段设置了 `default_for_unmapped: true`，未映射的实体类型会自动归入 `others`
5. **配置热重载**: 当前版本不支持热重载，修改配置后需要重启应用
6. **向后兼容**: 如果配置文件不存在，系统会自动使用默认配置，确保向后兼容

## 相关文件

- 配置加载器: `src/config/entity_mapping_loader.py`
- 转换函数: `src/processors/converters.py`
- 映射关系文档: `md_document/映射关系说明.md`

## 故障排查

### 问题1: 配置未生效

**可能原因**:
- JSON格式错误
- 配置文件路径不正确
- 应用未重启

**解决方法**:
1. 检查JSON格式是否正确（可使用在线JSON验证工具）
2. 查看日志确认配置文件是否成功加载
3. 重启应用

### 问题2: 某些实体类型未映射

**可能原因**:
- 实体类型未在配置文件中定义
- `others` 字段未设置 `default_for_unmapped: true`

**解决方法**:
1. 在配置文件中添加该实体类型到相应字段
2. 或确保 `others` 字段设置了 `default_for_unmapped: true`

### 问题3: 配置加载失败

**解决方法**:
1. 检查文件权限
2. 检查文件编码（应为UTF-8）
3. 查看应用日志获取详细错误信息

---

**最后更新**: 2024年

