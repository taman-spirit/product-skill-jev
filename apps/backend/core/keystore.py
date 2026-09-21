"""
Multi-key store: save multiple API keys and switch active key.
Stored in _system/settings.db (SQLite).
"""
import os
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

WORKSPACE = lambda: Path(os.environ.get("WORKSPACE_PATH", "/workspace"))
DB = lambda: WORKSPACE() / "_system" / "settings.db"


def _conn() -> sqlite3.Connection:
    DB().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB()))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            nickname TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT DEFAULT '',
            base_url TEXT DEFAULT '',
            is_active INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jev_settings (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


# ── Jev settings ──────────────────────────────────────────────────────────────
#
# A flat key/value table read by both the web backend and the Telegram bot, which
# share this file through the workspace mount. Names are "api_key", "enabled",
# "base_url", and "threshold.<NAME>" for each overridden threshold. Absent means
# "use the environment variable or the measured default", which is not the same
# as an empty string.

def get_jev_settings() -> dict:
    with _conn() as conn:
        rows = conn.execute("SELECT name, value FROM jev_settings").fetchall()
        return {r["name"]: r["value"] for r in rows}


def set_jev_settings(values: dict) -> None:
    """Upsert each name. A None value removes that row and restores the default."""
    with _conn() as conn:
        for name, value in values.items():
            if value is None:
                conn.execute("DELETE FROM jev_settings WHERE name = ?", (name,))
            else:
                conn.execute(
                    "INSERT INTO jev_settings (name, value, updated_at) "
                    "VALUES (?, ?, datetime('now')) "
                    "ON CONFLICT(name) DO UPDATE SET value = excluded.value, "
                    "updated_at = excluded.updated_at",
                    (name, str(value)),
                )
        conn.commit()


def clear_jev_thresholds() -> int:
    """Drop every threshold override. The measured defaults take over again."""
    with _conn() as conn:
        cur = conn.execute("DELETE FROM jev_settings WHERE name LIKE 'threshold.%'")
        conn.commit()
        return cur.rowcount


def list_keys() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, provider, nickname, model, base_url, is_active, created_at,"
            "       substr(api_key,1,8)||'...'||substr(api_key,-4) as key_masked,"
            "       length(api_key) > 0 as key_set"
            " FROM api_keys ORDER BY is_active DESC, id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_key(provider: str, nickname: str, api_key: str,
            model: str = "", base_url: str = "", set_active: bool = False) -> dict:
    with _conn() as conn:
        if set_active:
            conn.execute("UPDATE api_keys SET is_active = 0")
        cur = conn.execute(
            "INSERT INTO api_keys (provider, nickname, api_key, model, base_url, is_active)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (provider, nickname, api_key, model, base_url, 1 if set_active else 0)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM api_keys WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def delete_key(key_id: int) -> bool:
    with _conn() as conn:
        row = conn.execute("SELECT is_active FROM api_keys WHERE id = ?", (key_id,)).fetchone()
        if not row:
            return False
        was_active = row["is_active"]
        conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        # If deleted key was active, activate the next one
        if was_active:
            conn.execute(
                "UPDATE api_keys SET is_active = 1 WHERE id = (SELECT id FROM api_keys LIMIT 1)"
            )
        conn.commit()
        return True


def activate_key(key_id: int) -> Optional[dict]:
    with _conn() as conn:
        conn.execute("UPDATE api_keys SET is_active = 0")
        conn.execute("UPDATE api_keys SET is_active = 1 WHERE id = ?", (key_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,)).fetchone()
        return dict(row) if row else None


def get_active_key() -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE is_active = 1 LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_active_config() -> dict:
    """Return config dict for the currently active key (for use in agent)."""
    key = get_active_key()
    if not key:
        # Fallback to env vars (legacy)
        provider = os.environ.get("AI_PROVIDER", "anthropic")
        if provider == "anthropic":
            return {"provider": "anthropic",
                    "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")}
        if provider in ("openai", "groq", "ollama"):
            return {"provider": provider,
                    "api_key": os.environ.get("OPENAI_API_KEY", ""),
                    "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                    "base_url": os.environ.get("OPENAI_BASE_URL", "")}
        if provider in ("google", "gemini"):
            return {"provider": "google",
                    "api_key": os.environ.get("GOOGLE_API_KEY", ""),
                    "model": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")}
        return {"provider": "anthropic", "api_key": "", "model": "claude-sonnet-4-6"}

    provider = key["provider"]
    base_url = key.get("base_url") or ""
    if provider == "groq" and not base_url:
        base_url = "https://api.groq.com/openai/v1"
    return {
        "provider": provider,
        "api_key": key["api_key"],
        "model": key.get("model") or "",
        "base_url": base_url,
    }
