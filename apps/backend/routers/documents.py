"""Documents router - read and serve workspace markdown files."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()
WORKSPACE = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))


@router.get("/read")
async def read_document(path: str):
    """Read a workspace document by relative path."""
    file_path = WORKSPACE / path
    if not file_path.exists():
        raise HTTPException(404, f"File not found: {path}")
    if not str(file_path.resolve()).startswith(str(WORKSPACE.resolve())):
        raise HTTPException(403, "Access denied")
    return {
        "path": path,
        "content": file_path.read_text(),
        "name": file_path.name,
    }


@router.get("/versions")
async def list_versions(prd_path: str):
    """List all versions of a PRD or Epic."""
    folder = WORKSPACE / prd_path
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(404, "PRD folder not found")

    versions = []
    for f in sorted(folder.glob("*.md")):
        if f.name == "CHANGELOG.md":
            continue
        content = f.read_text()
        fm = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ": " in line:
                        k, v = line.split(": ", 1)
                        fm[k.strip()] = v.strip()
        versions.append({
            "file": f.name,
            "version": fm.get("version", "v?"),
            "status": fm.get("status", "unknown"),
            "approved_by": fm.get("approved-by", ""),
            "approved": fm.get("approved", ""),
            "changes": fm.get("changes", ""),
        })

    return {"versions": versions}


from pydantic import BaseModel

class WriteDoc(BaseModel):
    path: str
    content: str

@router.post("/write")
async def write_document(body: WriteDoc):
    file_path = WORKSPACE / body.path
    if not str(file_path.resolve()).startswith(str(WORKSPACE.resolve())):
        raise HTTPException(403, "Access denied")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(body.content)
    return {"path": body.path, "status": "written"}


class StatusBody(BaseModel):
    path: str
    status: str


@router.patch("/status")
async def update_status(body: StatusBody):
    """Update the status field in a markdown document's frontmatter."""
    import re
    file_path = WORKSPACE / body.path
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    content = file_path.read_text()
    new_content = re.sub(r'^(status:\s*).*$', f'\\g<1>{body.status}', content, flags=re.MULTILINE)
    file_path.write_text(new_content)
    return {"path": body.path, "status": body.status}
