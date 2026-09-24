# TEST_INFRA — AI-Skills-Registry E2E Test Infrastructure Specification

**Document Version**: 1.0.0  
**Status**: APPROVED  
**Author**: `test_writer_e2e_1` (Teamwork E2E Test Orchestrator)  
**Authoritative References**: `ORIGINAL_REQUEST.md`, `PROJECT.md`, `survey_specs.md`, `survey_pipeline.md`

---

## 1. Test Philosophy & Principles

The testing framework for **AI-Skills-Registry** is designed as a rigorous, **opaque-box, requirement-driven verification system**. The test suites evaluate system compliance against authoritative interface contracts, security guarantees, schema definitions, and platform behaviors derived strictly from `ORIGINAL_REQUEST.md` and `PROJECT.md`.

### Core Principles:
1. **Opaque-Box Requirement Verification**: Tests do not couple to internal implementation details, private variables, or transient state. All assertions target observable outputs: generated catalog files, JSON schema conformance, dry-run diagnostic reports, filesystem mounts, non-destructive config merges, delimiter-bound markdown injections, and process exit codes.
2. **Zero Host Mutation (Strict Sandbox Isolation)**: Tests run inside virtual staging sandboxes via `PipelineEnvironmentConfig`. Tests never touch or mutate `C:\Users\BangerSoul\.claude.json`, `C:\Users\BangerSoul\.gemini\`, or live user rule files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
3. **Mandatory 4-Tier Quality Model**:
   - **Tier 1 (Category-Partition)**: Systematic equivalence partitioning covering all primary behaviors in isolation.
   - **Tier 2 (Boundary Value Analysis & Negative Testing)**: Stress testing edge values (0 bytes, 24 KB limits, 100-star thresholds, 365-day commit windows, malformed syntax, injection attacks).
   - **Tier 3 (Pairwise Integration Testing)**: Multi-module handshake verification across the pipeline lifecycle (Crawler ↔ Validator ↔ Deployer ↔ Router).
   - **Tier 4 (Real-World Workload Testing)**: End-to-end application scenarios simulating dirty environments, pre-existing configurations (`tinyfish` credentials, AWS Toolkit directives, Crave build policies), and multi-cycle idempotent runs.
4. **Authoritative Output Derivation**: Expected test values are derived from mathematical constraints, Draft-07 schemas, Model Context Protocol JSON-RPC 2.0 specifications, and documented Antigravity runtime bounds.
5. **Deterministic & Network-Independent**: Tests execute deterministically without relying on live external networks or unauthenticated GitHub API rate limits (60 req/hr). Offline HTTP mocking and deterministic fixture injection guarantee 100% reproducible execution.

---

## 2. Comprehensive Feature Inventory & Tier Mapping

All 15 system features identified in `PROJECT.md` are systematically mapped across Tiers 1 through 4:

| Feature # | Feature Name | Primary Milestone | Tier 1: Category-Partition (Feature Isolation) | Tier 2: Boundary Value Analysis (BVA & Negatives) | Tier 3: Pairwise Interactions | Tier 4: Real-World Workload Scenarios |
|---|---|---|---|---|---|---|
| **F1** | Official & Community Registry Crawling | M1 | `test_f1_crawler_querying.py`: Official repo scanning, community repo filtering, stargate thresholds | Zero stars, 99 stars (reject), 100 stars (accept), archived repos, network 429 rate limit | Pair 1: Crawler ↔ Validator | Scenarios 1, 4 (Monorepo discovery, bad repo skip) |
| **F2** | Standardized Metadata Schema Extraction | M1 | `test_f2_metadata_extraction.py`: Draft-07 field extraction (name, description, capabilities, schemas, license) | Missing optional vs required fields, null schemas, unicode descriptions, unconventional license strings | Pair 1: Crawler ↔ Validator | Scenarios 1, 2 (End-to-end catalog generation) |
| **F3** | Comprehensive 20-Package Catalog Generation | M1 | `test_f3_catalog_generation.py`: 20 packages indexed across 5 categories (Browser, Code, Data, Ops, Media) | Empty catalog, single package, duplicate IDs, missing category partition | Pair 1: Crawler ↔ Validator | Scenarios 1, 4, 5 (Catalog compilation & formatting) |
| **F4** | Deprecation & Vulnerability Filter | M2 | `test_f4_security_deprecation_filter.py`: Rejection of `aws-api-mcp-server`, yanked packages, unmaintained repos | 365-day commit boundary, CVSS 6.9 (warn) vs 7.0 (reject), shell injection in args (`cmd.exe /c`, `sh -c`) | Pair 2: Validator ↔ Deployer | Scenarios 2, 4 (Vulnerable package isolation) |
| **F5** | SKILL.md Frontmatter & Progressive Disclosure Validator | M2 | `test_f5_skill_frontmatter_validator.py`: Frontmatter YAML parsing, lowercase-hyphen name regex, third-person description | Name regex boundaries, description length (19 chars vs 20 chars min vs 1,024 max), missing `references/` | Pair 2: Validator ↔ Deployer | Scenarios 1, 4 (Malformed SKILL.md rejection) |
| **F6** | MCP JSON-RPC Spec Validator | M2 | `test_f6_mcp_jsonrpc_validator.py`: stdio (command, args, env) and sse (serverUrl) transport validation | Command without args, empty env, invalid URL schemes (`ftp://`), missing executable binary | Pair 2: Validator ↔ Deployer | Scenarios 1, 2 (Transport schema enforcement) |
| **F7** | Zero-Unhandled-Exception Dry-Run Test Script | M2 | `test_f7_dry_run_runner.py`: CLI dry-run mode, JSON reporting, 100% exception wrapping | Corrupt JSON, broken YAML, unreadable files, memory exhaustion simulation; exit code 0 | Pair 2: Validator ↔ Deployer | Scenarios 1, 4 (Fault-tolerant dry-run audit) |
| **F8** | Antigravity Native Skill Mounting | M3 | `test_f8_antigravity_skill_mount.py`: Generates `~/.gemini/config/skills/<name>/SKILL.md` and subdirs | Deep nested subdirs, read-only permissions, filename collisions, staging cleanup | Pair 3: Deployer ↔ Router | Scenarios 1, 2, 5 (Skill filesystem mounting) |
| **F9** | Antigravity MCP Server Configuration | M3 | `test_f9_antigravity_mcp_config.py`: Writes and merges `~/.gemini/config/mcp_config.json` | 0-byte initial file, missing parent directory, duplicate server keys, invalid JSON backup | Pair 3: Deployer ↔ Router | Scenarios 1, 3, 5 (MCP configuration init & merge) |
| **F10** | Claude Code Non-Destructive Deep Merge | M3 | `test_f10_claude_deep_merge.py`: Merges `mcpServers` in `~/.claude.json` preserving all other keys | `tinyfish` API key preservation, 52 KB file integrity, non-dict root, missing `mcpServers` | Pair 3: Deployer ↔ Router | Scenarios 2, 5 (`tinyfish` and user state preservation) |
| **F11** | Parameterized Environment Sandbox | M3 | `test_f11_sandbox_environment.py`: `PipelineEnvironmentConfig` redirection and isolation | Relative vs absolute paths, Windows drive letters, directory symlinks, temp cleanup | Pair 6: Deployer ↔ Sandbox | Scenarios 1, 2, 3, 4, 5 (Sandbox integrity) |
| **F12** | 2-Tier Progressive Task-Based Routing Directives | M4 | `test_f12_routing_matrix.py`: Generates compact routing table (<100 lines, <4 KB) across 5 domains | Unassigned task category, conflicting tool names, maximum description length per table row | Pair 4: Deployer ↔ Router | Scenarios 1, 3 (Routing table generation) |
| **F13** | Idempotent Rule File Injection | M4 | `test_f13_rule_injector.py`: Delimiter-based injection into `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | Pre-existing AWS rules, Crave Builder policy, 24 KB truncation boundary (23,999 vs 24,001 B) | Pair 4: Deployer ↔ Router | Scenarios 3, 5 (Idempotent 5-run injection) |
| **F14** | E2E Test Suite 100% Pass (Tiers 1-4) | M5 | `run_all_tests.py`: Aggregated execution across all 4 tiers with structured reporting | Missing test files, exit code non-zero on failure, exit code 0 on all pass | All Pairs (1-6) | Full suite validation |
| **F15** | Adversarial Coverage Hardening (Tier 5) | M5 | Stress-test suite: white-box mutation, malformed stream payloads, directory traversal attacks | Extreme fuzz payloads (`../`, `\0`, `CON`, `NUL`), multi-megabyte payloads, corrupted state | Pipeline Resilience | Scenario 4 (Adversarial rejection) |

---

## 3. Test Architecture & Directory Layout

### 3.1 Directory Layout
```
AI-Skills-Registry/
├── TEST_INFRA.md                               # This specification
├── TEST_READY.md                               # Readiness signoff
├── tests/
│   ├── __init__.py
│   ├── conftest.py                             # Sandbox isolation fixtures & mock environments
│   ├── run_all_tests.py                        # Standalone CLI test runner (exits 0 or 1)
│   ├── tier1_feature_coverage/                 # Tier 1: Category-Partition (Features 1-13)
│   │   ├── __init__.py
│   │   ├── test_f1_crawler_querying.py
│   │   ├── test_f2_metadata_extraction.py
│   │   ├── test_f3_catalog_generation.py
│   │   ├── test_f4_security_deprecation_filter.py
│   │   ├── test_f5_skill_frontmatter_validator.py
│   │   ├── test_f6_mcp_jsonrpc_validator.py
│   │   ├── test_f7_dry_run_runner.py
│   │   ├── test_f8_antigravity_skill_mount.py
│   │   ├── test_f9_antigravity_mcp_config.py
│   │   ├── test_f10_claude_deep_merge.py
│   │   ├── test_f11_sandbox_environment.py
│   │   ├── test_f12_routing_matrix.py
│   │   └── test_f13_rule_injector.py
│   ├── tier2_boundary_corner/                  # Tier 2: Boundary Value Analysis & Corner Cases
│   │   ├── __init__.py
│   │   ├── test_bva_catalog_boundaries.py
│   │   ├── test_bva_security_and_injection.py
│   │   ├── test_bva_skill_and_mcp_schemas.py
│   │   ├── test_bva_deployment_transactions.py
│   │   └── test_bva_rule_file_size_limits.py
│   ├── tier3_cross_feature/                    # Tier 3: Pairwise Inter-Module Integration
│   │   ├── __init__.py
│   │   ├── test_pair1_crawler_to_validator.py
│   │   ├── test_pair2_validator_to_deployer.py
│   │   ├── test_pair3_deployer_to_router.py
│   │   └── test_pair4_sandbox_isolation_pipeline.py
│   └── tier4_real_world/                       # Tier 4: Real-World Workload Scenarios
│       ├── __init__.py
│       ├── test_scenario1_clean_machine_init.py
│       ├── test_scenario2_claude_tinyfish_preservation.py
│       ├── test_scenario3_aws_crave_rule_preservation.py
│       ├── test_scenario4_adversarial_rejection_pipeline.py
│       └── test_scenario5_idempotent_multirun_lifecycle.py
```

### 3.2 Test Runner Command & Execution Interface
The test suite can be executed via two standard interfaces:

1. **Standalone Test Runner (Preferred for Orchestration & CI)**:
   ```powershell
   python tests/run_all_tests.py
   ```
   * Emits structured terminal output with colored pass/fail indicators.
   * Prints per-tier summaries and total coverage counts.
   * Returns exit code `0` on 100% pass, or non-zero on failure.
   * Supports command-line filtering: `python tests/run_all_tests.py --tier 1` or `--feature 10`.

2. **Pytest CLI Runner**:
   ```powershell
   python -m pytest tests/ -v --tb=short
   ```
   * Standard pytest execution with granular test discovery.

---

## 4. Real-World Application Scenarios (Tier 4 Workloads)

### Scenario 1: Clean Machine Initialization
* **Context**: Fresh developer machine with no prior Antigravity skills and an empty (0-byte) `~/.gemini/config/mcp_config.json`.
* **Execution**: Full pipeline runs: crawl mock catalog -> validate candidate packages -> deploy skills to `.gemini/config/skills/` -> initialize `mcp_config.json` -> create initial `.claude.json` -> inject managed rules.
* **Assertions**:
  - `mcp_config.json` is initialized from 0 bytes into valid JSON with `mcpServers` dict.
  - Skills directories are created with valid `SKILL.md` frontmatter and progressive disclosure pointers.
  - Delimiter blocks are cleanly appended to `AGENTS.md` and `GEMINI.md`.

### Scenario 2: Claude Code `tinyfish` Credential Preservation
* **Context**: Pre-existing `~/.claude.json` (52 KB, 1,364 lines) containing active server `tinyfish` with `X-API-Key: sk-tinyfish-XF3WGyHrnMiULqKTZWQ4vk8IONL-DIfO`, custom growthbook feature flags, and tips history.
* **Execution**: Deployer merges 5 verified MCP servers (e.g. `sqlite`, `brave-search`, `git`, `filesystem`, `postgres`) into `.claude.json`.
* **Assertions**:
  - `tinyfish` server entry and exact `X-API-Key` remain 100% unchanged.
  - All 1,300+ lines of top-level user configuration (`cachedGrowthBookFeatures`, `numStartups`, `tipsHistory`) remain bit-for-bit intact.
  - New MCP servers are present alongside `tinyfish`.
  - Timestamped backup `.claude.json.bak.<timestamp>` is generated.

### Scenario 3: Protected Ambient Directives Preservation (AWS Toolkit & Crave Policies)
* **Context**: User rule files `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` containing existing critical guidelines:
  - AWS Agent Toolkit rules (`<!-- BEGIN AWS Agent Toolkit rules -->` ... `<!-- END AWS Agent Toolkit rules -->`) specifying regional constraints and account policies.
  - Heavy Builds & Cloud Compilation Policy: Crave Builder (`crave.exe -n run ...`).
* **Execution**: Rule injector synthesizes 2-tier task-based routing matrix and updates all three rule files.
* **Assertions**:
  - Pre-existing AWS rules and Crave policies are unmodified.
  - Managed routing block is inserted between `<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->` and `<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->`.
  - Total file size remains strictly under 24,000 bytes (Antigravity truncation limit).

### Scenario 4: Adversarial & Deprecated Package Isolation
* **Context**: Input catalog contains a mixture of valid candidates and hostile/broken packages:
  - Deprecated package (`aws-api-mcp-server`).
  - Stale unmaintained package (last commit > 365 days, < 100 stars).
  - Malicious entrypoint with command injection (`cmd.exe /c calc.exe`).
  - Corrupt `SKILL.md` missing YAML frontmatter.
* **Execution**: Full pipeline runs dry-run and validation stages.
* **Assertions**:
  - Zero unhandled exceptions occur (exit code 0 in dry-run).
  - All hostile and unmaintained packages are rejected with specific diagnostic issue codes.
  - Valid packages are verified and staged for deployment.
  - `validation_report.json` documents exact reasons for rejection.

### Scenario 5: Idempotent Multi-Cycle Lifecycle
* **Context**: Pipeline is executed 5 consecutive times in succession on the same target sandbox.
* **Execution**: Iterative crawl, validate, deploy, and inject cycles.
* **Assertions**:
  - Skill directories are updated cleanly without duplicating files.
  - `.claude.json` and `mcp_config.json` contain exactly one entry per server (no duplicated keys).
  - Rule files contain exactly one managed routing delimiter block; file checksums stabilize after initial injection.
  - Zero state drift across repeated runs.

---

## 5. Coverage Thresholds & Quality Gates

To guarantee enterprise robustness, the following quantitative coverage thresholds are mandated:

| Tier | Quality Scope | Minimum Coverage Requirement | Verification Command | Gate Condition |
|---|---|---|---|---|
| **Tier 1** | Feature Coverage (F1–F13) | $\ge 5$ isolated unit tests per feature ($\ge 65$ tests total) | `python -m pytest tests/tier1_feature_coverage/` | 100% Pass |
| **Tier 2** | Boundary Value Analysis & Negatives | $\ge 5$ boundary/negative tests per feature category ($\ge 25$ tests total) | `python -m pytest tests/tier2_boundary_corner/` | 100% Pass |
| **Tier 3** | Pairwise Inter-Module Integration | All 4 primary interface pairs tested across valid & invalid payloads ($\ge 15$ tests total) | `python -m pytest tests/tier3_cross_feature/` | 100% Pass |
| **Tier 4** | Real-World Application Workloads | All 5 defined application scenarios tested end-to-end ($\ge 5$ comprehensive scenarios) | `python -m pytest tests/tier4_real_world/` | 100% Pass |
| **Aggregate** | Complete Test Harness | Standalone runner passes all tiers with exit code 0 | `python tests/run_all_tests.py` | 100% Pass |

---

## 6. Authoritative Expected Output Specifications

### 6.1 Draft-07 Catalog Specification (`catalog.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "total_packages": 20,
  "categories": ["browser_search", "code_intelligence", "data_databases", "system_ops", "media"],
  "packages": [
    {
      "id": "browser-playwright",
      "name": "Playwright Browser Automation",
      "category": "browser_search",
      "description": "Headless browser automation for web navigation, screenshots, and scraping.",
      "repo_url": "https://github.com/microsoft/playwright-mcp",
      "type": "mcp_server",
      "stars": 36000,
      "capabilities": ["browser_navigate", "browser_click", "browser_screenshot"],
      "entrypoint": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "env": {}
      },
      "dependencies": { "node": ">=18" },
      "license": "Apache-2.0",
      "validation_status": "verified",
      "platform_targets": ["antigravity", "claude_code"]
    }
  ]
}
```

### 6.2 Antigravity `SKILL.md` Specification
```markdown
---
name: opencut
description: Comprehensive guide and reference for OpenCut web-based video editor. Use when the user asks about video editing or timeline assembly.
---
# OpenCut Video Editor

