"""Antigravity Skill and MCP Server Deployment Engine.

Mounts skills to ~/.gemini/config/skills/<skill_id>/ and registers MCP servers
into ~/.gemini/config/mcp_config.json safely and atomically.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class AntigravityDeployer:
    """Production deployment engine for Google Antigravity."""

    @classmethod
    def mount_skill(
        cls, skills_dir: Path, skill_id: str, skill_meta: Dict[str, Any]
    ) -> Path:
        """Mount skill into Antigravity config directory.

        Creates compliant SKILL.md, references/ subfolder, and atomic replacement.
        """
        skills_dir.mkdir(parents=True, exist_ok=True)
        target_dir = skills_dir / skill_id
        staging_dir = skills_dir / f".staging_{skill_id}_{os.getpid()}"

        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Write SKILL.md
            skill_md = staging_dir / "SKILL.md"
            title = skill_meta.get("name", skill_id)
            desc = skill_meta.get("description", "")
            overview = skill_meta.get("overview") or desc

            content = f"""---
name: {skill_id}
description: {desc}
---
# {title}

## Overview
{overview}

## When to Use
Activate this skill when requested.

## References
See [references/](references/) for detailed operational guidance.
"""
            with open(skill_md, "w", encoding="utf-8") as f:
                f.write(content)

            # Create progressive disclosure directories
            (staging_dir / "references").mkdir(parents=True, exist_ok=True)
            (staging_dir / "scripts").mkdir(parents=True, exist_ok=True)

            # Atomic replacement
            if target_dir.exists():
                shutil.rmtree(target_dir)
            staging_dir.replace(target_dir)

            return target_dir
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

    @classmethod
    def register_mcp_server(
        cls,
        mcp_config_path: Path,
        server_id: str,
        server_def: Dict[str, Any],
        backup_dir: Path,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Safely register an MCP server into mcp_config.json."""
        mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Read or initialize
        if not mcp_config_path.exists() or mcp_config_path.stat().st_size == 0:
            data = {"mcpServers": {}}
        else:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}

        # Step 2: Backup if existing has content
        if mcp_config_path.exists() and mcp_config_path.stat().st_size > 0:
            ts = int(time.time() * 1000)
            backup_file = backup_dir / f"mcp_config.json.bak.{ts}"
            shutil.copy2(mcp_config_path, backup_file)

        # Step 3: Register
        if server_id in data["mcpServers"] and not force:
            return {"status": "SKIPPED", "reason": "Server already registered"}

        data["mcpServers"][server_id] = server_def

        # Step 4: Atomic write
        tmp_file = mcp_config_path.with_suffix(f".tmp.{os.getpid()}_{int(time.time()*1000)}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, mcp_config_path)

        return {"status": "UPDATED", "server_id": server_id}
