# Landscape Dashboard Template

A reusable skeleton for building an **interactive market-intelligence dashboard + AI scenario simulator** for any industry, from a single scored Excel workbook. It was originally built for Amadeus (travel distribution: 553 companies, live at `amadeus-travel-landscape.vercel.app`, source repo `github.com/mukewl/amadeus-travel-landscape`) — that project is the **working reference implementation**, and the code in this template is a verbatim copy of its machinery.

**The core idea:** you research an industry into one Excel workbook (one row per company, scored on willingness / readiness signals), and this pipeline turns it into:

- a **Threat Board** — sortable, filterable ranking of every company by a composite disruption index
- a **Relationship Web** — a "constellation" of all companies + external entities as stars (sized by company scale, colored by sector), with acquisition/partnership/investor edges, clickable sector & quadrant filters, ego-focus, search with autocomplete, and a **globe mode** (companies plotted at HQ on a rotating wireframe earth)
- a **company card** — gauges, quadrant minimap, capability signal bars, value-chain coverage funnel, financials, connections
- an **AI scenario simulator** — a free-text bar ("X acquires Y", "the incumbent is bypassed by …") answered by an LLM grounded in the workbook's own scoring model, rendered as a 3-phase narrative (Now / 6 / 12 months) with capability-vs-incumbent bars, a quadrant map, ranked most-affected companies, and highlighted stars in the sky
- **Synergy Combos** and **Findings** tabs — curated analysis content

Everything ships as **one self-contained `viz/dashboard.html`** (data embedded, no external requests) plus **one serverless function** for the AI, deployed free on Vercel.

---

## Read these in order

| Doc | What it covers |
|---|---|
| **README.md** (this file) | Architecture, file map, working method, local dev, deployment |
| **DATA-CONTRACT.md** | The exact Excel shape and scoring model the pipeline expects |
| **ADAPTATION-CHECKLIST.md** | Every industry-specific touchpoint in the code, as ordered steps |

---

## Architecture

```
 <industry>_landscape.xlsx              (SOURCE OF TRUTH — one row per company)
        │
        │  python -X utf8 scripts/extract_excel.py        (re-run whenever Excel changes)
        ▼
 data/companies.json + support_sheets.json + extract_meta.json (sha256 staleness check)
        │
        │  python -X utf8 scripts/extract_relationships.py (parses partnership/M&A text
        ▼                                                   into a graph; hand-curated
 data/relationships.json  ◄── data/relationships_manual.json  overrides live here)
        │
        │  python -X utf8 scripts/build_dashboard.py
        ▼
 ┌──────────────────────────────┬──────────────────────────────┐
 │ viz/dashboard.html           │ api/company_index.json        │
 │ (self-contained artifact:    │ (compact per-company context  │
 │  all data + CSS + JS inline) │  for the AI system prompt)    │
 └──────────────────────────────┴──────────────────────────────┘
        │                                   │
        │ static hosting                    │ read at cold start by
        ▼                                   ▼
     Vercel  ──── /api/scenario ────► api/scenario.js (serverless)
                                            │  passcode gate → Gemini
                                            │  generateContent with strict
                                            │  responseSchema, temperature 0
                                            ▼
                              optional Vercel KV shared cache
                              (same scenario → same stored answer)
```

Key properties:

- **`dashboard.html` is generated — never hand-edit it.** All changes go into `scripts/build_dashboard.py` (a Python file whose bottom half is a giant HTML/CSS/JS template string) followed by a rebuild.
- **The Excel is the single source of truth** for company data. `data/*.json` is machine-generated (the one exception: `relationships_manual.json`, hand-curated by design).
- The dashboard works **offline as a plain file**; the AI bar needs the deployed serverless function (or a local equivalent) plus a Gemini API key.

## File map

```
template/
├── README.md                     ← you are here
├── DATA-CONTRACT.md              ← Excel schema + scoring model contract
├── ADAPTATION-CHECKLIST.md       ← ordered steps to adapt to a new industry
├── CLAUDE.md                     ← session protocol TEMPLATE (fill placeholders)
├── PROJECT.md                    ← project charter TEMPLATE
├── STATE.md                      ← living dashboard TEMPLATE (empty)
├── DECISIONS.md                  ← append-only decision log (empty)
├── FINDINGS.md                   ← insight register (empty)
├── .gitignore                    ← excludes xlsx, generated json, backups
├── vercel.json                   ← rewrites "/" → /viz/dashboard.html
├── claude-launch.json.example    ← rename to .claude/launch.json (dev server config)
├── scripts/
│   ├── extract_excel.py          ← Excel → data/*.json  (small; adapt first)
│   ├── extract_relationships.py  ← free-text relations → graph json
│   ├── build_dashboard.py        ← THE artifact builder (~1600 lines; the html/css/js
│   │                                template string is the whole front-end)
│   ├── sandbox_server.py         ← local http server + POST /api/save-scenario
│   └── peek.py                   ← tiny data explorer for sanity checks
├── api/
│   └── scenario.js               ← Vercel serverless AI simulator (Gemini + KV cache)
├── data/      README only        ← generated by the scripts
├── viz/       README only        ← generated dashboard.html lands here
├── analysis/  README only        ← numbered workstream .md deliverables
├── sessions/  README only        ← one log per working session
├── scenarios/ README only        ← saved scenario briefs
├── backups/   README only        ← workbook backups before any edit
└── deliverables/ README only     ← client-facing outputs (decks etc.)
```

