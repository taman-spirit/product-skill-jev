"""
Bridge between the web backend and the existing bot/agent.py.
Reuses all AI logic without duplication.
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import AsyncGenerator

def _get_workspace() -> Path:
    """Dynamic workspace - reads env var each call so tests can override it."""
    return Path(os.environ.get("WORKSPACE_PATH", "/workspace"))

# Keep WORKSPACE for backward compat - but use _get_workspace() in functions
WORKSPACE = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))

# ── Tool execution (same as bot/agent.py) ────────────────────────────────────

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the PM workspace",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Create or update a file in the PM workspace",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a workspace directory",
        "input_schema": {
            "type": "object",
            "properties": {"directory": {"type": "string", "description": "Relative path. Use '.' for root."}}
        }
    },
    {
        "name": "search_files",
        "description": "Search for text across workspace .md files",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "directory": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "move_file",
        "description": "Move a file to a new location",
        "input_schema": {
            "type": "object",
            "properties": {"source": {"type": "string"}, "destination": {"type": "string"}},
            "required": ["source", "destination"]
        }
    },
    {
        "name": "scan_tags",
        "description": (
            "Find every pair of PRDs in a project that share a module tag. This is file "
            "scanning, not judgment: it returns the same pairs every run. Run it before "
            "judging any conflict, and treat the list it returns as complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "sprint": {"type": "string"}
            },
            "required": ["project"]
        }
    },
    # Mirrors the judge tool in bot/agent.py, whose TOOL_CONTEXT this module
    # imports. Change both together or the prompt will describe a tool the web
    # backend does not have.
    {
        "name": "judge",
        "description": (
            "Ask Jev, a fast classification model, for a typed judgment about a document. "
            "Use it only at the decision points named in the workspace guide. It answers "
            "with labels, confidence, and what each one implies. It never writes a file "
            "and it never decides anything. When Jev is unavailable it says so and you "
            "carry on with the manual checklist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_set": {
                    "type": "string",
                    "enum": [
                        "fr_triage", "gate_review", "cr_assessment",
                        "conflict_pair", "rice_bands",
                    ]
                },
                "content": {"type": "string"},
                "context": {"type": "string"}
            },
            "required": ["question_set", "content"]
        }
    }
]


def execute_tool(name: str, args: dict) -> str:
    try:
        ws = _get_workspace()
        if name == "read_file":
            p = ws / args["path"]
            return p.read_text() if p.exists() else f"File not found: {args['path']}"

        elif name == "write_file":
            p = ws / args["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"Written: {args['path']}"

        elif name == "list_files":
            d = ws / args.get("directory", ".")
            if not d.exists():
                return "Directory not found"
            files = sorted(
                str(f.relative_to(ws))
                for f in d.rglob("*")
                if f.is_file() and not f.name.startswith(".")
            )
            return "\n".join(files) if files else "(empty)"

        elif name == "search_files":
            r = subprocess.run(
                ["grep", "-r", "-l", "--include=*.md", args["query"],
                 str(ws / args.get("directory", "."))],
                capture_output=True, text=True, timeout=10
            )
            lines = [str(Path(l).relative_to(ws)) for l in r.stdout.strip().splitlines() if l]
            return "\n".join(lines) if lines else "No results"

        elif name == "scan_tags":
            bot_dir = str(ws / "bot")
            if bot_dir not in sys.path:
                sys.path.insert(0, bot_dir)
            try:
                import tags
            except ImportError:
                return (
                    "Tag scanning is unavailable in this deployment. Say so rather than "
                    "reading the PRDs yourself, because a scan you do by eye can miss a "
                    "pair without anyone noticing."
                )
            return tags.scan(ws, args.get("project", ""), args.get("sprint", ""))

        elif name == "judge":
            # jev.py ships with the bot. A backend-only deployment will not have it,
            # so fall through to the manual flow instead of erroring the whole turn.
            bot_dir = str(ws / "bot")
            if bot_dir not in sys.path:
                sys.path.insert(0, bot_dir)
            try:
                import jev
            except ImportError:
                return (
                    "Jev is unavailable, so there is no automated judgment for this "
                    "step. Continue with the manual checklist and say that the check "
                    "was skipped."
                )
            return jev.judge(
                args.get("question_set", ""),
                args.get("content", ""),
                args.get("context", ""),
            )

        elif name == "move_file":
            src = ws / args["source"]
            dst = ws / args["destination"]
            if not src.exists():
                return f"Source not found: {args['source']}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return f"Moved: {args['source']} -> {args['destination']}"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error in {name}: {e}"


import re as _re

def _parse_xml_tool_calls(text):
    """Parse XML-style function calls: <function=name{args}></function>"""
    results = []
    if not text:
        return results
    pattern = r'<function=(\w+)\s*?(\{(?:[^{}]|\{[^{}]*\})*\})\s*>?\s*</function>'
    for name, args_str in _re.findall(pattern, text, _re.DOTALL):
        try:
            results.append((name, json.loads(args_str)))
        except Exception:
            pass
    return results


def _strip_xml_calls(text):
    """Remove XML function call tags from text."""
    return _re.sub(
        r'<function=\w+\s*?\{(?:[^{}]|\{[^{}]*\})*\}\s*>?\s*</function>',
        '', text or '', flags=_re.DOTALL
    ).strip()


def load_system_prompt() -> str:
    p = _get_workspace() / "CLAUDE.md"
    base = p.read_text() if p.exists() else "You are an AI Product Management co-pilot."
    # Import TOOL_CONTEXT from the bot agent if available
    try:
        import sys
        sys.path.insert(0, str(_get_workspace() / "bot"))
        from agent import TOOL_CONTEXT
        return base + TOOL_CONTEXT
    except ImportError:
        return base


# ── Streaming agent for web (yields SSE events) ──────────────────────────────

async def run_agent_stream(
    user_message: str,
    history: list[dict],
    provider: str = "anthropic",
    api_key: str = "",
    model: str = "",
) -> AsyncGenerator[str, None]:
    """
    Run the AI agent and yield SSE-formatted events.
    Yields:
      data: {"type": "text_delta", "text": "..."}
      data: {"type": "tool_use", "name": "...", "path": "..."}
      data: {"type": "tool_result", "result": "..."}
      data: {"type": "done", "suggestions": [...]}
      data: {"type": "error", "message": "..."}
    """
    system = load_system_prompt()
    history.append({"role": "user", "content": user_message})
    msgs = list(history)

    try:
        if provider == "anthropic":
            async for event in _stream_anthropic(system, msgs, api_key, model):
                yield event
        elif provider in ("openai", "groq", "ollama"):
            async for event in _stream_openai(system, msgs, api_key, model, provider):
                yield event
        elif provider in ("google", "gemini"):
            async for event in _stream_gemini(system, msgs, api_key, model):
                yield event
        else:
            yield _sse({"type": "error", "message": f"Unknown provider: {provider}"})
    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _extract_suggestions(text: str) -> list[str]:
    import re
    pattern = r'(?:What to do next|Next steps?):\s*\n((?:[-*]\s*"[^"]+".+\n?)+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return []
    cmds = []
    for line in match.group(1).split("\n"):
        q = re.search(r'"([^"]{3,60})"', line)
        if q:
            cmds.append(q.group(1))
    return cmds[:3]


MAX_ITER = 15


async def _stream_anthropic(system, msgs, api_key, model):
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key)
    model = model or "claude-sonnet-4-6"
    sys_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    full_text = ""

    for _ in range(MAX_ITER):
        resp = await client.messages.create(
            model=model, max_tokens=8192,
            system=sys_blocks, tools=TOOLS, messages=msgs
        )
        msgs.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            full_text = text
            # Stream text in chunks
            for chunk in _split_chunks(text, 50):
                yield _sse({"type": "text_delta", "text": chunk})
            break

        if resp.stop_reason == "tool_use":
            results = []
            for b in resp.content:
                if b.type == "tool_use":
                    yield _sse({"type": "tool_use", "name": b.name, "input": b.input})
                    result = await asyncio.to_thread(execute_tool, b.name, b.input)
                    yield _sse({"type": "tool_result", "name": b.name, "result": result[:200]})
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": result})
            msgs.append({"role": "user", "content": results})

    suggestions = _extract_suggestions(full_text)
    yield _sse({"type": "done", "suggestions": suggestions})


async def _stream_openai(system, msgs, api_key, model, provider):
    from openai import AsyncOpenAI
    base_url = None
    if provider == "groq":
        base_url = "https://api.groq.com/openai/v1"
    elif provider == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    client = AsyncOpenAI(api_key=api_key or "ollama", base_url=base_url)
    model = model or "gpt-4o-mini"
    oai_tools = [{"type": "function", "function": {
        "name": t["name"], "description": t["description"], "parameters": t["input_schema"]
    }} for t in TOOLS]
    oai_msgs = [{"role": "system", "content": system}]
    for m in msgs:
        if isinstance(m["content"], str):
            oai_msgs.append({"role": m["role"], "content": m["content"]})

    full_text = ""
    import json as json_mod
    for _ in range(MAX_ITER):
        resp = await client.chat.completions.create(model=model, messages=oai_msgs, tools=oai_tools)
        choice = resp.choices[0].message
        if not choice.tool_calls:
            full_text = choice.content or ""
            for chunk in _split_chunks(full_text, 50):
                yield _sse({"type": "text_delta", "text": chunk})
            break
        oai_msgs.append(choice)
        for tc in choice.tool_calls:
            args = json_mod.loads(tc.function.arguments)
            yield _sse({"type": "tool_use", "name": tc.function.name, "input": args})
            result = await asyncio.to_thread(execute_tool, tc.function.name, args)
            yield _sse({"type": "tool_result", "name": tc.function.name, "result": result[:200]})
            oai_msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    suggestions = _extract_suggestions(full_text)
    yield _sse({"type": "done", "suggestions": suggestions})


async def _stream_gemini(system, msgs, api_key, model):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model_name = model or "gemini-2.0-flash"
    gem_tools = [{"function_declarations": [
        {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
        for t in TOOLS
    ]}]
    g_model = genai.GenerativeModel(model_name, system_instruction=system, tools=gem_tools)
    history_g = []
    for m in msgs[:-1]:
        if isinstance(m["content"], str):
            history_g.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
    chat = g_model.start_chat(history=history_g)
    last_input = msgs[-1]["content"] if msgs else ""
    full_text = ""

    for _ in range(MAX_ITER):
        resp = await asyncio.to_thread(chat.send_message, last_input)
        part = resp.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            args = dict(fc.args)
            yield _sse({"type": "tool_use", "name": fc.name, "input": args})
            result = await asyncio.to_thread(execute_tool, fc.name, args)
            yield _sse({"type": "tool_result", "name": fc.name, "result": result[:200]})
            last_input = [{"function_response": {"name": fc.name, "response": {"result": result}}}]
        else:
            full_text = part.text or ""
            for chunk in _split_chunks(full_text, 50):
                yield _sse({"type": "text_delta", "text": chunk})
            break

    suggestions = _extract_suggestions(full_text)
    yield _sse({"type": "done", "suggestions": suggestions})


def _split_chunks(text: str, size: int = 50) -> list[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]
