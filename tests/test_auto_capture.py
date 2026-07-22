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


class AutoCaptureTests(unittest.TestCase):
    def test_find_api_key(self) -> None:
        text = "here is my key sk-abcdefghijklmnopqrstuvwxyz123456"
        found = auto_capture.find_secrets(text)
        self.assertTrue(any(v.startswith("sk-") for _, _, v in found))

    def test_mask(self) -> None:
        self.assertIn("****", auto_capture.mask_secret("sk-abcdefghijklmnop"))

    def test_append_secret_dedupe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "me").mkdir()
            secrets = vault / "me" / "secrets.local.md"
            ok1 = auto_capture.append_secret(secrets, "api_key", "api_key", "sk-test-unique-value-001", "test")
            ok2 = auto_capture.append_secret(secrets, "api_key", "api_key", "sk-test-unique-value-001", "test")
            self.assertTrue(ok1)
            self.assertFalse(ok2)
            body = secrets.read_text(encoding="utf-8")
            self.assertEqual(body.count("sk-test-unique-value-001"), 1)

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


if __name__ == "__main__":
    unittest.main()
