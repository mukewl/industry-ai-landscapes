// ============================================================
// TEMPLATE REFERENCE COPY (from the Amadeus travel-distribution project).
// This is WORKING code for the travel industry, shipped as the reference
// implementation. To adapt it to a new industry, follow the numbered steps
// in ../ADAPTATION-CHECKLIST.md (or ADAPTATION-CHECKLIST.md at template root)
// -- every industry-specific marker in this file is listed there by name.
// ============================================================
// Vercel serverless function: AI scenario simulator for the Amadeus landscape.
// Calls Google Gemini with the dataset + scoring rules and returns a strict-JSON impact.
// Env: GEMINI_API_KEY (required), GEMINI_MODEL (default gemini-2.5-flash), SCENARIO_PASSCODE (optional gate).
const COMPANIES = require('./company_index.json');
const MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash';
const PROMPT_VER = 'v2'; // bump to invalidate the shared cache when the rules/output change

const RULES = [
  'You are the simulation engine for a travel-distribution threat landscape built for Amadeus (the incumbent global GDS).',
  'You receive a free-text "what if" scenario and must estimate how it reshapes the companies in the dataset, returning ONLY JSON in the required schema.',
  '',
  'SCORING MODEL (use these exact rules so numbers stay consistent with the dataset):',
  '- Each company has W (willingness to disrupt, 0-100), D (distribution reach, 0-100), AI (AI readiness, 0-100).',
  '- R = 0.5*D + 0.5*AI. EPI (disruption score, 0-100) = 0.4*W + 0.6*R.',
  '- Bands: EPI >= 60 High, >= 40 Medium, else Low.',
  '- Quadrant: Imminent threat (W>=60 and R>=60), Sleeping giant (W<60 and R>=60), Aspirant (W>=60 and R<60), Dormant (otherwise).',
  '- Three pillars of a full no-GDS stack: demand (own consumer reach/intent), content (own travel inventory / NDC), settlement (merchant-of-record / payments). pil in the data shows which a company already holds (D=demand, C=content, S=settlement).',
  '',
  'DOMAIN CONTEXT (from the analysis):',
  '- Lock-and-key: fintechs with demand+settlement pair with travel rails that have content; any cross-pairing = a full no-GDS stack (a real threat to Amadeus).',
  '- A few supply rails sit beneath many front-ends (e.g. Spotnana, Duffel, Sabre, Verteil); compete for the rail, not each logo.',
  '- Merchant-of-record (mor=1) correlates strongly with High threat tier.',
  '- India is the highest-threat-density market; OpenAI is the most depended-on model provider.',
  '- Distressed-but-strategic NDC players (Verteil, TPConnects, Paxport, AirGateway, Mystifly) are acquisition targets; rolled up they become global NDC-bypass coverage.',
  '- Amadeus benchmark: strong distribution/content/settlement on the B2B GDS rail, moderate consumer-AI. Scenarios that build no-GDS stacks or bypass distribution RAISE the threat to Amadeus; scenarios where Amadeus supplies/defends LOWER it.',
  '',
  'OUTPUT RULES:',
  '- Resolve every company to an EXACT name from the dataset below. "before" numbers MUST be the company\'s real current W/D/AI/EPI from the dataset. Estimate "after" values yourself, each justified.',
  '- primary: the single company OR combined entity most central to the scenario (for a merger use name "A + B"; before = the stronger partner\'s current numbers, after = your combined estimate).',
  '- affected: up to 12 companies, each with effect (transformed | rises | falls | exposed | mitigated | removed), epiBefore (real), epiAfter (estimate), and a reason of AT MOST 12 words grounded in the data. Include the most important 2nd-order companies exposed via partnerships/dependencies.',
  '- amadeus: direction (higher | lower | neutral) threat to Amadeus + a note of at most one short sentence.',
  '- phases: exactly 3 — labels "Now", "In 6 months", "In 12 months" — each a punchy 3rd-person headline (<= 8 words) + a story of just 1-2 SHORT sentences showing the disruption-score trajectory. Be concise; no jargon, no formula-speak; write "disruption score out of 100".',
  '- confidence (high/medium/low) + caveats (AT MOST one short sentence). If the scenario names a company or force NOT in the dataset, you may reason about it but set confidence lower and NEVER invent dataset membership or fake "before" numbers for it.',
  '- Keep all text tight and scannable — this feeds a visual dashboard, not a report.',
  '- Keep numbers internally consistent with the formula (e.g. an "after" EPI should roughly equal 0.4*W + 0.6*(0.5*D+0.5*AI)).',
  '',
  'THE DATASET (553 companies, current values):',
  JSON.stringify(COMPANIES),
].join('\n');

