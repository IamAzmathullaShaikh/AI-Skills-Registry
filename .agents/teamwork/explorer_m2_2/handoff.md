# Milestone 2 Explorer Handoff: SKILL.md & MCP JSON-RPC Schema Validators

**From**: `explorer_m2_2`  
**To**: `orchestrator_1` (conversation ID: `40a6594f-8daa-4f4a-b75e-76633ee5c4c9`)  
**Date**: 2026-09-23  
**Artifact Created**: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_2\plan_schema_validator.md`  
**Target Module**: `src/validator/schema_validator.py`  

---

## 1. Observation

1. **Python Environment Dependency Check**:
   - Command: `python -c "import jsonschema, yaml; print('jsonschema version:', jsonschema.__version__, 'yaml version:', yaml.__version__)"`
   - Result:
     ```
     Traceback (most recent call last):
       File "<string>", line 1, in <module>
         import jsonschema, yaml; print('jsonschema version:', jsonschema.__version__, 'yaml version:', yaml.__version__)
         ^^^^^^^^^^^^^^^^^^^^^^^
     ModuleNotFoundError: No module named 'jsonschema'
     ```
   - Command: `python -c "import yaml; print('yaml version:', yaml.__version__)"`
   - Result: `yaml version: 6.0.3` (PyYAML installed and operational).
   - In `pip list`: `pydantic` 2.13.5, `PyYAML` 6.0.3, and `pytest` 9.1.1 are installed. `jsonschema` is not present in Python 3.14.7.

2. **Existing Contract Oracle & Test Assertions**:
   - `tests/tier1_feature_coverage/test_f5_skill_frontmatter_validator.py` (lines 44, 70, 83, 95):
     - Expects: `"violates lowercase-hyphen pattern"` for uppercase or invalid characters.
     - Expects: `"Missing required field 'description'"` for missing descriptions.
     - Expects: `"Description shorter than 20 chars minimum"` for short descriptions.
     - Expects: `"Unclosed frontmatter delimiter"` for unclosed frontmatter blocks.
     - Tests relative link extraction: `./references/architecture.md` and `./scripts/deploy.ps1`.
   - `tests/tier2_boundary_corner/test_bva_skill_and_mcp_schemas.py` (lines 24, 64, 76):
     - Length boundary: 19 characters rejected with `"Description shorter than 20 chars minimum"`, 20 characters accepted.
     - Length boundary: 1,024 characters accepted, 1,025 characters rejected with `"Description longer than 1,024 chars maximum"`.
     - Name regex: single-character `x` accepted; leading/trailing hyphens `-tool`, `tool-`, `-tool-` rejected.
   - `tests/tier1_feature_coverage/test_f6_mcp_jsonrpc_validator.py` (lines 28, 33, 35, 37, 42, 50, 52, 54, 144):
     - Transport validation requires either `command` (stdio) or `serverUrl`/`url` (sse/http).
     - Rejects non-http(s) schemes: `"Invalid URL scheme in endpoint: {url}"`.
     - Rejects non-list args: `"Field 'args' must be a list of strings"`.
     - Response envelope requires `jsonrpc: "2.0"`, `id` presence, and `result` or `error`.
     - Tool execution error semantics: in-band `"isError": true` inside `result`.
   - `tests/tier2_boundary_corner/test_bva_catalog_boundaries.py` (lines 38, 43, 54):
     - Minimum 20 packages: `"Catalog has {total} packages (requires >= 20)"`.
     - Duplicate IDs check: `"Catalog contains duplicate package IDs"`.
     - Category distribution: `"Category '{cat}' has {cnt} items (< 3)"` across 5 categories (`browser_search`, `code_intelligence`, `data_databases`, `system_ops`, `media`).
   - `tests/conftest.py` (lines 468, 489):
     - Regex used in oracle: `SKILL_NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")`.

3. **Live Reference Antigravity Skill Structure**:
   - `C:\Users\BangerSoul\.gemini\config\skills\opencut\SKILL.md` (73 lines, 3,806 bytes):
     - Starts with `---`, `name: opencut`, descriptive third-person trigger, closed by `---`.
     - References `./references/architecture-and-usage.md` at line 72.
     - Accompanied by physical directory `references/` containing `architecture-and-usage.md` (2,349 bytes).

---

## 2. Logic Chain

1. **Self-Contained Validation Requirement**:
   - Observation 1 confirmed `jsonschema` is not installed in the environment. Attempting to `import jsonschema` raises `ModuleNotFoundError`.
   - Therefore, `src/validator/schema_validator.py` must either require an external installation or provide an internal, zero-dependency Draft-07 validation engine.
   - Providing an internal `Draft07Engine` ensures that all automated test tiers (Tiers 1–4, CI, and isolated sandboxes) execute seamlessly with zero external runtime dependencies.

