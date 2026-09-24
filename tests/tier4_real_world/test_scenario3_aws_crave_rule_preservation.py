"""Tier 4 Real-World Workload Scenario 3: Protected Ambient Directives Preservation.

Simulates rule injection across user rule files containing pre-existing policies:
- AGENTS.md: AWS Agent Toolkit directives and Crave Cloud Builder policy
- CLAUDE.md: Core Implementation Directive and Crave Cloud Builder policy
- GEMINI.md: AWS Agent Toolkit directives
- Synthesis of 2-Tier Progressive Task-Based Routing Directives (<100 lines)
- Injection using delimiters: <!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING --> ...
- Verification of 100% preservation of all pre-existing sections
- Adherence to Antigravity 24 KB / 24,000-byte per-file limit
"""

from pathlib import Path
import pytest


def test_scenario3_rule_preservation_and_size_caps(sandbox_env, canonical_catalog, oracle):
    """Verify ambient rule preservation and size cap adherence across all rule targets."""
    # 1. Capture initial contents
    initial_agents = sandbox_env.read_rule_file("AGENTS.md")
    initial_claude = sandbox_env.read_rule_file("CLAUDE.md")
    initial_gemini = sandbox_env.read_rule_file("GEMINI.md")

    # 2. Synthesize routing directive
    routing_directive = """# AI Skills & MCP Tool Routing Matrix

| Domain / Task Type | Assigned Capability | Platform | Key Policy |
| :--- | :--- | :--- | :--- |
| **Database & SQL** | `mcp:sqlite` / `mcp:postgres` | Claude / Antigravity | Read-only queries by default. |
| **Web Research** | `mcp:brave-search` / `mcp:fetch` | Claude / Antigravity | brave-search for queries; fetch for URLs. |
| **Video & Media** | `skill:opencut` | Antigravity | Read skills/opencut/SKILL.md. |
| **Version Control** | `mcp:git` | Claude / Antigravity | Prefer native git; use mcp:git for deep history. |
| **Cloud & DevOps** | AWS Toolkit / `mcp:docker` | System / Crave | Adhere strictly to AWS Region and Crave build policies. |

## Progressive Activation Guidelines:
1. Load skill documentation on-demand only.
2. Destructive operations require user confirmation.
3. Heavy compilation must route to Crave Devspace CLI (`crave.exe -n run`)."""

    # 3. Inject into all 3 rule files
    for rf_name in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
        initial_text = sandbox_env.read_rule_file(rf_name)
        injected = oracle.inject_rule_delimiters(initial_text, routing_directive)
        (sandbox_env.root_dir / rf_name).write_text(injected, encoding="utf-8")

    # 4. Assertions on AGENTS.md
    updated_agents = sandbox_env.read_rule_file("AGENTS.md")
    assert "<!-- BEGIN AWS Agent Toolkit rules -->" in updated_agents
    assert "<!-- END AWS Agent Toolkit rules -->" in updated_agents
    assert "MUST NOT use Lambda@Edge." in updated_agents
    assert "Heavy Builds & Cloud Compilation Policy: Crave Builder" in updated_agents
    assert "crave.exe -n run" in updated_agents
    assert oracle.DELIMITER_START in updated_agents
    assert oracle.DELIMITER_END in updated_agents
    assert len(updated_agents.encode("utf-8")) < 24000

    # 5. Assertions on CLAUDE.md
    updated_claude = sandbox_env.read_rule_file("CLAUDE.md")
    assert "Core Implementation Directive" in updated_claude
    assert "Boil the ocean" in updated_claude
    assert "crave.exe" in updated_claude
    assert oracle.DELIMITER_START in updated_claude
    assert oracle.DELIMITER_END in updated_claude
    assert len(updated_claude.encode("utf-8")) < 24000

    # 6. Assertions on GEMINI.md
    updated_gemini = sandbox_env.read_rule_file("GEMINI.md")
    assert "<!-- BEGIN AWS Agent Toolkit rules -->" in updated_gemini
    assert oracle.DELIMITER_START in updated_gemini
    assert oracle.DELIMITER_END in updated_gemini
    assert len(updated_gemini.encode("utf-8")) < 24000