const SCHEMA = {
  type: 'OBJECT',
  properties: {
    title: { type: 'STRING' },
    confidence: { type: 'STRING', enum: ['high', 'medium', 'low'] },
    caveats: { type: 'STRING' },
    amadeus: {
      type: 'OBJECT',
      properties: { direction: { type: 'STRING', enum: ['higher', 'lower', 'neutral'] }, note: { type: 'STRING' } },
      required: ['direction', 'note'],
    },
    phases: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: { label: { type: 'STRING' }, date: { type: 'STRING' }, headline: { type: 'STRING' }, story: { type: 'STRING' } },
        required: ['label', 'headline', 'story'],
      },
    },
    primary: {
      type: 'OBJECT',
      properties: {
        name: { type: 'STRING' },
        before: { type: 'OBJECT', properties: { w: { type: 'NUMBER' }, d: { type: 'NUMBER' }, ai: { type: 'NUMBER' }, epi: { type: 'NUMBER' } }, required: ['w', 'd', 'ai', 'epi'] },
        after: { type: 'OBJECT', properties: { w: { type: 'NUMBER' }, d: { type: 'NUMBER' }, ai: { type: 'NUMBER' }, epi: { type: 'NUMBER' } }, required: ['w', 'd', 'ai', 'epi'] },
      },
      required: ['name', 'before', 'after'],
    },
    affected: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          name: { type: 'STRING' },
          effect: { type: 'STRING', enum: ['transformed', 'rises', 'falls', 'exposed', 'mitigated', 'removed'] },
          epiBefore: { type: 'NUMBER' },
          epiAfter: { type: 'NUMBER' },
          reason: { type: 'STRING' },
        },
        required: ['name', 'effect', 'reason'],
      },
    },
    newBonds: { type: 'ARRAY', items: { type: 'ARRAY', items: { type: 'STRING' } } },
  },
  required: ['title', 'confidence', 'amadeus', 'phases', 'affected'],
};

// ---- shared cache via Vercel KV / Upstash REST (optional; skipped gracefully if unset) ----
const KV_URL = process.env.KV_REST_API_URL;
const KV_TOKEN = process.env.KV_REST_API_TOKEN;
function cacheKey(scenario) {
  const norm = scenario.toLowerCase().replace(/\s+/g, ' ').trim();
  return 'scn:' + PROMPT_VER + ':' + MODEL + ':' + norm;
}
async function kvCmd(cmd) {
  if (!KV_URL || !KV_TOKEN) return null;
  const res = await fetch(KV_URL, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + KV_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify(cmd),
  });
  if (!res.ok) return null;
  return res.json();
}
async function cacheGet(key) {
  try {
    const j = await kvCmd(['GET', key]);
    return j && typeof j.result === 'string' ? JSON.parse(j.result) : null;
  } catch (e) { return null; }
}
async function cacheSet(key, value) {
  try { await kvCmd(['SET', key, JSON.stringify(value), 'EX', 2592000]); } catch (e) {} // 30-day TTL
}

async function readBody(req) {
  if (req.body) return typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  let raw = '';
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

function parseModelJson(text) {
  if (!text) return null;
  let t = text.trim();
  if (t.startsWith('```')) t = t.replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '').trim();
  try { return JSON.parse(t); } catch (e) {
    const a = t.indexOf('{'), b = t.lastIndexOf('}');
    if (a >= 0 && b > a) { try { return JSON.parse(t.slice(a, b + 1)); } catch (e2) {} }
    return null;
  }
}

async function callGemini(scenario) {
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODEL + ':generateContent';
  const body = {
    systemInstruction: { parts: [{ text: RULES }] },
    contents: [{ role: 'user', parts: [{ text: 'Scenario: ' + scenario }] }],
    generationConfig: { temperature: 0, responseMimeType: 'application/json', responseSchema: SCHEMA },
  };
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error('Gemini ' + res.status + ': ' + txt.slice(0, 300));
  }
  const data = await res.json();
  const text = data && data.candidates && data.candidates[0] && data.candidates[0].content
    && data.candidates[0].content.parts && data.candidates[0].content.parts[0]
    && data.candidates[0].content.parts[0].text;
  return parseModelJson(text);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ error: 'Use POST.' }); return; }
  if (!process.env.GEMINI_API_KEY) { res.status(500).json({ error: 'AI is not configured yet (missing GEMINI_API_KEY on the server).' }); return; }
  let body;
  try { body = await readBody(req); } catch (e) { res.status(400).json({ error: 'Bad request body.' }); return; }

  const passcode = (body.passcode || '').trim();
  if (process.env.SCENARIO_PASSCODE && passcode !== process.env.SCENARIO_PASSCODE) {
    res.status(401).json({ error: 'Wrong passcode.' }); return;
  }
  const scenario = (body.scenario || '').toString().trim();
  if (!scenario) { res.status(400).json({ error: 'Empty scenario.' }); return; }
  if (scenario.length > 600) { res.status(400).json({ error: 'Scenario is too long — keep it under ~600 characters.' }); return; }

  try {
    const key = cacheKey(scenario);
    const cached = await cacheGet(key);
    if (cached) { res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Cache', 'HIT'); res.status(200).json(cached); return; }
    let out = await callGemini(scenario);
    if (!out || !out.phases || !out.affected) out = await callGemini(scenario); // one retry
    if (!out || !out.phases || !out.affected) { res.status(502).json({ error: 'The AI returned an unreadable result — try rephrasing the scenario.' }); return; }
    await cacheSet(key, out);
    res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Cache', 'MISS');
    res.status(200).json(out);
  } catch (err) {
    res.status(502).json({ error: 'AI simulation failed: ' + (err && err.message ? err.message : 'unknown error') });
  }
};

// Local test:  GEMINI_API_KEY=xxx node api/scenario.js "Tata Neu acquires Hopper"
if (require.main === module) {
  const scenario = process.argv.slice(2).join(' ') || 'Tata Neu acquires Hopper';
  if (!process.env.GEMINI_API_KEY) { console.error('Set GEMINI_API_KEY first.'); process.exit(1); }
  callGemini(scenario).then(o => console.log(JSON.stringify(o, null, 2))).catch(e => { console.error(String(e)); process.exit(1); });
}
