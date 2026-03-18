# Trading Skills Catalog

39 Claude Code skills for systematic trading analysis — from macro regime detection to stock screening to strategy synthesis.

## Quick Start

```bash
# 1. Install prerequisites (30+ skills from tradermonty)
git clone https://github.com/tradermonty/claude-trading-skills.git
cd claude-trading-skills && ./install.sh

# 2. Install trading-hub entry point
git clone https://github.com/zinan92/trading-skills-catalog.git
cd trading-skills-catalog && ./install.sh

# 3. Optional: set FMP API key (enables 14 additional skills)
export FMP_API_KEY=your_key_here
```

Then in Claude Code:
```
/trading-hub
```

## What's Included

| Category | Skills | Examples |
|----------|--------|---------|
| Macro & Regime | 5 | macro-regime-detector, macro-liquidity, us-market-sentiment |
| Market Breadth & Timing | 5 | market-breadth-analyzer, market-top-detector, ftd-detector |
| Stock Screening | 10 | canslim-screener, vcp-screener, finviz-screener |
| Stock Analysis & Reports | 9 | us-stock-analysis, tech-earnings-deepdive, stock-research-executor |
| Strategy & Execution | 10 | stanley-druckenmiller-investment, position-sizer, backtest-expert |

**API requirements:** 15 free, 14 FMP, 7 WebSearch, 3 other

## Preset Workflows

- **Morning Review** — economic calendar → news → breadth → sector → bubble detector
- **Stock Screening** — pick screener → deep dive → position sizing
- **Earnings Season** — earnings calendar → earnings analysis → trade scoring
- **Strategy Synthesis** — run 8 upstream skills → Druckenmiller 0-100 conviction score

## Live Catalog

Browse all skills with descriptions and API requirements: [Trading Skills Catalog](https://zinan92.github.io/trading-skills-catalog/)

## Credits

- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) — 30+ trading skills
- [Day1Global Skills](https://github.com/star23/Day1Global-Skills) — tech-earnings-deepdive, us-value-investing
- [stock-research-executor](https://github.com/liangdabiao/claude-code-stock-deep-research-agent) — 8-phase deep research
- [trading-plan-generator](https://skills.sh/jamesrochabrun/skills/trading-plan-generator) — 9-module trading plan

## Related Projects

- [AI-Trader](https://github.com/HKUDS/AI-Trader) — Multi-AI model live trading competition (NASDAQ/A-shares/Crypto)
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) — Multi-agent LLM trading framework (analyst → debate → risk → execution)
- [daily-stock-analysis](https://github.com/ZhuLinsen/daily_stock_analysis) — GitHub Actions EOD analysis for A/H/US stocks with Telegram push

## License

MIT
