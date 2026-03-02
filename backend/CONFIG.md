# Backend Configuration

## 环境变量说明

### 数据库配置
- `DATABASE_URL`: PostgreSQL 数据库连接字符串
  - 格式: `postgresql://用户名:密码@主机:端口/数据库名`
  - 示例: `postgresql://newsuser:newspass@localhost:5432/newsdb`

### API 配置
- `GOOGLE_NEWS_API_KEY`: Google News API 密钥（可选）
  - 获取地址: https://newsapi.org/register
  - 如果不配置，系统会自动使用备用搜索方案

### CORS 配置
- `CORS_ORIGINS`: 允许的跨域来源
  - 开发环境: `http://localhost:3000`
  - 生产环境: 添加你的域名

## 备用搜索方案

当 Google News API 不可用时（未配置 API Key 或请求失败），系统会自动切换到备用搜索方案：

1. **Web Search Service**: 使用通用 Web 搜索引擎
2. **Simple Search Service**: 简化版搜索（开发测试用）

### 配置备用搜索

如果需要使用 Brave Search API 作为备用方案：

```env
BRAVE_API_KEY=your_brave_api_key_here
```

获取 Brave Search API Key: https://brave.com/search/api/

## 完整配置示例

```env
# 数据库
DATABASE_URL=postgresql://newsuser:newspass@localhost:5432/newsdb

# 主搜索 API（推荐）
GOOGLE_NEWS_API_KEY=your_newsapi_key_here

# 备用搜索 API（可选）
BRAVE_API_KEY=your_brave_api_key_here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 其他配置
DEBUG=True
LOG_LEVEL=INFO
```

## 搜索优先级

1. Google News API（如果配置了 API Key）
2. Brave Search API（如果配置了 API Key）
3. Simple Search Service（始终可用，但结果有限）

系统会自动按优先级尝试，确保始终能返回结果。
