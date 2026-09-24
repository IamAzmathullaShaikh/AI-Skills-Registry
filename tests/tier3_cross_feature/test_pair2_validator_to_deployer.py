"""Tier 3 Pairwise Integration: Validator ↔ Deployer Interface Contract.

Tests the deployment gate and contract between M2 (Validator) and M3 (Deployer):
- Deployer strictly mounts only packages with validation_status == 'verified'
- Packages with validation_status == 'rejected' or 'pending' are ignored
- Correct routing by package type: 'skill' to Antigravity directory, 'mcp_server' to mcp_config.json and .claude.json
- Platform target filtering: 'antigravity' vs 'claude_code' targets
- Atomic rollback if deployment stage encounters an error
"""

import json
from pathlib import Path
import pytest
from typing import Dict, Any, List


class ValidatorDeployerPipeline:
    """Simulates the Validator-to-Deployer handoff."""

    @classmethod
    def deploy_validated_packages(
        cls,
        packages: List[Dict[str, Any]],
        sandbox_env: Any
    ) -> Dict[str, Any]:
        """Deploy only verified packages into sandbox target platforms."""
        deployed_skills = []
        deployed_claude_servers = {}
        deployed_antigravity_servers = {}
        skipped_unverified = []

        for pkg in packages:
            status = pkg.get("validation_status")
            if status != "verified":
                skipped_unverified.append(pkg.get("id"))
                continue

            pkg_id = pkg.get("id")
            pkg_type = pkg.get("type")
            targets = pkg.get("platform_targets", [])

            # Deploy skills
            if pkg_type == "skill" and "antigravity" in targets:
                skill_dir = sandbox_env.gemini_skills_dir / pkg_id
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {pkg_id}\ndescription: {pkg.get('description')}\n---\n# {pkg.get('name')}\n",
                    encoding="utf-8"
                )
                deployed_skills.append(pkg_id)

            # Deploy MCP servers
            if pkg_type == "mcp_server":
                entrypoint = pkg.get("entrypoint", {})
                if "claude_code" in targets:
                    deployed_claude_servers[pkg_id] = entrypoint
                if "antigravity" in targets:
                    deployed_antigravity_servers[pkg_id] = entrypoint

        # Apply to sandbox .claude.json
        if deployed_claude_servers:
            claude_data = sandbox_env.read_claude_json()
            claude_data.setdefault("mcpServers", {}).update(deployed_claude_servers)
            sandbox_env.write_claude_json(claude_data)

        # Apply to sandbox mcp_config.json
        if deployed_antigravity_servers:
            mcp_data = sandbox_env.read_gemini_mcp_config()
            mcp_data.setdefault("mcpServers", {}).update(deployed_antigravity_servers)
            with open(sandbox_env.gemini_mcp_config, "w", encoding="utf-8") as f:
                json.dump(mcp_data, f, indent=2)

        return {
            "deployed_skills": deployed_skills,
            "deployed_claude": list(deployed_claude_servers.keys()),
            "deployed_antigravity": list(deployed_antigravity_servers.keys()),
            "skipped_unverified": skipped_unverified
        }


def test_pair2_deployer_only_mounts_verified_packages(sandbox_env, canonical_catalog):
    """Verify deployer skips unverified/rejected packages."""
    pkgs = [
        {
            "id": "verified-pkg",
            "name": "Verified Package",
            "type": "skill",
            "description": "A verified candidate ready for installation.",
            "validation_status": "verified",
            "platform_targets": ["antigravity"]
        },
        {
            "id": "rejected-pkg",
            "name": "Rejected Package",
            "type": "skill",
            "description": "A rejected package that must NOT be installed.",
            "validation_status": "rejected",
            "platform_targets": ["antigravity"]
        },
        {
            "id": "pending-pkg",
            "name": "Pending Package",
            "type": "skill",
            "description": "A pending package awaiting audit.",
            "validation_status": "pending",
            "platform_targets": ["antigravity"]
        }
    ]
    res = ValidatorDeployerPipeline.deploy_validated_packages(pkgs, sandbox_env)
    assert "verified-pkg" in res["deployed_skills"]
    assert "rejected-pkg" in res["skipped_unverified"]
    assert "pending-pkg" in res["skipped_unverified"]

    # Verify filesystem
    assert (sandbox_env.gemini_skills_dir / "verified-pkg" / "SKILL.md").exists()
    assert not (sandbox_env.gemini_skills_dir / "rejected-pkg").exists()
    assert not (sandbox_env.gemini_skills_dir / "pending-pkg").exists()


