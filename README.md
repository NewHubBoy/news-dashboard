# 📈 股票新闻资讯看板

一站式股票新闻聚合与 AI 智能分析平台。自动从多个数据源采集金融资讯，并利用大语言模型生成专业投资分析报告。

## ✨ 核心功能

- **多源新闻聚合** — 同时接入 SerpApi (Google News)、Brave Search、东方财富网，全方位覆盖中英文金融资讯
- **AI Agent 智能分析** — 基于 ADP (Agentic Design Patterns) 设计模式，4 步链式流水线生成投资分析报告
- **实时流式展示** — SSE (Server-Sent Events) 实时推送 Agent 工作状态，前端同步展示分析进度
- **金融数据采集** — 自动搜索交易所公告、监管披露、券商研报、行情/财务数据
- **分析结果缓存** — 24 小时内同一股票不重复调用大模型，节省 Token 消耗
- **定时自动更新** — APScheduler 每 4 小时自动刷新已关注股票的数据
- **后台运行管理** — 支持交互式菜单与命令行参数，服务后台运行不阻塞终端

## 🤖 AI Agent 架构 (基于 ADP 设计模式)

系统采用 [Agentic Design Patterns](https://adp.xindoo.xyz/) 中的三种核心模式构建分析 Agent：

### 分析流水线

```
用户请求 (stock_code, stock_name)
        │
        ▼
  ┌─────────────┐
  │ 🔍 事实提取  │  ← Prompt Chain Step 1: JSON 结构化提取
  │ (Extract)    │    角色: 数据提取分析师 | temp=0.3
  └──────┬──────┘
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │  ⟳ 反思循环 (最多 3 轮)                       │
  │  ┌─────────────┐     ┌─────────────┐         │
  │  │ 📈 深度分析  │ ──→ │ ✅ 质量审查  │         │
  │  │ (Analyze)    │     │ (Review)     │         │
  │  │ temp=0.6     │     │ temp=0.3     │         │
  │  └──────────────┘     └──────┬──────┘         │
  │         ▲                    │                 │
  │         └── 未通过: 反馈 ────┘                 │
  │              通过: 跳出 ──→                    │
  └──────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────┐
  │ 📝 报告生成  │  ← Prompt Chain Step 3: Markdown 格式化
  │ (Format)     │    角色: 报告撰写人 | temp=0.4
  └──────┬──────┘
         │
         ▼
    入库缓存 + SSE 推送前端
```

### 应用的设计模式

| 模式                | ADP 章节      | 应用方式                                                   |
| ------------------- | ------------- | ---------------------------------------------------------- |
| **Prompt Chaining** | Ch.1 提示词链 | 事实提取 → 深度分析 → 格式化输出，每步不同角色和温度       |
| **Reflection**      | Ch.4 反思     | 审查者 (风控专家) 评分 ≥8 分通过，否则循环修正 (最多 3 轮) |
| **Tool Use**        | Ch.5 工具调用 | 动态调用 SerpApi / Brave / 东方财富等搜索工具              |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────┐
│           Next.js 16 + TailwindCSS 4        │  ← 前端 (SSE 实时展示)
├─────────────────────────────────────────────┤
│           FastAPI + Uvicorn (SSE Stream)     │  ← 后端 API
├──────────┬──────────┬───────────┬────────────┤
│ SerpApi  │  Brave   │ 东方财富  │  LLM API   │  ← 外部服务
│ (Google) │  Search  │ Playwright│ (OpenAI)   │
├──────────┴──────────┴───────────┴────────────┤
│         PostgreSQL + SQLAlchemy              │  ← 数据持久化
└─────────────────────────────────────────────┘
```

| 层级     | 技术栈                                             |
| -------- | -------------------------------------------------- |
| 前端     | Next.js 16, React 19, TailwindCSS 4, ReactMarkdown |
| 后端     | FastAPI, SQLAlchemy 2, Pydantic, APScheduler       |
| 数据库   | PostgreSQL (Docker)                                |
| 搜索引擎 | SerpApi, Brave Search API, Playwright (东方财富)   |
| AI 分析  | OpenAI 兼容接口 (NVIDIA NIM / Moonshot / 自定义)   |

## 🚀 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Playwright Chromium（`playwright install chromium`）

### 1. 克隆项目

```bash
git clone <repo-url>
cd news-dashboard
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填写以下配置：

```env
# 数据库 (默认即可)
DATABASE_URL=postgresql+psycopg://newsuser:newspass@localhost:5433/newsdb

# 搜索 API (至少配置一个)
GOOGLE_NEWS_API_KEY=your_serpapi_key        # https://serpapi.com/
BRAVE_API_KEY=your_brave_key               # https://brave.com/search/api/

# AI 分析 (必填)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或其他兼容接口
LLM_MODEL_NAME=gpt-4o                      # 模型名称
```

### 3. 启动服务

```bash
chmod +x start.sh
./start.sh
```

选择菜单 `1) 🚀 启动全部服务`，或直接运行：

```bash
./start.sh start    # 后台启动全部
./start.sh stop     # 停止全部
./start.sh restart  # 重启全部
./start.sh status   # 查看运行状态
./start.sh logs     # 查看日志
```

启动后访问：

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8110/docs

## 📁 项目结构

```
news-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # API 路由 (含 SSE 流式端点)
│   │   ├── config.py                  # 配置管理
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── scheduler.py               # APScheduler 定时任务
│   │   ├── db/database.py             # 数据库连接
│   │   ├── models/
│   │   │   ├── news.py                # ORM 模型
│   │   │   └── schemas.py             # Pydantic 数据模型
│   │   └── services/
│   │       ├── news_service.py        # 新闻聚合服务
│   │       ├── web_search_service.py  # Brave Search 服务
│   │       ├── eastmoney_scraper.py   # 东方财富 Playwright 爬虫
│   │       ├── financial_service.py   # 金融数据服务
│   │       └── agent_service.py       # AI Agent (ADP 架构)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── src/
│       ├── app/page.tsx               # 主页面 (SSE 消费)
│       ├── components/
│       │   ├── SearchForm.tsx         # 搜索栏
│       │   ├── NewsList.tsx           # 新闻列表
│       │   └── AIAnalysis.tsx         # AI 分析 (步骤进度条)
│       └── services/api.ts           # API 请求层 (含 SSE 流式)
├── docker-compose.yml                 # PostgreSQL 容器
├── start.sh                           # 服务管理脚本
└── README.md
```

## 🔌 API 接口

| 方法 | 路径                         | 说明                           |
| ---- | ---------------------------- | ------------------------------ |
| POST | `/api/search`                | 搜索股票新闻 + 金融数据        |
| POST | `/api/agent/analyze`         | AI 分析（JSON 响应，自动缓存） |
| POST | `/api/agent/analyze/stream`  | AI 分析（SSE 流式，实时状态）  |
| GET  | `/api/history/{stock_code}`  | 获取历史搜索记录               |
| GET  | `/api/analysis/{stock_code}` | 获取缓存的分析结果             |
| GET  | `/api/stocks`                | 获取所有已搜索股票列表         |

## 🔍 搜索引擎优先级

系统按以下顺序尝试获取新闻数据，任一成功即返回结果：

1. **SerpApi** (Google News) — 最优质的全球新闻源
2. **Brave Search** — 备用搜索引擎
3. **东方财富网** — 通过 Playwright 无头浏览器抓取国内金融垂直资讯
4. **模拟数据** — 所有 API 均不可用时的兜底方案

## 📝 License

MIT
