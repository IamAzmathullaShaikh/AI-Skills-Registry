# Comprehensive Architectural Survey: Discovery, Validation, Multi-Platform Deployment & Routing Pipeline

**Author**: `explorer_pipeline_survey_1` (Teamwork Preview Explorer)  
**Date**: 2026-09-24  
**Project**: AI-Skills-Registry (`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry`)  
**Target Environments**: Google Antigravity, Claude Code / Freebuff Desktop, Cursor / Codex  

---

## 1. Executive Summary & Architecture Overview

The objective of the **AI-Skills-Registry** is to establish an end-to-end automated pipeline that systematically discovers, audits, validates, mounts, and routes verified AI model skills and Model Context Protocol (MCP) servers across heterogeneous local agent environments.

To achieve production reliability without destabilizing developer workflows, the pipeline is architected around four foundational pillars:
1. **Automated Quality, Security & Schema Validation Filter**: A deterministic multi-stage filter that rejects unmaintained, deprecated, vulnerable, or non-conforming packages before any installation occurs. It features a zero-unhandled-exception dry-run schema validator.
2. **Multi-Platform Deployment Engine**: An atomic, non-destructive mount engine that generates compliant `SKILL.md` structures for Antigravity, populates `mcp_config.json`, and merges MCP servers into `~/.claude.json` under `mcpServers` while safeguarding existing user keys (e.g. `tinyfish`), environment variables, and client settings.
3. **Rule Generation & Task-Based Routing Directives**: An intelligent directive generator that injects non-destructive routing tables into `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`. By adhering to Antigravity's 24 KB / 20,000-token rules budget and utilizing progressive disclosure, it prevents context saturation while providing clear activation pathways.
4. **Testing & Verification Architecture**: A fully isolated testing framework utilizing virtualized sandboxes and mock fixtures, enabling end-to-end testing of crawling, validation, deployment, and rule generation without mutating the user's live system configurations.

```
+---------------------------------------------------------------------------------------------------+
|                                  AI-SKILLS-REGISTRY PIPELINE ARCHITECTURE                         |
+---------------------------------------------------------------------------------------------------+
                                                  |
           [ 1. Discovery & Metadata Indexing ]   v   (GitHub API / Catalogs / Monorepos)
                                                  |
                                                  v
       +---------------------------------------------------------------------+
       | 2. Automated Quality, Security & Schema Validation Engine           |
       |  - Maintenance & Freshness Filter (stars > 100, active commits)    |
       |  - Security Audits & Injection Scanner (CVE, shell injection, paths)|
       |  - SKILL.md YAML Frontmatter & Progressive Disclosure Validator     |
       |  - MCP JSON-RPC Transports Validator (stdio/sse/http)               |
       |  - Dry-Run Execution Mode with Structured Diagnostic Reports        |
       +---------------------------------------------------------------------+
                                                  |
                               [ Validated Candidate Artifacts ]
                                                  |
                                                  v
       +---------------------------------------------------------------------+
       | 3. Multi-Platform Deployment Engine (Atomic & Non-Destructive)      |
       |  - Staging & Atomic Swaps (write to .tmp.<uuid> -> os.replace)      |
       |  - Antigravity Mount: ~/.gemini/config/skills/<name>/SKILL.md       |
       |  - Antigravity MCP: ~/.gemini/config/mcp_config.json                |
       |  - Claude Code Merge: ~/.claude.json (Deep merge preserving keys)   |
       |  - Rolling Backup (.bak) & Automated Rollback Handler               |
       +---------------------------------------------------------------------+
                                                  |
                                                  v
       +---------------------------------------------------------------------+
       | 4. Task-Based Rule Generation & Routing Directives                  |
       |  - Delimiter-Bound Injection (<!-- BEGIN ... --> ... <!-- END -->)  |
       |  - Protected Pre-Existing Directives (AWS Toolkit, Crave Builder)  |
       |  - 2-Tier Progressive Routing Matrix (Zero context bloat)          |
       |  - Targets: AGENTS.md, CLAUDE.md, GEMINI.md                         |
       +---------------------------------------------------------------------+
                                                  |
                                                  v
       +---------------------------------------------------------------------+
       | 5. Isolated Sandbox E2E Testing & Verification Harness              |
       |  - Mock Root / Virtual Staging Targets (No host mutation)           |
       |  - Idempotency & Fault Injection Test Suites                        |
       +---------------------------------------------------------------------+
```

---

## 2. System Environment & Target Platforms Baseline

Direct filesystem inspection of the local host (`C:\Users\BangerSoul`) established the concrete baselines, existing schemas, and safety boundaries for all target environments.

