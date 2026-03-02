from typing import List
import re
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.models.schemas import AgentAnalyzeRequest
from app.models.news import AIAnalysisResult


class AgentService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model_name = settings.llm_model_name
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def analyze_comprehensive(
        self, stock_code: str, stock_name: str, data: AgentAnalyzeRequest, db: Session
    ) -> str:
        """根据新闻、公告、财报、研报等综合信息给出建议并入库"""
        if not self.client:
            return "未配置 AI 助手所需的 API Key，无法提供分析建议。"

        # Compile information
        info_content = ""

        info_content += "【最新新闻资讯】\n"
        for i, article in enumerate(data.articles[:5]):
            info_content += (
                f"{i+1}. 标题: {article.title}\n   摘要: {article.description}\n"
            )

        info_content += "\n【交易所公告】\n"
        for i, item in enumerate(data.announcements[:3]):
            info_content += f"{i+1}. 标题: {item.title}\n"

        info_content += "\n【监管披露】\n"
        for i, item in enumerate(data.disclosures[:2]):
            info_content += f"{i+1}. 标题: {item.title}\n"

        info_content += "\n【券商研报】\n"
        for i, item in enumerate(data.reports[:3]):
            info_content += (
                f"{i+1}. 标题: {item.title}\n   摘要: {item.content_summary}\n"
            )

        info_content += "\n【行情与财务数据分析】\n"
        for i, item in enumerate(data.financial_data[:3]):
            info_content += (
                f"{i+1}. 标题: {item.title}\n   摘要: {item.content_summary}\n"
            )

        prompt = f"""
你是一位专业的金融分析师。请根据以下关于【{stock_name} ({stock_code})】的多维度数据信息（包含新闻、公告、券商研报及财务数据分析），提供一份深度且简明扼要的综合投资建议报告。

以下是收集到的信息：
{info_content}

请严格按以下 Markdown 结构输出报告：

### 1. 核心事件与基本面总结
(综合上述信息，重点讲述近期发生了什么关键事件，以及这些事件对公司基本面的影响)

### 2. 市场与机构态度
(根据新闻和券商研报，分析当前市场和专业机构的态度是偏乐观还是悲观)

### 3. 潜在的风险与机会
(结合监管披露和财务数据变化，指出投资者需要关注的可能风险及存在的投资机会)

### 4. 综合操作建议
(给出对该股票近期的明确关注侧重点或短期/中长期的操作建议)

**格式要求：**
- 使用标准 Markdown 语法
- 标题使用 ### 格式
- 要点列表使用 - 或 * 开头
- 重点内容使用 **加粗**
- 可以适当使用分段和空行提高可读性

注意：请保持客观专业，仅针对提供的信息进行推导，不要捏造不实数据。

**重要：直接从"### 1. 核心事件与基本面总结"开始输出，不要包含任何开场白、前言或说明文字。**
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位专业的金融顾问。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            analysis_text = response.choices[0].message.content

            # 清理 AI 输出，移除开头和结尾的无用标签和多余内容
            analysis_text = analysis_text.strip()

            # 尝试找到报告真正开始的位置（以 ### 1. 或 ## 1. 开头）
            report_start_patterns = [
                r'###\s*1\s*[.、]\s*核心事件',
                r'##\s*1\s*[.、]\s*核心事件',
                r'#{1,3}\s*1\s*[.、]\s*核心事件',
                r'#{1,3}\s*核心事件',
            ]

            for pattern in report_start_patterns:
                match = re.search(pattern, analysis_text)
                if match:
                    # 从真正报告开始的位置截取
                    analysis_text = analysis_text[match.start():]
                    break

            # 清理开头的无用标签
            start_patterns = [
                r'^[分析总结评估建议备注说明报告结果]+[：:：]\s*',  # "分析：" 或 "分析:" 开头
                r'^[分析总结评估建议备注说明报告结果]+\s*',          # 纯标签开头
                r'^##?#+\s*[分析总结评估建议备注说明报告结果]+[：:：]?\s*',  # Markdown 标题格式
            ]

            for pattern in start_patterns:
                analysis_text = re.sub(pattern, '', analysis_text, count=1)
                analysis_text = analysis_text.strip()

            # 清理结尾的无用标签
            lines = analysis_text.split('\n')
            if lines:
                last_line = lines[-1].strip()
                # 如果最后一行是常见的无用标签，移除它
                tag_patterns = [
                    r'^[分析总结评估建议备注说明]+[。。，、；：,;]?$',  # 纯标签+可选标点
                    r'^[分析总结评估建议备注说明]+$',  # 纯标签
                ]
                if any(re.match(pattern, last_line) for pattern in tag_patterns):
                    lines.pop()
                    analysis_text = '\n'.join(lines).strip()

            # 移除末尾可能残留的空行和标点
            analysis_text = re.sub(r'[\n\r，。、；：,;]+$', '', analysis_text).strip()

            # 如果清理后内容为空，返回原始内容
            if not analysis_text:
                analysis_text = response.choices[0].message.content.strip()

            # 存入数据库缓存
            db_analysis = AIAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_content=analysis_text,
            )
            db.add(db_analysis)
            db.commit()

            return analysis_text

        except Exception as e:
            return f"分析过程中出现错误: {str(e)}"


agent_service = AgentService()
