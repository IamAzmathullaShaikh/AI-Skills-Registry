# Comprehensive Technical Specification Survey: Antigravity Skills, MCP JSON-RPC & Target Environment Configurations

**Author**: `spec_miner_survey_1` (Teamwork Preview Spec Miner)  
**Date**: 2026-09-23  
**Status**: Authoritative Technical Reference  
**Working Directory**: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1`  

---

## 1. Executive Summary & Specification Scope

This document provides the foundational engineering specification and schema survey for building an automated discovery, validation, and multi-platform distribution pipeline for AI Model Skills and Model Context Protocol (MCP) servers.

The findings herein are derived directly from authoritative local runtime configurations, built-in customization engines (Google Antigravity IDE/CLI), Claude Code configuration stores, root rule files, and the official Model Context Protocol (MCP) JSON-RPC 2.0 specifications.

---

## 2. Antigravity SKILL.md Specification & Architecture

Antigravity skills are modular packages of procedures, domain runbooks, and tool workflows that extend an AI agent's capabilities on demand.

### 2.1 Package Directory Layout
A skill is packaged as a discrete directory located within a designated customization discovery path (e.g., `skills/<skill_name>/`).

```text
skills/<skill_name>/
├── SKILL.md          # MANDATORY: Entry point with YAML frontmatter + operational runbook
├── scripts/          # OPTIONAL: Executable helper scripts (sh, bash, ps1, py, js)
├── examples/         # OPTIONAL: Reference code implementations, sample queries, fixture data
├── resources/        # OPTIONAL: Static assets, schemas, templates, configurations
└── references/       # OPTIONAL: In-depth technical documentation, extended architecture guides
```

#### Directory Role Specifications:
1. **`SKILL.md` (Mandatory)**: Must reside at the root of the skill folder. Contains frontmatter parsed by the agent host for capability discovery and trigger evaluation, followed by concise human- and agent-readable procedural instructions.
2. **`scripts/` (Optional)**: Contains deterministic helper scripts that execute complex multi-step tasks. Must be linked relatively within `SKILL.md` (e.g., `[run.ps1](./scripts/run.ps1)`).
3. **`examples/` (Optional)**: Contains working sample inputs/outputs, sample configuration files, and code snippets demonstrating proper usage.
4. **`resources/` (Optional)**: Holds non-markdown static data files, such as JSON schemas, prompt templates, seed datasets, or binary assets.
5. **`references/` (Optional)**: Holds extended documentation and secondary manuals. Critical for the progressive disclosure pattern.

### 2.2 YAML Frontmatter Specification
The `SKILL.md` file **must** begin with a YAML frontmatter block enclosed between triple-dashed lines (`---`).

#### Exact Schema Definition:
```yaml
---
name: <identifier>
description: <activation_and_purpose_directive>
---
```

#### Field Constraints:
*   **`name`** (`string`, **required**):
    *   **Format**: Lowercase alphanumeric with hyphens or underscores (e.g., `opencut`, `agy-customizations`, `generative_ui`, `sqlite-inspector`).
    *   **Naming Rule**: Must uniquely identify the skill. Hyphenated kebab-case is standard; snake_case is accepted by parser. Must match or closely mirror the parent directory name.
*   **`description`** (`string`, **required**):
    *   **Format**: Plain text or YAML folded string (`>-` or `|`).
    *   **Semantic Requirement**: This field is the sole metadata inspected by the agent runtime during intent classification. It must explicitly declare:
        1. **What** the skill provides (capabilities and tools).
        2. **When** the agent must activate the skill (specific triggers, user intents, problem domains).
    *   **Perspective**: Must use third-person directive syntax (e.g., `"Comprehensive guide and reference for OpenCut... Use when the user asks about..."` or `"Activate this skill when the user asks questions about..."`).

### 2.3 Body Structure & Progressive Disclosure Pattern
To prevent context window saturation while allowing deep execution knowledge:
1. **Top-Level Structure**:
   * `# <Skill Title>`: Clean, concise heading.
   * `## Overview / Key Links`: High-level summary of the tool or library.
   * `## Core Capabilities & Features`: Numbered or bulleted list of operations.
   * `## Step-by-Step Procedures / Workflows`: Concrete instructions, CLI invocations, and parameters.
   * `## Verification / Validation Steps`: Instructions detailing how the agent independently verifies success (e.g., exit codes, output logs, dry runs).
   * `## When to Recommend / Decision Rules`: Criteria distinguishing this skill from alternatives.
   * `## Additional Documentation (Progressive Disclosure Pointer)`: Pointers to files in `references/`.
