"""Shared helpers for vault path resolution, secrets, dashboard data.

Stdlib only. Obsidian-free plain markdown vault for any coding agent.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def plugin_root() -> Path:
    for key in ("GROK_PLUGIN_ROOT", "AGENT_VAULT_ROOT", "HERMES_PLUGIN_ROOT"):
        env = os.environ.get(key)
        if env:
            return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def plugin_data_dir() -> Path:
    for key in ("GROK_PLUGIN_DATA", "AGENT_VAULT_DATA", "HERMES_PLUGIN_DATA"):
        env = os.environ.get(key)
        if env:
            path = Path(env).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
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


def default_vault_path() -> Path:
    # Prefer AgentVault; keep legacy folder if already created.
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


def secrets_relpath() -> Path:
    return Path("me") / ".private" / "secrets.local.md"


def legacy_secrets_relpath() -> Path:
    return Path("me") / "secrets.local.md"


def secrets_file(vault: Path) -> Path:
    deep = vault / secrets_relpath()
    legacy = vault / legacy_secrets_relpath()
    if deep.is_file():
        return deep
    if legacy.is_file() and not deep.is_file():
        return legacy
    return deep


def migrate_secrets_to_deep(vault: Path) -> Path | None:
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
        deep.write_text(legacy.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    protect_path(deep)
    try:
        legacy.write_text(
            "# Moved\n\n"
            "Secrets now live at `me/.private/secrets.local.md` (local only).\n"
            "This stub contains **no** secret values.\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    return deep


def protect_path(path: Path) -> None:
    try:
        if not path.exists():
            return
        if sys.platform.startswith("win"):
            return
        mode = stat.S_IRUSR | stat.S_IWUSR
        if path.is_dir():
            mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        os.chmod(path, mode)
    except OSError:
        pass


def ensure_private_dir(vault: Path) -> Path:
    private = vault / "me" / ".private"
    private.mkdir(parents=True, exist_ok=True)
    protect_path(private)
    gitkeep = private / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    ignore = private / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n!.gitignore\n!.gitkeep\n", encoding="utf-8")
    return private


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def list_open_todos(vault: Path) -> list[str]:
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
    rows: list[list[str]] = []
    path = secrets_file(vault)
    for line in _read_lines(path):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "When (UTC)" in stripped or stripped.startswith("|---") or stripped.startswith("|---"):
            continue
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 4 and cells[0] and cells[0] != "When (UTC)":
            rows.append(cells)
    return rows


def count_secret_rows(vault: Path) -> int:
    return len(_secret_data_rows(vault))


def list_secret_keys(vault: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for cells in _secret_data_rows(vault):
        out.append(
            {
                "when": cells[0] if len(cells) > 0 else "",
                "kind": cells[1] if len(cells) > 1 else "",
                "label": cells[2] if len(cells) > 2 else "",
                "source": cells[4] if len(cells) > 4 else "",
            }
        )
    return out


def parse_about_simple(vault: Path) -> list[str]:
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
            facts.append(f"{section}: {body}" if section else body)
    return facts


def list_reminders(vault: Path) -> list[str]:
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


def list_projects(vault: Path, limit: int = 12) -> list[str]:
    """Project names from projects/_index.md table + note titles."""
    names: list[str] = []
    seen: set[str] = set()
    index = vault / "projects" / "_index.md"
    for line in _read_lines(index):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "Project" in stripped and "Status" in stripped:
            continue
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        name = cells[0]
        if not name or name.startswith("(") or name.lower() == "project":
            continue
        low = name.lower()
        if low in seen:
            continue
        seen.add(low)
        status = cells[1] if len(cells) > 1 else ""
        names.append(f"{name}" + (f" · {status}" if status else ""))
    proj_dir = vault / "projects"
    if proj_dir.is_dir():
        for p in sorted(proj_dir.glob("*.md")):
            if p.name.startswith("_"):
                continue
            title = p.stem.replace("-", " ").replace("_", " ").strip()
            if title.lower() in seen:
                continue
            seen.add(title.lower())
            names.append(title)
    return names[:limit]


def format_box(lines: list[str], min_width: int = 40) -> str:
    if not lines:
        lines = ["(empty)"]
    width = max(min_width, max(len(ln) for ln in lines) + 2)
    top = "┌" + "─" * width + "┐"
    bot = "└" + "─" * width + "┘"
    body = [f"│ {ln.ljust(width - 1)}│" for ln in lines]
    return "\n".join([top, *body, bot])


def append_activity(vault: Path, kind: str, summary: str) -> None:
    """Append one quiet activity line (no secret values)."""
    sessions = vault / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = sessions / f"activity-{day}.log"
    when = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
    safe = summary.replace("\n", " ").strip()[:160]
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{when}\t{kind}\t{safe}\n")


def recent_activity(vault: Path, limit: int = 8) -> list[str]:
    sessions = vault / "sessions"
    if not sessions.is_dir():
        return []
    files = sorted(sessions.glob("activity-*.log"), reverse=True)
    lines: list[str] = []
    for fp in files:
        for line in reversed(_read_lines(fp)):
            if not line.strip():
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 3:
                lines.append(f"{parts[0]} · {parts[1]} · {parts[2]}")
            else:
                lines.append(line.strip())
            if len(lines) >= limit:
                return lines
    return lines


def brief_context_for_agent(vault: Path, max_facts: int = 12) -> str:
    if not vault.is_dir():
        return ""
    parts: list[str] = [
        "[agent-vault] Quiet personal memory is ON. "
        f"path={vault}. Never print secret values."
    ]
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
    projs = list_projects(vault, limit=6)
    if projs:
        parts.append("Projects:")
        parts.extend(f"- {p}" for p in projs)
    n = count_secret_rows(vault)
    if n:
        parts.append(f"Sealed keys stored: {n} (values never injected; /vaultkeys for labels)")
    if len(parts) == 1:
        return parts[0] + " Vault empty — capture durable facts silently as user shares them."
    return "\n".join(parts)


def _is_highlight_repo(item: dict[str, Any], login: str | None) -> bool:
    name = str(item.get("name") or "")
    if not name or item.get("isFork"):
        return False
    if login and name.lower() == login.lower():
        return False
    skip = {
        "skills-introduction-to-github",
        "developer-roadmap",
        "portfolio-template",
        "Leetcode",
        "Leet-code",
    }
    if name in skip:
        return False
    desc = (item.get("description") or "").strip()
    low = desc.lower()
    if low.startswith(("my clone repository", "config files for my github profile")):
        return False
    lang = item.get("primaryLanguage")
    has_lang = bool(lang and (lang.get("name") if isinstance(lang, dict) else lang))
    if len(desc) >= 20 or (has_lang and len(desc) >= 8) or (has_lang and not desc):
        return True
    return False


def list_github_repos(limit: int = 50, highlight_limit: int = 6) -> list[str]:
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
    login = None
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
                recency = int(updated[0:4]) * 12 + int(updated[5:7])
            except ValueError:
                recency = 0
        score = recency * 50 + stars * 20 + (150 if len(desc) >= 20 else 0)
        candidates.append((score, updated, name))
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [n for _, _, n in candidates[: max(1, highlight_limit)]]


def render_creative_dashboard(
    vault: Path,
    *,
    include_github: bool = True,
) -> str:
    """Full creative /vault dashboard text (never includes secret values)."""
    todos = list_open_todos(vault)
    about = parse_about_simple(vault)
    reminders = list_reminders(vault)
    projects = list_projects(vault)
    keys_n = count_secret_rows(vault)
    activity = recent_activity(vault, limit=6)
    gh = list_github_repos() if include_github else []
    sec = secrets_file(vault)

    W = 58

    def rule(ch: str = "═") -> str:
        return ch * W

    def row(text: str) -> str:
        t = text[: W - 2]
        return "║ " + t.ljust(W - 2) + "║"

    def blank() -> str:
        return "║" + " " * W + "║"

    def section(title: str) -> list[str]:
        return [row(f"▸ {title}"), row("─" * (W - 4))]

    sealed = "●" * min(keys_n, 8) + ("○" * max(0, 4 - keys_n) if keys_n < 4 else "")
    if keys_n == 0:
        sealed = "○○○○"

    lines = [
        "╔" + rule() + "╗",
        row("◆  AGENT VAULT"),
        row("quiet memory · local · locked"),
        "╠" + rule() + "╣",
        row(f"path  {vault}"),
        row(f"seal  {sec.name}  (values never shown)"),
        blank(),
    ]
    lines += section("YOU")
    if about:
        for a in about[:10]:
            lines.append(row(f"· {a}"))
    else:
        lines.append(row("· (nothing yet — keep chatting normally)"))
    lines.append(blank())
    lines += section(f"TODOS  ({len(todos)} open)")
    if todos:
        for t in todos[:8]:
            lines.append(row(f"☐  {t}"))
        if len(todos) > 8:
            lines.append(row(f"… +{len(todos) - 8} more"))
    else:
        lines.append(row("☐  (inbox zero)"))
    lines.append(blank())
    lines += section(f"REMINDERS  ({len(reminders)})")
    if reminders:
        for r in reminders[:6]:
            lines.append(row(f"✧  {r}"))
    else:
        lines.append(row("✧  (none)"))
    lines.append(blank())
    lines += section(f"PROJECTS  ({len(projects)})")
    if projects:
        for p in projects[:8]:
            lines.append(row(f"◈  {p}"))
    else:
        lines.append(row("◈  (none indexed)"))
    lines.append(blank())
    if include_github:
        lines += section("GITHUB HIGHLIGHTS")
        if gh:
            for name in gh:
                lines.append(row(f"⌥  {name}"))
        else:
            lines.append(row("⌥  (gh unavailable or none)"))
        lines.append(blank())
    lines += section(f"SEALED KEYS  {sealed}  {keys_n}")
    lines.append(row("labels only via /vaultkeys — never values here"))
    lines.append(blank())
    lines += section("RECENT CAPTURES")
    if activity:
        for a in activity:
            lines.append(row(f"· {a}"))
    else:
        lines.append(row("· (watcher idle — no captures yet)"))
    lines.append(blank())
    lines.append(row("cmds  /vaultkeys  /vault-remember  /vault-todo  /vault-preview"))
    lines.append(row("tip   just work — the quiet watcher saves durable details"))
    lines.append("╚" + rule() + "╝")
    return "\n".join(lines)
