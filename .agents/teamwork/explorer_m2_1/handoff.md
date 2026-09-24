# Handoff Report: Security, Deprecation & Vulnerability Filter Design (`src/validator/security_filter.py`)

**Agent**: `explorer_m2_1` (Teamwork Explorer)  
**Parent**: `orchestrator_1` (Conversation ID: `40a6594f-8daa-4f4a-b75e-76633ee5c4c9`)  
**Working Directory**: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1`  
**Target Module**: `src/validator/security_filter.py`  
**Plan Artifact**: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\plan_security_filter.md`  
**Date**: 2026-09-24  
**Type**: Hard Handoff (Investigation & Architecture Design Complete)

---

## 1. Observation

Direct inspection of the codebase, existing test suites, and M1 adversarial evaluation reports revealed the following concrete observations:

1. **Deprecated Candidate Packages**:
   - `ORIGINAL_REQUEST.md` line 18 mandates: *"Implement a validation filter that rejects unmaintained, deprecated, or vulnerable packages."*
   - `DISPATCH.md` line 9 specifies: *"Known deprecated packages database (e.g. `aws-api-mcp-server` deprecated July 15, 2026, succeeded by Agent Toolkit for AWS)."*
   - In `tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py` lines 20–24, the reference mock filter specifies:
     ```python
     DEPRECATED_PACKAGE_IDS = {
         "aws-api-mcp-server",
         "deprecated-mcp-tools",
         "legacy-sqlite-bridge"
     }
     ```
   - In `tests/tier4_real_world/test_scenario4_adversarial_rejection_pipeline.py` lines 30–32, `aws-api-mcp-server` is explicitly rejected with `"Explicitly deprecated"`.

2. **Filesystem Boundary Constraints**:
   - In `src/crawler/registry_sources.py` lines 449–451, `@modelcontextprotocol/server-filesystem` is invoked with:
     ```python
     "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
     ```
   - In unbounded configurations, tools might pass `"/"`, `"C:\\"`, or empty strings, giving agents uncontrolled write/read access to the host operating system.
   - `DISPATCH.md` lines 11–12 requires: *"Filesystem boundary enforcement: verify tools like `@modelcontextprotocol/server-filesystem` specify explicit boundary paths rather than unbounded root."*

3. **Credential Isolation**:
   - `tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py` lines 34–38 tests for hardcoded OpenAI keys (`sk-...`), GitHub PATs (`ghp_...`), and AWS secret access keys (`aws_secret_access_key = ...`).
   - `DISPATCH.md` line 13 specifies: *"verify API keys and tokens are supplied via environment variables, never hardcoded in args or plain text."*
   - In `src/crawler/registry_sources.py`, all valid entries with API keys use variable expansion:
     Line 153: `"BRAVE_API_KEY": "${BRAVE_API_KEY}"`
     Line 209: `"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"`

4. **Single-Region AWS Compliance Constraints**:
   - System user rule `<RULE[user_global]>` establishes strict project constraints:
     - *"All projects share a single AWS Region determined by the user's contact address. Resources cannot be created in other Regions"*
     - *"MUST create all Regional resources in the project's assigned Region"*
     - *"You CAN create AWS WAF and Cloudwatch Logs resources in us-east-1 when there are global resources... MUST NOT attempt to create Lambda, API Gateway, or other Regional resources in any other Region"*
     - *"MUST NOT use Lambda@Edge"*
     - *"MUST NOT use CloudFormation StackSets"*
     - *"MUST NOT attempt cross-Region actions — no cross-Region replication for DynamoDB/S3/RDS, no multi-Region KMS keys"*
     - *"MUST NOT use Route 53 cross-Region routing"*
     - In `eu-north-1`: Rekognition, Textract, Personalize, App Runner are unavailable.

