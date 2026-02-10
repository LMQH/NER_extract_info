-- 添加成功计数字段到API使用统计表
-- 执行时间: 执行后会自动添加字段，不影响现有数据
-- 说明: 为 extract_api_usage 表添加 success_count 字段用于统计成功的API调用次数

-- 检查并添加 success_count 字段
ALTER TABLE `extract_api_usage`
ADD COLUMN IF NOT EXISTS `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功调用次数'
AFTER `call_count`;

-- 验证字段是否添加成功
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'extract_api_usage'
  AND COLUMN_NAME = 'success_count';

-- 注意事项：
-- 1. 如果表名不同（通过 MYSQL_API_USAGE_TABLE 配置），请将 'extract_api_usage' 替换为实际的表名
-- 2. 该操作是幂等的，可以重复执行
-- 3. 添加字段后，现有记录的 success_count 默认值为 0
-- 4. 代码会自动检测并添加该字段，但手动执行可以确保字段立即生效
