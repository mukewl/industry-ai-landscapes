"""Sandbox server: serves viz/ and persists scenario briefs from the dashboard.

    python -X utf8 scripts/sandbox_server.py [port]

Endpoints:
    GET  /...                anything in viz/ (dashboard.html is the index)
    POST /api/save-scenario  {name, note, moves, brief}
        -> scenarios/YYYY-MM-DD-<slug>.md           (the human brief)
        -> data/scenarios/saved/<slug>.json          (reloadable; re-baked into
           the preset list on the next build_dashboard.py run)
"""
import json
import re
import sys
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIZ = ROOT / "viz"
SCN = ROOT / "scenarios"
SAVED = ROOT / "data" / "scenarios" / "saved"


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "scenario"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(VIZ), **kw)

    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/dashboard.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/save-scenario":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n).decode("utf-8"))
            name = str(data.get("name") or "scenario")
            slug = slugify(name)
            SCN.mkdir(exist_ok=True)
            SAVED.mkdir(parents=True, exist_ok=True)
            md_path = SCN / f"{date.today().isoformat()}-{slug}.md"
            md_path.write_text(data.get("brief", ""), encoding="utf-8")
            (SAVED / f"{slug}.json").write_text(json.dumps(
                {"name": name, "note": data.get("note", ""), "moves": data.get("moves", []),
                 "saved": date.today().isoformat()}, indent=1, ensure_ascii=False), encoding="utf-8")
            body = json.dumps({"ok": True, "md": str(md_path.relative_to(ROOT))}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(f"saved scenario -> {md_path.name}")
        except Exception as ex:
            self.send_error(500, str(ex))

    def log_message(self, fmt, *args):
        pass  # quiet


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"sandbox server on http://localhost:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