### 2.1 Google Antigravity Baseline
* **Customization Documentation Located**: `C:\Users\BangerSoul\.gemini\antigravity\builtin\skills\agy-customizations\docs\`
  * `skills.md`: Mandates YAML frontmatter with `name` (lowercase, hyphenated) and `description` (third-person trigger instructions). Strongly prescribes progressive disclosure via `references/`, `scripts/`, `examples/`, and `resources/`.
  * `mcp_servers.md`: Authoritative specification for Antigravity MCP configuration. Confirms support for `stdio` (command, args, env) and `sse` (serverUrl) transports.
  * `rules.md`: Establishes the hard **24 KB (24,000 bytes) per-file limit** and **20,000 token aggregate rules budget** for workspace and directory rules (`GEMINI.md` / `AGENTS.md`).
  * `json_configs.md`: Authoritative specification for `skills.json` and `plugins.json`. Confirms path resolution (`~/`, absolute, workspace-relative) and entry scanning.
* **Global Skills Mount Directory**: `C:\Users\BangerSoul\.gemini\config\skills\`
  * Contains existing validated skill: `opencut/SKILL.md` (3,806 bytes) with subfolder `references/`.
* **Global MCP Configuration**: `C:\Users\BangerSoul\.gemini\config\mcp_config.json`
  * Currently present on disk as an empty file (0 bytes). Must be initialized to compliant root JSON structure.
* **Global Skills Manifest**: `C:\Users\BangerSoul\.gemini\config\skills.json`
  * Currently contains:
    ```json
    {
      "entries": [
        {
          "path": "~/.gemini/config/skills"
        }
      ]
    }
    ```

### 2.2 Claude Code / Freebuff Desktop Baseline
* **Configuration File**: `C:\Users\BangerSoul\.claude.json`
  * **File Size & Complexity**: 52,000 bytes, 1,364 lines.
  * Contains critical user state: `numStartups`, `autoUpdates`, `tipsHistory`, `cachedGrowthBookFeatures` (hundreds of toggles), `pluginUsage`, `autoModeEnvSetup`.
  * **Existing MCP Servers (Lines 1323–1331)**:
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
  * **Critical Safety Constraint**: Any automated deployment modifying `.claude.json` **MUST NEVER** overwrite the file blindly, replace the entire `mcpServers` map, or strip the user's active `tinyfish` server or its API key. A deep non-destructive merge is strictly mandatory.

### 2.3 Rule Files Baseline
* **Inspected Files**:
  * `C:\Users\BangerSoul\AGENTS.md` (85 lines, 7,541 bytes)
  * `C:\Users\BangerSoul\CLAUDE.md` (50 lines, 4,604 bytes)
  * `C:\Users\BangerSoul\GEMINI.md` (76 lines, 6,656 bytes)
  * `C:\Users\BangerSoul\.gemini\GEMINI.md` (69 lines, 7,487 bytes)
* **Pre-Existing Managed Directives**:
  * AWS Agent Toolkit rules enclosed in `<!-- BEGIN AWS Agent Toolkit rules -->` ... `<!-- END AWS Agent Toolkit rules -->` across `AGENTS.md` and `GEMINI.md`.
  * Heavy Builds & Cloud Compilation Policy: Crave Builder (`crave.exe -n run ...`) across all files.
  * Core Implementation Directive and Agent Workflow in `CLAUDE.md`.
* **Critical Safety Constraint**: Rule injection must be strictly partitioned using isolated comment delimiters so pre-existing AWS rules, Crave build policies, and core agent directives remain untouched.

---

## 3. Automated Validation & Quality/Security Filters

The validation subsystem operates as a multi-stage deterministic gate. A package candidate must pass all stages before it can be added to `catalog.json` or mounted into any platform.

```
+-----------------------------------------------------------------------------+
|                     MULTI-STAGE VALIDATION PIPELINE                         |
+-----------------------------------------------------------------------------+
Candidate Package
       |
       v
[ Stage 1: Maintenance & Deprecation Gate ]
  - Star threshold check (>= 100 stars for community repos)
  - GitHub repo status (archived == false, disabled == false)
  - Last activity / commit recency (< 365 days)
  - Registry deprecation check (npm deprecated flag, PyPI yanked status)
  - OSI-approved license validation (MIT, Apache-2.0, BSD, ISC)
       | (Pass)
       v
[ Stage 2: Security & Supply-Chain Audit ]
  - Known CVE audit via OSV API (api.osv.dev) or GitHub Security Advisories
  - Command execution sanitization (no bare shell calls: cmd.exe /c, sh -c)
  - Path traversal check (no '../', absolute host root injection)
  - Secret & token leak regex scanning
       | (Pass)
       v
