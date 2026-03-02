#!/bin/bash

set -e

echo "🚀 股票新闻资讯看板 - Docker 部署脚本"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 检查 Docker Compose 版本
if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 检查 .env 文件
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env.production 文件${NC}"
    echo "📝 从 .env.production.example 创建 .env.production 文件..."
    cp .env.production.example .env.production
    echo -e "${YELLOW}⚠️  请编辑 .env.production 文件，填入正确的配置！${NC}"
    echo ""
    echo "编辑完成后，再次运行此脚本继续部署。"
    exit 1
fi

# 加载环境变量
export $(cat .env.production | grep -v '^#' | xargs)

# 询问用户是否使用 Nginx
echo ""
read -p "是否使用 Nginx 反向代理？(y/n) [默认: n]: " use_nginx
use_nginx=${use_nginx:-n}

# 构建镜像
echo ""
echo "📦 构建 Docker 镜像..."
echo "======================================"

echo "🐍 构建 Backend 镜像..."
$DOCKER_COMPOSE -f docker-compose.prod.yml build backend

echo "⚛️  构建 Frontend 镜像..."
$DOCKER_COMPOSE -f docker-compose.prod.yml build frontend

if [ "$use_nginx" = "y" ]; then
    echo "🌐 使用 Nginx 反向代理模式"
    PROFILE="--profile with-nginx"
    echo "   访问地址: http://localhost:${NGINX_PORT:-80}"
else
    echo "🔧 使用独立端口模式"
    PROFILE=""
    echo "   前端: http://localhost:3000"
    echo "   后端: http://localhost:8000"
fi

# 启动服务
echo ""
echo "🚀 启动服务..."
echo "======================================"

# 停止旧容器
$DOCKER_COMPOSE -f docker-compose.prod.yml down

# 启动新容器
$DOCKER_COMPOSE -f docker-compose.prod.yml $PROFILE up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态:"
echo "======================================"
$DOCKER_COMPOSE -f docker-compose.prod.yml ps

# 运行数据库迁移（如果需要）
echo ""
echo "🗄️  运行数据库迁移..."
$DOCKER_COMPOSE -f docker-compose.prod.yml exec -T backend python -c "
from app.db.database import engine
from app.models.news import Base
import asyncio
Base.metadata.create_all(bind=engine)
print('✅ 数据库表创建成功')
" 2>/dev/null || echo "⚠️  数据库迁移跳过（可能已完成）"

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "📍 访问地址:"

if [ "$use_nginx" = "y" ]; then
    echo "   应用: http://localhost:${NGINX_PORT:-80}"
    echo "   API: http://localhost:${NGINX_PORT:-80}/api/"
    echo "   API 文档: http://localhost:${NGINX_PORT:-80}/docs"
else
    echo "   前端: http://localhost:3000"
    echo "   后端 API: http://localhost:8000/docs"
fi

echo ""
echo "📝 常用命令:"
echo "   查看日志: $DOCKER_COMPOSE -f docker-compose.prod.yml logs -f"
echo "   停止服务: $DOCKER_COMPOSE -f docker-compose.prod.yml down"
echo "   重启服务: $DOCKER_COMPOSE -f docker-compose.prod.yml restart"
echo ""
