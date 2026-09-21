"""
Installation validation tests.
Tests that all required files exist and are valid.
Run: pytest tests/test_installation.py -v
"""
import os
import re
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent


class TestRequiredFiles:
    def test_agent_md_exists(self):
        assert (ROOT / "AGENT.md").exists(), "AGENT.md missing"

    def test_env_example_exists(self):
        assert (ROOT / ".env.example").exists(), ".env.example missing"

    def test_setup_sh_exists(self):
        assert (ROOT / "setup.sh").exists(), "setup.sh missing"

    def test_setup_sh_executable(self):
        assert os.access(ROOT / "setup.sh", os.X_OK), "setup.sh not executable"

    def test_makefile_exists(self):
        assert (ROOT / "Makefile").exists(), "Root Makefile missing"

    def test_bot_dockerfile_exists(self):
        assert (ROOT / "bot" / "Dockerfile").exists(), "bot/Dockerfile missing"

    def test_bot_agent_py_exists(self):
        assert (ROOT / "bot" / "agent.py").exists(), "bot/agent.py missing"

    def test_bot_bot_py_exists(self):
        assert (ROOT / "bot" / "bot.py").exists(), "bot/bot.py missing"

    def test_bot_requirements_exists(self):
        assert (ROOT / "bot" / "requirements.txt").exists()

    def test_bot_docker_compose_exists(self):
        assert (ROOT / "bot" / "docker-compose.yml").exists()

    def test_apps_backend_main_exists(self):
        assert (ROOT / "apps" / "backend" / "main.py").exists()

    def test_apps_backend_dockerfile_exists(self):
        assert (ROOT / "apps" / "backend" / "Dockerfile").exists()

    def test_apps_frontend_dockerfile_exists(self):
        assert (ROOT / "apps" / "frontend" / "Dockerfile").exists()

    def test_apps_docker_compose_exists(self):
        assert (ROOT / "apps" / "docker-compose.yml").exists()

    def test_apps_makefile_exists(self):
        assert (ROOT / "apps" / "Makefile").exists()

    def test_license_file_exists(self):
        assert (ROOT / "LICENSE").exists()

    def test_readme_exists(self):
        assert (ROOT / "README.md").exists()

    def test_gitignore_excludes_env(self):
        gitignore = (ROOT / ".gitignore").read_text()
        assert ".env" in gitignore, ".env should be in .gitignore"

    def test_gitignore_excludes_system(self):
        gitignore = (ROOT / ".gitignore").read_text()
        assert "_system/" in gitignore, "_system/ should be in .gitignore"


class TestSetupScript:
    def test_setup_sh_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(ROOT / "setup.sh")],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"setup.sh syntax error:\n{result.stderr}"

    def test_setup_sh_has_install_options(self):
        content = (ROOT / "setup.sh").read_text()
        assert "install_telegram" in content
        assert "install_web" in content
        assert "install_both" in content

    def test_setup_sh_functions_before_case(self):
        """Functions must be defined before the case statement."""
        content = (ROOT / "setup.sh").read_text()
        lines = content.split("\n")
        func_line = next((i for i, l in enumerate(lines) if "install_telegram()" in l), None)
        case_line = next((i for i, l in enumerate(lines) if l.strip().startswith("case $OPTION")), None)
        assert func_line is not None, "install_telegram function not found"
        assert case_line is not None, "case statement not found"
        assert func_line < case_line, f"Functions (line {func_line}) must come before case (line {case_line})"

    def test_env_example_has_required_keys(self):
        content = (ROOT / ".env.example").read_text()
        required = ["TELEGRAM_BOT_TOKEN", "ANTHROPIC_API_KEY"]
        for key in required:
            assert key in content, f"{key} missing from .env.example"


class TestDockerConfigs:
    def test_bot_docker_compose_valid_yaml(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(ROOT / "bot" / "docker-compose.yml"), "config", "--quiet"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"bot docker-compose invalid:\n{result.stderr}"

    def test_apps_docker_compose_valid_yaml(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(ROOT / "apps" / "docker-compose.yml"), "config", "--quiet"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"apps docker-compose invalid:\n{result.stderr}"

    def test_bot_requirements_has_anthropic(self):
        req = (ROOT / "bot" / "requirements.txt").read_text()
        assert "anthropic" in req

    def test_bot_requirements_has_telegram(self):
        req = (ROOT / "bot" / "requirements.txt").read_text()
        assert "python-telegram-bot" in req

    def test_apps_backend_requirements_has_fastapi(self):
        req = (ROOT / "apps" / "backend" / "requirements.txt").read_text()
        assert "fastapi" in req

    def test_apps_backend_requirements_has_anthropic(self):
        req = (ROOT / "apps" / "backend" / "requirements.txt").read_text()
        assert "anthropic" in req


class TestSkills:
    """Skills live in .claude/skills/ so Claude Code auto-discovers them.
    The bot and the web backend find them through the Skills Index in CLAUDE.md."""

    SKILLS_ROOT = ROOT / ".claude" / "skills"

    def _skill_dirs(self):
        assert self.SKILLS_ROOT.is_dir(), ".claude/skills/ missing"
        return sorted(d for d in self.SKILLS_ROOT.iterdir() if d.is_dir())

    def test_skills_root_exists(self):
        assert self.SKILLS_ROOT.is_dir(), ".claude/skills/ missing"
        assert self._skill_dirs(), ".claude/skills/ has no skill folders"

    def test_all_skill_dirs_have_skill_md(self):
        for d in self._skill_dirs():
            assert (d / "SKILL.md").exists(), f"Missing SKILL.md in {d}"

    def test_skill_mds_have_frontmatter(self):
        for d in self._skill_dirs():
            content = (d / "SKILL.md").read_text()
            assert content.startswith("---"), f"{d}: missing frontmatter"
            assert "name:" in content, f"{d}: missing name field"
            assert "description:" in content, f"{d}: missing description field"

    def test_skill_names_match_dirs_and_are_unique(self):
        seen = {}
        for d in self._skill_dirs():
            content = (d / "SKILL.md").read_text()
            m = re.search(r"^name:\s*(\S+)", content, re.M)
            assert m, f"{d}: no name in frontmatter"
            name = m.group(1)
            assert name == d.name, f"{d}: frontmatter name {name!r} != folder {d.name!r}"
            assert name not in seen, f"duplicate skill name {name!r}"
            seen[name] = d

    def test_agent_md_references_every_skill(self):
        agent = (ROOT / "AGENT.md").read_text()
        for d in self._skill_dirs():
            ref = f".claude/skills/{d.name}"
            assert ref in agent, f"AGENT.md doesn't reference {ref}"

    def test_claude_md_matches_agent_md(self):
        claude = ROOT / "CLAUDE.md"
        if claude.exists():
            assert claude.read_text() == (ROOT / "AGENT.md").read_text(), \
                "CLAUDE.md drifted from AGENT.md, re-run setup.sh or copy it across"

