"""Vercel serverless function for /api/config."""

import os
import json


def handler(request):
    data = {
        "has_platform_key": bool(os.environ.get("MINIMAX_API_KEY", "")),
        "has_anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY", "")),
        "default_provider": "minimax" if os.environ.get("MINIMAX_API_KEY") else "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "none",
    }

    class Response:
        status_code = 200
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }
        body = json.dumps(data)

    return Response()
