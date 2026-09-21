"""
Unit tests for deterministic tag scanning.
Run without Docker: pytest tests/test_tags.py -v

Detection has to be exact. A pair this module misses is a conflict no later
step ever reconsiders, so most of these cover the ways a tag can hide.
"""
import sys
from pathlib import Path

import pytest

BOT_PATH = Path(__file__).parent.parent / "bot"
sys.path.insert(0, str(BOT_PATH))

import tags as tagmod  # noqa: E402


def prd(folder: Path, prd_id: str, version: str, frontmatter: str = "", body: str = "x"):
    folder.mkdir(parents=True, exist_ok=True)
    head = f"---\n{frontmatter}\n---\n" if frontmatter else ""
    (folder / f"{prd_id}-v{version}.md").write_text(f"{head}# {prd_id}\n{body}\n")


@pytest.fixture
def ws(tmp_path):
    (tmp_path / "proj" / "prd").mkdir(parents=True)
    return tmp_path


class TestExtractTags:
    def test_frontmatter_with_hashes(self):
        assert tagmod.extract_tags("---\ntags: #auth, #api-gateway\n---\nbody") == (
            ["#api-gateway", "#auth"], "frontmatter",
        )

    def test_frontmatter_without_hashes(self):
        got, src = tagmod.extract_tags("---\ntags: auth payment\n---\nbody")
        assert got == ["#auth", "#payment"] and src == "frontmatter"

    def test_case_is_normalised(self):
        got, _ = tagmod.extract_tags("---\ntags: #Auth, #AUTH\n---\n")
        assert got == ["#auth"]

    def test_body_is_only_a_fallback(self):
        got, src = tagmod.extract_tags("---\ntags: #auth\n---\nalso mentions #payment")
        assert got == ["#auth"] and src == "frontmatter"

    def test_body_used_when_frontmatter_has_no_tags(self):
        got, src = tagmod.extract_tags("---\ntitle: x\n---\ntouches #payment and #auth")
        assert got == ["#auth", "#payment"] and src == "body, inferred"

    def test_markdown_headings_are_not_tags(self):
        got, src = tagmod.extract_tags("# PRD-001 - Title\n## 1. Summary\n### Details\n")
        assert got == [] and src == "none"

    def test_empty_tags_field_is_not_a_tag(self):
        got, src = tagmod.extract_tags("---\ntags:   \n---\nno hashes here")
        assert got == [] and src == "none"


class TestLatestVersions:
    def test_picks_highest_version_not_newest_file(self, ws):
        folder = ws / "proj" / "prd" / "PRD-001-slug"
        prd(folder, "PRD-001", "2.0")
        prd(folder, "PRD-001", "1.1")
        # Touch the older file last: mtime ordering would pick the wrong one.
        (folder / "PRD-001-v1.1.md").touch()
        found = tagmod.latest_versions(ws / "proj" / "prd")
        assert [f.name for _, f in found] == ["PRD-001-v2.0.md"]

    def test_minor_versions_compare_numerically(self, ws):
        folder = ws / "proj" / "prd" / "PRD-001-slug"
        prd(folder, "PRD-001", "1.9")
        prd(folder, "PRD-001", "1.10")
        found = tagmod.latest_versions(ws / "proj" / "prd")
        assert [f.name for _, f in found] == ["PRD-001-v1.10.md"]

    def test_non_prd_files_in_the_folder_are_ignored(self, ws):
        folder = ws / "proj" / "prd" / "PRD-001-slug"
        prd(folder, "PRD-001", "1.0")
        (folder / "CHANGELOG.md").write_text("# log")
        (folder / "DEV-BRIEF-v1.0.md").write_text("# brief")
        assert len(tagmod.latest_versions(ws / "proj" / "prd")) == 1


