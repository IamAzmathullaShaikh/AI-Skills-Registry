"""GitHub & Registry Crawler Engine for AI-Skills-Registry.

Discovers, fetches, and normalizes AI skill and MCP server metadata
from GitHub, npm, and PyPI registries with robust offline fallback.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure module logger
logger = logging.getLogger("ai_skills_registry.crawler")

# Default Constants
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 2
USER_AGENT = "AI-Skills-Registry-Crawler/1.0 (+https://github.com/BangerSoul/AI-Skills-Registry)"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CrawlStatus:
    """Diagnostic tracking record for an individual package crawl attempt."""

    source: str         # "live_api" | "offline_seed" | "fallback"
    timestamp: str
    warnings: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class CatalogPackageRecord:
    """Standardized metadata record for a discovered AI skill or MCP server."""

    id: str
    name: str
    category: str
    type: str
    description: str
    repo_url: str
    stars: int
    maintainer: str
    capabilities: List[str]
    entrypoint: Dict[str, Any]
    dependencies: Dict[str, Any]
    license: str
    validation_status: str = "verified"
    platform_targets: List[str] = field(default_factory=list)
    security_notes: Dict[str, Any] = field(default_factory=dict)
    crawl_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Resilient Network Client (Pure Standard Library)
# ---------------------------------------------------------------------------

class ResilientHttpClient:
    """Standard-library HTTP client with bounded retries, exponential backoff,

    timeout handling, and total exception containment.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        github_token: Optional[str] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        self._rate_limited_domains: set[str] = set()

    def get_json(
        self,
        url: str,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
        start_time = time.time()
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc

        if domain in self._rate_limited_domains:
            latency = (time.time() - start_time) * 1000
            return None, CrawlStatus(
                source="fallback",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                warnings=[f"Domain {domain} previously encountered rate-limit."],
                latency_ms=latency,
            )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        if "api.github.com" in domain:
            headers["Accept"] = "application/vnd.github.v3+json"
            if self.github_token:
                headers["Authorization"] = f"Bearer {self.github_token}"
        if extra_headers:
            headers.update(extra_headers)

        attempts = 0
        last_error_msg = ""

        while attempts <= self.max_retries:
            attempts += 1
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                ssl_context = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as resp:
                    # Check rate limits
                    remaining = resp.headers.get("X-RateLimit-Remaining")
                    if remaining is not None and remaining == "0":
                        logger.warning("GitHub rate limit reached (0 remaining).")
                        self._rate_limited_domains.add(domain)

                    raw_bytes = resp.read()
                    data = json.loads(raw_bytes.decode("utf-8"))
                    latency = (time.time() - start_time) * 1000
                    return data, CrawlStatus(
                        source="live_api",
                        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        latency_ms=latency,
                    )

            except urllib.error.HTTPError as http_err:
                last_error_msg = f"HTTP {http_err.code}: {http_err.reason}"
                if http_err.code in (403, 429):
                    logger.warning(f"Rate limited on {url}: {last_error_msg}")
                    self._rate_limited_domains.add(domain)
                    break
                elif http_err.code == 404:
                    logger.debug(f"Resource not found (404): {url}")
                    break
                elif http_err.code >= 500:
                    logger.warning(
                        f"Server error {http_err.code} for {url}. "
                        f"Retrying attempt {attempts}/{self.max_retries}..."
                    )
                    time.sleep(0.5 * (2 ** (attempts - 1)))
                else:
                    break

            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionResetError, OSError) as net_err:
                last_error_msg = f"Network exception: {net_err}"
                logger.warning(
                    f"Network error accessing {url}: {net_err}. "
                    f"Retrying attempt {attempts}/{self.max_retries}..."
                )
                time.sleep(0.5 * (2 ** (attempts - 1)))

            except json.JSONDecodeError as json_err:
                last_error_msg = f"JSON decode error: {json_err}"
                logger.error(f"Malformed JSON from {url}: {json_err}")
                break

            except Exception as unhandled:
                last_error_msg = f"Unhandled error: {unhandled}"
                logger.error(f"Unexpected error querying {url}: {unhandled}")
                break

        latency = (time.time() - start_time) * 1000
        return None, CrawlStatus(
            source="fallback",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            warnings=[last_error_msg] if last_error_msg else ["Failed to retrieve live data."],
            latency_ms=latency,
        )


