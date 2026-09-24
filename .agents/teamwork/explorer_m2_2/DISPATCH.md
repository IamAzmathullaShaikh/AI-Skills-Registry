# DISPATCH — explorer_m2_2

## Milestone 2: Quality, Security & Schema Validation Engine
Focus: SKILL.md & MCP JSON-RPC Schema Validators (`src/validator/schema_validator.py`)

## Objective
Design the concrete implementation plan for `src/validator/schema_validator.py`:
1. Antigravity SKILL.md Schema Validator:
   - YAML frontmatter parser and validator:
     - `name`: mandatory, lowercase alphanumeric with hyphens, matching regex `^[a-z0-9-]+$`.
     - `description`: mandatory, non-empty, actionable third-person trigger phrasing.
   - Progressive disclosure checks:
     - Document size cap: ensure root `SKILL.md` is under 500 lines or 24 KB.
     - Structured subdirectories: verify `references/`, `scripts/`, `examples/` if present.
     - Markdown link checker: verify relative markdown links resolve to existing files.
2. MCP JSON-RPC Spec Validator:
   - Validate transport: `stdio` (requires valid command string and args array) or `sse`/`http` (requires valid URL).
   - Validate capabilities & tools: verify tools have non-empty name, description, and valid `inputSchema` (Draft-07 object schema with `properties` and `required`).
   - Validate error semantics: support in-band `isError: true` tool call results.
3. Master Draft-07 Catalog Validator:
   - Full JSON Schema validation against the Draft-07 specification.

## Files to Read
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1\survey_specs.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json`

## Output Requirements
Write your implementation plan to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_2\plan_schema_validator.md`
and write your completion `handoff.md` in your working directory.
Report back to orchestrator_1 when finished.

## 2026-09-23T20:29:12Z
You are explorer_m2_2, a teamwork_preview_explorer subagent.
Your working directory is: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_2
Your parent is orchestrator_1 (conversation ID: 40a6594f-8daa-4f4a-b75e-76633ee5c4c9).

Your focus is SKILL.md & MCP JSON-RPC Schema Validators for Milestone 2:
1. Design src/validator/schema_validator.py for Antigravity SKILL.md (YAML frontmatter name/description, progressive disclosure, markdown links).
2. Design MCP JSON-RPC 2.0 schema validation (stdio/sse entrypoints, tools, inputSchema, error handling).
3. Design master Draft-07 catalog validation.
