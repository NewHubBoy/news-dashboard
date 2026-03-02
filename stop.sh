#!/bin/bash

echo "🛑 停止所有服务..."

# 停止后端
pkill -f "uvicorn app.main:app"

# 停止前端
pkill -f "next dev"

# 停止数据库
docker-compose down

echo "✅ 所有服务已停止"
