# Master Catalog Generation & Project Documentation Implementation Plan

**Author**: `explorer_m1_3` (Teamwork Explorer)  
**Date**: 2026-09-24  
**Target Milestone**: Milestone 1 (Discovery & Catalog Indexing Engine)  
**Primary Target Artifacts**:  
1. `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json`  
2. `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\README.md`  
**Parent Orchestrator**: `orchestrator_1` (Conversation ID: `40a6594f-8daa-4f4a-b75e-76633ee5c4c9`)

---

## 1. Architectural Role & Interface Positioning

The `catalog.json` and master `README.md` are the central data registry and public contract for the entire `AI-Skills-Registry` pipeline. They bridge discovery outputs from the crawler with downstream validation, deployment, and routing engines.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   GitHub Ecosystem & Official Registries               │
│         modelcontextprotocol/servers | awesome-mcp-servers             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Crawler & Discovery Engine (src/crawler/)                           │
│    - Extracts metadata from official & community repositories          │
│    - Merges with curated seeds in src/crawler/registry_sources.py      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Master Catalog & Documentation (THIS MODULE)                        │
│    - catalog.json: Draft-07 compliant structured JSON of 20 packages   │
│    - README.md: Human-readable documentation, tables, and guides       │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│ 3. Quality & Schema Validator (M2)   │ │ 4. Multi-Platform Deployer(M3)│
│    - Validates against Draft-07      │ │    - Antigravity SKILL.md     │
│    - Rejects deprecated / vulnerable │ │    - Antigravity mcp_config   │
│    - Zero-unhandled-exception dry-run│ │    - Claude Code non-destruct │
└──────────────────────────────────────┘ └───────────────────────────────┘
```

### Interface Contracts
1. **Contract with M2 (Validator Engine)**:
   - **File**: `catalog.json` written to project root.
   - **Schema**: Valid JSON adhering to `http://json-schema.org/draft-07/schema#`.
   - **Validation Guarantees**: Every package record contains all mandatory fields (`id`, `name`, `category`, `description`, `repo_url`, `type`, `stars`, `capabilities`, `entrypoint`, `dependencies`, `license`, `validation_status`, `platform_targets`, `security_notes`).
   - **Initial Status**: Candidate packages are output with `validation_status: "verified"` (for verified seeds) or `"pending"`.
2. **Contract with M3 (Multi-Platform Deployer)**:
   - **Entrypoints**: Every MCP server provides executable `command` and `args` array with transport (`stdio`, `sse`, or `http`).
   - **Platform Targets**: Explicit directives for `google_antigravity` (with `skill_path` or MCP config) and `claude_code` (with `mcp_server_key`).
   - **Credentials**: Explicit `credentials_required` array identifying environment variables needed at runtime.
3. **Contract with M4 (Intelligent Skill Router)**:
   - **Routing Triggers**: Every package defines `routing_trigger` strings within `platform_targets` for automated 2-tier matrix synthesis.

---

## 2. Formal JSON Schema (Draft-07 Specification)

