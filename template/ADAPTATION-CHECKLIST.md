# ADAPTATION-CHECKLIST.md — porting the artifact to a new industry

Ordered steps. Every code touchpoint is named by a **searchable marker** (constant/function name) — grep for it rather than trusting line numbers. The shipped code is the *working travel version*; you are re-skinning a running machine, so rebuild + preview after each stage instead of changing everything blind.

**Decide up front (with the user), before touching code** — the concept mapping table at the end of DATA-CONTRACT.md:
incumbent + its benchmark profile · composite index name · 3 signal groups · 3 pillars · value-chain stages · sector taxonomy (~6 values + colors) · connectivity/protocol flags · platform-dependency signal · quadrant labels. Log these in DECISIONS.md.

## Stage 0 — project setup
1. Copy `template/` to a fresh folder; `git init`.
2. Rename `claude-launch.json.example` → `.claude/launch.json`.
3. Fill the placeholders in `CLAUDE.md` and `PROJECT.md`; leave STATE/DECISIONS/FINDINGS as headers.
4. Drop the new industry workbook in the root.

## Stage 1 — extraction (`scripts/extract_excel.py`)
5. Set `EXCEL_FILE` to the new filename; check `HEADER_ROW`/`DATA_START_ROW` match the sheet; sheet must be named `Landscape` (or change `extract_landscape`).
6. Run `python -X utf8 scripts/extract_excel.py`. Verify the printed company/column counts, then spot-check `data/companies.json` field names against DATA-CONTRACT.md §2 (`scripts/peek.py` helps). **Fix mismatches in the workbook, not by renaming keys in code**, wherever possible.

## Stage 2 — relationships (`scripts/extract_relationships.py`)
7. Markers: `SOURCE_FIELDS` (which free-text columns to mine), `TYPE_RULES` (keyword → edge type), `NOISE` / `LEADING_LABEL` (junk filters), `ALIASES` (name normalization — start empty, grow as you find dupes), and `is_amadeus` (node flag keyed on the incumbent's name — change the `startswith` string).
8. Run it; review the top nodes/edges; put corrections in `data/relationships_manual.json` (this file is hand-maintained by design). Acquisition direction is worth hand-verifying — it was the biggest data-quality task in the reference project.

## Stage 3 — the artifact (`scripts/build_dashboard.py`)
Python half (top of file):
9. `company_size` — field fallback order for star size (keep unless your financial columns differ).
10. `sig_vec` calls + `SIGLBL` (JS) — signal-group prefixes and counts (`w`/5, `d`/6, `ai`/7). Change both together, plus the weights in step 14.
11. `openai_dep` — the platform-dependency detector (rename + re-keyword).
12. `CITIES` / `COUNTRIES` — geocode tables; extend with your industry's HQ cities as the "unplaced" build warning lists them.
13. `comp.append({...})` — the column→payload mapping. This is where any workbook naming differences get absorbed.
14. Content blocks: `TOP10` (act-now list), `COMBOS` (synergy tab), `FINDINGS` (findings tab), `PRESETS` (canned scenarios incl. incumbent counter-moves) — all travel content; replace with your industry's or stub with `[]` at first (tabs render empty).
15. `_pillars` (AI-index pillar string) — mirror your pillar definitions.

JS/CSS half (inside the `HTML = r"""…"""` string):
16. `<title>` + the `<header><h1>` product name.
17. `SECCOL` — sector→color map; must cover every value of your sector column (else grey "Other"). `AMACOL` is the incumbent's gold.
18. `JSTAGES` — the 7 value-chain stages (label, emoji, color) for the journey funnel; update the `jc` column list in step 13 to match, and the coverage/gap copy near it.
19. Scoring: `WW`/`DW`/`AIW`, `HAIRCUT`, `band()`, `quad()` (quadrant labels also appear in `quadHtml` corner labels and the card minimap), `pillars()`, `pTxt()` — mirror your Model Config exactly.
20. `AMA` — the incumbent benchmark `{w,d,ai}` (document the chosen values in DECISIONS.md).
21. Incumbent strings: `byId['Amadeus']` lookups, the `ama` move handlers in `runScenario` (`agent-rail`, `openai-supply`, mitigation messages), the "The incumbent rail" tooltip, and the narrative helpers `narr` / `pillarSentence` / `tierWord` / `amaCompare` — grep the file for `Amadeus` and rewrite each in your industry's language. Keep the plain-language rule: no internal jargon in user-facing text.
22. `ex` (example chips in `initSandbox`) and the `#scnInput` placeholder — realistic scenarios for your industry.
23. Rebuild + verify locally: `python -X utf8 scripts/build_dashboard.py`, serve, then check: Relationship Web renders all stars with correct colors/legend counts; sector & quadrant filters toggle; a company card shows gauges/funnel/connections; globe places most companies (check the build's "unplaced" warning); a preset scenario runs (sky dims → bonds → report at "Now").

## Stage 4 — the AI simulator (`api/scenario.js`)
24. `RULES` — the system prompt. Rewrite: the engine's identity line (industry + incumbent), the SCORING MODEL lines (mirror step 19), the DOMAIN CONTEXT block (your industry's key findings, once you have them; the incumbent's strengths and what raises/lowers threat to it), and the pillar letters in the OUTPUT RULES. Keep: the strict-JSON discipline, real-before/estimated-after rule, ≤12-word reasons, confidence/caveats, never-fabricate-membership.
25. Bump `PROMPT_VER` (invalidates the shared cache). `SCHEMA` is industry-agnostic — keep.
26. Local smoke test: `GEMINI_API_KEY=xxx node api/scenario.js "X acquires Y"` → valid JSON with sensible names from *your* dataset.

## Stage 5 — deploy & wire up
27. Push to GitHub → import in Vercel (preset **Other**) → add `GEMINI_API_KEY`, `SCENARIO_PASSCODE` (+ optional `GEMINI_MODEL`) → redeploy. Optional: attach a KV store for the shared answer cache. (Details: README.md deployment section.)
28. Live verification: run a scenario end-to-end on the public URL (progress bar → sky animation → report), re-run the same text (should be instant if KV is attached), try a wrong passcode (clean 401 message), and click through all four tabs.

## Stage 6 — bookkeeping
29. Session log in `sessions/`, decisions in DECISIONS.md, STATE.md updated — per CLAUDE.md. From here the project is a normal multi-session engagement.

### Known deliberate limitations (fine to inherit)
- Engine presets share only content-side signals on partner-merges, no chained merges, exposure is flag-only.
- The incumbent is a benchmark constant, not a scored row.
- Free Gemini tier may train on inputs; the dataset is public in the HTML anyway — treat as non-confidential.
- `viz/dashboard.html` embeds everything (~1.4 MB for 553 companies); thousands of rows will grow it linearly.