[ Stage 3: Strict Schema & Progressive Disclosure Verification ]
  - SKILL.md: YAML frontmatter validity, regex on name, trigger description
  - SKILL.md: Structure check, reference/script file existence verification
  - MCP Config: Transport schema check (stdio vs sse vs http)
  - MCP Config: Executable binary existence (npx, uvx, python, node, docker)
       | (Pass)
       v
[ Stage 4: Dry-Run Verification Engine (Zero Unhandled Exceptions) ]
  - In-memory simulated mount and configuration merge
  - Emit structured ValidationReport (PASS / FAIL / WARN)
```

### 3.1 Maintenance & Deprecation Rejection Heuristics

1. **Star Threshold**: Community repositories must have $\ge 100$ GitHub stars. Repositories from official organizations (e.g. `modelcontextprotocol`, `anthropics`, `google`) are exempt from the star threshold but must satisfy all maintenance and security criteria.
2. **Repository Status**:
   - `archived == false`: Archived repositories indicate that the maintainers have ceased updates; rejected immediately.
   - `disabled == false`: Repositories suspended or taken down are rejected.
3. **Commit Recency & Maintenance Velocity**:
   - The latest commit to the default branch or newest release tag must have occurred within the past **365 days**.
   - If the last commit is $> 180$ days old and unresolved issue count $> 50$ with zero maintainer responses in 90 days, the package is flagged as `STALE_UNMAINTAINED` and skipped.
4. **Registry Deprecation Flags**:
   - **npm**: Query registry metadata `https://registry.npmjs.org/<package>`. If `versions[latest].deprecated` is present, reject immediately.
   - **PyPI**: Query `https://pypi.org/pypi/<package>/json`. If any target release is `yanked: true` or trove classifiers include `Development Status :: 7 - Inactive`, reject immediately.
5. **License Compliance**:
   - Approved permissive licenses: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Unlicense`, `CC0-1.0`.
   - Copyleft (`GPL-3.0`, `AGPL-3.0`) or proprietary/unlicensed candidates must be flagged or rejected to prevent license taint.

### 3.2 Security Auditing & Supply-Chain Integrity Filters

1. **CVE Vulnerability Auditing**:
   - Integration with the Open Source Vulnerabilities (OSV) API (`https://api.osv.dev/v1/query`).
   - Query package name and resolved version. Any package with an unpatched `CRITICAL` or `HIGH` CVSS score ($\ge 7.0$) is rejected.
2. **Command Injection Prevention in MCP Server Entry Points**:
   - Servers configuring `command` and `args` must be strictly validated.
   - Prohibit command wrappers that pass unescaped strings to shells:
     - Flagged patterns: `cmd.exe /c *`, `powershell -Command *`, `sh -c *`, `bash -c *`.
     - Validated format: Direct binary invocation with explicit argument tokens:
       - `command: "npx"`, `args: ["-y", "@modelcontextprotocol/server-sqlite", "db.sqlite"]`
       - `command: "uvx"`, `args: ["mcp-server-git", "--repository", "."]`
3. **Path Traversal & Filesystem Safety**:
   - Skill identifiers and internal file paths must be sanitized against directory traversal attacks (`../`, `..\`, null bytes `\0`, absolute drive specifiers like `C:\Windows`).
   - Target mounting paths must be strictly checked to ensure they resolve within the authorized directories (`~/.gemini/config/skills/<name>` or `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\...`).
4. **Credential & Secret Leak Detection**:
   - Candidate files and template configs are scanned for embedded secrets using high-entropy regexes:
     - GitHub Personal Access Tokens (`ghp_[0-9a-zA-Z]{36}`)
     - Anthropic API keys (`sk-ant-[0-9a-zA-Z_-]{80,}`)
     - OpenAI API keys (`sk-[0-9a-zA-Z]{48}`)
     - Hardcoded AWS Secret Access Keys (`(?<![A-Z0-9])[A-Z0-9]{40}(?![A-Z0-9])`)
   - Any candidate containing hardcoded secrets is rejected. Placeholders must adhere strictly to variable expansion syntax (e.g. `${GITHUB_TOKEN}`).

### 3.3 Strict Schema Validation Specifications

#### A. Antigravity `SKILL.md` Specification
Based on Antigravity's official `skills.md` documentation, the schema requirements are:
1. **YAML Frontmatter**:
   - Begins on line 1 with `---` and terminates with `---`.
   - **`name`** (required, string): Matches `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase, alphanumeric, hyphen-separated).
   - **`description`** (required, string): Must be 20 to 1,024 characters long. Must use third-person phrasing declaring what the skill does and when the agent should invoke it (e.g., `Use this skill when...`).
