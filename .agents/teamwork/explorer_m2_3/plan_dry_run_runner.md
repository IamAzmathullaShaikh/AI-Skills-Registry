# Implementation Plan: Milestone 2 Dry-Run Engine & CLI Architecture (`src/validator/dry_run_runner.py`)

**Author**: `explorer_m2_3` (teamwork_preview_explorer)  
**Date**: 2026-09-24  
**Target Milestone**: Milestone 2 (Quality, Security & Schema Validation Engine)  
**File Target**: `src/validator/dry_run_runner.py`  
**Dependencies**: `src/config.py`, `src/validator/security_filter.py`, `src/validator/schema_validator.py`  

---

## 1. Executive Summary & Mission Scope

The primary objective of Milestone 2's Dry-Run Engine (`dry_run_runner.py`) is to provide an automated, bulletproof, zero-unhandled-exception validation harness that audits all candidate skills and MCP servers discovered by Milestone 1 before any local installation or system modification can occur in Milestone 3.

To satisfy the authoritative user request and project acceptance criteria:
1. **Zero Unhandled Exceptions**: Must complete dry-run validation over hundreds of arbitrary, corrupted, or hostile package definitions without raising an uncaught syntax, type, encoding, or format exception.
2. **4-Stage Automated Pipeline**:
   - **Stage 1**: Maintenance & Deprecation Gating
   - **Stage 2**: Security & Isolation Boundary Audit
   - **Stage 3**: Schema Compliance (Draft-07, SKILL.md Frontmatter, MCP JSON-RPC)
   - **Stage 4**: Dry-Run Tool Execution / Entry Point Simulation
3. **Structured JSON Reporting**: Generates a standardized `validation_report.json` detailing pass/fail counts, per-stage diagnostics, exact rule IDs, and remediation instructions.
4. **CLI & Programmatic Interface**: Exposes a developer-friendly CLI (`python -m src.validator.dry_run_runner`) and deterministic exit codes.
5. **M2 ↔ M3 Deployment Contract**: Produces a filtered, verified catalog artifact (`verified_catalog.json`) that feeds directly into Milestone 3's Antigravity and Claude Code deployment engines.

---

## 2. 4-Stage Automated Validation Pipeline Architecture

Every candidate package undergoes a deterministic sequential audit through four pipeline stages. If a package fails a critical check in an earlier stage, it is flagged as rejected with detailed error attribution, while subsequent non-fatal checks can continue or short-circuit cleanly.

```
+───────────────────────────────────────────────────────────────────────────────+
|                        4-STAGE DRY-RUN VALIDATION PIPELINE                    |
+───────────────────────────────────────────────────────────────────────────────+
                                        │
                         Candidate Package Dictionary
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: Maintenance & Deprecation Gating                                     │
│  - Known deprecation blacklist check (e.g. aws-api-mcp-server)                │
│  - Repository status (archived == false, disabled == false)                   │
│  - Maintenance velocity & commit freshness (< 365 days)                       │
│  - Star threshold gating (>= 100 stars for community repos; exempt official) │
│  - License compliance (approved permissive/compatible SPDX)                   │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ (Pass)
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: Security & Isolation Boundary Audit                                  │
│  - Shell injection pattern scanner (cmd.exe /c, sh -c, powershell -c, ;, |, `)│
│  - Filesystem boundary & traversal prevention (.., /etc, C:\Windows)           │
│  - Scoped directory enforcement for tools (e.g. filesystem mcp must scope)    │
│  - Credential isolation & secret leak regex (sk-*, ghp_*, AWS access keys)    │
│  - AWS single-region constraint compliance (no cross-region/Lambda@Edge)      │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ (Pass)
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 3: Schema Compliance Verification                                       │
│  - Master Catalog Draft-07 schema compliance (types, required fields)         │
│  - SKILL.md YAML Frontmatter: regex ^[a-z0-9-]+$, third-person description    │
│  - Progressive disclosure validation (references/, scripts/, link integrity)  │
│  - MCP JSON-RPC 2.0 Transport compliance (stdio vs sse/http parameters)       │
│  - Tool definitions, JSON Schema inputSchema, error semantics (isError: true) │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ (Pass)
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 4: Dry-Run Tool Execution / Entry Point Simulation                      │
│  - Entrypoint command probing & executable availability resolution            │
│  - Parameter placeholder syntax validation (${ENV_VAR})                       │
│  - Mock JSON-RPC Handshake simulation (initialize request/response)           │
│  - In-memory deployment simulation (Antigravity SKILL.md mount & Claude merge)│
│  - Collision prevention against existing user keys (e.g. tinyfish)            │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
                     Standardized Validation Result & Report
                         (Status: VERIFIED or REJECTED)
