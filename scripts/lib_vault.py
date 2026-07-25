"""Shared helpers for vault path resolution, secrets location, and config.

Stdlib only. Works for Grok Build, Hermes, and any agent that shells out
to these scripts.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Plugin / data roots
# ---------------------------------------------------------------------------


def plugin_root() -> Path:
    for key in ("GROK_PLUGIN_ROOT", "AGENT_VAULT_ROOT", "HERMES_PLUGIN_ROOT"):
        env = os.environ.get(key)
        if env:
            return Path(env).expanduser().resolve()
    # scripts/ is one level under plugin root
    return Path(__file__).resolve().parent.parent


def plugin_data_dir() -> Path:
    for key in ("GROK_PLUGIN_DATA", "AGENT_VAULT_DATA", "HERMES_PLUGIN_DATA"):
        env = os.environ.get(key)
        if env:
            path = Path(env).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
    # Hermes home fallback (profile-safe)
    hermes = os.environ.get("HERMES_HOME")
    if hermes:
        path = Path(hermes).expanduser().resolve() / "agent-vault"
        path.mkdir(parents=True, exist_ok=True)
        return path
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    protect_path(path)


# ---------------------------------------------------------------------------
# Vault path
# ---------------------------------------------------------------------------


def default_vault_path() -> Path:
    # Prefer a neutral name; keep legacy "Grok Build" if it already exists.
    legacy = (Path.home() / "Grok Build").resolve()
    modern = (Path.home() / "AgentVault").resolve()
    if legacy.is_dir():
        return legacy
    return modern


def resolve_vault_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    for key in (
        "AGENT_VAULT_PATH",
        "GROK_VAULT_PATH",
        "HERMES_VAULT_PATH",
        "VAULT_PATH",
    ):
        env = os.environ.get(key)
        if env:
            return Path(env).expanduser().resolve()
    cfg = load_config()
    if cfg.get("vault_path"):
        return Path(cfg["vault_path"]).expanduser().resolve()
    return default_vault_path()


def template_dir() -> Path:
    root = plugin_root()
    for candidate in (root / "vault-template", root / "templates" / "vault"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"vault-template not found under {root}")


# ---------------------------------------------------------------------------
# Deep / protected secrets path
# ---------------------------------------------------------------------------


def secrets_relpath() -> Path:
    """Preferred deep location (hidden folder)."""
    return Path("me") / ".private" / "secrets.local.md"


def legacy_secrets_relpath() -> Path:
    return Path("me") / "secrets.local.md"


def secrets_file(vault: Path) -> Path:
    """Resolve secrets file: prefer deep path, fall back to legacy if present."""
    deep = vault / secrets_relpath()
    legacy = vault / legacy_secrets_relpath()
    if deep.is_file():
        return deep
    if legacy.is_file() and not deep.is_file():
        return legacy
    return deep


def migrate_secrets_to_deep(vault: Path) -> Path | None:
    """Move legacy me/secrets.local.md → me/.private/secrets.local.md once."""
    deep = vault / secrets_relpath()
    legacy = vault / legacy_secrets_relpath()
    if deep.is_file():
        protect_path(deep)
        return None
    if not legacy.is_file():
        return None
    deep.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(legacy), str(deep))
    except OSError:
        # copy+leave legacy if move fails (cross-device etc.)
        deep.write_text(legacy.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    protect_path(deep)
    # Leave a stub pointer at legacy path (no values)
    try:
        legacy.write_text(
            "# Moved\n\n"
            "Secrets now live at `me/.private/secrets.local.md` (gitignored, restricted).\n"
            "This stub contains **no** secret values.\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    return deep


def protect_path(path: Path) -> None:
    """Best-effort owner-only permissions (POSIX). No-op / soft on Windows."""
    try:
        if not path.exists():
            return
        if sys.platform.startswith("win"):
            # Windows ACL tightening is optional; disk encryption is the real layer.
            return
        mode = stat.S_IRUSR | stat.S_IWUSR  # 0o600
        if path.is_dir():
            mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR  # 0o700
        os.chmod(path, mode)
    except OSError:
        pass


def ensure_private_dir(vault: Path) -> Path:
    private = vault / "me" / ".private"
    private.mkdir(parents=True, exist_ok=True)
    protect_path(private)
    # Hide from casual listing / git
    gitkeep = private / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    ignore = private / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n!.gitignore\n!.gitkeep\n", encoding="utf-8")
    return private


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def list_open_todos(vault: Path) -> list[str]:
    """Return open todo item texts (without the checkbox prefix)."""
    items: list[str] = []
    for line in _read_lines(vault / "todos" / "TODO.md"):
        stripped = line.lstrip()
        if stripped.startswith("- [ ]"):
            text = stripped[len("- [ ]") :].strip()
            if text and not text.startswith("("):
                items.append(text)
    return items


def count_open_todos(vault: Path) -> int:
    return len(list_open_todos(vault))


def _secret_data_rows(vault: Path) -> list[list[str]]:
    """Parse data rows from secrets table. Cells: When, Kind, Label, Value, Source."""
    rows: list[list[str]] = []
    path = secrets_file(vault)
    for line in _read_lines(path):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "When (UTC)" in stripped or stripped.startswith("|---"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 4 and cells[0] and cells[0] != "When (UTC)":
            rows.append(cells)
    return rows


def count_secret_rows(vault: Path) -> int:
    return len(_secret_data_rows(vault))


def list_secret_keys(vault: Path) -> list[dict[str, str]]:
    """Metadata only — never includes the secret Value column."""
    out: list[dict[str, str]] = []
    for cells in _secret_data_rows(vault):
        when = cells[0] if len(cells) > 0 else ""
        kind = cells[1] if len(cells) > 1 else ""
        label = cells[2] if len(cells) > 2 else ""
        source = cells[4] if len(cells) > 4 else ""
        out.append({"when": when, "kind": kind, "label": label, "source": source})
    return out


def parse_about_simple(vault: Path) -> list[str]:
    """Non-placeholder bullets from about-me.md and preferences.md."""
    facts: list[str] = []
    for rel in ("me/about-me.md", "me/preferences.md"):
        section = ""
        for line in _read_lines(vault / rel):
            stripped = line.strip()
            if stripped.startswith("#"):
                section = stripped.lstrip("#").strip()
                continue
            if not stripped.startswith("- "):
                continue
            body = stripped[2:].strip()
            if not body or body.startswith("("):
                continue
            if section:
                facts.append(f"{section}: {body}")
            else:
                facts.append(body)
    return facts


def list_reminders(vault: Path) -> list[str]:
    """Open reminder bullets from me/reminders.md."""
    path = vault / "me" / "reminders.md"
    items: list[str] = []
    for line in _read_lines(path):
        stripped = line.lstrip()
        if stripped.startswith("- [ ]"):
            text = stripped[len("- [ ]") :].strip()
            if text and not text.startswith("("):
                items.append(text)
        elif stripped.startswith("- ") and not stripped.startswith("- [x]"):
            text = stripped[2:].strip()
            if text and not text.startswith("(") and text not in {"…", "-", ""}:
                items.append(text)
    return items


def format_box(lines: list[str], min_width: int = 40) -> str:
    """ASCII box for reminder notes."""
    if not lines:
        lines = ["(no reminders yet — tell me what to remember)"]
    width = max(min_width, max(len(ln) for ln in lines) + 2)
    top = "┌" + "─" * width + "┐"
    bot = "└" + "─" * width + "┘"
    body = [f"│ {ln.ljust(width - 1)}│" for ln in lines]
    return "\n".join([top, *body, bot])


def brief_context_for_agent(vault: Path, max_facts: int = 12) -> str:
    """Compact non-secret context string to inject into agent turns."""
    if not vault.is_dir():
        return ""
    parts: list[str] = [f"[agent-vault] path={vault}"]
    about = parse_about_simple(vault)[:max_facts]
    if about:
        parts.append("Personal facts:")
        parts.extend(f"- {a}" for a in about)
    todos = list_open_todos(vault)[:8]
    if todos:
        parts.append("Open todos:")
        parts.extend(f"- [ ] {t}" for t in todos)
    rems = list_reminders(vault)[:6]
    if rems:
        parts.append("Reminders:")
        parts.extend(f"- {r}" for r in rems)
    n = count_secret_rows(vault)
    if n:
        parts.append(f"Secrets stored: {n} (values never injected; use vault keys list)")
    if len(parts) == 1:
        return parts[0] + " (empty — capture facts as the user shares them)"
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# GitHub highlights (optional dashboard)
# ---------------------------------------------------------------------------


_GITHUB_SKIP_NAMES = frozenset(
    {
        "skills-introduction-to-github",
        "developer-roadmap",
        "React-stuffss",
        "Leetcode",
        "Leet-code",
        "portfolio-template",
        "fossmce-portfolios",
        "Odin-project",
        "Blog.github.io",
        "blog-claude.github.io",
        "figma-plugin-dev-intro",
    }
)
_GITHUB_SKIP_DESC_PREFIXES = (
    "my clone repository",
    "config files for my github profile",
    "just some solutions",
)


def _is_highlight_repo(item: dict[str, Any], login: str | None) -> bool:
    """Original, intentional projects — not forks, clones, or profile shells."""
    name = str(item.get("name") or "")
    if not name:
        return False
    if item.get("isFork"):
        return False
    if login and name.lower() == login.lower():
        return False
    if name in _GITHUB_SKIP_NAMES:
        return False
    desc = (item.get("description") or "").strip()
    low = desc.lower()
    if any(low.startswith(p) for p in _GITHUB_SKIP_DESC_PREFIXES):
        return False
    lang = item.get("primaryLanguage")
    has_lang = bool(lang and (lang.get("name") if isinstance(lang, dict) else lang))
    if len(desc) >= 20:
        return True
    if has_lang and len(desc) >= 8:
        return True
    if has_lang and not desc:
        return True
    return False


def list_github_repos(limit: int = 50, highlight_limit: int = 6) -> list[str]:
    """Best/highlight repo names only via `gh` (not the full dump)."""
    gh = shutil.which("gh")
    if not gh:
        return []
    try:
        r = subprocess.run(
            [
                gh,
                "repo",
                "list",
                "--limit",
                str(limit),
                "--json",
                "name,description,isFork,stargazerCount,updatedAt,primaryLanguage,owner",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if r.returncode != 0 or not r.stdout.strip():
        return []
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []

    login: str | None = None
    if data and isinstance(data[0], dict):
        owner = data[0].get("owner")
        if isinstance(owner, dict):
            login = owner.get("login")

    candidates: list[tuple[int, str, str]] = []
    for item in data:
        if not isinstance(item, dict) or not _is_highlight_repo(item, login):
            continue
        name = str(item["name"])
        desc = (item.get("description") or "").strip()
        stars = int(item.get("stargazerCount") or 0)
        updated = str(item.get("updatedAt") or "")
        recency = 0
        if len(updated) >= 7:
            try:
                year = int(updated[0:4])
                month = int(updated[5:7])
                recency = year * 12 + month
            except ValueError:
                recency = 0
        score = recency * 50 + stars * 20 + (150 if len(desc) >= 20 else 0) + min(len(desc), 40)
        candidates.append((score, updated, name))

    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [name for _, _, name in candidates[: max(1, highlight_limit)]]
