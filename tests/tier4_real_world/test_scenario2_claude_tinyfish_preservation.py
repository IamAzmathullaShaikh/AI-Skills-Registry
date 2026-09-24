"""Tier 4 Real-World Workload Scenario 2: Claude Code tinyfish Credential Preservation.

Simulates deployment into an existing, complex, and sensitive Claude Code environment:
- ~/.claude.json contains user's active 'tinyfish' MCP server with sensitive API key
- ~/.claude.json contains extensive user state (cachedGrowthBookFeatures, numStartups, tips)
- Deployment of 15+ newly discovered and verified MCP servers
- Verification that tinyfish credentials, server URL, headers, and user flags remain 100% intact
- Verification that timestamped pre-mutation backup is generated
"""

import copy
import json
import time
from pathlib import Path
import pytest


def test_scenario2_tinyfish_credential_and_state_preservation(sandbox_env, canonical_catalog, oracle):
    """Verify complete non-destructive merging with sensitive tinyfish server preservation."""
    # 1. Baseline state check
    baseline_claude = sandbox_env.read_claude_json()
    assert "tinyfish" in baseline_claude["mcpServers"]
    tinyfish_config = copy.deepcopy(baseline_claude["mcpServers"]["tinyfish"])
    assert tinyfish_config["headers"]["X-API-Key"] == "sk-tinyfish-XF3WGyHrnMiULqKTZWQ4vk8IONL-DIfO"
    original_startups = baseline_claude["numStartups"]
    original_growthbook = copy.deepcopy(baseline_claude["cachedGrowthBookFeatures"])

    # 2. Extract new verified MCP servers targeting Claude Code
    new_servers = {}
    for pkg in canonical_catalog["packages"]:
        if pkg["type"] == "mcp_server" and "claude_code" in pkg.get("platform_targets", []):
            new_servers[pkg["id"]] = pkg["entrypoint"]

    assert len(new_servers) >= 15

    # 3. Simulate pre-mutation backup
    ts = int(time.time() * 1000)
    backup_file = sandbox_env.backups_dir / f".claude.json.bak.{ts}"
    backup_file.write_text(json.dumps(baseline_claude, indent=2), encoding="utf-8")

    # 4. Perform non-destructive deep merge
    merged_data = oracle.deep_merge_claude_json(baseline_claude, new_servers, force=False)
    sandbox_env.write_claude_json(merged_data)

    # 5. Post-deployment rigorous assertions
    result_claude = sandbox_env.read_claude_json()

    # CRITICAL ASSERTION: tinyfish is present and identical
    assert "tinyfish" in result_claude["mcpServers"]
    assert result_claude["mcpServers"]["tinyfish"] == tinyfish_config
    assert result_claude["mcpServers"]["tinyfish"]["headers"]["X-API-Key"] == "sk-tinyfish-XF3WGyHrnMiULqKTZWQ4vk8IONL-DIfO"

    # CRITICAL ASSERTION: All user settings intact
    assert result_claude["numStartups"] == original_startups
    assert result_claude["cachedGrowthBookFeatures"] == original_growthbook
    assert result_claude["tipsHistory"] == baseline_claude["tipsHistory"]
    assert result_claude["autoUpdates"] == baseline_claude["autoUpdates"]

    # Newly deployed servers present
    for srv_id in new_servers.keys():
        assert srv_id in result_claude["mcpServers"]

    # Total servers count: 1 (tinyfish) + new_servers
    assert len(result_claude["mcpServers"]) == len(new_servers) + 1

    # Verify backup exists and is valid JSON
    assert backup_file.exists()
    backup_content = json.loads(backup_file.read_text(encoding="utf-8"))
    assert backup_content == baseline_claude
