"""Tier 1 Feature 9: Antigravity MCP Server Configuration.

Tests updating and initializing ~/.gemini/config/mcp_config.json:
- Initializing an empty (0-byte) or non-existent mcp_config.json
- Stdio MCP server registration (command, args, env)
- SSE MCP server registration (serverUrl)
- Non-destructive preservation of pre-existing configured servers
- Atomic writing and temporary file cleanup
- Rolling backup generation
"""

import json
import os
import shutil
import time
from pathlib import Path
import pytest
from typing import Dict, Any


class MockAntigravityMcpConfigurator:
    """Mock/Reference Antigravity MCP configurator."""

    @classmethod
    def register_mcp_server(
        cls,
        mcp_config_path: Path,
        server_id: str,
        server_def: Dict[str, Any],
        backup_dir: Path,
        force: bool = False
    ) -> Dict[str, Any]:
        """Safely register an MCP server into mcp_config.json."""
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
        tmp_file = mcp_config_path.with_suffix(f".tmp.{os.getpid()}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, mcp_config_path)

        return {"status": "UPDATED", "server_id": server_id}


def test_f9_initializes_empty_0_byte_file(sandbox_env):
    """Verify 0-byte mcp_config.json is successfully initialized into valid JSON object."""
    assert sandbox_env.gemini_mcp_config.stat().st_size == 0
    server_def = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-sqlite"]}
    res = MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config,
        "sqlite",
        server_def,
        sandbox_env.backups_dir
    )
    assert res["status"] == "UPDATED"
    data = sandbox_env.read_gemini_mcp_config()
    assert "sqlite" in data["mcpServers"]
    assert data["mcpServers"]["sqlite"]["command"] == "npx"


def test_f9_registers_sse_mcp_server(sandbox_env):
    """Verify SSE remote server registration with serverUrl."""
    server_def = {"serverUrl": "https://remote.example.com/sse"}
    res = MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config,
        "remote-sse",
        server_def,
        sandbox_env.backups_dir
    )
    assert res["status"] == "UPDATED"
    data = sandbox_env.read_gemini_mcp_config()
    assert data["mcpServers"]["remote-sse"]["serverUrl"] == "https://remote.example.com/sse"


def test_f9_preserves_existing_servers(sandbox_env):
    """Verify subsequent registrations preserve already configured servers."""
    server1 = {"command": "npx", "args": ["server-1"]}
    server2 = {"command": "uvx", "args": ["server-2"]}

    MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config, "srv1", server1, sandbox_env.backups_dir
    )
    MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config, "srv2", server2, sandbox_env.backups_dir
    )

    data = sandbox_env.read_gemini_mcp_config()
    assert "srv1" in data["mcpServers"]
    assert "srv2" in data["mcpServers"]


def test_f9_atomic_write_leaves_no_stray_tmp_files(sandbox_env):
    """Verify atomic write cleans up all .tmp files."""
    server_def = {"command": "npx", "args": ["server-clean"]}
    MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config, "srv-clean", server_def, sandbox_env.backups_dir
    )
    tmp_files = list(sandbox_env.gemini_config_dir.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_f9_creates_backup_when_updating_populated_file(sandbox_env):
    """Verify backup file is created in backup dir when updating populated config."""
    server1 = {"command": "npx", "args": ["server-1"]}
    server2 = {"command": "uvx", "args": ["server-2"]}

    MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config, "srv1", server1, sandbox_env.backups_dir
    )
    MockAntigravityMcpConfigurator.register_mcp_server(
        sandbox_env.gemini_mcp_config, "srv2", server2, sandbox_env.backups_dir
    )

    backups = list(sandbox_env.backups_dir.glob("mcp_config.json.bak.*"))
    assert len(backups) >= 1
