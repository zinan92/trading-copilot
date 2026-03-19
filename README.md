<div align="center">

# Trading Copilot

**告诉 AI 你的交易想法，它自动选择最合适的分析方法，给你可执行的建议**

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/methods-44-blue.svg)](https://trading-skills-catalog-xbb3.vercel.app/catalog)
[![MiniMax](https://img.shields.io/badge/AI-MiniMax_M1-10B981.svg)](https://www.minimax.io/)

[Try It](https://trading-skills-catalog-xbb3.vercel.app/) · [Skill Catalog](https://trading-skills-catalog-xbb3.vercel.app/catalog) · [GitHub](https://github.com/zinan92/trading-skills-catalog)

</div>

---

## 痛点

交易者需要做大量分析 — 宏观研判、选股筛选、财报解读、仓位计算 — 每种分析都有专业方法论（CANSLIM、VCP、Druckenmiller 策略合成等）。但普通交易者记不住这些方法论，更不知道什么场景该用哪个。

## 解决方案

Trading Copilot 把 44 个专业交易分析方法论封装进一个 AI system prompt。你只需要用自然语言说交易想法，AI 自动选择正确的方法论并给出结构化分析。

- 不需要知道任何 skill 名称
- 不需要安装任何东西
- 打开网页，输入交易想法，得到专业分析

## 架构

```
┌──────────────────────────────────────────────────┐
│              Trading Copilot (Web)                │
│         用户输入交易想法 → AI 自动分析             │
├─────────────────────┬────────────────────────────┤
│  Landing Page       │  Chat Mode                 │
│  居中输入框          │  流式 Markdown 渲染         │
│  6 个快捷按钮        │  对话历史持久化             │
│  用户 Profile        │  Copy / 时间戳              │
└─────────────────────┴────────────────────────────┘
          │                        │
          ▼                        ▼
┌──────────────────┐    ┌──────────────────────────┐
│  Vercel Serverless│    │  System Prompt (SKILL.md) │
│  /api/chat.js    │    │  44 个交易方法论           │
│  /api/config.js  │    │  Intent Routing 表        │
└────────┬─────────┘    │  输出格式规范              │
         │              └──────────────────────────┘
         ▼
┌──────────────────┐
│  MiniMax M1 (免费) │
│  或 Anthropic BYOK │
└──────────────────┘
```

## 快速开始

### 在线使用（零安装）

打开 [Trading Copilot](https://trading-skills-catalog-xbb3.vercel.app/) → 输入你的交易想法 → 得到分析。

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/zinan92/trading-skills-catalog.git
cd trading-skills-catalog

# 2. 安装依赖
pip install fastapi uvicorn httpx

# 3. 启动（MiniMax 免费 AI）
MINIMAX_API_KEY=your_key python3 app/server.py

# 4. 打开 http://localhost:3000
```

### Claude Code 用户

```bash
# 安装 44 个 trading skills + unified hub
git clone https://github.com/tradermonty/claude-trading-skills.git
cd claude-trading-skills && ./install.sh
cd .. && git clone https://github.com/zinan92/trading-skills-catalog.git
cd trading-skills-catalog && ./install.sh

# 在 Claude Code 中使用
/trading-hub
```

## 功能一览

| 功能 | 说明 | 状态 |
|------|------|------|
| Trading Copilot Chat | 网页端 AI 交易助手，自动选择分析方法论 | ✅ |
| 44 个交易方法论 | CANSLIM、VCP、Druckenmiller、Buffett 等专业框架 | ✅ |
| 流式 Markdown 渲染 | 表格、标题、粗体实时渲染 | ✅ |
| 用户 Profile | 交易风格/市场/风险偏好，个性化分析 | ✅ |
| 双 AI Provider | MiniMax（免费）+ Anthropic Claude（BYOK） | ✅ |
| 对话持久化 | 聊天记录 localStorage 保存，刷新不丢 | ✅ |
| Skill Catalog 展示页 | 44 个 skill 分类展示 + 工作流全景图 | ✅ |
| Trading Hub Skill | Claude Code `/trading-hub` 统一入口 | ✅ |
| 5 个 A 股 Skills | 调用本地 quant-data-pipeline API | ✅ |
| 自定义工作流 | YAML 保存/加载自定义 skill 序列 | ✅ |
| Vercel 部署 | 免费云端，任何设备可访问 | ✅ |

## 内置方法论

| 分类 | 数量 | 核心方法 |
|------|------|---------|
| 宏观 & Regime | 5 | 宏观体制检测、流动性监控、情绪分析、泡沫检测 |
| 市场择时 | 5 | 广度分析、顶部检测(O'Neil)、底部确认(FTD) |
| 选股筛选 | 10 | CANSLIM、VCP(Minervini)、价值股息、PEAD、配对交易 |
| 个股分析 | 9 | 综合研究、价值投资(Buffett)、财报深度、8阶段尽调 |
| 策略执行 | 10 | Druckenmiller 合成器、仓位计算(Kelly)、期权策略、回测 |
| A 股分析 | 5 | 日度复盘、概念追踪、信号扫描、条件选股、自选股简报 |

## 预设工作流

| 工作流 | 步骤 |
|--------|------|
| 晨间复盘 | economic-calendar → market-news → breadth → sector → bubble-detector |
| 选股流程 | screener (CANSLIM/VCP/Theme) → stock-analysis → position-sizer |
| 财报季 | earnings-calendar → tech-earnings-deepdive → earnings-trade-analyzer |
| 策略合成 | 8 upstream skills → druckenmiller synthesizer → 0-100 conviction score |
| A 股复盘 | daily-review → concept-tracker → signal-scanner → watchlist-briefing |

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | HTML + CSS + JS (单文件) | Chat 终端 UI |
| 渲染 | marked.js + DOMPurify | Markdown 安全渲染 |
| 字体 | DM Sans + DM Mono | 金融科技风格 |
| 后端(本地) | FastAPI + httpx | API 代理 + 流式转发 |
| 后端(云端) | Vercel Serverless (Node.js) | 零运维部署 |
| AI | MiniMax M1 (免费) / Anthropic Claude | 对话生成 |
| 持久化 | localStorage | 用户 Profile + 聊天记录 |

## 项目结构

```
trading-skills-catalog/
├── app/                          # Trading Copilot (产品)
│   ├── index.html                # Chat 终端 UI
│   ├── server.py                 # FastAPI 本地代理
│   └── prompts/
│       └── SKILL.md              # 44 个方法论 System Prompt
├── api/                          # Vercel Serverless Functions
│   ├── chat.js                   # AI 对话代理 (MiniMax/Anthropic)
│   └── config.js                 # 配置端点
├── skills/                       # Claude Code Skills (6 个本地)
│   ├── trading-hub/SKILL.md      # 统一入口
│   ├── ashare-daily-review/      # A 股日度复盘
│   ├── ashare-concept-tracker/   # 概念板块追踪
│   ├── ashare-signal-scanner/    # 信号扫描
│   ├── ashare-stock-screener/    # 条件选股
│   └── ashare-watchlist-briefing/# 自选股简报
├── agents/AGENTS.md              # Agent Trading Knowledge
├── catalog.html                  # Skill Catalog 展示页
├── .claude-plugin/plugin.json    # Claude Code Plugin
├── vercel.json                   # Vercel 部署配置
├── install.sh                    # 安装脚本
└── LICENSE                       # MIT
```

## 配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `MINIMAX_API_KEY` | MiniMax API Key (免费 AI) | 是(二选一) | 无 |
| `ANTHROPIC_API_KEY` | Anthropic API Key (BYOK) | 是(二选一) | 无 |
| `FMP_API_KEY` | Financial Modeling Prep (Claude Code skills 用) | 否 | 无 |

不设 API key 时，用户可在网页 Settings 中手动输入自己的 key。

## For AI Agents

本节面向需要将此项目作为工具或依赖集成的 AI Agent。

### 结构化元数据

```yaml
name: trading-copilot
description: AI trading analysis terminal with 44 professional methodologies and auto-routing
version: 1.0.0
type: web-app + claude-code-skill-collection

web_app:
  url: https://trading-skills-catalog-xbb3.vercel.app/
  api_base: https://trading-skills-catalog-xbb3.vercel.app/api
  endpoints:
    - path: /api/chat
      method: POST
      description: Send trading question, get streaming AI analysis
      body:
        message: string (user's trading question)
        history: array (conversation history)
        provider: string (minimax | anthropic)
        api_key: string (optional, for BYOK)
        user_profile: string (optional, trading preferences)
      response: text/event-stream
    - path: /api/config
      method: GET
      description: Check available AI providers

skill_entry_point:
  name: trading-hub
  trigger: /trading-hub
  description: Menu-driven entry point with 5 workflows and 6 category browsers

install_command: ./install.sh
health_check: curl https://trading-skills-catalog-xbb3.vercel.app/api/config

capabilities:
  - auto-route user trading intent to best analysis methodology
  - analyze stocks using CANSLIM, VCP, Buffett, Druckenmiller frameworks
  - synthesize market breadth, regime, and timing into conviction score (0-100)
  - calculate position sizes using Kelly criterion and ATR
  - screen stocks by natural language conditions
  - analyze tech earnings with 16-module institutional framework

categories:
  macro_regime: 5 methods
  market_breadth_timing: 5 methods
  stock_screening: 10 methods
  stock_analysis_reports: 9 methods
  strategy_execution: 10 methods
  ashare: 5 methods
```

### Agent 调用示例

```python
import httpx

async def ask_trading_copilot(question: str):
    """Ask Trading Copilot a trading question and get streaming analysis."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://trading-skills-catalog-xbb3.vercel.app/api/chat",
            json={"message": question, "provider": "minimax"},
            timeout=60
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data["type"] == "text":
                        print(data["text"], end="", flush=True)
                    elif data["type"] == "done":
                        break

# Example
await ask_trading_copilot("帮我分析一下 NVDA 值不值得买入")
```

## 相关项目

| 项目 | 说明 | 链接 |
|------|------|------|
| tradermonty/claude-trading-skills | 30+ 交易分析 Skills 源头 | [GitHub](https://github.com/tradermonty/claude-trading-skills) |
| Day1Global-Skills | 机构级财报分析 Skill | [GitHub](https://github.com/star23/Day1Global-Skills) |
| AI-Trader | 多 AI 模型实盘竞技 | [GitHub](https://github.com/HKUDS/AI-Trader) |
| TradingAgents | 多 Agent 交易框架 | [GitHub](https://github.com/TauricResearch/TradingAgents) |
| daily-stock-analysis | A/H/US 自动分析 + 推送 | [GitHub](https://github.com/ZhuLinsen/daily_stock_analysis) |

## License

MIT