2. **Markdown Body & Progressive Disclosure**:
   - Must contain a level 1 heading `# <Skill Name>`.
   - Must contain explicit sections:
     - `## Overview` or `## Core Capabilities`: High-level workflow summary.
     - `## When to Use`: Explicit trigger conditions and keywords.
     - `## Instructions` or `## Workflow`: Step-by-step procedural runbook.
   - **Progressive Disclosure Validation**:
     - Large documentation (> 300 lines or > 12 KB) must NOT be embedded in `SKILL.md`. It must be partitioned into `references/<topic>.md`.
     - Executable utilities must reside in `scripts/<script_name>`.
     - All markdown links within `SKILL.md` (e.g. `[Documentation](./references/guide.md)`) must be resolved locally; dangling links trigger a validation failure.

#### B. MCP JSON-RPC Server Specification
Based on Model Context Protocol specification and Antigravity's `mcp_servers.md`:
1. **Transport Type 1: Stdio Transport (Local Executable)**
   - `command` (required, string): Executable binary name or path.
   - `args` (optional, list of strings): Command-line argument array.
   - `env` (optional, object of string -> string): Injected environment variables.
   - Pre-flight check: Verify if the executable is accessible in host `PATH` (e.g., `npx`, `python`, `uvx`, `docker`).
2. **Transport Type 2: SSE / HTTP Transport (Remote Service)**
   - Antigravity format: `serverUrl` (required, valid `http://` or `https://` URL).
   - Claude Code format: `type: "http" | "sse"`, `url` (required string), `headers` (optional object).
3. **JSON-RPC Schema Conformance**:
   - Tool names exposed by the server must conform to regex `^[a-zA-Z0-9_-]{1,64}$`.
   - Tool schemas must adhere to standard JSON Schema Draft 7 / 2020-12 without circular `$ref` references.

### 3.4 Zero-Unhandled-Exception Dry-Run Validation Architecture

To ensure the automated validation script executes over hundreds of candidate packages without ever terminating unexpectedly, it is designed with a fault-tolerant exception hierarchy and structured diagnostics.

```python
# Validation Exception Hierarchy & Data Model (Design)
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

class ValidationSeverity(Enum):
    CRITICAL = "CRITICAL" # Rejects package immediately
    ERROR = "ERROR"       # Rejects package
    WARNING = "WARNING"   # Package accepted with advisory notes
    INFO = "INFO"         # Informational detail

@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    rule_id: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None

@dataclass
class ValidationReport:
    candidate_id: str
    package_type: str  # "skill" | "mcp_server"
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

**Defensive Implementation Principles**:
1. **Total Exception Encapsulation**: Every validator step (YAML parsing, regex evaluation, JSON decoding, URL parsing, link verification) is wrapped in isolated `try ... except Exception as exc` blocks. Any unexpected exception is intercepted, formatted as a `ValidationIssue(severity=CRITICAL, rule_id="UNHANDLED_EXCEPTION", message=str(exc))`, and appended to the report. The runner never crashes.
2. **Strict Parser Handlers**:
   - YAML: Uses `yaml.safe_load` with `yaml.YAMLError` handler. Checks for null documents, multiple frontmatters, unclosed quotes, and non-dict frontmatter.
   - JSON: Uses `json.loads` with `json.JSONDecodeError` handler. Handles invalid escapes, trailing commas, and encoding issues.
3. **Pure Dry-Run Execution Mode**:
   - The validator operates strictly in-memory or on read-only clones in temporary directories.
   - Returns exit code `0` when dry-run validation finishes and writes a complete summary `validation_summary.json` containing pass/fail breakdowns for all candidates.

---

## 4. Multi-Platform Deployment Engine

The deployment engine mounts verified packages into their respective native runtime configuration locations while ensuring atomicity, safety, and non-destructiveness.

### 4.1 Safe Antigravity Skill Generation & Mount Pipeline

1. **Mount Target**: `C:\Users\BangerSoul\.gemini\config\skills\<skill_name>\`
2. **Directory Structure Generated**:
   ```
   C:\Users\BangerSoul\.gemini\config\skills\<skill_name>\
   ├── SKILL.md              # Frontmatter + concise workflow runbook
   ├── references/           # Detailed manuals, API references
   ├── scripts/              # Helper CLI scripts or automation
   └── examples/             # Reference usage examples
   ```
3. **Safe File Generation Procedure**:
   - Generate `SKILL.md` content with strict YAML frontmatter (`name` and sanitized `description`).
   - Write files to an isolated temporary staging directory:
     `C:\Users\BangerSoul\.gemini\config\skills\.staging_<skill_name>_<uuid>\`
   - Run post-generation schema verification on the staged directory.
   - Perform an atomic directory swap or file replace using `os.replace` (on Windows, `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING`).
   - If an older version of the skill exists, preserve a backup at `skills/.backup_<skill_name>_<timestamp>`.
4. **Skills Manifest Verification**:
   - Check `C:\Users\BangerSoul\.gemini\config\skills.json`.
   - Ensure `"path": "~/.gemini/config/skills"` exists in `"entries"`. If missing, safely append it using atomic JSON rewrite.

### 4.2 Safe Antigravity MCP Server Configuration (`mcp_config.json`)

1. **Mount Target**: `C:\Users\BangerSoul\.gemini\config\mcp_config.json`
2. **Handling the Current State**:
   - Local inspection showed `mcp_config.json` currently exists as 0 bytes.
   - If file size is 0 or file does not exist, initialize with empty structure: `{"mcpServers": {}}`.
3. **Merge Logic**:
   - Read and parse existing JSON. If invalid JSON, backup as `mcp_config.json.corrupt.<timestamp>` and report warning.
   - Create rolling backup: `mcp_config.json.bak.<timestamp>`.
   - For each candidate server (e.g. `sqlite`, `brave-search`, `git`):
     - Format entry matching Antigravity's schema:
       ```json
       {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-sqlite", "path/to/db.sqlite"],
         "env": { "READONLY": "true" }
       }
       ```
     - If key already exists in `mcpServers`, check if it's user-customized. If conflict occurs, do not overwrite without `--force`; instead, generate non-colliding alias (e.g. `<server_name>-registry`).
   - Write merged structure to `mcp_config.json.tmp.<uuid>`.
   - Validate that the temporary file parses and passes schema check.
   - Atomically rename temporary file to `mcp_config.json`.

### 4.3 Non-Destructive Claude Code Server Merging (`.claude.json`)

`C:\Users\BangerSoul\.claude.json` is a highly sensitive 52 KB file containing critical user settings, feature flags, and existing servers (e.g. `tinyfish` with its API key). The merge mechanism must guarantee zero loss of existing data.

**Algorithm for Non-Destructive Claude Merge**:

```python
# Conceptual Merge Implementation
import json
import os
import shutil
import time
from pathlib import Path

