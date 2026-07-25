#!/usr/bin/env python3
"""Minimal local markdown vault browser (stdlib only)."""

from __future__ import annotations

import argparse
import html
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_vault import resolve_vault_path  # noqa: E402


def list_md_files(vault: Path) -> list[Path]:
    files: list[Path] = []
    for p in vault.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".markdown", ".txt"}:
            continue
        if "secrets.local" in p.name.lower():
            continue  # never serve secrets over HTTP
        rel_parts = p.relative_to(vault).parts
        if ".private" in rel_parts or ".obsidian" in rel_parts:
            continue  # deep private dir + Obsidian config never served
        if any(part.startswith(".") for part in rel_parts if part != "."):
            continue
        files.append(p)
    return sorted(files, key=lambda x: str(x).lower())


def render_index(vault: Path) -> str:
    items = []
    for f in list_md_files(vault):
        rel = f.relative_to(vault).as_posix()
        items.append(f'<li><a href="/note?path={html.escape(rel)}">{html.escape(rel)}</a></li>')
    body = "\n".join(items) or "<li><em>No notes yet</em></li>"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Agent Vault · local</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;background:#0f1115;color:#e6e6e6}}
a{{color:#7cb7ff}} h1{{font-size:1.4rem}} pre{{white-space:pre-wrap;background:#1a1d24;padding:1rem;border-radius:8px}}
.muted{{color:#999;font-size:0.9rem}}
</style></head>
<body>
<h1>Personal Agent Vault</h1>
<p class="muted">{html.escape(str(vault))}</p>
<p class="muted">Secrets and <code>me/.private/</code> are never served.</p>
<ul>{body}</ul>
</body></html>"""


def render_note(vault: Path, rel: str) -> str:
    path = (vault / rel).resolve()
    try:
        path.relative_to(vault.resolve())
    except ValueError:
        return "<h1>Forbidden</h1>"
    if not path.is_file() or "secrets.local" in path.name.lower() or ".private" in path.parts:
        return "<h1>Not found</h1>"
    text = path.read_text(encoding="utf-8", errors="replace")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(rel)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;background:#0f1115;color:#e6e6e6}}
a{{color:#7cb7ff}} pre{{white-space:pre-wrap;background:#1a1d24;padding:1rem;border-radius:8px}}
</style></head>
<body>
<p><a href="/">&larr; Back</a></p>
<h1>{html.escape(rel)}</h1>
<pre>{html.escape(text)}</pre>
</body></html>"""


def make_handler(vault: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            return  # quiet

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                body = render_index(vault).encode("utf-8")
            elif parsed.path == "/note":
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query)
                rel = unquote(qs.get("path", [""])[0])
                body = render_note(vault, rel).encode("utf-8")
            elif parsed.path == "/health":
                body = b"ok"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault preview HTTP server")
    parser.add_argument("--vault", help="Override vault path")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open browser")
    parser.add_argument("--once", action="store_true", help="Print URL and keep running in foreground")
    args = parser.parse_args()

    vault = resolve_vault_path(args.vault)
    if not vault.is_dir():
        print(f"Vault missing: {vault}", file=sys.stderr)
        return 1

    handler = make_handler(vault)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Vault preview: {url}")
    print(f"Serving: {vault}")
    print("Secrets are not exposed. Ctrl+C to stop.")
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
