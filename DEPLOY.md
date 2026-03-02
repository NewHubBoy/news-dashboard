# Docker 部署指南

本项目支持使用 Docker 和 Docker Compose 进行一键部署。

## 前置要求

- Docker (20.10+)
- Docker Compose (2.0+)

## 快速部署

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑配置文件，填入必要的配置
vim .env.production
```

### 2. 一键部署

```bash
# 运行部署脚本
./deploy.sh
```

部署脚本会：
1. 检查 Docker 环境
2. 构建 Docker 镜像
3. 启动所有服务
4. 运行数据库迁移

### 3. 访问应用

- **使用 Nginx 代理** (推荐): `http://localhost`
- **独立端口**:
  - 前端: `http://localhost:3000`
  - 后端: `http://localhost:8000`

## 手动部署

如果你想手动控制部署流程：

```bash
# 1. 构建镜像
docker compose -f docker-compose.prod.yml build

# 2. 启动服务
docker compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 4. 查看服务状态
docker compose -f docker-compose.prod.yml ps
```

## 配置说明

### 环境变量 (.env.production)

```bash
# 数据库配置
POSTGRES_USER=newsuser              # 数据库用户名
POSTGRES_PASSWORD=your_password     # 数据库密码（请修改）
POSTGRES_DB=newsdb                  # 数据库名

# API Keys（可选）
GOOGLE_NEWS_API_KEY=xxx             # SerpApi API Key
BRAVE_API_KEY=xxx                   # Brave Search API Key

# AI 配置
OPENAI_API_KEY=xxx                  # OpenAI API Key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini          # 模型名称

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:8000

# Nginx 端口
NGINX_PORT=80                       # Nginx 监听端口
```

## 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                         Nginx (可选)                     │
│                      Port 80                             │
└─────────────────────────────────────────────────────────┘
                    │                   │
        ┌───────────┘                   └───────────┐
        ▼                                           ▼
┌───────────────┐                           ┌───────────────┐
│    Frontend   │                           │    Backend    │
│  Next.js App  │                           │   FastAPI     │
│   Port 3000   │                           │   Port 8000   │
└───────────────┘                           └───────────────┘
                                                     │
                                             ┌───────┘
                                             ▼
                                      ┌───────────────┐
                                      │   PostgreSQL  │
                                      │   Port 5432   │
                                      └───────────────┘
```

## 常用命令

```bash
# 查看所有容器状态
docker compose -f docker-compose.prod.yml ps

# 查看实时日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 停止并删除数据卷
docker compose -f docker-compose.prod.yml down -v

# 重新构建并启动
docker compose -f docker-compose.prod.yml up -d --build

# 进入后端容器
docker compose -f docker-compose.prod.yml exec backend bash

# 进入数据库
docker compose -f docker-compose.prod.yml exec postgres psql -U newsuser -d newsdb
```

## 数据备份

### 备份数据库

```bash
# 创建备份
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U newsuser newsdb > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复数据库

```bash
# 从备份恢复
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U newsuser -d newsdb
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并部署
docker compose -f docker-compose.prod.yml up -d --build

# 或使用部署脚本
./deploy.sh
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs

# 检查端口占用
netstat -tulpn | grep -E '(3000|8000|80|5432)'
```

### 数据库连接失败

```bash
# 检查数据库是否就绪
docker compose -f docker-compose.prod.yml exec postgres \
  pg_isready -U newsuser

# 查看数据库日志
docker compose -f docker-compose.prod.yml logs postgres
```

### 清理并重新部署

```bash
# 停止并删除所有容器和数据卷
docker compose -f docker-compose.prod.yml down -v

# 清理悬空镜像
docker image prune

# 重新部署
./deploy.sh
```

## 服务器部署建议

### 1. 使用 Nginx 反向代理

推荐使用 Nginx 模式部署，统一端口管理：

```bash
./deploy.sh
# 选择 y 使用 Nginx
```

### 2. 配置域名

编辑 `nginx.conf`，修改 `server_name`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名
    ...
}
```

### 3. 配置 HTTPS (可选)

使用 Certbot 获取免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com
```

### 4. 设置防火墙

```bash
# 开放 HTTP 端口
sudo ufw allow 80/tcp

# 开放 HTTPS 端口
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 5. 设置自动重启

Docker Compose 已配置 `restart: unless-stopped`，服务会自动重启。

## 性能优化

### 1. 限制容器资源

在 `docker-compose.prod.yml` 中添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### 2. 配置数据库缓存

优化 PostgreSQL 配置以提高性能。

### 3. 使用 CDN

将静态资源托管到 CDN，减轻服务器压力。

## 监控

### 查看容器资源使用

```bash
docker stats
```

### 查看服务健康状态

```bash
docker compose -f docker-compose.prod.yml ps
```

## 支持

如有问题，请查看：
- 项目 Issues
- API 文档: http://localhost:8000/docs
