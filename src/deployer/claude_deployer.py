"""Claude Code & Freebuff Desktop MCP Server Deep-Merge Engine.

Provides atomic, non-destructive deep-merging of MCP servers into ~/.claude.json,
safeguarding existing configurations, third-party credentials (tinyfish),
and top-level metadata bit-for-bit.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ClaudeDeployer:
    """Production deployment engine for Claude Code and Freebuff Desktop."""

    @classmethod
    def deep_merge_mcp_servers(
        cls,
        claude_json_path: Path,
        new_servers: Dict[str, Any],
        backup_dir: Path,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Safely merge new MCP servers into ~/.claude.json."""
        if not claude_json_path.exists():
            raise FileNotFoundError(f"Missing configuration file: {claude_json_path}")

        backup_dir.mkdir(parents=True, exist_ok=True)

        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Root of .claude.json must be a JSON object")

        # Create timestamped backup
        ts = int(time.time() * 1000)
        backup_file = backup_dir / f".claude.json.bak.{ts}"
        shutil.copy2(claude_json_path, backup_file)

        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}

        merged = 0
        preserved = 0
        for srv_name, srv_cfg in new_servers.items():
            if srv_name in data["mcpServers"] and not force:
                preserved += 1
                continue
            data["mcpServers"][srv_name] = srv_cfg
            merged += 1

        # Atomic write with PID and timestamp to avoid collision
        tmp_file = claude_json_path.with_suffix(f".tmp.{os.getpid()}_{ts}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Post-write verify
        with open(tmp_file, "r", encoding="utf-8") as f:
            verify = json.load(f)

        if "tinyfish" in data.get("mcpServers", {}):
            assert "tinyfish" in verify.get("mcpServers", {}), "Verification failed: tinyfish server was lost!"
            if "headers" in data["mcpServers"]["tinyfish"]:
                orig_key = data["mcpServers"]["tinyfish"]["headers"].get("X-API-Key")
                verif_key = verify["mcpServers"]["tinyfish"].get("headers", {}).get("X-API-Key")
                assert orig_key == verif_key, "Verification failed: tinyfish API key corrupted!"

        os.replace(tmp_file, claude_json_path)

        return {
            "status": "SUCCESS",
            "merged": merged,
            "preserved": preserved,
            "backup": str(backup_file),
        }
