"""Crawler module for AI-Skills-Registry.

Exports the discovery and crawling engine, seed registry sources, and data models.
"""

from typing import Any

from src.crawler.registry_sources import (
    CATEGORIES,
    CURATED_REGISTRIES,
    SEED_PACKAGES,
    RegistrySources,
    get_curated_registries,
    get_package_by_id,
    get_packages_by_category,
    get_seed_catalog,
    get_seed_packages,
)

__all__ = [
    "CrawlerEngine",
    "CatalogPackageRecord",
    "CrawlStatus",
    "MetadataNormalizer",
    "RegistrySources",
    "SEED_PACKAGES",
    "CURATED_REGISTRIES",
    "CATEGORIES",
    "get_seed_packages",
    "get_package_by_id",
    "get_packages_by_category",
    "get_curated_registries",
    "get_seed_catalog",
]


def __getattr__(name: str) -> Any:
    if name in ("CrawlerEngine", "CatalogPackageRecord", "CrawlStatus", "MetadataNormalizer"):
        from src.crawler import github_crawler
        return getattr(github_crawler, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
