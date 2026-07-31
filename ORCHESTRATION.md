# ORCHESTRATION.md — how the Excels get filled

The population system: **Opus plans, instructs and QA-gates; Sonnet agents do the research at breadth.** Opus keeps the two jobs that need judgment (writing the spec, deciding what's good enough to enter the dataset); Sonnet does the expensive parallel web work.

```
  ┌─ OPUS (orchestrator, this session) ──────────────────────────────┐
  │ 1. load frame.md + Scoring Guide → regenerate researcher_brief.md │
  │ 2. pick the next N companies from seedlist.md                     │
  └───────────────────────────┬───────────────────────────────────────┘
                              ▼  Workflow: scripts/research_batch.js
        ┌──────────┬──────────┬──────────┬──────────┬──────────┐
        │ sonnet 1 │ sonnet 2 │ sonnet 3 │ sonnet 4 │ sonnet 5 │   ← WebSearch + WebFetch
        │ 3-5 cos  │ 3-5 cos  │ 3-5 cos  │ 3-5 cos  │ 3-5 cos  │
        └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
             ▼          ▼          ▼          ▼          ▼
        batches/raw/<company>.json  ← WRITTEN THE MOMENT EACH COMPANY IS DONE
             └──────────┴──────────┴──────────┴──────────┘
                              ▼  {rows:[...]} (happy path) — disk is the safety net
  ┌─ OPUS QA-GATE (before anything is written) ──────────────────────┐
  │ 3. schema/evidence/anchor/sanity review → accept · fix · re-run   │
  └───────────────────────────┬───────────────────────────────────────┘
                              ▼
        scripts/populate.py  →  workbook rows + computed scores + ledger
                              ▼
        scripts/qa_check.py  →  PASS/WARN/FAIL report (non-zero exit on FAIL)
                              ▼
        PROGRESS.md · session log · commit + push
```

## The pieces

| File | Role |
|---|---|
| `industries/<ind>/frame.md` | The disruption frame, pillars, taxonomy, why-now. Hand-written, user-approved. |
| `industries/<ind>/seedlist.md` | Ranked candidate companies (P1/P2/P3) + the calibration anchors. |
| `industries/<ind>/researcher_brief.md` | **Generated** by `make_workbook.py` from the `INDUSTRIES` dict — the single source of truth agents read. Never hand-edit; regenerate. |
| `industries/<ind>/anchors.md` | The scored calibration companies. Written after batch 1; every later batch is calibrated against it. |
| `.claude/agents/company-researcher.md` | The Sonnet agent definition: method, scoring discipline, output contract. |
| `scripts/research_batch.js` | Workflow script: chunks the list, fans out agents with a strict JSON schema, returns rows. Writes nothing. |
| `scripts/populate.py` | Validates + maps rows → columns, computes all derived scores, writes, appends to the ledger. Idempotent. |
| `scripts/qa_check.py` | Post-write quality gate. Exits non-zero on any FAIL. |
| `industries/<ind>/batches/` | Raw batch JSONs (the audit trail) + `ledger.md`. |

## Running a batch

```bash
# 1. (only if signal definitions changed) regenerate the brief
python -X utf8 scripts/make_workbook.py igaming

# 2. fan out — Workflow tool, args as a REAL JSON object (not a string):
#    {industry, root (absolute), perAgent, companies:[...]}
#    → save the returned rows to industries/igaming/batches/igaming-batch-NN.json

# 3. QA-gate the JSON by hand (see below), then write:
python -X utf8 scripts/populate.py igaming industries/igaming/batches/igaming-batch-NN.json --dry-run
python -X utf8 scripts/populate.py igaming industries/igaming/batches/igaming-batch-NN.json

# 4. gate the workbook:
python -X utf8 scripts/qa_check.py igaming
```

## The Opus QA-gate (step 3) — what to actually check

Before any batch is written:

1. **Coverage** — every requested company returned? (the workflow reports `missing`). Re-run missing ones in the next batch rather than blocking.
2. **Evidence** — ≥2 real URLs per company; links plausible (not invented paths); recency noted where it matters.
3. **Vocabulary** — `sector` is exactly one of the taxonomy values; verticals/value-chain names match the brief.
4. **Anchor consistency** — spot-check 2–3 rows against `anchors.md`. A supplier scoring high on *willingness to own the player* is a red flag; so is a small startup scoring 5s on distribution.
5. **Frame discipline** — the classic failure is scoring **size** instead of **the frame**. A giant with no interest in this disruption must score LOW on willingness.
6. **Nulls** — honest nulls are fine; a wall of nulls means re-research (bad company choice or opaque target).
7. **Duplicates/subsidiaries** — check `notes` for flagged overlaps (e.g. NetEnt inside Evolution). One row per legal entity.

Outcomes: **accept** → populate · **fix** → edit the JSON (small factual corrections are fine, log them) · **re-run** → send the company back through with a sharper prompt.

## Crash safety — read this before running anything

Long fleet runs **will** be killed by usage limits. This happened twice while building this
system (5 agents / 237k tokens / 0 rows, then 3 agents / 0 rows) because workflow agents only
return their result at the very end — a kill mid-flight loses everything.

**The fix: agents write one JSON file per company to `industries/<ind>/batches/raw/` the instant
that company is researched**, before starting the next one. Disk is the safety net; the
workflow's return value is just the happy path.

Recovery after any interruption:

```bash
ls industries/<ind>/batches/raw/*.json          # what survived
python -X utf8 scripts/populate.py <ind> --from-raw --dry-run
python -X utf8 scripts/populate.py <ind> --from-raw     # ingests, then retires files to raw/consumed/
python -X utf8 scripts/qa_check.py <ind>
```

Then re-run **only** the companies still missing (compare the workbook's company list against the
batch list — `populate.py` is idempotent, so a re-run of an already-written company updates rather
than duplicates, but re-researching one is wasted tokens).

**Never assume a run's tokens produced data.** Check the workbook and `batches/ledger.md` first —
nothing exists until `populate.py` has run.

## Scale knobs

- `perAgent` (default 5) and batch size — 25/batch (5×5) is the tuned default: big enough to be efficient, small enough that a bad spec is caught before it wastes a lot of tokens.
- The concurrency cap is `min(16, cores-2)`; batches larger than ~50 just queue.
- Cost scales roughly linearly with companies. Re-runs are cheap relative to a bad dataset.

## Calibration protocol

- **Batch 1** of every industry contains the 5 anchors spanning the range (see `seedlist.md`). After QA, record their final scores in `anchors.md`.
- Every batch afterwards: agents read `anchors.md`; `qa_check.py` fails if a recorded anchor drifts more than 8 EPI points.
- Every ~50 companies: re-read a sample of earlier rows against the anchors; if the scale has crept, rescore the affected batch and log it in DECISIONS.md.

## Adding a new industry

1. Add an entry to `INDUSTRIES` in `scripts/make_workbook.py` (title, incumbent, verticals, stages, sectors, pillars, W/D signal definitions with 0/3/5 anchors, optional `extra_profile`).
2. `python -X utf8 scripts/make_workbook.py <ind>` → workbook + brief.
3. Write `frame.md` and `seedlist.md`; review with the user.
4. Run batches exactly as above. Everything else is industry-agnostic.
