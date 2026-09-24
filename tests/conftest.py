"""Global pytest configuration and sandbox isolation fixtures for AI-Skills-Registry.

This module provides virtual target sandboxes, mock configurations, and
authoritative contract fixtures ensuring strict opaque-box testing without
mutating any live user files or directories.
"""

import copy
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import yaml


# ==============================================================================
# 1. Environment Sandbox Model
# ==============================================================================

@dataclass
class SandboxEnv:
    """Represents an isolated, virtualized target environment."""
    root_dir: Path
    gemini_config_dir: Path
    gemini_skills_dir: Path
    gemini_mcp_config: Path
    gemini_skills_json: Path
    claude_json_path: Path
    agents_md_path: Path
    claude_md_path: Path
    gemini_md_path: Path
    backups_dir: Path

    def read_claude_json(self) -> Dict[str, Any]:
        """Read and parse sandbox .claude.json."""
        with open(self.claude_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_claude_json(self, data: Dict[str, Any]) -> None:
        """Write sandbox .claude.json atomically."""
        tmp = self.claude_json_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.claude_json_path)

    def read_gemini_mcp_config(self) -> Dict[str, Any]:
        """Read and parse sandbox mcp_config.json."""
        if not self.gemini_mcp_config.exists() or self.gemini_mcp_config.stat().st_size == 0:
            return {}
        with open(self.gemini_mcp_config, "r", encoding="utf-8") as f:
            return json.load(f)

    def read_rule_file(self, filename: str) -> str:
        """Read text from sandbox rule file."""
        target = self.root_dir / filename
        if not target.exists():
            return ""
        with open(target, "r", encoding="utf-8") as f:
            return f.read()


# ==============================================================================
# 2. Canonical Mock Data Fixtures
# ==============================================================================

MOCK_TINYFISH_SERVER = {
    "type": "http",
    "url": "https://agent.tinyfish.ai/mcp?source=tinyfish_cli&client=claude-code&connect_attempt_id=0e304406-54b0-40b9-8ad3-d4a2b4f4ba06",
    "headers": {
        "X-API-Key": "sk-tinyfish-XF3WGyHrnMiULqKTZWQ4vk8IONL-DIfO"
    }
}

MOCK_CLAUDE_JSON_TEMPLATE = {
    "numStartups": 42,
    "autoUpdates": True,
    "tipsHistory": {
        "tip_welcome": 5,
        "tip_shortcut": 2
    },
    "cachedGrowthBookFeatures": {
        "claude_code_beta_features": True,
        "enhanced_ast_indexer": False,
        "streaming_buffer_size": 4096
    },
    "pluginUsage": {
        "terminal_view": 12
    },
    "mcpServers": {
        "tinyfish": MOCK_TINYFISH_SERVER
    }
}

MOCK_AGENTS_MD_TEMPLATE = """<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance for the new AWS experience
This user has signed up for the new AWS experience.
Constraints:
- All projects share a single AWS Region determined by the user's contact address.
- MUST NOT use Lambda@Edge.
- MUST NOT use CloudFormation StackSets.
<!-- END AWS Agent Toolkit rules -->

# Heavy Builds & Cloud Compilation Policy: Crave Builder
- Never Build Heavy Targets Locally.
- Always Use Crave: crave.exe -n run -- "<commands>"
"""

MOCK_CLAUDE_MD_TEMPLATE = """# Core Implementation Directive
- Boil the ocean: complete implementations, zero TODO stubs.
- Full unit test coverage for every module.

# Heavy Builds & Cloud Compilation Policy: Crave Builder
- Never Build Heavy Targets Locally. Always use Crave.
"""

MOCK_GEMINI_MD_TEMPLATE = """<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance for the new AWS experience
- Region constraints apply to all resources.
<!-- END AWS Agent Toolkit rules -->
"""


