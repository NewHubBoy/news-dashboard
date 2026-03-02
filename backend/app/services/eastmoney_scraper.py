import asyncio
from typing import List, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright
import traceback


class EastMoneyScraper:
    """东方财富网无头浏览器爬虫"""

    async def fetch_news(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        url = f"https://so.eastmoney.com/news/s?keyword={keyword}"
        return await self._scrape_page(url, "div.news_item", limit, is_news=True)

    async def fetch_web(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        url = f"https://so.eastmoney.com/web/s?keyword={keyword}"
        return await self._scrape_page(
            url, "div.news_item", limit, is_news=False
        )

    async def _scrape_page(
        self, url: str, selector: str, limit: int, is_news: bool
    ) -> List[Dict[str, Any]]:
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 设置超时并将路由阻止以加快图片等静态加载
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort()
                )
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                try:
                    await page.wait_for_selector(selector, timeout=8000)
                    items = await page.locator(selector).all()

                    for item in items[:limit]:
                        try:
                            # Both news and web search use the same structure
                            title_loc = item.locator(".news_item_t a")
                            time_loc = item.locator(".news_item_time")
                            content_loc = item.locator(".news_item_c span:not(.news_item_time)")

                            title = ""
                            content = ""
                            pub_time = datetime.now().isoformat()

                            # Extract title
                            if await title_loc.count() > 0:
                                title = await title_loc.text_content()

                            # Extract content
                            if await content_loc.count() > 0:
                                content = await content_loc.text_content()

                            # Extract timestamp
                            if await time_loc.count() > 0:
                                time_text = await time_loc.text_content()
                                # Extract timestamp before " - "
                                if " - " in time_text:
                                    pub_time = time_text.split(" - ")[0].strip()
                                else:
                                    pub_time = time_text.strip()

                            # Extract article URL
                            article_url = url
                            link_loc = item.locator(".news_item_t a")
                            if await link_loc.count() > 0:
                                href = await link_loc.get_attribute("href")
                                if href:
                                    article_url = href

                            results.append(
                                {
                                    "title": title.strip()[:100] if title else "",
                                    "description": (
                                        content.strip()[:200] if content else ""
                                    ),
                                    "url": article_url,
                                    "source": "东方财富网",
                                    "published_at": (
                                        pub_time.strip()
                                        if pub_time
                                        else datetime.now().isoformat()
                                    ),
                                    "image_url": None,
                                }
                            )
                        except Exception as inner_e:
                            print(f"Eastmoney inner parse error: {inner_e}")

                except Exception as wait_e:
                    print(f"Eastmoney did not find elements {selector}: {wait_e}")

                await browser.close()
        except Exception as e:
            print(f"Eastmoney scraper failed for {url}")
            print(traceback.format_exc())

        return results


eastmoney_scraper = EastMoneyScraper()
