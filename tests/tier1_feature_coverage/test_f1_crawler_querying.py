"""Tier 1 Feature 1: Official & Community Registry Crawling.

Tests the discovery and filtering logic for official and community MCP/skill registries:
- Official registry recognition (modelcontextprotocol/servers)
- Community repository star threshold (>= 100 stars)
- Archived repository exclusion
- Disabled/fork status handling
- Monorepo subdirectory package discovery
"""

import pytest
from typing import Dict, Any, List


class MockCrawlerEngine:
    """Mock/Reference implementation of Crawler filter logic for opaque-box testing."""

    OFFICIAL_ORGS = {"modelcontextprotocol", "anthropics", "google"}
    MIN_COMMUNITY_STARS = 100

    @classmethod
    def filter_candidate_repo(cls, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if a repository meets discovery criteria."""
        owner = repo.get("owner", "").lower()
        stars = repo.get("stars", 0)
        archived = repo.get("archived", False)
        disabled = repo.get("disabled", False)

        if disabled:
            return {"accepted": False, "reason": "Repository is disabled"}
        if archived:
            return {"accepted": False, "reason": "Repository is archived"}
        if owner in cls.OFFICIAL_ORGS:
            return {"accepted": True, "type": "official"}
        if stars >= cls.MIN_COMMUNITY_STARS:
            return {"accepted": True, "type": "community"}
        return {"accepted": False, "reason": f"Community repository has {stars} stars (< {cls.MIN_COMMUNITY_STARS})"}

    @classmethod
    def discover_monorepo_packages(cls, repo: Dict[str, Any], subpaths: List[str]) -> List[Dict[str, Any]]:
        """Extract multi-package tools from monorepo directories."""
        discovered = []
        for path in subpaths:
            parts = path.strip("/").split("/")
            pkg_id = parts[-1]
            discovered.append({
                "id": pkg_id,
                "subpath": path,
                "parent_repo": repo.get("full_name")
            })
        return discovered


def test_f1_official_registry_inclusion():
    """Verify that official organization repositories are accepted unconditionally."""
    official_repo = {
        "full_name": "modelcontextprotocol/servers",
        "owner": "modelcontextprotocol",
        "stars": 42,  # Below 100 stars still accepted for official
        "archived": False,
        "disabled": False
    }
    result = MockCrawlerEngine.filter_candidate_repo(official_repo)
    assert result["accepted"] is True
    assert result["type"] == "official"


def test_f1_community_repo_above_star_threshold():
    """Verify that community repositories with >= 100 stars are accepted."""
    community_repo = {
        "full_name": "community-dev/sqlite-inspector-mcp",
        "owner": "community-dev",
        "stars": 245,
        "archived": False,
        "disabled": False
    }
    result = MockCrawlerEngine.filter_candidate_repo(community_repo)
    assert result["accepted"] is True
    assert result["type"] == "community"


def test_f1_community_repo_below_star_threshold():
    """Verify that community repositories with < 100 stars are rejected."""
    community_repo = {
        "full_name": "hobbyist/personal-calc-mcp",
        "owner": "hobbyist",
        "stars": 48,
        "archived": False,
        "disabled": False
    }
    result = MockCrawlerEngine.filter_candidate_repo(community_repo)
    assert result["accepted"] is False
    assert "Community repository has 48 stars" in result["reason"]


def test_f1_archived_repo_rejection():
    """Verify that archived repositories are rejected even if they have many stars."""
    archived_repo = {
        "full_name": "legacy-org/abandoned-server",
        "owner": "legacy-org",
        "stars": 12500,
        "archived": True,
        "disabled": False
    }
    result = MockCrawlerEngine.filter_candidate_repo(archived_repo)
    assert result["accepted"] is False
    assert result["reason"] == "Repository is archived"


def test_f1_disabled_repo_rejection():
    """Verify that disabled repositories are rejected immediately."""
    disabled_repo = {
        "full_name": "bad-actor/malicious-pkg",
        "owner": "bad-actor",
        "stars": 500,
        "archived": False,
        "disabled": True
    }
    result = MockCrawlerEngine.filter_candidate_repo(disabled_repo)
    assert result["accepted"] is False
    assert result["reason"] == "Repository is disabled"


def test_f1_monorepo_subdirectory_discovery():
    """Verify that subpackages within official monorepos are indexed as distinct tools."""
    monorepo = {"full_name": "modelcontextprotocol/servers", "owner": "modelcontextprotocol"}
    subpaths = ["src/sqlite", "src/postgres", "src/brave-search", "src/fetch"]
    packages = MockCrawlerEngine.discover_monorepo_packages(monorepo, subpaths)
    assert len(packages) == 4
    pkg_ids = [p["id"] for p in packages]
    assert "sqlite" in pkg_ids
    assert "postgres" in pkg_ids
    assert "brave-search" in pkg_ids
    assert "fetch" in pkg_ids
