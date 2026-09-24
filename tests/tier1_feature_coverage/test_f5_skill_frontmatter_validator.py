"""Tier 1 Feature 5: SKILL.md Frontmatter & Progressive Disclosure Validator.

Tests Antigravity SKILL.md structural and metadata compliance:
- YAML frontmatter boundary delimitation (---)
- Lowercase alphanumeric hyphenated name regex enforcement
- Third-person activation description constraint (min 20 chars, max 1024 chars)
- Progressive disclosure validation (pointers to references/ and scripts/)
- Clean error reporting for malformed YAML frontmatters
"""

import pytest


def test_f5_valid_skill_frontmatter_passes(oracle):
    """Verify fully compliant SKILL.md content passes validation."""
    content = """---
name: opencut
description: Comprehensive guide and reference for OpenCut web-based video editor. Use when the user asks about video editing or timeline assembly.
---
# OpenCut Video Editor

## Overview
OpenCut is an open-source, privacy-first web-based video editor.

## When to Use
Use when editing video timelines.
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is True
    assert result["metadata"]["name"] == "opencut"
    assert "OpenCut web-based video editor" in result["metadata"]["description"]


def test_f5_uppercase_name_rejected(oracle):
    """Verify skill name containing uppercase letters is rejected."""
    content = """---
name: OpenCut-Tool
description: Comprehensive guide and reference for OpenCut video editor.
---
# Body
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is False
    assert "violates lowercase-hyphen pattern" in result["error"]


def test_f5_name_with_spaces_or_special_chars_rejected(oracle):
    """Verify skill name containing spaces or disallowed symbols is rejected."""
    bad_names = ["open cut", "opencut@tool", "open/cut", "-opencut", "opencut-"]
    for bn in bad_names:
        content = f"""---
name: {bn}
description: Valid description for this tool that meets the twenty character length requirement.
---
# Body
"""
        result = oracle.validate_skill_frontmatter(content)
        assert result["valid"] is False, f"Expected name '{bn}' to be rejected"


def test_f5_missing_description_field_rejected(oracle):
    """Verify frontmatter lacking 'description' is rejected."""
    content = """---
name: valid-name
---
# Body
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is False
    assert "Missing required field 'description'" in result["error"]


def test_f5_short_description_rejected(oracle):
    """Verify description under 20 characters is rejected."""
    content = """---
name: valid-name
description: Too short
---
# Body
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is False
    assert "Description shorter than 20 chars minimum" in result["error"]


def test_f5_unclosed_frontmatter_delimiter_rejected(oracle):
    """Verify unclosed frontmatter delimiter produces a structured error."""
    content = """---
name: valid-name
description: A sufficiently long description that satisfies the length requirement.
# Body without closing dashes
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is False
    assert "Unclosed frontmatter delimiter" in result["error"]


def test_f5_progressive_disclosure_reference_pointer_extraction(oracle):
    """Verify progressive disclosure links to references/ are identified in body."""
    content = """---
name: complex-tool
description: A tool utilizing progressive disclosure documentation.
---
# Complex Tool

For detailed architecture, see [Architecture Guide](./references/architecture.md).
For CLI scripts, run [deploy.ps1](./scripts/deploy.ps1).
"""
    result = oracle.validate_skill_frontmatter(content)
    assert result["valid"] is True
    body = result["body"]
    assert "./references/architecture.md" in body
    assert "./scripts/deploy.ps1" in body
