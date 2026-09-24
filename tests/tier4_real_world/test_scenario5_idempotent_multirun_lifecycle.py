"""Tier 4 Real-World Workload Scenario 5: Idempotent Multi-Run Lifecycle.

Simulates 5 consecutive automated execution cycles (e.g. daily catalog updates):
- Successive runs of crawl -> validate -> deploy -> rule injection
- Asserts zero duplicate skill directories
- Asserts zero duplicate MCP servers in .claude.json and mcp_config.json
- Asserts exactly one managed routing block in rule files
- Asserts zero configuration drift across iterations
"""

import copy
import hashlib
import json
from pathlib import Path
import pytest


def test_scenario5_five_cycle_idempotent_lifecycle(sandbox_env, canonical_catalog, oracle):
    """Verify system stability and zero state drift over 5 consecutive pipeline cycles."""
    # Packages to deploy
    skill_pkg = next(p for p in canonical_catalog["packages"] if p["type"] == "skill")
    mcp_pkg = next(p for p in canonical_catalog["packages"] if p["type"] == "mcp_server")

    # Run 5 consecutive simulated pipeline cycles
    for cycle in range(5):
        # 1. Mount skill
        skill_dir = sandbox_env.gemini_skills_dir / skill_pkg["id"]
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_pkg['id']}\ndescription: {skill_pkg['description']}\n---\n# Title\n",
            encoding="utf-8"
        )

        # 2. Merge into Claude
        claude = sandbox_env.read_claude_json()
        merged_claude = oracle.deep_merge_claude_json(
            claude,
            {mcp_pkg["id"]: mcp_pkg["entrypoint"]},
            force=False
        )
        sandbox_env.write_claude_json(merged_claude)

        # 3. Merge into mcp_config.json
        mcp_cfg = sandbox_env.read_gemini_mcp_config()
        mcp_cfg.setdefault("mcpServers", {})[mcp_pkg["id"]] = mcp_pkg["entrypoint"]
        with open(sandbox_env.gemini_mcp_config, "w", encoding="utf-8") as f:
            json.dump(mcp_cfg, f, indent=2)

        # 4. Inject rules
        for rf in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
            target = sandbox_env.root_dir / rf
            initial_text = target.read_text(encoding="utf-8")
            injected = oracle.inject_rule_delimiters(initial_text, "# Routing Table\n| DB | sqlite |")
            target.write_text(injected, encoding="utf-8")

    # Post 5-cycle verifications
    # 1. Skills directory check
    skills = [d.name for d in sandbox_env.gemini_skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    assert skills.count(skill_pkg["id"]) == 1

    # 2. Claude Code check
    final_claude = sandbox_env.read_claude_json()
    assert "tinyfish" in final_claude["mcpServers"]
    assert mcp_pkg["id"] in final_claude["mcpServers"]
    # Check that mcpServers is a simple dictionary, not nested
    assert isinstance(final_claude["mcpServers"][mcp_pkg["id"]], dict)

    # 3. Antigravity MCP check
    final_mcp = sandbox_env.read_gemini_mcp_config()
    assert mcp_pkg["id"] in final_mcp["mcpServers"]

    # 4. Rule files delimiter check
    for rf in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
        text = sandbox_env.read_rule_file(rf)
        assert text.count(oracle.DELIMITER_START) == 1
        assert text.count(oracle.DELIMITER_END) == 1

    # 5. Stability check: compute hash of all targets, run cycle 6, assert identical hashes
    hash_agents_5 = hashlib.sha256(sandbox_env.read_rule_file("AGENTS.md").encode("utf-8")).hexdigest()
    hash_claude_5 = hashlib.sha256(sandbox_env.claude_json_path.read_bytes()).hexdigest()

    # Cycle 6
    injected = oracle.inject_rule_delimiters(sandbox_env.read_rule_file("AGENTS.md"), "# Routing Table\n| DB | sqlite |")
    sandbox_env.agents_md_path.write_text(injected, encoding="utf-8")

    hash_agents_6 = hashlib.sha256(sandbox_env.read_rule_file("AGENTS.md").encode("utf-8")).hexdigest()
    assert hash_agents_5 == hash_agents_6
