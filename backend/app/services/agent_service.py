"""
Agent Service — 基于 LangGraph 状态机的金融分析 Agent

使用 LangGraph StateGraph 实现 ADP 设计模式:
  - Prompt Chaining: extract_facts → analyze → format_report (节点链)
  - Reflection: analyze ⇄ review 条件循环 (最多 3 轮)
  - SSE 流式推送: 通过 status_updates 队列实时向前端推送状态
"""

import json
import re
from typing import TypedDict, Annotated, Optional, Dict, Any
from operator import add

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from sqlalchemy.orm import Session
from app.config import settings
from app.models.schemas import AgentAnalyzeRequest
from app.models.news import AIAnalysisResult


# ================================================================
# State 定义
# ================================================================


class AgentState(TypedDict):
    """LangGraph 状态 — 在节点之间流转的数据"""

    stock_code: str
    stock_name: str
    raw_data: str
    key_facts: str
    analysis_draft: str
    review_feedback: str
    review_score: int
    review_approved: bool
    reflection_count: int
    final_report: str
    # Annotated[list, add] 使得每个节点 append 的项会自动合并
    status_updates: Annotated[list, add]


MAX_REFLECTION_ROUNDS = 3


# ================================================================
# Graph 节点 (每个节点是一个 async 函数)
# ================================================================


def _get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """创建 ChatOpenAI 实例"""
    return ChatOpenAI(
        model=settings.llm_model_name,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
        timeout=120,
        max_retries=1,
    )


async def extract_facts(state: AgentState) -> dict:
    """Node 1: 从原始数据中提取结构化关键事实"""
    llm = _get_llm(temperature=0.3)
    stock = f"{state['stock_name']} ({state['stock_code']})"

    response = await llm.ainvoke(
        [
            SystemMessage(
                content="你是一位专注于数据提取的金融分析师助手。你的任务是从杂乱的原始数据中准确提取结构化事实，不做主观推断。"
            ),
            HumanMessage(
                content=f"""请从以下关于【{stock}】的多维度原始数据中，提取关键事实。

原始数据：
{state['raw_data']}

请严格按以下 JSON 格式输出提取结果：
{{
  "core_events": ["事件1的简要描述", "事件2的简要描述", ...],
  "financial_signals": ["财务信号1", "财务信号2", ...],
  "market_sentiment": "偏乐观/中性/偏悲观",
  "sentiment_evidence": ["支撑情绪判断的依据1", "依据2", ...],
  "risk_factors": ["风险因素1", "风险因素2", ...],
  "opportunity_factors": ["机会因素1", "机会因素2", ...],
  "data_quality": "充分/一般/不足"
}}

要求：
- 只基于提供的数据提取，不要捏造
- 每个字段至少填写 1 条，最多 5 条
- 如果某类信息不足，在对应字段写 ["数据不足，无法判断"]
- 直接输出 JSON，不要包含其他内容"""
            ),
        ]
    )

    return {
        "key_facts": response.content.strip(),
        "status_updates": [{"step": 1, "total": 4, "message": "🔍 关键事实提取完成"}],
    }


async def analyze(state: AgentState) -> dict:
    """Node 2: 基于结构化事实进行深度因果分析"""
    llm = _get_llm(temperature=0.6)
    stock = f"{state['stock_name']} ({state['stock_code']})"
    round_num = state.get("reflection_count", 0) + 1

    feedback_section = ""
    if state.get("review_feedback"):
        feedback_section = f"""
⚠️ 上一版分析被审查者退回，请特别注意以下修正意见：
{state['review_feedback']}
请在本次分析中针对性地修正上述问题。
"""

    response = await llm.ainvoke(
        [
            SystemMessage(
                content="你是一位资深金融分析师，擅长基于结构化数据进行因果推理和投资分析。你的分析必须有理有据，逻辑严密。"
            ),
            HumanMessage(
                content=f"""你是一位拥有 20 年经验的资深金融分析师。请根据以下关于【{stock}】的结构化事实数据，进行深度因果分析。

提取到的关键事实：
{state['key_facts']}
{feedback_section}
请从以下四个维度进行分析：

1. **核心事件与基本面影响**：这些事件如何影响公司的基本面？是利好还是利空？程度如何？
2. **市场与机构态度研判**：基于情绪信号和证据，当前市场共识是什么？是否存在预期差？
3. **风险与机会的深度剖析**：风险因素的发生概率和冲击程度？机会因素的确定性和潜在回报？
4. **操作策略建议**：针对短期（1周内）、中期（1-3个月）、长期（6个月以上）分别给出具体建议

要求：
- 每个分析点必须有因果推导链条，不能只陈述结论
- 如果数据不足以支撑某个判断，明确标注"数据不足，需进一步验证"
- 避免使用模糊表述，尽量给出具体指标或区间"""
            ),
        ]
    )

    return {
        "analysis_draft": response.content.strip(),
        "reflection_count": round_num,
        "status_updates": [
            {"step": 2, "total": 4, "message": f"📈 深度分析完成 (第 {round_num} 轮)"}
        ],
    }


