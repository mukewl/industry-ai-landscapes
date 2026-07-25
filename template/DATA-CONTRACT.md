# DATA-CONTRACT.md — what the pipeline expects from the Excel

The whole artifact hangs off one workbook. If your new industry's workbook honors this contract, the pipeline runs with only cosmetic code changes; where you deviate, ADAPTATION-CHECKLIST.md tells you which code to touch.

## 1. Workbook shape

- One sheet named **`Landscape`**: one row per company. **Headers in row 3, data from row 4** (constants `HEADER_ROW` / `DATA_START_ROW` in `scripts/extract_excel.py`).
- Headers are converted to `snake_case` (`%`→`pct`, `&`→`and`); duplicate header names get `_2`, `_3` suffixes. All downstream code refers to columns by these snake names.
- A **`Reviewer notes`** column is the audit trail for any workbook edit made during the project; rows whose value starts with `DUPLICATE` are **excluded** by the extractor.
- Any other sheets (scoring config, scenarios, response plans…) are dumped as raw grids into `data/support_sheets.json` for reference.
- Recommended supporting sheet: **Model Config** documenting your scoring weights (§3), so the workbook stays self-describing.

## 2. Columns the pipeline actually consumes

Everything else in the workbook is fine to keep — it just won't render. The generated payload key each column feeds is shown in parentheses (see `comp.append({...})` in `scripts/build_dashboard.py`).

### Identity & classification
| Column (snake name) | Used for |
|---|---|
| `company` | Unique key everywhere (`n`). Spelling must match `relationships.json` node ids. |
| `source_sector_taxonomy` | Sector → star color, legend, filters (`sec`). Keep it a **small controlled vocabulary** (~5–8 values) — each needs a color in `SECCOL`. |
| `hq` | Geocoding for globe mode (`geo`) — "City, Country" free text; matched against city/country centroid tables. |
| `business_model_notes` | Card callout + the AI index note (`biz`). First ~300 chars used. |

### Scores (the heart of the model)
| Column | Used for |
|---|---|
| `w1_*` … `w5_*` (five columns, prefix-matched: any header starting `w1_`, `w2_`…) | Willingness signal vector, each **0–5** (`sig.w`) |
| `d1_*` … `d6_*` (six) | Distribution/market-readiness signals, 0–5 (`sig.d`) |
| `ai1_*` … `ai7_*` (seven) | AI-readiness signals, 0–5 (`sig.ai`) |
| `willingness_pct`, `distribution_readiness_pct`, `ai_readiness_pct` | The workbook-computed 0–100 rollups (`w`,`d`,`ai`) — displayed on cards/tables |
| `entry_potential_index` | Composite 0–100 (`epi`) — the ranking metric everywhere |
| `threat_tier` | `High` / `Medium` / `Low` (`t`) — pills, red rings, filters |
| `quadrant` | One of the four quadrant labels (`q`) — filters, minimap |
| `horizon`, `position_class`, `final_action` | Card metadata (`hz`,`pc`,`act`) |

> **Vector lengths (5/6/7) and the group names W/D/AI are baked into the code** (`sig_vec` calls, `SIGLBL` labels, scoring weights). Different counts are fine — change them consistently (checklist step 5).

### Structural flags
| Column | Used for |
|---|---|
| `merchant_of_record` (`y`/`n`) | Settlement pillar (`mor`) |
| `ndc` (`y`/`n`) — industry-specific connectivity standard | Content pillar (`ndc`) |
| `mcp`,`a2a`,`ucp`,`acp` (`y`/`n`) | Agentic-protocol chips (`protos`) — swap for whatever forward-looking adoption signals your industry has |
| 7 value-chain stage columns (`inspiration`, `research_planning`, `shopping_comparison`, `booking`, `payment`, `in_trip_experience`, `post_trip_loyalty`, each `y`/`n`) | The journey-coverage funnel (`jc`) — rename to your industry's chain (see `JSTAGES`) |
| `existing_partnerships` (free text) | Relationship extraction + card (`par`) |
| `gen_ai_platform_partnerships` (free text) | Model-provider dependency detection (`oai`) |

