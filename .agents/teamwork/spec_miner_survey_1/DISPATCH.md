# DISPATCH — spec_miner_survey_1

## Objective
Investigate exact specifications, schemas, existing implementations, and formats for:
1. Antigravity SKILL.md specification:
   - Check existing skills on local machine (e.g. `C:\Users\BangerSoul\.gemini\config\skills\opencut\SKILL.md` and any other directories in `C:\Users\BangerSoul\.gemini\config\skills\`).
   - Identify exact YAML frontmatter fields (`name`, `description`, etc.), body structure, progressive disclosure pattern, scripts/resources layout.
2. Model Context Protocol (MCP) JSON-RPC specification & configuration schemas:
   - Standard MCP server JSON-RPC schemas (tools/list, tools/call, resources, prompts).
   - Server entry point definitions (executable command, args, env, transport: stdio, sse).
3. Target environment configuration file schemas:
   - Google Antigravity MCP config: inspect `C:\Users\BangerSoul\.gemini\` to see where/how MCP servers are configured (e.g. `mcp_config.json` or `antigravity_mcp.json`).
   - Claude Code / Freebuff Desktop: inspect `C:\Users\BangerSoul\.claude.json` to see existing format, `mcpServers` structure, environment variables, and ensure safe non-destructive merging rules.
   - Model rule files: inspect `C:\Users\BangerSoul\AGENTS.md` and any `CLAUDE.md`, `GEMINI.md` to see existing triggers and rules.

## Input Files to Read
- Authoritative user request: `C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md`

## Output Requirements
Write a comprehensive report to:
`C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1\survey_specs.md`
and write your completion `handoff.md` in your working directory.

## 2026-09-23T20:05:12Z

You are spec_miner_survey_1, a teamwork_preview_spec_miner subagent.
Your working directory is: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1
Your parent is orchestrator_1 (conversation ID: 40a6594f-8daa-4f4a-b75e-76633ee5c4c9).

First, read the authoritative user request at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\ORIGINAL_REQUEST.md
and your dispatch instructions at:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1\DISPATCH.md

Your task is to thoroughly inspect and document specifications, schemas, existing implementations, and formats:
1. Antigravity SKILL.md specification:
   - Inspect existing skills on the local system (check C:\Users\BangerSoul\.gemini\config\skills\ and specifically C:\Users\BangerSoul\.gemini\config\skills\opencut\SKILL.md).
   - Document exact YAML frontmatter fields (name, description, etc.), body structure, progressive disclosure pattern, scripts/resources layout.
2. Model Context Protocol (MCP) JSON-RPC specification & configuration schemas:
   - Standard MCP server JSON-RPC schemas (tools/list, tools/call, resources, prompts).
   - Server entry point definitions (executable command, args, env, transport: stdio, sse).
3. Target environment configuration file schemas:
   - Google Antigravity MCP config: inspect C:\Users\BangerSoul\.gemini\ to see where/how MCP servers are configured (e.g. mcp_config.json or antigravity_mcp.json).
   - Claude Code / Freebuff Desktop: inspect C:\Users\BangerSoul\.claude.json to see existing format, mcpServers structure, environment variables, and ensure safe non-destructive merging rules.
   - Model rule files: inspect C:\Users\BangerSoul\AGENTS.md, CLAUDE.md, GEMINI.md to see existing triggers and rules.

Write your comprehensive findings to:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1\survey_specs.md

Write your handoff report to:
C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry\.agents\teamwork\spec_miner_survey_1\handoff.md
Follow the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification).
When complete, notify orchestrator_1 via send_message.
