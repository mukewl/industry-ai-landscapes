// Vercel serverless: the AI Radar's question engine.
// Free-text question -> Gemini grounded in the scored 25-company iGaming index +
// the Betsson field-research facts -> strict-JSON briefing the constellation renders.
// Env: GEMINI_API_KEY (required), GEMINI_MODEL (default gemini-2.5-flash),
//      SCENARIO_PASSCODE (gate), optional KV_REST_API_URL/KV_REST_API_TOKEN (shared cache).
const COMPANIES = require('./company_index_igaming.json');
const MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash';
const PROMPT_VER = 'r1';

const RULES = [
  'You are the analyst engine of an iGaming AI Radar: an interactive constellation of scored companies built to answer',
  'strategic questions from the vantage point of Betsson AB, the Stockholm-listed multi-brand operator (Betsson, Betsafe,',
  'Nordicbet, Rizk). You receive one free-text question and return ONLY JSON in the required schema.',
  '',
  'THE SCORING MODEL (all numbers in the dataset follow it — keep yours consistent):',
  '- W = willingness to disrupt the licensed-operator model (0-100). D = distribution readiness. AI = AI readiness.',
  '- Readiness R = 0.5*D + 0.5*AI. Disruption score = 0.4*W + 0.6*R. Bands: >=60 High, >=40 Medium, else Low.',
  '- Quadrants: Imminent threat (W>=60,R>=60) / Aspirant (W>=60,R<60) / Sleeping giant (W<60,R>=60) / Dormant.',
  '- Pillars: P=Player (owns intent), R=pRoduct (owns odds/games), W=Wallet (licensed money). All three = can bypass operators.',
  '',
  'GROUNDED FACTS ABOUT BETSSON (researched Aug 2026, cite-worthy — do not contradict):',
  '- Q2 2026: record revenue EUR 310m but EBIT -39%; gaming taxes +~EUR15m; marketing = 16% of B2C revenue, 21% incl. affiliates;',
  '  CEO Lindwall: cutting marketing/product spend "wouldn\'t be wise". LatAm now largest division (36% of revenue, +32%).',
  '- EUR 75m credit facility earmarked for M&A: "entering new markets or acquiring valuable technologies".',
  '- CEO on prediction markets (Feb 2026): "very interesting market segment" but "no plans to enter as of now" (regulatory fit).',
  '- Betsson is building an AI org: hiring a Head of AI (Malta, Center of Excellence, explicit competitive-radar duties),',
  '  AI Tech Lead, AI Engineers (Malta/Budapest). Director of Data & AI Cleber de Lima (Jun 2026): direction is self-service',
  '  AI agents answering questions in minutes instead of dashboards; 2,000+ staff AI-trained; GenAI streams scaling into 2026.',
  '- Sector context: AI search is collapsing the affiliate/SEO acquisition rail (organic CTR -61% under AI Overviews;',
  '  71% of affiliate sites hit by the March 2026 core update). Betsson still runs the classic funnel (CRM/PPC/SEO/affiliate hires).',
  '',
  'ANSWERING RULES:',
  '- Ground every claim in the dataset scores or the facts above. Company "before" numbers are REAL data — never alter them.',
  '- Resolve companies to EXACT dataset names. If the question involves an entity outside the dataset, reason about it but',
  '  say so in caveats and lower confidence. Never invent scores for non-dataset companies.',
  '- briefing: 2-4 tight paragraphs, plain language, no jargon, written like a memo to Betsson\'s C-level.',
  '- forBetsson: ONE sentence — the single action or watch-signal this implies for Betsson.',
  '- affected: up to 8 dataset companies materially relevant to the question. effect: rises|falls|exposed|watch|opportunity.',
  '  reason <= 15 words each, grounded.',
  '- confidence high/medium/low + caveats (one short sentence). Be honest about uncertainty.',
  '',
  'THE DATASET (25 scored companies):',
  JSON.stringify(COMPANIES),
].join('\n');

const SCHEMA = {
  type: 'OBJECT',
  properties: {
    title: { type: 'STRING' },
    briefing: { type: 'STRING' },
    forBetsson: { type: 'STRING' },
    affected: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          name: { type: 'STRING' },
          effect: { type: 'STRING', enum: ['rises', 'falls', 'exposed', 'watch', 'opportunity'] },
          reason: { type: 'STRING' },
        },
        required: ['name', 'effect', 'reason'],
      },
    },
    confidence: { type: 'STRING', enum: ['high', 'medium', 'low'] },
    caveats: { type: 'STRING' },
  },
  required: ['title', 'briefing', 'forBetsson', 'affected', 'confidence'],
};

const KV_URL = process.env.KV_REST_API_URL;
const KV_TOKEN = process.env.KV_REST_API_TOKEN;
async function kvCmd(cmd) {
  if (!KV_URL || !KV_TOKEN) return null;
  const res = await fetch(KV_URL, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + KV_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify(cmd),
  });
  return res.ok ? res.json() : null;
}
const cacheKey = q => 'radar:' + PROMPT_VER + ':' + MODEL + ':' + q.toLowerCase().replace(/\s+/g, ' ').trim();
async function cacheGet(k) { try { const j = await kvCmd(['GET', k]); return j && typeof j.result === 'string' ? JSON.parse(j.result) : null; } catch (e) { return null; } }
async function cacheSet(k, v) { try { await kvCmd(['SET', k, JSON.stringify(v), 'EX', 2592000]); } catch (e) {} }

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
async function callGemini(question) {
  const res = await fetch('https://generativelanguage.googleapis.com/v1beta/models/' + MODEL + ':generateContent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: RULES }] },
      contents: [{ role: 'user', parts: [{ text: 'Question: ' + question }] }],
      generationConfig: { temperature: 0, responseMimeType: 'application/json', responseSchema: SCHEMA },
    }),
  });
  if (!res.ok) throw new Error('Gemini ' + res.status + ': ' + (await res.text().catch(() => '')).slice(0, 300));
  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  return parseModelJson(text);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ error: 'Use POST.' }); return; }
  if (!process.env.GEMINI_API_KEY) { res.status(500).json({ error: 'The radar is not configured yet (missing GEMINI_API_KEY on the server).' }); return; }
  let body;
  try { body = await readBody(req); } catch (e) { res.status(400).json({ error: 'Bad request body.' }); return; }
  const passcode = (body.passcode || '').trim();
  if (process.env.SCENARIO_PASSCODE && passcode !== process.env.SCENARIO_PASSCODE) { res.status(401).json({ error: 'Wrong passcode.' }); return; }
  const q = (body.question || '').toString().trim();
  if (!q) { res.status(400).json({ error: 'Empty question.' }); return; }
  if (q.length > 500) { res.status(400).json({ error: 'Keep the question under ~500 characters.' }); return; }
  try {
    const key = cacheKey(q);
    const cached = await cacheGet(key);
    if (cached) { res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Cache', 'HIT'); res.status(200).json(cached); return; }
    let out = await callGemini(q);
    if (!out || !out.briefing) out = await callGemini(q);
    if (!out || !out.briefing) { res.status(502).json({ error: 'The radar returned an unreadable answer — try rephrasing.' }); return; }
    await cacheSet(key, out);
    res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Cache', 'MISS');
    res.status(200).json(out);
  } catch (err) {
    res.status(502).json({ error: 'Radar failed: ' + (err?.message || 'unknown error') });
  }
};
