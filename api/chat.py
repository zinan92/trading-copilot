"""Vercel serverless: POST /api/chat — proxy to MiniMax or Anthropic with streaming."""

import os
import json
from http.server import BaseHTTPRequestHandler
from http.client import HTTPSConnection

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'prompts', 'SKILL.md')
try:
    with open(SYSTEM_PROMPT_PATH) as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a trading analysis assistant."

MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        user_message = body.get("message", "")
        history = body.get("history", [])
        user_profile = body.get("user_profile", "")
        provider = body.get("provider", "minimax")
        user_api_key = body.get("api_key", "")

        system = SYSTEM_PROMPT
        if user_profile:
            system += "\n\n## Current User Profile\n" + user_profile

        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": user_message})

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            if provider == "anthropic":
                self._stream_anthropic(system, messages, user_api_key or ANTHROPIC_KEY)
            else:
                self._stream_minimax(system, messages, user_api_key or MINIMAX_KEY)
        except Exception as e:
            self._write_event({"type": "error", "error": str(e)})

    def _stream_minimax(self, system, messages, api_key):
        if not api_key:
            self._write_event({"type": "error", "error": "No MiniMax API key."})
            return

        full_messages = [{"role": "system", "content": system}] + messages
        payload = json.dumps({"model": "MiniMax-M1", "messages": full_messages, "stream": True, "max_tokens": 4096})

        conn = HTTPSConnection("api.minimax.chat", timeout=60)
        conn.request("POST", "/v1/chat/completions", body=payload, headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        })
        resp = conn.getresponse()

        if resp.status != 200:
            self._write_event({"type": "error", "error": resp.read().decode()})
            conn.close()
            return

        for line in self._iter_lines(resp):
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                self._write_event({"type": "done"})
                break
            try:
                chunk = json.loads(data)
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    text = delta.get("content", "")
                    if text:
                        self._write_event({"type": "text", "text": text})
                    if choices[0].get("finish_reason"):
                        self._write_event({"type": "done"})
            except json.JSONDecodeError:
                pass
        conn.close()

    def _stream_anthropic(self, system, messages, api_key):
        if not api_key:
            self._write_event({"type": "error", "error": "No Anthropic API key."})
            return

        payload = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system, "messages": messages, "stream": True})

        conn = HTTPSConnection("api.anthropic.com", timeout=60)
        conn.request("POST", "/v1/messages", body=payload, headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        })
        resp = conn.getresponse()

        if resp.status != 200:
            self._write_event({"type": "error", "error": resp.read().decode()})
            conn.close()
            return

        for line in self._iter_lines(resp):
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                self._write_event({"type": "done"})
                break
            try:
                event = json.loads(data)
                if event.get("type") == "content_block_delta":
                    text = event.get("delta", {}).get("text", "")
                    if text:
                        self._write_event({"type": "text", "text": text})
                elif event.get("type") == "message_stop":
                    self._write_event({"type": "done"})
            except json.JSONDecodeError:
                pass
        conn.close()

    def _iter_lines(self, resp):
        buf = ""
        while True:
            chunk = resp.read(4096)
            if not chunk:
                if buf.strip():
                    yield buf.strip()
                break
            buf += chunk.decode("utf-8", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if line:
                    yield line

    def _write_event(self, data):
        self.wfile.write(("data: " + json.dumps(data) + "\n\n").encode())
        self.wfile.flush()
