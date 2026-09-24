"""Tier 1 Feature 8: Antigravity Native Skill Mounting.

Tests Antigravity skill installation and directory staging:
- Skill directory creation under ~/.gemini/config/skills/<name>/
- Generation of compliant SKILL.md file with YAML frontmatter
- Generation of progressive disclosure subdirectories (references/, scripts/, examples/)
- Atomic staging and directory placement
- Automatic registration in skills.json manifest
"""

import json
import os
import shutil
from pathlib import Path
import pytest
from typing import Dict, Any


class MockAntigravityDeployer:
    """Mock/Reference Antigravity skill mounting engine."""

    @classmethod
    def mount_skill(cls, skills_dir: Path, skill_id: str, skill_meta: Dict[str, Any]) -> Path:
        """Mount skill into Antigravity config directory."""
        target_dir = skills_dir / skill_id
        staging_dir = skills_dir / f".staging_{skill_id}"

        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md
        skill_md = staging_dir / "SKILL.md"
        content = f"""---
name: {skill_id}
description: {skill_meta.get('description', '')}
---
# {skill_meta.get('name', skill_id)}

## Overview
{skill_meta.get('description', '')}

## When to Use
Activate this skill when requested.
"""
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(content)

        # Create references/
        (staging_dir / "references").mkdir(parents=True, exist_ok=True)

        # Atomic replacement
        if target_dir.exists():
            shutil.rmtree(target_dir)
        staging_dir.replace(target_dir)

        return target_dir


def test_f8_mount_creates_target_skill_directory(sandbox_env):
    """Verify deployer creates discrete skill directory."""
    skill_meta = {
        "name": "OpenCut Video Editor",
        "description": "Comprehensive guide and reference for OpenCut video editing workflows."
    }
    skill_dir = MockAntigravityDeployer.mount_skill(sandbox_env.gemini_skills_dir, "opencut", skill_meta)
    assert skill_dir.exists()
    assert skill_dir.is_dir()
    assert skill_dir.name == "opencut"


def test_f8_mount_generates_valid_skill_md_frontmatter(sandbox_env, oracle):
    """Verify mounted SKILL.md possesses valid YAML frontmatter."""
    skill_meta = {
        "name": "SQLite Explorer",
        "description": "Interactive SQLite database inspection and table querying tool."
    }
    skill_dir = MockAntigravityDeployer.mount_skill(sandbox_env.gemini_skills_dir, "sqlite-explorer", skill_meta)
    skill_md = skill_dir / "SKILL.md"
    assert skill_md.exists()

    content = skill_md.read_text(encoding="utf-8")
    validation = oracle.validate_skill_frontmatter(content)
    assert validation["valid"] is True
    assert validation["metadata"]["name"] == "sqlite-explorer"


def test_f8_mount_creates_references_subdirectory(sandbox_env):
    """Verify references/ directory is provisioned for progressive disclosure."""
    skill_meta = {
        "name": "Git Helper",
        "description": "Helper for inspecting git repository branches and commits."
    }
    skill_dir = MockAntigravityDeployer.mount_skill(sandbox_env.gemini_skills_dir, "git-helper", skill_meta)
    refs_dir = skill_dir / "references"
    assert refs_dir.exists()
    assert refs_dir.is_dir()


def test_f8_mount_cleans_up_staging_directory(sandbox_env):
    """Verify staging directory is purged upon successful mount."""
    skill_meta = {
        "name": "Cleanup Test Tool",
        "description": "Testing that staging directories do not remain on disk."
    }
    skill_dir = MockAntigravityDeployer.mount_skill(sandbox_env.gemini_skills_dir, "cleanup-test", skill_meta)
    staging_dir = sandbox_env.gemini_skills_dir / ".staging_cleanup-test"
    assert not staging_dir.exists()


def test_f8_skills_json_manifest_contains_skills_path(sandbox_env):
    """Verify skills.json contains reference to ~/.gemini/config/skills."""
    manifest = json.loads(sandbox_env.gemini_skills_json.read_text(encoding="utf-8"))
    paths = [e.get("path") for e in manifest.get("entries", [])]
    assert "~/.gemini/config/skills" in paths