5. **Milestone 1 Adversarial Vulnerabilities Under Empirical Confirmation**:
   - **Finding ADV-01 (Path Traversal in `PipelineEnvironmentConfig.get_backup_path`)**:
     `src/config.py` line 174–176:
     ```python
     prefix_str = f"{prefix}_" if prefix else ""
     backup_name = f"{prefix_str}{clean_name}.bak.{timestamp}_{rand_suffix}"
     return self.backup_dir / backup_name
     ```
     `challenger_m1_2` report line 49 confirmed: passing `prefix="../../escape"` escapes `self.backup_dir` entirely.
   - **Challenge 1 & ST-19 (PID Collision on Windows)**:
     `src/crawler/github_crawler.py` line 489:
     ```python
     temp_file = out.with_suffix(f".tmp.{os.getpid()}")
     ```
     `challenger_m1_1` report line 34 confirmed: 7 of 10 concurrent threads sharing the same PID crashed with `WinError 32 PermissionError` and left orphaned `.tmp` files.
   - **Challenge 2 & ST-17 (Birthday Collision on 6-hex Truncation)**:
     `src/config.py` line 172:
     ```python
     rand_suffix = uuid.uuid4().hex[:6]
     ```
     `challenger_m1_1` report line 47 confirmed 5 collisions per 10k paths in the same second due to 24-bit entropy ceiling.
   - **Challenge 5 & ST-07 (Malformed IPv6 URL Crash)**:
     `src/crawler/github_crawler.py` line 101:
     ```python
     parsed_url = urllib.parse.urlparse(url)
     ```
     Placed outside the `try` block (which begins at line 129). `challenger_m1_1` report line 86 confirmed unclosed IPv6 URLs (`http://[invalid`) raise `ValueError: Invalid IPv6 URL` causing an unhandled crash.

---

## 2. Logic Chain

1. **From Observation 1 (Deprecation)**:
   Because packages like `aws-api-mcp-server` are explicitly superseded and unmaintained packages present supply-chain risks, the validator requires a dedicated `DeprecationAuditor` with both an exact-match blacklist mapping to successors (e.g. `awslabs/mcp`) and dynamic abandonment heuristics (commit age $> 365$ days, stars $< 100$, npm `deprecated` tag, PyPI `yanked` status).

2. **From Observation 2 (Filesystem Boundaries)**:
   Because local MCP servers run with the user's host OS privileges, unbounded filesystem access represents an unrestricted read/write vector. The `PathContainmentAuditor` must inspect entrypoint arguments for root strings (`/`, `C:\`, `\\`) and path traversal sequences (`..`), restricting packages with file access capabilities to explicitly declared scoped folders.

3. **From Observation 3 (Credential Isolation)**:
   Because plaintext tokens in config files or command arguments leak into shell process trees (`ps`), log files, and shell history, `CredentialIsolationAuditor` must enforce regex matching against known secret formats (`sk-...`, `ghp_...`, `AKIA...`) and mandate that sensitive keys use environment variable expansion (`${VAR_NAME}`).

4. **From Observation 4 (Single-Region AWS Compliance)**:
   Because the user's AWS project environment strictly prohibits multi-region resources, Lambda@Edge, CloudFormation StackSets, and cross-region replication, any AWS-targeted MCP tool or deployment descriptor must be audited by `AwsSingleRegionPolicyAuditor` to ensure parameters and target regions comply with project policies.

5. **From Observation 5 (M1 Defect Hardening)**:
   Because the deployment engine (M3) and concurrent runners will rely on atomic file replacement and backup path isolation:
   - Sanitizing `prefix` via `re.sub(r"[^a-zA-Z0-9_-]", "", prefix)` and calling `.is_relative_to(self.backup_dir)` eliminates ADV-01 path traversal.
   - Incorporating `threading.get_ident()` and a full 128-bit UUID (`uuid.uuid4().hex`) into temporary filenames eliminates PID collisions and the 24-bit Birthday Paradox collisions.
   - Wrapping `urllib.parse.urlparse()` inside a `try...except (ValueError, Exception)` block prevents malformed IPv6 URLs from crashing the crawler.

