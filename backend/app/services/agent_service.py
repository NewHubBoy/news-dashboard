"""
Agent Service — 基于 ADP 设计模式的金融分析 Agent

设计模式:
  - Prompt Chaining (Ch.1): 事实提取 → 深度分析 → 报告格式化
  - Reflection (Ch.4): 审查者角色检验分析质量 + 反馈循环
  - Tool Use (Ch.5): 动态决定调用哪些搜索工具
"""

import json
import re
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.models.schemas import AgentAnalyzeRequest
from app.models.news import AIAnalysisResult


class AgentService:
    MAX_REFLECTION_ROUNDS = 3  # 反思循环最大轮数

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model_name = settings.llm_model_name
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120.0,  # 单次请求最长 120 秒
                max_retries=3,  # 504 等错误最多重试 1 次，不会无限卡住
            )

    # ================================================================
    # 主入口
    # ================================================================

    async def analyze_comprehensive(
        self, stock_code: str, stock_name: str, data: AgentAnalyzeRequest, db: Session
    ) -> str:
        """基于 ADP 设计模式的多步链式分析流水线"""
        if not self.client:
            return "未配置 AI 助手所需的 API Key，无法提供分析建议。"

        try:
            # 准备原始数据文本
            raw_data = self._compile_raw_data(data)
            print(
                f"[Agent] 开始分析 {stock_name}({stock_code})，数据长度: {len(raw_data)} 字符"
            )

            # ── Step 1: 事实提取 (Prompt Chain - Step 1) ──
            print("[Agent] Step 1/4: 结构化事实提取...")
            key_facts = await self._extract_key_facts(stock_code, stock_name, raw_data)

            # ── Step 2 + Step 3: 分析 → 审查 反思循环 ──
            review_feedback = ""
            for round_num in range(1, self.MAX_REFLECTION_ROUNDS + 1):
                print(f"[Agent] Step 2/4: 深度因果分析... (第 {round_num} 轮)")
                analysis_draft = await self._deep_analysis(
                    stock_code, stock_name, key_facts, review_feedback=review_feedback
                )

                print(
                    f"[Agent] Step 3/4: 质量审查 (第 {round_num}/{self.MAX_REFLECTION_ROUNDS} 轮)..."
                )
                review_result = await self._review_analysis(
                    stock_code, stock_name, key_facts, analysis_draft
                )

                if not review_result or review_result.get("approved", True):
                    score = review_result.get("score", "?") if review_result else "?"
                    print(f"[Agent] ✅ 审查通过 ({score}/10)，结束反思循环")
                    break

                score = review_result.get("score", "?")
                review_feedback = review_result.get("feedback", "")
                print(
                    f"[Agent] ❌ 审查未通过 ({score}/10)，修正意见: {review_result.get('issues', [])}"
                )

                if round_num == self.MAX_REFLECTION_ROUNDS:
                    print(
                        f"[Agent] ⚠️ 已达最大反思轮数 ({self.MAX_REFLECTION_ROUNDS})，使用当前版本继续"
                    )

            # ── Step 4: 报告格式化 (Prompt Chain - Step 3) ──
            print("[Agent] Step 4/4: 报告格式化...")
            final_report = await self._format_report(
                stock_code, stock_name, analysis_draft
            )

            # 清理并保存
            final_report = self._clean_output(final_report)

            db_analysis = AIAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_content=final_report,
            )
            db.add(db_analysis)
            db.commit()

            print(f"[Agent] ✅ 分析完成并已缓存入库")
            return final_report

        except Exception as e:
            print(f"[Agent] ❌ 分析出错: {e}")
            import traceback

            traceback.print_exc()
            return f"分析过程中出现错误: {str(e)}"

    # ================================================================
    # 流式分析入口 (SSE)
    # ================================================================

    async def analyze_streaming(
        self, stock_code: str, stock_name: str, data: AgentAnalyzeRequest, db: Session
    ):
        """流式分析 — 通过 SSE 事件实时推送 Agent 工作状态和最终报告"""
        import asyncio

        def _sse(event: str, data_str: str) -> str:
            lines = data_str.replace("\n", "\\n")
            return f"event: {event}\ndata: {lines}\n\n"

        if not self.client:
            yield _sse("error", "未配置 AI 助手所需的 API Key，无法提供分析建议。")
            return

        try:
            raw_data = self._compile_raw_data(data)

            # ── Step 1 ──
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
            key_facts = await self._extract_key_facts(stock_code, stock_name, raw_data)

            # ── Step 2 + Step 3: 分析 → 审查 反思循环 ──
            review_feedback = ""
            for round_num in range(1, self.MAX_REFLECTION_ROUNDS + 1):
                yield _sse(
                    "status",
                    json.dumps(
                        {
                            "step": 2,
                            "total": 4,
                            "message": f"📈 正在进行深度因果分析... (第 {round_num} 轮)",
                        },
                        ensure_ascii=False,
                    ),
                )
                analysis_draft = await self._deep_analysis(
                    stock_code, stock_name, key_facts, review_feedback=review_feedback
                )

                yield _sse(
                    "status",
                    json.dumps(
                        {
                            "step": 3,
                            "total": 4,
                            "message": f"🔍 质量审查中... (第 {round_num}/{self.MAX_REFLECTION_ROUNDS} 轮)",
                        },
                        ensure_ascii=False,
                    ),
                )
                review_result = await self._review_analysis(
                    stock_code, stock_name, key_facts, analysis_draft
                )

                if not review_result or review_result.get("approved", True):
                    score = review_result.get("score", "?") if review_result else "?"
                    yield _sse(
                        "status",
                        json.dumps(
                            {
                                "step": 3,
                                "total": 4,
                                "message": f"✅ 审查通过 ({score}/10)",
                            },
                            ensure_ascii=False,
                        ),
                    )
                    break

                score = review_result.get("score", "?")
                review_feedback = review_result.get("feedback", "")

                if round_num < self.MAX_REFLECTION_ROUNDS:
                    yield _sse(
                        "status",
                        json.dumps(
                            {
                                "step": 3,
                                "total": 4,
                                "message": f"🔄 审查评分 {score}/10，未通过，即将进入第 {round_num + 1} 轮修正...",
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
                                "message": f"⚠️ 已达最大反思轮数 ({self.MAX_REFLECTION_ROUNDS})，评分 {score}/10，使用当前版本",
                            },
                            ensure_ascii=False,
                        ),
                    )

            # ── Step 4 ──
            yield _sse(
                "status",
                json.dumps(
                    {"step": 4, "total": 4, "message": "📝 正在格式化分析报告..."},
                    ensure_ascii=False,
                ),
            )
            final_report = await self._format_report(
                stock_code, stock_name, analysis_draft
            )
            final_report = self._clean_output(final_report)

            # 入库
            db_analysis = AIAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_content=final_report,
            )
            db.add(db_analysis)
            db.commit()

            # 推送最终报告
            yield _sse(
                "result",
                json.dumps(
                    {"analysis_result": final_report, "cached": False},
                    ensure_ascii=False,
                ),
            )
            yield _sse("done", "")

        except Exception as e:
            yield _sse("error", str(e))

    # ================================================================
    # Prompt Chain Step 1: 结构化事实提取
    # ================================================================

    async def _extract_key_facts(
        self, stock_code: str, stock_name: str, raw_data: str
    ) -> str:
        """Step 1: 从原始数据中提取结构化关键事实"""

        prompt = f"""请从以下关于【{stock_name} ({stock_code})】的多维度原始数据中，提取关键事实。

原始数据：
{raw_data}

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

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专注于数据提取的金融分析师助手。你的任务是从杂乱的原始数据中准确提取结构化事实，不做主观推断。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # 低温度提高事实提取准确性
        )
        return response.choices[0].message.content.strip()

    # ================================================================
    # Prompt Chain Step 2: 深度因果分析
    # ================================================================

    async def _deep_analysis(
        self,
        stock_code: str,
        stock_name: str,
        key_facts: str,
        review_feedback: str = "",
    ) -> str:
        """Step 2: 基于结构化事实进行深度分析"""

        feedback_section = ""
        if review_feedback:
            feedback_section = f"""
