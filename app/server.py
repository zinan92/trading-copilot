"""Trading Copilot — lightweight FastAPI server that proxies Anthropic API + serves the chat UI."""

import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI()

# Load system prompt
PROMPT_PATH = Path(__file__).parent / "prompts" / "SKILL.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text() if PROMPT_PATH.exists() else "You are a trading analysis assistant."

# Anthropic API config
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.get("/api/config")
async def config():
    """Return client-safe config (no secrets)."""
    return JSONResponse({
        "has_api_key": bool(ANTHROPIC_API_KEY),
        "model": DEFAULT_MODEL,
    })


@app.post("/api/chat")
async def chat(request: Request):
    """Proxy chat request to Anthropic Messages API with streaming."""
    body = await request.json()

    user_message = body.get("message", "")
    history = body.get("history", [])
    api_key = body.get("api_key", "") or ANTHROPIC_API_KEY

    if not api_key:
        return JSONResponse({"error": "No API key. Set ANTHROPIC_API_KEY or pass api_key in request."}, status_code=400)

    # Build messages array
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": body.get("model", DEFAULT_MODEL),
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": messages,
        "stream": True,
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async def stream_response():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", ANTHROPIC_URL, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    yield f"data: {json.dumps({'type': 'error', 'error': error_body.decode()})}\n\n"
                    return

                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                            return
                        try:
                            event = json.loads(data)
                            event_type = event.get("type", "")

                            if event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield f"data: {json.dumps({'type': 'text', 'text': delta['text']})}\n\n"

                            elif event_type == "message_stop":
                                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                        except json.JSONDecodeError:
                            pass

    return StreamingResponse(stream_response(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    print("Trading Copilot starting on http://localhost:3000")
    print(f"API Key: {'configured' if ANTHROPIC_API_KEY else 'not set (user must provide)'}")
    uvicorn.run(app, host="0.0.0.0", port=3000)
