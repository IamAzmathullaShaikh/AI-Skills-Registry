"""Comprehensive End-to-End Verification Tests for Complete Production Pipeline.

Verifies:
- src.validator (SecurityFilter, SkillSchemaValidator, McpSchemaValidator, DryRunRunner)
- src.deployer (AntigravityDeployer, ClaudeDeployer)
- src.router (RoutingMatrixGenerator, RuleInjector)
- src.pipeline.PipelineRunner (Full lifecycle execution in virtual sandbox)
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.config import PipelineEnvironmentConfig
from src.deployer import AntigravityDeployer, ClaudeDeployer
from src.pipeline import PipelineRunner
from src.router import RoutingMatrixGenerator, RuleInjector
from src.validator import (
    DryRunRunner,
    McpSchemaValidator,
    SecurityFilter,
    SkillSchemaValidator,
)


def test_production_security_filter():
    """Verify production SecurityFilter detects injection and deprecation."""
    assert SecurityFilter.audit_package({"id": "aws-api-mcp-server"})["pass"] is False
    assert SecurityFilter.audit_package({
        "id": "bad-shell",
        "entrypoint": {"command": "cmd.exe", "args": ["/c", "dir"]}
    })["pass"] is False
    assert SecurityFilter.audit_package({
        "id": "clean-tool",
        "repo_url": "https://github.com/microsoft/playwright-mcp",
        "entrypoint": {"command": "npx", "args": ["@playwright/mcp"]}
    })["pass"] is True


def test_production_skill_schema_validator():
    """Verify production SkillSchemaValidator frontmatter rules."""
    valid_content = """---
name: opencut-editor
description: Comprehensive guide and reference for OpenCut video editing workflows.
---
# OpenCut
"""
    res = SkillSchemaValidator.validate_frontmatter(valid_content)
    assert res["valid"] is True
    assert res["metadata"]["name"] == "opencut-editor"

    bad_content = """---
name: Bad Name!
description: Short
---
"""
    res_bad = SkillSchemaValidator.validate_frontmatter(bad_content)
    assert res_bad["valid"] is False


def test_production_mcp_schema_validator():
    """Verify production McpSchemaValidator transport rules."""
    assert McpSchemaValidator.validate_transport_config({
        "command": "npx",
        "args": ["-y", "pkg"]
    })["valid"] is True

    assert McpSchemaValidator.validate_transport_config({
        "url": "https://mcp.example.com"
    })["valid"] is True

    assert McpSchemaValidator.validate_transport_config({})["valid"] is False


def test_production_dry_run_runner(canonical_catalog):
    """Verify production DryRunRunner on canonical catalog."""
    report = DryRunRunner.run_dry_run(canonical_catalog["packages"])
    assert report["total"] == 20
    assert report["passed"] == 20
    assert report["rejected"] == 0


def test_production_antigravity_deployer(sandbox_env):
    """Verify production AntigravityDeployer mounting and MCP registration."""
    skill_meta = {
        "name": "Custom Video Skill",
        "description": "Video editing and processing skill for multimedia workflows."
    }
    target = AntigravityDeployer.mount_skill(
        sandbox_env.gemini_skills_dir, "custom-video", skill_meta
    )
    assert target.exists()
    assert (target / "SKILL.md").exists()
    assert (target / "references").is_dir()

    mcp_res = AntigravityDeployer.register_mcp_server(
        sandbox_env.gemini_mcp_config,
        "test-mcp",
        {"command": "npx", "args": ["test"]},
        sandbox_env.backups_dir
    )
    assert mcp_res["status"] == "UPDATED"
    loaded = sandbox_env.read_gemini_mcp_config()
    assert "test-mcp" in loaded["mcpServers"]


def test_production_claude_deployer(sandbox_env):
    """Verify production ClaudeDeployer deep merge preserves tinyfish."""
    new_servers = {
        "sqlite": {"command": "npx", "args": ["@modelcontextprotocol/server-sqlite"]}
    }
    res = ClaudeDeployer.deep_merge_mcp_servers(
        sandbox_env.claude_json_path,
        new_servers,
        sandbox_env.backups_dir
    )
    assert res["status"] == "SUCCESS"
    assert res["merged"] == 1
    updated = sandbox_env.read_claude_json()
    assert "tinyfish" in updated["mcpServers"]
    assert "sqlite" in updated["mcpServers"]


def test_production_routing_matrix_and_injector(sandbox_env, canonical_catalog):
    """Verify production RoutingMatrixGenerator and RuleInjector."""
    directive = RoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    assert "**Database & SQL**" in directive
    assert len(directive.splitlines()) < 100
    assert len(directive.encode("utf-8")) < 4000

    content = sandbox_env.read_rule_file("AGENTS.md")
    injected = RuleInjector.inject_rule_delimiters(content, directive)
    assert RuleInjector.DELIMITER_START in injected
    assert RuleInjector.DELIMITER_END in injected
    assert "crave.exe -n run" in injected
    assert len(injected.encode("utf-8")) < 24000


def test_production_full_pipeline_sandbox_lifecycle():
    """Verify full PipelineRunner execution in virtual sandbox environment."""
    with tempfile.TemporaryDirectory() as tmp:
        sandbox_path = Path(tmp).resolve()
        config = PipelineEnvironmentConfig.from_sandbox(sandbox_path, populate_fixtures=True)

        runner = PipelineRunner(config)
        summary = runner.run()

        assert summary["status"] == "SUCCESS"
        assert summary["total_packages"] == 20
        assert summary["verified_packages"] == 20
        assert len(summary["injected_rule_files"]) == 3

        # Check sandbox .claude.json
        with open(config.claude_json_path, "r", encoding="utf-8") as f:
            claude_data = json.load(f)
        assert "tinyfish" in claude_data["mcpServers"]
        assert "browser-playwright" in claude_data["mcpServers"]

        # Check sandbox AGENTS.md
        with open(config.agents_rule_file, "r", encoding="utf-8") as f:
            agents_md = f.read()
        assert RuleInjector.DELIMITER_START in agents_md
        assert "<!-- BEGIN AWS Agent Toolkit rules -->" in agents_md
        assert "crave.exe -n run" in agents_md
