# Betsson × AI — field research memo

**Status: researched 2026-08-02.** Purpose: identify evidenced Betsson pain points so the constellation can be reframed into something they would demonstrably value. Sources primary-first (their own job ads, their own interviews, earnings calls); every claim dated.

## P1 — Betsson is building an AI organisation *right now*, and its leaders are on the hook for "competitiveness"

- **Live opening: Head of Artificial Intelligence** (Malta HQ). Remit: "establishing a Center of Excellence, promoting the integration and utilization of AI across the organization… **stay updated on industry trends, emerging technologies, and best practices to inform strategy development and ensure competitiveness**… translate complex AI concepts into clear business strategies… communicated to C-Level Management." ([betssongroup.com/job/head-of-artificial-intelligence](https://betssongroup.com/job/head-of-artificial-intelligence/), [jobsinmalta listing March 2026](https://jobsinmalta.com/job/data/head-of-artificial-intelligence-92775), [LinkedIn posting](https://mt.linkedin.com/jobs/view/head-of-artificial-intelligence-at-betsson-group-4379916561))
- Also open: **AI Tech Lead** ("shape the future of our Artificial Intelligence platform", [Greenhouse 7541132](https://job-boards.greenhouse.io/betsson/jobs/7541132)), **AI Engineers** (Malta + Budapest), ML intern — while the 123-role board shows **zero competitive-intelligence roles**. The radar duty exists in the Head-of-AI JD; no tooling or team behind it.
- **Cleber de Lima, Director of Data & AI** (company interview, 2026-06-25): AI Adoption programme trained **2,000+ employees**; three GenAI product streams (product discovery, software dev, content/design) "scaling into 2026"; agents built inside CRM, SEO, HR, Ops, Legal. His stated direction: **"self-service data through AI agents, allowing employees to ask specific questions and receive answers within minutes, without having to open a dashboard or export data into Excel."** ([betssongroup.com/news](https://betssongroup.com/news/driving-data-and-ai-innovation-at-betsson-a-conversation-with-cleber-de-lima/))
- Q2 2026 call: AI framed as efficiency + CX (AI match previews, customer service, predictive tools) — applied AI, not strategic radar. ([Investing.com transcript, 2026-07-17](https://www.investing.com/news/transcripts/earnings-call-transcript-betsson-posts-record-q2-2026-revenue-as-profit-falls-93CH-4797660))

**Implication for us:** an artifact that *answers landscape questions* speaks their internal language ("ask, don't dashboard"), and the Head-of-AI's explicit competitive-radar duty is exactly what the constellation does.

## P2 — The acquisition machine is expensive and its main external rail is breaking

- Q2 2026: record revenue €310m but **EBIT −39%**; marketing = 16% of B2C revenue, **21% including affiliate costs**; CEO: cutting marketing/product spend "wouldn't be wise." Cost pressure from gaming taxes (+~€15m), payments, personnel. ([Investing.com transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-betsson-posts-record-q2-2026-revenue-as-profit-falls-93CH-4797660))
- Hiring shows the classic funnel still running at full tilt: **5 CRM roles**, Head of PPC (Malta), Senior SEO Specialist (Buenos Aires), Affiliate Account Manager (Chile). ([Greenhouse board](https://job-boards.greenhouse.io/betsson))
- Meanwhile AI search is collapsing that channel sector-wide: AI Overviews on 25.8%–48% of searches (2026), **organic CTR −61% when an Overview appears**, **71% of affiliate sites hit by the March 2026 core update**, "visibility without traffic." ([omnibound AI-Overview stats](https://www.omnibound.ai/blog/google-ai-overviews-statistics), [thestacc 2026 stats](https://thestacc.com/blog/google-ai-overview-statistics/), [xseek 2026](https://www.xseek.io/blogs/articles/ai-traffic-decline-2026), [businessofigaming on iGaming affiliates](https://www.businessofigaming.com/igaming-affiliates-ai-search/))
- Our dataset already scores the affiliate rail: Better Collective 48/Aspirant ("owns intent traffic, lacks licence/wallet/product"), Catena Media 30/Dormant — and the whole frame is "who owns the player when AI reshapes acquisition."

## P3 — Growth = LatAm + M&A "acquiring valuable technologies," with no visible target-scanning capability

- LatAm is now **Betsson's largest division** (36% of revenue, +32% YoY, Q2 2026); new **€75m credit facility explicitly for M&A** — "entering new markets or acquiring valuable technologies"; CEO eyeing further LatAm deals. ([iGB LatAm/M&A](https://igamingbusiness.com/strategy/betsson-latam-ma-q2/), transcript)
- Our pillar view is an M&A lens out of the box: 9 companies "one move away" (each labelled with the missing pillar), distressed/at-risk flags, AI-native assets as cheap capability grafts.

## P4 — The CEO is publicly watching the disruptor flank while staying out of it

- Post-Q4 call, 2026-02-06: prediction markets are "**a very interesting market segment**" but "**no plans to enter that business as of now**… we don't see that fit as well in our core markets' regulations." ([iGB](https://igamingbusiness.com/strategy/betsson-ceo-pontus-lindwall-prediction-markets/))
- Watching-without-entering requires a watchtower. Our sky's top of table **is** that flank: Underdog 73 (Imminent), Kalshi 69, Polymarket 64 — each with horizon and "what it still lacks."

## The reframe (proposal — see DECISIONS)

From "portfolio dashboard" → **the AI Radar Betsson's new AI org is hiring to build**:
1. **Betsson vantage** — Betsson as the gold reference star; every dossier's incumbent-impact line reads as "what this means for Betsson"; threat lenses on the funnel (P2), the product, the wallet.
2. **The question bar returns** (Gemini serverless, passcode) — de Lima's own words are the justification: agents that answer questions in minutes instead of dashboards. "What happens to Betsson's funnel if Google's AI Overviews reach 60% of gambling queries?"
3. **Three job-relevant lenses**: Acquisition-risk (affiliate/SEO exposure under AI search) · M&A radar (one-move-away + distressed + LatAm) · Watchtower (prediction markets & AI-natives, with horizons).
4. Application cover-note maps the artifact 1:1 onto the Head-of-AI JD sentence about trends → strategy → C-level communication.

## Tooling note

`agent-reach` v1.5.0 installed (web-read via Jina, RSS, GitHub, V2EX live). Its `install --env=auto` bootstrapper (Node/gh installs) was blocked by session permissions; LinkedIn/Twitter/Reddit channels additionally need the user's browser cookies — LinkedIn employee-post mining is therefore pending user cookie setup. Job-board + trade-press + company-site coverage above did not require it.