2. **Progressive Disclosure Rules**:
   * The root `SKILL.md` should remain compact (< 100 lines / ~2,500 words).
   * Detailed architectural RFCs, API references, database schemas, and edge case documents are moved to `references/<topic>.md`.
   * The agent loads the main `SKILL.md` when triggered, and only navigates to `references/*.md` via `view_file` when specifically required by a sub-task.

### 2.4 Antigravity Discovery Locations & Configuration
Antigravity discovers skills across three distinct scopes:
1. **Workspace Scope**:
   * `.agents/skills/` (or `.agent/skills/`, `_agents/skills/`, `_agent/skills/`) located at the repository/workspace root.
2. **Global User Scope**:
   * `~/.gemini/config/skills/<skill_name>/` (active across all sessions on the machine).
   * `~/.gemini/antigravity/skills/<skill_name>/` (managed installed skills).
   * `~/.gemini/antigravity/builtin/skills/<skill_name>/` (system built-in skills).
3. **Explicit JSON Registration (`skills.json`)**:
   Located at `~/.gemini/config/skills.json` or `.agents/skills.json`:
   ```json
   {
     "inherits": [
       {
         "path": "path/to/shared/skills.json",
         "include_only": ["skill-a"],
         "exclude": ["deprecated-.*"]
       }
     ],
     "entries": [
       {
         "path": "~/.gemini/config/skills",
         "exclude": ["experimental-.*"]
       }
     ]
   }
   ```
   * **Resolution Rules**:
     * Absolute paths start with `/` or drive letter (e.g., `C:/...`).
     * Home-relative paths start with `~/`.
     * Workspace-relative paths resolve against repository root.
     * Each directory entry is scanned **one level deep** for directories containing `SKILL.md`.

---

## 3. Model Context Protocol (MCP) JSON-RPC Specification

The Model Context Protocol (MCP) is an open standard governed by JSON-RPC 2.0 enabling bidirectional communication between LLM clients and local/remote tool servers.

### 3.1 JSON-RPC 2.0 Base Framing
Every MCP message must be a valid JSON-RPC 2.0 object.

#### Request Schema:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "<method_name>",
  "params": {}
}
```

#### Response Schema (Success):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {}
}
```

#### Response Schema (Protocol Error):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": null
  }
}
```

### 3.2 Protocol Lifecycle & Negotiation

#### 1. `initialize` (Request)
Sent by the client upon establishing transport connection:
```json
{
  "jsonrpc": "2.0",
  "id": "init-1",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {},
      "experimental": {}
    },
    "clientInfo": {
      "name": "AntigravityOrClaudeClient",
      "version": "1.0.0"
    }
  }
}
```

#### 2. `initialize` (Response)
Returned by the server declaring supported primitives:
```json
{
  "jsonrpc": "2.0",
  "id": "init-1",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true, "listChanged": true },
      "prompts": { "listChanged": true },
      "logging": {}
    },
    "serverInfo": {
      "name": "sqlite-mcp-server",
      "version": "0.4.1"
    }
  }
}
```

#### 3. `notifications/initialized`
Sent by client as a notification (`no "id"`) to confirm readiness:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

#### 4. `ping`
Heartbeat method supported by servers:
```json
{
  "jsonrpc": "2.0",
  "id": "ping-1",
  "method": "ping"
}
// Response: { "jsonrpc": "2.0", "id": "ping-1", "result": {} }
```

### 3.3 Core Primitives

#### 1. Tools Primitive (`tools/list` and `tools/call`)
*   **`tools/list` Request**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/list",
      "params": { "cursor": "optional-pagination-token" }
    }
    ```
