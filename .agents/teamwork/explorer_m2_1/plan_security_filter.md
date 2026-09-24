# Implementation Plan: Security, Deprecation & Vulnerability Filter (`src/validator/security_filter.py`)

**Milestone**: Milestone 2: Quality, Security & Schema Validation Engine  
**Author**: `explorer_m2_1` (Teamwork Explorer)  
**Target Path**: `src/validator/security_filter.py`  
**Related Modules**: `src/config.py`, `src/crawler/github_crawler.py`, `src/validator/dry_run_runner.py`  
**Test Suites**: `tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py`, `tests/tier2_boundary_corner/test_bva_security_and_injection.py`, `tests/tier4_real_world/test_scenario4_adversarial_rejection_pipeline.py`

---

## 1. Executive Summary & Architectural Scope

The **Security, Deprecation & Vulnerability Filter** (`src/validator/security_filter.py`) serves as the defensive perimeter for the AI-Skills-Registry pipeline. Operating across Stages 1 and 2 of the 4-Stage Dry-Run Pipeline, it ensures that no malicious, unmaintained, deprecated, or misconfigured tool package is ever deployed to local environments (Google Antigravity, Claude Code / Freebuff, or Codex/Cursor).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Candidate Package Input                         │
│                    (from catalog.json / seed feeds)                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Stage 1: Deprecation & Maintenance Gating (DeprecationAuditor)         │
│  - Known Deprecation Blacklist (e.g. aws-api-mcp-server -> awslabs/mcp)│
│  - Community Stars Threshold (stars >= 100 unless official org)        │
│  - Commit Recency & Abandonment Heuristics (last commit <= 365 days)   │
│  - Ecosystem Flags (npm deprecated, PyPI yanked / Inactive classifier) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ [PASS]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Stage 2: Security & Isolation Boundary Audit                           │
│  ├── VulnerabilityAuditor: CVSS score gating (CVSS >= 7.0 REJECT)      │
│  ├── CommandInjectionAuditor: Shell wrappers (cmd / sh / powershell)   │
│  ├── PathContainmentAuditor: Traversal (../) & Unbounded Filesystem    │
│  ├── CredentialIsolationAuditor: Plaintext secrets -> ${ENV_VAR}       │
│  └── AwsSingleRegionPolicyAuditor: Single-region & service constraint  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ SecurityAuditResult (is_safe: bool, severity: str, violations: list)   │
│   --> Forwarded to Stage 3 (SchemaValidator) & Stage 4 (DryRunRunner)   │
└────────────────────────────────────────────────────────────────────────┘
```

In addition to filtering package candidates, this plan defines the concrete remediation patches for all 4 vulnerabilities identified in Milestone 1 adversarial testing:
1. Path traversal in backup path generation (`src/config.py` - Finding ADV-01).
2. Multi-threaded PID collisions in `save_catalog` (`src/crawler/github_crawler.py` - Challenge 1).
3. Birthday paradox collisions in 24-bit truncated backup paths (`src/config.py` - Challenge 2).
4. Malformed IPv6 URL exception leakage in `ResilientHttpClient` (`src/crawler/github_crawler.py` - Challenge 5).

---

## 2. Core Data Models & Exception Hierarchy

All data structures must be immutable, type-annotated dataclasses supporting full JSON serialization.

```python
"""Data structures and enums for Security Filter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ValidationSeverity(str, Enum):
    """Severity levels for audit findings."""
    PASS = "PASS"          # Clean pass, zero violations
    INFO = "INFO"          # Informational notice
    WARNING = "WARNING"    # Non-blocking advisory (e.g. CVSS 4.0 - 6.9)
    REJECT = "REJECT"      # Blocking rejection (CVSS >= 7.0, deprecated, injection)
    CRITICAL = "CRITICAL"  # Immediate security hazard (shell injection, secret leak)


@dataclass(frozen=True)
class SecurityViolation:
    """Represents a discrete rule failure or security advisory."""
    code: str                  # e.g. "ERR_DEPRECATED_PACKAGE", "ERR_COMMAND_INJECTION"
    severity: ValidationSeverity
    message: str               # Human-readable diagnostic description
    target_field: str          # e.g. "entrypoint.args", "entrypoint.env.API_KEY"
    remediation: str           # Actionable guidance to fix the violation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "target_field": self.target_field,
            "remediation": self.remediation,
        }


@dataclass
class SecurityAuditResult:
    """Complete audit evaluation for a single candidate package."""
    package_id: str
    is_safe: bool
    highest_severity: ValidationSeverity
    violations: List[SecurityViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "is_safe": self.is_safe,
            "highest_severity": self.highest_severity.value,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class SecurityFilterConfig:
    """Configurable thresholds and operational parameters for SecurityFilter."""
    min_community_stars: int = 100
    max_commit_age_days: int = 365
    stale_commit_age_days: int = 180
    stale_open_issues_threshold: int = 50
    cvss_reject_threshold: float = 7.0
    cvss_warn_threshold: float = 4.0
    strict_mode: bool = False
    enforce_aws_single_region: bool = True
    project_aws_region: Optional[str] = None  # Resolved from env or ~/.aws/config
```

---

## 3. Subsystem 1: Deprecation & Abandonment Detection Engine

### 3.1 Known Deprecated Packages Database

The `DeprecationAuditor` maintains an authoritative registry of deprecated packages, their exact deprecation dates, successor packages, and deprecation rationales:

```python
KNOWN_DEPRECATED_PACKAGES: Dict[str, Dict[str, Any]] = {
    "aws-api-mcp-server": {
        "successor": "@awslabs/agent-toolkit-for-aws",
        "successor_repo": "https://github.com/awslabs/mcp",
        "deprecated_date": "2026-07-15",
        "reason": (
            "Deprecated by AWS on July 15, 2026. Superseded by the official "
            "Agent Toolkit for AWS which implements single-region safety and managed policies."
        ),
    },
    "deprecated-mcp-tools": {
        "successor": None,
        "successor_repo": None,
        "deprecated_date": "2025-11-01",
        "reason": "Legacy prototype MCP tool suite no longer supported by maintainers.",
    },
    "legacy-sqlite-bridge": {
        "successor": "mcp-server-sqlite",
        "successor_repo": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite",
        "deprecated_date": "2025-08-20",
        "reason": "Superseded by official Model Context Protocol SQLite server.",
    },
    "mcp-server-filesystem-unscoped": {
        "successor": "@modelcontextprotocol/server-filesystem",
        "successor_repo": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        "deprecated_date": "2025-10-12",
        "reason": "Unscoped community package deprecated in favor of official npm scoped package.",
    },
    "anthropic-mcp-legacy": {
        "successor": "@modelcontextprotocol/servers",
        "successor_repo": "https://github.com/modelcontextprotocol/servers",
        "deprecated_date": "2025-06-30",
        "reason": "Initial prototype Anthropic MCP servers relocated to official modelcontextprotocol monorepo.",
    },
}
```

### 3.2 Abandonment & Maintenance Heuristics

1. **Star Threshold Gate**:
   - Community repositories MUST have $\ge 100$ stars (`stars >= 100`).
   - Packages failing this threshold are rejected with `ERR_LOW_COMMUNITY_STARS`.
   - **Exemption Whitelist**: Repositories owned or maintained by verified official organizations are exempt from the 100-star minimum:
     `{"modelcontextprotocol", "awslabs", "anthropic", "anthropics", "google", "microsoft", "github", "duckdb", "docker", "kubernetes", "redis", "opencut"}`.
   - Skill-type entries (e.g. `type == "skill"`) curated for local ideation are also exempt if authored in-tree.

2. **Commit Freshness Gate**:
   - The latest commit to the repository's default branch must be $\le 365$ days old.
   - Commit age $> 365$ days triggers rejection with `ERR_ABANDONED_REPOSITORY`.
   - Stale Velocity Check: If commit age $> 180$ days AND open issues $> 50$ with zero maintainer responses in 90 days, mark as `WARN_STALE_MAINTENANCE` (or `REJECT` if in `strict_mode`).

3. **Repository State Invariants**:
   - `archived == True` -> Rejection with `ERR_REPOSITORY_ARCHIVED`.
   - `disabled == True` -> Rejection with `ERR_REPOSITORY_DISABLED`.

4. **Ecosystem & Supply-Chain Quality**:
   - **npm**: Check for deprecation notice in npm manifest `versions[latest].deprecated`.
   - **PyPI**: Check if distribution is `yanked` or includes Trove classifier `Development Status :: 7 - Inactive`.
   - **Copycat / Typosquatting Heuristic**: Reject packages that use unscoped names matching official servers (e.g. an unscoped PyPI/npm package named `server-postgres` or `server-filesystem` uploaded by an unaffiliated third party, lacking verifiable links to the official repository).

---

## 4. Subsystem 2: Security, Isolation & Boundary Containment

### 4.1 Filesystem Boundary Enforcement

Tools with local filesystem access (such as `@modelcontextprotocol/server-filesystem` or `mcp-server-filesystem`) represent high-risk attack surfaces if granted unbounded access to the host machine.

```python
class PathContainmentAuditor:
    """Enforces directory containment and filesystem safety boundaries."""

    WINDOWS_RESERVED_NAMES = {
        "con", "prn", "aux", "nul",
        "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
        "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"
    }

    UNBOUNDED_ROOT_PATTERNS = {
        "/", "\\", "c:\\", "c:/", "d:\\", "d:/", "*", "c:\\windows", "c:\\users"
    }

    TRAVERSAL_REGEX = re.compile(r"(\.\.[/\\]|[/\\]\.\.|%2e%2e|\0)", re.IGNORECASE)
    DISALLOWED_NAME_CHARS = re.compile(r'[<>:"/\\|?*]')
```

**Verification Logic**:
1. **Identifier Safety**:
   - Package `id` and Skill `name` must not contain Windows reserved device names (`con`, `prn`, `aux`, `nul`, `com1-9`, `lpt1-9`).
   - Package `id` must not contain filesystem characters (`<>:"/\\|?*`).
2. **Path Traversal Scanning**:
   - Check all tokens in `entrypoint.command`, `entrypoint.args`, and `dependencies` for path traversal substrings (`..`, `../`, `..\`, `%2e%2e`, `\0`).
   - Disallow arguments that target sensitive host roots (e.g. `/etc/passwd`, `C:\Windows\System32`, `~/.ssh`).
3. **Filesystem Server Boundary Restriction**:
   - If a package has `security_notes.filesystem_access == "scoped_read_write"` or the entrypoint references `@modelcontextprotocol/server-filesystem`:
     - Inspect `args` for directory path arguments.
     - **REJECT** if the argument specifies an unbounded root (`/`, `C:\`, `\\`, or empty string `""`).
     - **ACCEPT** only if the argument specifies a scoped local directory (e.g., `"."`, `"./workspace"`, or an explicit sandbox subfolder).

### 4.2 Command & Shell Injection Prevention

Candidate MCP servers execute via `stdio` transport. If an entrypoint uses shell interpreters or wraps commands in shell evaluation, an attacker could achieve arbitrary code execution.

```python
class CommandInjectionAuditor:
    """Prevents shell wrapper injection and execution of dangerous shell metacharacters."""

    SHELL_COMMAND_WRAPPERS = [
        re.compile(r"^cmd(\.exe)?(\s+/[ck])", re.IGNORECASE),
        re.compile(r"^powershell(\.exe)?(\s+(-c|-command|-encodedcommand))", re.IGNORECASE),
        re.compile(r"^pwsh(\.exe)?(\s+(-c|-command|-encodedcommand))", re.IGNORECASE),
        re.compile(r"^sh(\s+-c)", re.IGNORECASE),
        re.compile(r"^bash(\s+-c)", re.IGNORECASE),
        re.compile(r"^zsh(\s+-c)", re.IGNORECASE),
    ]

    SUBSHELL_AND_CONTROL_OPERATORS = re.compile(
        r"(\$\(.*\)|`.*`|&&|\|\||;|\||\s>\s|\s>>\s|\s<\s)",
        re.DOTALL
    )
```

**Verification Logic**:
1. `command` must be a direct executable name (e.g. `"npx"`, `"uvx"`, `"python"`, `"docker"`, `"rust-analyzer-mcp"`), never a shell interpreter (`cmd.exe`, `powershell`, `sh`, `bash`).
2. Neither `command` nor any element of `args` may contain chained control operators (`&&`, `||`, `;`), command substitution (`$(...)`, `` `...` ``), or I/O redirection (`>`, `>>`, `<`).
3. If detected, emit `ERR_COMMAND_INJECTION` with `CRITICAL` severity and reject immediately.

### 4.3 Credential & Secret Isolation

MCP servers often require API keys (e.g. Brave Search, GitHub, Postgres). Storing plaintext secrets in configuration files or command-line arguments creates an immediate credential leakage vulnerability.

```python
class CredentialIsolationAuditor:
    """Audits entrypoints for hardcoded plaintext secrets and enforces environment variable isolation."""

    SECRET_SIGNATURES = [
        ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9]{32,}")),
        ("ANTHROPIC_KEY", re.compile(r"sk-ant-[a-zA-Z0-9_\-]{32,}")),
        ("GITHUB_PAT_LEGACY", re.compile(r"ghp_[a-zA-Z0-9]{36}")),
        ("GITHUB_PAT_FINE_GRAINED", re.compile(r"github_pat_[a-zA-Z0-9_]{22,}")),
        ("AWS_SECRET_KEY", re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}")),
        ("AWS_SECRET_STANDALONE", re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])")),
        ("AWS_ACCESS_KEY_ID", re.compile(r"AKIA[0-9A-Z]{16}")),
        ("GENERIC_BEARER_TOKEN", re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{32,}")),
        ("PRIVATE_KEY", re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----")),
    ]

    ALLOWED_ENV_EXPANSION = re.compile(r"^\$\{?[a-zA-Z_][a-zA-Z0-9_]*\}?$")
```

**Verification Logic**:
1. **Environment Dictionary (`entrypoint.env`)**:
   - Inspect every `key: value` pair.
   - Values must strictly be environment variable placeholders (e.g. `"${BRAVE_API_KEY}"`, `"$GITHUB_TOKEN"`, or empty `""`).
   - If a value matches any pattern in `SECRET_SIGNATURES` without being an environment reference, flag `ERR_HARDCODED_SECRET` (`CRITICAL` severity).
2. **Command Arguments (`entrypoint.args`)**:
   - Inspect all argument strings.
   - Arguments matching flags like `--api-key=<val>`, `--token=<val>`, `--password=<val>` must NOT contain plaintext secrets.
3. **Preservation of Existing State**:
   - Cross-check against known existing keys (e.g. `tinyfish` in `~/.claude.json`) to guarantee validation does not overwrite or expose host credentials.

### 4.4 Vulnerability Database & CVSS Scoring

```python
class VulnerabilityAuditor:
    """Checks candidate packages against CVE advisories and CVSS score thresholds."""

    @classmethod
    def evaluate_cves(
        cls,
        package_id: str,
        known_cves: Optional[List[Dict[str, Any]]] = None,
        reject_threshold: float = 7.0,
        warn_threshold: float = 4.0
    ) -> List[SecurityViolation]:
        violations = []
        if not known_cves:
            return violations

        for cve in known_cves:
            cvss = float(cve.get("cvss", 0.0))
            cve_id = cve.get("id", "UNKNOWN-CVE")
            desc = cve.get("description", "No description provided.")

            if cvss >= reject_threshold:
                violations.append(SecurityViolation(
                    code="ERR_CRITICAL_CVE",
                    severity=ValidationSeverity.REJECT,
                    message=f"CRITICAL CVE {cve_id} (CVSS {cvss}): {desc}",
                    target_field="dependencies",
                    remediation=f"Upgrade package or patch vulnerability {cve_id}."
                ))
            elif cvss >= warn_threshold:
                violations.append(SecurityViolation(
                    code="WARN_MEDIUM_CVE",
                    severity=ValidationSeverity.WARNING,
                    message=f"Advisory CVE {cve_id} (CVSS {cvss}): {desc}",
                    target_field="dependencies",
                    remediation=f"Review security advisory {cve_id}."
                ))
        return violations
```

---

## 5. Subsystem 3: Single-Region AWS Policy Compliance

In accordance with the authoritative user rules (`<RULE[user_global]>`), all AWS infrastructure operations are strictly bound by the "new AWS experience" constraints. The `AwsSingleRegionPolicyAuditor` ensures that any AWS-related MCP servers, skills, or operational parameters strictly obey these boundaries.

### 5.1 Authoritative AWS Constraints

| Constraint Area | Rule Requirement | Policy Violation Code |
| :--- | :--- | :--- |
| **Terminology** | Say "project" (not "account"), "team member" (not "IAM user"), "AWS Settings" (not "IAM console"), "selected Region" (not "home Region"). | `WARN_AWS_TERMINOLOGY` |
| **Regional Isolation** | All Regional resources MUST be created strictly in the project's assigned region. No resources in other regions. | `ERR_AWS_MULTI_REGION` |
| **us-east-1 Exception** | AWS WAF and CloudWatch Logs CAN be in `us-east-1` ONLY when connected to global resources (like global CloudFront WAF). | Handled as legitimate exception |
| **Lambda & API Gateway** | MUST NOT create Lambda or API Gateway in any region other than the project's assigned region (specifically prohibited in `us-east-1` unless assigned). | `ERR_AWS_UNAUTHORIZED_REGION` |
| **Lambda@Edge** | MUST NOT use Lambda@Edge under any circumstances (excluded from both Lambda and CloudFront). | `ERR_AWS_LAMBDA_EDGE_PROHIBITED` |
| **CloudFormation StackSets** | MUST NOT use CloudFormation StackSets (no multi-account or multi-region deployments). | `ERR_AWS_STACKSETS_PROHIBITED` |
| **Cross-Region Replication** | MUST NOT attempt cross-region replication (no DynamoDB Global Tables, S3 Cross-Region Replication, multi-region KMS keys). | `ERR_AWS_CROSS_REGION_REPLICATION` |
| **Route 53 Routing** | MUST NOT use Route 53 cross-region routing policies (geolocation, latency-based, failover). | `ERR_AWS_ROUTE53_CROSS_REGION` |
| **eu-north-1 Exclusions** | If assigned region is `eu-north-1`: Rekognition, Textract, Personalize, and App Runner are unavailable. | `ERR_AWS_SERVICE_UNAVAILABLE` |

### 5.2 Implementation of `AwsSingleRegionPolicyAuditor`

```python
class AwsSingleRegionPolicyAuditor:
    """Validates candidate configurations against AWS Single-Region constraints."""

    DISALLOWED_SERVICES_IN_EU_NORTH_1 = {
        "rekognition", "textract", "personalize", "apprunner"
    }

    DISALLOWED_ARG_PATTERNS = [
        (re.compile(r"--stack-set", re.IGNORECASE), "ERR_AWS_STACKSETS_PROHIBITED", "CloudFormation StackSets are prohibited."),
        (re.compile(r"lambda@edge", re.IGNORECASE), "ERR_AWS_LAMBDA_EDGE_PROHIBITED", "Lambda@Edge is prohibited."),
        (re.compile(r"--cross-region-replication", re.IGNORECASE), "ERR_AWS_CROSS_REGION_REPLICATION", "Cross-region replication is prohibited."),
        (re.compile(r"global-table", re.IGNORECASE), "ERR_AWS_CROSS_REGION_REPLICATION", "DynamoDB Global Tables are prohibited."),
    ]

    @classmethod
    def audit_aws_candidate(
        cls,
        pkg: Dict[str, Any],
        assigned_region: Optional[str] = None
    ) -> List[SecurityViolation]:
        violations: List[SecurityViolation] = []
        pkg_id = pkg.get("id", "")
        pkg_name = pkg.get("name", "")

        is_aws_related = "aws" in pkg_id.lower() or "aws" in pkg_name.lower() or "amazon" in pkg_name.lower()
        if not is_aws_related:
            return violations

        entrypoint = pkg.get("entrypoint", {})
        args = entrypoint.get("args", [])
        env = entrypoint.get("env", {})
        full_args_str = " ".join(args)

        # 1. Prohibited architectures
        for pattern, code, msg in cls.DISALLOWED_ARG_PATTERNS:
            if pattern.search(full_args_str):
                violations.append(SecurityViolation(
                    code=code,
                    severity=ValidationSeverity.REJECT,
                    message=msg,
                    target_field="entrypoint.args",
                    remediation="Remove prohibited multi-region or StackSet architecture."
                ))

        # 2. Region Parameter Enforcement
        # If --region is explicitly passed in args, ensure it matches assigned_region or is ${AWS_REGION}
        for arg in args:
            if arg.startswith("--region=") or arg.startswith("--region"):
                val = arg.split("=", 1)[1] if "=" in arg else ""
                if val and val != "${AWS_REGION}" and assigned_region and val != assigned_region:
                    # Allow us-east-1 only if targeting global WAF / CloudWatch logs
                    if val == "us-east-1" and ("waf" in full_args_str.lower() or "cloudwatch" in full_args_str.lower()):
                        continue
                    violations.append(SecurityViolation(
                        code="ERR_AWS_UNAUTHORIZED_REGION",
                        severity=ValidationSeverity.REJECT,
                        message=f"Hardcoded region '{val}' violates single-region policy (assigned: {assigned_region}).",
                        target_field="entrypoint.args",
                        remediation="Use ${AWS_REGION} or the assigned project region."
                    ))

        # 3. eu-north-1 Reduced Availability Check
        if assigned_region == "eu-north-1":
            for disallowed in cls.DISALLOWED_SERVICES_IN_EU_NORTH_1:
                if disallowed in pkg_id.lower() or disallowed in full_args_str.lower():
                    violations.append(SecurityViolation(
                        code="ERR_AWS_SERVICE_UNAVAILABLE",
                        severity=ValidationSeverity.REJECT,
                        message=f"AWS service '{disallowed}' is not available in selected Region 'eu-north-1'.",
                        target_field="id",
                        remediation="Do not deploy services unsupported in eu-north-1."
                    ))

        return violations
```

---

## 6. Concrete Mitigations & Patches for M1 Adversarial Findings

During Milestone 1 adversarial evaluations by `challenger_m1_1` and `challenger_m1_2`, four distinct vulnerabilities and failure modes were uncovered. This plan includes the exact, drop-in remediation patches to be applied directly during Milestone 2 hardening.

### 6.1 Mitigation for Finding ADV-01: Path Traversal in `PipelineEnvironmentConfig.get_backup_path()`

- **Target File**: `src/config.py` lines 169–176
- **Vulnerability**: If `prefix` contains `../../`, the generated backup path escapes `backup_dir`.
- **Patch**:
  ```python
  def get_backup_path(self, target_file: Path, prefix: str = "") -> Path:
      """Computes a non-colliding timestamped backup path for the target file.
      
      Sanitizes the prefix against path traversal and enforces strict directory containment.
      """
      # 1. Sanitize prefix against path traversal characters
      clean_prefix = re.sub(r"[^a-zA-Z0-9_-]", "", prefix)
      prefix_str = f"{clean_prefix}_" if clean_prefix else ""
      
      # 2. Prevent PID and birthday paradox collisions (128-bit UUID + thread ID)
      timestamp = int(time.time())
      thread_id = threading.get_ident()
      rand_suffix = uuid.uuid4().hex[:16]
      clean_name = target_file.name.lstrip(".")
      backup_name = f"{prefix_str}{clean_name}.bak.{timestamp}_{thread_id}_{rand_suffix}"
      
      # 3. Strict containment verification
      candidate_path = (self.backup_dir / backup_name).resolve()
      resolved_backup_dir = self.backup_dir.resolve()
      if not candidate_path.is_relative_to(resolved_backup_dir):
          raise ValueError(f"Security containment failure: backup path {candidate_path} escapes {resolved_backup_dir}")
          
      return candidate_path
  ```

### 6.2 Mitigation for Challenge 1 & ST-19: Multi-Threaded PID Collisions in `save_catalog()`

- **Target File**: `src/crawler/github_crawler.py` lines 485–495
- **Vulnerability**: Temporary file uses `out.with_suffix(f".tmp.{os.getpid()}")`. In multi-threaded execution or if `out` is a directory, collisions and unhandled `PermissionError` occur without cleanup.
- **Patch**:
  ```python
  def save_catalog(self, catalog: Dict[str, Any], output_path: Union[str, Path]) -> Path:
      """Saves compiled catalog to disk atomically with thread-safe UUIDs and directory handling."""
      out = Path(output_path).resolve()
      if out.is_dir():
          out = out / "catalog.json"
      out.parent.mkdir(parents=True, exist_ok=True)
      
      # Incorporate PID, Thread ID, and cryptographic UUID
      unique_token = f"{os.getpid()}_{threading.get_ident()}_{uuid.uuid4().hex[:8]}"
      temp_file = out.with_suffix(f".tmp.{unique_token}")
      
      try:
          with open(temp_file, "w", encoding="utf-8") as f:
              json.dump(catalog, f, indent=2, ensure_ascii=False)
          temp_file.replace(out)
          logger.info(f"Catalog saved successfully to: {out} ({len(catalog['packages'])} packages)")
          return out
      finally:
          if temp_file.exists():
              try:
                  temp_file.unlink()
              except OSError:
                  pass
  ```

### 6.3 Mitigation for Challenge 5 & ST-07: Malformed IPv6 URL Exception Boundary

- **Target File**: `src/crawler/github_crawler.py` lines 100–112
- **Vulnerability**: `parsed_url = urllib.parse.urlparse(url)` is placed at line 101 outside the `try` block. URLs with unclosed brackets (`http://[invalid`) raise `ValueError: Invalid IPv6 URL` uncaught.
- **Patch**:
  ```python
  def get_json(
      self,
      url: str,
      extra_headers: Optional[Dict[str, str]] = None,
  ) -> Tuple[Optional[Dict[str, Any]], CrawlStatus]:
      start_time = time.time()
      
      # Wrap URL parsing in exception guard
      try:
          parsed_url = urllib.parse.urlparse(url)
          domain = parsed_url.netloc
      except (ValueError, Exception) as url_err:
          latency = (time.time() - start_time) * 1000
          logger.warning(f"Malformed URL '{url}': {url_err}")
          return None, CrawlStatus(
              source="fallback",
              timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              warnings=[f"Malformed URL rejected: {url_err}"],
              latency_ms=latency,
          )

      if domain in self._rate_limited_domains:
          latency = (time.time() - start_time) * 1000
          return None, CrawlStatus(
              source="fallback",
              timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              warnings=[f"Domain {domain} previously encountered rate-limit."],
              latency_ms=latency,
          )
      ...
  ```

### 6.4 Mitigation for Challenges 3, 4, 6: Metadata Normalizer Robustness

- **Target File**: `src/crawler/github_crawler.py` lines 270–290 & 460–465
- **Vulnerabilities**: Non-dict JSON triggers `AttributeError`; `None` star counts trigger `TypeError`; missing `"category"` triggers `KeyError`.
- **Patch**:
  ```python
  # Safe star count conversion:
  if isinstance(github_data, dict):
      raw_stars = github_data.get("stargazers_count")
      if isinstance(raw_stars, (int, float)):
          stars = int(raw_stars)
      elif isinstance(raw_stars, str) and raw_stars.isdigit():
          stars = int(raw_stars)
      else:
          stars = seed_package.get("stars", 0)

  # Defensive category extraction:
  cats_found = {p.get("category") for p in seed_packages if isinstance(p, dict) and "category" in p}
  ```

---

## 7. Master Facade Design: `SecurityFilter`

The master facade `SecurityFilter` coordinates all auditor subsystems into a unified, thread-safe, zero-unhandled-exception interface.

```python
class SecurityFilter:
    """Master Security and Deprecation Filter engine for AI-Skills-Registry."""

    def __init__(self, config: Optional[SecurityFilterConfig] = None):
        self.config = config or SecurityFilterConfig()

    def audit_package(
        self,
        package: Dict[str, Any],
        known_cves: Optional[List[Dict[str, Any]]] = None
    ) -> SecurityAuditResult:
        """Runs candidate package through all security, deprecation, and boundary checks.
        
        Zero-unhandled-exception guarantee: Catches any unexpected formatting or parsing
        errors and returns a structured SecurityAuditResult with CRITICAL or REJECT status.
        """
        pkg_id = package.get("id", "unknown-package")
        violations: List[SecurityViolation] = []
        warnings: List[str] = []

        try:
            # 1. Deprecation and Abandonment Checks
            dep_violations = DeprecationAuditor.audit(package, self.config)
            violations.extend(dep_violations)

            # 2. Known CVE Vulnerability Checks
            cve_violations = VulnerabilityAuditor.evaluate_cves(
                pkg_id,
                known_cves,
                reject_threshold=self.config.cvss_reject_threshold,
                warn_threshold=self.config.cvss_warn_threshold,
            )
            violations.extend(cve_violations)

            # 3. Command and Subshell Injection Checks
            cmd_violations = CommandInjectionAuditor.audit(package)
            violations.extend(cmd_violations)

            # 4. Path Containment and Filesystem Boundaries
            path_violations = PathContainmentAuditor.audit(package)
            violations.extend(path_violations)

            # 5. Credential Isolation Checks
            cred_violations = CredentialIsolationAuditor.audit(package)
            violations.extend(cred_violations)

            # 6. Single-Region AWS Policy Checks
            if self.config.enforce_aws_single_region:
                aws_violations = AwsSingleRegionPolicyAuditor.audit_aws_candidate(
                    package,
                    assigned_region=self.config.project_aws_region
                )
                violations.extend(aws_violations)

        except Exception as audit_exc:
            violations.append(SecurityViolation(
                code="ERR_AUDIT_INTERNAL_EXCEPTION",
                severity=ValidationSeverity.CRITICAL,
                message=f"Internal exception during security audit: {type(audit_exc).__name__}: {audit_exc}",
                target_field="root",
                remediation="Ensure candidate package dictionary conforms to required schema types."
            ))

        # Determine highest severity and pass/fail
        severities = {v.severity for v in violations}
        if ValidationSeverity.CRITICAL in severities or ValidationSeverity.REJECT in severities:
            highest_sev = ValidationSeverity.CRITICAL if ValidationSeverity.CRITICAL in severities else ValidationSeverity.REJECT
            is_safe = False
        elif ValidationSeverity.WARNING in severities:
            highest_sev = ValidationSeverity.WARNING
            is_safe = True
        else:
            highest_sev = ValidationSeverity.PASS
            is_safe = True

        return SecurityAuditResult(
            package_id=pkg_id,
            is_safe=is_safe,
            highest_severity=highest_sev,
            violations=violations,
            warnings=warnings,
            metadata={"total_violations": len(violations)}
        )

    def audit_catalog(
        self,
        catalog: Dict[str, Any],
        known_cves: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Audits an entire catalog and partitions packages into verified vs rejected."""
        packages = catalog.get("packages", [])
        verified: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for pkg in packages:
            res = self.audit_package(pkg, known_cves=known_cves)
            if res.is_safe:
                verified.append(pkg)
            else:
                rejected.append({
                    "package": pkg,
                    "audit_result": res.to_dict()
                })

        return {
            "total": len(packages),
            "verified_count": len(verified),
            "rejected_count": len(rejected),
            "verified": verified,
            "rejected": rejected,
        }
