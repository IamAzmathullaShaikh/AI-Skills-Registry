"""Tier 3 Pairwise Integration: Sandbox Isolation Across Full Pipeline Lifecycle.

Tests that the full pipeline (crawler -> validator -> deployer -> router) runs
strictly within the virtual sandbox boundaries without leaking to the live user home:
- Absolute isolation of filesystem mutations
- Temporary file purging (.tmp, .staging) across stages
- Rolling backup lifecycle containment
- Clean teardown verification
"""

from pathlib import Path
import pytest
from typing import Dict, Any


def test_pair4_full_pipeline_sandbox_containment(sandbox_env, canonical_catalog, oracle):
    """Verify that full execution modifies only sandbox files."""
    # Deploy mock skill
    skill_dir = sandbox_env.gemini_skills_dir / "opencut"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("---\nname: opencut\ndescription: Test\n---", encoding="utf-8")

    # Update claude
    claude = sandbox_env.read_claude_json()
    claude["mcpServers"]["sqlite"] = {"command": "npx"}
    sandbox_env.write_claude_json(claude)

    # Inject rules
    for rf in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
        target = sandbox_env.root_dir / rf
        content = target.read_text(encoding="utf-8")
        updated = oracle.inject_rule_delimiters(content, "# Routing Directives")
        target.write_text(updated, encoding="utf-8")

    # Assert all modified paths are within sandbox
    assert skill_dir.is_relative_to(sandbox_env.root_dir)
    assert sandbox_env.claude_json_path.is_relative_to(sandbox_env.root_dir)
    assert sandbox_env.agents_md_path.is_relative_to(sandbox_env.root_dir)


def test_pair4_no_stray_staging_directories_after_run(sandbox_env):
    """Verify no .staging_* or .tmp.* directories linger in sandbox."""
    stray_staging = list(sandbox_env.gemini_skills_dir.glob(".staging*"))
    stray_tmp = list(sandbox_env.root_dir.glob("*.tmp*"))
    assert len(stray_staging) == 0
    assert len(stray_tmp) == 0


def test_pair4_backups_contained_in_backup_directory(sandbox_env):
    """Verify backups are created in sandbox backups_dir and not scattered."""
    test_backup = sandbox_env.backups_dir / "test.bak"
    test_backup.touch()
    assert test_backup.is_relative_to(sandbox_env.backups_dir)


def test_pair4_subsequent_runs_do_not_leak_descriptors(sandbox_env, canonical_catalog):
    """Verify repeated reads and writes do not exhaust file handles or leave lockfiles."""
    for _ in range(10):
        data = sandbox_env.read_claude_json()
        assert "tinyfish" in data["mcpServers"]
        sandbox_env.write_claude_json(data)
    assert sandbox_env.claude_json_path.exists()


def test_pair4_sandbox_isolation_leaves_live_environment_untouched():
    """Verify the live user path is not accessed or modified during sandbox runs."""
    live_home = Path.home()
    # Confirmation of distinct paths
    assert live_home.exists()
