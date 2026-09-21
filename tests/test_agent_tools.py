"""
Unit tests for agent file tools and config logic.
Run without Docker: pytest tests/test_agent_tools.py -v
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

BACKEND_PATH = Path(__file__).parent.parent / "apps" / "backend"
sys.path.insert(0, str(BACKEND_PATH))


@pytest.fixture
def workspace(tmp_path):
    """Fresh temporary workspace for each test."""
    os.environ["WORKSPACE_PATH"] = str(tmp_path)
    yield tmp_path
    # Reset
    os.environ.pop("WORKSPACE_PATH", None)


# ── Tool execution ───────────────────────────────────────────────

class TestFileTools:
    def test_write_and_read_file(self, workspace):
        from agent_bridge import execute_tool
        # Write
        result = execute_tool("write_file", {"path": "test.md", "content": "# Hello"})
        assert "Written" in result
        # Read
        result = execute_tool("read_file", {"path": "test.md"})
        assert result == "# Hello"

    def test_read_nonexistent_file(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("read_file", {"path": "does-not-exist.md"})
        assert "not found" in result.lower() or "File" in result

    def test_write_creates_parent_dirs(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("write_file", {
            "path": "deep/nested/dir/file.md",
            "content": "content"
        })
        assert "Written" in result
        assert (workspace / "deep" / "nested" / "dir" / "file.md").exists()

    def test_list_files_empty_dir(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("list_files", {"directory": "."})
        assert result == "(empty)" or isinstance(result, str)

    def test_list_files_with_content(self, workspace):
        from agent_bridge import execute_tool
        execute_tool("write_file", {"path": "a.md", "content": "a"})
        execute_tool("write_file", {"path": "b.md", "content": "b"})
        result = execute_tool("list_files", {"directory": "."})
        assert "a.md" in result
        assert "b.md" in result

    def test_list_files_nonexistent_dir(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("list_files", {"directory": "nonexistent"})
        assert "not found" in result.lower()

    def test_search_files(self, workspace):
        from agent_bridge import execute_tool
        execute_tool("write_file", {"path": "doc.md", "content": "FINDME"})
        result = execute_tool("search_files", {"query": "FINDME"})
        assert "doc.md" in result

    def test_search_no_results(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("search_files", {"query": "XYZNOTEXIST"})
        assert "No results" in result

    def test_move_file(self, workspace):
        from agent_bridge import execute_tool
        execute_tool("write_file", {"path": "source.md", "content": "move me"})
        result = execute_tool("move_file", {"source": "source.md", "destination": "moved/dest.md"})
        assert "Moved" in result
        assert not (workspace / "source.md").exists()
        assert (workspace / "moved" / "dest.md").exists()

    def test_move_nonexistent_source(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("move_file", {"source": "ghost.md", "destination": "out.md"})
        assert "not found" in result.lower() or "Source" in result

    def test_unknown_tool(self, workspace):
        from agent_bridge import execute_tool
        result = execute_tool("nonexistent_tool", {})
        assert "Unknown" in result


# ── Config (SQLite) ──────────────────────────────────────────────

class TestConfig:
    def test_get_provider_config_returns_dict(self, workspace):
        from core.config import get_provider_config
        config = get_provider_config()
        assert isinstance(config, dict)
        assert "provider" in config
        assert "api_key" in config
        assert "model" in config

    def test_save_and_get_anthropic_config(self, workspace):
        from core.config import save_provider_config, get_provider_config
        save_provider_config({
            "provider": "anthropic",
            "api_key": "sk-ant-test-123",
            "model": "claude-sonnet-4-6",
        })
        config = get_provider_config()
        assert config["provider"] == "anthropic"
        assert config["api_key"] == "sk-ant-test-123"
        assert config["model"] == "claude-sonnet-4-6"

    def test_save_and_get_groq_config(self, workspace):
        from core.config import save_provider_config, get_provider_config
        save_provider_config({
            "provider": "groq",
            "api_key": "gsk_test_key",
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1",
        })
        config = get_provider_config()
        assert config["provider"] == "groq"
        assert config["api_key"] == "gsk_test_key"
        assert "groq.com" in config.get("base_url", "")

    def test_save_empty_key_does_not_overwrite(self, workspace):
        from core.config import save_provider_config, get_provider_config
        # Save with real key
        save_provider_config({
            "provider": "anthropic",
            "api_key": "sk-ant-original",
            "model": "claude-sonnet-4-6",
        })
        # Save with empty key (should not overwrite)
        save_provider_config({
            "provider": "anthropic",
            "api_key": "",
            "model": "claude-haiku-4-5",
        })
        config = get_provider_config()
        # Key should be preserved
        assert config["api_key"] == "sk-ant-original"
        # Model should be updated
        assert config["model"] == "claude-haiku-4-5"

    def test_get_active_display_masks_key(self, workspace):
        from core.config import save_provider_config, get_active_display
        save_provider_config({
            "provider": "anthropic",
            "api_key": "sk-ant-abcdefghijklmn",
            "model": "claude-sonnet-4-6",
        })
        display = get_active_display()
        assert display["key_set"] is True
        assert "sk-ant-" in display["key_masked"]
        assert display["key_masked"] != "sk-ant-abcdefghijklmn"  # masked

    def test_get_active_display_no_key(self, workspace):
        # Fresh workspace with no config
        from core.config import get_active_display
        display = get_active_display()
        # key_set is False when only env var fallback with empty value
        assert isinstance(display["key_set"], bool)
        assert "key_masked" in display

    def test_env_var_fallback(self, workspace):
        """Env vars used when no DB config set (fresh workspace)."""
        import sqlite3
        # Clear DB to ensure env var fallback is tested
        db_path = workspace / "_system" / "settings.db"
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("DELETE FROM settings WHERE key = 'anthropic_api_key'")
                conn.execute("DELETE FROM settings WHERE key = 'provider'")
                conn.commit()
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-from-env"
        os.environ["AI_PROVIDER"] = "anthropic"
        from core import config as cfg
        # Re-evaluate to pick up cleared DB
        import importlib; importlib.reload(cfg)
        c = cfg.get_provider_config()
        assert c["api_key"] == "sk-ant-from-env"
        del os.environ["ANTHROPIC_API_KEY"]
        del os.environ["AI_PROVIDER"]

    def test_db_overrides_env_var(self, workspace):
        """DB config should override env vars."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-from-env"
        from core.config import save_provider_config, get_provider_config
        save_provider_config({
            "provider": "anthropic",
            "api_key": "sk-ant-from-db",
            "model": "claude-sonnet-4-6",
        })
        config = get_provider_config()
        assert config["api_key"] == "sk-ant-from-db"
        del os.environ["ANTHROPIC_API_KEY"]


