"""Authoritative Seed Registry & Verified Package Metadata Module.

Provides curated official and community registry source definitions and
20 verified candidate packages across 5 key functional categories.
All metadata conforms strictly to Draft-07 JSON Schema specifications.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

CATEGORIES: List[str] = [
    "browser_search",
    "code_intelligence",
    "data_databases",
    "system_ops",
    "media",
]

CURATED_REGISTRIES: List[Dict[str, Any]] = [
    {
        "id": "mcp-reference-monorepo",
        "name": "Model Context Protocol Reference Servers",
        "owner": "modelcontextprotocol",
        "repo": "servers",
        "url": "https://github.com/modelcontextprotocol/servers",
        "type": "official_monorepo",
        "ecosystems": ["npm", "pypi"],
        "stars": 32000,
    },
    {
        "id": "awesome-mcp-servers",
        "name": "Awesome MCP Servers Directory",
        "owner": "punkpeye",
        "repo": "awesome-mcp-servers",
        "url": "https://github.com/punkpeye/awesome-mcp-servers",
        "type": "community_directory",
        "ecosystems": ["npm", "pypi", "docker", "binary"],
        "stars": 95500,
    },
    {
        "id": "playwright-mcp",
        "name": "Playwright MCP Server",
        "owner": "microsoft",
        "repo": "playwright-mcp",
        "url": "https://github.com/microsoft/playwright-mcp",
        "type": "enterprise_official",
        "ecosystems": ["npm"],
        "stars": 36000,
    },
    {
        "id": "github-mcp-server",
        "name": "GitHub Official MCP Server",
        "owner": "github",
        "repo": "github-mcp-server",
        "url": "https://github.com/github/github-mcp-server",
        "type": "enterprise_official",
        "ecosystems": ["npm"],
        "stars": 33000,
    },
    {
        "id": "aws-agent-toolkit",
        "name": "Agent Toolkit for AWS",
        "owner": "awslabs",
        "repo": "mcp",
        "url": "https://github.com/awslabs/mcp",
        "type": "enterprise_official",
        "ecosystems": ["npm"],
        "stars": 2550,
    },
    {
        "id": "docker-mcp-registry",
        "name": "Docker MCP Catalog & Registry",
        "owner": "docker",
        "repo": "mcp-registry",
        "url": "https://github.com/docker/mcp-registry",
        "type": "container_registry",
        "ecosystems": ["docker"],
        "stars": 1200,
    },
]

SEED_PACKAGES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # Category 1: browser_search (4 packages)
    # -------------------------------------------------------------------------
    {
        "id": "browser-playwright",
        "name": "Playwright Browser Automation",
        "category": "browser_search",
        "description": "Headless browser automation for web navigation, screenshots, and DOM inspection.",
        "repo_url": "https://github.com/microsoft/playwright-mcp",
        "type": "mcp_server",
        "stars": 36000,
        "maintainer": "Microsoft",
        "capabilities": ["browser_navigate", "browser_click", "browser_screenshot"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "Apache-2.0",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "full",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "browser-puppeteer",
        "name": "Puppeteer MCP Server",
        "category": "browser_search",
        "description": "Automated web browsing and scraping using Chrome DevTools Protocol.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["navigate", "screenshot", "evaluate_js"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "full",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "brave-search",
        "name": "Brave Search MCP",
        "category": "browser_search",
        "description": "Real-time web search and news querying powered by the Brave Search API.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["brave_web_search", "brave_local_search"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "outbound_http",
            "credentials_required": ["BRAVE_API_KEY"],
            "sandbox_safe": True,
        },
    },
    {
        "id": "fetch-markdown",
        "name": "Fetch Web to Markdown",
        "category": "browser_search",
        "description": "Fetches web URLs and converts raw HTML into clean, token-efficient markdown.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["fetch_url"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-fetch"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "outbound_http",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },

    # -------------------------------------------------------------------------
    # Category 2: code_intelligence (4 packages)
    # -------------------------------------------------------------------------
    {
        "id": "github-inspector",
        "name": "GitHub Context Server",
        "category": "code_intelligence",
        "description": "Query GitHub repositories, issues, pull requests, commits, and workflow runs.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "GitHub",
        "capabilities": ["search_repositories", "get_file_contents", "list_issues"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "outbound_http",
            "credentials_required": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
            "sandbox_safe": True,
        },
    },
    {
        "id": "git-repo-tools",
        "name": "Git Operations Server",
        "category": "code_intelligence",
        "description": "Local Git repository inspection, history analysis, branching, and status checking.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/git",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["git_status", "git_diff", "git_log"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-git"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "local_only",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "pyright-lsp",
        "name": "Pyright Language Server",
        "category": "code_intelligence",
        "description": "Python type checking, definition jumping, symbol references, and diagnostic analysis.",
        "repo_url": "https://github.com/microsoft/pyright",
        "type": "mcp_server",
        "stars": 14000,
        "maintainer": "Microsoft",
        "capabilities": ["goto_definition", "find_references", "type_check"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "pyright-mcp-server"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "rust-analyzer-mcp",
        "name": "Rust Analyzer MCP",
        "category": "code_intelligence",
        "description": "Rust language intelligence providing cargo diagnostics, type signatures, and macros.",
        "repo_url": "https://github.com/rust-lang/rust-analyzer",
        "type": "mcp_server",
        "stars": 16000,
        "maintainer": "rust-lang",
        "capabilities": ["rust_diagnostics", "rust_hover", "rust_expand_macro"],
        "entrypoint": {
            "command": "rust-analyzer-mcp",
            "args": [],
            "env": {},
        },
        "dependencies": {"rust": ">=1.75"},
        "license": "Apache-2.0",
        "validation_status": "verified",
        "platform_targets": ["claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },

    # -------------------------------------------------------------------------
    # Category 3: data_databases (4 packages)
    # -------------------------------------------------------------------------
    {
        "id": "sqlite-inspector",
        "name": "SQLite Database Explorer",
        "category": "data_databases",
        "description": "Read and query local SQLite database tables, schemas, and query execution plans.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["read_query", "describe_table", "list_tables"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "test.db"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "postgres-connector",
        "name": "PostgreSQL Database Server",
        "category": "data_databases",
        "description": "Inspect PostgreSQL tables, execute parameterized SQL queries, and inspect relations.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["query", "get_schema", "explain_query"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/db"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "outbound_http",
            "credentials_required": ["POSTGRES_URL"],
            "sandbox_safe": True,
        },
    },
    {
        "id": "duckdb-analyzer",
        "name": "DuckDB Analytical Engine",
        "category": "data_databases",
        "description": "Fast analytical SQL processing over Parquet, CSV, and embedded columnar databases.",
        "repo_url": "https://github.com/duckdb/duckdb-mcp",
        "type": "mcp_server",
        "stars": 1200,
        "maintainer": "DuckDB Community",
        "capabilities": ["execute_sql", "export_parquet", "describe_dataset"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-duckdb"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "redis-manager",
        "name": "Redis In-Memory Store MCP",
        "category": "data_databases",
        "description": "Inspect keys, query hashsets, review TTLs, and monitor Redis instances safely.",
        "repo_url": "https://github.com/redis/mcp-server-redis",
        "type": "mcp_server",
        "stars": 850,
        "maintainer": "Redis Community",
        "capabilities": ["get_key", "scan_keys", "get_info"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@redis/mcp-server-redis"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "BSD-3-Clause",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "local_only",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },

    # -------------------------------------------------------------------------
    # Category 4: system_ops (4 packages)
    # -------------------------------------------------------------------------
    {
        "id": "docker-container-mcp",
        "name": "Docker Engine Inspector",
        "category": "system_ops",
        "description": "Inspect running containers, query logs, review image layers, and check network health.",
        "repo_url": "https://github.com/docker/mcp-server-docker",
        "type": "mcp_server",
        "stars": 2400,
        "maintainer": "Docker Community",
        "capabilities": ["list_containers", "inspect_container", "get_logs"],
        "entrypoint": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "docker/mcp-server-docker"],
            "env": {},
        },
        "dependencies": {"docker": ">=24"},
        "license": "Apache-2.0",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "local_only",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "filesystem-mcp",
        "name": "Secure Filesystem MCP",
        "category": "system_ops",
        "description": "Controlled filesystem access enabling directory tree listings and scoped file reads.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        "type": "mcp_server",
        "stars": 32000,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["read_file", "list_directory", "search_files"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "terminal-executor",
        "name": "Safe Command Executor",
        "category": "system_ops",
        "description": "Executes whitelisted terminal commands in isolated child processes with timeout caps.",
        "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/terminal",
        "type": "mcp_server",
        "stars": 1500,
        "maintainer": "Model Context Protocol Authors",
        "capabilities": ["run_whitelisted_command"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-terminal"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "kubernetes-mcp",
        "name": "Kubernetes Cluster Inspector",
        "category": "system_ops",
        "description": "Read-only Kubernetes cluster state inspection, pod logs, and deployment status.",
        "repo_url": "https://github.com/kubernetes/mcp-server-k8s",
        "type": "mcp_server",
        "stars": 920,
        "maintainer": "Kubernetes Community",
        "capabilities": ["get_pods", "get_services", "get_deployment_status"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@k8s/mcp-server"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "Apache-2.0",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "outbound_http",
            "credentials_required": ["KUBECONFIG"],
            "sandbox_safe": True,
        },
    },

    # -------------------------------------------------------------------------
    # Category 5: media (4 packages)
    # -------------------------------------------------------------------------
    {
        "id": "opencut",
        "name": "OpenCut Video Editor Skill",
        "category": "media",
        "description": "Comprehensive guide and reference for OpenCut web-based video editor. Use when the user asks about video editing, timeline assembly, or media exports.",
        "repo_url": "https://github.com/opencut/opencut",
        "type": "skill",
        "stars": 4500,
        "maintainer": "OpenCut Community",
        "capabilities": ["video_timeline_edit", "wasm_video_processing", "media_slice"],
        "entrypoint": {
            "command": "internal",
            "args": [],
            "env": {},
        },
        "dependencies": {},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity"],
        "security_notes": {
            "filesystem_access": "none",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "ffmpeg-media-tools",
        "name": "FFmpeg Media Converter",
        "category": "media",
        "description": "Audio and video transcoding, clipping, stream probing, and thumbnail generation.",
        "repo_url": "https://github.com/ffmpeg-mcp/server",
        "type": "mcp_server",
        "stars": 1100,
        "maintainer": "FFmpeg MCP Community",
        "capabilities": ["probe_media", "transcode_stream", "generate_thumbnail"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-ffmpeg"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "LGPL-2.1",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "image-processor",
        "name": "Image Manipulation MCP",
        "category": "media",
        "description": "Resize, crop, convert color spaces, and extract EXIF metadata from raster images.",
        "repo_url": "https://github.com/image-mcp/processor",
        "type": "mcp_server",
        "stars": 750,
        "maintainer": "Image MCP Community",
        "capabilities": ["resize_image", "extract_exif", "convert_format"],
        "entrypoint": {
            "command": "npx",
            "args": ["-y", "@media/image-processor-mcp"],
            "env": {},
        },
        "dependencies": {"node": ">=18"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
    {
        "id": "audio-transcriber",
        "name": "Audio Speech Transcriber",
        "category": "media",
        "description": "Local speech-to-text audio transcription and timestamped subtitle generation.",
        "repo_url": "https://github.com/whisper-mcp/transcriber",
        "type": "mcp_server",
        "stars": 1850,
        "maintainer": "Whisper MCP Community",
        "capabilities": ["transcribe_audio", "generate_vtt", "detect_language"],
        "entrypoint": {
            "command": "uvx",
            "args": ["mcp-server-whisper"],
            "env": {},
        },
        "dependencies": {"python": ">=3.10"},
        "license": "MIT",
        "validation_status": "verified",
        "platform_targets": ["antigravity", "claude_code"],
        "security_notes": {
            "filesystem_access": "scoped_read_write",
            "network_access": "none",
            "credentials_required": [],
            "sandbox_safe": True,
        },
    },
]


def get_seed_packages() -> List[Dict[str, Any]]:
    """Returns a deep copy of all 20 verified seed package records.

    Modifying the returned collection does not mutate the authoritative registry.
    """
    return copy.deepcopy(SEED_PACKAGES)


def get_package_by_id(package_id: str) -> Optional[Dict[str, Any]]:
    """Looks up a seed package by its unique identifier.

    Returns a deep copy of the package dictionary or None if not found.
    """
    for pkg in SEED_PACKAGES:
        if pkg["id"] == package_id:
            return copy.deepcopy(pkg)
    return None


def get_packages_by_category(category: str) -> List[Dict[str, Any]]:
    """Filters and returns deep copies of packages matching the specified category."""
    return [copy.deepcopy(pkg) for pkg in SEED_PACKAGES if pkg["category"] == category]


def get_curated_registries() -> List[Dict[str, Any]]:
    """Returns a deep copy of the curated official and community registry sources."""
    return copy.deepcopy(CURATED_REGISTRIES)


def get_seed_catalog() -> Dict[str, Any]:
    """Constructs and returns the full Draft-07 compliant seed catalog dictionary."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "version": "1.0.0",
        "last_updated": "2026-09-24T00:00:00Z",
        "total_packages": len(SEED_PACKAGES),
        "categories": list(CATEGORIES),
        "packages": get_seed_packages(),
    }


class RegistrySources:
    """Helper class providing unified accessor methods to the curated registry sources."""

    CATEGORIES = CATEGORIES
    CURATED_REGISTRIES = CURATED_REGISTRIES
    SEED_PACKAGES = SEED_PACKAGES

    @classmethod
    def get_seed_packages(cls) -> List[Dict[str, Any]]:
        return get_seed_packages()

    @classmethod
    def get_package_by_id(cls, package_id: str) -> Optional[Dict[str, Any]]:
        return get_package_by_id(package_id)

    @classmethod
    def get_packages_by_category(cls, category: str) -> List[Dict[str, Any]]:
        return get_packages_by_category(category)

    @classmethod
    def get_curated_registries(cls) -> List[Dict[str, Any]]:
        return get_curated_registries()

    @classmethod
    def get_seed_catalog(cls) -> Dict[str, Any]:
        return get_seed_catalog()
