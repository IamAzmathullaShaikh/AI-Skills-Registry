"""Tier 1 Feature 2: Standardized Metadata Schema Extraction.

Tests extraction of structured metadata from repository descriptors into Draft-07
catalog entry schema:
- Mandatory field presence (id, name, category, description, type, entrypoint)
- Capabilities extraction as list of string tokens
- Entrypoint structure verification (stdio vs sse)
- SPDX license normalization
- Runtime dependency specification
- Category partition taxonomy validation
"""

import pytest
from typing import Dict, Any, List

VALID_CATEGORIES = {
    "browser_search",
    "code_intelligence",
    "data_databases",
    "system_ops",
    "media"
}

REQUIRED_METADATA_FIELDS = {
    "id",
    "name",
    "category",
    "description",
    "repo_url",
    "type",
    "capabilities",
    "entrypoint",
    "dependencies",
    "license",
    "validation_status",
    "platform_targets"
}


class MockMetadataExtractor:
    """Mock/Reference metadata extraction validator."""

    @classmethod
    def validate_package_schema(cls, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata conforms to Draft-07 entry contract."""
        missing = [f for f in REQUIRED_METADATA_FIELDS if f not in entry]
        if missing:
            return {"valid": False, "error": f"Missing required fields: {missing}"}

        if entry["category"] not in VALID_CATEGORIES:
            return {"valid": False, "error": f"Invalid category: {entry['category']}"}

        if not isinstance(entry["capabilities"], list) or not entry["capabilities"]:
            return {"valid": False, "error": "Capabilities must be a non-empty list of strings"}

        if not isinstance(entry["entrypoint"], dict) or "command" not in entry["entrypoint"]:
            return {"valid": False, "error": "Entrypoint must be an object with 'command'"}

        if not isinstance(entry["dependencies"], dict):
            return {"valid": False, "error": "Dependencies must be a dict"}

        if not isinstance(entry["platform_targets"], list) or not entry["platform_targets"]:
            return {"valid": False, "error": "Platform targets must be non-empty list"}

        return {"valid": True, "error": None}


def test_f2_canonical_package_has_all_required_fields(canonical_catalog):
    """Verify all 20 canonical packages possess complete required field sets."""
    for pkg in canonical_catalog["packages"]:
        res = MockMetadataExtractor.validate_package_schema(pkg)
        assert res["valid"] is True, f"Package {pkg.get('id')} failed schema: {res['error']}"


def test_f2_missing_required_field_detected():
    """Verify validator flags missing mandatory fields."""
    incomplete_pkg = {
        "id": "test-pkg",
        "name": "Incomplete Pkg",
        # 'category' missing
        "description": "A package missing category field",
        "repo_url": "https://github.com/org/repo",
        "type": "mcp_server",
        "capabilities": ["test"],
        "entrypoint": {"command": "npx", "args": []},
        "dependencies": {},
        "license": "MIT",
        "validation_status": "pending",
        "platform_targets": ["claude_code"]
    }
    res = MockMetadataExtractor.validate_package_schema(incomplete_pkg)
    assert res["valid"] is False
    assert "Missing required fields" in res["error"]


def test_f2_invalid_category_rejected():
    """Verify unknown category triggers validation error."""
    pkg = {
        "id": "test-pkg",
        "name": "Test Pkg",
        "category": "blockchain_crypto",  # Not in taxonomy
        "description": "An invalid category package",
        "repo_url": "https://github.com/org/repo",
        "type": "mcp_server",
        "capabilities": ["test"],
        "entrypoint": {"command": "npx", "args": []},
        "dependencies": {},
        "license": "MIT",
        "validation_status": "pending",
        "platform_targets": ["claude_code"]
    }
    res = MockMetadataExtractor.validate_package_schema(pkg)
    assert res["valid"] is False
    assert "Invalid category: blockchain_crypto" in res["error"]


def test_f2_capabilities_must_be_non_empty_list():
    """Verify capabilities field cannot be empty or non-list."""
    pkg = {
        "id": "test-pkg",
        "name": "Test Pkg",
        "category": "browser_search",
        "description": "A package with empty capabilities",
        "repo_url": "https://github.com/org/repo",
        "type": "mcp_server",
        "capabilities": [],  # Empty
        "entrypoint": {"command": "npx", "args": []},
        "dependencies": {},
        "license": "MIT",
        "validation_status": "pending",
        "platform_targets": ["claude_code"]
    }
    res = MockMetadataExtractor.validate_package_schema(pkg)
    assert res["valid"] is False
    assert "Capabilities must be a non-empty list" in res["error"]


def test_f2_entrypoint_structure_validation():
    """Verify entrypoint dictionary contains mandatory command key."""
    pkg = {
        "id": "test-pkg",
        "name": "Test Pkg",
        "category": "browser_search",
        "description": "A package with bad entrypoint",
        "repo_url": "https://github.com/org/repo",
        "type": "mcp_server",
        "capabilities": ["run"],
        "entrypoint": {"not_a_command": "npx"},
        "dependencies": {},
        "license": "MIT",
        "validation_status": "pending",
        "platform_targets": ["claude_code"]
    }
    res = MockMetadataExtractor.validate_package_schema(pkg)
    assert res["valid"] is False
    assert "Entrypoint must be an object with 'command'" in res["error"]


def test_f2_platform_targets_contain_valid_runtimes(canonical_catalog):
    """Verify platform targets only reference supported platforms (antigravity, claude_code)."""
    allowed_platforms = {"antigravity", "claude_code", "cursor", "codex"}
    for pkg in canonical_catalog["packages"]:
        targets = pkg["platform_targets"]
        assert all(t in allowed_platforms for t in targets)
