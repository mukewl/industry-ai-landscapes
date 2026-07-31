export const meta = {
  name: 'research-batch',
  description: 'Fan out Sonnet researchers over a batch of companies and return scored landscape rows',
  whenToUse: 'Populating an industry landscape workbook. Pass {industry, companies:[...]} as args.',
  phases: [
    { title: 'Research', detail: 'Sonnet agents research and score companies in parallel' },
  ],
}

// ---- inputs -----------------------------------------------------------------
// args may arrive as an object or as a JSON-encoded string — accept both.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
A = A || {}
const industry = A.industry || 'igaming'
const companies = A.companies || []
// perAgent=4, set from MEASUREMENT not theory:
//   perAgent=5 -> 27k tokens/company (batch 01, 10 companies)
//   perAgent=1 -> 68k tokens/company (canary, 3 companies)  <-- 2.5x WORSE
// Every agent turn re-sends the full context (system prompt + tool defs + schema +
// brief), so fixed overhead is paid PER TURN. More agents multiplies that overhead
// instead of amortizing it. Grouping similar companies also lets one search inform
// several. Keep companies in a chunk thematically similar (all operators, all
// suppliers) for the same reason.
const perAgent = A.perAgent || 4
if (!companies.length) throw new Error('research_batch: args.companies is empty (got: ' + JSON.stringify(args).slice(0, 200) + ')')

// root must be absolute — the session cwd is not necessarily the project folder
const root = A.root || 'D:/Amadeus Consulting Project/industry-landscapes'
const brief = `${root}/industries/${industry}/researcher_brief.md`
const frame = `${root}/industries/${industry}/frame.md`
const anchors = `${root}/industries/${industry}/anchors.md`

// ---- output contract --------------------------------------------------------
// Signals are arrays so the schema stays readable: w[5], d[6], ai[7] — index i is
// signal i+1, and *_notes[i] is its <=12-word justification.
const SIGNAL_ARRAY = { type: 'array', items: { type: ['integer', 'null'], minimum: 0, maximum: 5 } }
const NOTE_ARRAY = { type: 'array', items: { type: 'string' } }

const COMPANY = {
  type: 'object',
  properties: {
    name: { type: 'string', description: 'Legal entity / listed group name (not a brand)' },
    sector: { type: 'string', description: 'EXACTLY one value from the brief taxonomy' },
    hq: { type: ['string', 'null'] },
    founded: { type: ['integer', 'null'] },
    ftes: { type: ['integer', 'null'] },
    total_funding_mn: { type: ['number', 'null'], description: 'USD millions raised, null if unknown/NA' },
    market_cap_valuation_mn: { type: ['number', 'null'], description: 'USD millions, listed cap or latest valuation' },
    business_model_notes: { type: 'string', description: '1-2 sentences: how it makes money' },
    customer_base_segment: { type: ['string', 'null'], description: 'B2C / B2B / B2B2C + who' },
    revenue_traction: { type: ['string', 'null'], description: 'Latest revenue or scale datapoint with year' },
    survival_tier: { type: ['string', 'null'], enum: ['Strong', 'Stable', 'At-risk', 'Distressed', 'Unknown', null] },
    // industry-specific profile (iGaming)
    licensed_jurisdictions: { type: ['string', 'null'], description: 'Key licences held, comma separated' },
    regulated_revenue_pct: { type: ['number', 'null'] },
    crypto_accepted: { type: ['string', 'null'], enum: ['y', 'n', null] },
    responsible_gambling_stance: { type: ['string', 'null'] },
    // flags
    merchant_of_record: { type: ['string', 'null'], enum: ['y', 'n', null] },
    direct_channel: { type: ['string', 'null'], enum: ['y', 'n', null] },
    api_commerce_ready: { type: ['string', 'null'], enum: ['y', 'n', null] },
    mcp: { type: ['string', 'null'], enum: ['y', 'n', null] },
    a2a: { type: ['string', 'null'], enum: ['y', 'n', null] },
    ucp: { type: ['string', 'null'], enum: ['y', 'n', null] },
    acp: { type: ['string', 'null'], enum: ['y', 'n', null] },
    // AI stack
    is_ai_the_core_focus: { type: ['string', 'null'], enum: ['y', 'n', null] },
    foundation_model_approach: { type: ['string', 'null'] },
    customer_facing_ai_assistant: { type: ['string', 'null'], enum: ['y', 'n', null] },
    agentic_maturity_layer: { type: ['string', 'null'], description: 'L0/L1/L2/L3' },
    proprietary_data_advantage: { type: ['string', 'null'] },
    gen_ai_platform_partnerships: { type: ['string', 'null'] },
    existing_partnerships: { type: ['string', 'null'], description: 'Named partners/investors/acquisitions, comma separated' },
    // coverage
    verticals: { type: 'array', items: { type: 'string' }, description: 'Which of the 5 verticals it covers' },
    value_chain: { type: 'array', items: { type: 'string' }, description: 'Which VC stages it covers' },
    // signals
    w: SIGNAL_ARRAY, w_notes: NOTE_ARRAY,
    d: SIGNAL_ARRAY, d_notes: NOTE_ARRAY,
    ai: SIGNAL_ARRAY, ai_notes: NOTE_ARRAY,
    f: SIGNAL_ARRAY, f_notes: NOTE_ARRAY,
    // posture judgement
    impact_on_incumbent_line: { type: 'string', description: 'One line: what this company does to the incumbent' },
    residual_gap: { type: ['string', 'null'], description: 'What it still lacks to complete the bypass' },
    horizon: { type: ['string', 'null'], enum: ['0-12m', '1-3y', '3y+', null] },
    // provenance
    evidence_links: { type: 'array', items: { type: 'string' } },
    evidence_notes: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    notes: { type: ['string', 'null'], description: 'Ambiguity, subsidiary/duplicate flags, scoring rationale' },
  },
  required: ['name', 'sector', 'business_model_notes', 'w', 'd', 'ai',
             'w_notes', 'd_notes', 'ai_notes', 'evidence_links', 'confidence',
             'impact_on_incumbent_line'],
}

