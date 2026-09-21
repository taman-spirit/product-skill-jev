"""Projects router - reads workspace files to build project data."""
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
import re

router = APIRouter()
WORKSPACE = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML-style frontmatter from markdown."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ": " in line:
            k, v = line.split(": ", 1)
            fm[k.strip()] = v.strip()
    return fm


def _list_projects() -> list[dict]:
    """Scan my-projects/ for PROJ-* folders."""
    projects_dir = WORKSPACE / "my-projects"
    if not projects_dir.exists():
        return []
    projects = []
    for folder in sorted(projects_dir.iterdir()):
        if folder.is_dir() and folder.name.startswith("PROJ-"):
            project_md = folder / "PROJECT.md"
            if project_md.exists():
                content = project_md.read_text()
                fm = _parse_frontmatter(content)
                projects.append({
                    "id": folder.name,
                    "name": fm.get("title", folder.name),
                    "status": fm.get("status", "unknown"),
                    "priority": fm.get("priority", ""),
                    "product": fm.get("product", ""),
                    "pm": fm.get("pm", ""),
                    "start": fm.get("start", ""),
                    "target_end": fm.get("target-end", ""),
                    "path": str(folder.relative_to(WORKSPACE)),
                })
    return projects


def _count_items(project_path: Path, subfolder: str, pattern: str = "*.md") -> int:
    d = project_path / subfolder
    if not d.exists():
        return 0
    return len(list(d.glob(pattern)))


def _get_project_health(project_path: Path) -> dict:
    """Build health metrics for a project."""
    inbox = project_path / "discovery" / "inbox"
    scoring = project_path / "discovery" / "scoring"
    gate_approved = project_path / "discovery" / "gate" / "approved.md"
    prd_dir = project_path / "prd"
    cr_log = project_path / "cr" / "cr-log.md"

    fr_count = len(list(inbox.glob("FR-*.md"))) if inbox.exists() else 0
    scored_count = len(list(scoring.glob("RICE-*.md"))) if scoring.exists() else 0
    gate_approved_count = 0
    if gate_approved.exists():
        content = gate_approved.read_text()
        gate_approved_count = len([l for l in content.split("\n") if l.startswith("| FR-")])

    prd_count = 0
    prd_approved = 0
    if prd_dir.exists():
        for prd_folder in prd_dir.iterdir():
            if prd_folder.is_dir():
                prd_count += 1
                for f in prd_folder.glob("*.md"):
                    if "v" in f.stem:
                        content = f.read_text()
                        if "status: approved" in content:
                            prd_approved += 1
                            break

    open_crs = 0
    if cr_log.exists():
        content = cr_log.read_text()
        open_crs = len([l for l in content.split("\n")
                        if "| CR-" in l and ("intake" in l or "assessment" in l)])

    return {
        "fr_count": fr_count,
        "fr_scored": scored_count,
        "fr_gate_approved": gate_approved_count,
        "prd_count": prd_count,
        "prd_approved": prd_approved,
        "open_crs": open_crs,
    }


@router.get("")
async def list_projects():
    return {"projects": _list_projects()}


@router.get("/{project_id}")
async def get_project(project_id: str):
    project_path = WORKSPACE / "my-projects" / project_id
    if not project_path.exists():
        raise HTTPException(404, f"Project {project_id} not found")

    project_md = project_path / "PROJECT.md"
    content = project_md.read_text() if project_md.exists() else ""
    fm = _parse_frontmatter(content)

    # Extract milestones from content
    milestones = []
    for line in content.split("\n"):
        if line.startswith("| M") and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                milestones.append({
                    "id": parts[0],
                    "name": parts[1],
                    "target": parts[2] if len(parts) > 2 else "",
                    "status": parts[3] if len(parts) > 3 else "Pending",
                })

    health = _get_project_health(project_path)

    return {
        "id": project_id,
        "name": fm.get("title", project_id),
        "status": fm.get("status", "planning"),
        "priority": fm.get("priority", ""),
        "product": fm.get("product", ""),
        "pm": fm.get("pm", ""),
        "start": fm.get("start", ""),
        "target_end": fm.get("target-end", ""),
        "milestones": milestones,
        "health": health,
        "content": content,
    }


