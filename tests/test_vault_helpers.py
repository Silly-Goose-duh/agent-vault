#!/usr/bin/env python3
"""Tests for vault dashboard helpers and scripts."""

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
    _is_highlight_repo,
    format_box,
    list_open_todos,
    list_secret_keys,
    parse_about_simple,
    render_creative_dashboard,
)


class VaultHelperTests(unittest.TestCase):
    def test_list_open_todos_and_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "todos").mkdir()
            (vault / "me" / ".private").mkdir(parents=True)
            (vault / "todos" / "TODO.md").write_text(
                "# Todos\n\n- [ ] Ship vaultkeys\n- [x] Done item\n- [ ] Second open\n",
                encoding="utf-8",
            )
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "# Secrets\n\n## Entries\n\n"
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|------------|------|-------|-------|--------|\n"
                "| 2026-01-01T00:00:00Z | api_key | demo | SECRET_VALUE_NEVER | test |\n",
                encoding="utf-8",
            )
            (vault / "me" / "about-me.md").write_text(
                "# About Me\n\n## Identity\n\n- (name, role)\n- Alice Dev\n",
                encoding="utf-8",
            )
            (vault / "me" / "preferences.md").write_text(
                "# Preferences\n\n## Communication\n\n- Prefer bullets\n",
                encoding="utf-8",
            )

            todos = list_open_todos(vault)
            self.assertEqual(todos, ["Ship vaultkeys", "Second open"])

            keys = list_secret_keys(vault)
            self.assertEqual(len(keys), 1)
            self.assertEqual(keys[0]["label"], "demo")
            self.assertNotIn("SECRET_VALUE_NEVER", str(keys))

            about = parse_about_simple(vault)
            self.assertTrue(any("Alice Dev" in a for a in about))
            self.assertFalse(any("(name, role)" in a for a in about))

            box = format_box(["Pay rent"])
            self.assertIn("Pay rent", box)
            self.assertTrue(box.startswith("┌"))

    def test_creative_dashboard_hides_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "todos").mkdir(parents=True)
            (vault / "me" / ".private").mkdir(parents=True)
            (vault / "projects").mkdir(parents=True)
            (vault / "todos" / "TODO.md").write_text("- [ ] Build dash\n", encoding="utf-8")
            (vault / "me" / "about-me.md").write_text(
                "## Identity\n\n- Nova User\n", encoding="utf-8"
            )
            (vault / "me" / "preferences.md").write_text("", encoding="utf-8")
            (vault / "me" / "reminders.md").write_text(
                "- [ ] Ship plugin\n", encoding="utf-8"
            )
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|---|---|---|---|---|\n"
                "| t | api_key | k | SUPER_SECRET_ZZZ | t |\n",
                encoding="utf-8",
            )
            dash = render_creative_dashboard(vault, include_github=False)
            self.assertIn("AGENT VAULT", dash)
            self.assertIn("Nova User", dash)
            self.assertIn("Build dash", dash)
            self.assertIn("Ship plugin", dash)
            self.assertIn("SEALED KEYS", dash)
            self.assertNotIn("SUPER_SECRET_ZZZ", dash)
            self.assertTrue(dash.startswith("╔"))

    def test_vault_keys_script_hides_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "vault"
            data = Path(td) / "pdata"
            (vault / "me" / ".private").mkdir(parents=True)
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "## Entries\n\n"
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|------------|------|-------|-------|--------|\n"
                "| 2026-01-01T00:00:00Z | aws_key | aws_key | AKIA_SHOULD_NOT_PRINT | hook |\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            r = subprocess.run(
                [sys.executable, str(SCRIPTS / "vault_keys.py"), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertIn("aws_key", r.stdout)
            self.assertNotIn("AKIA_SHOULD_NOT_PRINT", r.stdout)

    def test_vault_status_creative(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "vault"
            data = Path(td) / "pdata"
            (vault / "todos").mkdir(parents=True)
            (vault / "me").mkdir(parents=True)
            (vault / "todos" / "TODO.md").write_text(
                "- [ ] Example todo\n", encoding="utf-8"
            )
            (vault / "me" / "reminders.md").write_text(
                "## Active\n\n- [ ] Call dentist\n", encoding="utf-8"
            )
            (vault / "me" / "about-me.md").write_text(
                "## Identity\n\n- Tom\n", encoding="utf-8"
            )
            (vault / "me" / "preferences.md").write_text("", encoding="utf-8")
            (vault / "me" / ".private").mkdir(parents=True)
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "## Entries\n\n"
                "| When (UTC) | Kind | Label | Value | Source |\n"
                "|------------|------|-------|-------|--------|\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            r = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "vault_status.py"),
                    "--vault",
                    str(vault),
                    "--no-github",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            out = r.stdout
            self.assertIn("AGENT VAULT", out)
            self.assertIn("Example todo", out)
            self.assertIn("Call dentist", out)
            self.assertIn("Tom", out)
            self.assertIn("/vaultkeys", out)

    def test_quiet_watcher(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "v"
            data = Path(td) / "d"
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            subprocess.run(
                [sys.executable, str(SCRIPTS / "ensure_vault.py"), "--vault", str(vault)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            key = "sk-" + ("w" * 24)
            r = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "quiet_watcher.py"),
                    "--vault",
                    str(vault),
                    "--text",
                    f"My name is Quiet Quinn. key={key}",
                    "--json",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertIn("secrets_added", r.stdout)
            self.assertNotIn(key, r.stdout)
            about = (vault / "me" / "about-me.md").read_text(encoding="utf-8")
            self.assertIn("Quiet Quinn", about)
            # activity log masked
            sessions = list((vault / "sessions").glob("activity-*.log"))
            self.assertTrue(sessions)
            log = sessions[0].read_text(encoding="utf-8")
            self.assertNotIn(key, log)

    def test_highlight_repo_filter(self) -> None:
        login = "Silly-Goose-duh"
        self.assertTrue(
            _is_highlight_repo(
                {
                    "name": "MakeYourPass",
                    "description": "Event OS campus",
                    "isFork": False,
                    "primaryLanguage": {"name": "TypeScript"},
                },
                login,
            )
        )
        self.assertFalse(
            _is_highlight_repo(
                {"name": "x", "description": "", "isFork": True, "primaryLanguage": None},
                login,
            )
        )


if __name__ == "__main__":
    unittest.main()