class TestScan:
    def test_finds_every_pair_sharing_a_tag(self, ws):
        root = ws / "proj" / "prd"
        prd(root / "PRD-001-a", "PRD-001", "1.0", "tags: #auth, #api-gateway")
        prd(root / "PRD-004-b", "PRD-004", "1.0", "tags: #auth")
        prd(root / "PRD-009-c", "PRD-009", "1.0", "tags: #api-gateway")
        out = tagmod.scan(ws, "proj")
        assert "Candidate pairs: 2" in out
        assert "PRD-001 & PRD-004 share #auth" in out
        assert "PRD-001 & PRD-009 share #api-gateway" in out

    def test_no_shared_tag_means_no_pairs(self, ws):
        root = ws / "proj" / "prd"
        prd(root / "PRD-001-a", "PRD-001", "1.0", "tags: #auth")
        prd(root / "PRD-002-b", "PRD-002", "1.0", "tags: #search")
        assert "No candidate pairs" in tagmod.scan(ws, "proj")

    def test_untagged_prd_is_reported_not_silently_skipped(self, ws):
        root = ws / "proj" / "prd"
        prd(root / "PRD-001-a", "PRD-001", "1.0", "tags: #auth")
        prd(root / "PRD-002-b", "PRD-002", "1.0", "title: no tags here")
        out = tagmod.scan(ws, "proj")
        assert "Not checkable: PRD-002" in out
        assert "Silence is not the same as no conflict" in out

    def test_inferred_tags_are_flagged_as_a_guess(self, ws):
        root = ws / "proj" / "prd"
        prd(root / "PRD-001-a", "PRD-001", "1.0", "tags: #auth")
        prd(root / "PRD-002-b", "PRD-002", "1.0", "title: x", body="touches #auth")
        out = tagmod.scan(ws, "proj")
        assert "PRD-001 & PRD-002 share #auth" in out
        assert "Read from the body rather than frontmatter: PRD-002" in out

    def test_sprint_filter_limits_scope(self, ws):
        root = ws / "proj" / "prd"
        for pid in ("PRD-001", "PRD-002", "PRD-003"):
            prd(root / f"{pid}-x", pid, "1.0", "tags: #auth")
        sprints = ws / "proj" / "sprints"
        sprints.mkdir()
        (sprints / "S12-sprint-01-09-2026.md").write_text(
            "# Sprint S12\nIn scope: PRD-001 and PRD-002.\n"
        )
        out = tagmod.scan(ws, "proj", "S12")
        assert "Scanned 2 PRDs" in out
        assert "PRD-003" not in out

    def test_missing_sprint_file_says_so(self, ws):
        prd(ws / "proj" / "prd" / "PRD-001-a", "PRD-001", "1.0", "tags: #auth")
        assert "No sprint file starting with S99" in tagmod.scan(ws, "proj", "S99")

    def test_missing_prd_folder_is_not_an_error(self, ws):
        assert "nothing to scan" in tagmod.scan(ws, "does-not-exist")

    def test_empty_prd_folder_says_so(self, ws):
        assert "No versioned PRD files" in tagmod.scan(ws, "proj")

    def test_only_the_latest_version_is_compared(self, ws):
        """An old version's tags must not resurrect a conflict that was removed."""
        root = ws / "proj" / "prd"
        folder = root / "PRD-001-a"
        prd(folder, "PRD-001", "1.0", "tags: #auth, #payment")
        prd(folder, "PRD-001", "2.0", "tags: #auth")
        prd(root / "PRD-002-b", "PRD-002", "1.0", "tags: #payment")
        out = tagmod.scan(ws, "proj")
        assert "No candidate pairs" in out

    def test_output_tells_the_agent_the_list_is_complete(self, ws):
        prd(ws / "proj" / "prd" / "PRD-001-a", "PRD-001", "1.0", "tags: #auth")
        assert "complete set of candidates" in tagmod.scan(ws, "proj")


class TestAgainstTheRealRepo:
    def test_the_shipped_prd_template_writes_a_tags_field(self):
        """conflict-check reads tags from frontmatter, so creation must write it."""
        agent = (Path(__file__).parent.parent / "bot" / "agent.py").read_text()
        assert "tags: #tag-one, #tag-two" in agent, "PRD template stopped writing tags"

    def test_scan_tags_is_reachable_from_the_prompt(self):
        agent = (Path(__file__).parent.parent / "bot" / "agent.py").read_text()
        assert 'scan_tags(project="[PROJECT]"' in agent