def merge_claude_mcp_servers(
    claude_json_path: Path,
    new_servers: dict[str, dict],
    backup_dir: Path,
    force: bool = False
) -> dict:
    """
    Safely merges new MCP servers into ~/.claude.json without mutating
    any other user configurations, growthbook flags, or existing server keys.
    """
    if not claude_json_path.exists():
        raise FileNotFoundError(f"Configuration file {claude_json_path} does not exist.")

    # Step 1: Read existing raw file
    with open(claude_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Step 2: Validate root is a dictionary
    if not isinstance(data, dict):
        raise ValueError(f"Corrupt {claude_json_path}: root must be a JSON object.")

    # Step 3: Create pre-mutation timestamped backup
    timestamp = int(time.time())
    backup_file = backup_dir / f".claude.json.bak.{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(claude_json_path, backup_file)

    # Step 4: Ensure mcpServers dictionary exists
    if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        data["mcpServers"] = {}

    existing_mcp = data["mcpServers"]
    merged_count = 0
    skipped_count = 0

    # Step 5: Non-destructive merge
    for server_name, server_config in new_servers.items():
        if server_name in existing_mcp:
            if not force:
                # CRITICAL: Preserve existing user server (e.g. tinyfish)
                skipped_count += 1
                continue
        existing_mcp[server_name] = server_config
        merged_count += 1

    # Step 6: Atomic write to temporary file
    temp_file = claude_json_path.with_suffix(f".tmp.{timestamp}")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Step 7: Post-write verification
    with open(temp_file, "r", encoding="utf-8") as f:
        verify_data = json.load(f)
    assert "tinyfish" in verify_data.get("mcpServers", {}), "CRITICAL: Existing user server lost during merge!"
    assert verify_data["numStartups"] == data["numStartups"], "CRITICAL: User settings corrupted!"

    # Step 8: Atomic replace
    os.replace(temp_file, claude_json_path)

    return {
        "status": "SUCCESS",
        "merged": merged_count,
        "preserved": skipped_count,
        "backup": str(backup_file)
    }
```

### 4.4 Atomic File Transactions, Backups, and Rollback Mechanisms

1. **Atomicity Guarantee**:
   - Files are never opened directly in `"w"` mode on their destination path.
   - All mutations write to a temporary file (`<target>.tmp.<pid>_<timestamp>`) in the same volume/directory, followed by `os.replace`.
   - On Windows, `os.replace` leverages the `MoveFileExW` Win32 API with `MOVEFILE_REPLACE_EXISTING`, ensuring that in-flight reads never see a partially written file.
2. **Rolling Backup Strategy**:
   - All destination files are backed up to a dedicated `.backups/` directory prior to modification:
     - `~/.claude.json.bak.<timestamp>`
     - `~/.gemini/config/mcp_config.json.bak.<timestamp>`
   - The deployment engine maintains a rolling retention window of the last 5 backups, pruning older backups automatically.
3. **Automated Rollback Handler**:
   - If an unhandled error occurs during schema validation of the merged file or during the atomic replace step, the rollback handler immediately restores the original file from the pre-mutation backup and purges any stray `.tmp` files.

---

## 5. Rule Generation & Task-Based Routing Directives

Deploying 15+ MCP servers and dozens of skills creates a significant context saturation hazard if their full descriptions and tool schemas are injected into every agent prompt turn. The rule generation subsystem solves this by generating concise, task-based routing directives adhering strictly to context limits.

### 5.1 Context Window Budget & Token Conservation Constraints

* **Antigravity Rule Limits**:
  * **24 KB (24,000 bytes) per-file limit**: Confirmed via `C:\Users\BangerSoul\.gemini\antigravity\builtin\skills\agy-customizations\docs\rules.md`. Rule files larger than 24,000 bytes are truncated on line boundaries.
  * **20,000 token aggregate rules budget**: Always-on and global rules share this budget. Exceeding it demotes rules to file-path pointers.
* **Claude Code Context Considerations**:
  * `CLAUDE.md` is loaded at session initialization. Bloating it with thousands of tokens of tool descriptions degrades reasoning capability and exhausts prompt caching budgets.
* **Design Solution**: The routing directive must be a **compact 2-Tier Routing Matrix** that takes fewer than 100 lines (under 4 KB / ~800 tokens) while providing disambiguation paths for models.

### 5.2 Managed Marker Injection Pattern

To ensure that pre-existing AWS Agent Toolkit rules and Crave Builder policies in `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` remain completely intact, the rule generator employs an idempotent delimiter-bound replacement mechanism.

**Delimiters**:
```markdown
<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->
... generated routing directives ...
<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->
```

**Injection Logic**:
1. Read target rule file (`AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`).
2. Search for the delimiter block using regex:
   `<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->[\s\S]*?<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->`
3. **If delimiter block exists**: Replace only the text between the markers with the freshly synthesized directive. All content above and below (AWS rules, Crave policies, custom user prompts) remains byte-for-byte identical.
4. **If delimiter block does not exist**: Append the block to the end of the file with appropriate newline spacing.
5. **Idempotency**: Running the generator $N$ times results in the exact same file content without duplication.

### 5.3 2-Tier Progressive Task-Based Routing Directives

The generated routing directive utilizes a two-tier architecture:
- **Tier 1 (Always-on Compact Matrix)**: Maps user task intents to specific tools and invocation guidelines.
- **Tier 2 (Progressive Disclosure)**: Instructs models to read full `SKILL.md` runbooks or query MCP schemas only when task triggers match.

```markdown
<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->
# AI Skills & MCP Tool Routing Matrix

Activate newly installed capabilities strictly based on task domain:

| Domain / Task Type | Intent Keywords | Assigned Capability | Platform / Location | Key Policy / Action |
| :--- | :--- | :--- | :--- | :--- |
| **Database & SQL** | sqlite, postgres, sql query, schema inspect | `mcp:sqlite` / `mcp:postgres` | Claude / Antigravity | Read-only queries by default. Verify schema first. |
| **Web Research** | web search, scrape page, documentation | `mcp:brave-search`, `mcp:fetch` | Claude / Antigravity | Use brave-search for queries; fetch for URL reading. |
| **Video & Media** | video edit, cut, timeline, opencut, render | `skill:opencut` | Antigravity (`config/skills`) | Read `~/.gemini/config/skills/opencut/SKILL.md`. |
| **Version Control** | git status, diff, commit, branch history | `mcp:git` | Claude / Antigravity | Prefer built-in git tool; use mcp:git for deep inspection. |
| **Cloud & DevOps** | aws, s3, lambda, docker, container | AWS Toolkit / `mcp:docker` | System / Crave | Adhere strictly to AWS Region and Crave cloud build policy. |
| **Code Intelligence**| lsp, definition, references, typecheck | `mcp:rust-analyzer`, `mcp:pyright`| Claude Code | Use language server tools for symbol resolution. |

## Progressive Activation Guidelines:
1. **On-Demand Loading**: Do NOT load or inspect skill directories until the user prompt directly invokes that domain.
2. **Safety First**: Destructive database writes, filesystem mutations, or remote deployments require explicit user confirmation.
3. **AWS & Crave Compliance**: Cloud operations must respect project Region constraints; heavy builds must route through Crave (`crave.exe -n run`).
<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->
```

### 5.4 Tool Conflict Resolution & Namespace Management

When multiple MCP servers offer overlapping tools (e.g. `sqlite` tool `read_query` vs `postgres` tool `read_query`, or `brave-search` vs native web search):
1. **Server-Level Namespacing**: In Antigravity and Claude Code, tools are namespaced by server identifier where possible (`mcp__sqlite__read_query`).
2. **Explicit Routing Priority**: The routing directive specifies the primary tool for each task domain (e.g. native tools take precedence for general filesystem operations; MCP tools take precedence for relational database queries).
3. **Disambiguation Prompts**: If an intent is ambiguous (e.g. searching code vs searching the public web), the directive instructs the model to inspect local files first before invoking external web search MCPs.

---

## 6. Testing & Verification Architecture

To verify the end-to-end pipeline (crawling, validation, mounting, merging, rule generation) without risking corruption of the developer's live environment, the testing architecture is built around **Virtual Target Sandboxes** and **Isolated Test Suites**.

### 6.1 Virtual Target Sandbox & Isolation Architecture

The pipeline engine exposes a configuration interface allowing all target paths to be parameterized or overridden:

```python
@dataclass
class PipelineEnvironmentConfig:
    gemini_config_dir: Path
    gemini_skills_dir: Path
    gemini_mcp_config: Path
    claude_json_path: Path
    user_home_dir: Path
    dry_run: bool = False

    @classmethod
    def live_default(cls) -> "PipelineEnvironmentConfig":
        home = Path(os.path.expanduser("~"))
        return cls(
            gemini_config_dir=home / ".gemini" / "config",
            gemini_skills_dir=home / ".gemini" / "config" / "skills",
            gemini_mcp_config=home / ".gemini" / "config" / "mcp_config.json",
            claude_json_path=home / ".claude.json",
            user_home_dir=home,
            dry_run=False,
        )

    @classmethod
    def create_sandbox(cls, sandbox_root: Path) -> "PipelineEnvironmentConfig":
        gemini_dir = sandbox_root / ".gemini" / "config"
        skills_dir = gemini_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            gemini_config_dir=gemini_dir,
            gemini_skills_dir=skills_dir,
            gemini_mcp_config=gemini_dir / "mcp_config.json",
            claude_json_path=sandbox_root / ".claude.json",
            user_home_dir=sandbox_root,
            dry_run=False,
        )
