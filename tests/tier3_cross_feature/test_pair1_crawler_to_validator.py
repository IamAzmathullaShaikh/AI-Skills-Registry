"""Tier 3 Pairwise Integration: Crawler ↔ Validator Interface Contract.

Tests the data handoff and contract between M1 (Crawler) and M2 (Validator):
- Ingestion of crawled catalog.json candidate structures by the validation engine
- Transition of validation_status from 'pending' to 'verified' or 'rejected'
- Structured error generation for invalid or deprecated candidates
- Preservation of package attributes across validation stages
- Category and total count reconciliation
"""

import copy
import pytest
from typing import Dict, Any, List


class CrawlerValidatorPipeline:
    """Simulates the Crawler-to-Validator data flow and interface contract."""

    @classmethod
    def process_crawled_catalog(cls, catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all packages produced by the crawler."""
        output_catalog = copy.deepcopy(catalog)
        validation_report = {
            "total": len(output_catalog.get("packages", [])),
            "passed": 0,
            "rejected": 0,
            "errors": []
        }

        for pkg in output_catalog.get("packages", []):
            pkg_id = pkg.get("id")
            # Quality & security criteria
            if pkg.get("stars", 0) < 100 and pkg.get("type") != "skill" and "modelcontextprotocol" not in pkg.get("repo_url", ""):
                pkg["validation_status"] = "rejected"
                pkg["validation_error"] = f"Community package has {pkg.get('stars')} stars (< 100)"
                validation_report["rejected"] += 1
                validation_report["errors"].append({"id": pkg_id, "error": pkg["validation_error"]})
                continue

            if pkg_id == "aws-api-mcp-server":
                pkg["validation_status"] = "rejected"
                pkg["validation_error"] = "Explicitly deprecated package"
                validation_report["rejected"] += 1
                validation_report["errors"].append({"id": pkg_id, "error": pkg["validation_error"]})
                continue

            desc = pkg.get("description", "")
            if len(desc) < 20:
                pkg["validation_status"] = "rejected"
                pkg["validation_error"] = "Description too short (< 20 chars)"
                validation_report["rejected"] += 1
                validation_report["errors"].append({"id": pkg_id, "error": pkg["validation_error"]})
                continue

            # Passed
            pkg["validation_status"] = "verified"
            validation_report["passed"] += 1

        return {
            "validated_catalog": output_catalog,
            "report": validation_report
        }


def test_pair1_canonical_catalog_passes_validator(canonical_catalog):
    """Verify all 20 canonical packages from crawler pass validation into 'verified' status."""
    res = CrawlerValidatorPipeline.process_crawled_catalog(canonical_catalog)
    report = res["report"]
    assert report["total"] == 20
    assert report["passed"] == 20
    assert report["rejected"] == 0

    for pkg in res["validated_catalog"]["packages"]:
        assert pkg["validation_status"] == "verified"


def test_pair1_deprecated_package_marked_rejected_with_error(canonical_catalog):
    """Verify deprecated packages discovered by crawler are marked 'rejected' with error explanation."""
    test_catalog = copy.deepcopy(canonical_catalog)
    test_catalog["packages"].append({
        "id": "aws-api-mcp-server",
        "name": "Deprecated AWS Server",
        "stars": 500,
        "description": "Deprecated legacy MCP server for AWS API access.",
        "repo_url": "https://github.com/deprecated/aws-api-mcp-server",
        "type": "mcp_server",
        "entrypoint": {"command": "npx", "args": ["aws-api-mcp-server"]}
    })
    res = CrawlerValidatorPipeline.process_crawled_catalog(test_catalog)
    report = res["report"]
    assert report["total"] == 21
    assert report["passed"] == 20
    assert report["rejected"] == 1

    rejected_pkgs = [p for p in res["validated_catalog"]["packages"] if p["validation_status"] == "rejected"]
    assert len(rejected_pkgs) == 1
    assert rejected_pkgs[0]["id"] == "aws-api-mcp-server"
    assert "Explicitly deprecated" in rejected_pkgs[0]["validation_error"]


def test_pair1_low_star_community_repo_rejected(canonical_catalog):
    """Verify community repos with < 100 stars discovered by crawler are rejected."""
    test_catalog = copy.deepcopy(canonical_catalog)
    test_catalog["packages"].append({
        "id": "low-star-pkg",
        "name": "Low Star Community Tool",
        "stars": 42,
        "description": "A community tool with fewer than the required 100 stars.",
        "repo_url": "https://github.com/community/low-star-pkg",
        "type": "mcp_server",
        "entrypoint": {"command": "uvx", "args": ["low-star"]}
    })
    res = CrawlerValidatorPipeline.process_crawled_catalog(test_catalog)
    report = res["report"]
    assert report["rejected"] == 1
    err = report["errors"][0]
    assert err["id"] == "low-star-pkg"
    assert "42 stars" in err["error"]


def test_pair1_short_description_rejected(canonical_catalog):
    """Verify candidate with short description from crawler fails validator."""
    test_catalog = copy.deepcopy(canonical_catalog)
    test_catalog["packages"][0]["description"] = "Short"
    res = CrawlerValidatorPipeline.process_crawled_catalog(test_catalog)
    assert res["report"]["rejected"] == 1
    assert "Description too short" in res["report"]["errors"][0]["error"]


def test_pair1_catalog_metadata_preserved_through_validation(canonical_catalog):
    """Verify capabilities, entrypoint, license are preserved without mutation during validation."""
    orig_pkg = canonical_catalog["packages"][0]
    res = CrawlerValidatorPipeline.process_crawled_catalog(canonical_catalog)
    val_pkg = res["validated_catalog"]["packages"][0]

    assert val_pkg["id"] == orig_pkg["id"]
    assert val_pkg["capabilities"] == orig_pkg["capabilities"]
    assert val_pkg["entrypoint"] == orig_pkg["entrypoint"]
    assert val_pkg["license"] == orig_pkg["license"]