*   **`tools/list` Response**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "result": {
        "tools": [
          {
            "name": "query_database",
            "description": "Execute a read-only SQL query against the connected database",
            "inputSchema": {
              "type": "object",
              "properties": {
                "sql": {
                  "type": "string",
                  "description": "The SELECT query to execute"
                },
                "limit": {
                  "type": "integer",
                  "description": "Max rows to return",
                  "default": 100
                }
              },
              "required": ["sql"]
            }
          }
        ],
        "nextCursor": null
      }
    }
    ```
*   **`tools/call` Request**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 3,
      "method": "tools/call",
      "params": {
        "name": "query_database",
        "arguments": {
          "sql": "SELECT id, name FROM users LIMIT 5;"
        }
      }
    }
    ```
*   **`tools/call` Response (`CallToolResult`)**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 3,
      "result": {
        "content": [
          {
            "type": "text",
            "text": "[{\"id\": 1, \"name\": \"Alice\"}, {\"id\": 2, \"name\": \"Bob\"}]"
          }
        ],
        "isError": false
      }
    }
    ```
*   **Tool Execution Error Semantics**:
    *   **Crucial Rule**: When a tool fails execution (e.g. invalid SQL syntax, database timeout, missing table), the server returns a successful JSON-RPC result containing `"isError": true` inside `result`, rather than an RPC-level error code. This enables the LLM to inspect the failure output and self-correct.

#### 2. Resources Primitive (`resources/list` and `resources/read`)
*   **`resources/list` Response**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 4,
      "result": {
        "resources": [
          {
            "uri": "postgres://localhost:5432/schema/public",
            "name": "Public Schema DDL",
            "description": "Table definitions for the public schema",
            "mimeType": "application/sql"
          }
        ]
      }
    }
    ```
*   **`resources/read` Request/Response**:
    ```json
    // Request: { "jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": { "uri": "postgres://localhost:5432/schema/public" } }
    // Response:
    {
      "jsonrpc": "2.0",
      "id": 5,
      "result": {
        "contents": [
          {
            "uri": "postgres://localhost:5432/schema/public",
            "mimeType": "application/sql",
            "text": "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);"
          }
        ]
      }
    }
    ```

