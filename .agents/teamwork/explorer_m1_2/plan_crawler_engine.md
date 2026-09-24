# Implementation Plan: GitHub & Registry Crawler Engine (`src/crawler/github_crawler.py`)

**Document Version**: 1.0.0  
**Author**: `explorer_m1_2` (Teamwork Explorer)  
**Parent Orchestrator**: `orchestrator_1` (Conv ID: `40a6594f-8daa-4f4a-b75e-76633ee5c4c9`)  
**Project**: AI-Skills-Registry (`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry`)  
**Milestone**: Milestone 1: Discovery & Catalog Indexing Engine  
**Target Code File**: `src/crawler/github_crawler.py`

---

## 1. Executive Summary & Component Blueprint

The **GitHub & Registry Crawler Engine** is the foundational discovery and metadata aggregation subsystem of the AI-Skills-Registry pipeline. Its primary mandate is to ingest candidate skill and Model Context Protocol (MCP) server definitions, fetch live repository and package metadata from external authoritative registries (GitHub REST API, npm Registry API, PyPI JSON API), normalize disparate metadata formats into a unified Draft-07 Catalog Package record, and output a validated master catalog (`catalog.json`).

### Key Design Pillars
1. **Multi-Source Fetching**: Concurrent or sequential querying of GitHub repositories, npm packages, and PyPI modules.
2. **Offline-First & Zero-Unhandled-Exception Contract**: Seamless operation in airgapped, rate-limited, or testing environments. Network errors (`URLError`, `HTTPError`, `TimeoutError`, SSL faults, DNS resolution failures) are trapped 100% defensively and trigger automatic fallback to curated seed fixtures (`src.crawler.registry_sources.SEED_PACKAGES`) without crashing.
3. **Standard-Library Core**: Built using Python's native `urllib.request`, `json`, `dataclasses`, and `re` modules, ensuring zero mandatory third-party network dependencies.
4. **Clean Interface Contracts**: Directly satisfies the **M1 ↔ M2 contract** documented in `PROJECT.md`, supplying clean, schema-compliant records for the Quality & Schema Validator (`src/validator/`).
5. **Dual Interface**: Supports both programmatic invocation (`from src.crawler.github_crawler import CrawlerEngine`) and CLI execution (`python -m src.crawler.github_crawler --offline --output catalog.json`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   GitHub & Registry Crawler Engine                     │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[GitHub REST API v3]       [npm Registry API]             [PyPI JSON API]
GET /repos/{owner}/{repo}   GET /{package}                 GET /{package}/json
(stars, description,        (latest version, license,     (summary, releases,
 license, releases)          dependencies, deprecation)     classifiers, yanked)
    │                               │                               │
    └───────────────────────┬───────┴───────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │  Network Client & Guard   │
              │  - Exponential Backoff    │
              │  - Rate-Limit Detector    │
              │  - 100% Exception Contain │
              └─────────────┬─────────────┘
                            │ (On failure / --offline)
                            ▼
              ┌───────────────────────────┐
              │ Offline Fallback Manager  │◄─── [SEED_PACKAGES / Fixtures]
              │ (Curated Seed Metadata)   │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │    Metadata Normalizer    │
              │  - Draft-07 Schema Map    │
              │  - License SPDX Resolver  │
              │  - Platform Target Bind   │
              └─────────────┬─────────────┘
                            │
                            ▼
                 [ Master catalog.json ]
```

---

## 2. Remote Registry Protocols & Endpoint Specifications

### 2.1 GitHub REST API v3
* **Base URL**: `https://api.github.com`
* **Endpoints**:
  1. **Repository Details**: `GET /repos/{owner}/{repo}`
     - Extracts: `stargazers_count`, `description`, `license.spdx_id`, `archived`, `disabled`, `pushed_at`, `default_branch`, `topics`.
  2. **Latest Release**: `GET /repos/{owner}/{repo}/releases/latest`
     - Extracts: `tag_name`, `published_at`, `html_url`.
* **Headers**:
  ```http
  User-Agent: AI-Skills-Registry-Crawler/1.0 (+https://github.com/BangerSoul/AI-Skills-Registry)
  Accept: application/vnd.github.v3+json
  Authorization: Bearer <GITHUB_TOKEN>   [Optional: increases limit from 60 to 5,000 req/hr]
  ```
* **Rate Limit Handling**:
  - Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
  - When `X-RateLimit-Remaining == "0"` or HTTP 403 received with message containing `"API rate limit exceeded"`, immediately activate `OfflineFallbackManager` for remaining GitHub requests.

### 2.2 npm Registry API
* **Base URL**: `https://registry.npmjs.org`
* **Endpoint**: `GET /{package}` (e.g. `GET /@playwright/mcp` or `GET /@modelcontextprotocol%2Fserver-filesystem`)
* **Headers**:
  ```http
  User-Agent: AI-Skills-Registry-Crawler/1.0
  Accept: application/json
  ```
* **Extracts**:
  - `dist-tags.latest`: Latest released semver string.
  - `versions[<latest>].deprecated`: Deprecation status and advisory string.
  - `versions[<latest>].license`: SPDX license identifier.
  - `versions[<latest>].dependencies`: Node runtime dependency map.
  - `description`: Canonical package description.

### 2.3 PyPI JSON API
* **Base URL**: `https://pypi.org/pypi`
* **Endpoint**: `GET /{package}/json` (e.g. `GET /mcp-server-git/json`)
* **Headers**:
  ```http
  User-Agent: AI-Skills-Registry-Crawler/1.0
  Accept: application/json
  ```
* **Extracts**:
  - `info.version`: Latest stable release version.
  - `info.summary`: Package summary.
  - `info.license`: License declaration string.
  - `info.yanked`: Boolean indicating whether package version was revoked.
  - `info.classifiers`: Trove classifiers (development status, license).
  - `info.requires_dist`: Python package dependency specifications.

---

## 3. Robust Network Subsystem & Zero-Unhandled-Exception Contract

### 3.1 Network Exception Containment Hierarchy
Every external request executed by the crawler must be intercepted defensively. No uncaught network exception is permitted to crash the process or bubble up to the CLI.

```python
# Exception Handling Taxonomy
try:
    response_data = self._make_request(url, headers)
except urllib.error.HTTPError as http_err:
    if http_err.code in (403, 429):
        logger.warning(f"Rate limited on {url}: HTTP {http_err.code}. Switching to offline fallback.")
    elif http_err.code == 404:
        logger.warning(f"Endpoint not found: {url}. Using seed metadata.")
    else:
        logger.warning(f"HTTP Error {http_err.code} for {url}: {http_err.reason}")
    return None
except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionResetError, OSError) as net_err:
    logger.warning(f"Network error accessing {url}: {net_err}. Switching to offline fallback.")
    return None
except json.JSONDecodeError as json_err:
    logger.warning(f"Failed to parse JSON response from {url}: {json_err}.")
    return None
except Exception as unexpected:
    logger.error(f"Unexpected exception crawling {url}: {unexpected}")
    return None
```

### 3.2 Exponential Backoff Retry Strategy
For transient network glitches (HTTP 500, 502, 503, 504, connection reset), the client executes a bounded retry loop:
* **Max Attempts**: 3
* **Base Delay**: 1.0 second
* **Multiplier**: 2.0 (1s -> 2s -> 4s)
* **Jitter**: $\pm 0.2$ seconds uniform randomness to avoid thundering herds.
* **Non-Retryable Errors**: HTTP 404 (Not Found), HTTP 401 (Unauthorized), HTTP 403 (Rate Limit Exceeded), `offline_mode == True`.

### 3.3 Offline Fixture Fallback Subsystem
The crawler supports two primary operating states:
1. **Explicit Offline Mode (`--offline` or `AI_SKILLS_OFFLINE_MODE=1`)**:
   - Skips all network socket calls completely.
   - Instantly resolves package data from `src.crawler.registry_sources.SEED_PACKAGES` (or an optional JSON fixture path).
   - Marks each package record with `"crawl_metadata": {"source": "offline_fixture", "status": "cached"}`.
2. **Dynamic Live-with-Fallback Mode (Default)**:
   - Attempts live remote queries for GitHub stars, releases, and licenses.
   - If a request fails or times out, the engine immediately substitutes the curated baseline values from `SEED_PACKAGES`.
   - Never raises an unhandled exception; instead marks `"crawl_metadata": {"source": "seed_fallback", "status": "fallback"}`.

---

## 4. Metadata Normalization into Draft-07 Catalog Records

The output of `CrawlerEngine` strictly conforms to the **M1 ↔ M2 interface contract** defined in `PROJECT.md` Section 84–114.

### 4.1 Schema Mapping Rules

| Catalog Attribute | GitHub API Source | npm API Source | PyPI API Source | Fallback / Seed Source |
| :--- | :--- | :--- | :--- | :--- |
| `id` | - | - | - | `seed["id"]` (e.g. `browser-playwright`) |
| `name` | `name` or `seed["name"]` | `name` | `info.name` | `seed["name"]` |
| `category` | Verified category enum | Verified category enum | Verified category enum | `seed["category"]` |
| `type` | - | - | - | `seed["type"]` (`mcp_server`, `antigravity_skill`, `hybrid`) |
| `description` | `description` | `description` | `info.summary` | `seed["description"]` |
| `repo_url` | `html_url` | `repository.url` | `info.project_urls["Source"]` | `seed["repo_url"]` |
| `stars` | `stargazers_count` | Est. from GitHub repo | Est. from GitHub repo | `seed["stars"]` |
| `maintainer` | `owner.login` | `author.name` | `info.author` | `seed["maintainer"]` |
| `capabilities` | - | - | - | `seed["capabilities"]` (tools, resources, prompts) |
| `entrypoint` | - | Inferred / Seed | Inferred / Seed | `seed["entrypoint"]` (`command`, `args`, `env`, `transport`) |
| `dependencies` | Language / runtime detection | `dependencies` | `requires_dist` | `seed["dependencies"]` |
| `license` | `license.spdx_id` | `license` string | `info.license` | `seed["license"]` (SPDX identifier) |
| `validation_status` | Initialized as `"pending"` | Initialized as `"pending"` | Initialized as `"pending"` | `"pending"` |
| `platform_targets` | - | - | - | `seed["platform_targets"]` |
| `security_notes` | - | - | - | `seed["security_notes"]` |

### 4.2 License Normalization
License strings returned by registries vary wildly (e.g., `Apache 2.0`, `Apache-2.0`, `MIT License`, `{"type": "MIT"}`). The `MetadataNormalizer` maps them to standard SPDX identifiers:
```python
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
}
```

---

## 5. Detailed Source Code Architecture (`src/crawler/github_crawler.py`)

Below is the concrete, production-grade Python design for `src/crawler/github_crawler.py`.

```python
"""
GitHub & Registry Crawler Engine for AI-Skills-Registry.
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
    source: str         # "live_api" | "offline_seed" | "fallback"
    timestamp: str
    warnings: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class CapabilitiesRecord:
    tools: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    prompts: List[str] = field(default_factory=list)


@dataclass
class EntrypointRecord:
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"


@dataclass
class DependenciesRecord:
    runtime: str
    package_manager: str
    packages: List[str] = field(default_factory=list)
    system_binaries: List[str] = field(default_factory=list)


@dataclass
class CatalogPackageRecord:
    id: str
    name: str
    category: str
    type: str
    description: str
    repo_url: str
    stars: int
    maintainer: str
    capabilities: Dict[str, Any]
    entrypoint: Dict[str, Any]
    dependencies: Dict[str, Any]
    license: str
    validation_status: str = "pending"
    platform_targets: Dict[str, Any] = field(default_factory=dict)
    security_notes: Dict[str, Any] = field(default_factory=dict)
    crawl_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Resilient Network Client (Pure Standard Library)
# ---------------------------------------------------------------------------

class ResilientHttpClient:
    """
    Standard-library HTTP client with bounded retries, exponential backoff,
    timeout handling, and total exception containment.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        github_token: Optional[str] = None
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self._rate_limited_domains: set[str] = set()

    def get_json(self, url: str, extra_headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
        start_time = time.time()
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc

        if domain in self._rate_limited_domains:
            latency = (time.time() - start_time) * 1000
            return None, CrawlStatus(
                source="fallback",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                warnings=[f"Domain {domain} previously encountered rate-limit."],
                latency_ms=latency
            )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
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
                # Context with standard SSL verification
                ssl_context = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as resp:
                    # Check rate limits
                    remaining = resp.headers.get("X-RateLimit-Remaining")
                    if remaining is not None and remaining == "0":
                        logger.warning(f"GitHub rate limit reached (0 remaining).")
                        self._rate_limited_domains.add(domain)

                    content_type = resp.headers.get("Content-Type", "")
                    raw_bytes = resp.read()
                    data = json.loads(raw_bytes.decode("utf-8"))
                    latency = (time.time() - start_time) * 1000
                    return data, CrawlStatus(
                        source="live_api",
                        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        latency_ms=latency
                    )

            except urllib.error.HTTPError as http_err:
                last_error_msg = f"HTTP {http_err.code}: {http_err.reason}"
                if http_err.code in (403, 429):
                    logger.warning(f"Rate limited on {url}: {last_error_msg}")
                    self._rate_limited_domains.add(domain)
                    break  # Do not retry rate limit errors
                elif http_err.code == 404:
                    logger.debug(f"Resource not found (404): {url}")
                    break  # Do not retry 404
                elif http_err.code >= 500:
                    logger.warning(f"Server error {http_err.code} for {url}. Retrying attempt {attempts}/{self.max_retries}...")
                    time.sleep(1.0 * (2 ** (attempts - 1)))
                else:
                    break

            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionResetError, OSError) as net_err:
                last_error_msg = f"Network exception: {net_err}"
                logger.warning(f"Network error accessing {url}: {net_err}. Retrying attempt {attempts}/{self.max_retries}...")
                time.sleep(1.0 * (2 ** (attempts - 1)))

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
            latency_ms=latency
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
        # Handle scoped packages: @modelcontextprotocol/server-filesystem -> @modelcontextprotocol%2Fserver-filesystem
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
    """
    Normalizes disparate registry responses into standardized Draft-07
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
        crawl_status: Optional[CrawlStatus] = None
    ) -> CatalogPackageRecord:
        """
        Merges dynamic registry data with curated seed definitions.
        Seed values for entrypoints, capabilities, and platform targets
        take authoritative precedence, while live stars, licenses, and
        descriptions enrich the record.
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
                license_str = cls.normalize_license(github_data["license"].get("spdx_id"))
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
            "latency_ms": 0.0
        }

        return CatalogPackageRecord(
            id=seed["id"],
            name=seed.get("name", seed["id"]),
            category=seed["category"],
            type=seed.get("type", "mcp_server"),
            description=description,
            repo_url=seed.get("repo_url", ""),
            stars=stars,
            maintainer=maintainer,
            capabilities=seed.get("capabilities", {"tools": [], "resources": [], "prompts": []}),
            entrypoint=seed.get("entrypoint", {"command": "", "args": [], "env": {}, "transport": "stdio"}),
            dependencies=seed.get("dependencies", {"runtime": "node", "package_manager": "npm"}),
            license=license_str,
            validation_status="pending",
            platform_targets=seed.get("platform_targets", {}),
            security_notes=seed.get("security_notes", {}),
            crawl_metadata=status_dict
        )


# ---------------------------------------------------------------------------
# Core Crawler Engine
# ---------------------------------------------------------------------------

class CrawlerEngine:
    """
    Main programmatic orchestrator for registry crawling, metadata normalization,
    and catalog compilation.
    """

    def __init__(
        self,
        offline_mode: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        github_token: Optional[str] = None
    ):
        self.offline_mode = offline_mode or (os.environ.get("AI_SKILLS_OFFLINE_MODE", "0") in ("1", "true", "yes"))
        self.http_client = ResilientHttpClient(timeout=timeout, max_retries=max_retries, github_token=github_token)
        self.github_provider = GitHubProvider(self.http_client)
        self.npm_provider = NpmProvider(self.http_client)
        self.pypi_provider = PyPiProvider(self.http_client)

    def crawl_package(self, seed: Dict[str, Any]) -> CatalogPackageRecord:
        """
        Crawls metadata for a single seed package. If offline_mode is True,
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
                    latency_ms=0.0
                )
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
            pkg_mgr = deps.get("package_manager", "")
            packages = deps.get("packages", [])
            if packages:
                pkg_name = packages[0].split("@")[0] if "@" in packages[0] and not packages[0].startswith("@") else packages[0]
                if pkg_mgr == "npm":
                    npm_data, crawl_status = self.npm_provider.fetch_package_metadata(pkg_name)
                elif pkg_mgr in ("pip", "uvx"):
                    pypi_data, crawl_status = self.pypi_provider.fetch_package_metadata(pkg_name)

        # 3. Normalize and merge
        return MetadataNormalizer.merge_package(
            seed=seed,
            github_data=github_data,
            npm_data=npm_data,
            pypi_data=pypi_data,
            crawl_status=crawl_status
        )

    def crawl_all(self, seed_packages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Iterates across all seed packages, crawls metadata, and constructs
        the master catalog dictionary conforming to Draft-07 schema.
        """
        if seed_packages is None:
            # Dynamically import seed packages from registry_sources
            from src.crawler.registry_sources import SEED_PACKAGES
            seed_packages = SEED_PACKAGES

        logger.info(f"Starting catalog crawl for {len(seed_packages)} packages (Offline: {self.offline_mode})...")
        crawled_packages: List[Dict[str, Any]] = []

        categories = sorted(list({p["category"] for p in seed_packages}))

        for seed in seed_packages:
            try:
                record = self.crawl_package(seed)
                crawled_packages.append(record.to_dict())
                logger.info(f"  [{record.crawl_metadata.get('source', 'unknown')}] {record.id}: {record.stars} stars | {record.license}")
            except Exception as exc:
                # Absolute guarantee: no crash
                logger.error(f"Error processing {seed.get('id', 'unknown')}: {exc}. Using raw seed fallback.")
                fallback_record = MetadataNormalizer.merge_package(seed=seed)
                crawled_packages.append(fallback_record.to_dict())

        catalog = {
            "version": "1.0.0",
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_packages": len(crawled_packages),
            "categories": categories,
            "packages": crawled_packages
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
        description="Crawls and indexes AI Skills and MCP Servers into catalog.json"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="catalog.json",
        help="Destination path for catalog.json (default: ./catalog.json)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force offline mode using local seed registry fixtures (no network calls)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=["browser_search", "code_intelligence", "data_databases", "system_ops", "media"],
        help="Filter crawl to a specific category"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Network request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub Personal Access Token for authenticated rate limits (or set GITHUB_TOKEN)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
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
        github_token=args.token
    )

    try:
        catalog = engine.crawl_all(seed_packages=seeds)
        engine.save_catalog(catalog, args.output)
        
        # Summary output
        print(f"\n========================================================")
        print(f" AI-Skills-Registry Crawler Execution Summary")
        print(f"========================================================")
        print(f" Total Packages Processed: {catalog['total_packages']}")
        print(f" Mode:                     {'OFFLINE (Fixtures)' if engine.offline_mode else 'LIVE / HYBRID'}")
        print(f" Output Location:          {Path(args.output).resolve()}")
        print(f" Categories:               {', '.join(catalog['categories'])}")
        print(f" Status:                   SUCCESS (Exit 0)\n")
        return 0
    except Exception as exc:
        logger.critical(f"Fatal error during crawler execution: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. Programmatic API Specification

The crawler engine exposes a clean, intuitive Python API designed for seamless integration with testing suites and the higher-level pipeline orchestrator.

### 6.1 Basic In-Memory Crawl
```python
from src.crawler.github_crawler import CrawlerEngine

# Initialize with offline safety (recommended for test fixtures)
engine = CrawlerEngine(offline_mode=True)
catalog = engine.crawl_all()

print(f"Indexed {catalog['total_packages']} packages.")
for pkg in catalog["packages"]:
    print(f" - {pkg['id']} ({pkg['category']}): {pkg['stars']} stars")
```

### 6.2 Live Crawl with Custom GitHub Token and Target Path
```python
import os
from pathlib import Path
from src.crawler.github_crawler import CrawlerEngine

engine = CrawlerEngine(
    offline_mode=False,
    timeout=8.0,
    max_retries=2,
    github_token=os.environ.get("GITHUB_TOKEN")
)

# Crawl all packages and save directly to sandbox target
target_file = Path("./sandbox/catalog.json")
catalog = engine.crawl_all()
engine.save_catalog(catalog, target_file)
```

### 6.3 Isolated Single-Package Inspection
```python
from src.crawler.github_crawler import CrawlerEngine

engine = CrawlerEngine(offline_mode=True)
sample_seed = {
    "id": "data-sqlite",
    "name": "SQLite Database Engine",
    "category": "data_databases",
    "type": "mcp_server",
    "repo_url": "https://github.com/modelcontextprotocol/servers",
    "stars": 30000,
    "license": "MIT"
}

record = engine.crawl_package(sample_seed)
assert record.id == "data-sqlite"
assert record.validation_status == "pending"
assert record.license == "MIT"
```

---

## 7. Command-Line Interface (CLI) Specification

### 7.1 CLI Invocation Patterns

```bash
# 1. Standard Crawl (Defaults to live with automatic fallback to seed on network error)
python -m src.crawler.github_crawler --output catalog.json

# 2. Guaranteed Offline Crawl (Zero network calls; ideal for CI and airgapped environments)
python -m src.crawler.github_crawler --offline --output catalog.json

# 3. Filter by Specific Domain Category
python -m src.crawler.github_crawler --offline --category browser_search --output browser_catalog.json

# 4. Verbose Logging Mode with Custom Timeout
python -m src.crawler.github_crawler --verbose --timeout 15.0 --output catalog.json

# 5. Authenticated GitHub Rate Limit Mode
python -m src.crawler.github_crawler --token ghp_yourSecretTokenHere --output catalog.json
```

### 7.2 CLI Output Formatting Example
```text
14:02:10 [INFO] ai_skills_registry.crawler: Starting catalog crawl for 20 packages (Offline: True)...
14:02:10 [INFO] ai_skills_registry.crawler:   [offline_seed] browser-playwright: 36000 stars | Apache-2.0
14:02:10 [INFO] ai_skills_registry.crawler:   [offline_seed] browser-puppeteer: 30500 stars | MIT
14:02:10 [INFO] ai_skills_registry.crawler:   [offline_seed] browser-fetch: 30000 stars | MIT
14:02:10 [INFO] ai_skills_registry.crawler:   [offline_seed] browser-brave-search: 30000 stars | MIT
...
14:02:10 [INFO] ai_skills_registry.crawler: Catalog saved successfully to: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json (20 packages)

========================================================
 AI-Skills-Registry Crawler Execution Summary
========================================================
 Total Packages Processed: 20
 Mode:                     OFFLINE (Fixtures)
 Output Location:          C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json
 Categories:               browser_search, code_intelligence, data_databases, media, system_ops
 Status:                   SUCCESS (Exit 0)
```

---

## 8. Interface Verification & Test Plan

To support **Feature 1 & Feature 2** and parallel E2E test tracks, the crawler module is designed with testability hooks across all test tiers.

### 8.1 Unit & Component Tests (`tests/tier1_feature_coverage/test_crawler_unit.py`)
1. **`test_github_slug_parsing`**:
   - Asserts URLs (`https://github.com/microsoft/playwright-mcp`, `https://github.com/owner/repo.git`, `https://github.com/owner/repo/tree/main`) resolve correctly to `(owner, repo)`.
2. **`test_license_normalization`**:
   - Asserts variations (`"Apache 2.0"`, `"apache-2.0"`, `"MIT License"`, `{"spdx_id": "MIT"}`) normalize to standard SPDX IDs.
3. **`test_offline_mode_zero_network`**:
   - Injects a dummy non-resolvable URL (`http://invalid-non-existent-domain-12345.org`).
   - Executes with `offline_mode=True`.
   - Asserts no socket connection is attempted and execution completes with status `"offline_seed"`.
4. **`test_catalog_structure_conformance`**:
   - Runs `crawl_all(seed_packages)`.
   - Verifies all required Draft-07 root keys (`version`, `last_updated`, `total_packages`, `categories`, `packages`) and package keys (`id`, `name`, `category`, `stars`, `entrypoint`, `capabilities`, `dependencies`, `license`, `validation_status`) exist.

### 8.2 Boundary & Fault Injection Tests (`tests/tier2_boundary_corner/test_crawler_faults.py`)
1. **`test_rate_limit_graceful_fallback`**:
   - Mocks `urllib.request.urlopen` returning HTTP 403 with `X-RateLimit-Remaining: 0`.
   - Asserts the crawler does not throw an exception and smoothly returns seed fallback metadata.
2. **`test_socket_timeout_containment`**:
   - Mocks `urlopen` raising `socket.timeout`.
   - Asserts the client retries up to `max_retries` and then falls back cleanly.
3. **`test_malformed_json_containment`**:
   - Mocks `urlopen` returning bytes `b"{invalid json"`.
   - Asserts `JSONDecodeError` is caught and logged, yielding fallback metadata.
4. **`test_corrupted_seed_handling`**:
   - Supplies a seed dictionary with missing optional fields.
   - Asserts `MetadataNormalizer` supplies defensive default values.

### 8.3 CLI Dry-Run Tests (`tests/tier1_feature_coverage/test_crawler_cli.py`)
1. **`test_cli_offline_invocation`**:
   - Executes `subprocess.run([sys.executable, "-m", "src.crawler.github_crawler", "--offline", "--output", str(tmp_path / "catalog.json")])`.
   - Asserts return code is `0`.
   - Asserts `tmp_path / "catalog.json"` exists and parses as valid JSON with 20 packages.

---

## 9. Alignment & Dependencies with Peer Explorers

* **`explorer_m1_1` (`src/config.py` & `src/crawler/registry_sources.py`)**:
  - `github_crawler.py` imports `SEED_PACKAGES` from `src.crawler.registry_sources`.
  - When `explorer_m1_1` completes `registry_sources.py`, all 20 verified seed package definitions will be immediately crawlable.
  - `github_crawler.py` reads `AI_SKILLS_OFFLINE_MODE`, `AI_SKILLS_SANDBOX_DIR`, and `GITHUB_TOKEN` from the environment or from `PipelineEnvironmentConfig`.
* **`explorer_m1_3` (`catalog.json` & `README.md`)**:
  - `catalog.json` output produced by `CrawlerEngine.save_catalog()` matches the exact Draft-07 JSON schema and attribute names planned by `explorer_m1_3`.
  - README documentation will document the CLI commands specified in Section 7.
* **`test_writer_e2e_1` (`tests/`)**:
  - Test suites can safely invoke `CrawlerEngine(offline_mode=True)` or mock `ResilientHttpClient` with zero external network connectivity.

---

## 10. Summary Checklist for Implementers

- [ ] Place code in `src/crawler/github_crawler.py`.
- [ ] Keep imports strictly within standard library (`urllib.request`, `json`, `dataclasses`, `argparse`, `logging`, `re`, `pathlib`).
- [ ] Ensure `SEED_PACKAGES` import from `src.crawler.registry_sources` is lazy or clean with a friendly error if run standalone.
- [ ] Verify that `--offline` flag and `AI_SKILLS_OFFLINE_MODE` environment variable work equivalently.
- [ ] Ensure `save_catalog` utilizes an atomic write (`.tmp` file followed by `replace`).
- [ ] Confirm exit code is strictly `0` on successful crawl.