```

---

## 8. Interface Contracts (M1 ↔ M2 ↔ M3)

### 8.1 Ingestion Contract: M1 Crawler ↔ M2 SecurityFilter
- Input: `catalog.json` package objects conforming to Draft-07 catalog schema.
- Expected Fields: `id`, `name`, `category`, `stars`, `entrypoint`, `dependencies`, `security_notes`.
- Defensive Handling: If any optional field is absent or malformed (`None`, non-dict, non-list), default values are safely substituted.

### 8.2 Outbound Contract: M2 SecurityFilter ↔ M2 DryRunRunner (`src/validator/dry_run_runner.py`)
- `SecurityFilter.audit_package(pkg)` provides Stage 1 & Stage 2 evaluations for the DryRunRunner.
- The returned `SecurityAuditResult` is integrated directly into the final `validation_report.json`:
  ```json
  {
    "stage": "security_and_deprecation",
    "package_id": "aws-api-mcp-server",
    "passed": false,
    "severity": "REJECT",
    "violations": [
      {
        "code": "ERR_DEPRECATED_PACKAGE",
        "severity": "REJECT",
        "message": "Package 'aws-api-mcp-server' is deprecated as of 2026-07-15. Succeeded by '@awslabs/agent-toolkit-for-aws'.",
        "target_field": "id",
        "remediation": "Replace with Agent Toolkit for AWS."
      }
    ]
  }
  ```

### 8.3 Downstream Contract: M2 Validator ↔ M3 Deployer (`src/deployer/`)
- M3 deployment engine receives only packages where `audit_result.is_safe == True`.
- Any package flagged with `CRITICAL` or `REJECT` is excluded from installation to `~/.gemini/config/skills/` and `~/.claude.json`.

---

## 9. Implementation Work Breakdown Structure (WBS)

| Task ID | Component / File | Description | Target Agent |
| :--- | :--- | :--- | :--- |
| **M2-SEC-01** | `src/validator/security_filter.py` | Implement `ValidationSeverity`, `SecurityViolation`, `SecurityAuditResult`, and `SecurityFilterConfig`. | Worker M2 |
| **M2-SEC-02** | `src/validator/security_filter.py` | Implement `DeprecationAuditor` with known blacklist (`aws-api-mcp-server`, etc.), commit age, and star gates. | Worker M2 |
| **M2-SEC-03** | `src/validator/security_filter.py` | Implement `CommandInjectionAuditor` (shell wrappers, metacharacters, subshells). | Worker M2 |
| **M2-SEC-04** | `src/validator/security_filter.py` | Implement `PathContainmentAuditor` (traversal, Windows reserved names, filesystem boundaries). | Worker M2 |
| **M2-SEC-05** | `src/validator/security_filter.py` | Implement `CredentialIsolationAuditor` (OpenAI, Anthropic, AWS, GitHub secrets, `${ENV}` check). | Worker M2 |
| **M2-SEC-06** | `src/validator/security_filter.py` | Implement `AwsSingleRegionPolicyAuditor` (single region, no Lambda@Edge, no StackSets, no cross-region replication). | Worker M2 |
| **M2-SEC-07** | `src/validator/security_filter.py` | Implement `SecurityFilter` facade with `audit_package()` and `audit_catalog()`. | Worker M2 |
| **M2-SEC-08** | `src/config.py` | Apply patch for ADV-01 (prefix sanitization & containment check in `get_backup_path`). | Worker M2 |
| **M2-SEC-09** | `src/crawler/github_crawler.py` | Apply patches for PID collisions (Challenge 1) and IPv6 URL exceptions (Challenge 5). | Worker M2 |
| **M2-SEC-10** | `tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py` | Replace mock implementation with tests running against production `SecurityFilter`. | Test Writer |

---

## 10. Verification & Test Strategy

Verification is divided into three test layers:

### 10.1 Layer 1: Unit & Feature Coverage Tests
- **Target**: `tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py`
- **Test Scenarios**:
  - `test_f4_rejects_known_deprecated_packages`: Rejection of `aws-api-mcp-server` and successors.
  - `test_f4_rejects_critical_cve_package`: CVSS $\ge 7.0$ triggers rejection.
  - `test_f4_permits_low_cve_package`: CVSS $< 7.0$ passes (with advisory warning).
  - `test_f4_rejects_shell_command_injection_wrappers`: `cmd.exe /c`, `powershell -c`, `sh -c`.
  - `test_f4_rejects_path_traversal_attempts`: `../../etc/passwd`.
  - `test_f4_rejects_hardcoded_secrets_in_env`: Detection of `sk-...`, `ghp_...`, `AKIA...`.

### 10.2 Layer 2: Boundary Value Analysis Tests
- **Target**: `tests/tier2_boundary_corner/test_bva_security_and_injection.py`
- **Test Scenarios**:
  - Stars boundary: 99 stars (REJECT) vs 100 stars (PASS).
  - Commit age boundary: 365 days (PASS) vs 366 days (REJECT).
  - CVSS score boundary: 6.9 (WARN) vs 7.0 (REJECT).
  - Windows reserved names: `CON`, `PRN`, `AUX`, `NUL`, `COM1`.
  - Subshell operators: `$(...)`, `` `...` ``, `&&`, `||`, `;`.

### 10.3 Layer 3: Adversarial Regression & AWS Compliance Tests
- **Target**: `tests/adversarial/test_m1_stress_harness.py` & `tests/tier4_real_world/test_scenario4_adversarial_rejection_pipeline.py`
- **Test Scenarios**:
  - Verify ADV-01 path traversal prevention in `get_backup_path()` with malicious prefix `../../escaped`.
  - Verify concurrent `save_catalog()` across 10 threads without Windows `PermissionError`.
  - Verify malformed IPv6 URLs (`http://[invalid`) gracefully handled without `ValueError`.
  - Verify AWS candidate rejection when attempting cross-region replication or Lambda@Edge.

### 10.4 Execution Command
```bash
python tests/run_all_tests.py --tier 1,2,4
```
Expected outcome: 100% test pass across all tiers with zero unhandled exceptions.
