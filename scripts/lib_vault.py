"""Shared helpers for vault path resolution and config (stdlib only)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def plugin_root() -> Path:
    env = os.environ.get("GROK_PLUGIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def plugin_data_dir() -> Path:
    env = os.environ.get("GROK_PLUGIN_DATA")
    if env:
        path = Path(env).expanduser().resolve()
    else:
        path = plugin_root() / "plugin-data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return plugin_data_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def default_vault_path() -> Path:
    return (Path.home() / "Grok Build").resolve()


def resolve_vault_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    env = os.environ.get("GROK_VAULT_PATH")
    if env:
        return Path(env).expanduser().resolve()
    cfg = load_config()
    if cfg.get("vault_path"):
        return Path(cfg["vault_path"]).expanduser().resolve()
    return default_vault_path()


def template_dir() -> Path:
    root = plugin_root()
    candidate = root / "vault-template"
    if candidate.is_dir():
        return candidate
    # Installed layout fallback
    alt = root / "templates" / "vault"
    if alt.is_dir():
        return alt
    raise FileNotFoundError(f"vault-template not found under {root}")


def count_open_todos(vault: Path) -> int:
    todo = vault / "todos" / "TODO.md"
    if not todo.is_file():
        return 0
    n = 0
    for line in todo.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- [ ]"):
            n += 1
    return n


def count_secret_rows(vault: Path) -> int:
    secrets = vault / "me" / "secrets.local.md"
    if not secrets.is_file():
        return 0
    n = 0
    for line in secrets.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("|") and "When (UTC)" not in line and not line.strip().startswith("|---"):
            # data row with at least kind/value cells
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0] and cells[0] != "When (UTC)":
                n += 1
    return n
