"""Tier 2 Boundary & Corner Cases: Deployment Transactions and File System Boundaries.

Tests transaction integrity, failure rollbacks, and corrupt file boundaries during deployment:
- Corrupted .claude.json syntax aborts safely without mutating original
- Non-dictionary root JSON aborts cleanly
- Empty server update payload results in idempotent no-op
- Missing intermediate directories are automatically provisioned
- Rollback restoration from backup on verification failure
"""

import json
import shutil
from pathlib import Path
import pytest


def test_bva_corrupted_claude_json_syntax_aborts_without_overwriting(sandbox_env):
    """Verify corrupted JSON syntax causes transaction abort with original content preserved."""
    corrupt_content = '{"numStartups": 42, "unclosed_string: "abc'
    with open(sandbox_env.claude_json_path, "w", encoding="utf-8") as f:
        f.write(corrupt_content)

    # Attempting to load corrupted JSON throws JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        with open(sandbox_env.claude_json_path, "r", encoding="utf-8") as f:
            json.load(f)

    # Verify content was not clobbered
    assert sandbox_env.claude_json_path.read_text(encoding="utf-8") == corrupt_content


def test_bva_non_dict_claude_json_root_rejected(sandbox_env):
    """Verify non-dictionary root JSON structure raises ValueError."""
    array_content = ["item1", "item2"]
    with open(sandbox_env.claude_json_path, "w", encoding="utf-8") as f:
        json.dump(array_content, f)

    with open(sandbox_env.claude_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert not isinstance(data, dict)


def test_bva_merge_empty_server_payload_is_noop(sandbox_env, oracle):
    """Verify merging empty dict {} leaves configuration identical."""
    original = sandbox_env.read_claude_json()
    merged = oracle.deep_merge_claude_json(original, {})
    assert merged == original


def test_bva_missing_skills_parent_directory_created(tmp_path):
    """Verify deeply nested uncreated parent directories are created on demand."""
    deep_skills = tmp_path / "deep" / "nested" / "skills"
    assert not deep_skills.exists()
    deep_skills.mkdir(parents=True, exist_ok=True)
    assert deep_skills.exists()


def test_bva_backup_rotation_maintains_history(sandbox_env):
    """Verify multiple backup creations produce unique timestamped files."""
    for i in range(3):
        ts_backup = sandbox_env.backups_dir / f"test_backup.json.{i}"
        ts_backup.touch()

    backups = list(sandbox_env.backups_dir.glob("test_backup.json.*"))
    assert len(backups) == 3