6. **From Observations 1–5 to Conclusion**:
   Structuring `src/validator/security_filter.py` as a modular suite of 6 auditors orchestrated by a zero-unhandled-exception facade `SecurityFilter` directly satisfies requirement R2 from `ORIGINAL_REQUEST.md`, complies with `PROJECT.md` M2 specifications, and provides full remediation for all M1 adversarial findings.

---

## 3. Caveats

1. **Live Network OSV / CVE Lookup**: The design includes full offline CVSS threshold gating and an offline CVE advisory map. If online network access is restricted or offline mode (`--offline`) is enabled, the filter relies on the in-memory database and seed metadata rather than live HTTP queries to `api.osv.dev`.
2. **AWS Region Resolution**: In sandbox test environments where `~/.aws/config` does not exist and `AWS_REGION` is unset, `AwsSingleRegionPolicyAuditor` defaults to validating against standard single-region patterns (e.g. `us-west-2` or enforcing `${AWS_REGION}`).
3. **Shell Wrapper Disambiguation**: The command injection auditor forbids `cmd.exe /c`, `sh -c`, `bash -c`, and `powershell -c`. Direct invocations of tools that internally manage subcommands (e.g. `git diff` or `docker run`) are permitted because arguments are passed as discrete token arrays rather than unescaped shell strings.

---

## 4. Conclusion

The architectural design for `src/validator/security_filter.py` and the associated hardening fixes for M1 adversarial findings are complete, fully specified, and documented in:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\plan_security_filter.md`

Key deliverables designed:
1. `src/validator/security_filter.py`:
   - Enums & Dataclasses: `ValidationSeverity`, `SecurityViolation`, `SecurityAuditResult`, `SecurityFilterConfig`.
   - Auditors: `DeprecationAuditor`, `VulnerabilityAuditor`, `CommandInjectionAuditor`, `PathContainmentAuditor`, `CredentialIsolationAuditor`, `AwsSingleRegionPolicyAuditor`.
   - Facade: `SecurityFilter` with `audit_package()` and `audit_catalog()` providing zero unhandled exceptions.
2. Concrete M1 adversarial code patches:
   - Prefix sanitization and path containment in `PipelineEnvironmentConfig.get_backup_path()` (`src/config.py`).
   - Thread-safe UUID and directory handling in `CrawlerEngine.save_catalog()` (`src/crawler/github_crawler.py`).
   - URL parsing exception trap in `ResilientHttpClient.get_json()` (`src/crawler/github_crawler.py`).
   - Defensive type casting in `MetadataNormalizer` (`src/crawler/github_crawler.py`).

The downstream implementation worker can execute this plan with zero ambiguity.

---

## 5. Verification Method

To independently verify the architecture and its future implementation:

1. **Inspect Plan Artifact**:
   View `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\plan_security_filter.md` to confirm all class definitions, regexes, patch diffs, and integration contracts are documented.

2. **Execute Existing Tier 1 & Tier 2 Security Tests**:
   Run the following commands in the workspace root:
   ```bash
   pytest tests/tier1_feature_coverage/test_f4_security_deprecation_filter.py -v
   pytest tests/tier2_boundary_corner/test_bva_security_and_injection.py -v
   pytest tests/tier4_real_world/test_scenario4_adversarial_rejection_pipeline.py -v
   ```
   *Expected Current Result*: All 18 tests pass against existing reference/mock evaluators.
   *Post-Implementation Verification*: Once `src/validator/security_filter.py` is implemented, tests import the production module and achieve 100% pass rate.

3. **Execute Full Test Suite**:
   ```bash
   python tests/run_all_tests.py
   ```
   *Expected Result*: All 183+ tests across Tiers 1–4 pass cleanly with zero failures.

4. **Invalidation Conditions**:
   The plan is invalidated if:
   - `aws-api-mcp-server` is allowed into the verified catalog.
   - Command injection payloads (e.g. `cmd.exe /c calc.exe`) pass audit.
   - Plaintext API keys (`sk-...`) in `env` pass without triggering `ERR_HARDCODED_SECRET`.
   - Backup path prefix traversal (`../../escaped`) succeeds without raising `ValueError`.
