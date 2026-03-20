"""Trading Copilot — FastAPI server supporting Anthropic + MiniMax APIs with streaming."""

from __future__ import annotations

import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import httpx

app = FastAPI()

PROMPT_PATH = Path(__file__).parent / "prompts" / "SKILL.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text() if PROMPT_PATH.exists() else "You are a trading analysis assistant."

# Platform MiniMax key (free tier for users without their own key)
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_URL = "https://api.minimax.chat/v1/chat/completions"
MINIMAX_MODEL = "MiniMax-M1"

# Optional Anthropic key (for BYOK users or server-side config)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# quant-data-pipeline base URL
PIPELINE_BASE = os.environ.get("PIPELINE_URL", "http://localhost:8000")

KNOWN_US_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC", "NFLX",
    "CRM", "ORCL", "AVGO", "QCOM", "MU", "TSM", "ASML", "ARM", "PLTR", "COIN",
    "BABA", "NIO", "LI", "XPEV", "JD", "PDD",
]


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((Path(__file__).parent / "index.html").read_text())


@app.get("/api/config")
async def config():
    return JSONResponse({
        "has_platform_key": bool(MINIMAX_API_KEY),
        "has_anthropic_key": bool(ANTHROPIC_API_KEY),
        "default_provider": "minimax" if MINIMAX_API_KEY else ("anthropic" if ANTHROPIC_API_KEY else "none"),
    })


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    history = body.get("history", [])
    user_profile = body.get("user_profile", "")
    provider = body.get("provider", "minimax")
    user_api_key = body.get("api_key", "")

    # Build system prompt with user profile
    system = SYSTEM_PROMPT
    if user_profile:
        system += f"\n\n## Current User Profile\n{user_profile}"

    # Pre-fetch live market data
    market_data = await fetch_market_context(user_message)
    if market_data:
        system += f"\n\n## Live Market Data (just fetched)\n{market_data}"

    # Build messages
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": user_message})

    if provider == "anthropic":
        return await _stream_anthropic(system, messages, user_api_key or ANTHROPIC_API_KEY, body.get("model", ANTHROPIC_MODEL))
    else:
        return await _stream_minimax(system, messages, user_api_key or MINIMAX_API_KEY, body.get("model", MINIMAX_MODEL))


