"""In-memory session management for chat history."""
from collections import defaultdict

_sessions: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 20


def get_session(session_id: str) -> list[dict]:
    return _sessions[session_id]


def save_session(session_id: str, history: list[dict]):
    if len(history) > MAX_HISTORY:
        _sessions[session_id] = history[-MAX_HISTORY:]
    else:
        _sessions[session_id] = list(history)


def clear_session(session_id: str):
    _sessions[session_id] = []
