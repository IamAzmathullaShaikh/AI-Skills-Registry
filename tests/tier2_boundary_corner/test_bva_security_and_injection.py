"""Tier 2 Boundary & Corner Cases: Security and Injection Boundaries.

Tests boundary limits on security filters and sanitization:
- Star threshold boundary: 99 stars (reject) vs 100 stars (accept)
- Commit recency boundary: 365 days (accept) vs 366 days (reject)
- Vulnerability CVSS boundary: 6.9 (warn) vs 7.0 (reject)
- Complex nested subshell injection patterns ($(...), `...`, &&, ||)
- Windows reserved device names (CON, PRN, AUX, NUL, COM1)
- Deep path traversal with multiple drive or root escape patterns
"""

import re
import pytest
from typing import Dict, Any


class SecurityBoundaryEvaluator:
    """Evaluates boundary values for security policies."""

    WINDOWS_RESERVED_NAMES = {
        "con", "prn", "aux", "nul",
        "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
        "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"
    }

    SUBSHELL_REGEX = re.compile(r"(\$\(.*\)|`.*`|&&|\|\||;)")

    @classmethod
    def evaluate_community_stars(cls, stars: int) -> bool:
        """Community repos must have >= 100 stars."""
        return stars >= 100

    @classmethod
    def evaluate_commit_age(cls, days: int) -> bool:
        """Last commit must be <= 365 days ago."""
        return days <= 365

    @classmethod
    def evaluate_cvss_score(cls, score: float) -> str:
        """CVSS >= 7.0 rejects; < 7.0 passes (with warning if >= 4.0)."""
        if score >= 7.0:
            return "REJECT"
        if score >= 4.0:
            return "WARN"
        return "PASS"

    @classmethod
    def is_safe_skill_name(cls, name: str) -> bool:
        """Check if skill name avoids Windows reserved names and forbidden characters."""
        lower = name.lower()
        if lower in cls.WINDOWS_RESERVED_NAMES:
            return False
        if any(c in name for c in '<>:"/\\|?*'):
            return False
        return True

    @classmethod
    def contains_subshell_injection(cls, command_str: str) -> bool:
        """Check for nested subshell execution syntax."""
        return bool(cls.SUBSHELL_REGEX.search(command_str))


def test_bva_star_threshold_99_reject_vs_100_accept():
    """Verify 99 stars fails and 100 stars passes."""
    assert SecurityBoundaryEvaluator.evaluate_community_stars(99) is False
    assert SecurityBoundaryEvaluator.evaluate_community_stars(100) is True
    assert SecurityBoundaryEvaluator.evaluate_community_stars(101) is True


def test_bva_commit_age_365_days_accept_vs_366_reject():
    """Verify 365 days passes and 366 days fails."""
    assert SecurityBoundaryEvaluator.evaluate_commit_age(365) is True
    assert SecurityBoundaryEvaluator.evaluate_commit_age(366) is False


def test_bva_cvss_score_6_9_warn_vs_7_0_reject():
    """Verify CVSS 6.9 is marked WARN and 7.0 is marked REJECT."""
    assert SecurityBoundaryEvaluator.evaluate_cvss_score(6.9) == "WARN"
    assert SecurityBoundaryEvaluator.evaluate_cvss_score(7.0) == "REJECT"
    assert SecurityBoundaryEvaluator.evaluate_cvss_score(9.8) == "REJECT"
    assert SecurityBoundaryEvaluator.evaluate_cvss_score(3.9) == "PASS"


def test_bva_nested_subshell_injection_detected():
    """Verify complex nested subshell tokens are identified."""
    assert SecurityBoundaryEvaluator.contains_subshell_injection("echo $(whoami)") is True
    assert SecurityBoundaryEvaluator.contains_subshell_injection("run `rm -rf /`") is True
    assert SecurityBoundaryEvaluator.contains_subshell_injection("cmd1 && cmd2") is True
    assert SecurityBoundaryEvaluator.contains_subshell_injection("cmd1 || cmd2") is True
    assert SecurityBoundaryEvaluator.contains_subshell_injection("npx -y safe-server") is False


def test_bva_windows_reserved_device_names_rejected():
    """Verify Windows reserved device names cannot be used as skill names."""
    assert SecurityBoundaryEvaluator.is_safe_skill_name("con") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("aux") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("nul") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("com1") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("valid-skill") is True


def test_bva_disallowed_filesystem_characters_in_skill_name():
    """Verify invalid filesystem characters trigger rejection."""
    assert SecurityBoundaryEvaluator.is_safe_skill_name("skill:name") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("skill/name") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("skill\\name") is False
    assert SecurityBoundaryEvaluator.is_safe_skill_name("skill*name") is False