async def _stream_minimax(system, messages, api_key, model):
    if not api_key:
        return JSONResponse({"error": "No MiniMax API key configured."}, status_code=400)

    full_messages = [{"role": "system", "content": system}] + messages

    payload = {"model": model, "messages": full_messages, "stream": True, "max_tokens": 4096, "tools": []}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def stream():
        async with httpx.AsyncClient(timeout=120, verify=False) as client:
            async with client.stream("POST", MINIMAX_URL, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error = await resp.aread()
                    yield f"data: {json.dumps({'type': 'error', 'error': error.decode()})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return
                    try:
                        chunk = json.loads(data)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                            if choices[0].get("finish_reason"):
                                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    except json.JSONDecodeError:
                        pass

    return StreamingResponse(stream(), media_type="text/event-stream")


async def _stream_anthropic(system, messages, api_key, model):
    if not api_key:
        return JSONResponse({"error": "No Anthropic API key. Set it in Settings."}, status_code=400)

    payload = {"model": model, "max_tokens": 4096, "system": system, "messages": messages, "stream": True}
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    async def stream():
        async with httpx.AsyncClient(timeout=120, verify=False) as client:
            async with client.stream("POST", ANTHROPIC_URL, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error = await resp.aread()
                    yield f"data: {json.dumps({'type': 'error', 'error': error.decode()})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return
                    try:
                        event = json.loads(data)
                        if event.get("type") == "content_block_delta":
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                        elif event.get("type") == "message_stop":
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    except json.JSONDecodeError:
                        pass

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Market data pre-fetching ──
# Priority: quant-data-pipeline (localhost:8000) → no fallback (local only)


async def _pipeline_get(path: str, timeout: float = 4.0):
    """GET from quant-data-pipeline, returns parsed JSON or None."""
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            resp = await client.get(f"{PIPELINE_BASE}{path}")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


def _extract_us_tickers(msg: str) -> list[str]:
    """Extract US stock tickers from user message."""
    upper = msg.upper()
    tickers = [t for t in KNOWN_US_TICKERS if t in upper]
    # Also match $TICKER patterns
    dollar_matches = re.findall(r"\$([A-Z]{1,5})", msg)
    tickers.extend(dollar_matches)
    # Deduplicate, limit to 5
    seen = set()
    result = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result[:5]


def _is_ashare_query(msg: str) -> bool:
    return bool(re.search(r"A股|a股|沪深|创业板|涨停|跌停|板块|概念|茅台|宁德|上证|深证|科创板|港股通", msg))


async def fetch_market_context(message: str) -> str | None:
    """Fetch live market data from quant-data-pipeline to inject into system prompt."""
    lines: list[str] = []
    pipeline_ok = False

    # 1. US market summary (always try)
    us_summary = await _pipeline_get("/api/us-stock/summary")
    if us_summary and us_summary.get("indexes"):
        pipeline_ok = True
        lines.append("## US Market (Live from quant-data-pipeline)")
        lines.append("| Index | Price | Change% | Volume |")
        lines.append("|-------|-------|---------|--------|")
        for idx in us_summary["indexes"]:
            name = idx.get("cn_name") or idx.get("name", "-")
            price = idx.get("price", "-")
            pct = f"{idx['change_pct']:.2f}%" if idx.get("change_pct") is not None else "-"
            vol = f"{idx['volume']/1e9:.1f}B" if idx.get("volume") else "-"
            lines.append(f"| {name} | {price} | {pct} | {vol} |")
        lines.append("")

    # 2. Specific US stock quotes if mentioned
    tickers = _extract_us_tickers(message)
    if tickers and pipeline_ok:
        quotes = []
        for ticker in tickers:
            q = await _pipeline_get(f"/api/us-stock/quote/{ticker}", timeout=3.0)
            if q and q.get("price"):
                quotes.append(q)
        if quotes:
            lines.append("## Stock Quotes (Live)")
            lines.append("| Symbol | Name | Price | Change% | Volume | Market Cap | PE |")
            lines.append("|--------|------|-------|---------|--------|-----------|-----|")
            for q in quotes:
                sym = q.get("symbol", "-")
                name = q.get("cn_name") or q.get("name", "-")
                price = f"${q['price']}"
                pct = f"{q['change_pct']:.2f}%" if q.get("change_pct") is not None else "-"
                vol = f"{q['volume']/1e6:.1f}M" if q.get("volume") else "-"
                mcap = f"${q['market_cap']/1e9:.1f}B" if q.get("market_cap") else "-"
                pe = f"{q['pe_ratio']:.1f}" if q.get("pe_ratio") else "-"
                lines.append(f"| {sym} | {name} | {price} | {pct} | {vol} | {mcap} | {pe} |")
            lines.append("")

    # 3. A-share data if query is about A-shares
    if _is_ashare_query(message) and pipeline_ok:
        concepts = await _pipeline_get("/api/concept-monitor/top")
        if concepts and isinstance(concepts, list):
            lines.append("## A股热门概念 (Live)")
            lines.append("| 概念 | 涨幅 | 代表股 |")
            lines.append("|------|------|--------|")
            for c in concepts[:10]:
                cname = c.get("name") or c.get("concept", "-")
                cpct = f"{c['change_pct']:.2f}%" if c.get("change_pct") is not None else "-"
                ctop = c.get("top_stock", "-")
                lines.append(f"| {cname} | {cpct} | {ctop} |")
            lines.append("")

        anomaly = await _pipeline_get("/api/anomaly/scan")
        if anomaly and (anomaly.get("limit_up") or anomaly.get("results")):
            lines.append("## A股异常信号 (Live)")
            lines.append(json.dumps(anomaly, ensure_ascii=False)[:500])
            lines.append("")

        rotation = await _pipeline_get("/api/rotation/signals")
        if rotation:
            lines.append("## 板块轮动信号 (Live)")
            lines.append(json.dumps(rotation, ensure_ascii=False)[:500])
            lines.append("")

    # 4. News/intel if available
    news = await _pipeline_get("/api/news/latest?limit=5", timeout=3.0)
    if news and isinstance(news, list) and len(news) > 0:
        lines.append("## Latest News")
        for n in news[:5]:
            headline = n.get("title") or n.get("headline") or json.dumps(n, ensure_ascii=False)[:100]
            lines.append(f"- {headline}")
        lines.append("")

    if lines:
        now = datetime.now(timezone.utc).isoformat()
        lines.insert(0, f"Data fetched at: {now}")
        lines.append("IMPORTANT: Use this REAL live data in your analysis. These are actual market prices right now.")
        return "\n".join(lines)

    return None


if __name__ == "__main__":
    import uvicorn
    print("Trading Copilot starting on http://localhost:3000")
    print(f"Pipeline: {PIPELINE_BASE}")
    print(f"MiniMax: {'configured' if MINIMAX_API_KEY else 'not set'}")
    print(f"Anthropic: {'configured' if ANTHROPIC_API_KEY else 'not set'}")
    uvicorn.run(app, host="0.0.0.0", port=3000)
