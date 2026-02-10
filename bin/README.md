# 启动和停止脚本说明

本目录包含了 NER Demo API 服务的启动和停止脚本。

## 脚本文件

- **start.sh** - 前台启动脚本（开发模式，支持热重载）
- **start_background.sh** - 后台启动脚本（生产模式）
- **stop.sh** - 停止脚本

## 使用方法

### 1. 前台启动（开发模式）

适合开发和调试，支持代码热重载，日志直接输出到控制台：

```bash
cd bin
./start.sh
```

或者：

```bash
bash bin/start.sh
```

**特点**：
- 服务在前台运行
- 支持代码热重载（修改代码后自动重启）
- 日志直接显示在终端
- 使用 `Ctrl+C` 可以停止服务

### 2. 后台启动（生产模式）

适合生产环境，服务在后台运行：

```bash
cd bin
./start_background.sh
```

或者：

```bash
bash bin/start_background.sh
```

**特点**：
- 服务在后台运行，不占用终端
- 日志输出到 `logs/app.log` 文件
- PID 保存在 `ner_demo.pid` 文件
- 适合生产环境部署

### 3. 停止服务

停止正在运行的服务：

```bash
cd bin
./stop.sh
```

或者：

```bash
bash bin/stop.sh
```

**说明**：
- 脚本会先尝试优雅停止（SIGTERM信号）
- 如果10秒内未能停止，会强制停止（SIGKILL信号）
- 自动清理 PID 文件

## 脚本功能

### start.sh（前台启动）

- ✅ 自动检测项目根目录
- ✅ 检查 Python 环境
- ✅ 检查 uvicorn 模块
- ✅ 检查端口占用
- ✅ 显示启动信息
- ✅ 支持代码热重载

### start_background.sh（后台启动）

- ✅ 自动检测项目根目录
- ✅ 检查 Python 环境
- ✅ 检查 uvicorn 模块
- ✅ 检查端口和 PID 文件
- ✅ 后台运行服务
- ✅ 保存 PID 到文件
- ✅ 日志输出到文件

### stop.sh（停止服务）

- ✅ 支持通过 PID 文件停止（后台模式）
- ✅ 支持通过端口查找停止（前台模式）
- ✅ 优雅停止（SIGTERM）
- ✅ 强制停止（SIGKILL，如果需要）
- ✅ 自动清理 PID 文件

## 端口说明

默认端口：**13110**

如果需要修改端口，请编辑脚本中的 `--port` 参数。

## 日志文件

- 前台模式：日志直接输出到终端
- 后台模式：日志保存在 `logs/app.log`
- 应用日志：保存在 `logs/inference_YYYYMMDD.log`（按日期）

查看后台日志：

```bash
tail -f logs/app.log
```

## 检查服务状态

### 检查端口占用

```bash
# 使用 lsof（Linux/Mac）
lsof -i:13110

# 使用 netstat（Linux）
netstat -tlnp | grep 13110

# 使用 ss（Linux）
ss -tlnp | grep 13110
```

### 检查进程

```bash
# 如果使用后台启动，检查 PID 文件
cat ner_demo.pid

# 查看进程
ps aux | grep uvicorn
```

## 常见问题

### 1. 权限错误

如果遇到权限错误，给脚本添加执行权限：

```bash
chmod +x bin/*.sh
```

### 2. 端口被占用

如果端口 13110 已被占用，可以：

1. 使用 `stop.sh` 停止现有服务
2. 或者修改脚本中的端口号

### 3. Python 命令不存在

确保已安装 Python 3，并且 `python3` 命令可用。某些系统可能需要使用 `python` 而不是 `python3`。

### 4. Windows 系统

这些脚本是为 Linux/Mac 设计的。在 Windows 上：

- 使用 WSL（Windows Subsystem for Linux）
- 使用 Git Bash
- 或直接使用 `python app.py` 启动服务

## 注意事项

1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 确保已配置环境变量文件（`.env` 或 `dev.env`）
3. 确保有足够的系统资源运行模型
4. 生产环境建议使用 `start_background.sh` 后台运行