@router.get("/{project_id}/discovery")
async def get_discovery(project_id: str):
    base = WORKSPACE / "my-projects" / project_id / "discovery"
    if not base.exists():
        return {"frs": [], "scored": [], "approved": []}

    frs = []
    for f in sorted((base / "inbox").glob("FR-*.md")) if (base / "inbox").exists() else []:
        content = f.read_text()
        fm = _parse_frontmatter(content)
        frs.append({
            "id": f.stem,
            "title": fm.get("title", f.stem),
            "status": fm.get("status", "draft"),
            "rice_score": fm.get("rice-score", "not scored"),
            "gate_status": fm.get("gate-status", "not reviewed"),
            "file": str(f.relative_to(WORKSPACE)),
        })

    return {"frs": frs}


@router.get("/{project_id}/prd")
async def get_prds(project_id: str):
    prd_dir = WORKSPACE / "my-projects" / project_id / "prd"
    if not prd_dir.exists():
        return {"prds": []}

    prds = []
    for folder in sorted(prd_dir.iterdir()):
        if folder.is_dir():
            versions = []
            for f in sorted(folder.glob("PRD-*.md")):
                content = f.read_text()
                fm = _parse_frontmatter(content)
                versions.append({
                    "file": f.name,
                    "version": fm.get("version", "v1.0"),
                    "status": fm.get("status", "draft"),
                    "approved_by": fm.get("approved-by", ""),
                    "path": str(f.relative_to(WORKSPACE)),
                })
            if versions:
                latest = versions[-1]
                prds.append({
                    "id": folder.name,
                    "current_version": latest["version"],
                    "status": latest["status"],
                    "versions": versions,
                })

    return {"prds": prds}


@router.get("/{project_id}/stakeholders")
async def get_stakeholders(project_id: str):
    sh_dir = WORKSPACE / "my-projects" / project_id / "stakeholders"
    if not sh_dir.exists():
        return {"stakeholders": []}

    stakeholders = []
    for f in sorted(sh_dir.glob("SH-*.md")):
        content = f.read_text()
        fm = _parse_frontmatter(content)
        stakeholders.append({
            "id": f.stem,
            "name": fm.get("name", f.stem),
            "title": fm.get("title", ""),
            "power": fm.get("power", ""),
            "interest": fm.get("interest", ""),
            "quadrant": fm.get("quadrant", ""),
            "channel": fm.get("channel", ""),
            "file": str(f.relative_to(WORKSPACE)),
        })

    return {"stakeholders": stakeholders}


@router.get("/{project_id}/cr")
async def get_crs(project_id: str):
    cr_base = WORKSPACE / "my-projects" / project_id / "cr"
    if not cr_base.exists():
        return {"crs": []}

    crs = []
    for stage in ["intake", "assessment", "approval-board", "approved", "rejected"]:
        stage_dir = cr_base / stage
        if stage_dir.exists():
            for f in sorted(stage_dir.glob("CR-*.md")):
                content = f.read_text()
                fm = _parse_frontmatter(content)
                crs.append({
                    "id": f.stem,
                    "title": fm.get("title", f.stem),
                    "stage": stage,
                    "urgency": fm.get("urgency", ""),
                    "linked_prd": fm.get("linked-prd", ""),
                    "file": str(f.relative_to(WORKSPACE)),
                })

    return {"crs": crs}


