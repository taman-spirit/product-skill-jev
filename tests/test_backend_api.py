"""
Integration tests against live backend (localhost:8000).
Run with: pytest tests/test_backend_api.py -v
"""
import json
import pytest
import httpx

BASE = "http://localhost:8000"


@pytest.fixture(autouse=True)
def require_backend():
    try:
        r = httpx.get(f"{BASE}/api/health", timeout=3)
        if r.status_code != 200:
            pytest.skip("Backend not running")
    except Exception:
        pytest.skip("Backend not reachable at localhost:8000")


# ── Health ───────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self):
        r = httpx.get(f"{BASE}/api/health")
        assert r.status_code == 200

    def test_health_has_status_ok(self):
        r = httpx.get(f"{BASE}/api/health")
        data = r.json()
        assert data["status"] == "ok"

    def test_health_has_version(self):
        r = httpx.get(f"{BASE}/api/health")
        data = r.json()
        assert "version" in data
        assert data["version"] == "1.0.0"


# ── Settings ─────────────────────────────────────────────────────

class TestSettings:
    def test_get_providers_returns_list(self):
        r = httpx.get(f"{BASE}/api/settings/providers")
        assert r.status_code == 200
        data = r.json()
        assert "available_providers" in data
        assert isinstance(data["available_providers"], list)
        assert len(data["available_providers"]) >= 4

    def test_get_providers_includes_anthropic(self):
        r = httpx.get(f"{BASE}/api/settings/providers")
        providers = {p["id"] for p in r.json()["available_providers"]}
        assert "anthropic" in providers

    def test_get_providers_has_active_info(self):
        r = httpx.get(f"{BASE}/api/settings/providers")
        data = r.json()
        assert "active" in data
        active = data["active"]
        assert "provider" in active
        assert "model" in active
        assert "key_set" in active
        assert "key_masked" in active

    def test_save_provider_returns_saved(self):
        r = httpx.post(f"{BASE}/api/settings/providers", json={
            "provider": "anthropic",
            "api_key": "sk-ant-test-key-123456789",
            "model": "claude-sonnet-4-6",
            "base_url": "",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "saved"
        assert data["provider"] == "anthropic"

    def test_save_provider_persists(self):
        # Save a provider
        httpx.post(f"{BASE}/api/settings/providers", json={
            "provider": "anthropic",
            "api_key": "sk-ant-persist-test-key",
            "model": "claude-haiku-4-5",
            "base_url": "",
        })
        # Read back
        r = httpx.get(f"{BASE}/api/settings/providers")
        data = r.json()
        assert data["active"]["provider"] == "anthropic"
        assert data["active"]["model"] == "claude-haiku-4-5"
        assert data["active"]["key_set"] is True

    def test_test_provider_rejects_empty_key(self):
        r = httpx.post(f"{BASE}/api/settings/providers/test", json={
            "provider": "anthropic",
            "api_key": "",
            "model": "claude-sonnet-4-6",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "error"
        assert "required" in data["message"].lower() or "key" in data["message"].lower()

    def test_get_workspace_info(self):
        r = httpx.get(f"{BASE}/api/settings/workspace")
        assert r.status_code == 200
        data = r.json()
        assert "path" in data
        assert "exists" in data
        assert "project_count" in data


# ── Projects ─────────────────────────────────────────────────────

class TestProjects:
    def test_list_projects_returns_list(self):
        r = httpx.get(f"{BASE}/api/projects")
        assert r.status_code == 200
        data = r.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)

    def test_get_nonexistent_project_returns_404(self):
        r = httpx.get(f"{BASE}/api/projects/PROJ-999-nonexistent")
        assert r.status_code == 404

    def test_list_projects_has_required_fields(self):
        r = httpx.get(f"{BASE}/api/projects")
        projects = r.json()["projects"]
        if projects:
            p = projects[0]
            assert "id" in p
            assert "name" in p
            assert "status" in p


# ── Documents ────────────────────────────────────────────────────

class TestDocuments:
    def test_read_nonexistent_file_returns_404(self):
        r = httpx.get(f"{BASE}/api/documents/read", params={"path": "nonexistent/file.md"})
        assert r.status_code == 404

    def test_path_traversal_blocked(self):
        r = httpx.get(f"{BASE}/api/documents/read", params={"path": "../../etc/passwd"})
        assert r.status_code in (403, 404)

    def test_write_and_read_file(self):
        test_path = "_test_write_read.md"
        content = "# Test\nThis is a test file."
        # Write
        w = httpx.post(f"{BASE}/api/documents/write", json={
            "path": test_path,
            "content": content,
        })
        assert w.status_code == 200
        assert w.json()["status"] == "written"
        # Read back
        r = httpx.get(f"{BASE}/api/documents/read", params={"path": test_path})
        assert r.status_code == 200
        assert r.json()["content"] == content


# ── Chat ─────────────────────────────────────────────────────────

class TestChat:
    def test_chat_stream_returns_sse(self):
        """Chat stream should return data: lines (SSE format)."""
        with httpx.stream("POST", f"{BASE}/api/chat/stream",
                          json={"message": "hello", "session_id": "test-unit"},
                          timeout=15) as r:
            assert r.status_code == 200
            first_line = ""
            for line in r.iter_lines():
                if line:
                    first_line = line
                    break
            assert first_line.startswith("data:"), f"Expected SSE, got: {first_line}"

    def test_chat_stream_returns_valid_json(self):
        """Each SSE data line should be valid JSON."""
        with httpx.stream("POST", f"{BASE}/api/chat/stream",
                          json={"message": "hi", "session_id": "test-json"},
                          timeout=15) as r:
            for line in r.iter_lines():
                if line.startswith("data: "):
                    payload = json.loads(line[6:])
                    assert "type" in payload
                    break

    def test_chat_stream_ends_with_done_or_error(self):
        """Stream must end with a 'done' or 'error' event."""
        events = []
        with httpx.stream("POST", f"{BASE}/api/chat/stream",
                          json={"message": "hi", "session_id": "test-done"},
                          timeout=20) as r:
            for line in r.iter_lines():
                if line.startswith("data: "):
                    try:
                        evt = json.loads(line[6:])
                        events.append(evt)
                    except Exception:
                        pass
        assert len(events) > 0, "No events received"
        last_type = events[-1].get("type")
        assert last_type in ("done", "error"), f"Last event type: {last_type}"

    def test_chat_reset_clears_history(self):
        r = httpx.post(f"{BASE}/api/chat/reset", params={"session_id": "test-reset"})
        assert r.status_code == 200
        assert r.json()["status"] == "cleared"

    def test_chat_history_returns_list(self):
        r = httpx.get(f"{BASE}/api/chat/history", params={"session_id": "test-hist"})
        assert r.status_code == 200
        data = r.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)


# ── Audit ─────────────────────────────────────────────────────────

class TestAudit:
    def test_audit_returns_entries(self):
        r = httpx.get(f"{BASE}/api/audit")
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_audit_entries_have_required_fields(self):
        r = httpx.get(f"{BASE}/api/audit")
        entries = r.json()["entries"]
        if entries:
            e = entries[0]
            assert "timestamp" in e
            assert "project" in e
            assert "document" in e
            assert "action" in e


# ── Attachments ──────────────────────────────────────────────────

class TestAttachments:
    def test_list_attachments_returns_list(self):
        r = httpx.get(f"{BASE}/api/attachments/list")
        assert r.status_code == 200
        data = r.json()
        assert "attachments" in data

    def test_upload_text_file(self):
        r = httpx.post(
            f"{BASE}/api/attachments/upload",
            files={"file": ("test.txt", b"Hello world", "text/plain")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["filename"] == "test.txt"
        assert "content" in data
        assert "Hello world" in data["content"]

    def test_upload_markdown_file(self):
        md_content = b"# Title\n\nThis is markdown."
        r = httpx.post(
            f"{BASE}/api/attachments/upload",
            files={"file": ("test.md", md_content, "text/markdown")},
        )
        assert r.status_code == 200
        data = r.json()
        assert "Title" in data["content"]