## Overview
OpenCut is an open-source, privacy-first web-based video editor.

## When to Use
Activate this skill when user tasks involve timeline editing, media slicing, or video rendering.

## Workflows
1. Inspect project media.
2. Formulate timeline edit operations.
```

### 6.3 Delimiter-Bound Managed Routing Block
```markdown
<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->
# AI Skills & MCP Tool Routing Matrix

| Domain / Task Type | Assigned Capability | Platform | Key Policy |
| :--- | :--- | :--- | :--- |
| **Database & SQL** | `mcp:sqlite` / `mcp:postgres` | Claude / Antigravity | Read-only queries by default. |
| **Web Research** | `mcp:brave-search` / `mcp:fetch` | Claude / Antigravity | brave-search for queries; fetch for URLs. |
| **Video & Media** | `skill:opencut` | Antigravity | Read `skills/opencut/SKILL.md`. |
| **Version Control** | `mcp:git` | Claude / Antigravity | Prefer native git; use mcp:git for deep history. |
| **Cloud & DevOps** | AWS Toolkit / `mcp:docker` | System / Crave | Adhere strictly to AWS Region and Crave build policies. |

## Progressive Activation Guidelines:
1. Load skill documentation on-demand only.
2. Require confirmation for destructive mutations.
<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->
```

---
*Signed by `test_writer_e2e_1` — Parallel Track E2E Testing Lead*
