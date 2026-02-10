@echo off
set CONTAINER_NAME=local-redis
set IMAGE_NAME=redis:7
set PORT=6379

echo ==============================
echo Starting Redis via Docker
echo ==============================

:: 检查 Docker 是否可用
docker version >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

:: 检查容器是否已存在
docker ps -a --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Redis container already exists. Starting it...
    docker start %CONTAINER_NAME%
) else (
    echo Redis container not found. Creating a new one...
    docker run -d ^
      --name %CONTAINER_NAME% ^
      -p %PORT%:6379 ^
      -v redis-data:/data ^
      %IMAGE_NAME% ^
      redis-server --appendonly yes
)

echo.
echo Redis is running at localhost:%PORT%
pause
