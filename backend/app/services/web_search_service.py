"""
Web Search Service - 备用新闻搜索服务
当 Google News API 不可用时使用
"""

import httpx
from typing import List, Dict, Any
from datetime import datetime
from app.config import settings


class WebSearchService:
    """Web 搜索服务，作为 Google News API 的备用方案"""

    def __init__(self):
        self.brave_api_url = "https://api.search.brave.com/res/v1/web/search"
        self.brave_api_key = settings.brave_api_key

    async def search_stock_news(
        self, stock_code: str, stock_name: str, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        使用 Web 搜索查找股票相关新闻

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            max_results: 最大结果数

        Returns:
            新闻文章列表
        """
        # 构建搜索查询
        query = self._build_search_query(stock_code, stock_name)

        # 如果配置了 Brave API，使用 Brave Search
        if self.brave_api_key:
            try:
                results = await self._brave_search(query, max_results)
                return self._format_brave_results(results)
            except Exception as e:
                import traceback

                print(f"Brave Search failed for query '{query}': {e}")
                print(traceback.format_exc())

        # 否则返回模拟结果
        return self._get_mock_results(stock_code, stock_name)

    def _build_search_query(self, stock_code: str, stock_name: str) -> str:
        """构建搜索查询字符串"""
        query_parts = []

        if stock_name:
            query_parts.append(stock_name)
        if stock_code:
            query_parts.append(stock_code)

        # 添加新闻相关关键词
        query_parts.extend(["新闻", "资讯"])

        return " ".join(query_parts)

    async def _brave_search(self, query: str, count: int) -> Dict[str, Any]:
        """使用 Brave Search API 进行搜索"""
        async with httpx.AsyncClient() as client:
            params = {
                "q": query,
                "count": count,
                "search_lang": "zh-hans",
                "country": "cn",
                "freshness": "pw",  # past week
            }

            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key,
            }

            response = await client.get(
                self.brave_api_url, params=params, headers=headers, timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    def _format_brave_results(
        self, raw_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """格式化 Brave Search 结果"""
        articles = []
        web_results = raw_results.get("web", {}).get("results", [])

        for result in web_results:
            article = {
                "title": result.get("title", ""),
                "description": result.get("description", ""),
                "url": result.get("url", ""),
                "source": self._extract_domain(result.get("url", "")),
                "published_at": result.get("age", ""),
                "image_url": (
                    result.get("thumbnail", {}).get("src")
                    if result.get("thumbnail")
                    else None
                ),
            }
            articles.append(article)

        return articles

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名作为来源"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "Unknown"

    def _get_mock_results(
        self, stock_code: str, stock_name: str
    ) -> List[Dict[str, Any]]:
        """返回模拟搜索结果（用于开发测试）"""
        return [
            {
                "title": f"{stock_name}({stock_code}) 最新资讯 - 示例新闻",
                "description": "这是备用搜索返回的示例结果。建议配置 Google News API Key 或 Brave Search API Key 以获取真实新闻数据。",
                "url": f"https://example.com/news/{stock_code}",
                "source": "备用搜索",
                "published_at": datetime.now().isoformat(),
                "image_url": None,
            }
        ]


class SimpleWebSearchService:
    """
    简化版 Web 搜索服务
    不需要 API Key，返回模拟数据用于开发测试
    """

    async def search_stock_news(
        self, stock_code: str, stock_name: str, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """返回模拟搜索结果"""
        return [
            {
                "title": f"{stock_name}({stock_code}) - 最新市场动态",
                "description": "这是备用搜索服务返回的示例新闻。建议配置 Google News API Key 以获取真实新闻数据。",
                "url": f"https://example.com/news/{stock_code}/1",
                "source": "示例来源",
                "published_at": datetime.now().isoformat(),
                "image_url": None,
            },
            {
                "title": f"{stock_name} 股价分析与展望",
                "description": "备用搜索服务提供的示例内容。配置真实 API 后将显示实际新闻。",
                "url": f"https://example.com/news/{stock_code}/2",
                "source": "示例来源",
                "published_at": datetime.now().isoformat(),
                "image_url": None,
            },
        ]


def get_web_search_service(use_simple: bool = True):
    """
    获取 Web 搜索服务实例

    Args:
        use_simple: 是否使用简化版（不需要 API Key）
    """
    if use_simple or not settings.brave_api_key:
        return SimpleWebSearchService()
    else:
        return WebSearchService()
