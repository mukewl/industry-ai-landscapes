# iGaming calibration anchors

**Set from batch 01 (2026-07-13), QA-passed.** These are the scale. Every later batch must be scored consistently with them, and `qa_check.py` FAILS if any anchor drifts more than 8 EPI points. If a rescore is genuinely warranted, change it here deliberately and log it in DECISIONS.md — never let it drift silently.

| Company | Sector | EPI | W% / D% / AI% | Quadrant | Why it anchors |
|---|---|---|---|---|---|
| Flutter Entertainment plc | Operator (B2C) | 76 | 86 / 94 / 47 | Imminent threat | The ceiling. Owns audience, product and wallet, and is actively building the owned player surface (FanDuel One App, CME prediction JV). Nothing should score above this without an extraordinary case. |
| Polymarket | AI-native & prediction markets | 64 | 91 / 67 / 24 | Aspirant | Maximum willingness (91) — attacks the licensed model itself — with real but incomplete rails. The willingness ceiling. |
| Sportradar Group AG | Data & odds | 61 | 56 / 72 / 55 | Sleeping giant | The B2B firm that *could* go direct: strong rails and the best AI score in the batch, moderate appetite. |
| DraftKings Inc. | Operator (B2C) | 60 | 76 / 70 / 31 | Aspirant | High-willingness operator investing in owned demand, without Flutter's scale. |
| Bet365 Group Ltd | Operator (B2C) | 48 | 27 / 94 / 30 | Sleeping giant | **The size trap.** Enormous distribution (94) but almost no willingness to disrupt its own model. Use this to check that later batches score the *frame*, not company size. |
| Better Collective A/S | Affiliate & media | 48 | 75 / 20 / 40 | Aspirant | Owns intent traffic and wants the player, but has no licence, wallet or product (D 20). The "willing but unable" shape. |
| Entain plc | Operator (B2C) | 43 | 30 / 80 / 24 | Dormant | Incumbent scale, defensive posture. |
| Betsson AB (publ) | Operator (B2C) | 38 | 20 / 70 / 30 | Dormant | The named reference incumbent — scores LOW because it is the model being disrupted, not a disruptor. |
| Evolution AB (publ) | B2B supplier & platform | 26 | 9 / 58 / 16 | Dormant | Must-have content, deliberately no player-facing rails (D2 platform 1, D4 payments 0) and near-zero willingness (9). |
| Rithmm, Inc. | AI-native & prediction markets | 26 | 35 / 11 / 20 | Dormant | The floor. A small AI betting tool — stops later batches inflating early-stage startups. |

## Calibration notes for future batches

- **Score the frame, not size.** Bet365 (94 distribution, EPI 48) vs DraftKings (70 distribution, EPI 60) is the reference pair. If a giant lands high on *willingness* without evidence of attacking the player-ownership model, it is mis-scored.
- **Incumbent operators cluster low-to-mid** (Betsson 38, Entain 43, Bet365 48). This is correct under this frame — they are the thing being disrupted. Do not "correct" them upward for being big.
- **Deviation from the pre-research expectation, accepted:** `seedlist.md` predicted Evolution would land *Sleeping giant*; researched scores put it at *Dormant* (EPI 26). This is defensible — under the player-ownership frame Evolution has no player-facing platform or payments rails at all. The researched value is the anchor; the prior was wrong.
- **AI scores run low across the board** (16–55, mean ~31). iGaming genuinely has little shipped agentic capability today; do not inflate AI scores to look modern. Sportradar (55) is currently the ceiling.
- Willingness is the widest-spread signal group (9–91) and is doing most of the discriminating work — as intended for a "who will attack the incumbent" frame.
