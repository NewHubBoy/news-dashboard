import httpx
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.news import NewsArticle
from app.models.schemas import NewsArticleResponse


class NewsService:
    def __init__(self):
        self.api_key = settings.google_news_api_key
        self.base_url = "https://serpapi.com/search.json"

    async def search_news(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[NewsArticleResponse]:
        """搜索股票相关新闻，支持备用搜索"""
        all_articles = []

        # 1. 尝试使用 SerpApi 搜索
        try:
            all_articles.extend(
                await self._search_google_news(stock_code, stock_name, db)
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print("SerpApi Key is unauthorized or expired, falling back.")
            else:
                print(f"SerpApi HTTP error: {e}")
        except Exception as e:
            print(f"SerpApi failed: {e}")

        # 2. 如果 SerpApi 没有结果或失败，使用备用搜索
        if not all_articles:
            all_articles.extend(
                await self._search_with_fallback(stock_code, stock_name, db)
            )

        # 3. 添加东方财富网爬虫数据
        eastmoney_articles = await self._search_eastmoney(stock_code, stock_name, db)
        all_articles.extend(eastmoney_articles)

        return all_articles

    async def _search_google_news(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[NewsArticleResponse]:
        """使用 SerpApi (Google News engine) 搜索"""
        if not self.api_key:
            raise ValueError("SerpApi API Key not configured")

        query = f"{stock_name} {stock_code} stock"

        params = {
            "engine": "google_news",
            "q": query,
            "api_key": self.api_key,
            "gl": "cn",
            "hl": "zh-cn",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        articles = []
        for article_data in data.get("news_results", []):
            source_info = article_data.get("source", {})
            source_name = (
                source_info.get("name")
                if isinstance(source_info, dict)
                else str(source_info)
            )

            article = NewsArticle(
                stock_code=stock_code,
                stock_name=stock_name,
                title=article_data.get("title", ""),
                description=article_data.get("snippet", ""),
                url=article_data.get("link", ""),
                source=source_name or "Google News",
                published_at=self._parse_date(article_data.get("date")),
            )

            db.add(article)
            articles.append(NewsArticleResponse.model_validate(article))

        db.commit()
        return articles

    async def _search_with_fallback(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[NewsArticleResponse]:
        """使用备用 Web 搜索方案"""
        from app.services.web_search_service import get_web_search_service

        web_search = get_web_search_service(use_simple=False)
        raw_articles = await web_search.search_stock_news(stock_code, stock_name)

        articles = []
        for article_data in raw_articles:
            article = NewsArticle(
                stock_code=stock_code,
                stock_name=stock_name,
                title=article_data.get("title", ""),
                description=article_data.get("description", ""),
                url=article_data.get("url", ""),
                source=article_data.get("source", "Web Search"),
                published_at=self._parse_date(article_data.get("published_at")),
            )

            db.add(article)
            articles.append(NewsArticleResponse.model_validate(article))

        db.commit()
        return articles

    def get_history(
        self, stock_code: str, db: Session, limit: int = 50
    ) -> List[NewsArticleResponse]:
        """获取历史搜索记录"""
        articles = (
            db.query(NewsArticle)
            .filter(NewsArticle.stock_code == stock_code)
            .order_by(NewsArticle.created_at.desc())
            .limit(limit)
            .all()
        )

        return [NewsArticleResponse.model_validate(article) for article in articles]

    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

    async def _search_eastmoney(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[NewsArticleResponse]:
        """使用东方财富网爬虫搜索新闻"""
        from app.services.eastmoney_scraper import eastmoney_scraper

        articles = []
        try:
            # 同时搜索新闻和网页
            news_results = await eastmoney_scraper.fetch_news(stock_code, limit=5)
            web_results = await eastmoney_scraper.fetch_web(stock_code, limit=5)

            # 合并结果
            for item in news_results + web_results:
                # 检查是否已存在（根据URL去重）
                existing = (
                    db.query(NewsArticle)
                    .filter(NewsArticle.url == item.get("url"))
                    .first()
                )
                if existing:
                    articles.append(NewsArticleResponse.model_validate(existing))
                    continue

                article = NewsArticle(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    source=item.get("source", "东方财富网"),
                    published_at=self._parse_date(item.get("published_at")),
                )

                db.add(article)
                articles.append(NewsArticleResponse.model_validate(article))

            db.commit()
        except Exception as e:
            print(f"Eastmoney scraper failed: {e}")

        return articles


news_service = NewsService()
