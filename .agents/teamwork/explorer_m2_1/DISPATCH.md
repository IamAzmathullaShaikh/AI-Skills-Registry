# DISPATCH — explorer_m2_1

## Milestone 2: Quality, Security & Schema Validation Engine
Focus: Security, Deprecation & Vulnerability Filter Design (`src/validator/security_filter.py`)

## Objective
Design the concrete implementation plan for `src/validator/security_filter.py`:
1. Deprecation detection:
   - Known deprecated packages database (e.g. `aws-api-mcp-server` deprecated July 15, 2026, succeeded by Agent Toolkit for AWS).
   - Unmaintained/abandoned package heuristics (no commits in >12 months, un-scoped copycat packages on PyPI/npm).
2. Security & Isolation verification:
   - Filesystem boundary enforcement: verify tools like `@modelcontextprotocol/server-filesystem` specify explicit boundary paths rather than unbounded root.
   - Credential isolation: verify API keys and tokens are supplied via environment variables, never hardcoded in args or plain text.
   - Single-region AWS policy compliance (per user rule requirements).
3. Hardening fixes for issues flagged in M1 adversarial testing:
   - Path traversal prevention in backup paths (ADV-01).
   - High-entropy UUIDs to prevent PID collisions (Vuln 1 & 2).
   - Malformed URL/IPv6 exception containment (Vuln 4).

## Files to Read
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\challenger_m1_1\adversarial_report.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\challenger_m1_2\adversarial_report.md`

## Output Requirements
Write your implementation plan to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\plan_security_filter.md`
and write your completion `handoff.md` in your working directory.
Report back to orchestrator_1 when finished.

## 2026-09-23T20:29:12Z
You are explorer_m2_1, a teamwork_preview_explorer subagent.
Your working directory is: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1
Your parent is orchestrator_1 (conversation ID: 40a6594f-8daa-4f4a-b75e-76633ee5c4c9).

First, read the authoritative user request at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md
and the project master plan at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md
and your dispatch instructions at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\DISPATCH.md
and the master catalog at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\catalog.json

Your focus is Security, Deprecation & Vulnerability Filter Design for Milestone 2:
1. Design src/validator/security_filter.py to reject deprecated (e.g. aws-api-mcp-server), unmaintained, or insecure packages.
2. Design path traversal containment, credential isolation, and single-region AWS compliance.
3. Incorporate mitigations for vulnerabilities identified in M1 adversarial testing (path traversal, PID collisions, IPv6 URL errors).

Write your implementation plan to:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m2_1\plan_security_filter.md
and write your completion handoff.md in your working directory.
Follow the Handoff Protocol. When complete, notify orchestrator_1 via send_message.
