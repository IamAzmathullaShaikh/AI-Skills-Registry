# DISPATCH — explorer_registry_survey_1

## Objective
Survey GitHub repositories, official registries, APIs, and catalogs for AI skills & MCP servers:
1. Official registries & top sources:
   - `modelcontextprotocol/servers` official repository.
   - Anthropic MCP repositories & community catalogs.
   - Awesome-mcp-servers and verified skill repositories.
2. Candidate Selection across the 5 required categories (target >100 stars where applicable, high utility, clean maintenance status):
   - Category 1: Browser / Search (e.g. fetch, puppeteer, brave-search, playwright)
   - Category 2: Code Intelligence (e.g. git, github, filesystem, tree-sitter, language tools)
   - Category 3: Data / Databases (e.g. sqlite, postgres, duckdb, redis)
   - Category 4: System / Ops (e.g. docker, kubernetes, aws, shell)
   - Category 5: Media (e.g. opencut, image generation, audio/ffmpeg)
3. Standardized Metadata Schema definition:
   - Identify attributes required for `catalog.json`: id, name, category, description, repo_url, stars, capabilities/tools, entrypoint (command, args, env), schemas, dependencies (npm/pip/binary), license, validation_status.
   - Select at least 15 concrete, verified candidate packages meeting all criteria.

## Input Files to Read
- Authoritative user request: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`

## Output Requirements
Write a comprehensive report to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\explorer_registry_survey_1\survey_registries.md`
and write your completion `handoff.md` in your working directory.
Report back to orchestrator_1 when finished.