def build_canonical_20_packages() -> List[Dict[str, Any]]:
    """Build the canonical 20-package metadata list covering all 5 categories."""
    return [
        # Category 1: browser_search (4)
        {
            "id": "browser-playwright",
            "name": "Playwright Browser Automation",
            "category": "browser_search",
            "description": "Headless browser automation for web navigation, screenshots, and DOM inspection.",
            "repo_url": "https://github.com/microsoft/playwright-mcp",
            "type": "mcp_server",
            "stars": 36000,
            "capabilities": ["browser_navigate", "browser_click", "browser_screenshot"],
            "entrypoint": {"command": "npx", "args": ["-y", "@playwright/mcp@latest"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "Apache-2.0",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "browser-puppeteer",
            "name": "Puppeteer MCP Server",
            "category": "browser_search",
            "description": "Automated web browsing and scraping using Chrome DevTools Protocol.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["navigate", "screenshot", "evaluate_js"],
            "entrypoint": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "brave-search",
            "name": "Brave Search MCP",
            "category": "browser_search",
            "description": "Real-time web search and news querying powered by the Brave Search API.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["brave_web_search", "brave_local_search"],
            "entrypoint": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "fetch-markdown",
            "name": "Fetch Web to Markdown",
            "category": "browser_search",
            "description": "Fetches web URLs and converts raw HTML into clean, token-efficient markdown.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["fetch_url"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-fetch"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },

        # Category 2: code_intelligence (4)
        {
            "id": "github-inspector",
            "name": "GitHub Context Server",
            "category": "code_intelligence",
            "description": "Query GitHub repositories, issues, pull requests, commits, and workflow runs.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["search_repositories", "get_file_contents", "list_issues"],
            "entrypoint": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "git-repo-tools",
            "name": "Git Operations Server",
            "category": "code_intelligence",
            "description": "Local Git repository inspection, history analysis, branching, and status checking.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/git",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["git_status", "git_diff", "git_log"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-git"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "pyright-lsp",
            "name": "Pyright Language Server",
            "category": "code_intelligence",
            "description": "Python type checking, definition jumping, symbol references, and diagnostic analysis.",
            "repo_url": "https://github.com/microsoft/pyright",
            "type": "mcp_server",
            "stars": 14000,
            "capabilities": ["goto_definition", "find_references", "type_check"],
            "entrypoint": {"command": "npx", "args": ["-y", "pyright-mcp-server"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["claude_code"]
        },
        {
            "id": "rust-analyzer-mcp",
            "name": "Rust Analyzer MCP",
            "category": "code_intelligence",
            "description": "Rust language intelligence providing cargo diagnostics, type signatures, and macros.",
            "repo_url": "https://github.com/rust-lang/rust-analyzer",
            "type": "mcp_server",
            "stars": 16000,
            "capabilities": ["rust_diagnostics", "rust_hover", "rust_expand_macro"],
            "entrypoint": {"command": "rust-analyzer-mcp", "args": [], "env": {}},
            "dependencies": {"rust": ">=1.75"},
            "license": "Apache-2.0",
            "validation_status": "verified",
            "platform_targets": ["claude_code"]
        },

        # Category 3: data_databases (4)
        {
            "id": "sqlite-inspector",
            "name": "SQLite Database Explorer",
            "category": "data_databases",
            "description": "Read and query local SQLite database tables, schemas, and query execution plans.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["read_query", "describe_table", "list_tables"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-sqlite", "--db-path", "test.db"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "postgres-connector",
            "name": "PostgreSQL Database Server",
            "category": "data_databases",
            "description": "Inspect PostgreSQL tables, execute parameterized SQL queries, and inspect relations.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["query", "get_schema", "explain_query"],
            "entrypoint": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/db"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "duckdb-analyzer",
            "name": "DuckDB Analytical Engine",
            "category": "data_databases",
            "description": "Fast analytical SQL processing over Parquet, CSV, and embedded columnar databases.",
            "repo_url": "https://github.com/duckdb/duckdb-mcp",
            "type": "mcp_server",
            "stars": 1200,
            "capabilities": ["execute_sql", "export_parquet", "describe_dataset"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-duckdb"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "redis-manager",
            "name": "Redis In-Memory Store MCP",
            "category": "data_databases",
            "description": "Inspect keys, query hashsets, review TTLs, and monitor Redis instances safely.",
            "repo_url": "https://github.com/redis/mcp-server-redis",
            "type": "mcp_server",
            "stars": 850,
            "capabilities": ["get_key", "scan_keys", "get_info"],
            "entrypoint": {"command": "npx", "args": ["-y", "@redis/mcp-server-redis"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "BSD-3-Clause",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },

        # Category 4: system_ops (4)
        {
            "id": "docker-container-mcp",
            "name": "Docker Engine Inspector",
            "category": "system_ops",
            "description": "Inspect running containers, query logs, review image layers, and check network health.",
            "repo_url": "https://github.com/docker/mcp-server-docker",
            "type": "mcp_server",
            "stars": 2400,
            "capabilities": ["list_containers", "inspect_container", "get_logs"],
            "entrypoint": {"command": "docker", "args": ["run", "-i", "--rm", "docker/mcp-server-docker"], "env": {}},
            "dependencies": {"docker": ">=24"},
            "license": "Apache-2.0",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "filesystem-mcp",
            "name": "Secure Filesystem MCP",
            "category": "system_ops",
            "description": "Controlled filesystem access enabling directory tree listings and scoped file reads.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
            "type": "mcp_server",
            "stars": 32000,
            "capabilities": ["read_file", "list_directory", "search_files"],
            "entrypoint": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "terminal-executor",
            "name": "Safe Command Executor",
            "category": "system_ops",
            "description": "Executes whitelisted terminal commands in isolated child processes with timeout caps.",
            "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/terminal",
            "type": "mcp_server",
            "stars": 1500,
            "capabilities": ["run_whitelisted_command"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-terminal"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "kubernetes-mcp",
            "name": "Kubernetes Cluster Inspector",
            "category": "system_ops",
            "description": "Read-only Kubernetes cluster state inspection, pod logs, and deployment status.",
            "repo_url": "https://github.com/kubernetes/mcp-server-k8s",
            "type": "mcp_server",
            "stars": 920,
            "capabilities": ["get_pods", "get_services", "get_deployment_status"],
            "entrypoint": {"command": "npx", "args": ["-y", "@k8s/mcp-server"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "Apache-2.0",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },

        # Category 5: media (4)
        {
            "id": "opencut",
            "name": "OpenCut Video Editor Skill",
            "category": "media",
            "description": "Comprehensive guide and reference for OpenCut web-based video editor. Use when the user asks about video editing, timeline assembly, or media exports.",
            "repo_url": "https://github.com/opencut/opencut",
            "type": "skill",
            "stars": 4500,
            "capabilities": ["video_timeline_edit", "wasm_video_processing", "media_slice"],
            "entrypoint": {"command": "internal", "args": [], "env": {}},
            "dependencies": {},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity"]
        },
        {
            "id": "ffmpeg-media-tools",
            "name": "FFmpeg Media Converter",
            "category": "media",
            "description": "Audio and video transcoding, clipping, stream probing, and thumbnail generation.",
            "repo_url": "https://github.com/ffmpeg-mcp/server",
            "type": "mcp_server",
            "stars": 1100,
            "capabilities": ["probe_media", "transcode_stream", "generate_thumbnail"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-ffmpeg"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "LGPL-2.1",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "image-processor",
            "name": "Image Manipulation MCP",
            "category": "media",
            "description": "Resize, crop, convert color spaces, and extract EXIF metadata from raster images.",
            "repo_url": "https://github.com/image-mcp/processor",
            "type": "mcp_server",
            "stars": 750,
            "capabilities": ["resize_image", "extract_exif", "convert_format"],
            "entrypoint": {"command": "npx", "args": ["-y", "@media/image-processor-mcp"], "env": {}},
            "dependencies": {"node": ">=18"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        },
        {
            "id": "audio-transcriber",
            "name": "Audio Speech Transcriber",
            "category": "media",
            "description": "Local speech-to-text audio transcription and timestamped subtitle generation.",
            "repo_url": "https://github.com/whisper-mcp/transcriber",
            "type": "mcp_server",
            "stars": 1850,
            "capabilities": ["transcribe_audio", "generate_vtt", "detect_language"],
            "entrypoint": {"command": "uvx", "args": ["mcp-server-whisper"], "env": {}},
            "dependencies": {"python": ">=3.10"},
            "license": "MIT",
            "validation_status": "verified",
            "platform_targets": ["antigravity", "claude_code"]
        }
    ]


def build_canonical_catalog_dict() -> Dict[str, Any]:
    """Build canonical catalog.json dictionary according to Draft-07 specification."""
    pkgs = build_canonical_20_packages()
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "version": "1.0.0",
        "total_packages": len(pkgs),
        "categories": [
            "browser_search",
            "code_intelligence",
            "data_databases",
            "system_ops",
            "media"
        ],
        "packages": pkgs
    }


# ==============================================================================
# 3. Reference Contract Logic (Oracle & Test Verifier)
# ==============================================================================

class ContractOracle:
    """Provides pure reference contract validation functions derived from specs."""

    SKILL_NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    DELIMITER_START = "<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->"
    DELIMITER_END = "<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->"

    @classmethod
    def validate_skill_frontmatter(cls, content: str) -> Dict[str, Any]:
        """Validate YAML frontmatter according to Antigravity SKILL.md specs."""
        if not content.startswith("---"):
            return {"valid": False, "error": "Missing initial frontmatter delimiter '---'"}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {"valid": False, "error": "Unclosed frontmatter delimiter '---'"}
        try:
            meta = yaml.safe_load(parts[1])
        except Exception as exc:
            return {"valid": False, "error": f"YAML syntax error: {exc}"}
        if not isinstance(meta, dict):
            return {"valid": False, "error": "Frontmatter is not a key-value mapping"}
        if "name" not in meta:
            return {"valid": False, "error": "Missing required field 'name'"}
        name = str(meta["name"]).strip()
        if not cls.SKILL_NAME_REGEX.match(name):
            return {"valid": False, "error": f"Name '{name}' violates lowercase-hyphen pattern"}
        if "description" not in meta:
            return {"valid": False, "error": "Missing required field 'description'"}
        desc = str(meta["description"]).strip()
        if len(desc) < 20:
            return {"valid": False, "error": "Description shorter than 20 chars minimum"}
        if len(desc) > 1024:
            return {"valid": False, "error": "Description longer than 1,024 chars maximum"}
        return {"valid": True, "metadata": meta, "body": parts[2]}

    @classmethod
    def deep_merge_claude_json(cls, original: Dict[str, Any], new_servers: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """Deep merge new MCP servers into Claude Code config preserving existing state."""
        result = copy.deepcopy(original)
        if "mcpServers" not in result or not isinstance(result["mcpServers"], dict):
            result["mcpServers"] = {}
        for server_name, server_cfg in new_servers.items():
            if server_name in result["mcpServers"] and not force:
                continue
            result["mcpServers"][server_name] = copy.deepcopy(server_cfg)
        return result

    @classmethod
    def inject_rule_delimiters(cls, current_content: str, routing_directive: str) -> str:
        """Inject or replace routing directive block idempotently."""
        block = f"{cls.DELIMITER_START}\n{routing_directive.strip()}\n{cls.DELIMITER_END}"
        pattern = re.compile(
            rf"{re.escape(cls.DELIMITER_START)}[\s\S]*?{re.escape(cls.DELIMITER_END)}",
            re.MULTILINE
        )
        if pattern.search(current_content):
            return pattern.sub(block, current_content)
        separator = "\n\n" if current_content.strip() else ""
        return f"{current_content.rstrip()}{separator}{block}\n"


# ==============================================================================
# 4. Pytest Fixtures
# ==============================================================================

@pytest.fixture
def sandbox_env(tmp_path: Path) -> SandboxEnv:
    """Create a fully isolated virtual staging sandbox for tests."""
    gemini_cfg = tmp_path / ".gemini" / "config"
    skills_dir = gemini_cfg / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Empty 0-byte mcp_config.json as found on user machine
    mcp_config = gemini_cfg / "mcp_config.json"
    mcp_config.touch()

    # Default skills.json
    skills_json = gemini_cfg / "skills.json"
    with open(skills_json, "w", encoding="utf-8") as f:
        json.dump({"entries": [{"path": "~/.gemini/config/skills"}]}, f, indent=2)

    # Mock .claude.json with tinyfish
    claude_json = tmp_path / ".claude.json"
    with open(claude_json, "w", encoding="utf-8") as f:
        json.dump(MOCK_CLAUDE_JSON_TEMPLATE, f, indent=2)

    # Mock rule files with AWS and Crave policies
    agents_md = tmp_path / "AGENTS.md"
    with open(agents_md, "w", encoding="utf-8") as f:
        f.write(MOCK_AGENTS_MD_TEMPLATE)

    claude_md = tmp_path / "CLAUDE.md"
    with open(claude_md, "w", encoding="utf-8") as f:
        f.write(MOCK_CLAUDE_MD_TEMPLATE)

    gemini_md = tmp_path / "GEMINI.md"
    with open(gemini_md, "w", encoding="utf-8") as f:
        f.write(MOCK_GEMINI_MD_TEMPLATE)

    backups = tmp_path / ".backups"
    backups.mkdir(parents=True, exist_ok=True)

    return SandboxEnv(
        root_dir=tmp_path,
        gemini_config_dir=gemini_cfg,
        gemini_skills_dir=skills_dir,
        gemini_mcp_config=mcp_config,
        gemini_skills_json=skills_json,
        claude_json_path=claude_json,
        agents_md_path=agents_md,
        claude_md_path=claude_md,
        gemini_md_path=gemini_md,
        backups_dir=backups,
    )


@pytest.fixture
def canonical_catalog() -> Dict[str, Any]:
    """Provide the canonical 20-package Draft-07 catalog dictionary."""
    return build_canonical_catalog_dict()


@pytest.fixture
def oracle() -> ContractOracle:
    """Provide contract oracle validator."""
    return ContractOracle()
