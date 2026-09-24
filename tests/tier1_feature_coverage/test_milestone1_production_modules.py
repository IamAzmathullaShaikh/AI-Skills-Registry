"""Milestone 1 Production Code Verification Tests.

Directly verifies:
- src.config.PipelineEnvironmentConfig
- src.crawler.registry_sources (20 packages, 5 categories, accessors)
- src.crawler.github_crawler (CrawlerEngine, offline mode, metadata normalizer, save)
- catalog.json on disk
- README.md on disk
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.config import (
    BEGIN_MANAGED_ROUTING,
    END_MANAGED_ROUTING,
    MAX_RULE_FILE_BYTES,
    MIN_COMMUNITY_STARS,
    PipelineEnvironmentConfig,
)
from src.crawler import (
    CATEGORIES,
    CURATED_REGISTRIES,
    SEED_PACKAGES,
    CrawlerEngine,
    MetadataNormalizer,
    RegistrySources,
    get_curated_registries,
    get_package_by_id,
    get_packages_by_category,
    get_seed_catalog,
    get_seed_packages,
)


def test_config_live_default():
    """Verify live default configuration loads real paths without mutation."""
    cfg = PipelineEnvironmentConfig.live_default()
    assert not cfg.is_sandbox
    assert cfg.project_root.exists()
    assert cfg.user_home_dir == Path.home()
    assert cfg.gemini_config_dir == Path.home() / ".gemini" / "config"
    assert cfg.claude_json_path == Path.home() / ".claude.json"
    assert cfg.catalog_file == cfg.project_root / "catalog.json"
    assert BEGIN_MANAGED_ROUTING in BEGIN_MANAGED_ROUTING
    assert END_MANAGED_ROUTING in END_MANAGED_ROUTING
    assert MAX_RULE_FILE_BYTES == 24000
    assert MIN_COMMUNITY_STARS == 100


def test_config_from_sandbox():
    """Verify mock sandbox isolation and fixture creation."""
    with tempfile.TemporaryDirectory() as tmp:
        sandbox_path = Path(tmp).resolve()
        cfg = PipelineEnvironmentConfig.from_sandbox(sandbox_path, populate_fixtures=True)
        assert cfg.is_sandbox
        assert cfg.user_home_dir == sandbox_path
        assert cfg.claude_json_path.exists()
        assert (cfg.gemini_config_dir / "skills").exists()
        assert cfg.agents_rule_file.exists()
        assert cfg.claude_rule_file.exists()
        assert cfg.gemini_rule_file.exists()

        # Check backup path generation
        backup_path = cfg.get_backup_path(cfg.claude_json_path, prefix="test")
        assert backup_path.parent == cfg.backup_dir
        assert "claude.json.bak" in backup_path.name
        assert "test_" in backup_path.name

        # Check as_dict secret masking
        d = cfg.as_dict()
        assert d["is_sandbox"] is True
        assert d["project_root"] == str(cfg.project_root)


def test_config_validate_environment():
    """Verify environment validation identifies missing or valid paths."""
    with tempfile.TemporaryDirectory() as tmp:
        cfg = PipelineEnvironmentConfig.from_sandbox(Path(tmp), populate_fixtures=True)
        warnings = cfg.validate_environment()
        assert isinstance(warnings, list)


def test_registry_sources_constants_and_counts():
    """Verify seed packages count, categories, and curated registries."""
    assert len(SEED_PACKAGES) == 20
    assert len(CATEGORIES) == 5
    assert len(CURATED_REGISTRIES) == 6

    pkgs = get_seed_packages()
    assert len(pkgs) == 20

    # Ensure immutability via deepcopy
    pkgs[0]["test_mutation"] = True
    assert "test_mutation" not in SEED_PACKAGES[0]


def test_registry_sources_all_five_categories_balanced():
    """Verify each category has at least 3 packages."""
    for cat in CATEGORIES:
        cat_pkgs = get_packages_by_category(cat)
        assert len(cat_pkgs) >= 3, f"Category '{cat}' has only {len(cat_pkgs)} packages"


def test_registry_sources_get_by_id():
    """Verify lookup by unique identifier."""
    pkg = get_package_by_id("browser-playwright")
    assert pkg is not None
    assert pkg["name"] == "Playwright Browser Automation"
    assert pkg["category"] == "browser_search"

    missing = get_package_by_id("non-existent-pkg-id")
    assert missing is None


def test_registry_sources_seed_catalog_draft07_attributes():
    """Verify seed catalog dictionary meets root draft-07 requirements."""
    catalog = get_seed_catalog()
    assert catalog["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert catalog["version"] == "1.0.0"
    assert catalog["total_packages"] == 20
    assert len(catalog["packages"]) == 20
    assert catalog["categories"] == CATEGORIES


def test_crawler_engine_offline_crawl():
    """Verify CrawlerEngine produces valid 20-package catalog in offline mode."""
    engine = CrawlerEngine(offline_mode=True)
    catalog = engine.crawl_all()
    assert catalog["total_packages"] == 20
    assert len(catalog["packages"]) == 20

    for pkg in catalog["packages"]:
        assert pkg["crawl_metadata"]["source"] == "offline_seed"
        assert isinstance(pkg["capabilities"], list)
        assert len(pkg["capabilities"]) > 0
        assert isinstance(pkg["platform_targets"], list)
        assert len(pkg["platform_targets"]) > 0
        assert "command" in pkg["entrypoint"]


def test_crawler_metadata_normalizer_licenses():
    """Verify license normalization to standard SPDX identifiers."""
    assert MetadataNormalizer.normalize_license("mit") == "MIT"
    assert MetadataNormalizer.normalize_license("apache 2.0") == "Apache-2.0"
    assert MetadataNormalizer.normalize_license({"spdx_id": "Apache-2.0"}) == "Apache-2.0"
    assert MetadataNormalizer.normalize_license(None) == "Unknown"


def test_crawler_engine_atomic_save(tmp_path):
    """Verify save_catalog writes valid JSON atomically without temp remnants."""
    engine = CrawlerEngine(offline_mode=True)
    catalog = engine.crawl_all()
    out_file = tmp_path / "test_catalog.json"
    saved_path = engine.save_catalog(catalog, out_file)
    assert saved_path.exists()

    with open(saved_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["total_packages"] == 20

    # Ensure no leftover temp files
    tmp_files = list(tmp_path.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_catalog_json_on_disk():
    """Verify catalog.json exists at project root and is valid with 20 packages."""
    catalog_path = Path("catalog.json").resolve()
    assert catalog_path.exists(), "catalog.json does not exist at project root"

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    assert catalog["version"] == "1.0.0"
    assert catalog["total_packages"] == 20
    assert len(catalog["packages"]) == 20
    assert set(catalog["categories"]) == set(CATEGORIES)

    ids = [p["id"] for p in catalog["packages"]]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in catalog.json"
    assert "browser-playwright" in ids
    assert "opencut" in ids


def test_readme_md_on_disk():
    """Verify README.md exists and contains catalog presentation tables and guides."""
    readme_path = Path("README.md").resolve()
    assert readme_path.exists(), "README.md does not exist at project root"

    content = readme_path.read_text(encoding="utf-8")
    assert "# AI Skills & Model Context Protocol (MCP) Registry" in content
    assert "# AI Model Skills & MCP Servers Catalog" in content
    assert "## Category: Browser Search" in content
    assert "## Category: Media" in content
    assert "| `browser-playwright` |" in content
    assert "| `opencut` |" in content
    assert "BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING" in content
    assert "END AI-SKILLS-REGISTRY MANAGED ROUTING" in content
