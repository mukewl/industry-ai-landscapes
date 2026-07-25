# scenarios/ — saved sandbox briefs

Each file is a **scenario brief** saved from the dashboard's Relationship Web tab: the staged moves, headline index/quadrant/pillar deltas, exposed and mitigated companies, and a blank *Implications* section to fill in after discussion.

How briefs get here: run `python -X utf8 scripts/sandbox_server.py` → run a scenario → **Save brief**. The brief lands as `YYYY-MM-DD-<name>.md`; the move list also goes to `data/scenarios/saved/<name>.json` and reappears as a ★ preset after the next dashboard build. (Opened as a plain file instead, Save downloads the brief through the browser — move it here manually.)

Reading the numbers: engine-computed ranges are before → day-1 (signals × 0.85 integration haircut) → ceiling (full capability union), using the workbook's own Model Config weights. **Exposed** neighbors are flagged with a reason, scores deliberately unchanged. Briefs are inputs to analysis, not conclusions — verify before anything client-facing.
