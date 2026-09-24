"""Security, Deprecation & Vulnerability Filter Module.

Defensive perimeter that screens candidate packages, MCP servers, and skills
before they can be processed, dry-run tested, or deployed to local environments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ValidationSeverity(str, Enum):
    PASS = "PASS"
    INFO = "INFO"
    WARNING = "WARNING"
    REJECT = "REJECT"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityViolation:
    code: str
    severity: ValidationSeverity
    message: str
    target_field: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "target_field": self.target_field,
            "remediation": self.remediation,
        }


@dataclass
class SecurityAuditResult:
    package_id: str
    is_safe: bool
    violations: List[SecurityViolation] = field(default_factory=list)
    reason: str = "All security checks passed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "is_safe": self.is_safe,
            "pass": self.is_safe,
            "reason": self.reason,
            "violations": [v.to_dict() for v in self.violations],
        }


class SecurityFilter:
    """Production Security, Deprecation and Vulnerability Filter."""

    DEPRECATED_PACKAGE_IDS: Set[str] = {
        "aws-api-mcp-server",
        "deprecated-mcp-tools",
        "legacy-sqlite-bridge",
    }

    OFFICIAL_ORGS: Set[str] = {
        "modelcontextprotocol",
        "anthropics",
        "microsoft",
        "google",
        "github",
    }

    SUSPICIOUS_SHELL_PATTERNS: List[re.Pattern] = [
        re.compile(r"cmd\.exe\s+/c", re.IGNORECASE),
        re.compile(r"powershell(\.exe)?\s+(-c|-command)", re.IGNORECASE),
        re.compile(r"sh\s+-c", re.IGNORECASE),
        re.compile(r"bash\s+-c", re.IGNORECASE),
        re.compile(r"[;&|`$]"),
    ]

    SECRET_PATTERNS: List[re.Pattern] = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}"),
    ]

    WINDOWS_RESERVED_NAMES: Set[str] = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }

    @classmethod
    def is_official_repo(cls, repo_url: str) -> bool:
        if not repo_url:
            return False
        clean = repo_url.lower()
        return any(f"github.com/{org}/" in clean for org in cls.OFFICIAL_ORGS)

    @classmethod
    def audit_package(
        cls, pkg: Dict[str, Any], known_cves: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Audit candidate package against deprecation, CVEs, and injection hazards.

        Returns contract-compliant dict {"pass": bool, "reason": str}.
        """
        pkg_id = str(pkg.get("id", ""))
        repo_url = str(pkg.get("repo_url", ""))
        stars = pkg.get("stars", 0)

        # 1. Deprecation check
        if pkg_id in cls.DEPRECATED_PACKAGE_IDS or pkg.get("deprecated", False):
            return {"pass": False, "reason": f"Package '{pkg_id}' is explicitly deprecated"}

        # 2. Windows reserved name check
        if pkg_id.upper() in cls.WINDOWS_RESERVED_NAMES:
            return {"pass": False, "reason": f"Windows reserved device name: {pkg_id}"}

        # 3. Community stars threshold (< 100 stars unless official or skill)
        if (
            not cls.is_official_repo(repo_url)
            and pkg.get("type") != "skill"
            and stars < 100
        ):
            return {"pass": False, "reason": f"Community package '{pkg_id}' has {stars} stars (< 100 threshold)"}

        # 4. Commit freshness / age check
        commit_age_days = pkg.get("last_commit_age_days")
        if commit_age_days is not None and commit_age_days > 365:
            return {"pass": False, "reason": f"Package abandoned: last commit {commit_age_days} days ago (> 365 days)"}

        # 5. CVE Vulnerability check
        if known_cves:
            for cve in known_cves:
                score = float(cve.get("cvss", 0.0))
                if score >= 7.0:
                    return {"pass": False, "reason": f"CRITICAL CVE {cve.get('id')} with CVSS {score}"}

        # 6. Command injection check
        entrypoint = pkg.get("entrypoint", {})
        command = str(entrypoint.get("command", ""))
        args = [str(a) for a in entrypoint.get("args", [])]
        full_invocation = f"{command} " + " ".join(args)

        for pat in cls.SUSPICIOUS_SHELL_PATTERNS:
            if pat.search(full_invocation):
                return {"pass": False, "reason": f"Command injection pattern detected: {full_invocation}"}

        # 7. Path traversal check
        for token in [pkg_id, command] + args:
            if ".." in token or token.startswith("/etc") or token.startswith("C:\\Windows") or "\\" in token and ".." in token:
                return {"pass": False, "reason": f"Path traversal detected in token: {token}"}

        # 8. Secret leak check
        env = entrypoint.get("env", {})
        for k, v in env.items():
            for sec_pat in cls.SECRET_PATTERNS:
                if sec_pat.search(str(v)):
                    return {"pass": False, "reason": f"Hardcoded secret detected in env variable '{k}'"}

        return {"pass": True, "reason": "All security and deprecation checks passed"}
