from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.schemas import (
    StockSearchRequest,
    NewsSearchResponse,
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
)
from app.services.news_service import news_service
from app.services.agent_service import agent_service

from app.services.financial_service import financial_service
from app.models.schemas import IntegratedSearchResponse

router = APIRouter(prefix="/api", tags=["news"])


@router.post("/search", response_model=IntegratedSearchResponse)
async def search_stock_data(request: StockSearchRequest, db: Session = Depends(get_db)):
    """综合搜索股票相关新闻、公告、研报等"""
    try:
        articles = await news_service.search_news(
            stock_code=request.stock_code, stock_name=request.stock_name, db=db
        )
        announcements = await financial_service.fetch_announcements(
            request.stock_code, request.stock_name, db
        )
        disclosures = await financial_service.fetch_disclosures(
            request.stock_code, request.stock_name, db
        )
        reports = await financial_service.fetch_broker_reports(
            request.stock_code, request.stock_name, db
        )
        financial_data = await financial_service.fetch_market_data(
            request.stock_code, request.stock_name, db
        )

        return IntegratedSearchResponse(
            articles=articles,
            announcements=announcements,
            disclosures=disclosures,
            reports=reports,
            financial_data=financial_data,
            total_news=len(articles),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/{stock_code}", response_model=NewsSearchResponse)
def get_stock_news_history(stock_code: str, db: Session = Depends(get_db)):
    """获取股票新闻历史记录"""
    articles = news_service.get_history(stock_code=stock_code, db=db)
    return NewsSearchResponse(articles=articles, total=len(articles))


@router.get("/stocks")
def get_all_searched_stocks(db: Session = Depends(get_db)):
    """获取所有已搜索过的股票列表"""
    from app.models.news import NewsArticle
    from sqlalchemy import func

    # 获取所有搜索过的股票，按最新搜索时间排序
    stocks = (
        db.query(
            NewsArticle.stock_code,
            NewsArticle.stock_name,
            func.max(NewsArticle.created_at).label("last_searched"),
        )
        .group_by(NewsArticle.stock_code, NewsArticle.stock_name)
        .order_by(func.max(NewsArticle.created_at).desc())
        .all()
    )

    return [
        {
            "stock_code": stock.stock_code,
            "stock_name": stock.stock_name,
            "last_searched": stock.last_searched.isoformat() if stock.last_searched else None,
        }
        for stock in stocks
    ]


@router.get("/history/{stock_code}", response_model=IntegratedSearchResponse)
async def get_stock_full_history(stock_code: str, db: Session = Depends(get_db)):
    """获取股票完整历史数据（新闻、公告、研报、财务数据）"""
    from app.models.news import NewsArticle, FinancialDocument

    # 获取股票名称
    first_article = (
        db.query(NewsArticle)
        .filter(NewsArticle.stock_code == stock_code)
        .first()
    )
    stock_name = first_article.stock_name if first_article else stock_code

    # 获取所有历史数据
    articles = news_service.get_history(stock_code=stock_code, db=db)

    # 获取财务文档
    financial_docs = (
        db.query(FinancialDocument)
        .filter(FinancialDocument.stock_code == stock_code)
        .order_by(FinancialDocument.created_at.desc())
        .all()
    )

    # 分类财务文档
    announcements = []
    disclosures = []
    reports = []
    financial_data = []

    for doc in financial_docs:
        if doc.doc_type == "announcement":
            announcements.append(doc)
        elif doc.doc_type == "disclosure":
            disclosures.append(doc)
        elif doc.doc_type == "report":
            reports.append(doc)
        elif doc.doc_type == "financial_data":
            financial_data.append(doc)

    return IntegratedSearchResponse(
        articles=articles,
        announcements=announcements,
        disclosures=disclosures,
        reports=reports,
        financial_data=financial_data,
        total_news=len(articles),
    )


@router.get("/analysis/{stock_code}")
def get_stock_analysis(stock_code: str, db: Session = Depends(get_db)):
    """获取股票历史分析结果"""
    from app.models.news import AIAnalysisResult
    from datetime import datetime, timedelta

    # 获取最近7天的分析结果
    seven_days_ago = datetime.now() - timedelta(days=7)
    analysis = (
        db.query(AIAnalysisResult)
        .filter(
            AIAnalysisResult.stock_code == stock_code,
            AIAnalysisResult.created_at >= seven_days_ago,
        )
        .order_by(AIAnalysisResult.created_at.desc())
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this stock")

    return {
        "analysis_result": analysis.analysis_content,
        "created_at": analysis.created_at.isoformat(),
    }


@router.post("/agent/analyze", response_model=AgentAnalyzeResponse)
async def analyze_news_with_agent(
    request: AgentAnalyzeRequest, db: Session = Depends(get_db)
):
    """使用 AI Agent 分析新闻并给出建议(带缓存)"""
    try:
        from datetime import datetime
        from app.models.news import AIAnalysisResult

        # 只有在不绕过缓存时才检查缓存
        if not request.bypass_cache:
            # Check cache
            today = datetime.now().date()
            cached_analysis = (
                db.query(AIAnalysisResult)
                .filter(
                    AIAnalysisResult.stock_code == request.stock_code,
                    AIAnalysisResult.created_at >= today,
                )
                .first()
            )

            if cached_analysis:
                print(f"Hit LLM Analysis cache for {request.stock_code}")
                return AgentAnalyzeResponse(
                    analysis_result=cached_analysis.analysis_content, cached=True
                )

        analysis_result = await agent_service.analyze_comprehensive(
            stock_code=request.stock_code,
            stock_name=request.stock_name,
            data=request,
            db=db,
        )
        return AgentAnalyzeResponse(analysis_result=analysis_result, cached=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