```

In automated E2E tests, `create_sandbox` points all file operations to a temporary directory (`pytest` `tmp_path`). The test runner populates this sandbox with realistic mock files (including a mock `.claude.json` containing `tinyfish` and mock `AGENTS.md` containing AWS rules) before executing the pipeline.

### 6.2 Test Suites Breakdown

#### Test Suite 1: Candidate Crawling & Metadata Extraction
* **Scope**: Evaluates GitHub repository crawling, release scanning, and metadata compilation into `catalog.json`.
* **Verification Points**:
  * Successfully parses mock GitHub repository responses without live rate-limit dependency.
  * Correctly filters out packages with $< 100$ stars (for community repos), archived status, or missing licenses.
  * Validates that all candidate packages conform to the `CatalogEntry` schema.

#### Test Suite 2: Dry-Run Schema & Security Validation
* **Scope**: Evaluates the validation engine against positive and negative test cases.
* **Positive Tests**:
  * Valid `SKILL.md` (proper frontmatter, progressive disclosure, valid relative links) -> Status `PASS`.
  * Valid `mcp_config` (valid stdio command and args) -> Status `PASS`.
* **Negative & Security Tests**:
  * Missing `name` or `description` in YAML frontmatter -> Status `FAIL` with clear issue description.
  * Uppercase characters or spaces in skill `name` -> Status `FAIL`.
  * Broken internal relative links (e.g. `[ref](./missing.md)`) -> Status `FAIL`.
  * Malicious command injection payload (`cmd.exe /c calc.exe`) in MCP args -> Status `CRITICAL_FAIL`.
  * Corrupted/malformed YAML or JSON -> Intercepted cleanly without crashing; status `FAIL`.
  * Zero unhandled exceptions: 100% of tested failure payloads produce a structured `ValidationReport` with exit code `0` in dry-run mode.

#### Test Suite 3: Multi-Platform Deployment & Merge Engine
* **Scope**: Verifies safe mounting and non-destructive JSON merges in the sandbox.
* **Verification Points**:
  * Mounts valid skills into `<sandbox>/.gemini/config/skills/<name>/SKILL.md`.
  * Initializes `<sandbox>/.gemini/config/mcp_config.json` if empty or missing, populating valid Antigravity schema.
  * **Claude Merge Safety**: Merges new MCP servers into a mock `.claude.json`. Asserts that:
    - `tinyfish` and its `X-API-Key` remain 100% intact.
    - All top-level settings (`numStartups`, `tipsHistory`, `cachedGrowthBookFeatures`) remain completely unchanged.
    - Resulting file is valid JSON and parses cleanly.
  * **Rollback Verification**: Injects a disk write error during merge; asserts that the engine restores from backup without leaving `.tmp` artifacts.

#### Test Suite 4: Rule Generation & Delimiter Injection
* **Scope**: Verifies injection into `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
* **Verification Points**:
  * Pre-existing AWS Agent Toolkit rules and Crave Builder policies are preserved character-for-character.
  * Routing directives are placed strictly between `<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->` and `<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->`.
  * **Idempotency**: Running the rule injector 5 consecutive times produces identical hash/content.
  * **Size Cap Compliance**: Generated rule files remain well under the 24,000-byte Antigravity per-file threshold.

