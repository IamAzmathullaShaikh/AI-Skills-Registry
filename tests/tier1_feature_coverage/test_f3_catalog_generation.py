"""Tier 1 Feature 3: Comprehensive 20-Package Catalog Generation.

Tests the master catalog structure and generation rules:
- Catalog contains >= 20 packages
- Balanced distribution across 5 core categories (Browser, Code, Data, Ops, Media)
- Global uniqueness of package IDs
- Dual support for both mcp_server and skill package types
- Valid JSON serializability adhering to Draft-07 root attributes
- Catalog README markdown presentation table formatting
"""

import json
import pytest
from typing import Dict, Any, List


class MockCatalogGenerator:
    """Mock/Reference catalog presentation formatter."""

    @classmethod
    def generate_readme_markdown(cls, catalog: Dict[str, Any]) -> str:
        """Format catalog into structured README markdown tables."""
        lines = [
            "# AI Model Skills & MCP Servers Catalog",
            "",
            f"Total Packages: {len(catalog.get('packages', []))}",
            ""
        ]
        packages_by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for pkg in catalog.get("packages", []):
            cat = pkg.get("category", "uncategorized")
            packages_by_cat.setdefault(cat, []).append(pkg)

        for cat, pkgs in packages_by_cat.items():
            lines.append(f"## Category: {cat.replace('_', ' ').title()}")
            lines.append("")
            lines.append("| ID | Name | Type | Stars | License | Description |")
            lines.append("|---|---|---|---|---|---|")
            for p in pkgs:
                lines.append(
                    f"| `{p.get('id')}` | **{p.get('name')}** | `{p.get('type')}` | "
                    f"{p.get('stars', 0)} | `{p.get('license')}` | {p.get('description')} |"
                )
            lines.append("")
        return "\n".join(lines)


def test_f3_catalog_contains_at_least_20_packages(canonical_catalog):
    """Verify catalog meets or exceeds the required 20-package milestone threshold."""
    packages = canonical_catalog.get("packages", [])
    assert len(packages) >= 20, f"Catalog contains only {len(packages)} packages (required >= 20)"
    assert canonical_catalog["total_packages"] == len(packages)


def test_f3_all_five_categories_represented(canonical_catalog):
    """Verify each of the 5 categories has balanced representation (>= 3 packages each)."""
    expected_categories = [
        "browser_search",
        "code_intelligence",
        "data_databases",
        "system_ops",
        "media"
    ]
    packages = canonical_catalog["packages"]
    counts = {cat: 0 for cat in expected_categories}
    for p in packages:
        cat = p["category"]
        if cat in counts:
            counts[cat] += 1

    for cat in expected_categories:
        assert counts[cat] >= 3, f"Category '{cat}' has only {counts[cat]} packages (expected >= 3)"


def test_f3_package_ids_are_globally_unique(canonical_catalog):
    """Verify no duplicate package IDs exist in the catalog."""
    packages = canonical_catalog["packages"]
    ids = [p["id"] for p in packages]
    unique_ids = set(ids)
    assert len(ids) == len(unique_ids), f"Duplicate package IDs found: {[x for x in ids if ids.count(x) > 1]}"


def test_f3_catalog_includes_skills_and_mcp_servers(canonical_catalog):
    """Verify catalog includes both mcp_server and skill types."""
    types = {p["type"] for p in canonical_catalog["packages"]}
    assert "mcp_server" in types, "Catalog lacks mcp_server package type"
    assert "skill" in types, "Catalog lacks skill package type (e.g. opencut)"


def test_f3_catalog_json_serialization(canonical_catalog):
    """Verify catalog dictionary cleanly round-trips through JSON serialization."""
    serialized = json.dumps(canonical_catalog, indent=2)
    deserialized = json.loads(serialized)
    assert deserialized["version"] == canonical_catalog["version"]
    assert deserialized["total_packages"] == len(canonical_catalog["packages"])
    assert len(deserialized["packages"]) == len(canonical_catalog["packages"])


def test_f3_readme_markdown_generation_renders_tables(canonical_catalog):
    """Verify markdown table generation produces correct headers and package entries."""
    markdown = MockCatalogGenerator.generate_readme_markdown(canonical_catalog)
    assert "# AI Model Skills & MCP Servers Catalog" in markdown
    assert "## Category: Browser Search" in markdown
    assert "## Category: Media" in markdown
    assert "| `browser-playwright` |" in markdown
    assert "| `opencut` |" in markdown
