from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class StockSearchRequest(BaseModel):
    stock_code: str
    stock_name: str


class NewsArticleResponse(BaseModel):
    id: Optional[int] = None
    stock_code: str
    stock_name: str
    title: str
    description: Optional[str] = None
    url: str
    source: str
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsSearchResponse(BaseModel):
    articles: list[NewsArticleResponse]
    total: int


class FinancialDocumentResponse(BaseModel):
    id: Optional[int] = None
    stock_code: str
    stock_name: str
    doc_type: str
    title: str
    content_summary: Optional[str] = None
    url: str
    source: str
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IntegratedSearchResponse(BaseModel):
    articles: list[NewsArticleResponse]
    announcements: list[FinancialDocumentResponse]
    disclosures: list[FinancialDocumentResponse]
    reports: list[FinancialDocumentResponse]
    financial_data: list[FinancialDocumentResponse]
    total_news: int


class AgentAnalyzeRequest(BaseModel):
    stock_code: str
    stock_name: str
    articles: list[NewsArticleResponse]
    announcements: list[FinancialDocumentResponse]
    disclosures: list[FinancialDocumentResponse]
    reports: list[FinancialDocumentResponse]
    financial_data: list[FinancialDocumentResponse]
    bypass_cache: bool = False


class AgentAnalyzeResponse(BaseModel):
    analysis_result: str
    cached: bool = False