2. **Frontmatter & Progressive Disclosure Design**:
   - Observation 2 showed the exact contract error messages and boundary conditions expected for `SKILL.md`.
   - Observation 3 provided the reference file structure for Antigravity skills.
   - Therefore, `SkillSchemaValidator` must implement:
     - Exact regex `^[a-z0-9]+(-[a-z0-9]+)*$` matching single-character names (`x`), standard hyphenated names (`opencut`, `sqlite-inspector`), while rejecting uppercase, symbols, and leading/trailing hyphens (`-tool`, `tool-`).
     - Description length validation strictly between 20 and 1024 characters.
     - Document size cap: max 500 lines or 24,000 bytes (24 KB), matching host rule truncation thresholds.
     - Relative link extraction and file existence resolution against the skill root directory.

3. **MCP JSON-RPC 2.0 Design**:
   - Observation 2 detailed the transport and message contracts for MCP.
   - Therefore, `McpSchemaValidator` must provide:
     - `validate_transport_config` enforcing `command` + string list `args` + dict `env` for stdio, or `http(s)://` URL + dict `headers` for sse/http.
     - `validate_jsonrpc_request` and `validate_jsonrpc_response` verifying 2.0 envelopes and standard RPC error formats.
     - `validate_tool_definition` verifying non-empty tool `name`, `description`, and `inputSchema` Draft-07 object schema.
     - `validate_tool_call_result` verifying in-band `"isError": true` inside `result`.

4. **Master Catalog & Milestone Acceptance Boundaries**:
   - Observation 2 established catalog boundaries: >= 20 packages, >= 3 per category across all 5 canonical categories, and unique IDs.
   - Therefore, `CatalogSchemaValidator` must implement `evaluate_catalog_boundaries` and `validate_package_record` to enforce full Draft-07 catalog compliance and ensure verified packages are safely passed to Milestone 3 deployers.

---

## 3. Caveats

- **External `jsonschema` Package**: If `jsonschema` is installed in a future environment, `Draft07Engine` can optionally delegate to `jsonschema.validate()`, but our design functions 100% autonomously without it.
- **Third-Person Trigger Phrasing**: While length and non-emptiness are deterministically enforced, natural language trigger directives (e.g. "Use when...", "Activate when...") are audited via heuristics and warning flags rather than hard regexes, avoiding false-positive rejections of valid semantic phrasing.
- No other caveats.

---

## 4. Conclusion

The technical implementation plan for `src/validator/schema_validator.py` is fully designed and documented in:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_2\plan_schema_validator.md`

The module is decomposed into four cohesive classes:
1. `SkillSchemaValidator`: Antigravity SKILL.md YAML frontmatter, progressive disclosure (500L / 24 KB), and markdown relative link resolution.
2. `McpSchemaValidator`: MCP JSON-RPC 2.0 stdio/sse transports, message envelopes, tool definitions, `inputSchema` Draft-07 validation, and `isError: true` execution semantics.
3. `CatalogSchemaValidator`: Draft-07 catalog specification, milestone acceptance boundaries (20 packages, 5 categories, duplicate ID prevention), and package record validation.
4. `Draft07Engine`: Zero-dependency native JSON Schema Draft-07 validator ensuring 100% portability.

All method signatures and return dictionaries strictly adhere to existing contract oracles in `tests/conftest.py` and test suites in `tests/tier1_feature_coverage/` and `tests/tier2_boundary_corner/`.

---

## 5. Verification Method

To independently verify the contracts and specifications described in this plan:
1. **Inspect Plan Artifact**:
   - File: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_2\plan_schema_validator.md`
   - Verify class structures, method signatures, error string constants, and Draft-07 engine logic.
2. **Execute Existing Test Suites**:
   - Run: `pytest tests/tier1_feature_coverage/test_f5_skill_frontmatter_validator.py -v` (7 passed)
   - Run: `pytest tests/tier1_feature_coverage/test_f6_mcp_jsonrpc_validator.py -v` (7 passed)
   - Run: `pytest tests/tier2_boundary_corner/test_bva_skill_and_mcp_schemas.py -v` (6 passed)
   - Run: `pytest tests/tier2_boundary_corner/test_bva_catalog_boundaries.py -v` (6 passed)
3. **Invalidation Conditions**:
   - If the implementation requires external packages not present in `pip list` (`jsonschema`), causing import errors.
   - If error messages diverge from the exact string patterns expected by the Tier 1 and Tier 2 boundary tests.
