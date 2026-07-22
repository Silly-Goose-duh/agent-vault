#!/usr/bin/env python3
"""Tests for ensure_vault idempotency."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENSURE = ROOT / "scripts" / "ensure_vault.py"


class EnsureVaultTests(unittest.TestCase):
    def test_creates_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "vault"
            data = Path(td) / "pdata"
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            env.pop("GROK_VAULT_PATH", None)
            r1 = subprocess.run(
                [sys.executable, str(ENSURE), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r1.returncode, 0, r1.stderr + r1.stdout)
            self.assertTrue((vault / "AGENTS.md").is_file())
            self.assertTrue((vault / "todos" / "TODO.md").is_file())
            self.assertTrue((vault / "me" / "secrets.local.md").is_file())

            about = vault / "me" / "about-me.md"
            about.write_text("# About Me\n\n## Identity\n\n- KeepMe\n", encoding="utf-8")

            r2 = subprocess.run(
                [sys.executable, str(ENSURE), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
            self.assertIn("KeepMe", about.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
