"""
ᚱ RUNE Playground — FastAPI Backend
Enhances prompts via RUNE's 8-layer engine, sends to Gemini, validates with Spinoza.
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# RUNE imports
# ---------------------------------------------------------------------------
RUNE_PATH = os.environ.get("RUNE_PATH", "/opt/rune")
if RUNE_PATH not in sys.path:
    sys.path.insert(0, RUNE_PATH)

from rune.core.enhancer import Enhancer  # noqa: E402
from rune.core.validator import SpinozaValidator, SpinozaPrinciple  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RUNE_API_URL = os.environ.get(
    "RUNE_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
)
RUNE_API_KEY = os.environ.get("RUNE_API_KEY", "")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "5"))

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="RUNE Playground", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
enhancer = Enhancer()
validator = SpinozaValidator()

# Rate limiting: {ip: {"count": int, "date": str}}
rate_store: dict[str, dict[str, Any]] = {}


def _check_rate(ip: str) -> tuple[bool, int]:
    """Returns (allowed, remaining)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = rate_store.get(ip)
    if not entry or entry["date"] != today:
        rate_store[ip] = {"count": 0, "date": today}
        entry = rate_store[ip]
    if entry["count"] >= RATE_LIMIT:
        return False, 0
    entry["count"] += 1
    return True, RATE_LIMIT - entry["count"]


def _get_remaining(ip: str) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = rate_store.get(ip)
    if not entry or entry["date"] != today:
        return RATE_LIMIT
    return max(0, RATE_LIMIT - entry["count"])


def _call_gemini(enhanced_prompt: str) -> str:
    """Send enhanced prompt to Gemini API and return the text response."""
    if not RUNE_API_KEY:
        return "[Gemini API key not configured — showing enhanced prompt only]"

    url = f"{RUNE_API_URL}?key={RUNE_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": enhanced_prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[Gemini API error: {e}]"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


@app.get("/api/remaining")
async def remaining(request: Request):
    ip = request.client.host if request.client else "unknown"
    return {"remaining": _get_remaining(ip), "limit": RATE_LIMIT}


@app.post("/api/cast")
async def cast_spell(request: Request):
    ip = request.client.host if request.client else "unknown"
    allowed, remaining = _check_rate(ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again tomorrow.", "remaining": 0},
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse(status_code=400, content={"error": "Prompt is required"})
    if len(prompt) > 5000:
        return JSONResponse(status_code=400, content={"error": "Prompt too long (max 5000 chars)"})

    # 1) Enhance with RUNE
    result = enhancer.enhance(prompt)

    # 2) Call Gemini with enhanced prompt
    raw_output = _call_gemini(result.enhanced)

    # 3) Validate output with Spinoza
    report = validator.validate(raw_output)

    spinoza = {
        "conatus": report.principle_scores[SpinozaPrinciple.CONATUS].score,
        "ratio": report.principle_scores[SpinozaPrinciple.RATIO].score,
        "laetitia": report.principle_scores[SpinozaPrinciple.LAETITIA].score,
        "natura": report.principle_scores[SpinozaPrinciple.NATURA].score,
        "overall": report.overall_score,
        "grade": report.grade,
    }

    return {
        "enhanced": result.enhanced,
        "raw_output": raw_output,
        "rune_output": raw_output,
        "spinoza": spinoza,
        "layers_applied": len(result.layers_applied),
        "remaining": remaining,
    }


# Mount static files (after routes so /api takes priority)
app.mount("/static", StaticFiles(directory="static"), name="static")
