import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.news import NewsArticle
from app.services.news_service import news_service
from app.services.financial_service import financial_service
from app.services.agent_service import agent_service
from app.models.schemas import AgentAnalyzeRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def update_stock_data_job():
    """定时更新所有被搜索过的股票的相关数据和分析"""
    logger.info("开始执行定时股票数据更新任务...")

    db: Session = SessionLocal()
    try:
        # 提取所有不重复的股票代码和名称
        stocks = (
            db.query(NewsArticle.stock_code, NewsArticle.stock_name).distinct().all()
        )

        for stock_code, stock_name in stocks:
            logger.info(f"正在后台更新 {stock_name} ({stock_code}) ...")

            # 使用现有服务更新数据
            articles = await news_service.search_news(stock_code, stock_name, db)
            announcements = await financial_service.fetch_announcements(
                stock_code, stock_name, db
            )
            disclosures = await financial_service.fetch_disclosures(
                stock_code, stock_name, db
            )
            reports = await financial_service.fetch_broker_reports(
                stock_code, stock_name, db
            )
            financial_data = await financial_service.fetch_market_data(
                stock_code, stock_name, db
            )

            # Request LLM background re-analyze with fresh data
            analyze_req = AgentAnalyzeRequest(
                stock_code=stock_code,
                stock_name=stock_name,
                articles=articles,
                announcements=announcements,
                disclosures=disclosures,
                reports=reports,
                financial_data=financial_data,
            )

            await agent_service.analyze_comprehensive(
                stock_code=stock_code, stock_name=stock_name, data=analyze_req, db=db
            )

            logger.info(f"{stock_name} 更新完成。")

    except Exception as e:
        logger.error(f"更新任务执行失败: {e}")
    finally:
        db.close()


def start_scheduler():
    # 为了演示效果，可以在这里配置频率例如 hours=4
    scheduler.add_job(update_stock_data_job, "interval", hours=4)
    scheduler.start()
    logger.info("定时任务服务已启动！(频次：每4小时执行一次更新调度)")


def stop_scheduler():
    scheduler.shutdown()
