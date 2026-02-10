# Redis 管理脚本使用说明

本目录包含用于管理 Redis Docker 容器的便捷脚本，支持 Windows 和 Linux 系统。

## 📋 脚本列表

| 脚本文件 | 功能说明 | 适用系统 |
|---------|---------|---------|
| `start_redis.sh` / `start_redis.cmd` | 启动 Redis 容器 | Linux / Windows |
| `stop_redis.sh` / `stop_redis.cmd` | 停止 Redis 容器 | Linux / Windows |
| `remove_redis.sh` / `remove_redis.cmd` | 删除 Redis 容器和数据卷 | Linux / Windows |

## 🚀 快速开始

### 前置要求

- 已安装 Docker 和 Docker Compose
- Docker 服务正在运行

### Windows 系统

1. **启动 Redis**
   ```cmd
   redis_command\start_redis.cmd
   ```
   或双击 `start_redis.cmd` 文件

2. **停止 Redis**
   ```cmd
   redis_command\stop_redis.cmd
   ```
   或双击 `stop_redis.cmd` 文件

3. **删除 Redis（包括数据）**
   ```cmd
   redis_command\remove_redis.cmd
   ```
   或双击 `remove_redis.cmd` 文件

### Linux / macOS 系统

1. **启动 Redis**
   ```bash
   chmod +x redis_command/start_redis.sh
   ./redis_command/start_redis.sh
   ```

2. **停止 Redis**
   ```bash
   chmod +x redis_command/stop_redis.sh
   ./redis_command/stop_redis.sh
   ```

3. **删除 Redis（包括数据）**
   ```bash
   chmod +x redis_command/remove_redis.sh
   ./redis_command/remove_redis.sh
   ```

## ⚙️ 配置说明

### 默认配置

脚本使用以下默认配置：

- **容器名称**: `local-redis`
- **镜像版本**: `redis:7`
- **端口映射**: `6379:6379`（主机端口:容器端口）
- **数据卷**: `redis-data`（持久化存储）
- **持久化**: 启用 AOF（Append Only File）

### 修改配置

如需修改配置，请编辑对应的脚本文件，修改以下变量：

**Windows (.cmd 文件)**
```cmd
set CONTAINER_NAME=local-redis
set IMAGE_NAME=redis:7
set PORT=6379
```

**Linux (.sh 文件)**
```bash
CONTAINER_NAME="local-redis"
IMAGE_NAME="redis:7"
PORT=6379
```

## 📝 功能详解

### 1. 启动 Redis (`start_redis`)

**功能**：
- 检查 Docker 是否运行
- 如果容器已存在，则启动它
- 如果容器不存在，则创建新容器并启动
- 自动启用 AOF 持久化

**使用场景**：
- 首次启动 Redis
- 重启已停止的 Redis 容器

### 2. 停止 Redis (`stop_redis`)

**功能**：
- 检查 Docker 是否运行
- 停止运行中的 Redis 容器
- 数据不会丢失（已持久化到数据卷）

**使用场景**：
- 临时停止 Redis 服务
- 系统维护

### 3. 删除 Redis (`remove_redis`)

**功能**：
- 停止运行中的容器
- 删除 Redis 容器
- 删除 Redis 数据卷（**所有数据将被永久删除**）

**使用场景**：
- 完全清理 Redis 环境
- 重新初始化 Redis

⚠️ **警告**: 此操作会永久删除所有 Redis 数据，请谨慎使用！

## 🔍 验证 Redis 运行状态

### 检查容器状态

```bash
# 查看运行中的容器
docker ps | grep local-redis

# 查看所有容器（包括已停止的）
docker ps -a | grep local-redis
```

### 测试 Redis 连接

```bash
# 使用 redis-cli 连接（需要安装 Redis 客户端）
redis-cli -h localhost -p 6379 ping

# 或使用 Docker 执行
docker exec -it local-redis redis-cli ping
```

如果返回 `PONG`，说明 Redis 运行正常。

## 🛠️ 常见问题

### 1. Docker 未运行

**错误信息**: `Docker is not running. Please start Docker Desktop.`

**解决方法**:
- Windows: 启动 Docker Desktop
- Linux: 启动 Docker 服务
  ```bash
  sudo systemctl start docker
  ```

### 2. 端口已被占用

**错误信息**: `Error: bind: address already in use`

**解决方法**:
- 检查端口占用: `netstat -ano | findstr 6379` (Windows) 或 `lsof -i :6379` (Linux)
- 修改脚本中的 `PORT` 变量为其他端口（如 6380）
- 或停止占用端口的其他服务

### 3. 容器名称冲突

**错误信息**: `Error: container name "local-redis" is already in use`

**解决方法**:
- 使用 `remove_redis` 脚本删除现有容器
- 或修改脚本中的 `CONTAINER_NAME` 变量

### 4. 权限问题（Linux）

**错误信息**: `Permission denied`

**解决方法**:
```bash
chmod +x redis_command/*.sh
```

## 📊 数据持久化

Redis 数据存储在 Docker 数据卷 `redis-data` 中，即使容器被删除，数据卷仍然保留。只有使用 `remove_redis` 脚本才会删除数据卷。

### 查看数据卷

```bash
docker volume ls | grep redis-data
```

### 手动备份数据卷

```bash
# 创建备份
docker run --rm -v redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .
```

## 🔗 项目集成

Redis 配置应与项目环境变量匹配：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600
```

确保项目的 `.env` 文件或环境变量中包含上述配置。

## 📚 相关资源

- [Redis 官方文档](https://redis.io/documentation)
- [Docker 官方文档](https://docs.docker.com/)
- [Redis Docker 镜像](https://hub.docker.com/_/redis)

## 📄 许可证

本脚本为项目内部工具，遵循项目主许可证。

---

**最后更新**: 2024年

