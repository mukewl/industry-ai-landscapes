# data/ — machine-generated extracts

Everything here is produced by `scripts/` and is regenerable — **never hand-edit** (fix the Excel or the script instead), and most of it is gitignored.

| File | Producer |
|---|---|
| `companies.json`, `support_sheets.json`, `extract_meta.json` | `extract_excel.py` (meta holds the source sha256 for the staleness check) |
| `relationships.json` | `extract_relationships.py` |
| `relationships_manual.json` | **the one hand-curated exception** — alias fixes + verified edges; keep tracked in git |
| `world_110m.json` | world-atlas 110m topojson for globe mode; copy from the reference repo or download once (without it the globe is graticule-only) |
| `scenarios/saved/*.json` | scenario briefs saved via `sandbox_server.py`; re-baked as ★ presets on the next dashboard build |
