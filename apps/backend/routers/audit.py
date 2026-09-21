"""Audit log - timeline of document changes across all projects."""
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()
WORKSPACE = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))


def _parse_versions_md(path: Path, project_id: str) -> list[dict]:
    """Parse VERSIONS.md to extract change events."""
    if not path.exists():
        return []
    entries = []
    content = path.read_text()
    for line in content.split("\n"):
        if not line.startswith("| v") and not line.startswith("| PRD") and not line.startswith("| EP"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 4:
            continue
        version = parts[0] if parts[0].startswith("v") else None
        doc_name = parts[1] if len(parts) > 1 else ""
        status = parts[3] if len(parts) > 3 else ""
        date_str = parts[6] if len(parts) > 6 else parts[-1]
        if version and status and date_str and "/" in date_str:
            action = "approved" if status == "approved" else "created" if "initial" in status.lower() else "updated"
            try:
                d = datetime.strptime(date_str, "%d/%m/%Y")
                ts = d.isoformat()
            except Exception:
                ts = date_str
            entries.append({
                "timestamp": ts,
                "project": project_id,
                "document": doc_name,
                "version": version,
                "action": action,
                "path": str(path.relative_to(WORKSPACE)),
            })
    return entries


def _scan_file_changes(project_path: Path, project_id: str) -> list[dict]:
    """Scan all .md files for modification time-based audit entries."""
    entries = []
    for subdir in ["discovery/inbox", "discovery/scoring", "prd", "epics", "cr/approved", "cr/intake"]:
        d = project_path / subdir
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            if f.name.startswith("_"):
                continue
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            # Determine action from filename/path
            action = "approved" if "approved" in str(f) else "created"
            if "v" in f.stem and "." in f.stem:
                parts = f.stem.rsplit("v", 1)
                if len(parts) == 2 and "." in parts[1]:
                    action = "versioned"
            entries.append({
                "timestamp": mtime.isoformat(),
                "project": project_id,
                "document": f.name,
                "action": action,
                "path": str(f.relative_to(WORKSPACE)),
                "user": "",
            })
    return entries


@router.get("")
async def get_audit_log(project_id: str = ""):
    """Return all audit entries, sorted by timestamp desc."""
    projects_dir = WORKSPACE / "my-projects"
    if not projects_dir.exists():
        return {"entries": []}

    all_entries = []

    if project_id:
        dirs = [projects_dir / project_id]
    else:
        dirs = [d for d in projects_dir.iterdir() if d.is_dir() and d.name.startswith("PROJ-")]

    for project_path in dirs:
        pid = project_path.name
        # From VERSIONS.md
        versions_md = project_path / "VERSIONS.md"
        all_entries.extend(_parse_versions_md(versions_md, pid))
        # From file modification times
        all_entries.extend(_scan_file_changes(project_path, pid))

    # Deduplicate by path + action
    seen = set()
    unique = []
    for e in all_entries:
        key = f"{e['path']}:{e['action']}"
        if key not in seen:
            seen.add(key)
            unique.append(e)

    # Sort by timestamp descending
    unique.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"entries": unique[:200]}
