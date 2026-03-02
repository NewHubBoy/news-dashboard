from sqlalchemy.orm import Session
from typing import List
from app.models.news import FinancialDocument
from app.models.schemas import FinancialDocumentResponse
from app.services.web_search_service import get_web_search_service
from datetime import datetime


class FinancialService:
    def __init__(self):
        self.limit_per_category = 5

    async def fetch_documents(
        self, stock_code: str, stock_name: str, doc_type: str, keyword: str, db: Session
    ) -> List[FinancialDocumentResponse]:
        """通用拉取特定类型文档的方法"""
        # 如果当日已有，避免频繁重复拉取
        today = datetime.now().date()
        recent_docs = (
            db.query(FinancialDocument)
            .filter(
                FinancialDocument.stock_code == stock_code,
                FinancialDocument.doc_type == doc_type,
                FinancialDocument.created_at >= today,
            )
            .all()
        )

        if recent_docs:
            print(f"Hit cache for {doc_type} of {stock_code}")
            return [
                FinancialDocumentResponse.model_validate(doc) for doc in recent_docs
            ]

        # 请求 Web 搜索获取
        web_search = get_web_search_service(use_simple=False)  # 尝试使用 Brave 或其他
        search_query_name = f"{stock_name} {stock_code} {keyword}"
        raw_results = await web_search.search_stock_news(
            stock_code, search_query_name, max_results=self.limit_per_category
        )

        documents = []
        for result in raw_results:
            doc = FinancialDocument(
                stock_code=stock_code,
                stock_name=stock_name,
                doc_type=doc_type,
                title=result.get("title", ""),
                content_summary=result.get("description", ""),
                url=result.get("url", ""),
                source=result.get("source", "Web Search"),
                published_at=self._parse_date(result.get("published_at")),
            )
            db.add(doc)
            documents.append(FinancialDocumentResponse.model_validate(doc))

        if documents:
            db.commit()

        return documents

    async def fetch_announcements(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[FinancialDocumentResponse]:
        return await self.fetch_documents(
            stock_code, stock_name, "announcement", "交易所 最新 公告", db
        )

    async def fetch_disclosures(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[FinancialDocumentResponse]:
        return await self.fetch_documents(
            stock_code, stock_name, "disclosure", "监管 披露", db
        )

    async def fetch_broker_reports(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[FinancialDocumentResponse]:
        return await self.fetch_documents(
            stock_code, stock_name, "report", "券商 研报 评级", db
        )

    async def fetch_market_data(
        self, stock_code: str, stock_name: str, db: Session
    ) -> List[FinancialDocumentResponse]:
        return await self.fetch_documents(
            stock_code, stock_name, "financial_data", "财报 业绩 分析", db
        )

    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None


financial_service = FinancialService()