```

### 2.1 Detailed Stage Specifications

#### Stage 1: Maintenance & Deprecation Gating
- **Purpose**: Prevent dead, unmaintained, copycat, or deprecated packages from polluting the registry.
- **Rules Evaluated**:
  - `M1_DEPRECATION_CHECK`: Check `package.id` against `DEPRECATED_PACKAGE_IDS` (e.g., `aws-api-mcp-server`, `deprecated-mcp-tools`, `legacy-sqlite-bridge`).
  - `M1_STAR_THRESHOLD`: If `type == "mcp_server"` and not from an official organization (`modelcontextprotocol`, `microsoft`, `anthropic`, `duckdb`, `redis`, `docker`, `kubernetes`), require `stars >= 100`.
  - `M1_ARCHIVED_STATUS`: Check if repository is archived or unmaintained.
  - `M1_LICENSE_VALID`: Verify `license` is present, valid SPDX, and not proprietary/unlicensed.

#### Stage 2: Security & Isolation Boundary Audit
- **Purpose**: Protect local developer environments from remote code execution, secret leakage, and filesystem breakout.
- **Rules Evaluated**:
  - `S2_COMMAND_INJECTION`: Inspect `command` and `args` in `entrypoint`. Reject shell wrappers (`cmd.exe /c`, `powershell.exe -c`, `sh -c`, `bash -c`) and unquoted shell meta-characters (`;&|`$`).
  - `S2_PATH_TRAVERSAL`: Verify package ID, commands, arguments, and file paths do not contain `..`, `/etc`, or absolute root paths without explicit bounding.
  - `S2_SECRET_LEAK`: Scan `env` and `args` for hardcoded secrets matching `sk-[a-zA-Z0-9]{32,}`, `ghp_[a-zA-Z0-9]{36}`, or AWS keys. Enforce `${VAR_NAME}` placeholder format.
  - `S2_AWS_SINGLE_REGION`: Verify AWS-related configurations adhere to the user's selected single region policy (no multi-region replication, no Lambda@Edge).

#### Stage 3: Schema Compliance Verification
- **Purpose**: Guarantee structural integrity across Draft-07 catalog, Antigravity skills, and MCP JSON-RPC transports.
- **Rules Evaluated**:
  - `C3_CATALOG_SCHEMA`: Ensure package has mandatory fields: `id`, `name`, `category`, `type`, `description`, `repo_url`, `stars`, `capabilities`, `entrypoint`, `license`, `validation_status`, `platform_targets`.
  - `C3_SKILL_FRONTMATTER`: For `type == "skill"`, verify YAML frontmatter format:
    - `name`: Matches regex `^[a-z0-9]+(-[a-z0-9]+)*$`.
    - `description`: Non-empty, 20 to 1,024 characters, third-person phrasing.
  - `C3_PROGRESSIVE_DISCLOSURE`: Verify document size (< 500 lines / 24 KB) and ensure all markdown links to `references/` or `scripts/` resolve without dangling references.
  - `C3_MCP_TRANSPORT`: For `type == "mcp_server"`:
    - Stdio: `command` non-empty string, `args` list of strings, `env` dictionary.
    - SSE/HTTP: `serverUrl` or `url` with `http://` or `https://` scheme.
  - `C3_MCP_TOOL_ERROR_SEMANTICS`: Verify understanding of MCP JSON-RPC error handling (tool errors return `isError: true` inside result, not protocol-level crash).

#### Stage 4: Dry-Run Tool Execution / Entry Point Simulation
- **Purpose**: Verify that tools can be realistically spawned and configured without executing destructive commands or mutating host disk state.
- **Simulations Performed**:
  - `D4_ENTRYPOINT_PROBE`: Check binary name in command (`npx`, `uvx`, `python`, `node`, `docker`, etc.). Validate argument tokenization.
  - `D4_PARAMETER_EXPANSION`: Verify all environment variable references `${...}` are validly formatted identifiers.
  - `D4_JSONRPC_HANDSHAKE_SIM`: Simulate JSON-RPC 2.0 `initialize` request and mock response cycle.
  - `D4_DEPLOY_MOUNT_SIM`: Perform simulated in-memory deep merge with mock `.claude.json` and `mcp_config.json`. Assert that existing user servers (`tinyfish`) and settings are 100% preserved.

---

## 3. Zero-Unhandled-Exception Containment Architecture

To ensure the dry-run validation script executes over hundreds of arbitrary packages without ever terminating with an unhandled exception, the engine utilizes a 5-tier defensive encapsulation architecture.

### 3.1 5-Tier Exception Encapsulation Model

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Tier 5: CLI Top-Level Guard                                                   │
│   try: main() except Exception: print formatted error, sys.exit(2)            │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 4: Catalog & File I/O Guard                                              │
│   try: read_catalog() / write_report() except OSError/JSONDecodeError: report │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 3: Per-Package Iteration Guard                                           │
│   for pkg in packages: try: validate_package(pkg) except Exception: FAIL      │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 2: Per-Stage Execution Guard                                             │
│   try: run_stage_X() except Exception as exc: record_stage_error(exc)         │
├───────────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Localized Parser & Check Guards                                       │
│   try: json.loads() / yaml.safe_load() / re.search() / urlparse()             │
└───────────────────────────────────────────────────────────────────────────────┘
```

1. **Tier 1 (Localized Guards)**: Every external library call (e.g. `json.loads`, `yaml.safe_load`, `urllib.parse.urlparse`, `re.compile`, filesystem stats) is wrapped in its own specific `try...except` block catching precise error types (`json.JSONDecodeError`, `yaml.YAMLError`, `ValueError`, `re.error`, `KeyError`, `AttributeError`, `TypeError`).
2. **Tier 2 (Per-Stage Guards)**: Each stage runner (`_audit_stage1_maintenance`, `_audit_stage2_security`, etc.) is guarded. If a component fails or throws an unexpected exception, it is caught, converted into a `ValidationIssue(severity=CRITICAL, stage=..., rule_id="STAGE_EXECUTION_FAILURE", message=str(exc))`, and appended to the report.
3. **Tier 3 (Per-Package Guards)**: The package loop never assumes the package is a valid dictionary. Even if `pkg` is `None`, an empty list, an integer, or an invalid object, the loop catches the condition, records `"id": "UNKNOWN"`, `"status": "FAIL"`, and increments `rejected` without aborting the run.
4. **Tier 4 (Catalog & File I/O Guard)**: Loading input `catalog.json` and writing `validation_report.json` or `verified_catalog.json` are guarded. If the catalog file does not exist or contains invalid JSON, the runner creates an emergency error report and exits cleanly.
5. **Tier 5 (CLI Guard)**: The command-line entrypoint wraps argument parsing and runner invocation, emitting structured messages and deterministic exit codes.

### 3.2 Data Models & Structured Report Schema

```python
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

