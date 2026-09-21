from typing import Optional
"""
Provider configuration.
Priority order (highest first):
  1. SQLite database (set via web UI)
  2. _system/web-config.json (legacy file)
  3. Environment variables (.env)
"""
import json
import os
import sqlite3
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))
DB_PATH = WORKSPACE / "_system" / "settings.db"
JSON_PATH = WORKSPACE / "_system" / "web-config.json"


# ── SQLite helpers ────────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _db_get(key: str):
    try:
        with _get_db() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None
    except Exception:
        return None


def _db_set(key: str, value: str):
    with _get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, value)
        )
        conn.commit()


def _db_get_all() -> dict:
    try:
        with _get_db() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


# ── JSON fallback ─────────────────────────────────────────────────

def _json_load() -> dict:
    if JSON_PATH.exists():
        try:
            return json.loads(JSON_PATH.read_text())
        except Exception:
            pass
    return {}


# ── Public API ────────────────────────────────────────────────────

def get_provider_config() -> dict:
    """
    Return the active provider config.
    DB takes priority, then JSON file, then env vars.
    """
    db = _db_get_all()
    js = _json_load()

    def get(key: str, env_key: str = "", default: str = "") -> str:
        return db.get(key) or js.get(key) or (os.environ.get(env_key, default) if env_key else default)

    # Determine active provider
    provider = get("provider", "AI_PROVIDER", "anthropic")

    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "api_key": get("anthropic_api_key", "ANTHROPIC_API_KEY", ""),
            "model": get("anthropic_model", "ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        }
    if provider in ("openai", "groq", "ollama"):
        base_url = get("openai_base_url", "OPENAI_BASE_URL", "")
        if provider == "groq" and not base_url:
            base_url = "https://api.groq.com/openai/v1"
        return {
            "provider": provider,
            "api_key": get("openai_api_key", "OPENAI_API_KEY", ""),
            "model": get("openai_model", "OPENAI_MODEL", "gpt-4o-mini"),
            "base_url": base_url,
        }
    if provider in ("google", "gemini"):
        return {
            "provider": "google",
            "api_key": get("google_api_key", "GOOGLE_API_KEY", ""),
            "model": get("gemini_model", "GEMINI_MODEL", "gemini-2.0-flash"),
        }
    return {"provider": "anthropic", "api_key": "", "model": "claude-sonnet-4-6"}


def save_provider_config(data: dict) -> dict:
    """Save provider config to SQLite (persistent across restarts)."""
    provider = data.get("provider", "anthropic")
    _db_set("provider", provider)

    if provider == "anthropic":
        if data.get("api_key"):
            _db_set("anthropic_api_key", data["api_key"])
        if data.get("model"):
            _db_set("anthropic_model", data["model"])
    elif provider in ("groq", "openai", "ollama"):
        if data.get("api_key"):
            _db_set("openai_api_key", data["api_key"])
        if data.get("model"):
            _db_set("openai_model", data["model"])
        base_url = data.get("base_url", "")
        if not base_url and provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        if base_url:
            _db_set("openai_base_url", base_url)
    elif provider in ("google", "gemini"):
        if data.get("api_key"):
            _db_set("google_api_key", data["api_key"])
        if data.get("model"):
            _db_set("gemini_model", data["model"])

    return get_provider_config()


def get_active_display() -> dict:
    """Return display-safe info about the active provider (masked key)."""
    config = get_provider_config()
    key = config.get("api_key", "")
    masked = (key[:8] + "..." + key[-4:]) if len(key) > 12 else ("***" if key else "not set")
    return {
        "provider": config["provider"],
        "model": config.get("model", ""),
        "key_masked": masked,
        "key_set": bool(key),
    }


async def test_provider(data: dict) -> dict:
    provider = data.get("provider", "anthropic")
    api_key = data.get("api_key", "")
    model = data.get("model", "")

    if not api_key:
        return {"status": "error", "message": "API key is required"}

    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            await client.messages.create(
                model=model or "claude-haiku-4-5",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return {"status": "connected", "provider": "anthropic", "model": model}

        if provider in ("groq", "openai", "ollama"):
            from openai import AsyncOpenAI
            base_url = data.get("base_url") or None
            if not base_url and provider == "groq":
                base_url = "https://api.groq.com/openai/v1"
            client = AsyncOpenAI(api_key=api_key or "ollama", base_url=base_url)
            await client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return {"status": "connected", "provider": provider, "model": model}

        if provider in ("google", "gemini"):
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model or "gemini-2.0-flash")
            await m.generate_content_async("Hi")
            return {"status": "connected", "provider": "google", "model": model}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Unknown provider"}
