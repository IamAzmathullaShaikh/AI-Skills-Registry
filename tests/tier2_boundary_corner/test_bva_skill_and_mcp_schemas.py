"""Tier 2 Boundary & Corner Cases: SKILL.md and MCP Server Schema Boundaries.

Tests exact boundary conditions for YAML frontmatter and JSON-RPC transport definitions:
- Description character length boundaries: 19 (reject) vs 20 (accept)
- Description upper limit: 1024 (accept) vs 1025 (reject)
- Name regex boundaries (leading/trailing hyphens, single-character names)
- MCP environment dictionary scaling and boundary sizing
"""

import pytest


def test_bva_description_length_19_chars_rejected(oracle):
    """Verify description of exactly 19 characters is rejected."""
    desc_19 = "A" * 19
    content = f"""---
name: valid-name
description: {desc_19}
---
# Body
"""
    res = oracle.validate_skill_frontmatter(content)
    assert res["valid"] is False
    assert "Description shorter than 20 chars minimum" in res["error"]


def test_bva_description_length_20_chars_accepted(oracle):
    """Verify description of exactly 20 characters is accepted."""
    desc_20 = "A" * 20
    content = f"""---
name: valid-name
description: {desc_20}
---
# Body
"""
    res = oracle.validate_skill_frontmatter(content)
    assert res["valid"] is True


def test_bva_description_length_1024_chars_accepted(oracle):
    """Verify description of exactly 1,024 characters is accepted."""
    desc_1024 = "A" * 1024
    content = f"""---
name: valid-name
description: {desc_1024}
---
# Body
"""
    res = oracle.validate_skill_frontmatter(content)
    assert res["valid"] is True


def test_bva_description_length_1025_chars_rejected(oracle):
    """Verify description of 1,025 characters is rejected."""
    desc_1025 = "A" * 1025
    content = f"""---
name: valid-name
description: {desc_1025}
---
# Body
"""
    res = oracle.validate_skill_frontmatter(content)
    assert res["valid"] is False
    assert "Description longer than 1,024 chars maximum" in res["error"]


def test_bva_skill_name_single_character_accepted(oracle):
    """Verify single alphanumeric character name is valid under regex."""
    content = """---
name: x
description: Valid description of minimum twenty characters length.
---
# Body
"""
    res = oracle.validate_skill_frontmatter(content)
    assert res["valid"] is True


def test_bva_skill_name_leading_and_trailing_hyphen_rejected(oracle):
    """Verify leading or trailing hyphens fail regex validation."""
    for bad_name in ["-tool", "tool-", "-tool-"]:
        content = f"""---
name: {bad_name}
description: Valid description of minimum twenty characters length.
---
# Body
"""
        res = oracle.validate_skill_frontmatter(content)
        assert res["valid"] is False
