# AI Skills & Model Context Protocol (MCP) Registry

[![JSON Schema Draft-07](https://img.shields.io/badge/JSON%20Schema-Draft--07-blue.svg)](http://json-schema.org/draft-07/schema#)
[![Packages](https://img.shields.io/badge/Packages-20%20Verified-brightgreen.svg)](#master-catalog-inventory)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Platforms](https://img.shields.io/badge/Platforms-Antigravity%20%7C%20Claude%20Code%20%7C%20Cursor-purple.svg)](#multi-platform-deployment--host-safety)
[![Tests](https://img.shields.io/badge/Tests-Tiers%201--5%20Passing-success.svg)](#testing--verification-architecture)

The **AI Skills & MCP Registry** is an automated discovery, validation, and multi-platform distribution pipeline. It bridges the ecosystem between GitHub MCP/Skill registries and local AI environments (Google Antigravity, Claude Code / Freebuff Desktop, Cursor / Codex) with progressive task-based routing, zero context saturation, and non-destructive host deployment.

---

## Architecture

The pipeline processes packages through five deterministic, isolated stages:

```
┌────────────────────────────────────────────────────────┐
│                   GitHub Ecosystem                     │
│  - modelcontextprotocol/servers                        │
│  - Curated community repos (>100 stars)                │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 1. Discovery & Metadata Indexer (crawler_catalog)      │
│  - Query registries, extract standardized metadata     │
│  - Produce catalog.json & catalog README.md (20 pkgs)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Quality & Schema Validator (validator_engine)       │
│  - Security & deprecation filtering                    │
│  - Draft-07 schema check & SKILL.md frontmatter check  │
│  - Zero-unhandled-exception dry-run verification       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Multi-Platform Deployment Engine (deployer_engine)  │
│  - Antigravity: ~/.gemini/config/skills/<name>/SKILL.md│
│    and mcp_config.json                                 │
│  - Claude Code: ~/.claude.json safe non-destructive    │
│    atomic deep-merge (safeguarding tinyfish API key)   │
│  - Parameterized PipelineEnvironmentConfig for testing │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. Intelligent Routing Directives (router_engine)      │
│  - 2-Tier Progressive Task-Based Intent Matrix (<100L) │
│  - Safe delimiter injection into AGENTS.md, CLAUDE.md, │
│    GEMINI.md without exceeding 24 KB / 20k token limit │
│  - Preserves AWS Toolkit & Crave compilation policies  │
└────────────────────────────────────────────────────────┘
```

---

# AI Model Skills & MCP Servers Catalog

Total Packages: 20 across 5 functional categories.

## Category: Browser Search

| ID | Name | Type | Stars | License | Description |
|---|---|---|---|---|---|
| `browser-playwright` | **Playwright Browser Automation** | `mcp_server` | 36000 | `Apache-2.0` | Headless browser automation for web navigation, screenshots, and DOM inspection. |
| `browser-puppeteer` | **Puppeteer MCP Server** | `mcp_server` | 32000 | `MIT` | Automated web browsing and scraping using Chrome DevTools Protocol. |
| `brave-search` | **Brave Search MCP** | `mcp_server` | 32000 | `MIT` | Real-time web search and news querying powered by the Brave Search API. |
| `fetch-markdown` | **Fetch Web to Markdown** | `mcp_server` | 32000 | `MIT` | Fetches web URLs and converts raw HTML into clean, token-efficient markdown. |

## Category: Code Intelligence

| ID | Name | Type | Stars | License | Description |
|---|---|---|---|---|---|
| `github-inspector` | **GitHub Context Server** | `mcp_server` | 32000 | `MIT` | Query GitHub repositories, issues, pull requests, commits, and workflow runs. |
| `git-repo-tools` | **Git Operations Server** | `mcp_server` | 32000 | `MIT` | Local Git repository inspection, history analysis, branching, and status checking. |
| `pyright-lsp` | **Pyright Language Server** | `mcp_server` | 14000 | `MIT` | Python type checking, definition jumping, symbol references, and diagnostic analysis. |
| `rust-analyzer-mcp` | **Rust Analyzer MCP** | `mcp_server` | 16000 | `Apache-2.0` | Rust language intelligence providing cargo diagnostics, type signatures, and macros. |

## Category: Data Databases

| ID | Name | Type | Stars | License | Description |
|---|---|---|---|---|---|
| `sqlite-inspector` | **SQLite Database Explorer** | `mcp_server` | 32000 | `MIT` | Read and query local SQLite database tables, schemas, and query execution plans. |
| `postgres-connector` | **PostgreSQL Database Server** | `mcp_server` | 32000 | `MIT` | Inspect PostgreSQL tables, execute parameterized SQL queries, and inspect relations. |
| `duckdb-analyzer` | **DuckDB Analytical Engine** | `mcp_server` | 1200 | `MIT` | Fast analytical SQL processing over Parquet, CSV, and embedded columnar databases. |
| `redis-manager` | **Redis In-Memory Store MCP** | `mcp_server` | 850 | `BSD-3-Clause` | Inspect keys, query hashsets, review TTLs, and monitor Redis instances safely. |

## Category: System Ops

| ID | Name | Type | Stars | License | Description |
|---|---|---|---|---|---|
| `docker-container-mcp` | **Docker Engine Inspector** | `mcp_server` | 2400 | `Apache-2.0` | Inspect running containers, query logs, review image layers, and check network health. |
| `filesystem-mcp` | **Secure Filesystem MCP** | `mcp_server` | 32000 | `MIT` | Controlled filesystem access enabling directory tree listings and scoped file reads. |
| `terminal-executor` | **Safe Command Executor** | `mcp_server` | 1500 | `MIT` | Executes whitelisted terminal commands in isolated child processes with timeout caps. |
| `kubernetes-mcp` | **Kubernetes Cluster Inspector** | `mcp_server` | 920 | `Apache-2.0` | Read-only Kubernetes cluster state inspection, pod logs, and deployment status. |

## Category: Media

| ID | Name | Type | Stars | License | Description |
|---|---|---|---|---|---|
| `opencut` | **OpenCut Video Editor Skill** | `skill` | 4500 | `MIT` | Comprehensive guide and reference for OpenCut web-based video editor. Use when the user asks about video editing, timeline assembly, or media exports. |
| `ffmpeg-media-tools` | **FFmpeg Media Converter** | `mcp_server` | 1100 | `LGPL-2.1` | Audio and video transcoding, clipping, stream probing, and thumbnail generation. |
| `image-processor` | **Image Manipulation MCP** | `mcp_server` | 750 | `MIT` | Resize, crop, convert color spaces, and extract EXIF metadata from raster images. |
| `audio-transcriber` | **Audio Speech Transcriber** | `mcp_server` | 1850 | `MIT` | Local speech-to-text audio transcription and timestamped subtitle generation. |

---

## Quickstart & CLI Usage

### Prerequisites
- Python 3.10+
- Node.js 18+ (for npm/npx-based MCP servers)
- `uvx` / `pip` (for Python-based MCP servers)

### 1. Crawl & Index Registries
Run the crawler in offline fixture mode or live query mode:
```powershell
# Pure offline generation (zero external network requests)
python -m src.crawler.github_crawler --offline --output catalog.json

# Live crawl with authenticated GitHub token (falls back gracefully on network errors)
python -m src.crawler.github_crawler --token <GITHUB_TOKEN> --output catalog.json

# Filter crawl by category
python -m src.crawler.github_crawler --offline --category browser_search
```

### 2. Validate Schema & Security
Run dry-run validation with zero unhandled exceptions:
```powershell
python -m src.validator.dry_run_runner --catalog catalog.json
```

### 3. Deploy to Local Environments
Perform non-destructive dry-run previews or live mounts:
```powershell
# Antigravity native skill and MCP config
python -m src.deployer.antigravity_deployer --dry-run

# Claude Code non-destructive deep-merge (safeguards tinyfish API key)
python -m src.deployer.claude_deployer --dry-run
```

### 4. Inject Intelligent Task Routing
Inject managed delimiters into rule files without exceeding budget:
```powershell
python -m src.router.rule_file_manager --inject
```

---

## Multi-Platform Deployment & Host Safety

The deployment pipeline is built with strict non-destructive safety guarantees:

### Google Antigravity
- Native skills are mounted to `C:\Users\BangerSoul\.gemini\config\skills\<name>\SKILL.md`.
- Conforms strictly to YAML frontmatter specification (`name`, `description`) with progressive disclosure via `references/`.
- Global MCP server configuration is safely initialized/updated at `C:\Users\BangerSoul\.gemini\config\mcp_config.json`.

### Claude Code & Freebuff Desktop
- Non-destructive deep merge into `C:\Users\BangerSoul\.claude.json` under `mcpServers`.
- **Absolute Key Safeguard**: Explicitly preserves pre-existing user configurations, including active `tinyfish` HTTP MCP server credentials (`sk-tinyfish-...`).
- Atomic file operations write to temporary staging files (`.claude.json.tmp.<pid>`) followed by atomic swap (`os.replace`) with timestamped backups in `C:\Users\BangerSoul\.ai-skills-registry\backups\`.

### Global Workspace Rule Files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`)
- Managed directives are strictly encapsulated within deterministic delimiters:
  ```markdown
  <!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->
  ...
  <!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->
  ```
- **Preserved System Policies**: User's pre-existing AWS Agent Toolkit guidelines (single region requirement) and Crave Builder heavy compilation policies (`crave.exe -n run -- <cmd>`) are strictly untouched.
- **Budget Compliance**: Stays well beneath Antigravity's **24 KB (24,000 bytes) per-file limit** and **20,000 token aggregate rule budget**.

---

## Quality, Security & Validation Gating

Every candidate tool must pass through four validation gates before installation:
1. **Maintenance & Deprecation Gate**: Filters out archived, unmaintained, or explicitly deprecated packages (e.g. `aws-api-mcp-server`).
2. **Security & Boundary Filter**: Blocks high/critical CVEs, shell injection vectors (`cmd.exe /c`, `sh -c`), directory traversal attempts, and exposed plain-text API secrets.
3. **Draft-07 Schema Conformance**: Validates all JSON-RPC tool parameters, entrypoint commands, transports, and SKILL.md YAML frontmatter.
4. **Dry-Run Runner**: Runs test invocations in an isolated sandbox, capturing 100% of exceptions into structured JSON diagnostic reports.

---

## Intelligent Skill Routing Directives

The registry generates a 2-Tier Progressive Task-Based Intent Matrix (<100 lines) mapping user requests to installed capabilities:

| Intent Domain | Keywords / Triggers | Recommended Tool | Platform |
|---|---|---|---|
| **Web Automation** | browse, scrape, navigate, screenshot, test UI | `browser-playwright`, `browser-puppeteer` | Claude Code, Antigravity |
| **Web Research** | search web, look up docs, query online | `brave-search`, `fetch-markdown` | Claude Code, Antigravity |
| **Code & PRs** | github pr, issue triage, repo search, git diff | `github-inspector`, `git-repo-tools` | Claude Code, Antigravity |
| **Language Intelligence** | type check, lsp, diagnostics, hover | `pyright-lsp`, `rust-analyzer-mcp` | Claude Code |
| **SQL & Relational** | sqlite, postgres, table schema, query db | `sqlite-inspector`, `postgres-connector` | Claude Code, Antigravity |
| **Analytics & OLAP** | parquet, duckdb, columnar query, csv analytics | `duckdb-analyzer` | Claude Code, Antigravity |
| **Caching & K/V** | redis, cache inspect, session keys | `redis-manager` | Claude Code, Antigravity |
| **Container Ops** | docker container, inspect image, logs | `docker-container-mcp` | Claude Code, Antigravity |
| **Cluster Ops** | kubernetes, k8s pod, deployment status | `kubernetes-mcp` | Claude Code, Antigravity |
| **Video Editing** | video edit, trim video, timeline, opencut | `opencut` (Skill), `ffmpeg-media-tools` | Antigravity, Claude Code |
| **Media Processing** | transcode, convert audio, image resize, stt | `image-processor`, `audio-transcriber` | Claude Code, Antigravity |

---

## Testing & Verification Architecture

The test suite covers 5 tiers of quality validation:
- **Tier 1 (Feature Coverage)**: >=5 unit tests per pipeline feature.
- **Tier 2 (Boundary & Corner Cases)**: Network dropouts, rate limits, corrupted JSON, missing env vars.
- **Tier 3 (Cross-Feature Pairwise)**: Crawl -> Validate -> Deploy integration chains.
- **Tier 4 (Real-World Workflows)**: End-to-end sandbox deployments verifying file integrity.
- **Tier 5 (Adversarial Hardening)**: White-box stress testing, malformed frontmatter, mutation defense.

### Running Test Suite
```powershell
python -m pytest tests/tier1_feature_coverage/ -v
```

---

## License

This project is licensed under the [MIT License](LICENSE). All indexed tools and MCP servers are subject to their respective open-source licenses as documented in `catalog.json`.
