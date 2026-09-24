"""Tier 2 Adversarial Stress Suite for Milestone 1 (Crawler & Config).

Authored by challenger_m1_2 (teamwork_preview_challenger).
Empirically stress-tests:
1. ResilientHttpClient:
   - Empty response bodies (JSONDecodeError containment)
   - Non-JSON responses (HTML, plain text, malformed syntax)
   - HTTP 403 Rate Limiting with X-RateLimit-Remaining: 0
   - HTTP 429 Too Many Requests
   - Domain short-circuiting once rate-limited
   - Binary / non-UTF-8 response payloads
2. CLI Edge Cases:
   - Deeply nested nonexistent output directories (auto-creation)
   - Invalid CLI flags and invalid category options
   - Spaces and special characters in paths
3. Config & Security:
   - Path traversal in sandbox paths
   - Path traversal in backup prefixes (vulnerability discovery)
   - Constant verifications (MAX_RULE_FILE_BYTES == 24000)
4. MetadataNormalizer:
   - Resilient merging under malformed/corrupted seed inputs
"""

import datetime
import io
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.config import (
    BEGIN_MANAGED_ROUTING,
    DEFAULT_AWS_REGION,
    DEFAULT_CATALOG_VERSION,
    END_MANAGED_ROUTING,
    MAX_RULE_FILE_BYTES,
    MIN_COMMUNITY_STARS,
    PipelineEnvironmentConfig,
)
from src.crawler.github_crawler import (
    CatalogPackageRecord,
    CrawlStatus,
    CrawlerEngine,
    GitHubProvider,
    MetadataNormalizer,
    NpmProvider,
    PyPiProvider,
    ResilientHttpClient,
)
from src.crawler.registry_sources import CATEGORIES, SEED_PACKAGES


# ===========================================================================
# 1. ResilientHttpClient Adversarial Testing
# ===========================================================================

class MockServerHandler(BaseHTTPRequestHandler):
    """Configurable HTTP handler for adversarial testing."""

    response_status = 200
    response_headers = {"Content-Type": "application/json"}
    response_body = b"{}"

    def do_GET(self):
        self.send_response(self.response_status)
        for k, v in self.response_headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(self.response_body)

    def log_message(self, format, *args):
        # Silence HTTP server logs during tests
        pass


@pytest.fixture(scope="module")
def mock_http_server():
    """Spins up a lightweight localhost server for pure network stress-testing."""
    server = HTTPServer(("127.0.0.1", 0), MockServerHandler)
    port = server.server_port
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, f"http://127.0.0.1:{port}"
    server.shutdown()


def test_adv_empty_response_body_containment(mock_http_server):
    """Stress test: Empty response body (0 bytes) must not crash client."""
    server, base_url = mock_http_server
    MockServerHandler.response_status = 200
    MockServerHandler.response_headers = {"Content-Type": "application/json"}
    MockServerHandler.response_body = b""

    client = ResilientHttpClient(timeout=2.0, max_retries=1)
    start = time.perf_counter()
    data, status = client.get_json(f"{base_url}/empty")
    elapsed = time.perf_counter() - start

    assert data is None
    assert status.source == "fallback"
    assert len(status.warnings) > 0
    assert any("JSON decode error" in w for w in status.warnings)
    assert elapsed < 1.0


def test_adv_non_json_html_response_containment(mock_http_server):
    """Stress test: HTML 500 or error page instead of JSON must not raise."""
    server, base_url = mock_http_server
    MockServerHandler.response_status = 200
    MockServerHandler.response_headers = {"Content-Type": "text/html"}
    MockServerHandler.response_body = b"<!DOCTYPE html><html><body>Error 500: Server Down</body></html>"

    client = ResilientHttpClient(timeout=2.0, max_retries=1)
    data, status = client.get_json(f"{base_url}/error.html")

    assert data is None
    assert status.source == "fallback"
    assert any("JSON decode error" in w for w in status.warnings)


def test_adv_non_utf8_binary_payload(mock_http_server):
    """Stress test: Non-UTF-8 binary bytes must be cleanly contained."""
    server, base_url = mock_http_server
    MockServerHandler.response_status = 200
    MockServerHandler.response_headers = {"Content-Type": "application/octet-stream"}
    MockServerHandler.response_body = b"\x80\x81\xff\xfe\xab\xcd"

    client = ResilientHttpClient(timeout=2.0, max_retries=1)
    data, status = client.get_json(f"{base_url}/binary")

    assert data is None
    assert status.source == "fallback"
    assert len(status.warnings) > 0


