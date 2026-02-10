@echo off
set CONTAINER_NAME=local-redis
set VOLUME_NAME=redis-data

echo ==================================
echo Removing Redis (Container + Data)
echo ==================================

:: 检查 Docker 是否可用
docker version >nul 2>&1
if errorlevel 1 (
    echo Docker is not running.
    pause
    exit /b 1
)

:: 停止容器（如果存在）
docker ps --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Stopping Redis container...
    docker stop %CONTAINER_NAME%
)

:: 删除容器（如果存在）
docker ps -a --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Removing Redis container...
    docker rm %CONTAINER_NAME%
) else (
    echo Redis container not found.
)

:: 删除 volume（如果存在）
docker volume ls --format "{{.Name}}" | findstr /i "%VOLUME_NAME%" >nul
if not errorlevel 1 (
    echo Removing Redis data volume...
    docker volume rm %VOLUME_NAME%
) else (
    echo Redis data volume not found.
)

echo.
echo Redis has been completely removed.
pause
