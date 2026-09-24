# DISPATCH — explorer_m1_1

## Milestone 1: Discovery & Catalog Indexing Engine
Focus: Core Config & Registry Seed Architecture (`src/config.py`, `src/crawler/registry_sources.py`)

## Objective
Design the concrete implementation plan for:
1. `src/config.py`:
   - `PipelineEnvironmentConfig` class supporting both live host paths (`C:\Users\BangerSoul\.gemini\...`, `C:\Users\BangerSoul\.claude.json`, `C:\Users\BangerSoul\AGENTS.md`) and isolated mock sandboxes for safe automated testing.
   - Environment variables (e.g. `GITHUB_TOKEN`, `AI_SKILLS_SANDBOX_DIR`).
2. `src/crawler/registry_sources.py`:
   - Curated registry definitions and verified package metadata for all 20 candidates across the 5 categories:
     - Browser/Search: `browser-playwright`, `browser-puppeteer`, `browser-fetch`, `browser-brave-search`
     - Code Intelligence: `code-filesystem`, `code-git`, `code-github`, `code-memory`, `code-sequential-thinking`
     - Data/Databases: `data-sqlite`, `data-postgres`, `data-duckdb`, `data-redis`
     - System/Ops: `ops-kubernetes`, `ops-docker`, `ops-aws`, `ops-time`
     - Media: `media-opencut`, `media-ffmpeg`, `media-image-gen`
   - Complete package specifications: ID, category, name, description, repo_url, stars, capabilities, entrypoint (command, args, env), dependencies, license, platform_targets.

## Files to Read
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\PROJECT.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_registry_survey_1\survey_registries.md`
- `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_pipeline_survey_1\survey_pipeline.md`

## Output Requirements
Write your detailed implementation design to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_m1_1\plan_config_sources.md`
and write your completion `handoff.md` in your working directory.
Report back to orchestrator_1 when finished.

## 2026-09-23T20:13:00Z
Received dispatch request:
Focus: Core Config & Registry Seed Architecture for Milestone 1.
1. Design src/config.py with PipelineEnvironmentConfig supporting live paths vs isolated mock sandbox directories.
2. Design src/crawler/registry_sources.py containing verified seed package metadata for all 20 packages across the 5 categories (Browser/Search, Code Intelligence, Data/Databases, System/Ops, Media) adhering to Draft-07 schema.
Output to plan_config_sources.md, completion handoff.md, notify orchestrator_1.
