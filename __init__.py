"""Hermes plugin: personal agent vault with auto-capture + slash commands.

Shares the same markdown vault and Python scripts used by the Grok Build
plugin surface in this repo. Install:

    hermes plugins install Silly-Goose-duh/grok-build-obsidian-plugin --enable

Hooks:
  - on_session_start → ensure vault exists
  - pre_llm_call    → scan user message for facts/secrets; inject brief non-secret context on first turn
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent
_SCRIPTS = _PLUGIN_DIR / "scripts"

# Make scripts importable
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def _import_lib():
    import auto_capture  # type: ignore
    import lib_vault  # type: ignore

    return lib_vault, auto_capture


def _ensure_vault() -> Path:
    lib_vault, _ = _import_lib()
    vault = lib_vault.resolve_vault_path()
    ensure = _SCRIPTS / "ensure_vault.py"
    if not vault.is_dir() or not (vault / "me").is_dir():
        try:
            subprocess.run(
                [sys.executable, str(ensure), "--vault", str(vault)],
                check=False,
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            logger.debug("ensure_vault failed: %s", exc)
    return lib_vault.resolve_vault_path()


def _on_session_start(**_: Any) -> None:
    try:
        _ensure_vault()
    except Exception as exc:
        logger.debug("agent-vault session start: %s", exc)


def _on_pre_llm_call(
    user_message: str = "",
    is_first_turn: bool = False,
    **_: Any,
) -> Optional[dict]:
    """Capture from user text; inject brief vault context on first turn only."""
    context_out = ""
    try:
        lib_vault, auto_capture = _import_lib()
        vault = _ensure_vault()
        text = user_message if isinstance(user_message, str) else ""
        if text.strip():
            # Fail-open capture
            try:
                auto_capture.process_text(text, vault, source="hermes:pre_llm")
            except Exception as exc:
                logger.debug("auto_capture failed: %s", exc)
        if is_first_turn:
            try:
                context_out = lib_vault.brief_context_for_agent(vault)
            except Exception as exc:
                logger.debug("brief_context failed: %s", exc)
    except Exception as exc:
        logger.debug("pre_llm_call vault hook failed: %s", exc)
        return None

    if context_out:
        return {"context": context_out}
    return None


def _run_script(name: str, extra: list[str] | None = None) -> str:
    cmd = [sys.executable, str(_SCRIPTS / name)]
    if extra:
        cmd.extend(extra)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except Exception as exc:
        return f"[agent-vault] failed to run {name}: {exc}"
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0 and err:
        return out + ("\n" + err if out else err)
    return out or err or f"[agent-vault] {name} ok"


def _slash_vault(raw_args: str) -> Optional[str]:
    args = raw_args.strip().split()
    if not args or args[0] in {"status", "dash", "dashboard"}:
        _ensure_vault()
        return _run_script("vault_status.py", ["--no-github"] if "--no-github" in args else [])
    sub = args[0]
    if sub in {"init", "repair"}:
        return _run_script("ensure_vault.py")
    if sub in {"keys", "key"}:
        return _run_script("vault_keys.py")
    if sub == "path":
        lib_vault, _ = _import_lib()
        return str(lib_vault.resolve_vault_path())
    if sub == "context":
        return _run_script("vault_cli.py", ["context"])
    if sub == "remember":
        text = " ".join(args[1:]).strip()
        if not text:
            return "Usage: /vault remember <fact or secret text>"
        return _run_script("vault_cli.py", ["remember", "--text", text])
    if sub == "capture":
        text = " ".join(args[1:]).strip()
        if not text:
            return "Usage: /vault capture <text>"
        return _run_script("auto_capture.py", ["--text", text, "--source", "hermes:/vault"])
    if sub in {"help", "-h", "--help"}:
        return _HELP
    return f"Unknown subcommand: {sub}\n\n{_HELP}"


_HELP = """\
/vault — personal agent vault

Subcommands:
  (none)|status   Dashboard (todos, reminders, personal facts, key count)
  init            Create / repair vault on disk
  keys            List key labels only (never values)
  path            Print vault path
  context         Non-secret brief used by the agent
  remember <text> Save fact / auto-detect secret
  capture <text>  Force heuristic scan

Also: /vaultkeys (alias for keys)

Vault is Obsidian-compatible markdown. Secrets live in me/.private/ (gitignored).
"""


def _slash_vaultkeys(raw_args: str) -> Optional[str]:
    return _run_script("vault_keys.py")


def register(ctx) -> None:
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_command(
        "vault",
        handler=_slash_vault,
        description="Personal vault dashboard, capture, and keys (values never shown).",
    )
    ctx.register_command(
        "vaultkeys",
        handler=_slash_vaultkeys,
        description="List stored vault key labels only (never values).",
    )
