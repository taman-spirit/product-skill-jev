"""
Test configuration and fixtures.
Tests run against the live Docker backend (localhost:8000) and
also directly test backend logic without HTTP.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest

# Allow importing backend modules directly
BACKEND_PATH = Path(__file__).parent.parent / "apps" / "backend"
sys.path.insert(0, str(BACKEND_PATH))

# Use a temporary workspace for tests
@pytest.fixture(scope="session")
def tmp_workspace(tmp_path_factory):
    ws = tmp_path_factory.mktemp("workspace")
    (ws / "_system").mkdir()
    (ws / "my-projects").mkdir()
    # Set env var so backend modules use this workspace
    os.environ["WORKSPACE_PATH"] = str(ws)
    yield ws
    # Cleanup handled by pytest


@pytest.fixture
def api_base():
    return "http://localhost:8000"


@pytest.fixture
def api_available(api_base):
    """Skip test if backend is not running."""
    import httpx
    try:
        r = httpx.get(f"{api_base}/api/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False
