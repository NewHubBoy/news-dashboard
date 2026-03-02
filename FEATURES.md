# 备用搜索功能说明

## 功能概述

本项目集成了多数据源新闻搜索功能，当主要的 Google News API 不可用时，会自动切换到备用搜索方案，确保系统始终能够返回结果。

## 搜索优先级

系统按以下优先级尝试获取新闻数据：

1. **Google News API** (主要数据源)
   - 最全面的新闻覆盖
   - 需要配置 `GOOGLE_NEWS_API_KEY`
   - 失败时自动降级到备用方案

2. **Brave Search API** (备用数据源)
   - 当 Google News API 不可用时启用
   - 需要配置 `BRAVE_API_KEY`
   - 提供 Web 搜索结果

3. **简化搜索服务** (开发测试)
   - 无需任何配置
   - 返回示例数据
   - 适合开发和测试环境

## 自动降级机制

```python
# 搜索流程
try:
    # 1. 尝试 Google News API
    articles = await search_google_news(stock_code, stock_name)
except Exception:
    # 2. 自动切换到备用搜索
    articles = await search_with_fallback(stock_code, stock_name)
```

## 配置方式

### 仅使用 Google News API
```env
GOOGLE_NEWS_API_KEY=your_newsapi_key
BRAVE_API_KEY=
```

### 使用 Google News + Brave 备用
```env
GOOGLE_NEWS_API_KEY=your_newsapi_key
BRAVE_API_KEY=your_brave_key
```

### 仅使用简化搜索（开发测试）
```env
GOOGLE_NEWS_API_KEY=
BRAVE_API_KEY=
```

## 实现细节

### 1. Web Search Service (`web_search_service.py`)

提供两种实现：

- **WebSearchService**: 使用 Brave Search API
- **SimpleWebSearchService**: 返回模拟数据

### 2. News Service (`news_service.py`)

主要搜索服务，包含：

- `search_news()`: 主搜索入口，自动处理降级
- `_search_google_news()`: Google News API 实现
- `_search_with_fallback()`: 备用搜索实现

### 3. 数据格式统一

所有数据源返回统一的格式：

```python
{
    "title": str,
    "description": str,
    "url": str,
    "source": str,
    "published_at": str,
    "image_url": Optional[str]
}
```

## 使用建议

### 开发环境
- 可以不配置任何 API Key
- 使用简化搜索服务快速开发

### 生产环境
- 必须配置 `GOOGLE_NEWS_API_KEY`
- 建议配置 `BRAVE_API_KEY` 作为备用
- 确保高可用性

## API 获取

### Google News API (NewsAPI.org)
1. 访问 https://newsapi.org/register
2. 注册账号
3. 获取 API Key
4. 免费版限制：100 请求/天

### Brave Search API
1. 访问 https://brave.com/search/api/
2. 申请 API 访问
3. 获取 API Key
4. 查看定价和限制

## 监控和日志

系统会在控制台输出搜索状态：

```
Google News API failed: [错误信息]
使用备用搜索服务...
```

建议在生产环境配置日志系统监控 API 失败情况。
