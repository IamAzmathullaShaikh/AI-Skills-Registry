"""Progressive Task-Based Routing Directives Generator Module.

Synthesizes compact 2-tier routing tables that map task domains to newly
installed tools, adhering to strict size caps (<100 lines, <4,000 bytes)
to conserve model context windows while ensuring accurate skill activation.
"""

from __future__ import annotations

from typing import Any, Dict, List


class RoutingMatrixGenerator:
    """Production routing directive generator for local models."""

    DOMAIN_METADATA = {
        "data_databases": (
            "Database & SQL",
            "Read-only queries by default. Verify schema first.",
        ),
        "browser_search": (
            "Web Research",
            "brave-search for queries; fetch for URLs.",
        ),
        "media": (
            "Video & Media",
            "Read skill documentation before multi-step edit.",
        ),
        "code_intelligence": (
            "Code & VCS",
            "Prefer built-in git; use MCP for deep AST queries.",
        ),
        "system_ops": (
            "System & Ops",
            "Strictly respect AWS Region and Crave cloud policies.",
        ),
    }

    @classmethod
    def generate_directive(cls, deployed_tools: List[Dict[str, Any]]) -> str:
        """Generate a compact 2-tier routing directive table."""
        lines = [
            "# AI Skills & MCP Tool Routing Matrix",
            "",
            "Activate newly installed capabilities strictly based on task domain:",
            "",
            "| Domain / Task Type | Assigned Capability | Platform | Key Policy |",
            "| :--- | :--- | :--- | :--- |",
        ]

        categorized: Dict[str, List[str]] = {}
        for tool in deployed_tools:
            cat = tool.get("category", "system_ops")
            tool_id = tool.get("id", "")
            categorized.setdefault(cat, []).append(f"`{tool_id}`")

        for cat, (label, policy) in cls.DOMAIN_METADATA.items():
            tool_list = ", ".join(categorized.get(cat, ["`none`"]))
            lines.append(f"| **{label}** | {tool_list} | Antigravity / Claude | {policy} |")

        lines.extend([
            "",
            "## Progressive Activation Guidelines:",
            "1. On-Demand Loading: Do NOT load or inspect skill directories until user prompt triggers domain.",
            "2. Safety First: Destructive database writes or system changes require explicit confirmation.",
            "3. Cloud & Compilation: Route heavy builds through Crave Devspace CLI (`crave.exe -n run`).",
        ])

        return "\n".join(lines)
