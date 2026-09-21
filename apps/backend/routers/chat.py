"""Chat router - SSE streaming AI responses."""
import json
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.session import get_session, save_session, clear_session
from core.keystore import get_active_config
from agent_bridge import run_agent_stream

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    project_id: Optional[str] = None
    session_id: str = "default"


@router.post("/stream")
async def chat_stream(body: ChatMessage, request: Request):
    """Stream AI response as Server-Sent Events."""
    config = get_active_config()
    history = get_session(body.session_id)

    # Set active project and prepend context
    message = body.message
    if body.project_id:
        # Write active-project.md so agent can find it
        from pathlib import Path as _Path
        import os as _os
        ws = _Path(_os.environ.get("WORKSPACE_PATH", "/workspace"))
        active_file = ws / "_system" / "active-project.md"
        active_file.parent.mkdir(parents=True, exist_ok=True)
        project_path = f"my-projects/{body.project_id}" if not body.project_id.startswith("my-projects") else body.project_id
        active_file.write_text(project_path)
        message = f"[Active project: {project_path}]\n{message}"

    async def generate():
        full_response = ""
        async for chunk in run_agent_stream(
            message,
            history,
            provider=config["provider"],
            api_key=config["api_key"],
            model=config["model"],
        ):
            if await request.is_disconnected():
                break
            yield chunk
            # Accumulate text for history
            try:
                data = json.loads(chunk.replace("data: ", "").strip())
                if data.get("type") == "text_delta":
                    full_response += data.get("text", "")
            except Exception:
                pass

        # Save to session history
        save_session(body.session_id, history)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/reset")
async def reset_chat(session_id: str = "default"):
    """Clear conversation history."""
    clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/history")
async def get_history(session_id: str = "default"):
    """Get conversation history."""
    history = get_session(session_id)
    return {"session_id": session_id, "messages": history}
