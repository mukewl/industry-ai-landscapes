# PROJECT.md — <CLIENT> <INDUSTRY> Landscape

<!-- TEMPLATE: fill every <PLACEHOLDER>. This mirrors the structure that worked
     for the reference (travel) project — keep the sections, change the content. -->

## What this is

Market-intelligence / landscape research for **<CLIENT>** on how <DISRUPTION FORCE, e.g. AI> will disrupt <INDUSTRY / the incumbent's business model>. We mapped **<N> companies** — <the actor categories in your sector taxonomy> — and scored their potential to enter or disrupt <the market> in `<WORKBOOK_FILENAME>.xlsx`.

## Objectives (from the client brief)

1. <objective — e.g. identify non-traditional actors with entry potential>
2. <objective — e.g. map the emerging distribution/value-capture models>
3. <objective — e.g. strategic implications for the client ecosystem>
4. <objective — e.g. early signals, scenarios & trajectories (3–5 years)>
5. <objective — e.g. strategic options: engage / build / partner / defend>

## Current workstreams (this folder)

| # | Workstream | Deliverable | Status file |
|---|---|---|---|
| 1 | **Threat ranking** — top companies that threaten <CLIENT> + how to react | `analysis/01-threat-ranking.md` | see STATE.md |
| 2 | **Relationship web** — who partners with / acquired / powers whom | `analysis/02-relationship-web.md` + `data/relationships.json` | see STATE.md |
| 3 | **Synergy mapping** — non-obvious combinations that could become a major threat | `analysis/03-synergy-mapping.md` | see STATE.md |
| 4 | **Hidden patterns** — structural patterns in the data | `analysis/04-hidden-patterns.md` | see STATE.md |

## The workbook (source of truth)

**Landscape sheet** — <N> companies × <M> columns. Headers in row 3, data from row 4. Phases:

- **Phase 1 · PROFILE**: identity/firmographics, business model, <connectivity/technology stack>, <capability stack>, <value-chain coverage>.
- **Phase 2 · POSITION**: <market coverage / verticals>, position class, motion, target segments, rationale.
- **Phase 3 · POTENTIAL**: <Willingness signals (w1–w5)>, <readiness signals (d1–d6)>, <capability signals (ai1–ai7)>, each 0–5 → %; blended into **<INDEX NAME>** 0–100 and a quadrant.
- **Phase 4 · POSTURE**: threat tier (High/Medium/Low), horizon, impact on <CLIENT>, suggested/final action.
- **Phase 5 · ELIMINATION**: financials, financial-health %, survival tier.

**Supporting sheets**: Model Config (weights: <INDEX> = 0.4·Willingness + 0.6·Readiness; Readiness = 0.5·<D> + 0.5·<AI>; bands ≥60 High, ≥40 Medium) · <others>.

**Known data gaps**: <list them honestly — they shape what analysis is possible>.

## Glossary

| Term | Meaning |
|---|---|
| **<INCUMBENT TERM>** | <the rail/platform under threat> |
| **<INDEX NAME>** | Composite 0–100: blended willingness + readiness to enter |
| **Quadrants** | Imminent threat (high W · high R) · Aspirant (high W · low R) · Sleeping giant (low W · high R) · Dormant |
| **Pillars** | <demand-equivalent> / <content-equivalent> / <settlement-equivalent> — all three = a full no-<incumbent> stack |
| <industry terms> | … |

## People & context

- User: <name/role/email>.
- Reference date when scaffolded: <YYYY-MM-DD>.
- Built from the landscape-dashboard template (see the template's README.md for architecture; original reference implementation: github.com/mukewl/amadeus-travel-landscape).
