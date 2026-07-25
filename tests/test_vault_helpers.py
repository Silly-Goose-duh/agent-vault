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
            self.assertEqual(keys[0]["kind"], "api_key")
            self.assertNotIn("SECRET_VALUE_NEVER", str(keys))

            about = parse_about_simple(vault)
            self.assertTrue(any("Alice Dev" in a for a in about))
            self.assertTrue(any("Prefer bullets" in a for a in about))
            self.assertFalse(any("(name, role)" in a for a in about))

            box = format_box(["Pay rent"])
            self.assertIn("Pay rent", box)
            self.assertTrue(box.startswith("┌"))

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

    def test_vault_status_sections(self) -> None:
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
            self.assertIn("## Todos", out)
            self.assertIn("Example todo", out)
            self.assertIn("## Reminders", out)
            self.assertIn("Call dentist", out)
            self.assertIn("## Personal info", out)
            self.assertIn("Tom", out)
            self.assertIn("/vaultkeys", out)

    def test_vault_cli_remember_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "v"
            data = Path(td) / "d"
            env = os.environ.copy()
            env["GROK_PLUGIN_ROOT"] = str(ROOT)
            env["GROK_PLUGIN_DATA"] = str(data)
            env["AGENT_VAULT_PATH"] = str(vault)
            r0 = subprocess.run(
                [sys.executable, str(SCRIPTS / "vault_cli.py"), "--vault", str(vault), "init"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r0.returncode, 0, r0.stderr + r0.stdout)
            r1 = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "vault_cli.py"),
                    "--vault",
                    str(vault),
                    "remember",
                    "--text",
                    "My name is Riley Fox.",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r1.returncode, 0, r1.stderr + r1.stdout)
            r2 = subprocess.run(
                [sys.executable, str(SCRIPTS / "vault_cli.py"), "--vault", str(vault), "context"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
            self.assertIn("Riley", r2.stdout)

    def test_preview_blocks_private(self) -> None:
        from preview_server import list_md_files, render_note  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me" / ".private").mkdir(parents=True)
            (vault / "me" / "about-me.md").write_text("hi", encoding="utf-8")
            (vault / "me" / ".private" / "secrets.local.md").write_text(
                "SECRET_SHOULD_NOT_LIST", encoding="utf-8"
            )
            files = list_md_files(vault)
            names = [p.name for p in files]
            self.assertIn("about-me.md", names)
            self.assertNotIn("secrets.local.md", names)
            html = render_note(vault, "me/.private/secrets.local.md")
            self.assertIn("Not found", html)
            self.assertNotIn("SECRET_SHOULD_NOT_LIST", html)

    def test_highlight_repo_filter(self) -> None:
        login = "Silly-Goose-duh"
        self.assertTrue(
            _is_highlight_repo(
                {
                    "name": "MakeYourPass",
                    "description": "Event OS",
                    "isFork": False,
                    "primaryLanguage": {"name": "TypeScript"},
                },
                login,
            )
        )
        self.assertFalse(
            _is_highlight_repo(
                {
                    "name": "Tribe-",
                    "description": "",
                    "isFork": True,
                    "primaryLanguage": {"name": "TS"},
                },
                login,
            )
        )
        self.assertFalse(
            _is_highlight_repo(
                {
                    "name": "Silly-Goose-duh",
                    "description": "Config files for my GitHub profile.",
                    "isFork": False,
                    "primaryLanguage": None,
                },
                login,
            )
        )
        self.assertFalse(
            _is_highlight_repo(
                {
                    "name": "skills-introduction-to-github",
                    "description": "My clone repository",
                    "isFork": False,
                    "primaryLanguage": None,
                },
                login,
            )
        )


if __name__ == "__main__":
    unittest.main()