⚠️ 上一版分析被审查者退回，请特别注意以下修正意见：
{review_feedback}
请在本次分析中针对性地修正上述问题。
"""

        prompt = f"""你是一位拥有 20 年经验的资深金融分析师。请根据以下关于【{stock_name} ({stock_code})】的结构化事实数据，进行深度因果分析。

提取到的关键事实：
{key_facts}
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

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位资深金融分析师，擅长基于结构化数据进行因果推理和投资分析。你的分析必须有理有据，逻辑严密。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()

    # ================================================================
    # Reflection: 审查者角色
    # ================================================================

    async def _review_analysis(
        self, stock_code: str, stock_name: str, key_facts: str, analysis: str
    ) -> Optional[Dict[str, Any]]:
        """Reflection: 以审查者角色检验分析质量"""

        prompt = f"""你是一位资深金融风控专家和事实核查员。请审查以下关于【{stock_name} ({stock_code})】的投资分析报告。

原始提取的事实数据：
{key_facts}

待审查的分析报告：
{analysis}

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

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位严谨的金融风控专家。你的职责是客观审查分析报告的质量，发现错误和偏见。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            result_text = response.choices[0].message.content.strip()
            # 尝试提取 JSON
            json_match = re.search(r"\{[\s\S]*\}", result_text)
            if json_match:
                review = json.loads(json_match.group())
                print(
                    f"[Agent] 审查评分: {review.get('score', '?')}/10, 通过: {review.get('approved', '?')}"
                )
                return review
        except Exception as e:
            print(f"[Agent] 审查步骤出错 (跳过): {e}")

        return None  # 审查失败时不阻塞流程

    # ================================================================
    # Prompt Chain Step 3: 报告格式化
    # ================================================================

    async def _format_report(
        self, stock_code: str, stock_name: str, analysis: str
    ) -> str:
        """Step 3: 将分析内容格式化为结构化 Markdown 报告"""

        prompt = f"""请将以下关于【{stock_name} ({stock_code})】的投资分析内容，整理成一份结构清晰、排版美观的 Markdown 报告。

分析内容：
{analysis}

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

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的金融报告撰写人。你擅长将分析内容整理成结构清晰、排版美观的 Markdown 文档。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    # ================================================================
    # 工具函数
    # ================================================================

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

        # 找到报告真正开始的位置
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

        # 清理末尾
        text = re.sub(r"[\n\r，。、；：,;]+$", "", text).strip()
        return text if text else "分析结果为空，请重试。"


agent_service = AgentService()