import shutil
from datetime import date

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Move project to _deleted/ with 3-month retention."""
    project_path = WORKSPACE / "my-projects" / project_id
    if not project_path.exists():
        raise HTTPException(404, f"Project {project_id} not found")

    # Create _deleted/ folder
    deleted_dir = WORKSPACE / "_deleted" / date.today().isoformat()
    deleted_dir.mkdir(parents=True, exist_ok=True)

    dest = deleted_dir / project_id
    shutil.move(str(project_path), str(dest))

    # Log deletion
    log_path = WORKSPACE / "_deleted" / "deletion-log.md"
    entry = f"| {project_id} | {date.today().isoformat()} | {dest} | Delete after {date.today().replace(month=date.today().month + 3 if date.today().month < 10 else (date.today().month - 9), year=date.today().year + (1 if date.today().month >= 10 else 0))} |\n"
    with open(log_path, "a") as f:
        f.write(entry)

    return {"status": "deleted", "project_id": project_id, "moved_to": str(dest.relative_to(WORKSPACE))}


@router.get("/{project_id}/files")
async def list_project_files(project_id: str, folder: str = ""):
    """List files and subfolders in a project directory for the file browser."""
    project_path = WORKSPACE / "my-projects" / project_id
    if not project_path.exists():
        raise HTTPException(404, f"Project {project_id} not found")

    target = project_path / folder if folder else project_path
    if not target.exists():
        return {"items": []}

    items = []
    for entry in sorted(target.iterdir()):
        if entry.name.startswith(".") or entry.name.startswith("__"):
            continue
        rel = str(entry.relative_to(WORKSPACE))
        if entry.is_dir():
            # Count children
            children = [f for f in entry.iterdir() if not f.name.startswith(".")]
            items.append({
                "name": entry.name,
                "path": rel,
                "type": "folder",
                "children": len(children),
            })
        else:
            stat = entry.stat()
            items.append({
                "name": entry.name,
                "path": rel,
                "type": "file",
                "ext": entry.suffix.lower(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })

    return {"items": items, "folder": folder, "project": project_id}


# ── Status update ─────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel

class StatusUpdate(_BaseModel):
    path: str
    status: str  # draft | in-review | approved | archived


@router.patch("/{project_id}/status")
async def update_document_status(project_id: str, body: StatusUpdate):
    """Update the status field in a document's frontmatter."""
    file_path = WORKSPACE / body.path
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    content = file_path.read_text()
    # Replace status in frontmatter
    import re as _re
    new_content = _re.sub(
        r'^(status:\s*).*$',
        f'\\g<1>{body.status}',
        content, flags=_re.MULTILINE
    )
    file_path.write_text(new_content)
    return {"path": body.path, "status": body.status}


# ── Create items ──────────────────────────────────────────────────────────────

from datetime import date as _date

class NewFR(_BaseModel):
    title: str
    description: str = ""
    source: str = "internal"


@router.post("/{project_id}/fr")
async def create_fr(project_id: str, body: NewFR):
    """Create a new Feature Request in the project."""
    inbox = WORKSPACE / "my-projects" / project_id / "discovery" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    # Next FR number
    existing = sorted(inbox.glob("FR-*.md"))
    num = len(existing) + 1
    slug = body.title.lower().replace(" ", "-")[:40]
    fname = f"FR-{num:03d}-{slug}.md"
    path = inbox / fname
    today = _date.today().strftime("%d/%m/%Y")
    content = f"""---
fr-id: FR-{num:03d}
project: {project_id}
title: {body.title}
status: draft
source: {body.source}
created: {today}
rice-score: not scored
gate-status: not reviewed
linked-prd: -
---

# FR-{num:03d} - {body.title}

## Problem Statement
{body.description or "[Describe the problem this feature solves]"}

## Users Affected
[Who experiences this problem?]

## Requested Solution
[What is being asked for?]
"""
    path.write_text(content)
    return {"id": f"FR-{num:03d}", "file": str(path.relative_to(WORKSPACE)), "path": str(path.relative_to(WORKSPACE))}


class NewCR(_BaseModel):
    title: str
    linked_prd: str = ""
    description: str = ""
    urgency: str = "medium"


@router.post("/{project_id}/cr")
async def create_cr(project_id: str, body: NewCR):
    """Create a new Change Request in the project."""
    intake = WORKSPACE / "my-projects" / project_id / "cr" / "intake"
    intake.mkdir(parents=True, exist_ok=True)
    cr_log = WORKSPACE / "my-projects" / project_id / "cr" / "cr-log.md"
    # Next CR number
    existing = list(intake.glob("CR-*.md"))
    num = len(existing) + 1
    slug = body.title.lower().replace(" ", "-")[:40]
    fname = f"CR-{num:03d}-{slug}.md"
    path = intake / fname
    today = _date.today().strftime("%d/%m/%Y")
    content = f"""---
cr-id: CR-{num:03d}
project: {project_id}
title: {body.title}
linked-prd: {body.linked_prd}
status: intake
urgency: {body.urgency}
created: {today}
---

# CR-{num:03d} - {body.title}

## Description
{body.description or "[Describe what needs to change]"}

## Business Justification
[Why is this change needed?]

## Impact Assessment
- Story points: TBD
- Timeline impact: TBD
- Technical risk: Low / Medium / High
"""
    path.write_text(content)
    # Update cr-log
    if cr_log.exists():
        existing_log = cr_log.read_text()
        row = f"| CR-{num:03d} | {body.title} | {body.linked_prd} | {body.urgency} | intake | - | {today} |\n"
        cr_log.write_text(existing_log + row)
    return {"id": f"CR-{num:03d}", "file": str(path.relative_to(WORKSPACE))}