### Financials / scale
| Column | Used for |
|---|---|
| `market_cap_valuation_mn` → `post_money_valuation_mn` → `total_funding_raised_mn` → `total_funding_mn` → `ftes` | First non-empty wins → star size (log scale) |
| `financial_health_pct`, `survival_tier`, `revenue_traction` | Card financial section (`fin`,`sv`,`rev`) |
| `impact_on_amadeus_line`, `residual_gap_what_they_d_need` | "Impact on <incumbent>" and "what they still need" callouts (`imp`,`gap`) |

## 3. The scoring model (generic form)

The reference weights live in the workbook's Model Config sheet and are **mirrored in two places in code** (they must stay in sync): `build_dashboard.py` (`WW/DW/AIW`, `band`, `quad`) and the AI prompt in `api/scenario.js`.

```
W%  = Σ(w_i · WW_i) / 5 · 100          WW = [.25,.25,.20,.20,.10]
D%  = Σ(d_i · DW_i) / 5 · 100          DW = [.25,.25,.15,.15,.10,.10]
AI% = Σ(ai_i · AIW_i) / 5 · 100        AIW = [.20,.25,.15,.10,.10,.15,.05]
R   = 0.5·D% + 0.5·AI%                 (overall readiness)
EPI = 0.4·W% + 0.6·R                   (composite index, 0–100)
Bands:    EPI ≥ 60 High · ≥ 40 Medium · else Low
Quadrant: (W ≥ 60?) × (R ≥ 60?) → Imminent threat / Aspirant / Sleeping giant / Dormant
```

**The three pillars** (a company holding all three can run the industry's transaction end-to-end without the incumbent):
```
demand     = w5 ≥ 4                     (owns customer reach/intent)
content    = d1 ≥ 4 OR ndc = y          (owns the supply/inventory)
settlement = mor = y OR d4 ≥ 4          (takes the payment)
```
Function `pillars()` in `build_dashboard.py`; encoded as a `"DCS"` string (`pil`) in the AI index. Rename the pillar *concepts* to your industry, keep the shape.

**The incumbent benchmark** — the incumbent (Amadeus in the reference) is *not a scored row*; it's a constant `AMA = {w:35, d:95, ai:45}` in `build_dashboard.py` used for the vs-incumbent comparison bars and quadrant dot, and described in prose in the AI prompt. Set it deliberately for your industry and document it in DECISIONS.md.

## 4. Generated artifacts (never hand-edit)

| File | Producer | Notes |
|---|---|---|
| `data/companies.json` | extract_excel.py | full rows, snake keys |
| `data/support_sheets.json`, `data/extract_meta.json` | extract_excel.py | meta holds the source sha256 — the staleness check compares it against the live file |
| `data/relationships.json` | extract_relationships.py | `nodes:[{id, in_dataset, sector, threat_tier, is_amadeus, mentions}]`, `edges:[{source,target,type,raw}]`; edge types group to acquisition / investor / partnership |
| `data/relationships_manual.json` | **hand-curated** (the one exception) | alias fixes + verified edges; tracked in git |
| `viz/dashboard.html` | build_dashboard.py | the entire artifact, data embedded |
| `api/company_index.json` | build_dashboard.py | per company: `{n, sec, w, d, ai, epi, q, t, mor, sv, pil, note}` — the AI's grounding context |
| `data/scenarios/saved/*.json` + `scenarios/*.md` | sandbox_server.py | saved briefs; re-baked as ★ presets on next build |

## 5. Concept mapping table (travel → your industry)

| Generic concept | Travel reference value | Yours |
|---|---|---|
| Incumbent under threat | Amadeus (GDS) | … |
| Composite index name | EPI "Entry-Potential Index" (UI says "disruption score out of 100") | … |
| Signal groups | Willingness / Distribution readiness / AI readiness | … |
| Three pillars | demand / content / settlement | … |
| Value-chain stages (7) | Inspire→Plan→Shop→Book→Pay→In-trip→Post-trip | … |
| Sector taxonomy (~6) | Travel-native, Big Tech platform, Fintech & payments, Retail, AI model provider, Other | … |
| Connectivity standard flag | NDC | … |
| Forward-adoption protocol flags | MCP / A2A / UCP / ACP | … |
| Platform-dependency signal | OpenAI/ChatGPT mentions | … |
| Quadrant labels | Imminent threat / Aspirant / Sleeping giant / Dormant | (often reusable as-is) |
