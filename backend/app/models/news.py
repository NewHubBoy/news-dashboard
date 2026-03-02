from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), index=True)
    stock_name = Column(String(100), index=True)
    title = Column(String(500))
    description = Column(Text)
    url = Column(String(1000))
    source = Column(String(200))
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class FinancialDocument(Base):
    """用于存储公告、披露、研报等信息"""

    __tablename__ = "financial_documents"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), index=True)
    stock_name = Column(String(100), index=True)
    doc_type = Column(
        String(50), index=True
    )  # "announcement", "disclosure", "report", "financial_data"
    title = Column(String(500))
    content_summary = Column(Text)
    url = Column(String(1000))
    source = Column(String(200))
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class AIAnalysisResult(Base):
    """存储 AI 分析缓存"""

    __tablename__ = "ai_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), index=True)
    stock_name = Column(String(100), index=True)
    analysis_content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
