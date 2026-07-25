#!/usr/bin/env python3
"""Unit tests for auto_capture (stdlib unittest)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import auto_capture  # noqa: E402
from lib_vault import secrets_file  # noqa: E402


class AutoCaptureTests(unittest.TestCase):
    def test_find_api_key(self) -> None:
        # Realistic shape (length) without looking like a live production key pattern in CI logs
        fake = "sk-" + ("a" * 20) + "TESTONLY"
        text = f"here is my key {fake}"
        found = auto_capture.find_secrets(text)
        self.assertTrue(any(v.startswith("sk-") for _, _, v in found))

    def test_mask(self) -> None:
        self.assertIn("****", auto_capture.mask_secret("sk-abcdefghijklmnop"))

    def test_append_secret_dedupe_deep_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me" / ".private").mkdir(parents=True)
            secrets = vault / "me" / ".private" / "secrets.local.md"
            val = "sk-" + ("b" * 24)
            ok1 = auto_capture.append_secret(secrets, "api_key", "api_key", val, "test")
            ok2 = auto_capture.append_secret(secrets, "api_key", "api_key", val, "test")
            self.assertTrue(ok1)
            self.assertFalse(ok2)
            body = secrets.read_text(encoding="utf-8")
            self.assertEqual(body.count(val), 1)

    def test_process_text_writes_deep_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me").mkdir()
            val = "ghp_" + ("C" * 36)
            result = auto_capture.process_text(
                f"token {val} and my name is Casey Quinn.",
                vault,
                "test",
            )
            self.assertTrue(result["secrets_added"])
            self.assertTrue(result["personal_added"])
            deep = secrets_file(vault)
            self.assertTrue(deep.is_file())
            self.assertIn(".private", deep.parts)
            self.assertIn(val, deep.read_text(encoding="utf-8"))
            about = (vault / "me" / "about-me.md").read_text(encoding="utf-8")
            self.assertIn("Casey", about)

    def test_personal_name(self) -> None:
        items = auto_capture.find_personal("Hi, my name is Alex Rivera. Thanks.")
        self.assertTrue(any(k == "name" and "Alex" in v for k, v in items))

    def test_process_text_about_me(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me").mkdir()
            result = auto_capture.process_text(
                "My name is Sam. I prefer short answers.",
                vault,
                "test",
            )
            self.assertTrue(result["personal_added"])
            about = (vault / "me" / "about-me.md").read_text(encoding="utf-8")
            self.assertIn("Sam", about)

    def test_skip_placeholder_secrets(self) -> None:
        found = auto_capture.find_secrets("use sk-example-not-real-value-here-xx")
        # may or may not match length; must not keep if contains example
        for _, _, v in found:
            self.assertNotIn("example", v.lower())


if __name__ == "__main__":
    unittest.main()
