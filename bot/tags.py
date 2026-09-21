"""
Deterministic tag scanning for conflict detection.

The conflict flow has two halves and they must not be mixed up. Finding which
PRDs share a module is a matter of reading files and comparing strings, so it
belongs here, in code that behaves the same way every run. Judging whether a
shared tag is an actual collision is a matter of reading intent, which is what
Jev is for.

Keeping detection here is what stops a missed tag from becoming a missed
conflict. A model that overlooks one line of frontmatter silently drops a pair
that no later step will ever reconsider.
"""

from __future__ import annotations

import re
from pathlib import Path

# my-projects/PROJ-001-slug/prd/PRD-004-slug/PRD-004-v1.2.md
VERSIONED_PRD = re.compile(r"^(PRD-\d+)-v(\d+)\.(\d+)\.md$")
PRD_ID = re.compile(r"\bPRD-\d+\b")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TAGS_FIELD = re.compile(r"^tags\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
# A tag is #word. "# Heading" has a space after the hash, so it does not match.
BODY_TAG = re.compile(r"#([A-Za-z][\w-]*)")


def _normalise(raw: str) -> list[str]:
    """'#auth, api-gateway' -> ['#api-gateway', '#auth']"""
    parts = re.split(r"[,\s]+", raw.strip())
    return sorted({"#" + p.lstrip("#").lower() for p in parts if p.strip("#")})


def extract_tags(text: str) -> tuple[list[str], str]:
    """Return (tags, where they came from).

    Frontmatter is the documented source and the only trustworthy one. Scanning
    the body is a fallback for PRDs written before the field existed, and it is
    reported as such so nobody mistakes a guess for a declaration.
    """
    fm = FRONTMATTER.search(text)
    if fm:
        field = TAGS_FIELD.search(fm.group(1))
        if field and field.group(1).strip():
            return _normalise(field.group(1)), "frontmatter"

    body = text[fm.end():] if fm else text
    found = sorted({"#" + m.lower() for m in BODY_TAG.findall(body)})
    return (found, "body, inferred") if found else ([], "none")


def latest_versions(prd_root: Path) -> list[tuple[str, Path]]:
    """One file per PRD folder: the highest version number, not the newest mtime."""
    out = []
    for folder in sorted(p for p in prd_root.iterdir() if p.is_dir()):
        best = None
        for f in folder.iterdir():
            m = VERSIONED_PRD.match(f.name)
            if m:
                key = (int(m.group(2)), int(m.group(3)))
                if best is None or key > best[0]:
                    best = (key, m.group(1), f)
        if best:
            out.append((best[1], best[2]))
    return sorted(out)


def prds_in_sprint(sprint_file: Path) -> set[str]:
    """Every PRD id mentioned anywhere in the sprint file."""
    return set(PRD_ID.findall(sprint_file.read_text(errors="replace")))


def scan(workspace: Path, project: str, sprint: str = "") -> str:
    """Report which PRDs share a tag. Finds pairs, never judges them."""
    prd_root = workspace / project / "prd"
    if not prd_root.is_dir():
        return f"No prd folder at {project}/prd, so there is nothing to scan."

    files = latest_versions(prd_root)
    if not files:
        return f"No versioned PRD files under {project}/prd."

    in_scope = None
    scope_note = "all PRDs in the project"
    if sprint:
        matches = sorted((workspace / project / "sprints").glob(f"{sprint}*.md")) \
            if (workspace / project / "sprints").is_dir() else []
        if not matches:
            return (
                f"No sprint file starting with {sprint} under {project}/sprints. "
                "Create the sprint first, or scan without a sprint to cover every PRD."
            )
        in_scope = prds_in_sprint(matches[0])
        scope_note = f"sprint {sprint} ({matches[0].name})"
        files = [(pid, path) for pid, path in files if pid in in_scope]
        if not files:
            return f"The sprint file {matches[0].name} lists no PRD that exists on disk."

    tags_by_prd: dict[str, list[str]] = {}
    source_by_prd: dict[str, str] = {}
    for prd_id, path in files:
        tags, source = extract_tags(path.read_text(errors="replace"))
        tags_by_prd[prd_id] = tags
        source_by_prd[prd_id] = source

    lines = [f"Tag scan: {project}, {scope_note}", f"Scanned {len(files)} PRDs.", ""]
    for prd_id in sorted(tags_by_prd):
        tags = tags_by_prd[prd_id]
        shown = " ".join(tags) if tags else "(no tags)"
        source = source_by_prd[prd_id]
        lines.append(f"  {prd_id}  {shown}" + (f"   [{source}]" if tags else ""))

    pairs = []
    ids = sorted(tags_by_prd)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            shared = sorted(set(tags_by_prd[a]) & set(tags_by_prd[b]))
            if shared:
                pairs.append((a, b, shared))

    lines.append("")
    if pairs:
        lines.append(f"Candidate pairs: {len(pairs)}")
        for a, b, shared in pairs:
            lines.append(f"  {a} & {b} share {' '.join(shared)}")
    else:
        lines.append("No two PRDs in scope share a tag. No candidate pairs.")

    untagged = [p for p, t in tags_by_prd.items() if not t]
    if untagged:
        lines += [
            "",
            f"Not checkable: {', '.join(sorted(untagged))}. No tags found, so this scan "
            "cannot place those PRDs in any collision. Tell the PM, and offer to add a "
            "tags field from _system/tags-registry.md. Silence is not the same as no "
            "conflict.",
        ]

    inferred = [p for p, s in source_by_prd.items() if s == "body, inferred"]
    if inferred:
        lines += [
            "",
            f"Read from the body rather than frontmatter: {', '.join(sorted(inferred))}. "
            "Treat those tags as a guess and confirm them with the PM.",
        ]

    lines += [
        "",
        "This list is the complete set of candidates. Judge only these pairs, and judge "
        "every one of them.",
    ]
    return "\n".join(lines)
