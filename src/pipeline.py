"""Master AI Skills & MCP Pipeline Coordinator Module.

Orchestrates the entire lifecycle:
1. Crawling & Metadata Extraction (CrawlerEngine)
2. Quality, Security & Schema Validation (DryRunRunner)
3. Multi-Platform Deployment (AntigravityDeployer & ClaudeDeployer)
4. Intelligent Task Routing Matrix Generation & Injection (RuleInjector)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import PipelineEnvironmentConfig
from src.crawler import CrawlerEngine, get_seed_catalog
from src.deployer import AntigravityDeployer, ClaudeDeployer
from src.router import RoutingMatrixGenerator, RuleInjector
from src.validator import DryRunRunner


class PipelineRunner:
    """End-to-End Orchestrator for AI Skills and MCP tools."""

    def __init__(self, config: PipelineEnvironmentConfig):
        self.config = config

    def run(self) -> Dict[str, Any]:
        """Execute full pipeline and return execution summary."""
        print("=== AI Skills & MCP Pipeline Initiated ===")
        print(f"Target Environment: {'MOCK SANDBOX' if self.config.is_sandbox else 'HOST PRODUCTION'}")
        print(f"Dry Run Mode: {self.config.dry_run}")

        # Stage 1: Crawl & Load Catalog
        print("\n[Stage 1] Loading & Indexing Catalog...")
        if self.config.catalog_file.exists():
            with open(self.config.catalog_file, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        else:
            crawler = CrawlerEngine(offline_mode=True)
            catalog = crawler.crawl_all()

        packages = catalog.get("packages", [])
        print(f"Found {len(packages)} candidate packages across {len(catalog.get('categories', []))} categories.")

        # Stage 2: Quality & Schema Validation (Dry Run)
        print("\n[Stage 2] Executing 4-Stage Quality, Security & Schema Audit...")
        validation_report = DryRunRunner.run_dry_run(packages)
        passed_count = validation_report["passed"]
        rejected_count = validation_report["rejected"]
        print(f"Audit Complete: {passed_count} PASSED, {rejected_count} REJECTED.")

        if self.config.dry_run:
            print("\nDry run mode enabled - stopping before deployment.")
            return {
                "status": "DRY_RUN_COMPLETE",
                "total": len(packages),
                "passed": passed_count,
                "rejected": rejected_count,
            }

        # Filter only verified packages
        passed_ids = {
            r["id"] for r in validation_report["results"] if r.get("status") == "PASS"
        }
        verified_packages = [p for p in packages if p.get("id") in passed_ids]

        # Stage 3: Multi-Platform Deployment
        print(f"\n[Stage 3] Deploying {len(verified_packages)} Verified Packages to Local Environments...")

        deployed_skills: List[str] = []
        deployed_mcp_servers: Dict[str, Any] = {}

        for pkg in verified_packages:
            pkg_id = pkg["id"]
            pkg_type = pkg.get("type", "mcp_server")
            targets = pkg.get("platform_targets", ["antigravity", "claude_code"])

            if pkg_type == "skill":
                # Mount to Antigravity
                if "antigravity" in targets:
                    skill_dir = AntigravityDeployer.mount_skill(
                        self.config.gemini_skills_dir, pkg_id, pkg
                    )
                    deployed_skills.append(pkg_id)
                    print(f"  + Mounted Antigravity Skill: {pkg_id} -> {skill_dir}")
            else:
                entrypoint = pkg.get("entrypoint", {})
                # Format for MCP servers
                srv_cfg: Dict[str, Any] = {}
                if "command" in entrypoint:
                    srv_cfg["command"] = entrypoint["command"]
                    if "args" in entrypoint:
                        srv_cfg["args"] = entrypoint["args"]
                    if "env" in entrypoint and entrypoint["env"]:
                        srv_cfg["env"] = entrypoint["env"]
                elif "serverUrl" in entrypoint or "url" in entrypoint:
                    srv_cfg["type"] = "http"
                    srv_cfg["url"] = entrypoint.get("serverUrl") or entrypoint.get("url")

                # Antigravity MCP registration
                if "antigravity" in targets and srv_cfg:
                    AntigravityDeployer.register_mcp_server(
                        self.config.gemini_mcp_config,
                        pkg_id,
                        srv_cfg,
                        self.config.backup_dir,
                    )

                # Claude Code deep merge
                if "claude_code" in targets and srv_cfg:
                    deployed_mcp_servers[pkg_id] = srv_cfg

        # Execute Claude deep merge
        if deployed_mcp_servers:
            merge_res = ClaudeDeployer.deep_merge_mcp_servers(
                self.config.claude_json_path,
                deployed_mcp_servers,
                self.config.backup_dir,
            )
            print(f"  + Claude Code MCP Merge: {merge_res['merged']} merged, {merge_res['preserved']} preserved.")

        # Stage 4: Intelligent Task-Based Routing Directives
        print("\n[Stage 4] Generating & Injecting Task-Based Routing Directives...")
        directive = RoutingMatrixGenerator.generate_directive(verified_packages)

        rule_targets = [
            ("AGENTS.md", self.config.agents_rule_file),
            ("CLAUDE.md", self.config.claude_rule_file),
            ("GEMINI.md", self.config.gemini_rule_file),
        ]

        injected_files: List[str] = []
        for name, path in rule_targets:
            res = RuleInjector.inject_into_file(path, directive, self.config.backup_dir)
            injected_files.append(name)
            print(f"  + Injected managed routing directives into {name} ({res['bytes']} bytes)")

        print("\n=== All Stages Completed Successfully ===")
        return {
            "status": "SUCCESS",
            "total_packages": len(packages),
            "verified_packages": len(verified_packages),
            "deployed_skills": deployed_skills,
            "deployed_mcp_servers": list(deployed_mcp_servers.keys()),
            "injected_rule_files": injected_files,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Skills & MCP Registry Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Perform schema and security checks without deployment")
    parser.add_argument("--sandbox", type=str, default=None, help="Run inside an isolated temporary sandbox directory")
    args = parser.parse_args()

    if args.sandbox:
        config = PipelineEnvironmentConfig.from_sandbox(args.sandbox, populate_fixtures=True)
    else:
        config = PipelineEnvironmentConfig.live_default(dry_run=args.dry_run)

    runner = PipelineRunner(config)
    result = runner.run()
    return 0 if result.get("status") in ("SUCCESS", "DRY_RUN_COMPLETE") else 1


if __name__ == "__main__":
    sys.exit(main())