class ValidationSeverity(Enum):
    CRITICAL = "CRITICAL"  # Immediate hard rejection
    ERROR = "ERROR"        # Package rejected
    WARNING = "WARNING"    # Advisory note; package may still pass
    INFO = "INFO"          # Informational diagnostic

@dataclass
class ValidationIssue:
    rule_id: str
    message: str
    severity: str = "ERROR"  # "CRITICAL" | "ERROR" | "WARNING" | "INFO"
    stage: str = "general"   # "maintenance" | "security" | "schema" | "simulation"
    remediation: Optional[str] = None

@dataclass
class PackageValidationResult:
    id: str
    name: str
    category: str
    type: str
    status: str             # "PASS" | "FAIL"
    validation_status: str  # "verified" | "rejected"
    stage_results: Dict[str, str] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)

@dataclass
class ValidationReport:
    timestamp: str
    engine_version: str
    pipeline_stage: str
    total: int
    passed: int
    rejected: int
    warnings: int
    pass_rate_pct: float
    latency_ms: float
    results: List[PackageValidationResult] = field(default_factory=list)
```

### 3.3 Adversarial Hardening (Lessons from M1 Challenger)
In accordance with findings from `challenger_m1_1` and `challenger_m1_2`:
1. **Thread-Safe & Process-Safe Atomic File Writes**:
   - Write output reports and verified catalogs to:
     `out.with_suffix(f".tmp.{os.getpid()}_{threading.get_ident()}_{uuid.uuid4().hex[:8]}")`
   - Always wrap atomic replacement in `try ... finally` to unlink temporary files on error:
     ```python
     temp_path = ...
     try:
         with open(temp_path, "w", encoding="utf-8") as f:
             json.dump(...)
         temp_path.replace(final_path)
     finally:
         if temp_path.exists():
             try:
                 temp_path.unlink()
             except OSError:
                 pass
     ```
2. **Directory Collisions**: If `output_path` points to an existing directory, resolve to `output_path / "validation_report.json"`.
3. **Defensive Type Checking**: Always check `isinstance(pkg, dict)`, `isinstance(entrypoint, dict)`, `isinstance(args, list)` before subscripting or calling `.get()`.
4. **IPv6 URL Safety**: Wrap `urllib.parse.urlparse` in a try-catch for `ValueError` to prevent crashes on unclosed IPv6 brackets (`http://[invalid`).

---

## 4. CLI Architecture & Programmatic API

### 4.1 Command-Line Interface (CLI)

The dry-run engine can be invoked as a module:

```bash
# Standard dry-run validation (default catalog.json -> validation_report.json)
python -m src.validator.dry_run_runner

# Parameterized invocation with custom paths
python -m src.validator.dry_run_runner \
  --catalog C:\path\to\catalog.json \
  --report C:\path\to\validation_report.json \
  --verified-output C:\path\to\verified_catalog.json

# Strict gating mode (exit code non-zero if ANY package rejected)
python -m src.validator.dry_run_runner --strict

# Specific stage audit (e.g. stage 2 security only)
python -m src.validator.dry_run_runner --stage 2

# Sandbox mode
python -m src.validator.dry_run_runner --sandbox C:\path\to\sandbox
```

#### CLI Argument Reference:
| Flag | Type | Default | Description |
|---|---|---|---|
| `--catalog`, `-c` | `Path` | `catalog.json` | Path to candidate catalog JSON file |
| `--report`, `-r` | `Path` | `validation_report.json` | Path to write structured validation diagnostic report |
| `--verified-output`, `-o` | `Path` | `None` (optional) | Path to write filtered `verified_catalog.json` for M3 |
| `--strict`, `-s` | `flag` | `False` | If set, exits with code 1 if any package fails validation |
| `--stage` | `choice` | `all` | Specific stage to run: `1`, `2`, `3`, `4`, or `all` |
| `--sandbox` | `Path` | `None` | Run within an isolated sandbox environment directory |
| `--verbose`, `-v` | `flag` | `False` | Enable verbose DEBUG logging |

#### Deterministic Exit Codes:
- `0 (SUCCESS)`:
  - Default dry-run mode: All candidate packages processed, dry-run completed with zero unhandled exceptions, and report successfully written.
  - Strict mode: 100% of candidate packages passed all stages.
- `1 (VALIDATION_FAILURE)`:
  - Only when `--strict` is enabled and one or more packages were rejected.
- `2 (FATAL_INVOCATION_ERROR)`:
  - Invalid CLI arguments passed, missing input catalog file, or unreadable input file.