async def review(state: AgentState) -> dict:
    """Node 3 (Reflection): 审查者角色检验分析质量"""
    llm = _get_llm(temperature=0.3)
    stock = f"{state['stock_name']} ({state['stock_code']})"
    round_num = state.get("reflection_count", 1)

    response = await llm.ainvoke(
        [
            SystemMessage(
                content="你是一位严谨的金融风控专家。你的职责是客观审查分析报告的质量，发现错误和偏见。"
            ),
            HumanMessage(
                content=f"""你是一位资深金融风控专家和事实核查员。请审查以下关于【{stock}】的投资分析报告。

原始提取的事实数据：
{state['key_facts']}

待审查的分析报告：
{state['analysis_draft']}

请从以下维度进行审查：
1. **事实一致性**：分析中引用的事实是否与原始数据一致？是否存在捏造？
2. **逻辑严密性**：因果推导是否合理？是否存在逻辑跳跃？
3. **偏见检测**：是否存在过度乐观或过度悲观的倾向？
4. **完整性**：四个分析维度是否都有充分覆盖？

请严格按以下 JSON 格式输出审查结果：
{{
  "approved": true或false,
  "score": 1-10的质量评分,
  "issues": ["问题1", "问题2", ...],
  "feedback": "如果不通过，给出具体的修正建议（一段话）"
}}

评分标准：8分以上为通过（approved=true），8分以下需要修正（approved=false）
直接输出 JSON，不要包含其他内容。"""
            ),
        ]
    )

    # 解析 JSON
    result_text = response.content.strip()
    approved = True
    score = 8
    feedback = ""

    try:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            parsed = json.loads(json_match.group())
            approved = parsed.get("approved", True)
            score = parsed.get("score", 8)
            feedback = parsed.get("feedback", "")
            print(f"[LangGraph] Review 评分: {score}/10, 通过: {approved}")
    except Exception as e:
        print(f"[LangGraph] Review JSON 解析失败 (视为通过): {e}")

    if approved:
        msg = f"✅ 审查通过 ({score}/10)"
    else:
        msg = f"🔄 审查评分 {score}/10，未通过 (第 {round_num}/{MAX_REFLECTION_ROUNDS} 轮)"

    return {
        "review_approved": approved,
        "review_score": score,
        "review_feedback": feedback,
        "status_updates": [{"step": 3, "total": 4, "message": msg}],
    }


async def format_report(state: AgentState) -> dict:
    """Node 4: 将分析内容格式化为 Markdown 报告"""
    llm = _get_llm(temperature=0.4)
    stock = f"{state['stock_name']} ({state['stock_code']})"

    response = await llm.ainvoke(
        [
            SystemMessage(
                content="你是一位专业的金融报告撰写人。你擅长将分析内容整理成结构清晰、排版美观的 Markdown 文档。"
            ),
            HumanMessage(
                content=f"""请将以下关于【{stock}】的投资分析内容，整理成一份结构清晰、排版美观的 Markdown 报告。

分析内容：
{state['analysis_draft']}

输出要求：
1. 严格使用以下四个 ### 标题结构：
   ### 1. 核心事件与基本面总结
   ### 2. 市场与机构态度
   ### 3. 潜在的风险与机会
   ### 4. 综合操作建议

2. 格式规范：
   - 使用 **加粗** 突出关键结论
   - 使用 - 列表组织要点
   - 适当使用 > 引用块标注重要提示
   - 操作建议部分区分短期/中期/长期

3. 直接从 "### 1. 核心事件与基本面总结" 开始，不要有开场白
4. 保持简洁，每个章节 3-5 个要点即可
5. 结尾不要有总结性废话"""
            ),
        ]
    )

    return {
        "final_report": response.content.strip(),
        "status_updates": [{"step": 4, "total": 4, "message": "📝 报告格式化完成"}],
    }