#### 3. Prompts Primitive (`prompts/list` and `prompts/get`)
*   **`prompts/list` Response**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 6,
      "result": {
        "prompts": [
          {
            "name": "analyze_query_plan",
            "description": "Analyze an EXPLAIN output for performance bottlenecks",
            "arguments": [
              {
                "name": "query",
                "description": "The SQL query to explain",
                "required": true
              }
            ]
          }
        ]
      }
    }
    ```
*   **`prompts/get` Response**:
    ```json
    {
      "jsonrpc": "2.0",
      "id": 7,
      "result": {
        "description": "Plan analysis prompt",
        "messages": [
          {
            "role": "user",
            "content": {
              "type": "text",
              "text": "Please analyze the execution plan for: SELECT * FROM orders;"
            }
          }
        ]
      }
    }
    ```

### 3.4 Transports & Entry Points

MCP supports two primary transports:
1. **Stdio Transport (Standard Input/Output)**:
   * **Mechanism**: Host spawns a child process and communicates via NDJSON (Newline Delimited JSON) over `stdin` and `stdout`. `stderr` is reserved for debug logging.
   * **Entry Point Configuration**:
     * `command`: Executable binary or CLI runner (e.g., `uvx`, `npx`, `python`, `node`, `docker`).
     * `args`: Array of string arguments.
     * `env`: Key-value map of environment variables injected into the child process.
     * `cwd`: Optional working directory path.
2. **SSE / HTTP Transport (Server-Sent Events)**:
   * **Mechanism**: Host opens an SSE connection (`GET`) to receive server-to-client events and sends client-to-server requests via `POST`.
   * **Entry Point Configuration**:
     * `serverUrl` or `url`: HTTPS/HTTP endpoint URL.
     * `headers`: Key-value map of HTTP headers (e.g. `Authorization` or `X-API-Key`).

---

## 4. Target Environment Configuration Schemas

### 4.1 Google Antigravity Configuration
Antigravity supports MCP servers through global configuration and settings files.

#### Locations:
1. **Primary Global MCP Registry**:
   `C:\Users\BangerSoul\.gemini\config\mcp_config.json`
   * **Current State**: File exists (0 bytes).
   * **Schema**:
     ```json
     {
       "mcpServers": {
         "<server-name>": {
           "command": "<executable>",
           "args": ["<arg1>", "<arg2>"],
           "env": {
             "<VAR_NAME>": "<value>"
           }
         },
         "<remote-server-name>": {
           "serverUrl": "https://<host>/sse"
         }
       }
     }
     ```
2. **Settings Config**:
   `C:\Users\BangerSoul\.gemini\settings.json`
   * **Current State**: Contains active server `aws-mcp`:
     ```json
     {
       "mcpServers": {
         "aws-mcp": {
           "command": "uvx",
           "args": [
             "mcp-proxy-for-aws@latest",
             "https://aws-mcp.us-east-1.api.aws/mcp",
             "--metadata",
             "INSTALL_SOURCE=aws-cli"
           ],
           "env": {
             "AWS_MCP_PROXY_PROFILES": "agent-toolkit BangerSoul"
           }
         }
       }
     }
     ```
3. **Skills Discovery Config**:
   `C:\Users\BangerSoul\.gemini\config\skills.json`
   * **Current Content**:
     ```json
     {
       "entries": [
         {
           "path": "~/.gemini/config/skills"
         }
       ]
     }
     ```

### 4.2 Claude Code / Freebuff Desktop Configuration
Claude Code and Freebuff Desktop manage global preferences, telemetry, tips, plugins, and MCP servers in a single persistent JSON file.

#### Location:
`C:\Users\BangerSoul\.claude.json`

#### Existing Contents Analysis:
* Total Lines: 1,364 lines (52,000 bytes).
* Contains sensitive state including:
  * Approved/rejected custom API keys (`customApiKeyResponses`)
  * Feature flags (`cachedGrowthBookFeatures`)
  * Command tip counters (`tipsHistory`, `tipsHistoryByCommand`)
  * Active MCP server: `tinyfish` (lines 1323–1331):
    ```json
    "mcpServers": {
      "tinyfish": {
        "type": "http",
        "url": "https://agent.tinyfish.ai/mcp?source=tinyfish_cli&client=claude-code&connect_attempt_id=0e304406-54b0-40b9-8ad3-d4a2b4f4ba06",
        "headers": {
          "X-API-Key": "sk-tinyfish-XF3WGyHrnMiULqKTZWQ4vk8IONL-DIfO"
        }
      }
    }
    ```

#### Non-Destructive Merging Rules for `.claude.json`:
1. **Never Overwrite the Whole File**: The file must never be replaced with an MCP-only template.
2. **Atomic In-Memory Mutation**:
   * Read full file content using UTF-8 encoding.
   * Parse with standard JSON parser.
   * If key `mcpServers` does not exist, initialize it as `{}`.
   * For each new validated server:
     * Check if key already exists. If it exists and has custom credentials (like `tinyfish`), preserve existing credentials unless explicitly updating.
     * Assign server definition under its unique key.
   * Reserialize entire object with `indent=2`.
   * Write to a temporary file (`.claude.json.tmp`) and atomically rename/replace `C:\Users\BangerSoul\.claude.json`.
3. **Transport Field Mapping for Claude Code**:
   * Stdio servers:
     ```json
     "<server-name>": {
       "command": "uvx" | "npx" | "python" | "node",
       "args": [...],
       "env": { ... }
     }
     ```
   * Remote/HTTP servers:
     ```json
     "<server-name>": {
       "type": "http",
       "url": "https://...",
       "headers": { ... }
     }
     ```

### 4.3 Model Rule Files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`)
Rule files provide persistent, ambient instructions that govern model decision-making across directories and sessions.

#### Physical Locations & Existing Scope:
1. `C:\Users\BangerSoul\AGENTS.md` (85 lines / 7,541 bytes):
   * Contains AWS Guidance for the new AWS experience (Regions, spending limits, SCP/RCP rules, help levels).
   * Contains Crave Builder directive (prohibits heavy builds on Windows, directs to `crave.exe`).
2. `C:\Users\BangerSoul\CLAUDE.md` (50 lines / 4,604 bytes):
   * Contains Core Implementation Directive ("boil the ocean", full implementations, no TODO stubs).
   * Contains Agent Workflow & Execution Strategy (search first, test-driven perfection, documentation).
   * Contains Crave Builder directive.
3. `C:\Users\BangerSoul\GEMINI.md` (76 lines / 6,656 bytes):
   * Contains AWS Guidance for the new AWS experience.