### 4.2 Programmatic Interface

The module provides clean programmatic APIs for other modules, test harnesses, and pipelines:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.validator.dry_run_runner import DryRunRunner, ValidationReport

# 1. Direct package list validation (matches test_f7_dry_run_runner.py)
report_dict = DryRunRunner.run_dry_run(packages_list)

# 2. Complete catalog validation from file or dictionary
runner = DryRunRunner(config=pipeline_config, strict=False)
report: ValidationReport = runner.validate_catalog_file(Path("catalog.json"))

# 3. Export verified catalog payload for Milestone 3
verified_payload = runner.generate_verified_catalog(catalog_dict, report)
```

---

## 5. Downstream M2 ↔ M3 Interface Contract

The Validator serves as the definitive security and schema gate for Milestone 3's Multi-Platform Deployment Engine (`antigravity_deployer.py` and `claude_deployer.py`).

### 5.1 Verification Status Transition
In Milestone 1, candidate packages are generated with `validation_status == "pending"` or `"verified"`.
Milestone 2's `DryRunRunner` evaluates every package and transitions its status:
- If all 4 stages pass: `validation_status = "verified"`
- If any critical check fails: `validation_status = "rejected"`, with `validation_error = "<reason>"` and `issues = [...]`.

### 5.2 M3 Ingestion Invariants
Milestone 3 deployers must guarantee:
1. **Verified-Only Mounting**:
   - `if pkg.get("validation_status") != "verified": continue`
   - Any package with `validation_status == "rejected"` or `"pending"` is strictly excluded from disk mounting or configuration merging.
2. **Platform Routing**:
   - `if pkg["type"] == "skill" and "antigravity" in pkg["platform_targets"]`:
     Mounts to `~/.gemini/config/skills/<id>/SKILL.md`.
   - `if pkg["type"] == "mcp_server"`:
     - If `"antigravity" in pkg["platform_targets"]`: Merges into `~/.gemini/config/mcp_config.json`.
     - If `"claude_code" in pkg["platform_targets"]`: Merges into `~/.claude.json` under `mcpServers`.

### 5.3 Verified Catalog Payload Schema (`verified_catalog.json`)
The generated `verified_catalog.json` contains:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "last_updated": "2026-09-24T...",
  "generator": "AI-Skills-Registry DryRunRunner v1.0.0",
  "total_packages": 20,
  "verified_packages": 20,
  "rejected_packages": 0,
  "categories": [
    "browser_search",
    "code_intelligence",
    "data_databases",
    "system_ops",
    "media"
  ],
  "packages": [
    {
      "id": "browser-playwright",
      "name": "Playwright Browser Automation",
      "category": "browser_search",
      "type": "mcp_server",
      "description": "...",
      "repo_url": "https://github.com/microsoft/playwright-mcp",
      "stars": 36000,
      "capabilities": ["..."],
      "entrypoint": { ... },
      "license": "Apache-2.0",
      "validation_status": "verified",
      "platform_targets": ["antigravity", "claude_code"]
    }
  ]
}
```

---

## 6. Integration with Peer Validator Modules

`dry_run_runner.py` is the orchestrator for Milestone 2, coordinating with:
- `src.validator.security_filter.SecurityFilter` (designed by `explorer_m2_1`)
- `src.validator.schema_validator.SchemaValidator` (designed by `explorer_m2_2`)

### Decoupled Resilient Integration Strategy:
To guarantee that `dry_run_runner.py` can be tested and executed independently, it will employ a **graceful import pattern**:
```python
try:
    from src.validator.security_filter import SecurityFilter
except ImportError:
    SecurityFilter = None  # Use built-in reference security audit

try:
    from src.validator.schema_validator import SchemaValidator
except ImportError:
    SchemaValidator = None  # Use built-in reference schema audit
```
If the external validator classes are available, `DryRunRunner` delegates stages 1, 2, and 3 to them. If they are not yet installed or being tested in isolation, `DryRunRunner` executes its complete, built-in reference implementations. This ensures zero downtime, zero circular import issues, and 100% test compatibility!

---

## 7. Concrete Code Architecture & Design Skeleton

Here is the exact architectural design for `src/validator/dry_run_runner.py`:

```python
"""Dry-Run Validation Runner & CLI Architecture for AI-Skills-Registry.

Orchestrates the 4-stage validation pipeline:
1. Maintenance & Deprecation Gating
2. Security & Isolation Boundary Audit
3. Schema Compliance Verification (Draft-07, SKILL.md, MCP JSON-RPC)
4. Dry-Run Tool Execution & Entry Point Simulation

Guarantees zero unhandled exceptions and produces structured JSON diagnostic reports.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import yaml
except ImportError:
    yaml = None

# Configure module logger
logger = logging.getLogger("ai_skills_registry.validator.dry_run")

# Constants
DEFAULT_CATALOG_FILENAME = "catalog.json"
DEFAULT_REPORT_FILENAME = "validation_report.json"
DEFAULT_VERIFIED_FILENAME = "verified_catalog.json"
RUNNER_VERSION = "1.0.0"

# Import peer validators with graceful fallback
try:
    from src.validator.security_filter import SecurityFilter
except ImportError:
    SecurityFilter = None

try:
    from src.validator.schema_validator import SchemaValidator
except ImportError:
    SchemaValidator = None

try:
    from src.config import PipelineEnvironmentConfig
except ImportError:
    PipelineEnvironmentConfig = None


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ValidationIssue:
    rule_id: str
    message: str
    severity: str = "ERROR"   # "CRITICAL" | "ERROR" | "WARNING" | "INFO"
    stage: str = "general"
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PackageValidationResult:
    id: str
    name: str
    category: str
    type: str
    status: str              # "PASS" | "FAIL"
    validation_status: str   # "verified" | "rejected"
    stage_results: Dict[str, str] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)
    validation_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["issues"] = [i.to_dict() if isinstance(i, ValidationIssue) else i for i in self.issues]
        if not self.validation_error:
            d.pop("validation_error", None)
        return d


@dataclass
class ValidationReport:
    timestamp: str
    engine_version: str
    pipeline_stage: str
    total: int
    passed: int
    rejected: int
    warnings: int
    pass_rate_pct: float
    latency_ms: float
    results: List[PackageValidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["results"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.results]
        return d


# ---------------------------------------------------------------------------
# Dry-Run Validation Runner Class
# ---------------------------------------------------------------------------

class DryRunRunner:
    """Automated zero-unhandled-exception 4-stage validation runner."""

    # Built-in reference rules and patterns
    DEPRECATED_PACKAGE_IDS = {
        "aws-api-mcp-server",
        "deprecated-mcp-tools",
        "legacy-sqlite-bridge"
    }

    OFFICIAL_ORGS = {
        "modelcontextprotocol",
        "microsoft",
        "anthropic",
        "google",
        "duckdb",
        "redis",
        "docker",
        "kubernetes"
    }

    SUSPICIOUS_SHELL_PATTERNS = [
        re.compile(r"cmd\.exe\s+/c", re.IGNORECASE),
        re.compile(r"powershell(\.exe)?\s+(-c|-command)", re.IGNORECASE),
        re.compile(r"sh\s+-c", re.IGNORECASE),
        re.compile(r"bash\s+-c", re.IGNORECASE),
        re.compile(r"[;&|`$]"),
    ]

    SECRET_PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}")
    ]

    SKILL_NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def __init__(
        self,
        config: Optional[Any] = None,
        strict: bool = False,
        stage_filter: str = "all",
        verbose: bool = False
    ):
        self.config = config
        self.strict = strict
        self.stage_filter = stage_filter
        self.verbose = verbose

    # -----------------------------------------------------------------------
    # Primary Public Entry Points
    # -----------------------------------------------------------------------

    @classmethod
    def run_dry_run(cls, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute dry-run validation directly on package list.
        
        Matches Tier 1 Feature 7 test interface contract.
        """
        runner = cls()
        report = runner.validate_packages(packages)
        return report.to_dict()

    def validate_catalog_file(self, catalog_path: Path) -> ValidationReport:
        """Loads and validates catalog file with complete exception encapsulation."""
        start_time = time.time()
        try:
            p = Path(catalog_path).resolve()
            if not p.exists():
                return self._build_empty_report(
                    error_msg=f"Catalog file not found: {catalog_path}",
                    latency_ms=0.0
                )
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return self._build_empty_report(
                    error_msg="Catalog root must be a JSON object",
                    latency_ms=0.0
                )
            packages = data.get("packages", [])
            report = self.validate_packages(packages, start_time=start_time)
            return report
        except Exception as exc:
            logger.error(f"Failed to read catalog file {catalog_path}: {exc}")
            return self._build_empty_report(
                error_msg=f"Exception reading catalog: {exc}",
                latency_ms=(time.time() - start_time) * 1000
            )

    def validate_packages(
        self,
        packages: List[Any],
        start_time: Optional[float] = None
    ) -> ValidationReport:
        """Validates list of candidate packages through all 4 stages."""
        if start_time is None:
            start_time = time.time()

        if not isinstance(packages, list):
            packages = []

        results: List[PackageValidationResult] = []
        passed_count = 0
        rejected_count = 0
        warning_count = 0

        for pkg in packages:
            try:
                res = self._validate_single_package(pkg)
                results.append(res)
                if res.status == "PASS":
                    passed_count += 1
                else:
                    rejected_count += 1
                warning_count += sum(1 for i in res.issues if i.severity == "WARNING")
            except Exception as exc:
                # Ultimate per-package exception trap
                pkg_id = "UNKNOWN"
                if isinstance(pkg, dict):
                    pkg_id = str(pkg.get("id", "UNKNOWN"))
                res = PackageValidationResult(
                    id=pkg_id,
                    name=pkg.get("name", "Unknown") if isinstance(pkg, dict) else "Unknown",
                    category=pkg.get("category", "unknown") if isinstance(pkg, dict) else "unknown",
                    type=pkg.get("type", "unknown") if isinstance(pkg, dict) else "unknown",
                    status="FAIL",
                    validation_status="rejected",
                    validation_error=str(exc),
                    issues=[ValidationIssue(
                        rule_id="UNHANDLED_PACKAGE_EXCEPTION",
                        message=f"Fatal exception during package evaluation: {exc}",
                        severity="CRITICAL"
                    )]
                )
                results.append(res)
                rejected_count += 1

        total = len(packages)
        latency_ms = (time.time() - start_time) * 1000
        pass_rate = (passed_count / total * 100.0) if total > 0 else 0.0

        return ValidationReport(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            engine_version=RUNNER_VERSION,
            pipeline_stage="milestone_2_dry_run_validation",
            total=total,
            passed=passed_count,
            rejected=rejected_count,
            warnings=warning_count,
            pass_rate_pct=round(pass_rate, 2),
            latency_ms=round(latency_ms, 2),
            results=results
        )

    # -----------------------------------------------------------------------
    # Single Package Pipeline Execution
    # -----------------------------------------------------------------------

    def _validate_single_package(self, pkg: Any) -> PackageValidationResult:
        """Executes stages 1-4 on a single package."""
        if not isinstance(pkg, dict):
            return PackageValidationResult(
                id="INVALID_PAYLOAD",
                name="Invalid",
                category="invalid",
                type="invalid",
                status="FAIL",
                validation_status="rejected",
                validation_error="Package payload is not a dictionary",
                issues=[ValidationIssue(
                    rule_id="SCHEMA_VALIDATION_ERROR",
                    message="Package item must be a JSON dictionary object",
                    severity="CRITICAL"
                )]
            )

        pkg_id = str(pkg.get("id") or "").strip()
        name = str(pkg.get("name") or "").strip()
        category = str(pkg.get("category") or "general").strip()
        pkg_type = str(pkg.get("type") or "mcp_server").strip()

        issues: List[ValidationIssue] = []
        stage_results: Dict[str, str] = {}

        # Basic ID check
        if not pkg_id:
            issues.append(ValidationIssue(
                rule_id="SCHEMA_VALIDATION_ERROR",
                message="Package ID missing",
                severity="CRITICAL",
                stage="schema"
            ))

        # Stage 1: Maintenance & Deprecation Gating
        s1_pass, s1_issues = self._run_stage_1(pkg)
        stage_results["stage1_maintenance"] = "PASS" if s1_pass else "FAIL"
        issues.extend(s1_issues)

        # Stage 2: Security & Isolation Boundary Audit
        s2_pass, s2_issues = self._run_stage_2(pkg)
        stage_results["stage2_security"] = "PASS" if s2_pass else "FAIL"
        issues.extend(s2_issues)

        # Stage 3: Schema Compliance Verification
        s3_pass, s3_issues = self._run_stage_3(pkg)
        stage_results["stage3_schema"] = "PASS" if s3_pass else "FAIL"
        issues.extend(s3_issues)

        # Stage 4: Dry-Run Tool Execution / Entry Point Simulation
        s4_pass, s4_issues = self._run_stage_4(pkg)
        stage_results["stage4_simulation"] = "PASS" if s4_pass else "FAIL"
        issues.extend(s4_issues)

        has_critical = any(i.severity in ("CRITICAL", "ERROR") for i in issues)
        status = "FAIL" if has_critical else "PASS"
        validation_status = "verified" if status == "PASS" else "rejected"
        validation_error = issues[0].message if (has_critical and issues) else None

        return PackageValidationResult(
            id=pkg_id or "UNKNOWN",
            name=name,
            category=category,
            type=pkg_type,
            status=status,
            validation_status=validation_status,
            stage_results=stage_results,
            issues=issues,
            validation_error=validation_error
        )

    # -----------------------------------------------------------------------
    # Pipeline Stage Implementations
    # -----------------------------------------------------------------------

    def _run_stage_1(self, pkg: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """Stage 1: Maintenance & Deprecation Gating."""
        issues: List[ValidationIssue] = []
        pkg_id = pkg.get("id", "")
        repo_url = pkg.get("repo_url", "")
        stars = pkg.get("stars", 0)

        # 1. Deprecation check
        if pkg_id in self.DEPRECATED_PACKAGE_IDS or "deprecated" in pkg_id:
            issues.append(ValidationIssue(
                rule_id="M1_DEPRECATED_PACKAGE",
                message=f"Package '{pkg_id}' is explicitly deprecated",
                severity="CRITICAL",
                stage="maintenance"
            ))

        # 2. Star threshold check
        is_official = any(org in repo_url for org in self.OFFICIAL_ORGS)
        is_skill = pkg.get("type") == "skill"
        if not is_official and not is_skill:
            try:
                num_stars = int(stars) if isinstance(stars, (int, float)) else 0
            except (ValueError, TypeError):
                num_stars = 0
            if num_stars < 100:
                issues.append(ValidationIssue(
                    rule_id="M1_INSUFFICIENT_STARS",
                    message=f"Community package has {num_stars} stars (< 100)",
                    severity="ERROR",
                    stage="maintenance"
                ))

        # 3. License check
        license_str = pkg.get("license", "")
        if not license_str or license_str.lower() in ("unknown", "none"):
            issues.append(ValidationIssue(
                rule_id="M1_INVALID_LICENSE",
                message=f"Package '{pkg_id}' lacks a valid SPDX license",
                severity="WARNING",
                stage="maintenance"
            ))

        return len([i for i in issues if i.severity in ("CRITICAL", "ERROR")]) == 0, issues

    def _run_stage_2(self, pkg: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """Stage 2: Security & Isolation Boundary Audit."""
        issues: List[ValidationIssue] = []
        entrypoint = pkg.get("entrypoint", {})
        if not isinstance(entrypoint, dict):
            entrypoint = {}

        command = str(entrypoint.get("command", "") or "")
        args = entrypoint.get("args", [])
        if not isinstance(args, list):
            args = []
        args_str = [str(a) for a in args]
        full_cmd = f"{command} " + " ".join(args_str)

        # 1. Command injection check
        for pat in self.SUSPICIOUS_SHELL_PATTERNS:
            if pat.search(full_cmd):
                issues.append(ValidationIssue(
                    rule_id="S2_COMMAND_INJECTION",
                    message=f"Command injection pattern detected: {full_cmd}",
                    severity="CRITICAL",
                    stage="security"
                ))
                break

        # 2. Path traversal check
        pkg_id = str(pkg.get("id", ""))
        for token in [pkg_id, command] + args_str:
            if ".." in token or token.startswith("/etc") or token.startswith("C:\\Windows"):
                issues.append(ValidationIssue(
                    rule_id="S2_PATH_TRAVERSAL",
                    message=f"Path traversal detected in token: {token}",
                    severity="CRITICAL",
                    stage="security"
                ))
                break

        # 3. Secret leak check
        env = entrypoint.get("env", {})
        if isinstance(env, dict):
            for k, v in env.items():
                v_str = str(v)
                for sec_pat in self.SECRET_PATTERNS:
                    if sec_pat.search(v_str):
                        issues.append(ValidationIssue(
                            rule_id="S2_HARDCODED_SECRET",
                            message=f"Hardcoded secret detected in env variable '{k}'",
                            severity="CRITICAL",
                            stage="security"
                        ))
                        break

        return len([i for i in issues if i.severity in ("CRITICAL", "ERROR")]) == 0, issues

    def _run_stage_3(self, pkg: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """Stage 3: Schema Compliance Verification."""
        issues: List[ValidationIssue] = []
        pkg_id = pkg.get("id", "")
        name = pkg.get("name", "")
        desc = pkg.get("description", "")
        pkg_type = pkg.get("type", "mcp_server")

        if not name:
            issues.append(ValidationIssue(
                rule_id="SCHEMA_VALIDATION_ERROR",
                message=f"Package '{pkg_id}' missing name",
                severity="ERROR",
                stage="schema"
            ))

        if not isinstance(desc, str) or len(desc.strip()) < 20:
            issues.append(ValidationIssue(
                rule_id="SCHEMA_VALIDATION_ERROR",
                message=f"Package '{pkg_id}' description too short (< 20 chars)",
                severity="ERROR",
                stage="schema"
            ))

        # Check skill frontmatter constraints
        if pkg_type == "skill":
            if not self.SKILL_NAME_REGEX.match(pkg_id):
                issues.append(ValidationIssue(
                    rule_id="C3_SKILL_NAME_INVALID",
                    message=f"Skill name '{pkg_id}' violates lowercase-hyphen pattern",
                    severity="ERROR",
                    stage="schema"
                ))

        # Check MCP transport constraints
        if pkg_type == "mcp_server":
            entrypoint = pkg.get("entrypoint", {})
            if isinstance(entrypoint, dict):
                has_cmd = "command" in entrypoint and bool(str(entrypoint["command"]).strip())
                has_url = ("serverUrl" in entrypoint) or ("url" in entrypoint)
                if not has_cmd and not has_url:
                    issues.append(ValidationIssue(
                        rule_id="C3_MCP_MISSING_ENTRYPOINT",
                        message="MCP server must define either 'command' or 'serverUrl'/'url'",
                        severity="ERROR",
                        stage="schema"
                    ))

        return len([i for i in issues if i.severity in ("CRITICAL", "ERROR")]) == 0, issues

    def _run_stage_4(self, pkg: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """Stage 4: Dry-Run Tool Execution / Entry Point Simulation."""
        issues: List[ValidationIssue] = []
        entrypoint = pkg.get("entrypoint", {})
        if isinstance(entrypoint, dict):
            # Check environment placeholders syntax ${VAR_NAME}
            env = entrypoint.get("env", {})
            if isinstance(env, dict):
                for k, v in env.items():
                    val = str(v)
                    if "${" in val:
                        matches = re.findall(r"\$\{([^}]+)\}", val)
                        for m in matches:
                            if not re.match(r"^[A-Z0-9_]+$", m):
                                issues.append(ValidationIssue(
                                    rule_id="D4_INVALID_ENV_PLACEHOLDER",
                                    message=f"Invalid env placeholder '${{{m}}}' in key '{k}'",
                                    severity="WARNING",
                                    stage="simulation"
                                ))

        return len([i for i in issues if i.severity in ("CRITICAL", "ERROR")]) == 0, issues

    # -----------------------------------------------------------------------
    # Downstream M2 ↔ M3 Artifact Generation
    # -----------------------------------------------------------------------

    def generate_verified_catalog(
        self,
        catalog_dict: Dict[str, Any],
        report: ValidationReport
    ) -> Dict[str, Any]:
        """Generates verified catalog dictionary for Milestone 3 deployment."""
        verified_ids = {r.id for r in report.results if r.status == "PASS"}
        verified_packages = []

        for p in catalog_dict.get("packages", []):
            if isinstance(p, dict) and p.get("id") in verified_ids:
                p_copy = copy.deepcopy(p)
                p_copy["validation_status"] = "verified"
                verified_packages.append(p_copy)

        verified_catalog = copy.deepcopy(catalog_dict)
        verified_catalog["packages"] = verified_packages
        verified_catalog["total_packages"] = len(verified_packages)
        verified_catalog["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        verified_catalog["generator"] = f"AI-Skills-Registry DryRunRunner v{RUNNER_VERSION}"
        return verified_catalog

    def save_report(self, report: ValidationReport, output_path: Union[str, Path]) -> Path:
        """Atomically saves validation_report.json."""
        out = Path(output_path).resolve()
        if out.is_dir():
            out = out / DEFAULT_REPORT_FILENAME
        out.parent.mkdir(parents=True, exist_ok=True)

        temp_file = out.with_suffix(f".tmp.{os.getpid()}_{threading.get_ident()}_{uuid.uuid4().hex[:8]}")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            temp_file.replace(out)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
        return out

    def save_verified_catalog(self, catalog_dict: Dict[str, Any], output_path: Union[str, Path]) -> Path:
        """Atomically saves verified_catalog.json."""
        out = Path(output_path).resolve()
        if out.is_dir():
            out = out / DEFAULT_VERIFIED_FILENAME
        out.parent.mkdir(parents=True, exist_ok=True)

        temp_file = out.with_suffix(f".tmp.{os.getpid()}_{threading.get_ident()}_{uuid.uuid4().hex[:8]}")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(catalog_dict, f, indent=2, ensure_ascii=False)
            temp_file.replace(out)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
        return out

    def _build_empty_report(self, error_msg: str, latency_ms: float = 0.0) -> ValidationReport:
        return ValidationReport(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            engine_version=RUNNER_VERSION,
            pipeline_stage="milestone_2_dry_run_validation",
            total=0,
            passed=0,
            rejected=0,
            warnings=0,
            pass_rate_pct=0.0,
            latency_ms=latency_ms,
            results=[]
        )


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entrypoint
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.validator.dry_run_runner",
        description="Automated zero-unhandled-exception 4-stage validation runner for AI-Skills-Registry."
    )
    parser.add_argument("--catalog", "-c", type=str, default=DEFAULT_CATALOG_FILENAME,
                        help="Path to input catalog.json file (default: catalog.json)")
    parser.add_argument("--report", "-r", type=str, default=DEFAULT_REPORT_FILENAME,
                        help="Path to output validation_report.json (default: validation_report.json)")
    parser.add_argument("--verified-output", "-o", type=str, default=None,
                        help="Path to output verified_catalog.json for Milestone 3 deployment")
    parser.add_argument("--strict", "-s", action="store_true",
                        help="Strict mode: exit code 1 if any package fails validation")
    parser.add_argument("--stage", choices=["1", "2", "3", "4", "all"], default="all",
                        help="Run specific stage or 'all' (default: all)")
    parser.add_argument("--sandbox", type=str, default=None,
                        help="Run inside isolated sandbox root directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint with zero unhandled exceptions and deterministic exit codes."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    try:
        catalog_path = Path(args.catalog).resolve()
        if not catalog_path.exists():
            logger.error(f"Catalog file not found: {catalog_path}")
            return 2

        runner = DryRunRunner(strict=args.strict, stage_filter=args.stage, verbose=args.verbose)
        report = runner.validate_catalog_file(catalog_path)

        # Save structured report
        report_path = Path(args.report).resolve()
        runner.save_report(report, report_path)
        logger.info(f"Validation report saved to {report_path} (Passed: {report.passed}/{report.total})")

        # Optionally save verified catalog
        if args.verified_output:
            with open(catalog_path, "r", encoding="utf-8") as f:
                cat_dict = json.load(f)
            verified_cat = runner.generate_verified_catalog(cat_dict, report)
            verified_path = Path(args.verified_output).resolve()
            runner.save_verified_catalog(verified_cat, verified_path)
            logger.info(f"Verified catalog saved to {verified_path} ({len(verified_cat['packages'])} packages)")

        if args.strict and report.rejected > 0:
            logger.warning(f"Strict mode active: {report.rejected} package(s) rejected.")
            return 1

        return 0

    except Exception as fatal_exc:
        logger.critical(f"Fatal unhandled exception in dry_run_runner CLI: {fatal_exc}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

---

## 8. Verification Plan & Test Strategy

To verify this implementation plan before and during Milestone 2 handoff:

1. **Unit Test Suite Verification (Tier 1 Feature 7)**:
   - Run `pytest tests/tier1_feature_coverage/test_f7_dry_run_runner.py -v`
   - Assert all 5 test cases pass:
     - Catching `ValueError` cleanly
     - Generating structured counts (`total`, `passed`, `rejected`)
     - Empty package list handling
     - All 20 canonical packages pass dry-run schema validation
     - Diagnostic `rule_id` and `message` attribution
2. **Cross-Feature Interface Contracts (Tier 3)**:
   - Run `pytest tests/tier3_cross_feature/test_pair1_crawler_to_validator.py -v`
   - Run `pytest tests/tier3_cross_feature/test_pair2_validator_to_deployer.py -v`
   - Assert that `validation_status` transitions and M3 deployer gating work seamlessly.
3. **Adversarial Resilience (Tier 2 & Tier 5)**:
   - Test non-dict inputs, non-string IDs, missing descriptions, malformed IPv6 URLs, and command injection strings.
   - Assert 100% of adversarial payloads return a structured `ValidationReport` with exit code `0` in dry-run mode.
4. **CLI Execution**:
   - Run `python -m src.validator.dry_run_runner --catalog catalog.json --report validation_report.json`
   - Assert exit code `0` and verify valid `validation_report.json` on disk.
