#!/bin/bash

CONTAINER_NAME="local-redis"
VOLUME_NAME="redis-data"

echo "=================================="
echo " Removing Redis (Container + Data)"
echo "=================================="

# 检查 Docker 是否可用
if ! docker version >/dev/null 2>&1; then
    echo "Docker is not running."
    exit 1
fi

# 停止容器（如果在运行）
if docker ps --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "Stopping Redis container..."
    docker stop "$CONTAINER_NAME"
fi

# 删除容器（如果存在）
if docker ps -a --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "Removing Redis container..."
    docker rm "$CONTAINER_NAME"
else
    echo "Redis container not found."
fi

# 删除 volume（如果存在）
if docker volume ls --format '{{.Name}}' | grep -wq "$VOLUME_NAME"; then
    echo "Removing Redis data volume..."
    docker volume rm "$VOLUME_NAME"
else
    echo "Redis data volume not found."
fi

echo
echo "Redis has been completely removed."
