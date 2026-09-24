"""Core Configuration & Environment Management Module for AI-Skills-Registry.

Provides PipelineEnvironmentConfig supporting both live host environments
and isolated mock sandboxes for safe E2E testing and non-destructive deployments.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Delimiter markers for non-destructive rule injection
BEGIN_MANAGED_ROUTING = "<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->"
END_MANAGED_ROUTING = "<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->"

# Antigravity rule budget and constraint constants
MAX_RULE_FILE_BYTES = 24000  # 24 KB per-file threshold
MIN_COMMUNITY_STARS = 100    # Quality threshold for non-official repos
DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_CATALOG_VERSION = "1.0.0"


@dataclass(frozen=True)
class PipelineEnvironmentConfig:
    """Immutable configuration representing runtime paths and platform settings.

    Supports seamless switching between live host directories and isolated
    virtual sandboxes to guarantee test safety without code mutation.
    """

    project_root: Path
    user_home_dir: Path
    gemini_config_dir: Path
    gemini_skills_dir: Path
    gemini_mcp_config: Path
    gemini_skills_manifest: Path
    claude_json_path: Path
    agents_rule_file: Path
    claude_rule_file: Path
    gemini_rule_file: Path
    gemini_sub_rule_file: Path
    catalog_file: Path
    catalog_readme: Path
    backup_dir: Path
    is_sandbox: bool = False
    dry_run: bool = False
    github_token: Optional[str] = None
    aws_region: str = DEFAULT_AWS_REGION
    log_level: str = "INFO"

    @classmethod
    def live_default(
        cls,
        project_root: Optional[Path] = None,
        dry_run: bool = False,
    ) -> PipelineEnvironmentConfig:
        """Creates a configuration instance bound to the host user's actual files."""
        home = Path.home()
        if project_root is None:
            # Resolves repo root from src/config.py -> ../..
            project_root = Path(__file__).resolve().parent.parent

        gemini_config = home / ".gemini" / "config"
        backup_directory = home / ".ai-skills-registry" / "backups"

        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        region = os.environ.get("AWS_REGION", DEFAULT_AWS_REGION)
        dry_run_env = os.environ.get("AI_SKILLS_DRY_RUN", "").lower() in ("1", "true", "yes")

        return cls(
            project_root=project_root,
            user_home_dir=home,
            gemini_config_dir=gemini_config,
            gemini_skills_dir=gemini_config / "skills",
            gemini_mcp_config=gemini_config / "mcp_config.json",
            gemini_skills_manifest=gemini_config / "skills.json",
            claude_json_path=home / ".claude.json",
            agents_rule_file=home / "AGENTS.md",
            claude_rule_file=home / "CLAUDE.md",
            gemini_rule_file=home / "GEMINI.md",
            gemini_sub_rule_file=home / ".gemini" / "GEMINI.md",
            catalog_file=project_root / "catalog.json",
            catalog_readme=project_root / "README.md",
            backup_dir=backup_directory,
            is_sandbox=False,
            dry_run=dry_run or dry_run_env,
            github_token=token,
            aws_region=region,
            log_level=os.environ.get("AI_SKILLS_LOG_LEVEL", "INFO"),
        )

    @classmethod
    def from_sandbox(
        cls,
        sandbox_root: Path | str,
        project_root: Optional[Path] = None,
        dry_run: bool = False,
        populate_fixtures: bool = False,
    ) -> PipelineEnvironmentConfig:
        """Creates an isolated mock sandbox configuration under sandbox_root.

        All modifications in this mode are strictly isolated from host files.
        """
        sandbox = Path(sandbox_root).resolve()
        if project_root is None:
            project_root = sandbox / "AI-Skills-Registry"

        gemini_config = sandbox / ".gemini" / "config"
        backup_directory = sandbox / ".backups"

        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        region = os.environ.get("AWS_REGION", DEFAULT_AWS_REGION)
        dry_run_env = os.environ.get("AI_SKILLS_DRY_RUN", "").lower() in ("1", "true", "yes")

        config = cls(
            project_root=project_root,
            user_home_dir=sandbox,
            gemini_config_dir=gemini_config,
            gemini_skills_dir=gemini_config / "skills",
            gemini_mcp_config=gemini_config / "mcp_config.json",
            gemini_skills_manifest=gemini_config / "skills.json",
            claude_json_path=sandbox / ".claude.json",
            agents_rule_file=sandbox / "AGENTS.md",
            claude_rule_file=sandbox / "CLAUDE.md",
            gemini_rule_file=sandbox / "GEMINI.md",
            gemini_sub_rule_file=sandbox / ".gemini" / "GEMINI.md",
            catalog_file=project_root / "catalog.json",
            catalog_readme=project_root / "README.md",
            backup_dir=backup_directory,
            is_sandbox=True,
            dry_run=dry_run or dry_run_env,
            github_token=token,
            aws_region=region,
            log_level=os.environ.get("AI_SKILLS_LOG_LEVEL", "INFO"),
        )

        if populate_fixtures:
            config._populate_sandbox_fixtures()

        return config

    @classmethod
    def from_env(cls) -> PipelineEnvironmentConfig:
        """Instantiates configuration according to the AI_SKILLS_SANDBOX_DIR env var.

        If set, uses sandbox mode; otherwise, uses live_default().
        """
        sandbox_path = os.environ.get("AI_SKILLS_SANDBOX_DIR")
        if sandbox_path:
            return cls.from_sandbox(sandbox_path)
        return cls.live_default()

    def ensure_directories(self) -> None:
        """Creates all essential directories if they do not yet exist.

        Safe and idempotent.
        """
        self.gemini_skills_dir.mkdir(parents=True, exist_ok=True)
        self.gemini_config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
        self.gemini_sub_rule_file.parent.mkdir(parents=True, exist_ok=True)

    def get_backup_path(self, target_file: Path, prefix: str = "") -> Path:
        """Computes a non-colliding timestamped backup path for the target file."""
        timestamp = int(time.time())
        rand_suffix = uuid.uuid4().hex[:6]
        clean_name = target_file.name.lstrip(".")
        prefix_str = f"{prefix}_" if prefix else ""
        backup_name = f"{prefix_str}{clean_name}.bak.{timestamp}_{rand_suffix}"
        return self.backup_dir / backup_name

    def validate_environment(self) -> List[str]:
        """Runs validation checks on path accessibility and configuration health.

        Returns a list of warning or error messages (empty list if healthy).
        """
        warnings: List[str] = []
        if not self.project_root.exists():
            warnings.append(f"Project root does not exist: {self.project_root}")

        if not self.is_sandbox:
            if not self.user_home_dir.exists():
                warnings.append(f"User home directory not found: {self.user_home_dir}")
            if not self.claude_json_path.exists():
                warnings.append(f"Claude Code config file missing at: {self.claude_json_path}")

        return warnings

    def _populate_sandbox_fixtures(self) -> None:
        """Populates standard mock fixtures in the sandbox directory to

        accurately simulate the host environment during automated tests.
        """
        self.ensure_directories()

        # 1. Mock ~/.claude.json with active tinyfish entry
        if not self.claude_json_path.exists():
            mock_claude = {
                "numStartups": 42,
                "autoUpdates": True,
                "mcpServers": {
                    "tinyfish": {
                        "type": "http",
                        "url": "https://agent.tinyfish.ai/mcp?source=mock",
                        "headers": {
                            "X-API-Key": "sk-tinyfish-mock-key-12345"
                        }
                    }
                }
            }
            with open(self.claude_json_path, "w", encoding="utf-8") as f:
                json.dump(mock_claude, f, indent=2)

        # 2. Mock ~/.gemini/config/mcp_config.json (touch/empty)
        if not self.gemini_mcp_config.exists():
            with open(self.gemini_mcp_config, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {}}, f, indent=2)

        # 3. Mock ~/.gemini/config/skills.json
        if not self.gemini_skills_manifest.exists():
            with open(self.gemini_skills_manifest, "w", encoding="utf-8") as f:
                json.dump({"entries": [{"path": "~/.gemini/config/skills"}]}, f, indent=2)

        # 4. Mock AGENTS.md with pre-existing AWS & Crave policies
        if not self.agents_rule_file.exists():
            content = (
                "# Agent Guidelines\n\n"
                "<!-- BEGIN AWS Agent Toolkit rules -->\n"
                "Project Region: us-east-1\n"
                "<!-- END AWS Agent Toolkit rules -->\n\n"
                "# Heavy Builds & Cloud Compilation Policy: Crave Builder\n"
                "- crave.exe -n run -- <cmd>\n"
            )
            with open(self.agents_rule_file, "w", encoding="utf-8") as f:
                f.write(content)

        # 5. Mock CLAUDE.md and GEMINI.md
        for rule_path in (self.claude_rule_file, self.gemini_rule_file, self.gemini_sub_rule_file):
            if not rule_path.exists():
                with open(rule_path, "w", encoding="utf-8") as f:
                    f.write("# Rule File\n- Standard baseline directive\n")

    def as_dict(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """Returns a dictionary representation of paths and environment state."""
        token = self.github_token
        if mask_secrets and token:
            token = f"{token[:3]}...***" if len(token) > 6 else "***"

        return {
            "project_root": str(self.project_root),
            "user_home_dir": str(self.user_home_dir),
            "gemini_config_dir": str(self.gemini_config_dir),
            "gemini_skills_dir": str(self.gemini_skills_dir),
            "gemini_mcp_config": str(self.gemini_mcp_config),
            "gemini_skills_manifest": str(self.gemini_skills_manifest),
            "claude_json_path": str(self.claude_json_path),
            "agents_rule_file": str(self.agents_rule_file),
            "claude_rule_file": str(self.claude_rule_file),
            "gemini_rule_file": str(self.gemini_rule_file),
            "gemini_sub_rule_file": str(self.gemini_sub_rule_file),
            "catalog_file": str(self.catalog_file),
            "catalog_readme": str(self.catalog_readme),
            "backup_dir": str(self.backup_dir),
            "is_sandbox": self.is_sandbox,
            "dry_run": self.dry_run,
            "github_token": token,
            "aws_region": self.aws_region,
            "log_level": self.log_level,
        }

    def __repr__(self) -> str:
        mode = "SANDBOX" if self.is_sandbox else "LIVE"
        dry = " [DRY-RUN]" if self.dry_run else ""
        return f"<PipelineEnvironmentConfig mode={mode}{dry} home={self.user_home_dir}>"
