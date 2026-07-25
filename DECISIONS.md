# DECISIONS.md — Append-only decision log

> One dated line (or short block) per decision. Never rewrite history; if a decision is reversed, append the reversal.

- **2026-07-13 · D1** — Disruption frames locked (user choice): **Gaming** = AI/agentic disruption of game discovery & distribution (incumbents: Steam/console/app stores) · **FMCG** = agentic commerce bypassing the retail shelf (incumbents: brand × big-retail model) · **Luxury** = AI vs the controlled-distribution maison model (incumbents: LVMH/Kering-style houses). Frame details drafted in `industries/<ind>/frame.md` — still to be reviewed/approved per industry before population.
- **2026-07-13 · D2** — Toggle architecture (user choice): one repo + one Vercel project; `/gaming` `/fmcg` `/luxury` as separate self-contained dashboards; header toggle navigates between pages.
- **2026-07-13 · D3** — Scope (user choice): ~120–150 companies per industry at full column depth, populated by research agents in evidence-cited batches of ~15–25.
- **2026-07-13 · D4** — Home (user choice): new public repo `industry-ai-landscapes` built from the sanitized travel `template/`; zero Amadeus client material (no travel data, findings, or client names) may enter this repo.
- **2026-07-13 · D5** — Schema (Claude design, per plan approval): one identical 111-column skeleton for all three industries (five travel phases + a new EVIDENCE block; prefix conventions `w1_…/d1_…/ai1_…/vc1_…/f1_…`); per-industry meaning carried in each workbook's Scoring Guide sheet + `frame.md`. Scoring weights identical to the travel Model Config (EPI=.4W+.6R; R=.5D+.5AI; bands 60/40). **Derived scores are computed in Python by `populate.py` as plain values — never Excel formulas** (avoids the openpyxl cached-formula trap).