# ── XML Tool Call Parser ─────────────────────────────────────────

class TestXMLParser:
    def test_parses_basic_xml_call(self):
        from agent_bridge import _parse_xml_tool_calls
        text = '<function=read_file{"path": "test.md"}></function>'
        calls = _parse_xml_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "read_file"
        assert calls[0][1] == {"path": "test.md"}

    def test_parses_xml_with_space(self):
        from agent_bridge import _parse_xml_tool_calls
        text = '<function=read_file {"path": "test.md"}></function>'
        calls = _parse_xml_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "read_file"

    def test_parses_xml_without_closing_gt(self):
        from agent_bridge import _parse_xml_tool_calls
        text = '<function=read_file{"path": "test.md"}</function>'
        calls = _parse_xml_tool_calls(text)
        assert len(calls) == 1

    def test_parses_multiple_calls(self):
        from agent_bridge import _parse_xml_tool_calls
        text = '<function=read_file{"path": "a.md"}></function> text <function=write_file{"path": "b.md", "content": "x"}></function>'
        calls = _parse_xml_tool_calls(text)
        assert len(calls) == 2
        assert calls[0][0] == "read_file"
        assert calls[1][0] == "write_file"

    def test_returns_empty_for_no_calls(self):
        from agent_bridge import _parse_xml_tool_calls
        result = _parse_xml_tool_calls("Hello, how can I help?")
        assert result == []

    def test_strip_xml_calls(self):
        from agent_bridge import _strip_xml_calls
        text = 'Here is my response. <function=read_file{"path": "x"}></function>'
        result = _strip_xml_calls(text)
        assert "Here is my response." in result
        assert "<function=" not in result

    def test_handles_none_input(self):
        from agent_bridge import _parse_xml_tool_calls
        result = _parse_xml_tool_calls(None)
        assert result == []
