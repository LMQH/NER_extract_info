#!/bin/bash

CONTAINER_NAME="local-redis"

echo "=============================="
echo " Stopping Redis via Docker"
echo "=============================="

# 检查 Docker 是否可用
if ! docker version >/dev/null 2>&1; then
    echo "Docker is not running."
    exit 1
fi

# 检查容器是否存在
if docker ps -a --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "Redis container found. Stopping it..."
    docker stop "$CONTAINER_NAME"
    echo "Redis stopped successfully."
else
    echo "Redis container not found. Nothing to stop."
fi
