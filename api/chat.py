"""Vercel serverless function for /api/chat — proxies to MiniMax or Anthropic with streaming."""

import os
import json
from http.client import HTTPSConnection
from urllib.parse import urlparse

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'prompts', 'SKILL.md')
try:
    with open(SYSTEM_PROMPT_PATH) as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a trading analysis assistant."

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def handler(request):
    """Vercel serverless handler."""
    from http.server import BaseHTTPRequestHandler
    import io

    if request.method == "OPTIONS":
        return _cors_response(200, "")

    try:
        body = json.loads(request.body)
    except Exception:
        return _json_response(400, {"error": "Invalid JSON"})

    user_message = body.get("message", "")
    history = body.get("history", [])
    user_profile = body.get("user_profile", "")
    provider = body.get("provider", "minimax")
    user_api_key = body.get("api_key", "")

    system = SYSTEM_PROMPT
    if user_profile:
        system += f"\n\n## Current User Profile\n{user_profile}"

    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": user_message})

    if provider == "anthropic":
        return _stream_anthropic(system, messages, user_api_key or ANTHROPIC_API_KEY)
    else:
        return _stream_minimax(system, messages, user_api_key or MINIMAX_API_KEY)


def _stream_minimax(system, messages, api_key):
    if not api_key:
        return _json_response(400, {"error": "No MiniMax API key configured."})

    full_messages = [{"role": "system", "content": system}] + messages
    payload = json.dumps({"model": "MiniMax-M1", "messages": full_messages, "stream": True, "max_tokens": 4096})

    def generate():
        conn = HTTPSConnection("api.minimax.chat")
        conn.request("POST", "/v1/chat/completions", body=payload, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        resp = conn.getresponse()

        if resp.status != 200:
            error = resp.read().decode()
            yield f"data: {json.dumps({'type': 'error', 'error': error})}\n\n"
            return

        for line in _iter_lines(resp):
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
        conn.close()

    return _streaming_response(generate())


def _stream_anthropic(system, messages, api_key):
    if not api_key:
        return _json_response(400, {"error": "No Anthropic API key."})

    payload = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system, "messages": messages, "stream": True})

    def generate():
        conn = HTTPSConnection("api.anthropic.com")
        conn.request("POST", "/v1/messages", body=payload, headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        })
        resp = conn.getresponse()

        if resp.status != 200:
            error = resp.read().decode()
            yield f"data: {json.dumps({'type': 'error', 'error': error})}\n\n"
            return

        for line in _iter_lines(resp):
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
        conn.close()

    return _streaming_response(generate())


def _iter_lines(resp):
    """Read HTTP response line by line."""
    buf = ""
    while True:
        chunk = resp.read(4096)
        if not chunk:
            if buf:
                yield buf
            break
        buf += chunk.decode("utf-8", errors="replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if line:
                yield line


def _streaming_response(generator):
    """Return a Vercel-compatible streaming response."""
    from http.server import BaseHTTPRequestHandler

    class Response:
        status_code = 200
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        body = "".join(generator)

    return Response()


def _json_response(status, data):
    class Response:
        status_code = status
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }
        body = json.dumps(data)
    return Response()


def _cors_response(status, body):
    class Response:
        status_code = status
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        body = ""
    return Response()
