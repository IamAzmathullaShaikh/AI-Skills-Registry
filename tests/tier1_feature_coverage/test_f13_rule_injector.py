"""Tier 1 Feature 13: Idempotent Rule File Injection.

Tests safe delimiter-based injection of routing directives into AGENTS.md, CLAUDE.md, and GEMINI.md:
- Managed delimiter block boundaries (BEGIN / END)
- Strict character-for-character preservation of pre-existing AWS rules
- Strict preservation of Crave Builder compilation policy
- Idempotency over repeated consecutive executions
- Total file size adherence to Antigravity 24,000-byte cap
- Clean replacement of existing delimited blocks upon updates
"""

import re
from pathlib import Path
import pytest


def test_f13_injects_delimited_block_into_agents_md(sandbox_env, oracle):
    """Verify delimiter block is inserted into AGENTS.md."""
    initial = sandbox_env.read_rule_file("AGENTS.md")
    assert oracle.DELIMITER_START not in initial

    directive = "# New Routing Table\n| DB | sqlite |"
    updated = oracle.inject_rule_delimiters(initial, directive)

    assert oracle.DELIMITER_START in updated
    assert oracle.DELIMITER_END in updated
    assert "# New Routing Table" in updated


def test_f13_preserves_aws_guidance_block(sandbox_env, oracle):
    """Verify pre-existing AWS Agent Toolkit block is completely preserved."""
    initial = sandbox_env.read_rule_file("AGENTS.md")
    directive = "# Routing Table"
    updated = oracle.inject_rule_delimiters(initial, directive)

    assert "<!-- BEGIN AWS Agent Toolkit rules -->" in updated
    assert "<!-- END AWS Agent Toolkit rules -->" in updated
    assert "MUST NOT use Lambda@Edge." in updated


def test_f13_preserves_crave_cloud_compilation_policy(sandbox_env, oracle):
    """Verify Crave compilation policy is preserved."""
    initial = sandbox_env.read_rule_file("AGENTS.md")
    directive = "# Routing Table"
    updated = oracle.inject_rule_delimiters(initial, directive)

    assert "Heavy Builds & Cloud Compilation Policy: Crave Builder" in updated
    assert "crave.exe -n run" in updated


def test_f13_idempotency_over_multiple_injections(sandbox_env, oracle):
    """Verify running injection 5 times results in identical file content."""
    content = sandbox_env.read_rule_file("AGENTS.md")
    directive = "# Managed Routing Matrix\n| Tools | List |"

    first_run = oracle.inject_rule_delimiters(content, directive)
    run_output = first_run
    for _ in range(4):
        run_output = oracle.inject_rule_delimiters(run_output, directive)

    assert run_output == first_run
    # Count occurrences of delimiter start
    assert run_output.count(oracle.DELIMITER_START) == 1
    assert run_output.count(oracle.DELIMITER_END) == 1


def test_f13_replaces_old_delimited_content_on_update(sandbox_env, oracle):
    """Verify that updating the routing directive replaces previous content between markers."""
    initial = sandbox_env.read_rule_file("AGENTS.md")
    first_directive = "# Old Version 1 Table"
    step1 = oracle.inject_rule_delimiters(initial, first_directive)

    second_directive = "# Updated Version 2 Table"
    step2 = oracle.inject_rule_delimiters(step1, second_directive)

    assert "# Updated Version 2 Table" in step2
    assert "# Old Version 1 Table" not in step2


def test_f13_total_file_size_well_below_24kb_cap(sandbox_env, oracle):
    """Verify resulting AGENTS.md remains strictly below 24,000 bytes."""
    initial = sandbox_env.read_rule_file("AGENTS.md")
    directive = "# AI Skills & MCP Tool Routing Matrix\n" + ("| test | tool |" * 10)
    updated = oracle.inject_rule_delimiters(initial, directive)

    byte_size = len(updated.encode("utf-8"))
    assert byte_size < 24000, f"File size {byte_size} bytes exceeded 24,000-byte cap"
