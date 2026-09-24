"""SKILL.md and MCP JSON-RPC Schema Validation Module.

Provides native, robust schema validation for:
1. Antigravity SKILL.md frontmatters (YAML delimiters, naming conventions, descriptions)
2. MCP Server transport configurations (stdio, sse/http) and JSON-RPC 2.0 messages
3. Master catalog.json Draft-07 compliance
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ValidationIssue:
    rule_id: str
    message: str
    severity: str = "ERROR"
    path: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)
    body: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {"valid": self.valid, "error": self.error}
        if self.metadata:
            res["metadata"] = self.metadata
        if self.body is not None:
            res["body"] = self.body
        if self.issues:
            res["issues"] = [
                {
                    "rule_id": iss.rule_id,
                    "message": iss.message,
                    "severity": iss.severity,
                    "path": iss.path,
                    "line": iss.line,
                }
                for iss in self.issues
            ]
        return res


class SkillSchemaValidator:
    """Validates Antigravity SKILL.md files and metadata frontmatter."""

    NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)

    @classmethod
    def validate_frontmatter(cls, content: str) -> Dict[str, Any]:
        """Validate SKILL.md frontmatter and extract metadata.

        Returns contract-compliant dict {"valid": bool, "error": Optional[str], "metadata": dict}.
        """
        if not content or not content.strip():
            return {"valid": False, "error": "Empty SKILL.md content", "metadata": {}}

        match = cls.FRONTMATTER_PATTERN.match(content.strip())
        if not match:
            return {
                "valid": False,
                "error": "Missing or unclosed YAML frontmatter delimiter (---)",
                "metadata": {},
            }

        frontmatter_raw, body = match.groups()

        try:
            metadata = yaml.safe_load(frontmatter_raw)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to parse YAML frontmatter: {e}",
                "metadata": {},
            }

        if not isinstance(metadata, dict):
            return {
                "valid": False,
                "error": "Frontmatter must be a YAML dictionary mapping",
                "metadata": {},
            }

        # Check name
        name = metadata.get("name")
        if not name or not isinstance(name, str):
            return {"valid": False, "error": "Missing required field 'name'", "metadata": {}}

        if not cls.NAME_REGEX.match(name):
            return {
                "valid": False,
                "error": f"Skill name '{name}' violates lowercase-hyphen pattern (^[a-z0-9]+(-[a-z0-9]+)*$)",
                "metadata": metadata,
            }

        # Check description
        desc = metadata.get("description")
        if not desc or not isinstance(desc, str):
            return {
                "valid": False,
                "error": "Missing required field 'description'",
                "metadata": metadata,
            }

        desc_len = len(desc.strip())
        if desc_len < 20:
            return {
                "valid": False,
                "error": f"Description too short ({desc_len} chars, minimum 20 chars required)",
                "metadata": metadata,
            }

        if desc_len > 1024:
            return {
                "valid": False,
                "error": f"Description too long ({desc_len} chars, maximum 1024 chars allowed)",
                "metadata": metadata,
            }

        return {"valid": True, "error": None, "metadata": metadata, "body": body}


class McpSchemaValidator:
    """Validates Model Context Protocol transport and JSON-RPC specifications."""

    @classmethod
    def validate_transport_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an MCP server transport definition."""
        if not isinstance(config, dict):
            return {"valid": False, "error": "Configuration must be a dictionary"}

        has_command = "command" in config
        has_url = "serverUrl" in config or "url" in config

        if not has_command and not has_url:
            return {
                "valid": False,
                "error": "Server must define either 'command' (stdio) or 'serverUrl'/'url' (sse/http)",
            }

        if has_command:
            cmd = config["command"]
            if not isinstance(cmd, str) or not cmd.strip():
                return {"valid": False, "error": "Field 'command' must be a non-empty string"}
            if "args" in config and not isinstance(config["args"], list):
                return {"valid": False, "error": "Field 'args' must be a list of strings"}
            if "env" in config and not isinstance(config["env"], dict):
                return {"valid": False, "error": "Field 'env' must be a dictionary"}

        if has_url:
            url = config.get("serverUrl") or config.get("url")
            if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
                return {"valid": False, "error": f"Invalid URL scheme in endpoint: {url}"}

        return {"valid": True, "error": None}

    @classmethod
    def validate_jsonrpc_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON-RPC 2.0 response envelope."""
        if not isinstance(response, dict):
            return {"valid": False, "error": "Response must be a JSON object"}
        if response.get("jsonrpc") != "2.0":
            return {"valid": False, "error": "Missing or invalid 'jsonrpc' version (must be '2.0')"}
        if "id" not in response:
            return {"valid": False, "error": "Missing response 'id'"}
        if "result" not in response and "error" not in response:
            return {"valid": False, "error": "Response must contain either 'result' or 'error'"}
        return {"valid": True, "error": None}


class CatalogSchemaValidator:
    """Validates catalog.json structure and package integrity."""

    REQUIRED_PACKAGE_FIELDS = {
        "id", "name", "category", "type", "description",
        "repo_url", "stars", "entrypoint", "license", "platform_targets",
    }

    @classmethod
    def validate_catalog(cls, catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Validate master catalog dictionary against requirements."""
        if not isinstance(catalog, dict):
            return {"valid": False, "error": "Catalog root must be a JSON object"}

        packages = catalog.get("packages")
        if not isinstance(packages, list):
            return {"valid": False, "error": "Catalog missing 'packages' list"}

        if len(packages) < 15:
            return {"valid": False, "error": f"Catalog contains only {len(packages)} packages (minimum 15 required)"}

        seen_ids = set()
        for idx, pkg in enumerate(packages):
            if not isinstance(pkg, dict):
                return {"valid": False, "error": f"Package at index {idx} is not an object"}

            missing = cls.REQUIRED_PACKAGE_FIELDS - set(pkg.keys())
            if missing:
                return {"valid": False, "error": f"Package '{pkg.get('id', idx)}' missing required fields: {missing}"}

            pkg_id = pkg["id"]
            if pkg_id in seen_ids:
                return {"valid": False, "error": f"Duplicate package ID detected: '{pkg_id}'"}
            seen_ids.add(pkg_id)

        return {"valid": True, "error": None}