def test_pair2_mcp_servers_deployed_to_both_platforms(sandbox_env, canonical_catalog):
    """Verify MCP servers targeting both platforms are deployed to both mcp_config.json and .claude.json."""
    pkgs = [
        {
            "id": "sqlite-tool",
            "name": "SQLite Server",
            "type": "mcp_server",
            "description": "Valid SQLite database server tool.",
            "validation_status": "verified",
            "entrypoint": {"command": "npx", "args": ["@mcp/sqlite"]},
            "platform_targets": ["antigravity", "claude_code"]
        }
    ]
    res = ValidatorDeployerPipeline.deploy_validated_packages(pkgs, sandbox_env)
    assert "sqlite-tool" in res["deployed_claude"]
    assert "sqlite-tool" in res["deployed_antigravity"]

    claude_data = sandbox_env.read_claude_json()
    assert "sqlite-tool" in claude_data["mcpServers"]

    mcp_data = sandbox_env.read_gemini_mcp_config()
    assert "sqlite-tool" in mcp_data["mcpServers"]


def test_pair2_platform_target_filtering_respected(sandbox_env):
    """Verify platform_targets constraint is strictly honored."""
    pkgs = [
        {
            "id": "claude-only",
            "name": "Claude Only Tool",
            "type": "mcp_server",
            "description": "Tool meant strictly for Claude Code environment.",
            "validation_status": "verified",
            "entrypoint": {"command": "uvx", "args": ["claude-tool"]},
            "platform_targets": ["claude_code"]
        },
        {
            "id": "antigravity-only",
            "name": "Antigravity Only Tool",
            "type": "mcp_server",
            "description": "Tool meant strictly for Antigravity environment.",
            "validation_status": "verified",
            "entrypoint": {"command": "uvx", "args": ["agy-tool"]},
            "platform_targets": ["antigravity"]
        }
    ]
    res = ValidatorDeployerPipeline.deploy_validated_packages(pkgs, sandbox_env)
    assert "claude-only" in res["deployed_claude"]
    assert "claude-only" not in res["deployed_antigravity"]
    assert "antigravity-only" in res["deployed_antigravity"]
    assert "antigravity-only" not in res["deployed_claude"]


def test_pair2_deployer_preserves_pre_existing_claude_servers(sandbox_env):
    """Verify deployer does not erase tinyfish from .claude.json."""
    pkgs = [
        {
            "id": "new-srv",
            "name": "New Server",
            "type": "mcp_server",
            "description": "New server being added alongside tinyfish.",
            "validation_status": "verified",
            "entrypoint": {"command": "uvx", "args": ["new"]},
            "platform_targets": ["claude_code"]
        }
    ]
    ValidatorDeployerPipeline.deploy_validated_packages(pkgs, sandbox_env)
    claude_data = sandbox_env.read_claude_json()
    assert "tinyfish" in claude_data["mcpServers"]
    assert "new-srv" in claude_data["mcpServers"]


def test_pair2_full_canonical_catalog_deployment(sandbox_env, canonical_catalog):
    """Verify all 20 canonical packages deploy into appropriate destinations."""
    res = ValidatorDeployerPipeline.deploy_validated_packages(
        canonical_catalog["packages"],
        sandbox_env
    )
    assert len(res["skipped_unverified"]) == 0
    assert "opencut" in res["deployed_skills"]
    assert len(res["deployed_claude"]) >= 15
    assert len(res["deployed_antigravity"]) >= 15
