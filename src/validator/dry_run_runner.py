"""Zero-Unhandled-Exception Dry-Run Validation Runner Module.

Executes end-to-end dry-run verification over all candidate skills and MCP tools
before any deployment or system modifications occur.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.validator.security_filter import SecurityFilter
from src.validator.schema_validator import (
    CatalogSchemaValidator,
    McpSchemaValidator,
    SkillSchemaValidator,
)


class DryRunRunner:
    """Production Dry-Run Runner providing guaranteed zero unhandled exceptions."""

    @classmethod
    def run_dry_run(cls, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute dry-run validation with complete exception encapsulation.

        Returns structured report containing total, passed, rejected, and per-package results.
        """
        report: Dict[str, Any] = {
            "total": len(packages) if packages else 0,
            "passed": 0,
            "rejected": 0,
            "results": [],
        }

        if not packages:
            return report

        for pkg in packages:
            pkg_id = "UNKNOWN"
            try:
                if not isinstance(pkg, dict):
                    raise ValueError(f"Package entry must be a dictionary, got {type(pkg).__name__}")

                pkg_id = str(pkg.get("id") or "UNKNOWN")
                if pkg_id == "UNKNOWN":
                    raise ValueError("Package ID missing")

                name = pkg.get("name")
                if not name:
                    raise ValueError(f"Package '{pkg_id}' missing name")

                desc = str(pkg.get("description", ""))
                if len(desc) < 20:
                    raise ValueError(f"Package '{pkg_id}' description too short (< 20 chars)")

                # Stage 1 & 2: Security & Deprecation audit
                sec_res = SecurityFilter.audit_package(pkg)
                if not sec_res.get("pass", True):
                    raise ValueError(f"Security check failed: {sec_res.get('reason')}")

                # Stage 3: Type-specific schema verification
                pkg_type = pkg.get("type", "mcp_server")
                if pkg_type == "skill":
                    sample_md = f"""---
name: {pkg_id}
description: {desc}
---
# {name}
"""
                    skill_val = SkillSchemaValidator.validate_frontmatter(sample_md)
                    if not skill_val.get("valid", True):
                        raise ValueError(f"Skill frontmatter invalid: {skill_val.get('error')}")
                else:
                    entrypoint = pkg.get("entrypoint", {})
                    transport_val = McpSchemaValidator.validate_transport_config(entrypoint)
                    if not transport_val.get("valid", True):
                        raise ValueError(f"MCP transport config invalid: {transport_val.get('error')}")

                report["passed"] += 1
                report["results"].append({
                    "id": pkg_id,
                    "status": "PASS",
                    "issues": [],
                })

            except Exception as exc:
                report["rejected"] += 1
                report["results"].append({
                    "id": pkg_id,
                    "status": "FAIL",
                    "issues": [{"rule_id": "SCHEMA_VALIDATION_ERROR", "message": str(exc)}],
                })

        return report

    @classmethod
    def run_on_catalog(cls, catalog_path: Path) -> Dict[str, Any]:
        """Load catalog.json and execute dry-run on all packages."""
        if not catalog_path.exists():
            return {
                "total": 0,
                "passed": 0,
                "rejected": 1,
                "results": [{"id": "CATALOG_FILE", "status": "FAIL", "issues": [{"rule_id": "FILE_NOT_FOUND", "message": str(catalog_path)}]}],
            }

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            packages = data.get("packages", [])
            return cls.run_dry_run(packages)
        except Exception as exc:
            return {
                "total": 0,
                "passed": 0,
                "rejected": 1,
                "results": [{"id": "CATALOG_JSON", "status": "FAIL", "issues": [{"rule_id": "JSON_DECODE_ERROR", "message": str(exc)}]}],
            }