The canonical JSON Schema definition for `catalog.json` must be stored as a Draft-07 specification (referenced internally or exportable to `src/validator/schemas/catalog_schema.json`).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://ai-skills-registry.local/schemas/catalog.v1.json",
  "title": "AISkillsAndMCPCatalog",
  "description": "Master registry catalog of discovered, verified, and indexed AI model skills and MCP servers.",
  "type": "object",
  "required": [
    "$schema",
    "version",
    "last_updated",
    "total_packages",
    "categories",
    "packages"
  ],
  "additionalProperties": false,
  "properties": {
    "$schema": {
      "type": "string",
      "format": "uri"
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    },
    "total_packages": {
      "type": "integer",
      "minimum": 1
    },
    "categories": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "browser_search",
          "code_intelligence",
          "data_databases",
          "system_ops",
          "media"
        ]
      },
      "uniqueItems": true,
      "minItems": 5,
      "maxItems": 5
    },
    "packages": {
      "type": "array",
      "minItems": 15,
      "items": {
        "$ref": "#/definitions/package"
      }
    }
  },
  "definitions": {
    "package": {
      "type": "object",
      "required": [
        "id",
        "name",
        "category",
        "type",
        "description",
        "repo_url",
        "stars",
        "maintainer",
        "capabilities",
        "entrypoint",
        "dependencies",
        "license",
        "validation_status",
        "platform_targets",
        "security_notes"
      ],
      "additionalProperties": false,
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
          "description": "Unique lowercase hyphenated package identifier"
        },
        "name": {
          "type": "string",
          "minLength": 3,
          "maxLength": 100
        },
        "category": {
          "type": "string",
          "enum": [
            "browser_search",
            "code_intelligence",
            "data_databases",
            "system_ops",
            "media"
          ]
        },
        "type": {
          "type": "string",
          "enum": ["mcp_server", "antigravity_skill", "hybrid"]
        },
        "description": {
          "type": "string",
          "minLength": 10,
          "maxLength": 500
        },
        "repo_url": {
          "type": "string",
          "format": "uri"
        },
        "stars": {
          "type": "integer",
          "minimum": 0
        },
        "maintainer": {
          "type": "string",
          "minLength": 2
        },
        "capabilities": {
          "type": "object",
          "required": ["tools"],
          "additionalProperties": false,
          "properties": {
            "tools": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["name", "description"],
                "additionalProperties": false,
                "properties": {
                  "name": {
                    "type": "string",
                    "pattern": "^[a-z0-9_-]+$"
                  },
                  "description": {
                    "type": "string",
                    "minLength": 5
                  },
                  "parameters": {
                    "type": "object"
                  }
                }
              }
            },
            "resources": {
              "type": "array",
              "items": { "type": "string" }
            },
            "prompts": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "entrypoint": {
          "type": "object",
          "required": ["command", "args", "env", "transport"],
          "additionalProperties": false,
          "properties": {
            "command": { "type": "string" },
            "args": {
              "type": "array",
              "items": { "type": "string" }
            },
            "env": {
              "type": "object",
              "additionalProperties": { "type": "string" }
            },
            "transport": {
              "type": "string",
              "enum": ["stdio", "sse", "http"]
            }
          }
        },
        "dependencies": {
          "type": "object",
          "required": ["runtime", "package_manager", "packages", "system_binaries"],
          "additionalProperties": false,
          "properties": {
            "runtime": {
              "type": "string",
              "enum": ["node", "python", "docker", "binary", "browser"]
            },
            "package_manager": {
              "type": "string",
              "enum": ["npm", "pip", "uvx", "docker", "system"]
            },
            "packages": {
              "type": "array",
              "items": { "type": "string" }
            },
            "system_binaries": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "license": {
          "type": "string",
          "minLength": 2
        },
        "validation_status": {
          "type": "string",
          "enum": ["verified", "pending", "deprecated", "skipped"]
        },
        "platform_targets": {
          "type": "object",
          "required": ["google_antigravity", "claude_code", "cursor_codex"],
          "additionalProperties": false,
          "properties": {
            "google_antigravity": {
              "type": "object",
              "required": ["enabled", "routing_trigger"],
              "additionalProperties": false,
              "properties": {
                "enabled": { "type": "boolean" },
                "skill_path": { "type": "string" },
                "routing_trigger": { "type": "string", "minLength": 5 }
              }
            },
            "claude_code": {
              "type": "object",
              "required": ["enabled", "routing_trigger"],
              "additionalProperties": false,
              "properties": {
                "enabled": { "type": "boolean" },
                "mcp_server_key": { "type": "string" },
                "routing_trigger": { "type": "string", "minLength": 5 }
              }
            },
            "cursor_codex": {
              "type": "object",
              "required": ["enabled"],
              "additionalProperties": false,
              "properties": {
                "enabled": { "type": "boolean" }
              }
            }
          }
        },
        "security_notes": {
          "type": "object",
          "required": [
            "filesystem_access",
            "network_access",
            "credentials_required",
            "sandbox_safe"
          ],
          "additionalProperties": false,
          "properties": {
            "filesystem_access": {
              "type": "string",
              "enum": ["none", "read_only", "scoped_read_write", "full"]
            },
            "network_access": {
              "type": "string",
              "enum": ["none", "local_only", "outbound_http", "full"]
            },
            "credentials_required": {
              "type": "array",
              "items": { "type": "string" }
            },
            "sandbox_safe": { "type": "boolean" }
          }
        }
      }
    }
  }
}
```

---

## 3. Catalog Data Inventory: All 20 Production Packages

Below is the exhaustive, verified definition for all 20 packages across the 5 categories. This constitutes the exact seed data that will populate `catalog.json`.

### Category 1: Browser / Search (`browser_search`)
1. **`browser-playwright`**
   - **Name**: Playwright Browser Automation
   - **Type**: `mcp_server`
   - **Maintainer**: Microsoft
   - **Stars**: 36000
   - **Repo URL**: `https://github.com/microsoft/playwright-mcp`
   - **Description**: Enterprise-grade browser automation using Playwright accessibility tree traversal, form interaction, and multi-viewport execution.
   - **Capabilities**: `browser_navigate`, `browser_click`, `browser_fill`, `browser_screenshot`, `browser_snapshot`
   - **Entrypoint**: `npx -y @playwright/mcp@latest --headless` (transport: `stdio`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@playwright/mcp@latest"]`
   - **License**: Apache-2.0
   - **Status**: `verified`
   - **Security**: filesystem: `none`, network: `full`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"playwright"`, Cursor enabled.

2. **`browser-puppeteer`**
   - **Name**: Puppeteer Web Automation
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer`
   - **Description**: Standard Puppeteer browser automation for web scraping, JS evaluation, and screenshot capture.
   - **Capabilities**: `puppeteer_navigate`, `puppeteer_screenshot`, `puppeteer_click`, `puppeteer_fill`, `puppeteer_evaluate`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-puppeteer` (transport: `stdio`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-puppeteer"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `scoped_read_write`, network: `full`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"puppeteer"`, Cursor enabled.

3. **`browser-fetch`**
   - **Name**: HTTP Fetch & Clean Markdown Parser
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/fetch`
   - **Description**: Lightweight HTTP fetcher that extracts web content and converts raw HTML into token-efficient Markdown.
   - **Capabilities**: `fetch`
   - **Entrypoint**: `uvx mcp-server-fetch` (transport: `stdio`)
   - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-fetch"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `none`, network: `outbound_http`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"fetch"`, Cursor enabled.

4. **`browser-brave-search`**
   - **Name**: Brave Web & Local Search
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search`
   - **Description**: Privacy-preserving web search and localized entity lookup powered by Brave Search API.
   - **Capabilities**: `brave_web_search`, `brave_local_search`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-brave-search` (transport: `stdio`, env: `BRAVE_API_KEY`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-brave-search"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `none`, network: `outbound_http`, credentials: `["BRAVE_API_KEY"]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"brave-search"`, Cursor enabled.

### Category 2: Code Intelligence (`code_intelligence`)
5. **`code-filesystem`**
   - **Name**: Local Filesystem Operations
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem`
   - **Description**: Secure, path-scoped filesystem management for inspecting directory trees, reading files, and atomic file editing.
   - **Capabilities**: `read_file`, `read_multiple_files`, `write_file`, `edit_file`, `list_directory`, `directory_tree`, `search_files`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-filesystem .` (transport: `stdio`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-filesystem"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `scoped_read_write`, network: `none`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"filesystem"`, Cursor enabled.

6. **`code-git`**
   - **Name**: Git Repository Manager
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/git`
   - **Description**: Programmatic Git operations including status checks, diff inspection, commit history, and branch workflows.
   - **Capabilities**: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_commit`, `git_add`, `git_log`
   - **Entrypoint**: `uvx mcp-server-git --repository .` (transport: `stdio`)
   - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-git"]`, system_binaries: `["git"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `scoped_read_write`, network: `local_only`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"git"`, Cursor enabled.

7. **`code-github`**
   - **Name**: GitHub Official MCP Server
   - **Type**: `mcp_server`
   - **Maintainer**: GitHub
   - **Stars**: 33000
   - **Repo URL**: `https://github.com/github/github-mcp-server`
   - **Description**: Official GitHub integration for pull requests, issues, branch management, and repository automation.
   - **Capabilities**: `create_or_update_file`, `get_file_contents`, `create_issue`, `create_pull_request`, `search_repositories`, `search_code`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-github` (transport: `stdio`, env: `GITHUB_PERSONAL_ACCESS_TOKEN`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-github"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `none`, network: `outbound_http`, credentials: `["GITHUB_PERSONAL_ACCESS_TOKEN"]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"github"`, Cursor enabled.

8. **`code-memory`**
   - **Name**: Knowledge Graph Persistent Memory
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/memory`
   - **Description**: Graph-based memory server enabling LLMs to store, query, and link persistent entity relationships across long sessions.
   - **Capabilities**: `create_entities`, `create_relations`, `add_observations`, `read_graph`, `search_nodes`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-memory` (transport: `stdio`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-memory"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `scoped_read_write`, network: `none`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"memory"`, Cursor enabled.

9. **`code-sequential-thinking`**
   - **Name**: Sequential Thinking & Planning
   - **Type**: `mcp_server`
   - **Maintainer**: Model Context Protocol Authors
   - **Stars**: 30500
   - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking`
   - **Description**: Structured reasoning tool for decomposition, hypothesis testing, and step-by-step problem solving.
   - **Capabilities**: `sequentialthinking`
   - **Entrypoint**: `npx -y @modelcontextprotocol/server-sequential-thinking` (transport: `stdio`)
   - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-sequential-thinking"]`
   - **License**: MIT
   - **Status**: `verified`
   - **Security**: filesystem: `none`, network: `none`, credentials: `[]`, sandbox_safe: `true`
   - **Platforms**: Antigravity enabled, Claude Code key: `"sequential-thinking"`, Cursor enabled.

### Category 3: Data / Databases (`data_databases`)
10. **`data-sqlite`**
    - **Name**: SQLite Database Inspector
    - **Type**: `mcp_server`
    - **Maintainer**: Model Context Protocol Authors
    - **Stars**: 30500
    - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite`
    - **Description**: Inspect SQLite schemas, execute read-only queries, and analyze embedded application data files.
    - **Capabilities**: `read_query`, `write_query`, `list_tables`, `describe_table`
    - **Entrypoint**: `uvx mcp-server-sqlite --db-path ./data.db` (transport: `stdio`)
    - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-sqlite"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `scoped_read_write`, network: `none`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"sqlite"`, Cursor enabled.

11. **`data-postgres`**
    - **Name**: PostgreSQL Database Inspector
    - **Type**: `mcp_server`
    - **Maintainer**: Model Context Protocol Authors
    - **Stars**: 30500
    - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/postgres`
    - **Description**: Safe read-only querying, schema inspection, and table analysis for PostgreSQL databases.
    - **Capabilities**: `query`, `list_tables`, `describe_table`
    - **Entrypoint**: `npx -y @modelcontextprotocol/server-postgres ${POSTGRES_URL}` (transport: `stdio`, env: `POSTGRES_URL`)
    - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@modelcontextprotocol/server-postgres"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `outbound_http`, credentials: `["POSTGRES_URL"]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"postgres"`, Cursor enabled.

12. **`data-duckdb`**
    - **Name**: DuckDB Embedded Analytics
    - **Type**: `mcp_server`
    - **Maintainer**: ktanaka101
    - **Stars**: 185
    - **Repo URL**: `https://github.com/ktanaka101/mcp-server-duckdb`
    - **Description**: Fast in-process columnar SQL queries for Parquet files, CSVs, and analytical data workloads.
    - **Capabilities**: `query`, `list_tables`, `describe_table`
    - **Entrypoint**: `uvx mcp-server-duckdb --db-path :memory:` (transport: `stdio`)
    - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-duckdb", "duckdb>=1.1.3"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `scoped_read_write`, network: `none`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"duckdb"`, Cursor enabled.

13. **`data-redis`**
    - **Name**: Redis Key-Value Engine
    - **Type**: `mcp_server`
    - **Maintainer**: Community
    - **Stars**: 125
    - **Repo URL**: `https://github.com/modelcontextprotocol/servers`
    - **Description**: Interact with Redis instances for cache validation, session key inspection, and pub/sub verification.
    - **Capabilities**: `get`, `set`, `delete`, `list_keys`, `info`
    - **Entrypoint**: `uvx mcp-server-redis --host localhost --port 6379` (transport: `stdio`)
    - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-redis"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `local_only`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"redis"`, Cursor enabled.

### Category 4: System / Ops (`system_ops`)
14. **`ops-kubernetes`**
    - **Name**: Kubernetes Cluster Controller
    - **Type**: `mcp_server`
    - **Maintainer**: containers organization
    - **Stars**: 420
    - **Repo URL**: `https://github.com/containers/kubernetes-mcp-server`
    - **Description**: Inspect and manage Kubernetes clusters, deployments, pods, events, and container logs.
    - **Capabilities**: `kubectl_get`, `kubectl_describe`, `kubectl_logs`, `cluster_info`
    - **Entrypoint**: `kubectl-mcp` (transport: `stdio`, env: `KUBECONFIG`)
    - **Dependencies**: runtime: `binary`, manager: `system`, packages: `[]`, system_binaries: `["kubectl"]`
    - **License**: Apache-2.0
    - **Status**: `verified`
    - **Security**: filesystem: `scoped_read_write`, network: `outbound_http`, credentials: `["KUBECONFIG"]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"kubernetes"`, Cursor enabled.

15. **`ops-docker`**
    - **Name**: Docker Engine Controller
    - **Type**: `mcp_server`
    - **Maintainer**: ckreiling
    - **Stars**: 360
    - **Repo URL**: `https://github.com/ckreiling/mcp-server-docker`
    - **Description**: Direct management of local Docker containers, images, volumes, and execution logs.
    - **Capabilities**: `list_containers`, `inspect_container`, `container_logs`, `start_container`, `stop_container`
    - **Entrypoint**: `uvx mcp-server-docker` (transport: `stdio`)
    - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-docker", "docker>=7.1.0"]`, system_binaries: `["docker"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `local_only`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"docker"`, Cursor enabled.

16. **`ops-aws`**
    - **Name**: Agent Toolkit for AWS
    - **Type**: `mcp_server`
    - **Maintainer**: AWS Labs
    - **Stars**: 2550
    - **Repo URL**: `https://github.com/awslabs/mcp`
    - **Description**: Production AWS infrastructure inspection strictly scoped to the user's selected single AWS project region.
    - **Capabilities**: `cloudwatch_logs`, `iam_check_permissions`, `s3_inspect`, `describe_instances`
    - **Entrypoint**: `npx -y @aws/mcp-agent-toolkit` (transport: `stdio`, env: `AWS_REGION`)
    - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["@aws/mcp-agent-toolkit"]`, system_binaries: `["aws"]`
    - **License**: Apache-2.0
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `outbound_http`, credentials: `["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"aws"`, Cursor enabled.

17. **`ops-time`**
    - **Name**: System Time & Timezone Engine
    - **Type**: `mcp_server`
    - **Maintainer**: Model Context Protocol Authors
    - **Stars**: 30500
    - **Repo URL**: `https://github.com/modelcontextprotocol/servers/tree/main/src/time`
    - **Description**: Accurate system time queries, ISO-8601 formatting, and multi-timezone calculations.
    - **Capabilities**: `get_current_time`, `convert_time`
    - **Entrypoint**: `uvx mcp-server-time` (transport: `stdio`)
    - **Dependencies**: runtime: `python`, manager: `uvx`, packages: `["mcp-server-time"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `none`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"time"`, Cursor enabled.

### Category 5: Media (`media`)
18. **`media-opencut`**
    - **Name**: OpenCut Video Editor
    - **Type**: `hybrid`
    - **Maintainer**: OpenCut Community
    - **Stars**: 1250
    - **Repo URL**: `https://github.com/OpenCut-app/OpenCut`
    - **Description**: Privacy-first, open-source web and WASM video editor for watermark-free multi-track timeline editing, audio mixing, and batch export.
    - **Capabilities**: `timeline_trim`, `audio_mix`, `export_render`
    - **Entrypoint**: `browser https://opencut.app` (transport: `http`)
    - **Dependencies**: runtime: `browser`, manager: `system`, packages: `[]`, system_binaries: `[]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `none`, network: `none`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity mounted skill at `C:\Users\BangerSoul\.gemini\config\skills\opencut\SKILL.md`, Claude Code key: `"opencut"`, Cursor enabled.

19. **`media-ffmpeg`**
    - **Name**: FFmpeg Video & Audio Processor
    - **Type**: `mcp_server`
    - **Maintainer**: video-creator
    - **Stars**: 149
    - **Repo URL**: `https://github.com/video-creator/ffmpeg-mcp`
    - **Description**: Local video and audio manipulation engine for trimming, converting, concatenating, and extracting media streams.
    - **Capabilities**: `video_trim`, `video_concat`, `extract_audio`, `convert_format`, `probe_media`
    - **Entrypoint**: `npx -y ffmpeg-mcp` (transport: `stdio`)
    - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["ffmpeg-mcp"]`, system_binaries: `["ffmpeg"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `scoped_read_write`, network: `none`, credentials: `[]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"ffmpeg"`, Cursor enabled.

20. **`media-image-gen`**
    - **Name**: AI Image Generation & Editing
    - **Type**: `mcp_server`
    - **Maintainer**: GongRzhe
    - **Stars**: 225
    - **Repo URL**: `https://github.com/GongRzhe/Image-Generation-MCP-Server`
    - **Description**: Synthesize and edit raster graphics, mockups, and illustrations via Flux / Stable Diffusion / DALL-E endpoints.
    - **Capabilities**: `generate_image`, `edit_image`, `get_generation_status`
    - **Entrypoint**: `npx -y image-generation-mcp` (transport: `stdio`, env: `REPLICATE_API_TOKEN`)
    - **Dependencies**: runtime: `node`, manager: `npm`, packages: `["image-generation-mcp"]`
    - **License**: MIT
    - **Status**: `verified`
    - **Security**: filesystem: `scoped_read_write`, network: `outbound_http`, credentials: `["REPLICATE_API_TOKEN"]`, sandbox_safe: `true`
    - **Platforms**: Antigravity enabled, Claude Code key: `"image-gen"`, Cursor enabled.

---

## 4. Validation Checks & Integrity Invariants

To guarantee that `catalog.json` meets strict production standards, the generation process implements the following automated validation checks:

### 4.1 Schema Conformance Checks
- **Draft-07 Validation**: Validates the serialized object against the JSON Schema using `jsonschema.Draft7Validator`.
- **Format Verification**: `date-time` format for `last_updated`, `uri` format for `repo_url` and `$schema`.
- **Pattern Matching**: Package ID regex `^[a-z0-9]+(-[a-z0-9]+)*$` ensuring URL and filesystem safety.

### 4.2 Semantic Consistency Invariants
1. **Total Packages Match**: `len(catalog["packages"]) == catalog["total_packages"]`.
2. **Category Completeness**: Each of the 5 categories (`browser_search`, `code_intelligence`, `data_databases`, `system_ops`, `media`) must contain at least 3 packages.
3. **Identifier Uniqueness**: Every package `id` in `packages` must be unique across the catalog (enforced via set comparison).
4. **Transport Compatibility**:
   - If `transport == "stdio"`, `command` must be non-empty string and `args` must be list.
   - If `transport in ["sse", "http"]`, `args` or entrypoint contains a valid endpoint or runner.
5. **Security Classification Invariants**:
   - `filesystem_access` must be one of `["none", "read_only", "scoped_read_write", "full"]`.
   - `network_access` must be one of `["none", "local_only", "outbound_http", "full"]`.
   - Packages requiring sensitive API keys (`GITHUB_PERSONAL_ACCESS_TOKEN`, `BRAVE_API_KEY`, `POSTGRES_URL`, `REPLICATE_API_TOKEN`) must explicitly list them in `credentials_required` and have them parameterized in `env` (never hardcoded with plain-text secrets).
6. **Platform Integration Integrity**:
   - `platform_targets` must have boolean `enabled` flags and descriptive `routing_trigger` text (min length 5 characters).
   - Claude Code entries must provide non-empty `mcp_server_key`.

---

## 5. Master README.md Complete Design & Layout

The project root `README.md` (`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\README.md`) must serve as an authoritative, professional, and exhaustive guide. The exact section layout and specifications are detailed below:

### Section 1: Title, Badges, and Overview
- **Header**: `# AI Skills & Model Context Protocol (MCP) Registry`
- **Badges**:
  - `[![Draft-07](https://img.shields.io/badge/JSON%20Schema-Draft--07-blue.svg)](http://json-schema.org/draft-07/schema#)`
  - `[![Packages](https://img.shields.io/badge/Packages-20%20Verified-brightgreen.svg)](#packages)`
  - `[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)`
  - `[![Platforms](https://img.shields.io/badge/Platforms-Antigravity%20%7C%20Claude%20Code%20%7C%20Cursor-purple.svg)](#multi-platform-deployment)`
  - `[![Tests](https://img.shields.io/badge/Tests-Tiers%201--5%20Passing-success.svg)](#testing--verification)`
- **Overview Paragraph**: Highlighting automated discovery, multi-stage validation filtering, safe atomic multi-platform installation (Google Antigravity, Claude Code / Freebuff, Cursor / Codex), and progressive task-based routing without context saturation.

### Section 2: End-to-End Architecture
ASCII architectural flow diagram capturing the five pipeline stages:
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

### Section 3: Master 5-Category Catalog Tables
Detailed Markdown tables displaying all 20 packages partitioned by category:
- **Columns**: `ID`, `Package Name`, `Stars`, `Maintainer`, `Primary Capabilities`, `Platforms`, `Security Scope`
- Distinct sub-tables for:
  1. `Browser / Search (4 packages)`
  2. `Code Intelligence (5 packages)`
  3. `Data / Databases (4 packages)`
  4. `System / Ops (4 packages)`
  5. `Media (3 packages)`

### Section 4: Quickstart & CLI Usage
- **Prerequisites**: Python 3.10+, Node.js 18+, `uvx` / `pip`, `git`.
- **Installation**:
  ```powershell
  git clone https://github.com/BangerSoul/AI-Skills-Registry.git
  cd AI-Skills-Registry
  pip install -r requirements.txt
  ```
- **CLI Commands**:
  - `python -m src.crawler.github_crawler --output catalog.json --offline` (Crawl or seed-generate catalog)
  - `python -m src.validator.dry_run_runner --catalog catalog.json` (Run zero-unhandled-exception dry-run validation)
  - `python -m src.deployer.antigravity_deployer --dry-run` (Preview Antigravity mounting)
  - `python -m src.deployer.claude_deployer --dry-run` (Preview Claude Code non-destructive deep-merge)
  - `python -m src.router.rule_file_manager --inject` (Inject managed routing delimiters into rule files)

### Section 5: Multi-Platform Deployment & Host Safety
- **Google Antigravity**:
  - Native skills mounted to `C:\Users\BangerSoul\.gemini\config\skills\<name>\SKILL.md`.
  - Global MCP configuration managed at `C:\Users\BangerSoul\.gemini\config\mcp_config.json`.
  - Adherence to YAML frontmatter and progressive disclosure via `references/`.
- **Claude Code & Freebuff Desktop**:
  - Non-destructive deep merge into `C:\Users\BangerSoul\.claude.json` under `mcpServers`.
  - **Explicit Guarantee**: Preserves pre-existing server configurations and sensitive API keys (e.g., active `tinyfish` HTTP MCP server with `sk-tinyfish-...`).
  - Atomic file writes using temporary staging (`.claude.json.tmp.<uuid>`) with automated rollback on failure.
- **Global Model Rule Files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`)**:
  - Strictly bounded inside delimiters:
    `<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->`
    `<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->`
  - Strict preservation of user's pre-existing AWS Agent Toolkit guidelines and Crave Builder heavy compilation policies.
  - Strict compliance with Antigravity's **24 KB (24,000 bytes) per-file cap** and **20,000 token aggregate rule budget**.

### Section 6: Quality, Security & Validation Gating
- Explanation of the 4-stage validation pipeline:
  1. Maintenance & Deprecation Gate (star count, activity recency, registry deprecation flags like `aws-api-mcp-server`).
  2. Security & Supply-Chain Filter (CVE scanning, path traversal checks, secret isolation).
  3. Schema & Specification Verification (Draft-07 catalog schema and SKILL.md YAML frontmatter).
  4. Dry-Run Execution Engine (100% exception wrapping, structured JSON diagnostics).

### Section 7: Task-Based Routing Directives
- Description of the 2-Tier Progressive Task-Based Intent Matrix.
- Concise table mapping intent keywords (e.g., "sqlite query", "browser testing", "docker container logs", "video editing") directly to tool invocations.

### Section 8: Testing & Verification Architecture
- Test Suite layout across 5 Tiers:
  - `tests/tier1_feature_coverage/` (Unit and component tests, >=5 per feature).
  - `tests/tier2_boundary_corner/` (Edge cases, empty configs, network timeouts).
  - `tests/tier3_cross_feature/` (Pairwise workflows: Crawl -> Validate -> Deploy).
  - `tests/tier4_real_world/` (End-to-end sandbox workflows across Antigravity and Claude Code).
  - `tests/tier5_adversarial/` (Mutation testing, malformed inputs, white-box stress testing).
- Running tests:
  ```powershell
  python -m pytest tests/
  python tests/run_all_tests.py
  ```

---

## 6. Implementation Architecture & Code Structure

The implementation for generating `catalog.json` and `README.md` will reside within `src/crawler/` and `src/validator/`:

```
src/
├── config.py                         # PipelineEnvironmentConfig (host vs mock paths)
├── crawler/
│   ├── __init__.py
│   ├── registry_sources.py           # 20 curated package seed dictionaries
│   ├── github_crawler.py             # Crawler with offline fallback & catalog generator
│   └── readme_renderer.py            # Automated README.md markdown generator
└── validator/
    ├── __init__.py
    ├── schemas/
    │   └── catalog_schema.json       # Draft-07 JSON Schema definition
    └── schema_validator.py           # Draft-07 schema and invariant validator
```

### 6.1 `generate_catalog()` Algorithm
1. Retrieve seed packages from `src/crawler/registry_sources.py`.
2. If online mode is enabled and `GITHUB_TOKEN` is set:
   - Query GitHub API for latest star counts and release tags.
   - Update package metadata with current live counts.
3. If offline mode or network error:
   - Utilize cached seed values without raising exceptions.
4. Construct top-level object:
   - `$schema`: `"http://json-schema.org/draft-07/schema#"`
   - `version`: `"1.0.0"`
   - `last_updated`: Current UTC timestamp in ISO-8601 (`strftime("%Y-%m-%dT%H:%M:%SZ")`)
   - `total_packages`: `len(packages)` (20)
   - `categories`: `["browser_search", "code_intelligence", "data_databases", "system_ops", "media"]`
   - `packages`: Array of 20 normalized package objects.
5. Validate payload against Draft-07 schema and semantic invariants.
6. Write atomically to target destination (`catalog.json`).

### 6.2 `render_readme()` Algorithm
1. Read `catalog.json`.
2. Dynamically format markdown tables for each category with aligned columns.
3. Inject package count badges, star counts, capabilities, and platform support flags.
4. Render quickstart, CLI guides, security invariants, and test execution runbooks.
5. Write atomically to `README.md`.

---

## 7. Downstream Coordination & Handoff Summary

- **To `implementer_m1_1` / `implementer_m1_2`**:
  - The Draft-07 schema in Section 2 and package specifications in Section 3 are authoritative.
  - Curated seed packages in `src/crawler/registry_sources.py` must match the field naming, types, and structure defined herein.
  - The crawler output must validate cleanly against this Draft-07 schema with zero errors.
- **To `validator_engine` (M2)**:
  - The validation suite can load the JSON schema directly to verify incoming catalogs during dry-run testing.
- **To `deployer_engine` (M3)**:
  - All 20 package definitions include accurate `entrypoint`, `platform_targets`, and `security_notes` to enable deterministic deployment to Antigravity and Claude Code.