# ---------------------------------------------------------------------------
# Registry Providers (GitHub, npm, PyPI)
# ---------------------------------------------------------------------------

class GitHubProvider:
    """Fetches repository stars, descriptions, and licenses from GitHub API."""

    def __init__(self, http_client: ResilientHttpClient):
        self.client = http_client

    def parse_repo_slug(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """Extracts (owner, repo) from a GitHub repository URL."""
        match = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
        if match:
            owner, repo = match.group(1), match.group(2)
            if repo.endswith(".git"):
                repo = repo[:-4]
            return owner, repo
        return None

    def fetch_repo_metadata(self, owner: str, repo: str) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        return self.client.get_json(url)


class NpmProvider:
    """Fetches npm package metadata, latest version, and license."""

    def __init__(self, http_client: ResilientHttpClient):
        self.client = http_client

    def fetch_package_metadata(self, package_name: str) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
        safe_name = urllib.parse.quote(package_name, safe="@")
        url = f"https://registry.npmjs.org/{safe_name}"
        return self.client.get_json(url)


class PyPiProvider:
    """Fetches PyPI package summary, releases, and license."""

    def __init__(self, http_client: ResilientHttpClient):
        self.client = http_client

    def fetch_package_metadata(self, package_name: str) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
        url = f"https://pypi.org/pypi/{package_name}/json"
        return self.client.get_json(url)


# ---------------------------------------------------------------------------
# Metadata Normalizer
# ---------------------------------------------------------------------------

class MetadataNormalizer:
    """Normalizes disparate registry responses into standardized Draft-07

    CatalogPackageRecord structures.
    """

    LICENSE_MAP = {
        "apache-2.0": "Apache-2.0",
        "apache 2.0": "Apache-2.0",
        "mit": "MIT",
        "mit license": "MIT",
        "bsd-3-clause": "BSD-3-Clause",
        "bsd 3-clause": "BSD-3-Clause",
        "bsd-2-clause": "BSD-2-Clause",
        "isc": "ISC",
        "unlicense": "Unlicense",
        "cc0-1.0": "CC0-1.0",
        "lgpl-2.1": "LGPL-2.1",
    }

    @classmethod
    def normalize_license(cls, raw_license: Any) -> str:
        if not raw_license:
            return "Unknown"
        if isinstance(raw_license, dict):
            raw_license = raw_license.get("spdx_id") or raw_license.get("name") or raw_license.get("type", "")
        clean_license = str(raw_license).strip()
        return cls.LICENSE_MAP.get(clean_license.lower(), clean_license)

    @classmethod
    def merge_package(
        cls,
        seed: Dict[str, Any],
        github_data: Optional[Dict[str, Any]] = None,
        npm_data: Optional[Dict[str, Any]] = None,
        pypi_data: Optional[Dict[str, Any]] = None,
        crawl_status: Optional[CrawlStatus] = None,
    ) -> CatalogPackageRecord:
        """Merges dynamic registry data with curated seed definitions.

        Seed values for entrypoints, capabilities, and platform targets
        take authoritative precedence, while live stars, licenses, and
        descriptions enrich the record when available.
        """
        stars = seed.get("stars", 0)
        description = seed.get("description", "")
        license_str = seed.get("license", "Unknown")
        maintainer = seed.get("maintainer", "Community")

        # Enrich from GitHub
        if github_data:
            if "stargazers_count" in github_data:
                stars = int(github_data["stargazers_count"])
            if github_data.get("description"):
                description = github_data["description"]
            if github_data.get("license") and isinstance(github_data["license"], dict):
                spdx = github_data["license"].get("spdx_id")
                if spdx and spdx != "NOASSERTION":
                    license_str = cls.normalize_license(spdx)
            if github_data.get("owner") and isinstance(github_data["owner"], dict):
                maintainer = github_data["owner"].get("login", maintainer)

        # Enrich from npm
        elif npm_data:
            if npm_data.get("description"):
                description = npm_data["description"]
            if npm_data.get("license"):
                license_str = cls.normalize_license(npm_data["license"])

        # Enrich from PyPI
        elif pypi_data and "info" in pypi_data:
            info = pypi_data["info"]
            if info.get("summary"):
                description = info["summary"]
            if info.get("license"):
                license_str = cls.normalize_license(info["license"])

        status_dict = asdict(crawl_status) if crawl_status else {
            "source": "offline_seed",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "warnings": [],
            "latency_ms": 0.0,
        }

        # Normalize capabilities to list of strings
        raw_caps = seed.get("capabilities", [])
        if isinstance(raw_caps, dict):
            # Extract tool names if dictionary format
            tools = raw_caps.get("tools", [])
            caps_list = [t["name"] if isinstance(t, dict) else str(t) for t in tools]
        elif isinstance(raw_caps, list):
            caps_list = [t["name"] if isinstance(t, dict) else str(t) for t in raw_caps]
        else:
            caps_list = ["execute"]

        # Normalize platform_targets to list of strings
        raw_targets = seed.get("platform_targets", ["antigravity", "claude_code"])
        if isinstance(raw_targets, dict):
            targets_list = [k.replace("google_", "") for k, v in raw_targets.items() if v.get("enabled", True)]
        elif isinstance(raw_targets, list):
            targets_list = [str(t) for t in raw_targets]
        else:
            targets_list = ["antigravity", "claude_code"]

        return CatalogPackageRecord(
            id=seed["id"],
            name=seed.get("name", seed["id"]),
            category=seed["category"],
            type=seed.get("type", "mcp_server"),
            description=description,
            repo_url=seed.get("repo_url", ""),
            stars=stars,
            maintainer=maintainer,
            capabilities=caps_list,
            entrypoint=seed.get("entrypoint", {"command": "", "args": [], "env": {}}),
            dependencies=seed.get("dependencies", {"node": ">=18"}),
            license=license_str,
            validation_status=seed.get("validation_status", "verified"),
            platform_targets=targets_list,
            security_notes=seed.get("security_notes", {
                "filesystem_access": "none",
                "network_access": "none",
                "credentials_required": [],
                "sandbox_safe": True,
            }),
            crawl_metadata=status_dict,
        )


# ---------------------------------------------------------------------------
# Core Crawler Engine
# ---------------------------------------------------------------------------

class CrawlerEngine:
    """Main programmatic orchestrator for registry crawling, metadata normalization,

    and catalog compilation.
    """

    def __init__(
        self,
        offline_mode: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        github_token: Optional[str] = None,
    ):
        self.offline_mode = offline_mode or (os.environ.get("AI_SKILLS_OFFLINE_MODE", "0") in ("1", "true", "yes"))
        self.http_client = ResilientHttpClient(timeout=timeout, max_retries=max_retries, github_token=github_token)
        self.github_provider = GitHubProvider(self.http_client)
        self.npm_provider = NpmProvider(self.http_client)
        self.pypi_provider = PyPiProvider(self.http_client)

    def crawl_package(self, seed: Dict[str, Any]) -> CatalogPackageRecord:
        """Crawls metadata for a single seed package. If offline_mode is True,

        immediately resolves from seed data.
        """
        if self.offline_mode:
            logger.debug(f"Offline mode: using seed metadata for {seed['id']}")
            return MetadataNormalizer.merge_package(
                seed=seed,
                crawl_status=CrawlStatus(
                    source="offline_seed",
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    warnings=[],
                    latency_ms=0.0,
                ),
            )

        repo_url = seed.get("repo_url", "")
        github_data: Optional[Dict[str, Any]] = None
        crawl_status: Optional[CrawlStatus] = None

        # 1. Attempt GitHub crawl if URL points to github.com
        slug = self.github_provider.parse_repo_slug(repo_url)
        if slug:
            owner, repo = slug
            github_data, crawl_status = self.github_provider.fetch_repo_metadata(owner, repo)

        # 2. If GitHub not available or missing, check npm / PyPI
        npm_data = None
        pypi_data = None
        if not github_data:
            deps = seed.get("dependencies", {})
            for runtime_name in ("node", "npm"):
                if runtime_name in deps:
                    npm_data, crawl_status = self.npm_provider.fetch_package_metadata(seed["id"])
                    break
            for runtime_name in ("python", "pip", "uvx"):
                if runtime_name in deps:
                    pypi_data, crawl_status = self.pypi_provider.fetch_package_metadata(seed["id"])
                    break

        # 3. Normalize and merge
        return MetadataNormalizer.merge_package(
            seed=seed,
            github_data=github_data,
            npm_data=npm_data,
            pypi_data=pypi_data,
            crawl_status=crawl_status,
        )

    def crawl_all(self, seed_packages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Iterates across all seed packages, crawls metadata, and constructs

        the master catalog dictionary conforming to Draft-07 schema.
        """
        if seed_packages is None:
            from src.crawler.registry_sources import SEED_PACKAGES
            seed_packages = SEED_PACKAGES

        logger.info(f"Starting catalog crawl for {len(seed_packages)} packages (Offline: {self.offline_mode})...")
        crawled_packages: List[Dict[str, Any]] = []

        # Retain order of categories
        category_order = ["browser_search", "code_intelligence", "data_databases", "system_ops", "media"]
        cats_found = {p["category"] for p in seed_packages}
        categories = [c for c in category_order if c in cats_found]

        for seed in seed_packages:
            try:
                record = self.crawl_package(seed)
                crawled_packages.append(record.to_dict())
                logger.info(f"  [{record.crawl_metadata.get('source', 'unknown')}] {record.id}: {record.stars} stars | {record.license}")
            except Exception as exc:
                logger.error(f"Error processing {seed.get('id', 'unknown')}: {exc}. Using raw seed fallback.")
                fallback_record = MetadataNormalizer.merge_package(seed=seed)
                crawled_packages.append(fallback_record.to_dict())

        catalog = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "version": "1.0.0",
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_packages": len(crawled_packages),
            "categories": categories,
            "packages": crawled_packages,
        }

        return catalog

    def save_catalog(self, catalog: Dict[str, Any], output_path: Union[str, Path]) -> Path:
        """Saves compiled catalog to disk atomically."""
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        temp_file = out.with_suffix(f".tmp.{os.getpid()}")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        temp_file.replace(out)
        logger.info(f"Catalog saved successfully to: {out} ({len(catalog['packages'])} packages)")
        return out


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m src.crawler.github_crawler",
        description="Crawls and indexes AI Skills and MCP Servers into catalog.json",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="catalog.json",
        help="Destination path for catalog.json (default: ./catalog.json)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force offline mode using local seed registry fixtures (no network calls)",
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=["browser_search", "code_intelligence", "data_databases", "system_ops", "media"],
        help="Filter crawl to a specific category",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Network request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub Personal Access Token for authenticated rate limits (or set GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        from src.crawler.registry_sources import SEED_PACKAGES
    except ImportError:
        logger.error("Could not import SEED_PACKAGES from src.crawler.registry_sources. Ensure PYTHONPATH includes project root.")
        return 1

    seeds = SEED_PACKAGES
    if args.category:
        seeds = [p for p in seeds if p.get("category") == args.category]
        logger.info(f"Filtered to category '{args.category}': {len(seeds)} packages.")

    engine = CrawlerEngine(
        offline_mode=args.offline,
        timeout=args.timeout,
        github_token=args.token,
    )

    try:
        catalog = engine.crawl_all(seed_packages=seeds)
        engine.save_catalog(catalog, args.output)

        print("\n========================================================")
        print(" AI-Skills-Registry Crawler Execution Summary")
        print("========================================================")
        print(f" Total Packages Processed: {catalog['total_packages']}")
        print(f" Mode:                     {'OFFLINE (Fixtures)' if engine.offline_mode else 'LIVE / HYBRID'}")
        print(f" Output Location:          {Path(args.output).resolve()}")
        print(f" Categories:               {', '.join(catalog['categories'])}")
        print(" Status:                   SUCCESS (Exit 0)\n")
        return 0
    except Exception as exc:
        logger.critical(f"Fatal error during crawler execution: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
