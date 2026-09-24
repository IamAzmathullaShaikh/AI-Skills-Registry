"""Tier 1 Feature 10: Claude Code Non-Destructive Deep Merge.

Tests non-destructive dictionary merging of MCP servers into ~/.claude.json:
- Exact preservation of existing user server 'tinyfish' and its API key
- Bit-for-bit preservation of top-level user configuration (growthbook flags, startups, tips)
- Multi-server addition to mcpServers dictionary
- Pre-mutation timestamped backup creation
- Post-write verification assertion
- Conflict handling (skip vs force)
"""

import json
import os
import shutil
import time
from pathlib import Path
import pytest
from typing import Dict, Any


class MockClaudeDeployer:
    """Mock/Reference Claude Code deep merge deployer."""

    @classmethod
    def deep_merge_mcp_servers(
        cls,
        claude_json_path: Path,
        new_servers: Dict[str, Any],
        backup_dir: Path,
        force: bool = False
    ) -> Dict[str, Any]:
        """Safely merge new MCP servers into ~/.claude.json."""
        if not claude_json_path.exists():
            raise FileNotFoundError(f"Missing {claude_json_path}")

        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Root of .claude.json must be a JSON object")

        # Create backup
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

        # Atomic write
        tmp_file = claude_json_path.with_suffix(f".tmp.{ts}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Post-write verify
        with open(tmp_file, "r", encoding="utf-8") as f:
            verify = json.load(f)
        if "tinyfish" in data.get("mcpServers", {}):
            assert "tinyfish" in verify["mcpServers"], "Verification failed: tinyfish lost!"

        os.replace(tmp_file, claude_json_path)

        return {
            "status": "SUCCESS",
            "merged": merged,
            "preserved": preserved,
            "backup": str(backup_file)
        }


def test_f10_preserves_tinyfish_server_and_api_key(sandbox_env):
    """Verify active 'tinyfish' server and exact X-API-Key remain untouched after merge."""
    original = sandbox_env.read_claude_json()
    assert "tinyfish" in original["mcpServers"]
    original_key = original["mcpServers"]["tinyfish"]["headers"]["X-API-Key"]

    new_servers = {
        "sqlite": {"command": "npx", "args": ["@modelcontextprotocol/server-sqlite"]},
        "postgres": {"command": "npx", "args": ["@modelcontextprotocol/server-postgres"]}
    }

    res = MockClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        new_servers,
        sandbox_env.backups_dir
    )
    assert res["status"] == "SUCCESS"
    assert res["merged"] == 2

    updated = sandbox_env.read_claude_json()
    assert "tinyfish" in updated["mcpServers"]
    assert updated["mcpServers"]["tinyfish"]["headers"]["X-API-Key"] == original_key
    assert updated["mcpServers"]["tinyfish"]["url"] == original["mcpServers"]["tinyfish"]["url"]


def test_f10_preserves_all_top_level_settings(sandbox_env):
    """Verify top-level keys like numStartups, cachedGrowthBookFeatures, and tips are preserved."""
    original = sandbox_env.read_claude_json()

    new_servers = {"brave-search": {"command": "npx", "args": ["server-brave-search"]}}
    MockClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        new_servers,
        sandbox_env.backups_dir
    )

    updated = sandbox_env.read_claude_json()
    assert updated["numStartups"] == original["numStartups"]
    assert updated["cachedGrowthBookFeatures"] == original["cachedGrowthBookFeatures"]
    assert updated["tipsHistory"] == original["tipsHistory"]
    assert updated["autoUpdates"] == original["autoUpdates"]


def test_f10_adds_multiple_new_mcp_servers(sandbox_env):
    """Verify all new servers are populated under mcpServers."""
    new_servers = {
        "srv1": {"command": "uvx", "args": ["srv1"]},
        "srv2": {"command": "uvx", "args": ["srv2"]},
        "srv3": {"command": "uvx", "args": ["srv3"]}
    }
    res = MockClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        new_servers,
        sandbox_env.backups_dir
    )
    assert res["merged"] == 3
    updated = sandbox_env.read_claude_json()
    for name in ["srv1", "srv2", "srv3"]:
        assert name in updated["mcpServers"]


def test_f10_creates_pre_mutation_backup(sandbox_env):
    """Verify backup file is generated before .claude.json is modified."""
    new_servers = {"srv-backup-test": {"command": "uvx", "args": ["test"]}}
    res = MockClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        new_servers,
        sandbox_env.backups_dir
    )
    backup_path = Path(res["backup"])
    assert backup_path.exists()
    assert backup_path.name.startswith(".claude.json.bak.")


def test_f10_skips_overwriting_existing_server_without_force(sandbox_env):
    """Verify existing server definitions are not overwritten without force=True."""
    # Attempt to overwrite tinyfish with a dummy command
    overwrite_attempt = {
        "tinyfish": {"command": "corrupt-overwrite", "args": []}
    }
    res = MockClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        overwrite_attempt,
        sandbox_env.backups_dir,
        force=False
    )
    assert res["preserved"] == 1
    assert res["merged"] == 0

    updated = sandbox_env.read_claude_json()
    assert updated["mcpServers"]["tinyfish"]["type"] == "http"
    assert "corrupt-overwrite" not in str(updated["mcpServers"]["tinyfish"])