## The working method (why the .md files exist)

This project structure is designed for **multi-session work with an AI coding assistant** (Claude Code or any capable model). Context lives in files, not chat history:

- **CLAUDE.md** — the session protocol: what to read on start (PROJECT → STATE → latest session log), the staleness check (compare the Excel's sha256 against `data/extract_meta.json`; re-extract if different), source-of-truth rules, and end-of-session bookkeeping. Any model should follow it; rename the file if your tool expects a different name (e.g. `AGENTS.md`).
- **STATE.md** — a short living dashboard: Done / In progress / Next. The entry point for "where were we?"
- **DECISIONS.md** — append-only, one dated line per decision made with the user. Never rewritten.
- **FINDINGS.md** — insights with evidence pointers (company names + columns). A finding without an evidence pointer is not a finding.
- **sessions/** — one markdown log per session: what was done, what was produced, open threads.

This discipline is what makes the project safely resumable by a *different* model later — which is the point of this template.

### Kickoff prompt for a new model

Paste something like this into a fresh session in your new project copy:

> This folder is a copy of a landscape-dashboard template. Read `README.md`, `DATA-CONTRACT.md`, and `ADAPTATION-CHECKLIST.md` in the template docs, then `CLAUDE.md` for the working protocol. My industry is `<X>`; the scored workbook is `<file.xlsx>` with `<N>` companies. Work through the adaptation checklist step by step, asking me for the industry-specific choices (sector taxonomy, value-chain stages, capability pillars, the incumbent and its benchmark profile). Verify each stage before moving on: extraction counts, then the dashboard rendering in a browser preview, then deployment.

## Local development

```powershell
# 1. extract (whenever the Excel changes)
python -X utf8 scripts/extract_excel.py
python -X utf8 scripts/extract_relationships.py   # after curating aliases

# 2. build the artifact
python -X utf8 scripts/build_dashboard.py

# 3. serve locally (also enables scenario-brief saving)
python -X utf8 scripts/sandbox_server.py           # → http://localhost:8765
```

Requires Python 3.10+ with `openpyxl`. `world_110m.json` (globe wireframe) is downloaded once from the world-atlas project — or copy it from the reference repo's `data/`; without it the globe ships graticule-only.

### Windows / PowerShell gotchas (learned the hard way)

- Always run Python with `-X utf8` — the data is full of non-ASCII (·, —, →).
- PowerShell 5.1 has no `&&`; use `;`. It also mangles inner double quotes in `python -c` one-liners — write script files instead.
- If you ever edit the workbook programmatically: **back it up to `backups/` first**, and edit via **Excel COM**, never an openpyxl save — openpyxl strips cached formula values and will destroy computed columns.

## Deployment (GitHub + Vercel, all free tier)

1. `git init` → commit → create a GitHub repo → push. The provided `.gitignore` keeps the workbook and regenerable JSON out of git (the data is already embedded in `dashboard.html`; keep `data/relationships_manual.json` tracked).
2. **vercel.com → New Project → import the repo.** Framework preset **"Other"**, no build command, root directory `./`. `vercel.json` rewrites `/` → `/viz/dashboard.html`; Vercel auto-serves `api/*.js` as serverless functions. Every push to the default branch auto-redeploys.
3. **Environment variables** (Project → Settings → Environment Variables), then redeploy:
   - `GEMINI_API_KEY` — free key from aistudio.google.com (required for the AI bar; without it the endpoint returns a friendly "not configured" error and everything else still works)
   - `SCENARIO_PASSCODE` — any passphrase; users type it once per browser session to unlock the AI bar (protects your API quota on a public URL)
   - `GEMINI_MODEL` — optional, defaults to `gemini-2.5-flash`
4. **Shared answer cache** (optional but recommended): Vercel → Storage → create an **Upstash Redis / KV** store → connect it to the project (auto-adds `KV_REST_API_URL` / `KV_REST_API_TOKEN`) → redeploy. Same scenario text → same stored answer, instantly, for every visitor (30-day TTL; bump `PROMPT_VER` in `api/scenario.js` to invalidate). Without KV the AI still works, just uncached.
5. Privacy note: the full company dataset is embedded in the public `dashboard.html` and a compact index is sent to the LLM provider — treat the workbook contents as **non-confidential** or put the deployment behind access control.

## Design decisions worth keeping (from the reference project)

- **Plain language in user-facing scenario output** — no internal jargon ("85% integration haircut"); say "disruption score out of 100".
- **AI methodology is hybrid**: the LLM must use the *real* current scores from `company_index.json` as "before" values and may only estimate the "after" deltas, each with a one-line data-grounded reason; strict JSON via `responseSchema`; `temperature 0`; never fabricate dataset membership. The scoring formula is restated in the prompt so numbers stay internally consistent.
- **Scenario visuals**: dim everything not in the scenario to 30%, form gold bonds, let the sky animate ~1.6s, *then* open the report. Report opens at "Now".
- **Exposure is flag-only**: second-order neighbors get flagged with a reason, their scores are never silently changed.
- One motion language (CSS tokens `--ease`, `--t1/2/3`), `prefers-reduced-motion` respected; the constellation drifts perpetually but gently.
- The engine's own scenario model (union-find merges, capability union with a day-1 haircut → ceiling) still exists in `build_dashboard.py` (`runScenario`) as a no-AI fallback for programmatic presets, though the UI's primary path is the AI.
