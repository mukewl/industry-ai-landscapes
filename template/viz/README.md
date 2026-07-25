# viz/ — the generated dashboard

`dashboard.html` lands here, built by `python -X utf8 scripts/build_dashboard.py`. It is fully self-contained (all data, CSS and JS inline; no external requests) — **never hand-edit it**; edit the HTML/CSS/JS template string inside `scripts/build_dashboard.py` and rebuild.

Serve locally with `python -X utf8 scripts/sandbox_server.py` (→ http://localhost:8765, also enables scenario-brief saving), or open it as a plain file (everything works except saving briefs and the AI bar, which needs the deployed `/api/scenario`).
