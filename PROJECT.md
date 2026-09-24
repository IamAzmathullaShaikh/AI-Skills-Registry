# Project: AI-Skills-Registry

## Architecture
The AI Skills & MCP Registry is an automated, robust discovery, validation, and multi-platform distribution pipeline.
It bridges the ecosystem between GitHub MCP/Skill registries and local AI environments (Antigravity, Claude Code / Freebuff, Cursor / Codex).

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

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Official & Community Registry Crawling | Scrape & index official `modelcontextprotocol/servers` and community repos (>100 stars) | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Standardized Metadata Schema Extraction | Extract name, description, capabilities, schemas, dependencies, license into Draft-07 catalog.json | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Comprehensive 20-Package Catalog Generation | Build catalog.json and detailed README.md covering all 5 categories (Browser, Code, Data, Ops, Media) | M1 | ORIGINAL_REQUEST §AC |
| 4 | Deprecation & Vulnerability Filter | Reject unmaintained, deprecated (`aws-api-mcp-server`), or insecure candidates | M2 | ORIGINAL_REQUEST §R2 |
| 5 | SKILL.md Frontmatter & Progressive Disclosure Validator | Verify lowercase-hyphenated name, third-person description, and references/ layout | M2 | ORIGINAL_REQUEST §R2 |
| 6 | MCP JSON-RPC Spec Validator | Validate stdio/sse transport entrypoints, tools, schemas, and parameter requirements | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Zero-Unhandled-Exception Dry-Run Test Script | Automated CLI dry-run validation with structured JSON reporting and 100% exception wrapping | M2 | ORIGINAL_REQUEST §AC |
| 8 | Antigravity Native Skill Mounting | Generate and mount compliant SKILL.md bundles to `C:\Users\BangerSoul\.gemini\config\skills\<name>\` | M3 | ORIGINAL_REQUEST §R3 |
| 9 | Antigravity MCP Server Configuration | Safely initialize/update `C:\Users\BangerSoul\.gemini\config\mcp_config.json` | M3 | ORIGINAL_REQUEST §R3 |
| 10 | Claude Code Non-Destructive Deep Merge | Safely merge verified MCP servers into `C:\Users\BangerSoul\.claude.json` preserving `tinyfish` API key & state | M3 | ORIGINAL_REQUEST §R3 |
| 11 | Parameterized Environment Sandbox | Support mock directory sandboxing via `PipelineEnvironmentConfig` for risk-free E2E testing | M3 | survey_pipeline.md |
| 12 | 2-Tier Progressive Task-Based Routing Directives | Map task types (db, web, media, ops, code) to specific tools under 100 lines (<4 KB) | M4 | ORIGINAL_REQUEST §R4 |
| 13 | Idempotent Rule File Injection | Inject managed routing directives into AGENTS.md, CLAUDE.md, GEMINI.md using delimiters, preserving AWS & Crave policies | M4 | ORIGINAL_REQUEST §R3, R4 |
| 14 | E2E Test Suite 100% Pass (Tiers 1-4) | Comprehensive test suite covering features, boundaries, pairwise interactions, and real-world workflows | M5 | Project Pattern §Dual Track |
| 15 | Adversarial Coverage Hardening (Tier 5) | White-box stress-testing, malformed input handling, mutation coverage | M5 | Project Pattern §Dual Track |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Discovery & Catalog Indexing Engine (`crawler_catalog`) | Implement crawling, metadata extraction, catalog.json & README.md for 20 packages across 5 categories | none | DONE (catalog.json, README.md, src/config.py, src/crawler/, 154/154 tests passed) |
| 2 | M2: Quality, Security & Schema Validation (`validator_engine`) | Implement deprecation filters, Draft-07 catalog validator, SKILL.md & MCP validators, dry-run CLI | M1 | IN_PROGRESS |
| 3 | M3: Multi-Platform Deployment Engine (`deployer_engine`) | Implement Antigravity skill mounter, mcp_config.json updater, Claude Code deep merger with backup | M2 | PLANNED |
| 4 | M4: Intelligent Skill Routing Engine (`router_engine`) | Implement 2-tier task routing generator & managed delimiter injector for AGENTS.md/CLAUDE.md/GEMINI.md | M3 | PLANNED |
| 5 | M5: Final E2E Acceptance & Adversarial Hardening | Phase 1: 100% pass on E2E Test Suite (Tiers 1-4). Phase 2: Tier 5 adversarial hardening | M1, M2, M3, M4, E2E Track | PLANNED |

## Parallel Track: E2E Testing
| # | Name | Scope | Status |
|---|------|-------|--------|
| E2E | E2E Testing Orchestrator (`e2e_testing_track`) | Design requirement-driven test infra (TEST_INFRA.md), build Tiers 1-4 tests, publish TEST_READY.md | IN_PROGRESS |

## Interface Contracts

### M1 (Crawler) ↔ M2 (Validator)
- Input: `catalog.json` produced by M1 adhering to Draft-07 schema.
- Data Structure:
  ```json
  {
    "version": "1.0.0",
    "total_packages": 20,
    "categories": ["browser_search", "code_intelligence", "data_databases", "system_ops", "media"],
    "packages": [
      {
        "id": "browser-playwright",
        "name": "Playwright Browser Automation",
        "category": "browser_search",
        "description": "...",
        "repo_url": "https://github.com/microsoft/playwright-mcp",
        "type": "mcp_server",
        "stars": 36000,
        "capabilities": ["browser_navigate", ...],
        "entrypoint": {
          "command": "npx",
          "args": ["-y", "@playwright/mcp@latest"],
          "env": {}
        },
        "dependencies": { "node": ">=18" },
        "license": "Apache-2.0",
        "validation_status": "pending",
        "platform_targets": ["antigravity", "claude_code"]
      }
    ]
  }
  ```
- Errors: Returns structured error array `{ package_id: string, stage: string, error: string }`.

### M2 (Validator) ↔ M3 (Deployer)
- Input: Verified catalog where `validation_status == "verified"`.
- Output of Validator: `validation_report.json` with `{ total: int, passed: int, rejected: int, results: [...] }`.
- Deployer only mounts packages passing all stages (maintenance, security, schema, dry-run).

### M3 (Deployer) ↔ M4 (Router)
- Input: List of deployed skills in Antigravity (`~/.gemini/config/skills/`) and active servers in Claude Code (`~/.claude.json`).
- Router generates matching 2-Tier Progressive Task-Based Routing Directives and updates rule files with exact delimiters:
  `<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->`
  `<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->`

## Code Layout
```
AI-Skills-Registry/
├── catalog.json                                # Master catalog of discovered & verified packages
├── README.md                                    # Project overview and catalog presentation
├── src/
│   ├── __init__.py
│   ├── config.py                                # PipelineEnvironmentConfig (host paths vs mock sandbox)
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── github_crawler.py                   # Registry querying and catalog builder
│   │   └── registry_sources.py                 # Official & community seed registries
│   ├── validator/
│   │   ├── __init__.py
│   │   ├── schema_validator.py                 # JSON Schema and YAML frontmatter validation
│   │   ├── security_filter.py                  # Deprecation, vulnerability & boundary checks
│   │   └── dry_run_runner.py                   # Automated zero-unhandled-exception test runner
│   ├── deployer/
│   │   ├── __init__.py
│   │   ├── antigravity_deployer.py             # Mounts SKILL.md & writes mcp_config.json
│   │   └── claude_deployer.py                  # Safe atomic deep-merger for ~/.claude.json
│   └── router/
│       ├── __init__.py
│       ├── routing_matrix.py                   # 2-Tier Progressive Task-Based Directive generator
│       └── rule_file_manager.py                # Idempotent delimiter-based rule injector
├── tests/
│   ├── conftest.py                             # Mock fixtures and isolated sandbox setup
│   ├── tier1_feature_coverage/                 # >=5 tests per feature (isolated unit/component)
│   ├── tier2_boundary_corner/                  # Corrupt configs, empty inputs, network failure, etc.
│   ├── tier3_cross_feature/                    # Pairwise interaction tests (crawl->validate->deploy)
│   ├── tier4_real_world/                       # Realistic end-to-end multi-platform integration tests
│   └── run_all_tests.py                        # Automated E2E test runner
└── .agents/teamwork/                            # Orchestrator & subagent metadata
```