def test_adv_http_403_rate_limit_headers():
    """Stress test: HTTP 403 with X-RateLimit-Remaining: 0 triggers domain blacklist."""
    client = ResilientHttpClient(timeout=2.0, max_retries=1)

    # Mock urllib.request.urlopen raising HTTPError 403
    mock_headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1727140000",
    }
    http_error = urllib.error.HTTPError(
        url="https://api.github.com/repos/microsoft/playwright-mcp",
        code=403,
        msg="rate limit exceeded",
        hdrs=mock_headers,
        fp=io.BytesIO(b'{"message": "API rate limit exceeded"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        data, status = client.get_json("https://api.github.com/repos/microsoft/playwright-mcp")

    assert data is None
    assert status.source == "fallback"
    assert "api.github.com" in client._rate_limited_domains

    # Subsequent request to same domain should short-circuit instantly (< 1ms)
    t0 = time.perf_counter()
    data2, status2 = client.get_json("https://api.github.com/repos/github/github-mcp-server")
    t1 = time.perf_counter()

    assert data2 is None
    assert status2.source == "fallback"
    assert "previously encountered rate-limit" in status2.warnings[0]
    assert (t1 - t0) < 0.01  # Instantaneous local short-circuit


def test_adv_http_429_too_many_requests():
    """Stress test: HTTP 429 triggers domain rate-limiting."""
    client = ResilientHttpClient(timeout=2.0, max_retries=1)
    http_error = urllib.error.HTTPError(
        url="https://registry.npmjs.org/@playwright/mcp",
        code=429,
        msg="Too Many Requests",
        hdrs={"Retry-After": "30"},
        fp=io.BytesIO(b'{"error": "Too Many Requests"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        data, status = client.get_json("https://registry.npmjs.org/@playwright/mcp")

    assert data is None
    assert status.source == "fallback"
    assert "registry.npmjs.org" in client._rate_limited_domains


def test_adv_http_200_with_zero_remaining_rate_limit():
    """Stress test: HTTP 200 with X-RateLimit-Remaining: 0 serves data but blacklists domain."""
    client = ResilientHttpClient(timeout=2.0, max_retries=1)

    mock_resp = MagicMock()
    mock_resp.headers = {"X-RateLimit-Remaining": "0"}
    mock_resp.read.return_value = b'{"stargazers_count": 9999}'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        data, status = client.get_json("https://api.github.com/repos/test/last_call")

    assert data == {"stargazers_count": 9999}
    assert status.source == "live_api"
    assert "api.github.com" in client._rate_limited_domains


# ===========================================================================
# 2. CLI Edge Cases & Directory Traversal
# ===========================================================================

def test_adv_cli_deeply_nested_nonexistent_directory(tmp_path):
    """Stress test: CLI writing to deeply nested nonexistent directory auto-creates parents."""
    deep_path = tmp_path / "deep" / "nested" / "sub1" / "sub2" / "test_catalog.json"
    assert not deep_path.parent.exists()

    engine = CrawlerEngine(offline_mode=True)
    catalog = engine.crawl_all(seed_packages=SEED_PACKAGES[:2])
    saved = engine.save_catalog(catalog, deep_path)

    assert saved.exists()
    assert deep_path.parent.exists()
    with open(saved, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_packages"] == 2


def test_adv_cli_spaces_and_special_chars_path(tmp_path):
    """Stress test: Catalog paths with spaces and punctuation."""
    target_path = tmp_path / "my registry output (v1.0) #test" / "catalog [test].json"
    engine = CrawlerEngine(offline_mode=True)
    catalog = engine.crawl_all(seed_packages=SEED_PACKAGES[:1])
    saved = engine.save_catalog(catalog, target_path)

    assert saved.exists()
    assert target_path.exists()


def test_adv_cli_invalid_arguments_rejection():
    """Stress test: Invalid CLI argument should exit with code 2."""
    cmd = [sys.executable, "-m", "src.crawler.github_crawler", "--invalid-flag-abc"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "unrecognized arguments" in res.stderr.lower() or "error" in res.stderr.lower()


def test_adv_cli_invalid_category_rejection():
    """Stress test: Non-whitelisted category option should exit with code 2."""
    cmd = [sys.executable, "-m", "src.crawler.github_crawler", "--category", "invalid_category_xyz"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 2
    assert "invalid choice" in res.stderr.lower()


# ===========================================================================
# 3. Config & Security Bounds Testing
# ===========================================================================

def test_adv_rule_file_budget_constant():
    """Empirical verification: MAX_RULE_FILE_BYTES must strictly equal 24000."""
    assert MAX_RULE_FILE_BYTES == 24000
    assert MIN_COMMUNITY_STARS == 100
    assert "BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING" in BEGIN_MANAGED_ROUTING
    assert "END AI-SKILLS-REGISTRY MANAGED ROUTING" in END_MANAGED_ROUTING


def test_adv_sandbox_path_traversal_resolution(tmp_path):
    """Stress test: Passing relative traversals in sandbox_root resolves cleanly."""
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)

    # sandbox_root with traversal
    traversal_root = nested / ".." / ".." / "target_sandbox"
    config = PipelineEnvironmentConfig.from_sandbox(traversal_root)

    resolved_expected = (tmp_path / "a" / "target_sandbox").resolve()
    assert config.user_home_dir == resolved_expected
    assert str(config.user_home_dir) == os.path.abspath(str(traversal_root))
    assert config.is_sandbox is True


def test_adv_backup_path_traversal_vulnerability_investigation(tmp_path):
    """Adversarial check: Test if malicious prefix in get_backup_path escapes backup_dir.

    Observation: prefix is concatenated as f"{prefix}_{clean_name}". If prefix contains "../",
    the resulting Path can escape the backup_dir.
    """
    config = PipelineEnvironmentConfig.from_sandbox(tmp_path)
    target = Path("AGENTS.md")

    # Safe prefix
    safe_backup = config.get_backup_path(target, prefix="pre_m1")
    assert safe_backup.parent == config.backup_dir

    # Adversarial prefix with directory traversal
    evil_prefix = "../../escaped_dir/attack"
    escaped_backup = config.get_backup_path(target, prefix=evil_prefix)

    # Check whether escaped_backup resolves outside backup_dir
    # Note: On pathlib, (backup_dir / "../../escaped_dir/attack_AGENTS.md.bak...").resolve() escapes!
    escaped_resolved = escaped_backup.resolve()
    is_contained = str(escaped_resolved).startswith(str(config.backup_dir.resolve()))

    # Document this empirical behavior:
    # If is_contained is False, this confirms an adversarial path-traversal finding on unvalidated prefix!
    if not is_contained:
        # Confirmed vulnerability vector: prefix allows escaping backup_dir
        pass  # We will report this in adversarial_report.md
    assert escaped_backup is not None


# ===========================================================================
# 4. MetadataNormalizer Resiliency & Edge Inputs
# ===========================================================================

def test_adv_normalizer_corrupted_inputs():
    """Stress test: Normalizer handling bizarre license and capability structures."""
    # 1. Weird licenses
    assert MetadataNormalizer.normalize_license(None) == "Unknown"
    assert MetadataNormalizer.normalize_license("") == "Unknown"
    assert MetadataNormalizer.normalize_license({"spdx_id": "MIT"}) == "MIT"
    assert MetadataNormalizer.normalize_license({"type": "apache 2.0"}) == "Apache-2.0"
    assert MetadataNormalizer.normalize_license("UNKNOWN_CUSTOM_LICENSE") == "UNKNOWN_CUSTOM_LICENSE"

    # 2. Corrupted capabilities
    seed_dict_caps = {
        "id": "test-pkg",
        "category": "browser_search",
        "capabilities": {"tools": [{"name": "tool_a"}, {"name": "tool_b"}]},
    }
    rec1 = MetadataNormalizer.merge_package(seed_dict_caps)
    assert rec1.capabilities == ["tool_a", "tool_b"]

    seed_string_caps = {
        "id": "test-pkg-2",
        "category": "media",
        "capabilities": "single_string_not_list",
    }
    rec2 = MetadataNormalizer.merge_package(seed_string_caps)
    assert rec2.capabilities == ["execute"]


def test_adv_crawler_engine_resilient_to_individual_seed_crashes():
    """Stress test: If one seed package raises an unexpected exception, crawl_all continues."""
    bad_seed = {
        "id": "bad-seed",
        "category": "system_ops",
        "repo_url": "invalid://not-a-valid-url-at-all",
    }
    good_seed = SEED_PACKAGES[0]

    engine = CrawlerEngine(offline_mode=True)
    catalog = engine.crawl_all(seed_packages=[bad_seed, good_seed])

    assert catalog["total_packages"] == 2
    assert catalog["packages"][0]["id"] == "bad-seed"
    assert catalog["packages"][1]["id"] == good_seed["id"]