#### Technical Constraints & Budget Rules:
*   **Per-File Size Limit**: Capped at **24,000 bytes** (24 KB). Any file exceeding this cap is truncated on line boundaries by the runtime loader.
*   **Aggregate Rules Budget**: Maximum **20,000 tokens**. If total active rules across directory hierarchy exceed this budget, rules are demoted to file path pointers.
*   **Markdown Structure**: Standalone rule files **do not** use YAML frontmatter. Content is loaded directly as active system instructions.

#### Task-Based Routing Specification for Model Rules:
To route user requests intelligently without saturating token context, routing instructions must be injected as a compact, high-density Markdown table.

```markdown
<!-- BEGIN AI-SKILLS-REGISTRY TASK ROUTING -->
# Installed Skills & MCP Tool Routing Directives

When addressing user requests in the following domains, prefer activating the designated skill or MCP server:

| Domain / Task Type | Recommended Skill / MCP Tool | Activation Method | Key Capability |
| :--- | :--- | :--- | :--- |
| **Browser Video Editing** | `opencut` skill | Skill: `opencut` | Timeline editing, WASM processing, watermark-free export |
| **SQLite Databases** | `sqlite-mcp` | MCP: `query_database` | Inspect schema, execute read queries, analyze tables |
| **Web Research & Fetch** | `fetch-mcp` | MCP: `fetch` | Convert web URLs to markdown, crawl documentation |
| **Git & GitHub Operations** | `github-mcp` | MCP: `search_repositories` | Query issues, search PRs, inspect repositories |
| **Filesystem Operations** | `filesystem-mcp` | MCP: `read_file`, `list_directory`| Safe local directory traversal and file inspection |

### Directive Rules:
1. Only call tools specifically relevant to the current user objective.
2. Read `SKILL.md` before executing unfamiliar multi-step procedures.
3. Keep tool outputs focused to conserve conversation context budget.
<!-- END AI-SKILLS-REGISTRY TASK ROUTING -->
```

---

## 5. Specification Mining Tables

### Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Antigravity Skill | YAML Frontmatter `name` | Unique identifier for skill (lowercase kebab-case/snake_case) | String | Identifier string | Parse error / ignored if missing | `~/.gemini/antigravity/builtin/skills/agy-customizations/docs/skills.md` |
| 2 | Antigravity Skill | YAML Frontmatter `description` | Primary activation and purpose trigger evaluated by host agent | String (third-person directive) | Intent classification weight | Agent fails to activate skill if unclear or missing | `skills.md` & `opencut/SKILL.md` |
| 3 | Antigravity Skill | `references/` Subdirectory | Progressive disclosure store for bulky architecture/manuals | Markdown files | Context loaded on demand | None (graceful fallback) | `skills.md` & `opencut/references/` |
| 4 | Antigravity Skill | `scripts/` Subdirectory | Executable helper scripts for complex automation | Shell/PowerShell/Python scripts | Execution results/logs | Non-zero exit code caught by agent | `skills.md` |
| 5 | Antigravity Skill | `skills.json` Manifest | Customization path registration with include/exclude filters | JSON schema (`entries`, `inherits`) | Registered skill paths | Malformed JSON throws load warning | `~/.gemini/antigravity/builtin/skills/agy-customizations/docs/json_configs.md` |
| 6 | MCP JSON-RPC | `initialize` Lifecycle | Handshake negotiating protocol version and capabilities | `protocolVersion`, `capabilities`, `clientInfo` | `capabilities`, `serverInfo` | Protocol handshake failure / disconnect | MCP Specification / `modelcontextprotocol.io` |
| 7 | MCP JSON-RPC | `tools/list` Primitive | Discovers available tools and JSON Schema parameter definitions | Optional `cursor` | Array of tools with `inputSchema` | Protocol error code if unsupported | MCP Specification |
| 8 | MCP JSON-RPC | `tools/call` Primitive | Invocates a specific server tool with structured arguments | `name`, `arguments` object | `content` array (text/image) + `isError` boolean | Tool execution errors return `isError: true` inside result | MCP Specification |
| 9 | MCP JSON-RPC | `resources/list` & `read` | Read-only context and document inspection via URI scheme | Resource URI string | Descriptors or file `contents` | URI not found error | MCP Specification |
| 10 | MCP JSON-RPC | `prompts/list` & `get` | Discover and retrieve parameterized prompt templates | Prompt name + arguments | Structured message array | Prompt not found error | MCP Specification |
| 11 | MCP Transport | Stdio Transport | Local subprocess execution over stdin/stdout NDJSON | `command`, `args`, `env`, `cwd` | Process stdio stream | Process spawn error / non-zero exit | `mcp_servers.md` |
| 12 | MCP Transport | SSE / HTTP Transport | Remote HTTP communication via Server-Sent Events | `serverUrl` / `url`, `headers` | SSE event stream | HTTP error status (4xx/5xx) | `mcp_servers.md` |
| 13 | Antigravity Config | `mcp_config.json` | Global MCP registry for Google Antigravity sessions | JSON map of `mcpServers` | Registered agent toolset | Syntax error ignores file | `~/.gemini/config/mcp_config.json` |
| 14 | Antigravity Config | `settings.json` | Runtime settings storing active MCP servers (e.g. `aws-mcp`) | JSON map of `mcpServers` | Active tools in session | Corrupt JSON breaks settings load | `~/.gemini/settings.json` |
| 15 | Claude Code Config | `.claude.json` `mcpServers` | Claude Code persistent registry for stdio & http MCP tools | JSON dictionary of server configs | Registered MCP tools in Claude | JSON syntax error corrupts settings | `C:\Users\BangerSoul\.claude.json` |
| 16 | Model Rules | Rule File Truncation Cap | Enforces max 24,000 bytes per rule file (`GEMINI.md`/`AGENTS.md`) | Rule markdown files | Truncated markdown on line boundary | Content past 24 KB silently truncated | `~/.gemini/antigravity/builtin/skills/agy-customizations/docs/rules.md` |
| 17 | Model Rules | Aggregate Token Budget | Enforces 20,000 token ceiling across all active rule files | Total rule tokens | Full text or demoted path pointers | Over-budget rules demoted to path pointers | `rules.md` |

### Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Antigravity `mcp_config.json` | File size is 0 bytes (empty file) | Parser treats empty file as uninitialized; does not throw crash, but requires clean JSON object `{ "mcpServers": {} }` before inserting entries. |
| 2 | Claude Code `.claude.json` | Existing active server (`tinyfish`) with sensitive API keys | Naive overwriting erases `tinyfish` API key; non-destructive dictionary merging preserves existing servers and keys. |
| 3 | MCP `tools/call` error | Invalid tool parameter or execution failure | Must return `{ "content": [...], "isError": true }` within result. Throwing JSON-RPC protocol error prevents LLM self-correction. |
| 4 | SKILL.md Frontmatter | Missing `description` field | Skill is ignored or unusable by LLM router because host cannot evaluate intent activation triggers. |
| 5 | Model Rule File Size | File larger than 24,000 bytes | Host truncates file at line boundary nearest to 24,000 bytes; directives located at the bottom are discarded. |
| 6 | MCP Server Stdio on Windows | Command using `.cmd` or `.bat` wrapper (e.g., `npx`, `uvx`) | On Windows, executing shell scripts or wrappers without full path or shell resolution can cause `ENOENT` spawn failure; prefer binary executable names (`npx.cmd`, `uvx.exe`) or PATH-resolved commands. |
| 7 | Path Resolution in `skills.json` | `~/` on Windows vs Linux | `~/` expands to user profile directory (`C:\Users\BangerSoul`); forward slashes are normalized by runtime. |

---

## 6. Implementation Guidelines for Downstream Agents

1. **For Schema Validator (`validator_pipeline`)**:
   * Implement strict checks for `name` (regex: `^[a-z0-9_-]+$`) and `description` (non-empty string, min 20 chars).
   * Verify that every MCP server config contains either (`command` string) or (`serverUrl`/`url` string).
2. **For Cataloger / Discoverer (`discoverer_pipeline`)**:
   * Index metadata including: name, category, description, license, transport type, parameters schema.
3. **For Multi-Platform Installer (`installer_pipeline`)**:
   * Write skills to `C:\Users\BangerSoul\.gemini\config\skills\<name>\SKILL.md`.
   * Safely merge MCP configurations into `C:\Users\BangerSoul\.gemini\config\mcp_config.json` and `C:\Users\BangerSoul\.claude.json`.
   * Append formatted routing directives to `C:\Users\BangerSoul\AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` within designated delimiters.
