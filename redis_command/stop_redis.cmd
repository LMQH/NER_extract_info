@echo off
set CONTAINER_NAME=local-redis

echo ==============================
echo Stopping Redis via Docker
echo ==============================

:: 检查 Docker 是否可用
docker version >nul 2>&1
if errorlevel 1 (
    echo Docker is not running.
    pause
    exit /b 1
)

:: 检查容器是否存在
docker ps -a --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Redis container found. Stopping it...
    docker stop %CONTAINER_NAME%
    echo Redis stopped successfully.
) else (
    echo Redis container not found. Nothing to stop.
)

pause
