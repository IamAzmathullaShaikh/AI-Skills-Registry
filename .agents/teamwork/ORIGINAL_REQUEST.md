# Original User Request

## 2026-09-23T20:03:26Z

Use a very large team of agents.

Build an automated discovery, validation, and multi-platform distribution pipeline that systematically crawls GitHub for high-quality, verified AI model skills and Model Context Protocol (MCP) servers, safely integrating them into local AI environments (Antigravity, Freebuff / Claude Code, Codex/Cursor) with task-based routing.

Working directory: C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry
Integrity mode: development

## Requirements

### R1. GitHub Repository Discovery & Metadata Indexing
Crawl and index AI skills and MCP servers from official registries (e.g., modelcontextprotocol/servers, Anthropic, Model Context Protocol official catalogs) and top community repositories with >100 stars. Collect standardized metadata including name, description, capabilities, schemas, dependencies, and license.

### R2. Automated Quality, Security & Schema Validation
Implement a validation filter that rejects unmaintained, deprecated, or vulnerable packages. Verify that every candidate skill conforms to standard SKILL.md specifications (YAML frontmatter + progressive disclosure) and every candidate MCP server conforms to Model Context Protocol JSON-RPC specification with valid entry points.

### R3. Multi-Platform Deployment & Distribution
Generate native configuration bundles and install validated tools into local environments:
- Google Antigravity: Deploy skills to C:\Users\BangerSoul\.gemini\config\skills\<name>\SKILL.md and MCP server definitions to mcp_config.json.
- Freebuff Desktop & Claude Code: Register validated MCP servers into C:\Users\BangerSoul\.claude.json under mcpServers and document agent triggers in C:\Users\BangerSoul\AGENTS.md.
- Global & Project Context: Update workspace rule files with clear routing instructions so models know exactly when and how to activate newly available tools.

### R4. Intelligent Skill Routing & Efficiency Directives
Generate concise classification rules that map common task types (e.g., database inspection, web research, visual generation, binary analysis, cloud deployment) to specific installed skills, preventing context window saturation while maximizing agent problem-solving capabilities.

## Acceptance Criteria

### Discovery & Catalog
- [ ] A structured catalog (catalog.json / README.md) in C:\Users\BangerSoul\Desktop\Projects\AI-Skills-Registry documenting all discovered, verified, and skipped packages.
- [ ] At least 15 distinct, high-utility skills and MCP tools across key categories (Browser/Search, Code Intelligence, Data/Databases, System/Ops, Media) indexed and validated.

### Schema & Verification
- [ ] Automated validation script completes dry-run schema checks on all candidate skills and MCP tools with zero unhandled syntax or format exceptions.
- [ ] All generated SKILL.md files pass Antigravity frontmatter validation (name, description, clear progressive disclosure triggers).

### Platform Integration
- [ ] Validated skills are correctly mounted in C:\Users\BangerSoul\.gemini\config\skills.
- [ ] Verified MCP tools are configured in C:\Users\BangerSoul\.claude.json without corrupting existing configuration or API keys.
- [ ] Local model rule files (AGENTS.md, CLAUDE.md, GEMINI.md) contain updated, non-overlapping task routing guidelines for each added capability.