class NewStakeholder(_BaseModel):
    name: str
    title: str = ""
    power: str = "medium"
    interest: str = "medium"
    notes: str = ""


@router.post("/{project_id}/stakeholders")
async def create_stakeholder(project_id: str, body: NewStakeholder):
    sh_dir = WORKSPACE / "my-projects" / project_id / "stakeholders"
    sh_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(sh_dir.glob("SH-*.md"))
    num = len(existing) + 1
    slug = body.name.lower().replace(" ", "-")[:30]
    fname = f"SH-{num:03d}-{slug}.md"
    path = sh_dir / fname
    quadrant = "manage-closely" if body.power == "high" and body.interest == "high" \
        else "keep-satisfied" if body.power == "high" \
        else "keep-informed" if body.interest == "high" \
        else "monitor"
    today = _date.today().strftime("%d/%m/%Y")
    content = f"""---
sh-id: SH-{num:03d}
project: {project_id}
name: {body.name}
title: {body.title}
power: {body.power}
interest: {body.interest}
quadrant: {quadrant}
communication-style: direct
channel: email
created: {today}
---

# SH-{num:03d} - {body.name}

## Role and Influence
{body.title} — {body.notes or "[Describe their scope of authority]"}

## What They Care About
- [Topic 1]: [Brief context]
- [Topic 2]: [Brief context]

## Communication Preferences
- Style: direct
- Channel: email
- Best format: executive summary

## Known Positions and Past Decisions

| Date | Topic | Stance | Source |
|------|-------|--------|--------|

## Feedback Log
"""
    path.write_text(content)
    return {"id": f"SH-{num:03d}", "file": str(path.relative_to(WORKSPACE))}


# ── Conflict scan ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/conflicts")
async def scan_conflicts(project_id: str):
    """Scan all PRDs in the project for tag conflicts."""
    prd_dir = WORKSPACE / "my-projects" / project_id / "prd"
    if not prd_dir.exists():
        return {"conflicts": [], "total_prds": 0}

    import re as _re
    prd_tags: dict[str, list[str]] = {}

    for folder in prd_dir.iterdir():
        if not folder.is_dir():
            continue
        # Find latest version
        versions = sorted(folder.glob("PRD-*.md"))
        if not versions:
            continue
        latest = versions[-1]
        content = latest.read_text()
        # Extract tags from frontmatter
        tags_match = _re.search(r'^tags:\s*(.+)$', content, _re.MULTILINE)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split() if t.strip().startswith('#')]
            prd_tags[folder.name] = tags

    # Find conflicts
    tag_to_prds: dict[str, list[str]] = {}
    for prd, tags in prd_tags.items():
        for tag in tags:
            if tag not in tag_to_prds:
                tag_to_prds[tag] = []
            tag_to_prds[tag].append(prd)

    conflicts = []
    for tag, prds in tag_to_prds.items():
        if len(prds) >= 2:
            conflicts.append({
                "tag": tag,
                "prds": prds,
                "risk": "high" if len(prds) >= 3 else "medium",
                "message": f"Tag {tag} is used by {len(prds)} PRDs: {', '.join(prds)}"
            })

    return {
        "conflicts": conflicts,
        "total_prds": len(prd_tags),
        "has_conflicts": len(conflicts) > 0
    }


@router.post("/{project_id}/activate")
async def activate_project(project_id: str):
    """Set this project as the active project (writes _system/active-project.md)."""
    project_path = WORKSPACE / "my-projects" / project_id
    if not project_path.exists():
        raise HTTPException(404, f"Project {project_id} not found")
    active_file = WORKSPACE / "_system" / "active-project.md"
    active_file.parent.mkdir(parents=True, exist_ok=True)
    active_file.write_text(f"my-projects/{project_id}")
    return {"activated": project_id, "path": f"my-projects/{project_id}"}
