"""Vercel serverless: GET /api/config"""

import os
import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {
            "has_platform_key": bool(os.environ.get("MINIMAX_API_KEY", "")),
            "has_anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY", "")),
            "default_provider": "minimax" if os.environ.get("MINIMAX_API_KEY") else "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "none",
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