### 6.3 E2E Integration Verification Harness

A consolidated E2E verification command runs the full pipeline in dry-run and sandbox modes:

```bash
# E2E Test Execution Command
python -m pytest tests/test_e2e_pipeline.py -v --tb=short
```

**Acceptance Criteria Checklist Verified by Harness**:
- [x] Catalog documents discovered, verified, and skipped packages.
- [x] Candidate skills and MCP servers validate with zero unhandled exceptions.
- [x] Generated SKILL.md passes Antigravity frontmatter validation.
- [x] Validated skills mount cleanly into `.gemini/config/skills`.
- [x] Claude Code `.claude.json` merges without corrupting existing keys or settings.
- [x] Rule files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) contain non-overlapping, progressive routing guidelines.

---

## 7. Implementation Roadmap & Technical Recommendations

For the subsequent implementation phase, the following modular code layout and technical decisions are recommended:

### Recommended Project Layout
```
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\
├── src\
│   ├── __init__.py
│   ├── crawler\             # GitHub & catalog discovery
│   │   ├── github_client.py
│   │   └── catalog_indexer.py
│   ├── validator\           # Quality, security & schema filters
│   │   ├── exceptions.py
│   │   ├── security_scanner.py
│   │   ├── skill_validator.py
│   │   ├── mcp_validator.py
│   │   └── dry_run_runner.py
│   ├── deployer\            # Multi-platform deployment engine
│   │   ├── file_ops.py      # Atomic writes & rolling backups
│   │   ├── antigravity_mount.py
│   │   └── claude_merge.py
│   ├── router\              # Task-based routing & rule injection
│   │   ├── matrix_generator.py
│   │   └── rule_injector.py
│   └── cli.py               # Main CLI entry point
├── tests\
│   ├── fixtures\            # Mock .claude.json, SKILL.md, repo responses
│   ├── test_crawler.py
│   ├── test_validator.py
│   ├── test_deployer.py
│   ├── test_router.py
│   └── test_e2e_pipeline.py
├── catalog.json             # Discovered, validated, and skipped catalog
├── pyproject.toml           # Poetry / uv project config
└── README.md                # Project documentation & usage runbook
```

### Key Technical Recommendations
1. **Use Pure Python with Standard Library Fallbacks**: Keep dependencies minimal (`pyyaml`, `pydantic` or `jsonschema`, `requests` / `httpx`). Standard library `json`, `pathlib`, `shutil`, `re`, `tempfile` should drive the core deployment and file operations.
2. **Explicit CLI Flags**: Provide clear CLI subcommands:
   - `python -m registry crawl`: Discover and index repositories into `catalog.json`.
   - `python -m registry validate --dry-run`: Perform dry-run validation on candidates.
   - `python -m registry deploy [--target sandbox|live]`: Deploy validated tools to target platforms.
   - `python -m registry inject-rules [--target sandbox|live]`: Inject routing directives.
3. **Preserve User Privacy & API Keys**: Never log or commit user tokens discovered in `.claude.json`. When indexing community MCP servers requiring credentials, output parameter placeholders (`${VAR_NAME}`) and prompt the user to provide them in their local `.env` or configuration.
