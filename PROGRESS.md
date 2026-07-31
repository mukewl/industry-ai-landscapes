# PROGRESS.md — Cross-industry status board

> The resume point. Update after every batch/milestone, not just session end.

**Last updated:** 2026-07-13 (session 02 — iGaming + orchestration system)
**Current phase:** B (iGaming population) — **14 / ~130 companies populated**, QA green.

> ⛔ **BLOCKED: monthly spend limit reached.** The last fleet run died with "You've hit your monthly
> spend limit" (not a session limit). **Do not launch research agents until this is resolved** —
> they fail instantly and the run is wasted. Resolve by raising the limit at
> claude.ai/settings/usage or waiting for the monthly reset. Everything else (populate, QA,
> dashboard work, analysis) still works fine.

**Remaining from batch 02 (11 companies, re-run when unblocked):** evoke plc (888/William Hill) ·
Kindred Group · Super Group (Betway) · Playtech · Pragmatic Play · Kambi Group · SoftSwiss ·
Paysafe · Kalshi · Underdog Fantasy · GeoComply

## Status board

| | **iGaming** | Gaming | FMCG | Luxury |
|---|---|---|---|---|
| Frame (`frame.md`) | ⚠ draft (in use) | ⚠ draft | ⚠ draft | ⚠ draft |
| Skeleton workbook | ✅ 116 cols | ✅ 111 cols | ✅ 111 cols | ✅ 111 cols |
| Researcher brief | ✅ generated | — | — | — |
| Seed list (~150) | ✅ | — | — | — |
| **Populated companies** | **see ledger / ~130** | **0 / ~130** | **0 / ~130** | **0 / ~130** |
| Calibration anchors | batch 1 → `anchors.md` | — | — | — |
| Relationships pass | — | — | — | — |
| Dashboard adapted + built | — | — | — | — |
| Deployed | — | — | — | — |
| Findings register | — | — | — | — |

Population detail per industry: `industries/<ind>/batches/ledger.md`.

## Shared infrastructure

| Item | Status |
|---|---|
| Repo scaffold + `template/` | ✅ session 01 |
| GitHub repo `industry-ai-landscapes` (public) | ✅ pushed |
| **Orchestration system** (`ORCHESTRATION.md`, `research_batch.js`, `populate.py`, `qa_check.py`, agent def) | ✅ session 02 — write path verified end-to-end |
| Landing page + 4-way header toggle | — (Phase B5, with the first dashboard) |
| Vercel project + env vars | — (Phase B5) |
| Industry-aware `api/scenario.js` | — (Phase B5) |

## How to run the next batch (full detail in ORCHESTRATION.md)

1. Pick the next ~25 from `industries/igaming/seedlist.md` (skip anything already in the workbook — check it first, never assume).
2. `Workflow({scriptPath: "scripts/research_batch.js", args: {industry, root (ABSOLUTE), perAgent: 5, companies: [...]}})` — args must be a real JSON object.
3. QA-gate the returned rows (7 checks in ORCHESTRATION.md), save to `industries/igaming/batches/igaming-batch-NN.json`.
4. `python -X utf8 scripts/populate.py igaming <batch.json>` then `python -X utf8 scripts/qa_check.py igaming`.
5. Update this file + session log, commit.

## Watch-outs

- **Long fleet runs can die on the session/usage limit and return nothing** (happened in session 02: 5 agents, 237k tokens, 0 rows — agents never got to return their structured output). Keep batches ~10–25, and **always check the workbook + ledger before re-running** so you neither duplicate nor lose work. Nothing is persisted until `populate.py` runs.
- Frames are still **drafts** — worth a user review pass before the dataset gets large.
- `qa_check.py` exits non-zero on FAIL; treat that as a hard gate, not advice.
- Regenerating a workbook via `make_workbook.py` **wipes populated rows** — only safe while empty (regenerating the *brief* alone is always safe).
- No Amadeus client material in this repo, ever.