const SCHEMA = {
  type: 'object',
  properties: { companies: { type: 'array', items: COMPANY } },
  required: ['companies'],
}

// ---- fan out ----------------------------------------------------------------
const chunks = []
for (let i = 0; i < companies.length; i += perAgent) chunks.push(companies.slice(i, i + perAgent))
log(`${companies.length} companies → ${chunks.length} Sonnet agents × ~${perAgent}`)

phase('Research')
const results = await parallel(chunks.map((chunk, i) => () =>
  agent(
    [
      `Research and score these ${chunk.length} companies for the ${industry} disruption landscape:`,
      ...chunk.map((c) => `  TARGET: ${c}`),
      ``,
      `Work through them ONE AT A TIME and write each to disk before starting the next`,
      `(see CRASH SAFETY below). They are thematically similar, so a search that informs`,
      `more than one of them is a bonus — reuse what you already found rather than`,
      `re-searching the same ground.`,
      ``,
      `SCORING AUTHORITY — read these two files first (and only these):`,
      `  - \`${brief}\` : frame, sector taxonomy, verticals, value chain, 0/3/5 anchors.`,
      `  - \`${anchors}\` : already-scored calibration companies (if present). Match that scale.`,
      ``,
      `RESEARCH BUDGET — respect this, it is a hard constraint:`,
      `  - Max 3 web searches. Prefer search-result snippets; they usually suffice.`,
      `  - Max 2 WebFetch calls, and ONLY when snippets genuinely cannot answer a field`,
      `    (e.g. you need a specific revenue figure). Never fetch a page you can skip.`,
      `  - Do not research beyond what the schema needs. Stop when the fields are filled.`,
      ``,
      `METHOD:`,
      `1. Resolve to the legal entity / listed group, not a brand. Note subsidiaries or`,
      `   suspected duplicates in \`notes\`.`,
      `2. Score every signal 0-5 as whole integers against the brief's anchors.`,
      `3. Justify each score in <=10 words. \`f_notes\` may be omitted.`,
      `4. Cite >=2 real source URLs. Prefer evidence from the last 18 months.`,
      `5. Use null for genuine unknowns. NEVER invent funding, headcount, licences or`,
      `   partnerships — an honest null beats a fabricated number.`,
      ``,
      `SCORING DISCIPLINE:`,
      `- Score the FRAME, not company size. A giant uninterested in this disruption scores`,
      `  LOW on willingness; a startup attacking the incumbent's core scores HIGH on`,
      `  willingness, LOW on readiness. Big != high score.`,
      `- Evidence tiers: shipped product > announced partnership > exec quote > speculation.`,
      `- confidence: high = strong recent sources; medium = thin in places; low = opaque.`,
      ``,
      `Signal arrays: w=5 (W1..W5), d=6 (D1..D6), ai=7 (AI1..AI7), f=5 financial-health`,
      `(F1 funding adequacy, F2 revenue/profitability, F3 runway, F4 low leverage, F5 capital`,
      `access; null if private and opaque). *_notes hold one justification per score, in order.`,
      `\`sector\` must be EXACTLY one taxonomy value from the brief.`,
      ``,
      `*** CRASH SAFETY — DO THIS BEFORE RETURNING ***`,
      `A usage limit can kill this run at any moment; work is only safe once on disk.`,
      `The instant scoring is done, Write the company JSON object to:`,
      `    ${root}/industries/${industry}/batches/raw/<slug>.json`,
      `(<slug> = name lowercased, non-alphanumerics -> hyphens, e.g. kambi-group.json).`,
      `File content = the company object alone: {"name": "...", "sector": "...", "w": [...], ...}.`,
      `Write the file FIRST, then return the JSON. If a company cannot be researched`,
      `(defunct / no public footprint), still write and return it with confidence "low",`,
      `nulls, and an explanatory \`notes\` — do not drop it.`,
      ``,
      `Return the JSON object only.`,
    ].join('\n'),
    { label: `research:${i + 1}`, phase: 'Research', model: 'sonnet', schema: SCHEMA }
  )
))

const rows = results.filter(Boolean).flatMap((r) => (r && r.companies) || [])
const missing = companies.filter((c) => !rows.some((r) => r.name && r.name.toLowerCase().includes(String(c).toLowerCase().split(' ')[0])))
log(`returned ${rows.length}/${companies.length} rows${missing.length ? ` · not returned: ${missing.join(', ')}` : ''}`)

return { industry, requested: companies.length, returned: rows.length, missing, rows }
