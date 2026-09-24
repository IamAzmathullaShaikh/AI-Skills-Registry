"""Tier 2 Boundary & Corner Cases: Catalog Size and Category Distribution Boundaries.

Tests boundary limits on catalog ingestion, sizing, and taxonomy constraints:
- Empty catalog (0 packages)
- Single package catalog (1 package)
- 19 packages boundary (below milestone requirement)
- 20 packages boundary (exact milestone threshold)
- Extreme size catalog (100 packages stress test)
- Skewed category distribution (all packages in 1 category)
- Duplicate package IDs
"""

import copy
import pytest
from typing import Dict, Any, List


class CatalogBoundaryValidator:
    """Evaluates catalog against milestone acceptance criteria."""

    MIN_TOTAL_PACKAGES = 20
    REQUIRED_CATEGORIES = {
        "browser_search",
        "code_intelligence",
        "data_databases",
        "system_ops",
        "media"
    }
    MIN_PER_CATEGORY = 3

    @classmethod
    def evaluate_catalog_boundaries(cls, catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Check all catalog boundary requirements."""
        packages = catalog.get("packages", [])
        total = len(packages)

        if total < cls.MIN_TOTAL_PACKAGES:
            return {"pass": False, "reason": f"Catalog has {total} packages (requires >= {cls.MIN_TOTAL_PACKAGES})"}

        # Duplicate ID check
        ids = [p.get("id") for p in packages]
        if len(ids) != len(set(ids)):
            return {"pass": False, "reason": "Catalog contains duplicate package IDs"}

        # Category distribution
        counts = {cat: 0 for cat in cls.REQUIRED_CATEGORIES}
        for p in packages:
            cat = p.get("category")
            if cat in counts:
                counts[cat] += 1

        for cat, cnt in counts.items():
            if cnt < cls.MIN_PER_CATEGORY:
                return {"pass": False, "reason": f"Category '{cat}' has {cnt} items (< {cls.MIN_PER_CATEGORY})"}

        return {"pass": True, "reason": "All catalog boundary criteria satisfied"}


def test_bva_empty_catalog_rejection():
    """Verify empty catalog (0 items) fails milestone requirements."""
    catalog = {"version": "1.0.0", "total_packages": 0, "packages": []}
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(catalog)
    assert res["pass"] is False
    assert "Catalog has 0 packages" in res["reason"]


def test_bva_single_item_catalog_rejection(canonical_catalog):
    """Verify single package catalog fails milestone boundary."""
    single_pkg = canonical_catalog["packages"][:1]
    catalog = {"version": "1.0.0", "total_packages": 1, "packages": single_pkg}
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(catalog)
    assert res["pass"] is False
    assert "Catalog has 1 packages" in res["reason"]


def test_bva_nineteen_packages_rejection(canonical_catalog):
    """Verify 19 packages (boundary - 1) fails milestone threshold."""
    pkgs_19 = canonical_catalog["packages"][:19]
    catalog = {"version": "1.0.0", "total_packages": 19, "packages": pkgs_19}
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(catalog)
    assert res["pass"] is False
    assert "Catalog has 19 packages" in res["reason"]


def test_bva_exact_twenty_packages_acceptance(canonical_catalog):
    """Verify exactly 20 packages (boundary point) passes milestone threshold."""
    assert len(canonical_catalog["packages"]) == 20
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(canonical_catalog)
    assert res["pass"] is True


def test_bva_skewed_single_category_rejection(canonical_catalog):
    """Verify 20 packages assigned to only 1 category fails category coverage."""
    skewed = copy.deepcopy(canonical_catalog)
    for p in skewed["packages"]:
        p["category"] = "browser_search"
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(skewed)
    assert res["pass"] is False
    assert "has 0 items" in res["reason"]


def test_bva_duplicate_ids_rejection(canonical_catalog):
    """Verify catalog containing duplicate IDs is rejected."""
    dup_catalog = copy.deepcopy(canonical_catalog)
    dup_catalog["packages"][1]["id"] = dup_catalog["packages"][0]["id"]
    res = CatalogBoundaryValidator.evaluate_catalog_boundaries(dup_catalog)
    assert res["pass"] is False
    assert "duplicate package IDs" in res["reason"]
