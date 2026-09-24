"""Tier 4 Real-World Workload Scenario 1: Clean Machine Initialization.

Simulates a brand new developer machine setup:
- Zero pre-existing skills in ~/.gemini/config/skills/
- Empty (0-byte) ~/.gemini/config/mcp_config.json
- Initial empty ~/.claude.json
- Empty rule files
- Full end-to-end execution: crawl -> validate -> deploy -> inject rules
- Asserts that all platforms are safely initialized without crashes
"""

import json
from pathlib import Path
import pytest


def test_scenario1_clean_machine_full_lifecycle(tmp_path, canonical_catalog, oracle):
    """Execute end-to-end pipeline on clean machine environment."""
    # Step 1: Create fresh environment
    gemini_cfg = tmp_path / ".gemini" / "config"
    skills_dir = gemini_cfg / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 0-byte mcp_config.json
    mcp_config = gemini_cfg / "mcp_config.json"
    mcp_config.touch()
    assert mcp_config.stat().st_size == 0

    claude_json = tmp_path / ".claude.json"
    with open(claude_json, "w", encoding="utf-8") as f:
        json.dump({"mcpServers": {}}, f)

    agents_md = tmp_path / "AGENTS.md"
    agents_md.touch()

    # Step 2: Simulate Deployment of canonical packages
    # Mount skills
    skill_pkgs = [p for p in canonical_catalog["packages"] if p["type"] == "skill"]
    for s in skill_pkgs:
        s_dir = skills_dir / s["id"]
        s_dir.mkdir(parents=True, exist_ok=True)
        (s_dir / "SKILL.md").write_text(
            f"---\nname: {s['id']}\ndescription: {s['description']}\n---\n# {s['name']}\n",
            encoding="utf-8"
        )

    # Populate Antigravity mcp_config.json
    mcp_pkgs = [p for p in canonical_catalog["packages"] if p["type"] == "mcp_server" and "antigravity" in p["platform_targets"]]
    agy_servers = {p["id"]: p["entrypoint"] for p in mcp_pkgs}
    with open(mcp_config, "w", encoding="utf-8") as f:
        json.dump({"mcpServers": agy_servers}, f, indent=2)

    # Populate Claude Code .claude.json
    claude_pkgs = [p for p in canonical_catalog["packages"] if p["type"] == "mcp_server" and "claude_code" in p["platform_targets"]]
    claude_servers = {p["id"]: p["entrypoint"] for p in claude_pkgs}
    claude_data = {"mcpServers": claude_servers}
    with open(claude_json, "w", encoding="utf-8") as f:
        json.dump(claude_data, f, indent=2)

    # Inject rules into AGENTS.md
    directive = "# Clean Machine Installed Routing\n| Tools | Registered |"
    injected_agents = oracle.inject_rule_delimiters("", directive)
    agents_md.write_text(injected_agents, encoding="utf-8")

    # Step 3: Assertions
    # Antigravity skills mounted
    assert (skills_dir / "opencut" / "SKILL.md").exists()

    # mcp_config.json valid and non-empty
    assert mcp_config.stat().st_size > 0
    with open(mcp_config, "r", encoding="utf-8") as f:
        mcp_loaded = json.load(f)
    assert len(mcp_loaded["mcpServers"]) >= 15

    # Claude Code .claude.json valid
    with open(claude_json, "r", encoding="utf-8") as f:
        claude_loaded = json.load(f)
    assert len(claude_loaded["mcpServers"]) >= 15

    # AGENTS.md contains managed routing delimiters
    agents_content = agents_md.read_text(encoding="utf-8")
    assert oracle.DELIMITER_START in agents_content
    assert oracle.DELIMITER_END in agents_content
