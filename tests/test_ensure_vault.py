#!/usr/bin/env python3
"""Tests for vault ensure + helpers."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib_vault import (  # noqa: E402
    brief_context_for_agent,
    migrate_secrets_to_deep,
    secrets_file,
)


class EnsureVaultTests(unittest.TestCase):
    def test_creates_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "vault"
            data = Path(td) / "pdata"
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            env["AGENT_VAULT_PATH"] = str(vault)
            r1 = subprocess.run(
                [sys.executable, str(SCRIPTS / "ensure_vault.py"), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r1.returncode, 0, r1.stderr + r1.stdout)
            self.assertTrue((vault / "me" / "about-me.md").is_file())
            self.assertTrue((vault / "todos" / "TODO.md").is_file())
            self.assertTrue((vault / "me" / ".private").is_dir())
            sec = secrets_file(vault)
            self.assertTrue(sec.is_file())
            self.assertIn(".private", sec.parts)

            # idempotent
            before = (vault / "me" / "about-me.md").read_text(encoding="utf-8")
            (vault / "me" / "about-me.md").write_text(before + "\n- Keep me\n", encoding="utf-8")
            r2 = subprocess.run(
                [sys.executable, str(SCRIPTS / "ensure_vault.py"), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
            after = (vault / "me" / "about-me.md").read_text(encoding="utf-8")
            self.assertIn("Keep me", after)

    def test_migrate_legacy_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me").mkdir()
            legacy = vault / "me" / "secrets.local.md"
            legacy.write_text(
                "## Entries\n\n"
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|------------|------|-------|-------|--------|\n"
                "| 2026-01-01T00:00:00Z | api_key | x | SECRET_MIGRATE_VAL | old |\n",
                encoding="utf-8",
            )
            moved = migrate_secrets_to_deep(vault)
            self.assertIsNotNone(moved)
            deep = secrets_file(vault)
            self.assertIn(".private", deep.parts)
            self.assertIn("SECRET_MIGRATE_VAL", deep.read_text(encoding="utf-8"))
            # stub at legacy
            stub = legacy.read_text(encoding="utf-8")
            self.assertNotIn("SECRET_MIGRATE_VAL", stub)

    def test_brief_context_no_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me").mkdir()
            (vault / "todos").mkdir()
            (vault / "me" / "about-me.md").write_text(
                "## Identity\n\n- Jordan Lee\n", encoding="utf-8"
            )
            (vault / "me" / "preferences.md").write_text("", encoding="utf-8")
            (vault / "todos" / "TODO.md").write_text("- [ ] Ship plugin\n", encoding="utf-8")
            (vault / "me" / ".private").mkdir()
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|------------|------|-------|-------|--------|\n"
                "| t | api_key | k | SUPER_SECRET_VALUE_XYZ | t |\n",
                encoding="utf-8",
            )
            ctx = brief_context_for_agent(vault)
            self.assertIn("Jordan Lee", ctx)
            self.assertIn("Ship plugin", ctx)
            self.assertNotIn("SUPER_SECRET_VALUE_XYZ", ctx)
            self.assertIn("Secrets stored: 1", ctx)


if __name__ == "__main__":
    unittest.main()
