# PROGRESS.md — Cross-industry status board

> The resume point. Update after every batch/milestone, not just session end.

**Last updated:** 2026-07-13 (session 01 — scaffold)
**Current phase:** A complete → next is **Phase B (Gaming)**, starting with frame.md review with the user.

## Status board

| | Gaming | FMCG | Luxury |
|---|---|---|---|
| Frame (`frame.md`) | ⚠ draft — needs user review | ⚠ draft — needs user review | ⚠ draft — needs user review |
| Skeleton workbook (111 cols) | ✅ generated | ✅ generated | ✅ generated |
| Seed list (~150 companies) | — | — | — |
| **Populated companies** | **0 / ~130** | **0 / ~130** | **0 / ~130** |
| Calibration anchors set | — | — | — |
| Relationships pass | — | — | — |
| Dashboard adapted + built | — | — | — |
| Deployed (`/gaming` etc.) | — | — | — |
| Findings register | — | — | — |

## Shared infrastructure

| Item | Status |
|---|---|
| Repo scaffold (CLAUDE/PLAN/PROGRESS/DECISIONS, template/, generator) | ✅ session 01 |
| GitHub repo `industry-ai-landscapes` (public) | ✅ pushed |
| `scripts/populate.py` (batch writer + score computer) | — (Phase B) |
| Landing page + header toggle | — (Phase B, with the first dashboard) |
| Vercel project + env vars (`GEMINI_API_KEY`, `SCENARIO_PASSCODE`) | — (Phase B end) |
| Industry-aware `api/scenario.js` | — (Phase B end) |

## Next actions (in order)

1. **Review `industries/gaming/frame.md` with the user** — pillars, taxonomy+colors, verticals, incumbent benchmark `{w:30,d:95,ai:40}`, scoring anchors (in the workbook's Scoring Guide). Flip status to `approved`.
2. Build the gaming **seed list** (~150 candidates across the 7 sectors; agent sweep → dedupe → rank) → `industries/gaming/seedlist.md`.
3. Write `scripts/populate.py`; research + write **batch 1 (~20 companies incl. the 5 calibration anchors)**.
4. Continue batches to ~130 → relationships pass → dashboard adaptation (template/ADAPTATION-CHECKLIST.md) → deploy.

## Watch-outs

- Frames are **drafts** — do not populate until the user approves the active industry's frame.
- Regenerating a workbook (`make_workbook.py`) is only safe while it's EMPTY.
- No Amadeus client material in this repo, ever.
