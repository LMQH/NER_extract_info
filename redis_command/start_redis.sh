#!/bin/bash

CONTAINER_NAME="local-redis"
IMAGE_NAME="redis:7"
PORT=6379

echo "=============================="
echo " Starting Redis via Docker"
echo "=============================="

# 检查 Docker 是否可用
if ! docker version >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker."
    exit 1
fi

# 检查容器是否已存在
if docker ps -a --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "Redis container already exists. Starting it..."
    docker start "$CONTAINER_NAME"
else
    echo "Redis container not found. Creating a new one..."
    docker run -d \
      --name "$CONTAINER_NAME" \
      -p ${PORT}:6379 \
      -v redis-data:/data \
      "$IMAGE_NAME" \
      redis-server --appendonly yes
fi

echo
echo "Redis is running at localhost:${PORT}"
