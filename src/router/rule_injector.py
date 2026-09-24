"""Idempotent Managed Delimiter Rule Injection Engine.

Injects compact routing directives into AGENTS.md, CLAUDE.md, and GEMINI.md
using non-destructive HTML comments, preserving pre-existing AWS rules
and Crave Cloud Compilation policies with 100% idempotency and size caps.
"""

from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

DELIMITER_START = "<!-- BEGIN AI-SKILLS-REGISTRY MANAGED ROUTING -->"
DELIMITER_END = "<!-- END AI-SKILLS-REGISTRY MANAGED ROUTING -->"
MAX_RULE_FILE_BYTES = 24000


class RuleInjector:
    """Production rule injector with delimiter preservation and atomic writes."""

    DELIMITER_START = DELIMITER_START
    DELIMITER_END = DELIMITER_END

    @classmethod
    def inject_rule_delimiters(cls, content: str, directive: str) -> str:
        """Inject directive into markdown content between managed delimiters."""
        managed_block = f"{cls.DELIMITER_START}\n{directive.strip()}\n{cls.DELIMITER_END}"

        pattern = re.compile(
            rf"{re.escape(cls.DELIMITER_START)}.*?{re.escape(cls.DELIMITER_END)}",
            re.DOTALL,
        )

        if pattern.search(content):
            updated = pattern.sub(managed_block, content)
        else:
            if content.strip():
                updated = f"{content.rstrip()}\n\n{managed_block}\n"
            else:
                updated = f"{managed_block}\n"

        byte_size = len(updated.encode("utf-8"))
        if byte_size > MAX_RULE_FILE_BYTES:
            raise ValueError(
                f"Resulting rule content ({byte_size} bytes) exceeds {MAX_RULE_FILE_BYTES}-byte threshold"
            )

        return updated

    @classmethod
    def inject_into_file(
        cls,
        file_path: Path,
        directive: str,
        backup_dir: Path,
    ) -> Dict[str, Any]:
        """Safely and idempotently inject routing directive into target rule file."""
        backup_dir.mkdir(parents=True, exist_ok=True)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        initial_content = ""
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                initial_content = f.read()

            # Create backup if file is non-empty
            if initial_content.strip():
                ts = int(time.time() * 1000)
                backup_file = backup_dir / f"{file_path.name}.bak.{ts}"
                shutil.copy2(file_path, backup_file)

        updated_content = cls.inject_rule_delimiters(initial_content, directive)

        # Atomic replacement
        tmp_file = file_path.with_suffix(f".tmp.{os.getpid()}_{int(time.time()*1000)}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(updated_content)

        os.replace(tmp_file, file_path)

        return {
            "status": "SUCCESS",
            "file": str(file_path),
            "bytes": len(updated_content.encode("utf-8")),
        }
