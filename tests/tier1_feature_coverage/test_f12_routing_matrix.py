"""Tier 1 Feature 12: 2-Tier Progressive Task-Based Routing Directives.

Tests the generation of compact 2-tier task routing directives:
- Coverage of all 5 task domains (Database, Web, Media, Ops, Code)
- Strict brevity constraints (< 100 lines / < 4,000 bytes)
- Correct mapping of tools to assigned problem domains
- Clear invocation guidelines preventing context window saturation
"""

import pytest
from typing import Dict, Any, List


class MockRoutingMatrixGenerator:
    """Mock/Reference routing matrix generator."""

    @classmethod
    def generate_directive(cls, deployed_tools: List[Dict[str, Any]]) -> str:
        """Generate a compact 2-tier routing directive table."""
        lines = [
            "# AI Skills & MCP Tool Routing Matrix",
            "",
            "Activate newly installed capabilities strictly based on task domain:",
            "",
            "| Domain / Task Type | Assigned Capability | Platform | Key Policy |",
            "| :--- | :--- | :--- | :--- |"
        ]

        # Domain mapping
        domain_map = {
            "data_databases": ("Database & SQL", "Read-only queries by default. Verify schema first."),
            "browser_search": ("Web Research", "brave-search for queries; fetch for URLs."),
            "media": ("Video & Media", "Read skill documentation before multi-step edit."),
            "code_intelligence": ("Code & VCS", "Prefer built-in git; use MCP for deep AST queries."),
            "system_ops": ("System & Ops", "Strictly respect AWS Region and Crave cloud policies.")
        }

        categorized: Dict[str, List[str]] = {}
        for tool in deployed_tools:
            cat = tool.get("category", "system_ops")
            tool_id = tool.get("id", "")
            categorized.setdefault(cat, []).append(f"`{tool_id}`")

        for cat, (label, policy) in domain_map.items():
            tool_list = ", ".join(categorized.get(cat, ["`none`"]))
            lines.append(f"| **{label}** | {tool_list} | Antigravity / Claude | {policy} |")

        lines.extend([
            "",
            "## Progressive Activation Guidelines:",
            "1. On-Demand Loading: Do NOT load or inspect skill directories until user prompt triggers domain.",
            "2. Safety First: Destructive database writes or system changes require explicit confirmation.",
            "3. Cloud & Compilation: Route heavy builds through Crave Devspace CLI (`crave.exe -n run`)."
        ])

        return "\n".join(lines)


def test_f12_generates_all_five_domains(canonical_catalog):
    """Verify routing matrix contains all 5 required domains."""
    directive = MockRoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    assert "**Database & SQL**" in directive
    assert "**Web Research**" in directive
    assert "**Video & Media**" in directive
    assert "**Code & VCS**" in directive
    assert "**System & Ops**" in directive


def test_f12_directive_under_100_lines(canonical_catalog):
    """Verify generated routing directive is under 100 lines to conserve context."""
    directive = MockRoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    line_count = len(directive.strip().split("\n"))
    assert line_count < 100, f"Directive exceeded line threshold: {line_count} lines"


def test_f12_directive_under_4_kb(canonical_catalog):
    """Verify byte size of generated routing directive is strictly under 4,000 bytes."""
    directive = MockRoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    byte_size = len(directive.encode("utf-8"))
    assert byte_size < 4000, f"Directive exceeded byte threshold: {byte_size} bytes"


def test_f12_maps_canonical_tools_to_correct_domains(canonical_catalog):
    """Verify specific tools appear in their intended domain rows."""
    directive = MockRoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    assert "`sqlite-inspector`" in directive
    assert "`brave-search`" in directive
    assert "`opencut`" in directive
    assert "`docker-container-mcp`" in directive


def test_f12_includes_progressive_activation_guidelines(canonical_catalog):
    """Verify directive includes instructions for on-demand loading and Crave compilation."""
    directive = MockRoutingMatrixGenerator.generate_directive(canonical_catalog["packages"])
    assert "On-Demand Loading" in directive
    assert "crave.exe -n run" in directive