# ================================================================
# 条件路由
# ================================================================


def should_continue_reflection(state: AgentState) -> str:
    """条件边: 决定审查后是继续反思还是进入报告格式化"""
    if state.get("review_approved", True):
        return "format_report"
    if state.get("reflection_count", 0) >= MAX_REFLECTION_ROUNDS:
        print(f"[LangGraph] 已达最大反思轮数 ({MAX_REFLECTION_ROUNDS})，使用当前版本")
        return "format_report"
    return "analyze"


# ================================================================
# 构建 Graph
# ================================================================


def build_analysis_graph() -> StateGraph:
    """构建金融分析 StateGraph"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("extract_facts", extract_facts)
    graph.add_node("analyze", analyze)
    graph.add_node("review", review)
    graph.add_node("format_report", format_report)

    # 设置入口
    graph.set_entry_point("extract_facts")

    # 添加边
    graph.add_edge("extract_facts", "analyze")
    graph.add_edge("analyze", "review")
    graph.add_conditional_edges(
        "review",
        should_continue_reflection,
        {
            "analyze": "analyze",
            "format_report": "format_report",
        },
    )
    graph.add_edge("format_report", END)

    return graph.compile()


# ================================================================
# AgentService — 兼容现有接口
# ================================================================


class AgentService:
    def __init__(self):
        self.graph = None
        if settings.openai_api_key:
            self.graph = build_analysis_graph()

    def _compile_raw_data(self, data: AgentAnalyzeRequest) -> str:
        """编译原始数据为文本"""
        sections = []

        if data.articles:
            sections.append("【最新新闻资讯】")
            for i, a in enumerate(data.articles[:8]):
                sections.append(f"{i+1}. 标题: {a.title}\n   摘要: {a.description}")

        if data.announcements:
            sections.append("\n【交易所公告】")
            for i, a in enumerate(data.announcements[:5]):
                sections.append(f"{i+1}. {a.title}")

        if data.disclosures:
            sections.append("\n【监管披露】")
            for i, d in enumerate(data.disclosures[:3]):
                sections.append(f"{i+1}. {d.title}")

        if data.reports:
            sections.append("\n【券商研报】")
            for i, r in enumerate(data.reports[:5]):
                sections.append(f"{i+1}. 标题: {r.title}\n   摘要: {r.content_summary}")

        if data.financial_data:
            sections.append("\n【行情与财务数据】")
            for i, f in enumerate(data.financial_data[:5]):
                sections.append(f"{i+1}. 标题: {f.title}\n   摘要: {f.content_summary}")

        return "\n".join(sections) if sections else "暂无可用数据"

    def _clean_output(self, text: str) -> str:
        """清理 AI 输出"""
        text = text.strip()
        patterns = [
            r"###\s*1\s*[.、]\s*核心事件",
            r"##\s*1\s*[.、]\s*核心事件",
            r"#{1,3}\s*核心事件",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                text = text[match.start() :]
                break
        text = re.sub(r"[\n\r，。、；：,;]+$", "", text).strip()
        return text if text else "分析结果为空，请重试。"

    # ================================================================
    # 主入口 (非流式)
    # ================================================================

    async def analyze_comprehensive(
        self, stock_code: str, stock_name: str, data: AgentAnalyzeRequest, db: Session
    ) -> str:
        """使用 LangGraph 执行完整分析流水线"""
        if not self.graph:
            return "未配置 AI 助手所需的 API Key，无法提供分析建议。"

        try:
            raw_data = self._compile_raw_data(data)
            print(f"[LangGraph] 开始分析 {stock_name}({stock_code})")

            initial_state: AgentState = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "raw_data": raw_data,
                "key_facts": "",
                "analysis_draft": "",
                "review_feedback": "",
                "review_score": 0,
                "review_approved": False,
                "reflection_count": 0,
                "final_report": "",
                "status_updates": [],
            }

            result = await self.graph.ainvoke(initial_state)
            final_report = self._clean_output(result["final_report"])

            # 入库缓存
            db_analysis = AIAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_content=final_report,
            )
            db.add(db_analysis)
            db.commit()

            print(f"[LangGraph] ✅ 分析完成，经过 {result['reflection_count']} 轮反思")
            return final_report

        except Exception as e:
            print(f"[LangGraph] ❌ 分析出错: {e}")
            import traceback

            traceback.print_exc()
            return f"分析过程中出现错误: {str(e)}"

    # ================================================================
    # 流式分析入口 (SSE) — 使用 astream 逐节点推送
    # ================================================================

    async def analyze_streaming(
        self, stock_code: str, stock_name: str, data: AgentAnalyzeRequest, db: Session
    ):
        """流式分析 — 通过 LangGraph astream 逐节点推送 SSE 事件"""

        def _sse(event: str, data_str: str) -> str:
            lines = data_str.replace("\n", "\\n")
            return f"event: {event}\ndata: {lines}\n\n"

        if not self.graph:
            yield _sse("error", "未配置 AI 助手所需的 API Key，无法提供分析建议。")
            return

        try:
            raw_data = self._compile_raw_data(data)

            initial_state: AgentState = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "raw_data": raw_data,
                "key_facts": "",
                "analysis_draft": "",
                "review_feedback": "",
                "review_score": 0,
                "review_approved": False,
                "reflection_count": 0,
                "final_report": "",
                "status_updates": [],
            }

            # 发送初始状态
            yield _sse(
                "status",
                json.dumps(
                    {
                        "step": 1,
                        "total": 4,
                        "message": "🔍 正在从原始数据中提取关键事实...",
                    },
                    ensure_ascii=False,
                ),
            )

            # 使用 LangGraph astream 逐节点流式执行
            seen_updates = 0
            final_state = None

            async for event in self.graph.astream(initial_state, stream_mode="updates"):
                # event 是 {node_name: state_update} 的字典
                for node_name, state_update in event.items():
                    print(f"[LangGraph] 节点完成: {node_name}")

                    # 推送该节点产生的 status_updates
                    new_updates = state_update.get("status_updates", [])
                    for update in new_updates:
                        yield _sse("status", json.dumps(update, ensure_ascii=False))

                    # 如果是最终节点，记录结果
                    if node_name == "format_report":
                        final_report = self._clean_output(
                            state_update.get("final_report", "")
                        )

                        # 入库
                        db_analysis = AIAnalysisResult(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            analysis_content=final_report,
                        )
                        db.add(db_analysis)
                        db.commit()

                        yield _sse(
                            "result",
                            json.dumps(
                                {"analysis_result": final_report, "cached": False},
                                ensure_ascii=False,
                            ),
                        )

                    # 如果 analyze 后面要进 review，推送预告
                    if node_name == "analyze":
                        round_num = state_update.get("reflection_count", 1)
                        yield _sse(
                            "status",
                            json.dumps(
                                {
                                    "step": 3,
                                    "total": 4,
                                    "message": f"🔍 质量审查中... (第 {round_num}/{MAX_REFLECTION_ROUNDS} 轮)",
                                },
                                ensure_ascii=False,
                            ),
                        )

                    # 如果 review 不通过且要回到 analyze，推送下一轮预告
                    if node_name == "review":
                        approved = state_update.get("review_approved", True)
                        if not approved:
                            count = state_update.get("reflection_count", 1)
                            if count < MAX_REFLECTION_ROUNDS:
                                yield _sse(
                                    "status",
                                    json.dumps(
                                        {
                                            "step": 2,
                                            "total": 4,
                                            "message": f"📈 正在基于审查反馈重新分析... (第 {count + 1} 轮)",
                                        },
                                        ensure_ascii=False,
                                    ),
                                )
                            else:
                                yield _sse(
                                    "status",
                                    json.dumps(
                                        {
                                            "step": 3,
                                            "total": 4,
                                            "message": f"⚠️ 已达最大反思轮数，使用当前版本",
                                        },
                                        ensure_ascii=False,
                                    ),
                                )
                        # 如果通过且要进 format，推送预告
                        if approved:
                            yield _sse(
                                "status",
                                json.dumps(
                                    {
                                        "step": 4,
                                        "total": 4,
                                        "message": "📝 正在格式化分析报告...",
                                    },
                                    ensure_ascii=False,
                                ),
                            )

            yield _sse("done", "")

        except Exception as e:
            print(f"[LangGraph] ❌ 流式分析出错: {e}")
            import traceback

            traceback.print_exc()
            yield _sse("error", str(e))


agent_service = AgentService()
