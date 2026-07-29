"""Hermes plugin: Agent Vault — quiet personal memory for coding agents.

    hermes plugins install Silly-Goose-duh/agent-vault --enable

Hooks:
  - on_session_start → ensure vault
  - pre_llm_call    → quiet watcher + first-turn non-secret context

Slash:
  - /vault, /avault  → dashboard (in-process; never empty)
  - /vaultkeys       → key labels only
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

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def _import_lib():
    import auto_capture  # type: ignore
    import lib_vault  # type: ignore
    import quiet_watcher  # type: ignore

    return lib_vault, auto_capture, quiet_watcher


def _ensure_vault() -> Path:
    lib_vault, _, _ = _import_lib()
    vault = lib_vault.resolve_vault_path()
    if vault.is_dir() and (vault / "me").is_dir():
        return vault
    ensure = _SCRIPTS / "ensure_vault.py"
    try:
        # Prefer in-process ensure if importable
        from ensure_vault import main as _ensure_main  # type: ignore

        old = sys.argv[:]
        try:
            sys.argv = ["ensure_vault.py", "--vault", str(vault)]
            _ensure_main()
        finally:
            sys.argv = old
    except Exception:
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
    context_out = ""
    try:
        lib_vault, _ac, quiet_watcher = _import_lib()
        vault = _ensure_vault()
        text = user_message if isinstance(user_message, str) else ""
        if text.strip():
            try:
                quiet_watcher.watch(text, vault, source="hermes:pre_llm")
            except Exception as exc:
                logger.debug("quiet_watcher failed: %s", exc)
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


def _dashboard(include_github: bool = False) -> str:
    """Always return a visible dashboard string (in-process first)."""
    try:
        lib_vault, _, _ = _import_lib()
        vault = _ensure_vault()
        if not vault.is_dir():
            return (
                "Agent Vault is not initialized yet.\n"
                f"Expected path: {vault}\n"
                "Run: /vault init"
            )
        try:
            body = lib_vault.render_creative_dashboard(
                vault, include_github=include_github
            )
        except Exception as exc:
            logger.exception("render_creative_dashboard failed")
            # plain fallback
            about = lib_vault.parse_about_simple(vault)
            todos = lib_vault.list_open_todos(vault)
            keys = lib_vault.count_secret_rows(vault)
            lines = [
                "AGENT VAULT",
                f"path: {vault}",
                "",
                "YOU:",
                *([f"- {a}" for a in about] or ["- (empty)"]),
                "",
                f"TODOS ({len(todos)}):",
                *([f"- [ ] {t}" for t in todos] or ["- (none)"]),
                "",
                f"SEALED KEYS: {keys}  (use /vaultkeys for labels)",
                f"(render error: {exc})",
            ]
            body = "\n".join(lines)
        # Desktop-safe: prefix with plain header so something always shows
        # even if box-drawing fonts fail.
        header = (
            "AGENT VAULT\n"
            f"path: {vault}\n"
            "---\n"
        )
        out = f"{header}{body}\n---\ncmds: /vaultkeys · /vault remember <text> · /vault init"
        return out if out.strip() else "Agent Vault: (empty dashboard — try /vault init)"
    except Exception as exc:
        logger.exception("/vault failed")
        return f"Agent Vault error: {exc}\nTry: hermes plugins install Silly-Goose-duh/agent-vault --force --enable"


def _keys() -> str:
    try:
        lib_vault, _, _ = _import_lib()
        vault = _ensure_vault()
        keys = lib_vault.list_secret_keys(vault)
        lines = [
            "AGENT VAULT KEYS (values never shown)",
            f"path: {vault}",
            f"count: {len(keys)}",
            "",
        ]
        if not keys:
            lines.append("(no keys yet — paste a secret in chat or /vault remember --kind secret …)")
        else:
            lines.append(f"{'When':<22} {'Kind':<14} {'Label':<24} Source")
            lines.append("-" * 72)
            for k in keys:
                lines.append(
                    f"{k.get('when',''):<22} {k.get('kind',''):<14} "
                    f"{k.get('label',''):<24} {k.get('source','')}"
                )
        return "\n".join(lines)
    except Exception as exc:
        return f"Agent Vault keys error: {exc}"


def _slash_vault(raw_args: str) -> str:
    """Never return None — desktop shows blank for empty/None."""
    args = (raw_args or "").strip().split()
    if not args or args[0] in {"status", "dash", "dashboard", "show"}:
        return _dashboard(include_github="--github" in args)
    sub = args[0].lower()
    if sub in {"init", "repair"}:
        try:
            vault = _ensure_vault()
            return f"Vault ready: {vault}\n\n" + _dashboard(include_github=False)
        except Exception as exc:
            return f"Vault init failed: {exc}"
    if sub in {"keys", "key"}:
        return _keys()
    if sub == "path":
        try:
            lib_vault, _, _ = _import_lib()
            return f"Vault path: {lib_vault.resolve_vault_path()}"
        except Exception as exc:
            return f"path error: {exc}"
    if sub == "context":
        try:
            lib_vault, _, _ = _import_lib()
            return lib_vault.brief_context_for_agent(_ensure_vault()) or "(empty context)"
        except Exception as exc:
            return f"context error: {exc}"
    if sub == "remember":
        text = " ".join(args[1:]).strip()
        if not text:
            return "Usage: /vault remember <fact or secret text>"
        try:
            lib_vault, auto_capture, quiet_watcher = _import_lib()
            vault = _ensure_vault()
            out = quiet_watcher.watch(text, vault, source="hermes:/vault")
            if out.get("summary") and out.get("summary") != "noop":
                return f"Saved.\n{out.get('summary')}\n\n" + _dashboard(False)
            # force note
            auto_capture.append_personal(vault / "me" / "about-me.md", "note", text)
            return f"Saved note to about-me.\n\n" + _dashboard(False)
        except Exception as exc:
            return f"remember failed: {exc}"
    if sub == "watch":
        text = " ".join(args[1:]).strip()
        if not text:
            return "Usage: /vault watch <text>"
        try:
            _lv, _ac, quiet_watcher = _import_lib()
            out = quiet_watcher.watch(text, _ensure_vault(), source="hermes:/vault-watch")
            return f"watcher: {out.get('summary', out)}"
        except Exception as exc:
            return f"watch failed: {exc}"
    if sub in {"help", "-h", "--help"}:
        return _HELP
    return f"Unknown subcommand: {sub}\n\n{_HELP}"


_HELP = """\
/vault — Agent Vault (quiet personal memory)

  /vault              Creative dashboard
  /vault init         Create / repair vault
  /vault keys         Key labels only
  /vault path         Print vault path
  /vault context      Non-secret brief
  /vault remember …   Save fact/secret
  /avault             Same as /vault

Secrets stay in me/.private/ and are never printed.
"""


def _slash_vaultkeys(raw_args: str) -> str:
    return _keys()


def register(ctx) -> None:
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    # Primary + alias (desktop sometimes flaky on first name only)
    for name in ("vault", "avault"):
        ctx.register_command(
            name,
            handler=_slash_vault,
            description="Agent Vault dashboard + quiet memory controls.",
        )
    ctx.register_command(
        "vaultkeys",
        handler=_slash_vaultkeys,
        description="List sealed key labels only (never values).",
    )
