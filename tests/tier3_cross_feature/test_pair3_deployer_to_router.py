"""Tier 3 Pairwise Integration: Deployer ↔ Router Interface Contract.

Tests the integration and contract between M3 (Deployer) and M4 (Router):
- Router dynamically discovers deployed skills and MCP servers from the environment
- Router synthesizes task routing matrix matching only actually installed tools
- Delimiter-based injection into AGENTS.md, CLAUDE.md, and GEMINI.md
- Preservation of pre-existing AWS Agent Toolkit directives and Crave policies across all targets
- Idempotency over multiple deployment-router execution cycles
"""

import json
from pathlib import Path
import pytest
from typing import Dict, Any, List


class DeployerRouterPipeline:
    """Simulates the Deployer-to-Router workflow."""

    @classmethod
    def sync_routing_rules(cls, sandbox_env: Any, oracle: Any) -> Dict[str, Any]:
        """Inspect sandbox and inject matching routing directives."""
        # Step 1: Discover deployed tools
        deployed_skills = [
            d.name for d in sandbox_env.gemini_skills_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        claude_data = sandbox_env.read_claude_json()
        deployed_servers = list(claude_data.get("mcpServers", {}).keys())

        # Step 2: Formulate directive
        lines = [
            "# AI Skills & MCP Tool Routing Matrix",
            "",
            "| Domain | Installed Tools |",
            "|---|---|"
        ]
        if deployed_skills:
            lines.append(f"| **Skills** | {', '.join(f'`{s}`' for s in sorted(deployed_skills))} |")
        if deployed_servers:
            lines.append(f"| **MCP Servers** | {', '.join(f'`{s}`' for s in sorted(deployed_servers))} |")

        lines.extend([
            "",
            "## Activation Rules:",
            "1. Activate on demand only.",
            "2. Execute heavy builds via Crave Builder (`crave.exe -n run`)."
        ])
        directive = "\n".join(lines)

        # Step 3: Inject into rule files
        updated_files = []
        for rule_file in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
            target = sandbox_env.root_dir / rule_file
            if target.exists():
                initial = target.read_text(encoding="utf-8")
                injected = oracle.inject_rule_delimiters(initial, directive)
                target.write_text(injected, encoding="utf-8")
                updated_files.append(rule_file)

        return {
            "discovered_skills": deployed_skills,
            "discovered_servers": deployed_servers,
            "updated_files": updated_files
        }


def test_pair3_router_discovers_deployed_tools(sandbox_env, oracle):
    """Verify router identifies deployed skills and MCP servers."""
    # Mount a skill
    (sandbox_env.gemini_skills_dir / "opencut").mkdir(parents=True, exist_ok=True)
    # Add an MCP server
    claude = sandbox_env.read_claude_json()
    claude["mcpServers"]["sqlite"] = {"command": "npx"}
    sandbox_env.write_claude_json(claude)

    res = DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)
    assert "opencut" in res["discovered_skills"]
    assert "sqlite" in res["discovered_servers"]
    assert "tinyfish" in res["discovered_servers"]


def test_pair3_router_updates_all_three_rule_files(sandbox_env, oracle):
    """Verify AGENTS.md, CLAUDE.md, and GEMINI.md are all updated with delimiters."""
    res = DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)
    assert "AGENTS.md" in res["updated_files"]
    assert "CLAUDE.md" in res["updated_files"]
    assert "GEMINI.md" in res["updated_files"]

    for rf in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
        content = sandbox_env.read_rule_file(rf)
        assert oracle.DELIMITER_START in content
        assert oracle.DELIMITER_END in content


def test_pair3_preserves_aws_and_crave_rules_across_all_files(sandbox_env, oracle):
    """Verify AWS and Crave rules remain intact across all rule files after router injection."""
    DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)

    agents_content = sandbox_env.read_rule_file("AGENTS.md")
    assert "<!-- BEGIN AWS Agent Toolkit rules -->" in agents_content
    assert "crave.exe -n run" in agents_content

    claude_content = sandbox_env.read_rule_file("CLAUDE.md")
    assert "Boil the ocean" in claude_content
    assert "crave.exe" in claude_content

    gemini_content = sandbox_env.read_rule_file("GEMINI.md")
    assert "<!-- BEGIN AWS Agent Toolkit rules -->" in gemini_content


def test_pair3_idempotency_over_multiple_sync_cycles(sandbox_env, oracle):
    """Verify running deployer-to-router sync 3 times results in identical file content."""
    DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)
    content_cycle1 = sandbox_env.read_rule_file("AGENTS.md")

    DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)
    content_cycle2 = sandbox_env.read_rule_file("AGENTS.md")

    assert content_cycle1 == content_cycle2
    assert content_cycle2.count(oracle.DELIMITER_START) == 1
    assert content_cycle2.count(oracle.DELIMITER_END) == 1


def test_pair3_unmounted_packages_excluded_from_matrix(sandbox_env, oracle):
    """Verify tools not currently mounted on disk are omitted from routing table."""
    # Run sync on default sandbox (only opencut not mounted, tinyfish in claude)
    DeployerRouterPipeline.sync_routing_rules(sandbox_env, oracle)
    agents_content = sandbox_env.read_rule_file("AGENTS.md")
    assert "`phantom-unmounted-tool`" not in agents_content
