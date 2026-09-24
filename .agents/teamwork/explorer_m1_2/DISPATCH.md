# DISPATCH — explorer_m1_2

## Milestone 1: Discovery & Catalog Indexing Engine
Focus: GitHub & Registry Crawler Engine (`src/crawler/github_crawler.py`)

## Objective
Design the concrete implementation plan for:
1. `src/crawler/github_crawler.py`:
   - Asynchronous or synchronous HTTP client fetching repository metadata, star counts, licenses, and releases from GitHub API / npm / PyPI.
   - Robust offline fixture fallback mode: When offline, rate-limited, or when running tests, smoothly fall back to cached/seed registry data without raising unhandled network exceptions.
   - Metadata normalization into standardized Draft-07 catalog package records.
   - Error handling, timeouts, retry logic with exponential backoff.
   - CLI invocation support: `python -m src.crawler.github_crawler [--output path] [--offline]`.

## Files to Read
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_registry_survey_1\survey_registries.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_pipeline_survey_1\survey_pipeline.md`

## Output Requirements
Write your detailed implementation design to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m1_2\plan_crawler_engine.md`
and write your completion `handoff.md` in your working directory.

## 2026-09-23T20:12:00Z
You are explorer_m1_2, a teamwork_preview_explorer subagent.
Your working directory is: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m1_2
Your parent is orchestrator_1 (conversation ID: 40a6594f-8daa-4f4a-b75e-76633ee5c4c9).

First, read the authoritative user request at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md
and the project master plan at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md
and your dispatch instructions at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m1_2\DISPATCH.md

Your focus is the GitHub & Registry Crawler Engine for Milestone 1:
1. Design src/crawler/github_crawler.py to fetch and normalize metadata from official registries, npm, and PyPI.
2. Design an offline fixture fallback mode so the crawler can run reliably in offline test environments without raising unhandled network exceptions.
3. Design CLI invocation and programmatic API for crawler execution.

Write your implementation design to:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m1_2\plan_crawler_engine.md
and write your completion handoff.md in your working directory.
Follow the Handoff Protocol. When complete, notify orchestrator_1 via send_message.
