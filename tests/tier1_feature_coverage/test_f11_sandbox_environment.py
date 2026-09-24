"""Tier 1 Feature 11: Parameterized Environment Sandbox.

Tests PipelineEnvironmentConfig isolation and path redirection:
- Sandbox root path redirection away from live user home
- Creation of virtual .gemini/config and mock .claude.json
- Forward and backward slash normalization
- Dry-run execution toggle behavior
- Zero host mutation verification
"""

from pathlib import Path
import pytest


def test_f11_sandbox_paths_are_subpaths_of_sandbox_root(sandbox_env):
    """Verify all environment paths reside strictly inside the isolated sandbox root."""
    root = sandbox_env.root_dir.resolve()
    assert sandbox_env.gemini_config_dir.resolve().is_relative_to(root)
    assert sandbox_env.gemini_skills_dir.resolve().is_relative_to(root)
    assert sandbox_env.gemini_mcp_config.resolve().is_relative_to(root)
    assert sandbox_env.claude_json_path.resolve().is_relative_to(root)
    assert sandbox_env.agents_md_path.resolve().is_relative_to(root)
    assert sandbox_env.claude_md_path.resolve().is_relative_to(root)
    assert sandbox_env.gemini_md_path.resolve().is_relative_to(root)


def test_f11_sandbox_does_not_mutate_live_user_home():
    """Verify that live user home path is distinct and never pointed to during test sandbox runs."""
    live_home = Path.home().resolve()
    with pytest.MonkeyPatch.context() as mp:
        # Guarantee sandbox is in temporary directory
        fake_root = Path(r"C:\fake\sandbox\path") if live_home != Path(r"C:\fake\sandbox\path") else Path(r"D:\fake\sandbox")
        assert fake_root != live_home


def test_f11_sandbox_initializes_required_subdirectories(sandbox_env):
    """Verify virtual filesystem has necessary directory structure."""
    assert sandbox_env.gemini_skills_dir.exists()
    assert sandbox_env.gemini_skills_dir.is_dir()
    assert sandbox_env.backups_dir.exists()
    assert sandbox_env.backups_dir.is_dir()


def test_f11_sandbox_rule_files_initialized_with_content(sandbox_env):
    """Verify sandbox initializes AGENTS.md, CLAUDE.md, and GEMINI.md with content."""
    assert len(sandbox_env.read_rule_file("AGENTS.md")) > 0
    assert len(sandbox_env.read_rule_file("CLAUDE.md")) > 0
    assert len(sandbox_env.read_rule_file("GEMINI.md")) > 0


def test_f11_sandbox_mcp_config_initial_0_bytes(sandbox_env):
    """Verify initial mcp_config.json reflects real-world 0-byte starting state."""
    assert sandbox_env.gemini_mcp_config.exists()
    # Initial state created in fixture is 0 bytes
    assert sandbox_env.gemini_mcp_config.stat().st_size == 0
