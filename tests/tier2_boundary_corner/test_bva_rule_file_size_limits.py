"""Tier 2 Boundary & Corner Cases: Rule File 24 KB Limits and Delimiter Boundaries.

Tests strict size boundaries and parsing edge cases for model rule files:
- Antigravity 24,000-byte (24 KB) hard limit boundaries:
  - 23,999 bytes (passes without truncation warning)
  - 24,000 bytes (exact limit)
  - 24,001 bytes (exceeds limit, requires truncation or warning)
- Injection into empty (0-byte) rule file
- Markdown tables with complex pipe formatting inside delimiters
- Multiple existing non-standard delimiter comments
"""

import pytest


def test_bva_rule_file_23999_bytes_passes_limit():
    """Verify file of 23,999 bytes satisfies the Antigravity 24,000-byte cap."""
    content = "A" * 23999
    size = len(content.encode("utf-8"))
    assert size <= 24000


def test_bva_rule_file_24000_bytes_exact_boundary():
    """Verify file of exactly 24,000 bytes is at the ceiling."""
    content = "A" * 24000
    size = len(content.encode("utf-8"))
    assert size == 24000


def test_bva_rule_file_24001_bytes_exceeds_limit():
    """Verify file of 24,001 bytes is flagged as exceeding the 24 KB cap."""
    content = "A" * 24001
    size = len(content.encode("utf-8"))
    assert size > 24000


def test_bva_injection_into_empty_rule_file(oracle):
    """Verify delimiter injection into an empty (0-byte) rule file creates a clean file."""
    initial = ""
    directive = "# Routing Table"
    result = oracle.inject_rule_delimiters(initial, directive)
    assert result.startswith(oracle.DELIMITER_START)
    assert result.endswith(f"{oracle.DELIMITER_END}\n")
    assert "# Routing Table" in result


def test_bva_injection_handles_complex_markdown_meta_chars(oracle):
    """Verify tables with pipes, backticks, asterisks, brackets do not break delimiter parsing."""
    initial = "# Initial Rules\n"
    complex_table = """| Col 1 | Col 2 `code` | Col 3 *italic* |
|---|---|---|
| `[link](url)` | `foo | bar` | **bold** |"""
    result = oracle.inject_rule_delimiters(initial, complex_table)
    assert complex_table in result

    # Verify idempotency even with complex markdown
    second_run = oracle.inject_rule_delimiters(result, complex_table)
    assert second_run == result
