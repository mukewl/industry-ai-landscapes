# ============================================================
# TEMPLATE REFERENCE COPY (from the Amadeus travel-distribution project).
# This is WORKING code for the travel industry, shipped as the reference
# implementation. To adapt it to a new industry, follow the numbered steps
# in ../ADAPTATION-CHECKLIST.md (or ADAPTATION-CHECKLIST.md at template root)
# -- every industry-specific marker in this file is listed there by name.
# ============================================================
"""Build viz/dashboard.html - self-contained interactive dashboard.

Embeds data/companies.json + data/relationships.json into an HTML template.
Synergy combos and findings are summarized here (source of record: analysis/*.md).
Network tab = constellation redesign (2026-06-12 user spec): all companies as
sized stars, type-colored edges, acquisition clustering, light-up filters,
sector legend, ego-focus on click.

    python -X utf8 scripts/build_dashboard.py
"""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VIZ = ROOT / "viz"

companies = json.loads((DATA / "companies.json").read_text(encoding="utf-8"))
graph = json.loads((DATA / "relationships.json").read_text(encoding="utf-8"))
meta = json.loads((DATA / "extract_meta.json").read_text(encoding="utf-8"))


def first_num(v):
    """First number in a messy cell ('180000-190000', '~$702M revenue', 3200)."""
    if v is None:
        return None
    m = re.search(r"[\d][\d,]*\.?\d*", str(v).replace(",", ""))
    return float(m.group()) if m else None


def company_size(c):
    """Star radius proxy: $mn scale of the company, log-scaled. Fallback: headcount."""
    for k in ("market_cap_valuation_mn", "post_money_valuation_mn",
              "total_funding_raised_mn", "total_funding_mn"):
        v = first_num(c.get(k))
        if v and v > 0:
            return 2.0 + min(12.0, math.log10(v + 1) * 2.0)
    fte = first_num(c.get("ftes"))
    if fte and fte > 0:
        return 2.0 + min(12.0, math.log10(fte * 2 + 1) * 1.7)
    return 2.2


size_by = {c["company"]: round(company_size(c), 2) for c in companies}


def yes(v):
    return str(v).strip().lower() in ("y", "yes")


def sig_vec(c, prefix, n):
    """Signal vector w1..w5 / d1..d6 / ai1..ai7 by key prefix (robust to messy snake names)."""
    out = []
    for i in range(1, n + 1):
        key = next((k for k in c if re.match(rf"^{prefix}{i}_", k)), None)
        v = first_num(c.get(key)) if key else None
        out.append(min(5.0, max(0.0, v if v is not None else 0.0)))
    return out


def openai_dep(c):
    txt = (str(c.get("gen_ai_platform_partnerships") or "") + " " +
           str(c.get("existing_partnerships") or "")).lower()
    return 1 if ("openai" in txt or "chatgpt" in txt or "gpt-" in txt) else 0


# ---------------- globe: world wireframe + HQ geocoding ----------------
def world_polylines():
    """Decode world-atlas 110m topojson arcs into [[ [lon,lat], ... ], ...].
    Drawing the raw arcs gives all coastlines + country borders (no polygon
    assembly needed for a wireframe)."""
    wf = DATA / "world_110m.json"
    if not wf.exists():
        print("world_110m.json missing - globe ships graticule-only")
        return []
    topo = json.loads(wf.read_text(encoding="utf-8"))
    sc = topo["transform"]["scale"]; tr = topo["transform"]["translate"]
    lines = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((round(x * sc[0] + tr[0], 1), round(y * sc[1] + tr[1], 1)))
        # light simplification: keep every 2nd point on long arcs
        if len(pts) > 60:
            pts = pts[::2] + [pts[-1]]
        if len(pts) >= 2:
            lines.append([p for pt in pts for p in pt])  # flat [lon,lat,lon,lat...]
    return lines


CITIES = {  # (lat, lon)
    "mountain view": (37.4, -122.1), "san francisco": (37.8, -122.4), "palo alto": (37.4, -122.1),
    "bay area": (37.5, -122.2), "new york": (40.7, -74.0), "seattle": (47.6, -122.3),
    "boston": (42.4, -71.1), "denver": (39.7, -105.0), "chicago": (41.9, -87.6),
    "austin": (30.3, -97.7), "miami": (25.8, -80.2), "los angeles": (34.1, -118.2),
    "southlake": (33.0, -97.1), "mclean": (38.9, -77.2), "bentonville": (36.4, -94.2),
    "london": (51.5, -0.1), "berlin": (52.5, 13.4), "munich": (48.1, 11.6),
    "paris": (48.9, 2.4), "amsterdam": (52.4, 4.9), "barcelona": (41.4, 2.2),
    "madrid": (40.4, -3.7), "dublin": (53.3, -6.3), "zurich": (47.4, 8.5),
    "stockholm": (59.3, 18.1), "tel aviv": (32.1, 34.8), "brno": (49.2, 16.6),
    "gurugram": (28.5, 77.0), "gurgaon": (28.5, 77.0), "bangalore": (13.0, 77.6),
    "bengaluru": (13.0, 77.6), "mumbai": (19.1, 72.9), "new delhi": (28.6, 77.2),
    "delhi": (28.6, 77.2), "chennai": (13.1, 80.3), "hyderabad": (17.4, 78.5),
    "singapore": (1.35, 103.8), "tokyo": (35.7, 139.7), "seoul": (37.6, 127.0),
    "hong kong": (22.3, 114.2), "shanghai": (31.2, 121.5), "beijing": (39.9, 116.4),
    "hangzhou": (30.3, 120.2), "shenzhen": (22.5, 114.1), "sydney": (-33.9, 151.2),
    "melbourne": (-37.8, 145.0), "dubai": (25.2, 55.3), "abu dhabi": (24.5, 54.4),
    "riyadh": (24.7, 46.7), "jeddah": (21.5, 39.2), "cairo": (30.0, 31.2),
    "lagos": (6.5, 3.4), "nairobi": (-1.3, 36.8), "cape town": (-33.9, 18.4),
    "sao paulo": (-23.6, -46.6), "são paulo": (-23.6, -46.6), "mexico city": (19.4, -99.1),
    "buenos aires": (-34.6, -58.4), "toronto": (43.7, -79.4), "montreal": (45.5, -73.6),
    "vancouver": (49.3, -123.1), "amman": (32.0, 35.9), "istanbul": (41.0, 28.9),
    "warsaw": (52.2, 21.0), "tallinn": (59.4, 24.8), "vilnius": (54.7, 25.3),
    "lisbon": (38.7, -9.1), "oslo": (59.9, 10.8), "copenhagen": (55.7, 12.6),
    "helsinki": (60.2, 24.9), "brussels": (50.8, 4.4), "vienna": (48.2, 16.4),
    "ho chi minh": (10.8, 106.7), "hanoi": (21.0, 105.9), "jakarta": (-6.2, 106.8),
    "kuala lumpur": (3.1, 101.7), "manila": (14.6, 121.0), "bangkok": (13.8, 100.5),
    "dhaka": (23.8, 90.4), "taipei": (25.0, 121.6),
}
COUNTRIES = {
    "usa": (39.8, -98.6), "united states": (39.8, -98.6), "us": (39.8, -98.6),
    "uk": (52.6, -1.5), "united kingdom": (52.6, -1.5), "england": (52.6, -1.5),
    "india": (22.6, 79.0), "china": (35.0, 104.0), "germany": (51.1, 10.4),
    "france": (46.6, 2.4), "spain": (40.2, -3.6), "italy": (42.8, 12.6),
    "netherlands": (52.2, 5.5), "belgium": (50.6, 4.6), "switzerland": (46.8, 8.2),
    "austria": (47.6, 14.1), "sweden": (62.8, 16.7), "norway": (61.2, 9.5),
    "denmark": (55.9, 9.0), "finland": (64.5, 26.0), "poland": (52.1, 19.4),
    "czech republic": (49.8, 15.5), "czechia": (49.8, 15.5), "estonia": (58.7, 25.5),
    "lithuania": (55.3, 23.9), "latvia": (56.9, 24.9), "ireland": (53.2, -8.1),
    "portugal": (39.6, -8.0), "greece": (39.0, 22.0), "hungary": (47.2, 19.4),
    "romania": (45.8, 24.9), "bulgaria": (42.8, 25.2), "croatia": (45.1, 15.2),
    "serbia": (44.0, 20.9), "ukraine": (49.0, 31.4), "russia": (61.5, 105.0),
    "turkey": (39.0, 35.0), "israel": (31.4, 35.0), "uae": (24.0, 54.0),
    "united arab emirates": (24.0, 54.0), "saudi arabia": (24.0, 45.0),
    "qatar": (25.3, 51.2), "bahrain": (26.0, 50.5), "kuwait": (29.3, 47.5),
    "oman": (21.0, 57.0), "jordan": (31.2, 36.5), "lebanon": (33.9, 35.9),
    "egypt": (26.5, 30.0), "morocco": (31.8, -7.1), "tunisia": (34.1, 9.6),
    "algeria": (28.0, 2.6), "nigeria": (9.1, 8.7), "kenya": (0.2, 37.9),
    "ghana": (7.9, -1.0), "ethiopia": (9.1, 40.5), "rwanda": (-2.0, 29.9),
    "tanzania": (-6.4, 34.9), "uganda": (1.4, 32.3), "senegal": (14.4, -14.5),
    "south africa": (-29.0, 25.1), "zimbabwe": (-19.0, 29.9), "zambia": (-13.5, 27.8),
    "japan": (36.6, 138.2), "south korea": (36.4, 127.8), "korea": (36.4, 127.8),
    "taiwan": (23.7, 121.0), "hong kong": (22.3, 114.2), "singapore": (1.35, 103.8),
    "malaysia": (4.1, 109.1), "indonesia": (-2.5, 118.0), "thailand": (15.1, 101.0),
    "vietnam": (16.0, 106.0), "philippines": (12.9, 121.8), "cambodia": (12.5, 104.9),
    "bangladesh": (23.7, 90.4), "pakistan": (30.4, 69.4), "sri lanka": (7.9, 80.7),
    "nepal": (28.4, 84.1), "australia": (-25.3, 133.8), "new zealand": (-41.8, 172.8),
    "canada": (56.1, -106.3), "mexico": (23.6, -102.6), "brazil": (-10.8, -52.9),
    "argentina": (-34.0, -64.0), "chile": (-35.7, -71.5), "colombia": (4.6, -74.3),
    "peru": (-9.2, -75.0), "uruguay": (-32.5, -55.8), "ecuador": (-1.4, -78.4),
    "iceland": (64.9, -18.6), "luxembourg": (49.8, 6.1), "cyprus": (35.1, 33.2),
    "malta": (35.9, 14.4), "monaco": (43.7, 7.4), "kazakhstan": (48.0, 66.9),
    "côte d'ivoire": (7.5, -5.5), "ivory coast": (7.5, -5.5),
    "scotland": (56.5, -4.2), "wales": (52.1, -3.8), "georgia": (42.0, 43.5),
}


def hq_geo(name, hq):
    """Deterministic (lat, lon) for an HQ string, or None."""
    if not hq:
        return None
    txt = str(hq).lower().replace("(", " ").replace(")", " ")
    first = txt.split("/")[0]  # multi-HQ: take the first
    hit = None
    for city, ll in CITIES.items():
        if city in first:
            hit = ll; break
    if not hit:
        for country, ll in COUNTRIES.items():
            for part in reversed([p.strip() for p in first.split(",")]):
                if part == country or part.endswith(" " + country):
                    hit = ll; break
            if hit:
                break
    if not hit:  # last resort: word-boundary country match anywhere in full text
        for country in sorted(COUNTRIES, key=len, reverse=True):
            if re.search(r"\b" + re.escape(country) + r"\b", txt):
                hit = COUNTRIES[country]; break
    if not hit:
        return None
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
    jla = ((h % 1000) / 1000 - 0.5) * 3.0
    jlo = (((h // 1000) % 1000) / 1000 - 0.5) * 3.0
    return (round(hit[0] + jla, 2), round(hit[1] + jlo, 2))

# ---- compact company payload (full text for drawer) ----
comp = []
for c in companies:
    comp.append({
        "n": c.get("company"),
        "sec": c.get("source_sector_taxonomy") or "?",
        "hq": c.get("hq") or "",
        "epi": c.get("entry_potential_index"),
        "t": c.get("threat_tier") or "?",
        "q": c.get("quadrant") or "",
        "hz": c.get("horizon") or "",
        "sv": c.get("survival_tier") or "",
        "act": c.get("final_action") or "",
        "w": c.get("willingness_pct"),
        "d": c.get("distribution_readiness_pct"),
        "ai": c.get("ai_readiness_pct"),
        "pc": c.get("position_class") or "",
        "imp": c.get("impact_on_amadeus_line") or "",
        "gap": c.get("residual_gap_what_they_d_need") or "",
        "par": c.get("existing_partnerships") or "",
        "fin": c.get("financial_health_pct"),
        "rev": c.get("revenue_traction") or "",
        # scenario-engine inputs
        "sig": {"w": sig_vec(c, "w", 5), "d": sig_vec(c, "d", 6), "ai": sig_vec(c, "ai", 7)},
        "mor": 1 if yes(c.get("merchant_of_record")) else 0,
        "ndc": 1 if yes(c.get("ndc")) else 0,
        "protos": {p: (1 if yes(c.get(p)) else 0) for p in ("mcp", "a2a", "ucp", "acp")},
        "oai": openai_dep(c),
        "jc": [1 if yes(c.get(k)) else 0 for k in
               ("inspiration", "research_planning", "shopping_comparison", "booking",
                "payment", "in_trip_experience", "post_trip_loyalty")],
        "geo": hq_geo(c.get("company"), c.get("hq")),
        "biz": (c.get("business_model_notes") or "")[:300],
    })

# ---- graph payload with sizes + edge groups ----
gnodes = []
for n in graph["nodes"]:
    if n.get("in_dataset"):
        gnodes.append({"id": n["id"], "ds": 1, "sec": n.get("sector") or "Other",
                       "tier": n.get("threat_tier") or "", "sz": size_by.get(n["id"], 2.2)})
    else:
        sz = 14.0 if n.get("is_amadeus") else round(2.0 + math.sqrt(n.get("mentions", 1)) * 0.9, 2)
        gnodes.append({"id": n["id"], "ds": 0, "ama": 1 if n.get("is_amadeus") else 0, "sz": sz})

ACQ = {"acquired", "attempted_acquisition", "parent_brand"}
gedges = []
known = {n["id"] for n in graph["nodes"]}
extra = {}  # single-mention externals dropped by the extractor's noise threshold
for e in graph["edges"]:
    grp = "acq" if e["type"] in ACQ else ("inv" if e["type"] == "investor" else "part")
    ama = 1 if (str(e["source"]).lower().startswith("amadeus") or str(e["target"]).lower().startswith("amadeus")) else 0
    gedges.append({"s": e["source"], "t": e["target"], "g": grp, "a": ama, "ty": e["type"], "raw": e.get("raw", "")[:160]})
    for end in (e["source"], e["target"]):
        if end not in known:
            extra[end] = extra.get(end, 0) + 1
for name, n_mentions in extra.items():
    gnodes.append({"id": name, "ds": 0, "ama": 0, "sz": 1.7})

TOP10 = ["Google", "Sabre (Mosaic)", "Capital One", "Expedia Group", "Navan",
         "Alibaba / Fliggy", "Spotnana", "Accelya", "Trip.com Group", "Verteil Technologies"]

COMBOS = [
 {"id":"C1","title":"The United Airlines constellation","risk":"high",
  "who":"United Airlines Ventures × Blockskye + Mindtrip + Layla; United on Accelya offer-order; Duffel content airline; Bilt transfer partner",
  "what":"An airline quietly seeding every distribution layer: front-end (Mindtrip/Layla), offer-order (Accelya), settlement (Blockskye), loyalty demand (Bilt). Summed, it is a full GDS-bypass stack — never announced as one.",
  "signals":"UA Ventures follow-ons · Blockskye corporate wins · Mindtrip adding United NDC-direct",
  "counter":"Track carriers' venture portfolios as distribution intel; offer United better agentic offer-order economics before the stack closes."},
 {"id":"C2","title":"OpenAI + Stripe + one content rail = the S1 trigger","risk":"high",
  "who":"OpenAI (most-connected node, deg 45; co-owns ACP with Stripe) + Stripe + Duffel / Kiwi TEQUILA / Spotnana",
  "what":"ChatGPT-scale demand + ACP checkout + REST-native content = the 'Agentic OTA' scenario shipping in a quarter. Only the (reversible) March-2026 checkout walk-back holds it back.",
  "signals":"ACP adds a travel content partner · ChatGPT travel apps gain booking permissions · Stripe travel-merchant tooling",
  "counter":"Be the content rail inside ACP/Apps SDK first — one OpenAI supply deal sits beneath ~50 landscape players (F11)."},
 {"id":"C3","title":"The distressed-NDC roll-up","risk":"high",
  "who":"Any consolidator (Flight Centre owns TPConnects; Vista owns Accelya; PE; a fintech) × Verteil + Paxport + AirGateway + Mystifly (+ Otto, BizTrip AI)",
  "what":"~$50–100M of distressed assets = global NDC-bypass coverage that took each player a decade to build. The threat only exists in aggregate (F5).",
  "signals":"Flight Centre M&A · Vista bolt-ons · any fintech buying an NDC aggregator",
  "counter":"Pre-emptively acquire the 1–2 strategic assets (Verteil's new-carrier mandates are the crown jewel) or lock their airline contracts."},
 {"id":"C4","title":"Tata's Indian sovereign stack","risk":"med",
  "who":"Tata Neu (demand+loyalty+payments) + Air India (Tata-owned supply, Amadeus customer) + Verteil / TPConnects (both already serve Air India)",
  "what":"India's flag carrier selling through its conglomerate's super-app over an NDC rail — in the market with the highest High-tier density (F9). Routes around the airline's distribution team entirely.",
  "signals":"Tata Neu international flight features · Air India NDC-direct share · Verteil/TPConnects scope expansion",
  "counter":"Defend Air India at Tata-group level; offer Tata Neu embedded content directly."},
 {"id":"C5","title":"Apple — the sleeping full stack (hypothesis)","risk":"low",
  "who":"Apple (demand + settlement, missing only content) + Wallet mDL identity + one Expedia-style white-label deal",
  "what":"A billion devices + Apple Pay + boarding passes/IDs in Wallet + Siri-LLM. One content deal makes 'book in Wallet' real with zero infra build. Appears in nobody's threat model — exactly the profile this workstream exists to catch.",
  "signals":"Apple Intelligence commerce APIs · Wallet bookable surfaces · any travel-content hire",
  "counter":"Costs nothing to put on the radar with a named trigger."},
 {"id":"C6","title":"The Saudi state-coordinated stack","risk":"med",
  "who":"Riyadh Air + Almosafer/Seera (61% Saudi OTA air GBV) + Verteil (launch NDC aggregator) + TOURISE/Globant + AROYA; PIF capital throughout",
  "what":"A state aligning carrier, dominant OTA, NDC rail and a national agentic-tourism platform around Vision-2030 — distribution architecture decided top-down, vendor choices made once.",
  "signals":"TOURISE platform RFPs · Almosafer sourcing shifts · Riyadh Air NDC-direct share vs Amadeus agreement",
  "counter":"Expand the existing Riyadh Air agreement into a Kingdom-level platform play before the stack standardizes on Verteil+Sabre."},
 {"id":"C7","title":"Emerging-market wallet × emerging-market rail","risk":"med",
  "who":"Paytm/Niyo + TBO Tek (159k agents; near-exact complementary profile); MoMo + a SEA aggregator; Nubank+Hopper = the live LATAM instance",
  "what":"Wallet demand + B2B content rail in the same geography = a national full stack that never touches a Western GDS.",
  "signals":"TBO API deals with non-travel platforms · Paytm Checkin international air · wallets hiring travel-supply teams",
  "counter":"S3 no-regret move: embed Amadeus content into wallet checkouts first; partner TBO before it becomes someone's exclusive rail."},
 {"id":"C8","title":"Korea/Japan platform consolidation","risk":"med",
  "who":"Naver/Line (missing content) + Yanolja (Dist 73/AI 27 mirror profile; controls hotel supply via YCS) — SoftBank sits on both sides",
  "what":"Korea/Japan messaging+search demand and payments + the dominant hospitality supply layer = a regional full stack. Filed under different analyst buckets, same value chain.",
  "signals":"SoftBank-brokered cooperation · Yanolja air ambitions beyond Interpark · Line/Naver travel mini-apps",
  "counter":"Anchor Yanolja's channel manager to Amadeus economics; court Rakuten as the counterweight."},
 {"id":"C9","title":"BizTrip AI — the one cheap AI asset (hypothesis)","risk":"low",
  "who":"BizTrip AI: the ONLY company of 553 with AI≥60 / Dist<45 / High tier (AI 72, Dist 43) — and At-risk financially; already Sabre-partnered",
  "what":"Whoever buys it grafts a ready agentic layer onto a distribution-strong/AI-weak base (TBO? Amex GBT? Serko? Sabre itself?) and jumps quadrants overnight.",
  "signals":"Its funding news · Sabre deepening partnership into ownership",
  "counter":"Cheap optionality — evaluate acquiring it (or equivalent) for Cytric's agentic refresh."},
]

FINDINGS = [
 {"id":"F1","s":"retracted","t":"Blind-spot list","x":"RETRACTED — amadeus_knows_it column never completed (user-confirmed); N often means 'not filled in'."},
 {"id":"F2","s":"verified","t":"The Capital One constellation","x":"Capital One bought Hopper's portal tech + 150 staff (Mar 2026) AND is acquiring Brex ($5.15B); Brex Travel runs on Spotnana incl. NDC-direct with American. Three threat rows converging into one bank-owned consumer+corporate travel stack. Scenario S3 assembling now."},
 {"id":"F3","s":"verified","t":"The rail beneath the rails","x":"Front-end logos are interchangeable; a few supply rails power them: Spotnana → Brex/Otto/Direct Travel/JTB/Cadence; Duffel → Rippling; Sabre → Mindtrip; Expedia → Walmart+/Bilt/Alexa+; Priceline → Ramp; Hopper HTS → Nubank. Compete for the rail role, not against each logo."},
 {"id":"F4","s":"fixed","t":"Payments-led entry was under-tiered","x":"Klarna (EPI 62, Imminent-threat quadrant) and PayPal (load-bearing in the live Sabre+Mindtrip stack) were tiered Low along with 8 other indirect entrants. FIXED: 10 companies re-tiered Low→Medium in the workbook with audit notes (D5)."},
 {"id":"F5","s":"verified","t":"Distressed-but-strategic = acquisition radar","x":"High-threat + At-risk/Distressed/Defunct = targets, not competitors: Verteil, Otto, Paxport, AirGateway, Wakanow, Buzz, Orbzii, BizTrip AI, Voyagier. Whoever consolidates them assembles bypass capability fast — Amadeus could too."},
 {"id":"F6","s":"fixed","t":"Riyadh Air tier was misclassified","x":"Signed Amadeus customer (Aug 2025) multi-homing across Amadeus + Sabre + Verteil. FIXED: re-tiered High→Medium with reviewer note (D10). The watch signal is sourcing drift, not entry."},
 {"id":"F7","s":"verified","t":"Protocol adoption = 2× threat concentration","x":"31 protocol adopters avg EPI 53 vs dataset 33; ACP's 8 adopters are ALL fintech and were ALL tiered Low (now fixed). WebMCP/NLWeb: zero adoption in 553 — drop as watch signals."},
 {"id":"F8","s":"retracted","t":"Blind spot is travel-native","x":"RETRACTED — built on the incomplete amadeus_knows_it column (see F1)."},
 {"id":"F9","s":"verified","t":"India is the epicenter","x":"India: 25% of its 48 companies are High-tier vs 15% base rate (12 companies). Saudi 3/6. USA below base rate (13%) despite most absolute Highs. Threat density concentrates where Amadeus incumbency is weakest."},
 {"id":"F10","s":"verified","t":"Merchant-of-record tracks threat tier","x":"MoR=Y: 65% of High tier vs 40% of Low. Holding the money is a stronger structural threat marker than most AI fields. Weight MoR in re-scoring; Outpayce is defensive infrastructure."},
 {"id":"F11","s":"verified","t":"The landscape runs on OpenAI 2:1","x":"Model/platform dependencies: OpenAI 51, Google 25, Anthropic 5. OpenAI is also the most-connected graph node (deg 45). One Amadeus↔OpenAI supply deal would sit beneath ~50 players; equally, OpenAI policy shifts are systemic risk to S1."},
 {"id":"F12","s":"fixed","t":"Kiwi.com / Skypicker duplicate","x":"Skypicker s.r.o. = Kiwi.com's pre-2016 legal name. FIXED: flagged DUPLICATE in workbook, excluded from extracts; dataset 553 (D6)."},
 {"id":"F13","s":"verified","t":"The lock-and-key pattern","x":"Two mirror clusters strong on 2-of-3 pillars: fintechs missing only content (Bilt, Paytm, Ramp, Grab, Revolut, Uber, Apple…) × travel rails missing only settlement (Sabre, Accelya, Spotnana, Verteil…). Any cross-pairing = full no-GDS stack. Six pairings already live."},
 {"id":"F14","s":"verified","t":"United assembling bypass via venture portfolio","x":"UA Ventures: Blockskye + Mindtrip + Layla backing; United on Accelya, Duffel, Bilt. Every distribution layer seeded around one carrier. Monitor carriers' VC arms as distribution strategy."},
]

# ---- scenario presets (sources: analysis/03 combos C1-C9, workbook Scenarios S1-S4) ----
# move types: merge{a,b,mode:acquire|partner} · adopt{a,proto} · kill{a} · ama{kind,target?}
PRESETS = [
 {"id":"C1","name":"C1 · United constellation closes","moves":[
   {"type":"merge","a":"Mindtrip","b":"Blockskye","mode":"partner"},
   {"type":"merge","a":"Mindtrip","b":"Layla","mode":"partner"}],
  "note":"United's venture bets compose into one front-end + settlement stack."},
 {"id":"C2","name":"C2 · OpenAI + Stripe + content rail","moves":[
   {"type":"merge","a":"OpenAI","b":"Stripe","mode":"partner"},
   {"type":"merge","a":"OpenAI","b":"Duffel","mode":"partner"},
   {"type":"adopt","a":"OpenAI","proto":"acp"}],
  "note":"ChatGPT checkout re-enabled with a REST content rail = the S1 trigger."},
 {"id":"C3","name":"C3 · Distressed-NDC roll-up","moves":[
   {"type":"merge","a":"TPConnects","b":"Verteil Technologies","mode":"acquire"},
   {"type":"merge","a":"TPConnects","b":"Paxport","mode":"acquire"},
   {"type":"merge","a":"TPConnects","b":"AirGateway","mode":"acquire"},
   {"type":"merge","a":"TPConnects","b":"Mystifly","mode":"acquire"}],
  "note":"One consolidator buys the distressed NDC rails (Flight Centre owns TPConnects)."},
 {"id":"C4","name":"C4 · Tata Indian sovereign stack","moves":[
   {"type":"merge","a":"Tata Neu","b":"Verteil Technologies","mode":"partner"}],
  "note":"Tata Neu sells Air India over an NDC rail that bypasses the GDS."},
 {"id":"C5","name":"C5 · Apple wakes up (hypothesis)","moves":[
   {"type":"merge","a":"Apple","b":"Expedia Group","mode":"partner"}],
  "note":"One white-label deal makes 'book in Wallet' real."},
 {"id":"C6","name":"C6 · Saudi state stack","moves":[
   {"type":"merge","a":"Riyadh Air","b":"Almosafer","mode":"partner"},
   {"type":"merge","a":"Almosafer","b":"Verteil Technologies","mode":"partner"}],
  "note":"Carrier + dominant OTA + NDC rail aligned top-down by the state."},
 {"id":"C7","name":"C7 · Wallet × rail (Paytm + TBO)","moves":[
   {"type":"merge","a":"Paytm (Checkin)","b":"TBO Tek","mode":"acquire"}],
  "note":"Indian wallet demand + 159k-agent content rail in one market."},
 {"id":"C8","name":"C8 · Naver acquires Yanolja","moves":[
   {"type":"merge","a":"Naver / Line","b":"Yanolja","mode":"acquire"}],
  "note":"Korea/Japan platform + the hotel supply layer; SoftBank on both sides."},
 {"id":"C9","name":"C9 · Someone buys BizTrip AI","moves":[
   {"type":"merge","a":"TBO Tek","b":"BizTrip AI","mode":"acquire"}],
  "note":"The one cheap AI-strong asset grafted onto a distribution-strong base."},
 {"id":"S1","name":"S1 · Agentic OTA world","moves":[
   {"type":"adopt","a":"OpenAI","proto":"acp"},
   {"type":"adopt","a":"Perplexity","proto":"acp"},
   {"type":"adopt","a":"Layla","proto":"acp"},
   {"type":"adopt","a":"Mindtrip","proto":"acp"},
   {"type":"merge","a":"OpenAI","b":"Stripe","mode":"partner"}],
  "note":"AI assistants become the booking channel; checkout APIs everywhere."},
 {"id":"S2","name":"S2 · Big Tech buys in (Google × Expedia)","moves":[
   {"type":"merge","a":"Google","b":"Expedia Group","mode":"acquire"}],
  "note":"The hyperscaler shock scenario — demand + supply in one stack."},
 {"id":"S3","name":"S3 · Fintech super-apps bundle travel","moves":[
   {"type":"merge","a":"Revolut","b":"Kiwi.com","mode":"acquire"},
   {"type":"merge","a":"Paytm (Checkin)","b":"TBO Tek","mode":"acquire"}],
  "note":"Payments layer captures travel at checkout in two regions at once."},
 {"id":"S4","name":"S4 · GDS-augmented world (defense holds)","moves":[
   {"type":"ama","kind":"agent-rail"}],
  "note":"Amadeus ships the agentic stack first; incumbents adopt AI on GDS rails."},
 {"id":"AM1","name":"Amadeus · ships the agent rail","moves":[{"type":"ama","kind":"agent-rail"}],
  "note":"Production MCP/agent interfaces + Outpayce checkout before Sabre locks the role."},
 {"id":"AM2","name":"Amadeus · acquires Verteil","moves":[{"type":"ama","kind":"acquire","target":"Verteil Technologies"}],
  "note":"Buys the new-carrier NDC mandates (Riyadh Air, Turkish, Air India)."},
 {"id":"AM3","name":"Amadeus · OpenAI supply deal","moves":[{"type":"ama","kind":"openai-supply"}],
  "note":"Amadeus content inside ChatGPT/ACP — sits beneath ~50 OpenAI-dependent players."},
]
saved_dir = DATA / "scenarios" / "saved"
if saved_dir.exists():
    for f in sorted(saved_dir.glob("*.json")):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            if s.get("name") and s.get("moves"):
                PRESETS.append({"id": "USER", "name": "★ " + s["name"], "moves": s["moves"],
                                "note": s.get("note", "saved scenario")})
        except Exception as ex:
            print(f"skipping bad saved scenario {f.name}: {ex}")

WORLD = world_polylines()
geo_n = sum(1 for c in comp if c["geo"])
print(f"geocoded {geo_n}/{len(comp)} companies; world arcs: {len(WORLD)}")
if geo_n < len(comp):
    missing = [c["n"] + " (" + (c["hq"] or "no HQ") + ")" for c in comp if not c["geo"]]
    print("unplaced:", "; ".join(missing[:15]), "..." if len(missing) > 15 else "")

payload = {
    "meta": {"count": len(comp), "date": meta.get("extracted_on"), "sha": meta.get("sha256", "")[:12],
             "geoN": geo_n},
    "world": WORLD,
    "presets": PRESETS,
    "companies": comp,
    "top10": TOP10,
    "nodes": gnodes,
    "edges": gedges,
    "combos": COMBOS,
    "findings": FINDINGS,
}

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Amadeus AI Disruption Landscape — Dashboard</title>
<style>
:root{--bg:#0e1117;--panel:#161b25;--panel2:#1d2433;--line:#2a3245;--tx:#dde3ee;--tx2:#8b94a7;
--hi:#e74c5e;--med:#e7a93c;--low:#4f8edc;--ok:#3fbf7f;--gold:#f0c84b;--ac:#6ea8fe;
--ease:cubic-bezier(.22,.61,.36,1);--ease-soft:cubic-bezier(.34,1.2,.64,1);--t1:.15s;--t2:.28s;--t3:.42s}
*{box-sizing:border-box;margin:0;padding:0}
@keyframes viewIn{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
@keyframes fadeSwap{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
@keyframes shimmer{from{background-position:0% 0}to{background-position:-200% 0}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
body{background:var(--bg);color:var(--tx);font:14px/1.5 "Segoe UI",system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;gap:18px;padding:10px 18px;border-bottom:1px solid var(--line);background:var(--panel)}
header h1{font-size:16px;font-weight:600}
header .stamp{color:var(--tx2);font-size:12px;margin-left:auto}
nav{display:flex;gap:4px}
nav button{background:none;border:1px solid transparent;color:var(--tx2);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px;transition:background var(--t1) var(--ease),color var(--t1) var(--ease),border-color var(--t1) var(--ease)}
nav button:hover{color:var(--tx);background:#1a2130}
nav button.on{background:var(--panel2);color:var(--tx);border-color:var(--line)}
main{flex:1;overflow:hidden;display:flex}
.view{flex:1;overflow:auto;padding:16px;display:none}
.view.on{display:block;animation:viewIn var(--t2) var(--ease)}
#vNet.on{display:flex;padding:0;animation:none}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
input[type=text],select{background:var(--panel2);border:1px solid var(--line);color:var(--tx);padding:6px 10px;border-radius:8px;font-size:13px;outline:none}
.chip{padding:4px 10px;border-radius:20px;border:1px solid var(--line);background:var(--panel2);color:var(--tx2);cursor:pointer;font-size:12px;user-select:none}
.chip.on{color:#fff;border-color:var(--ac);background:#24304a}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;margin-bottom:14px}
.tcard{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px;cursor:pointer}
.tcard:hover{border-color:var(--ac)}
.tcard .rk{color:var(--tx2);font-size:11px}
.tcard .nm{font-weight:600;font-size:13px;margin:2px 0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{position:sticky;top:0;text-align:left;background:var(--panel);color:var(--tx2);font-weight:500;padding:8px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap}
td{padding:7px 8px;border-bottom:1px solid #1b2230;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px}
tbody tr{cursor:pointer}tbody tr:hover{background:#1a2130}
.pill{display:inline-block;padding:1px 9px;border-radius:12px;font-size:11px;font-weight:600}
.pHigh{background:#3a1820;color:#ff8e9d}.pMedium{background:#39301a;color:#ffd479}.pLow{background:#16263c;color:#7fb4f5}.pq{background:#222a3c;color:#9fb0cc}
.epibar{display:inline-block;width:56px;height:7px;background:#222a3a;border-radius:4px;vertical-align:middle;margin-right:6px}
.epibar i{display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,#4f8edc,#e7a93c 60%,#e74c5e)}
#drawer{position:fixed;top:0;right:-620px;width:600px;height:100vh;background:var(--panel);border-left:1px solid var(--line);transition:right var(--t3) var(--ease);z-index:30;display:flex;flex-direction:column;box-shadow:-12px 0 40px #0009}
#drawer.open{right:0}
#drawer.open .db{animation:fadeSwap var(--t3) var(--ease)}
#drawer .dh{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;align-items:flex-start;gap:10px}
#drawer .dh h2{font-size:17px}
#drawer .db{padding:14px 18px;overflow:auto;font-size:13px}
#drawer .db h4{color:var(--tx2);font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin:14px 0 4px}
#drawer .db p{white-space:pre-wrap}
.x{margin-left:auto;background:none;border:none;color:var(--tx2);font-size:20px;cursor:pointer}
.kv{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.kv span{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:2px 8px;font-size:12px;color:var(--tx2)}
.kv b{color:var(--tx)}
#netwrap{flex:1;position:relative;background:radial-gradient(ellipse at 55% 42%, #0d1430 0%, #070b18 55%, #04060e 100%)}
#cv{position:absolute;inset:0;width:100%;height:100%}
#netctl{position:absolute;top:12px;left:12px;background:rgba(9,13,26,.88);backdrop-filter:blur(6px);border:1px solid #232c48;border-radius:12px;padding:12px;z-index:5;width:262px;max-height:calc(100% - 24px);overflow:auto}
#netctl h5{font-size:10px;letter-spacing:1.4px;color:#6f7ba0;margin:10px 0 5px;text-transform:uppercase}
#netctl h5:first-child{margin-top:0}
.fbtn{display:flex;align-items:center;gap:8px;width:100%;text-align:left;background:none;border:1px solid transparent;border-radius:8px;color:#aab4d4;padding:5px 8px;cursor:pointer;font-size:12.5px}
.fbtn:hover{background:#141b33}
.fbtn.on{background:#1a2342;border-color:#33406e;color:#fff}
.fbtn .dot{width:18px;height:3px;border-radius:2px;flex:none}
.fbtn .cnt{margin-left:auto;color:#5f6a8e;font-size:11px}
.lgrow{display:flex;align-items:center;gap:8px;font-size:11.5px;color:#9aa4c4;padding:2.5px 2px}
.lgrow .st{width:11px;height:11px;border-radius:50%;flex:none;box-shadow:0 0 6px currentColor}
#tip{position:absolute;pointer-events:none;background:rgba(5,8,18,.92);border:1px solid #2b3454;padding:5px 9px;border-radius:7px;font-size:12px;display:none;z-index:6;max-width:260px}
#tip b{color:#fff}#tip .m{color:#8b94a7;font-size:11px}
#netfoot{position:absolute;bottom:10px;left:12px;color:#5f6a8e;font-size:11px;z-index:5}
#focusbar{position:absolute;top:12px;left:50%;transform:translateX(-50%);background:rgba(9,13,26,.9);border:1px solid #33406e;border-radius:20px;padding:5px 14px;z-index:6;font-size:12.5px;display:none;align-items:center;gap:10px}
#focusbar b{color:#f0c84b}
#focusbar button{background:none;border:none;color:#8b94a7;cursor:pointer;font-size:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:12px}
.combo,.fcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.combo h3{font-size:14px;margin-bottom:6px}
.combo .sec,.fcard p{color:var(--tx2);font-size:12.5px;margin-top:6px}
.combo .sec b,.fcard b{color:var(--tx)}
.badge{float:right;font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;letter-spacing:.5px}
.bhigh{background:#3a1820;color:#ff8e9d}.bmed{background:#39301a;color:#ffd479}.blow{background:#16263c;color:#7fb4f5}
.bverified{background:#15301f;color:#5fd99a}.bfixed{background:#16263c;color:#7fb4f5}.bhypothesis{background:#39301a;color:#ffd479}.bretracted{background:#3a1820;color:#ff8e9d}
.fcard.retracted{opacity:.55}
small.cnt{color:var(--tx2)}
/* ---- company card ---- */
.gaugerow{display:flex;gap:10px;margin:12px 0 4px}
.gauge{flex:1;text-align:center}
.gauge .ring{width:64px;height:64px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;position:relative}
.gauge .ring i{position:absolute;inset:6px;border-radius:50%;background:var(--panel);display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:700;font-size:15px}
.gauge .gl{font-size:10.5px;color:var(--tx2);margin-top:4px;text-transform:uppercase;letter-spacing:.6px}
.gauge .gp{font-size:10px;color:#5f6a8e}
.cardgrid{display:grid;grid-template-columns:1fr 130px;gap:12px;align-items:start}
.qmap{width:130px;height:130px;background:#101626;border:1px solid var(--line);border-radius:10px;position:relative;overflow:hidden}
.qmap .ql{position:absolute;font-size:8px;color:#566;padding:3px;color:#5f6a8e}
.qmap .qdot{position:absolute;width:11px;height:11px;border-radius:50%;background:#fff;box-shadow:0 0 10px #fff;transform:translate(-50%,50%)}
.qmap .gridl{position:absolute;background:#232c48}
.chiprow{display:flex;gap:5px;flex-wrap:wrap;margin:6px 0}
.pchip{padding:3px 10px;border-radius:14px;font-size:11px;font-weight:600;border:1px solid var(--line);color:#5f6a8e;background:#141b33}
.pchip.onp{color:#5fd99a;border-color:#1f4a34;background:#11251b}
.pchip.offp{text-decoration:line-through;opacity:.55}
.sgrp{margin:8px 0 2px;font-size:10px;letter-spacing:1px;color:#6f7ba0;text-transform:uppercase}
.sbar{display:flex;align-items:center;gap:8px;margin:2.5px 0}
.sbar .sl{width:148px;font-size:11px;color:var(--tx2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sbar .st2{flex:1;height:6px;background:#1a2235;border-radius:3px;overflow:hidden}
.sbar .st2 i{display:block;height:100%;border-radius:3px}
.sbar .sv{width:14px;font-size:10.5px;color:#8b94a7;text-align:right}
.jstrip{display:flex;gap:3px;margin:6px 0}
.jseg{flex:1;text-align:center;font-size:9.5px;padding:5px 2px;border-radius:6px;background:#141b33;color:#4a5470;border:1px solid #1d2742}
.jseg.onj{background:#152a3d;color:#7fb4f5;border-color:#27496b}
.callout{border-left:3px solid var(--ac);background:#131a2c;border-radius:0 8px 8px 0;padding:9px 12px;margin:8px 0;font-size:12.5px;color:#b9c2d8;white-space:pre-wrap}
.callout.imp{border-color:#e74c5e}.callout.gap{border-color:#e7a93c}.callout.biz{border-color:#4f8edc}
.connrow{display:flex;align-items:center;gap:7px;padding:4px 6px;border-radius:7px;cursor:pointer;font-size:12px}
.connrow:hover{background:#1a2235}
.connrow .cdot{width:8px;height:8px;border-radius:50%;flex:none}
.connrow .cty{margin-left:auto;font-size:10px;color:#5f6a8e}
.finbar{height:8px;background:#1a2235;border-radius:4px;overflow:hidden;margin:4px 0}
.finbar i{display:block;height:100%;background:linear-gradient(90deg,#e74c5e,#e7a93c 50%,#3fbf7f)}
.abtn{flex:1;background:#1a2342;border:1px solid #33406e;color:#dde3ee;border-radius:9px;padding:8px;cursor:pointer;font-size:12.5px;text-align:center}
.abtn:hover{background:#24304f}
#modeToggle{position:absolute;top:12px;right:14px;z-index:6;display:flex;background:rgba(9,13,26,.88);border:1px solid #232c48;border-radius:20px;overflow:hidden}
#modeToggle button{background:none;border:none;color:#8b94a7;padding:6px 16px;cursor:pointer;font-size:12.5px}
#modeToggle button.on{background:#1a2342;color:#fff}
#netctl details{border-top:1px solid #1c2440;margin-top:8px}
#netctl details summary{cursor:pointer;list-style:none;font-size:10px;letter-spacing:1.4px;color:#6f7ba0;text-transform:uppercase;padding:8px 0 5px;user-select:none}
#netctl details summary::before{content:'▸ ';color:#3d4a73}
#netctl details[open] summary::before{content:'▾ '}
#netctl #sandboxD{border-top:none;margin-top:6px}
#netctl #sandboxD>summary{list-style:none;text-transform:none;letter-spacing:.2px;font-size:12px;font-weight:600;color:#7fe3a6;background:rgba(63,191,127,.10);border:1px solid #2f7d52;border-radius:8px;padding:6px 10px;margin:2px 0 7px;cursor:pointer;display:flex;align-items:center;gap:6px}
#netctl #sandboxD>summary:hover{background:rgba(63,191,127,.18);border-color:#3fbf7f}
#netctl #sandboxD[open]>summary{background:rgba(63,191,127,.16);color:#a7f3c6}
#netctl #sandboxD>summary::before{content:'▶';color:#3fbf7f;font-size:9px}
#netctl #sandboxD[open]>summary::before{content:'▾';color:#3fbf7f;font-size:11px}
/* search autocomplete dropdown */
.nqwrap{position:relative}
#nqDrop{position:absolute;top:calc(100% + 3px);left:0;right:0;background:#0d1424;border:1px solid #2a3550;border-radius:9px;max-height:240px;overflow:auto;z-index:20;display:none;box-shadow:0 12px 30px #0008}
.nqitem{display:flex;align-items:center;gap:8px;padding:6px 10px;font-size:12.5px;color:#c3cce0;cursor:pointer}
.nqitem:hover,.nqitem.sel{background:#1a2342}
.nqitem .nqh{margin-left:auto;font-size:10.5px;color:#5f6a8e;white-space:nowrap}
/* zoom control (bottom-right) */
#zoomctl{position:absolute;right:14px;bottom:12px;z-index:6;display:flex;flex-direction:column;background:rgba(9,13,26,.88);backdrop-filter:blur(6px);border:1px solid #232c48;border-radius:10px;overflow:hidden}
#zoomctl button{background:none;border:none;color:#c3cce0;width:30px;height:28px;cursor:pointer;font-size:16px;line-height:1;display:flex;align-items:center;justify-content:center;font-family:inherit}
#zoomctl button+button{border-top:1px solid #232c48}
#zoomctl button:hover{background:#1a2342;color:#fff}
/* center-bottom free-text scenario bar (Step 1) */
#scnBar{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:7;width:min(640px,74%);text-align:center}
.sbRow{display:flex;gap:7px;align-items:center;background:rgba(9,13,26,.92);backdrop-filter:blur(7px);border:1px solid #2f3c63;border-radius:13px;padding:7px 8px;box-shadow:0 10px 34px #0009}
#scnInput{flex:1;background:#0e1626;border:1px solid #2a3550;color:var(--tx);border-radius:9px;padding:9px 12px;font-size:13.5px;outline:none}
#scnInput:focus{border-color:var(--ac)}
#scnGo{background:linear-gradient(180deg,#5fa3ff,#3f7fe0);border:none;color:#fff;font-weight:600;border-radius:9px;padding:9px 15px;cursor:pointer;font-size:13px;white-space:nowrap}
#scnGo:hover{filter:brightness(1.08)}
#scnReportBtn,#scnResetBtn{background:#1a2342;border:1px solid #33406e;color:#cdd6ea;border-radius:9px;padding:9px 11px;cursor:pointer;font-size:12.5px;white-space:nowrap}
#scnReportBtn:hover,#scnResetBtn:hover{background:#24304f}
.scnFb{min-height:15px;font-size:11.5px;margin-top:6px;color:#8b94a7;transition:opacity .18s var(--ease)}
.scnFb.ok{color:#7fe3a6}
.scnFb.err{color:#ff9aa6}
.sbChips{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:7px}
.sbChip{background:rgba(20,27,51,.85);border:1px solid #28324f;color:#9aa4c4;border-radius:20px;padding:4px 11px;cursor:pointer;font-size:11.5px}
.sbChip:hover{border-color:var(--ac);color:#fff;background:#1c2742}
/* AI processing progress bar */
#scnProg{display:none;margin-top:8px;height:5px;background:#161f33;border-radius:3px;overflow:hidden;opacity:1;transition:opacity var(--t2) var(--ease)}
#scnProg.on{display:block}
#scnProg i{display:block;height:100%;width:0;border-radius:3px;background:linear-gradient(90deg,#5fa3ff,#7fe3a6,#5fa3ff);background-size:200% 100%;animation:shimmer 1.3s linear infinite}
.scnFb.think{color:#9fb4ff}
/* AI modal: cleaner, more visual */
.amBanner{border-radius:10px;padding:9px 12px;font-size:12.5px;margin:4px 0 12px;border:1px solid}
.amBanner b{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px;opacity:.9}
.affRow{display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px solid #1b2230}
.affRow .nm{font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.affRow .rsn{flex:2;color:#8b94a7;font-size:11.5px}
.affChip{font-size:11px;font-weight:700;padding:2px 9px;border-radius:11px;white-space:nowrap}
.scnCaveat{font-size:11px;color:#6f7ba0;margin-top:12px;font-style:italic}
/* unified interactive motion */
.chip,.fbtn,.qchip,.sbChip,.ec,.phBtn,.abtn,#scnGo,#scnReportBtn,#scnResetBtn,.connrow,.tcard,.affChip{transition:background var(--t1) var(--ease),border-color var(--t1) var(--ease),color var(--t1) var(--ease),transform var(--t1) var(--ease),box-shadow var(--t1) var(--ease)}
.tcard:hover{transform:translateY(-2px)}
#scnGo:hover{transform:translateY(-1px)}
.affRow{transition:background var(--t1) var(--ease)}
.affRow:hover{background:#141b2e}
.mvrow{display:flex;align-items:center;gap:6px;background:#141b33;border:1px solid #232c48;border-radius:7px;padding:4px 8px;margin:3px 0;font-size:11.5px;color:#aab4d4}
.mvrow .rm{margin-left:auto;background:none;border:none;color:#5f6a8e;cursor:pointer;font-size:13px}
.rng{font-weight:600}
.rng .d1{color:#ffd479}.rng .ce{color:#ff8e9d}
.imp-row{border-bottom:1px solid #232c48;padding:9px 0}
.imp-row h3{font-size:14px;color:#fff}
.imp-row .meta{font-size:12px;color:#8b94a7;margin-top:2px}
.jumpchip{display:inline-block;background:#3a1820;color:#ff8e9d;border-radius:9px;padding:1px 8px;font-size:11px;font-weight:700;margin-left:6px}
.expchip{display:inline-block;background:#39301a;color:#ffd479;border-radius:9px;padding:1px 8px;font-size:11px;margin-left:6px}
.mitchip{display:inline-block;background:#15301f;color:#5fd99a;border-radius:9px;padding:1px 8px;font-size:11px;margin-left:6px}
/* ===== journey funnel (redesigned · change 1) ===== */
.jhead{display:flex;align-items:baseline;gap:8px;margin:14px 0 7px}
.jhead h4{margin:0}
.jhead .jcnt{margin-left:auto;font-size:11px;color:var(--tx2)}
.jflow{display:flex;gap:4px}
.jstep{flex:1;position:relative;text-align:center;border-radius:9px;padding:9px 2px 8px;background:#101626;border:1px solid #1d2742;color:#566179}
.jstep .ic{font-size:16px;line-height:1.15;display:block;filter:grayscale(1);opacity:.4}
.jstep .jl{font-size:9px;margin-top:4px;letter-spacing:.2px}
.jstep.on .ic{filter:none;opacity:1}
.jstep.on .jl{font-weight:600}
.jstep.on::after{content:'';position:absolute;left:7px;right:7px;bottom:4px;height:2px;border-radius:2px;background:currentColor}
.jgap{font-size:12px;color:#ffb074;margin:8px 0 2px}.jgap b{color:#ffd0a3}
/* ===== clickable filters (change 6) ===== */
#leg-sec .lgrow{cursor:pointer;border-radius:6px;padding:3px 4px;transition:.12s}
#leg-sec .lgrow[data-sec]:hover{background:#141b33}
#leg-sec .lgrow.off{opacity:.38}
#leg-sec .lgrow.off .st{box-shadow:none;filter:grayscale(1)}
.qfilt{display:flex;flex-wrap:wrap;gap:5px;margin-top:2px}
.qchip{font-size:11px;padding:4px 9px;border-radius:9px;border:1px solid #283450;background:#141b33;color:#7b86a6;cursor:pointer}
.qchip.on{background:#23304f;border-color:var(--ac);color:#fff}
/* ===== scenario pop-up screen (changes 3·4·5) ===== */
#scnModal{position:fixed;inset:0;background:rgba(4,7,15,.74);backdrop-filter:blur(5px);z-index:50;display:flex;align-items:center;justify-content:center;padding:24px;opacity:0;visibility:hidden;pointer-events:none;transition:opacity var(--t2) var(--ease),visibility 0s linear var(--t2)}
#scnModal.open{opacity:1;visibility:visible;pointer-events:auto;transition:opacity var(--t2) var(--ease)}
.scnCard{width:min(1140px,95vw);max-height:92vh;display:flex;flex-direction:column;background:linear-gradient(180deg,#141b29,#0f1420);border:1px solid #2a3550;border-radius:16px;box-shadow:0 30px 90px #000b;overflow:hidden;transform:translateY(16px) scale(.985);opacity:0;transition:transform var(--t3) var(--ease),opacity var(--t3) var(--ease)}
#scnModal.open .scnCard{transform:none;opacity:1}
.scnHead{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;align-items:flex-start;gap:12px}
.scnHead h2{font-size:19px}
.scnHead .sub{font-size:12.5px;color:var(--tx2);margin-top:3px;max-width:90%}
.scnBody{flex:1;overflow:auto;display:grid;grid-template-columns:1.05fr .95fr;gap:22px;padding:18px 20px}
@media(max-width:860px){.scnBody{grid-template-columns:1fr}}
.scnTag{display:inline-block;font-size:11px;font-weight:700;padding:2px 10px;border-radius:10px;margin-bottom:10px;letter-spacing:.3px}
.scnHeadline{font-size:17.5px;font-weight:600;color:#fff;margin-bottom:9px;line-height:1.34}
.scnStory{font-size:13.5px;line-height:1.62;color:#c3cce0;white-space:pre-wrap}
.scnEnt{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.scnEnt .ec{font-size:11.5px;padding:4px 10px;border-radius:9px;background:#161f33;border:1px solid var(--line);color:#aab4d4;cursor:pointer}
.scnEnt .ec.on{background:#23304f;border-color:var(--ac);color:#fff}
.vizBox{background:#0d1424;border:1px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:14px}
.vizBox h5{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--tx2);margin-bottom:11px}
.cmpRow{margin:10px 0}
.cmpRow .lab{display:flex;justify-content:space-between;font-size:11.5px;color:#aab4d4;margin-bottom:4px}
.cmpTrack{position:relative;height:20px;background:#161f33;border-radius:6px;overflow:hidden}
.cmpTrack .ent{position:absolute;left:0;top:0;height:100%;border-radius:6px;transition:width .55s cubic-bezier(.4,1.2,.5,1)}
.cmpTrack .ama{position:absolute;top:-3px;bottom:-3px;width:2px;background:#7fd7ff;box-shadow:0 0 7px #7fd7ff;z-index:2}
.cmpLeg{display:flex;gap:18px;font-size:11px;color:var(--tx2);margin-top:12px}
.cmpLeg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.qmapL{position:relative;width:100%;aspect-ratio:1;max-width:300px;margin:0 auto;background:radial-gradient(circle at 72% 28%,#16243f,#0c1322);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.qmapL .axL{position:absolute;font-size:9px;color:#5f6a8e}
.qmapL .qn{position:absolute;font-size:10px;color:#48526e;font-weight:600;max-width:46%}
.qmapL .gl{position:absolute;background:#222c44}
.qmapL .dotA{position:absolute;width:13px;height:13px;border-radius:50%;background:#7fd7ff;box-shadow:0 0 10px #7fd7ff;transform:translate(-50%,50%);z-index:3}
.qmapL .dotE{position:absolute;width:16px;height:16px;border-radius:50%;background:var(--gold);box-shadow:0 0 16px var(--gold);transform:translate(-50%,50%);z-index:4;transition:left .55s,bottom .55s}
.qmapL .trail{position:absolute;width:7px;height:7px;border-radius:50%;background:#f0c84b55;transform:translate(-50%,50%);z-index:2}
.scnPhases{display:flex;gap:10px;padding:14px 20px;border-top:1px solid var(--line);background:#0d1320}
.phBtn{flex:1;background:#141d31;border:1px solid #283450;border-radius:11px;padding:10px 13px;cursor:pointer;text-align:left;transition:.15s}
.phBtn:hover{border-color:#3a4a72}
.phBtn.on{background:linear-gradient(180deg,#243456,#1b2540);border-color:var(--ac)}
.phBtn .pt{font-size:13px;font-weight:600;color:#fff}
.phBtn .pd{font-size:11px;color:var(--tx2);margin-top:2px}
.phBtn.on .pd{color:#cdd6ea}
.plList{font-size:12.5px;color:#aab4d4;line-height:1.55;margin-top:6px}
.plList .h{color:var(--tx2);font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin:13px 0 4px}
</style></head><body>
<header><h1>Amadeus · AI Disruption Landscape</h1>
<nav><button data-v="vNet" class="on">Relationship Web</button><button data-v="vBoard">Threat Board</button><button data-v="vSyn">Synergy Combos</button><button data-v="vFin">Findings</button></nav>
<span class="stamp" id="stamp"></span></header>
<main>
<div id="vBoard" class="view">
  <div class="cards" id="top10"></div>
  <div class="bar">
    <input type="text" id="q" placeholder="Search company / HQ / impact…" size="28">
    <span class="chip tch on" data-t="High">High</span><span class="chip tch on" data-t="Medium">Medium</span><span class="chip tch" data-t="Low">Low</span>
    <select id="sec"><option value="">All sectors</option></select>
    <select id="quad"><option value="">All quadrants</option></select>
    <small class="cnt" id="cnt"></small>
  </div>
  <table><thead><tr>
    <th data-k="n">Company</th><th data-k="sec">Sector</th><th data-k="epi">EPI ▾</th><th data-k="t">Tier</th>
    <th data-k="q">Quadrant</th><th data-k="w">Will%</th><th data-k="d">Dist%</th><th data-k="ai">AI%</th>
    <th data-k="sv">Survival</th><th data-k="hz">Horizon</th><th data-k="act">Action</th>
  </tr></thead><tbody id="tb"></tbody></table>
</div>
<div id="vNet" class="view on"><div id="netwrap">
  <canvas id="cv"></canvas><div id="tip"></div>
  <div id="modeToggle"><button id="mSky" class="on">✦ Sky</button><button id="mGlobe">🌐 Globe</button></div>
  <div id="focusbar"><span>Focused on <b id="focusname"></b> — its direct links only</span><button onclick="clearFocus()">✕ clear</button></div>
  <div id="scnBar">
    <div class="sbRow">
      <input id="scnInput" type="text" autocomplete="off" placeholder="Describe a scenario — e.g. Tata Neu acquires Hopper">
      <button id="scnGo">▶ Run</button>
      <button id="scnReportBtn" style="display:none">▣ Report</button>
      <button id="scnResetBtn" style="display:none" title="Clear scenario">✕</button>
    </div>
    <div id="scnFb" class="scnFb"></div>
    <div id="scnProg"><i></i></div>
    <div id="scnChips" class="sbChips"></div>
  </div>
  <div id="zoomctl"><button id="zIn" title="Zoom in">+</button><button id="zFit" title="Reset view">⤢</button><button id="zOut" title="Zoom out">−</button></div>
  <div id="netctl">
    <h5>Find</h5>
    <div class="nqwrap"><input type="text" id="nq" placeholder="Type a company name…" autocomplete="off" style="width:100%"><div id="nqDrop"></div></div>
    <h5>Light up</h5>
    <div id="filters"></div>
    <details open><summary>Sector — click a row to filter</summary>
    <div id="leg-sec"></div>
    </details>
    <details open><summary>Quadrant — click to filter</summary>
    <div id="leg-quad" class="qfilt"></div>
    </details>
    <details><summary>Reading the sky</summary>
    <div class="lgrow">★ star size = company scale<br>(market cap / valuation / funding)</div>
    <div class="lgrow">acquired companies orbit their acquirer</div>
    <div class="lgrow">click a star = focus its links · click space = clear</div>
    <div class="lgrow">drag stars · wheel zoom · drag space to pan</div>
    <div class="lgrow">🌐 globe mode: drag rotates the earth; stars sit on their HQ</div>
    </details>
    <h5>View</h5>
    <button class="fbtn" id="labelsBtn"><span class="dot" style="background:#6f7ba0"></span>Labels: major stars</button>
    <button class="fbtn" id="extBtn"><span class="dot" style="background:#6f7ba0"></span>External entities: shown</button>
  </div>
  <div id="netfoot"></div>
</div></div>
<div id="vSyn" class="view"><div class="grid2" id="combos"></div></div>
<div id="vFin" class="view"><div class="grid2" id="findings"></div></div>
</main>
<div id="scnModal"><div class="scnCard">
 <div class="scnHead"><div style="flex:1"><h2 id="scnTitle">Scenario</h2><div class="sub" id="scnSub"></div></div><button class="x" onclick="closeScn()">×</button></div>
 <div class="scnBody">
  <div>
   <div class="scnEnt" id="scnEnt"></div>
   <span class="scnTag" id="scnTag"></span>
   <div class="scnHeadline" id="scnHeadline"></div>
   <div class="scnStory" id="scnStory"></div>
   <div class="plList" id="scnLists"></div>
  </div>
  <div>
   <div class="vizBox"><h5>How they stack up against Amadeus</h5><div id="scnBars"></div>
    <div class="cmpLeg"><span><i id="legE" style="background:#f0c84b"></i><span id="legEn">The challenger</span></span><span><i style="background:#7fd7ff"></i>Amadeus (today's incumbent)</span></div></div>
   <div class="vizBox"><h5>Where they sit on the map</h5>
    <div class="qmapL" id="scnQuad"></div>
    <div style="font-size:10.5px;color:#5f6a8e;text-align:center;margin-top:9px">→ further right = more willing to disrupt &nbsp;·&nbsp; ↑ higher = more capable</div></div>
  </div>
 </div>
 <div class="scnPhases" id="scnPhases"></div>
</div></div>
<div id="drawer"><div class="dh"><h2 id="dt"></h2><button class="x" onclick="drawer.classList.remove('open')">×</button></div><div class="db" id="dbody"></div></div>
<script>
const D=__DATA__;
document.getElementById('stamp').textContent=D.meta.count+' companies · extracted '+D.meta.date+' · '+D.meta.sha;
const byName={};D.companies.forEach(c=>byName[c.n]=c);
const JSTAGES=[['Inspire','💡','#a78bfa'],['Plan','🗺️','#60a5fa'],['Shop','🔍','#22d3ee'],['Book','✈️','#34d399'],['Pay','💳','#fbbf24'],['In-trip','🧳','#fb923c'],['Post-trip','⭐','#f472b6']];
const REDUCE = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
function fadeSwapEl(el){if(!el||REDUCE)return; el.style.animation='none'; void el.offsetWidth; el.style.animation='fadeSwap .28s cubic-bezier(.22,.61,.36,1)';}
const drawer=document.getElementById('drawer');
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
 document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');document.getElementById(b.dataset.v).classList.add('on');
 if(b.dataset.v==='vNet')initNet();
});
function esc(s){return String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]))}
function pill(t){return '<span class="pill p'+t+'">'+t+'</span>'}
// percentile context (computed once)
const EPIS=D.companies.map(c=>parseFloat(c.epi)).filter(x=>!isNaN(x)).sort((a,b)=>a-b);
function pctile(v){if(isNaN(v)||!EPIS.length)return null;
 let lo=0,hi=EPIS.length;while(lo<hi){const m=(lo+hi)>>1;EPIS[m]<v?lo=m+1:hi=m}
 return Math.round(100-lo/EPIS.length*100);}
function gauge(label,val,col,sub){
 const v=Math.max(0,Math.min(100,parseFloat(val)||0));
 return '<div class="gauge"><div class="ring" style="background:conic-gradient('+col+' '+(v*3.6)+'deg,#1a2235 0)"><i>'+(isNaN(parseFloat(val))?'–':Math.round(v))+'</i></div><div class="gl">'+label+'</div>'+(sub?'<div class="gp">'+sub+'</div>':'')+'</div>';}
const SIGLBL={w:['Strategic intent','Investment & M&A','Travel partnerships','Adjacent offerings','Customer travel intent'],
 d:['Vertical content','Connectivity & settlement','Compliance','Payments & MoR','Global scale','Brand trust'],
 ai:['Foundation models','Agentic capability','Agentic protocols','Assistant','Personalisation','Proprietary data','Ecosystem position']};
function sigBars(c){
 const grp=(key,col,title)=>'<div class="sgrp">'+title+'</div>'+c.sig[key].map((v,i)=>
  '<div class="sbar"><span class="sl" title="'+SIGLBL[key][i]+'">'+SIGLBL[key][i]+'</span><span class="st2"><i style="width:'+(v/5*100)+'%;background:'+col+'"></i></span><span class="sv">'+v+'</span></div>').join('');
 return grp('w','#e7a93c','Willingness signals')+grp('d','#4f8edc','Distribution readiness')+grp('ai','#b388ff','AI readiness');}
function connGroups(n){
 const rows=[];
 D.edges.forEach(e=>{if(e.ty==='scenario-bond')return;
  if(e.s!==n&&e.t!==n)return;const other=e.s===n?e.t:e.s;
  rows.push({other,g:e.g,ty:e.ty,raw:e.raw||''});});
 if(!rows.length)return '';
 const order={acq:0,inv:1,part:2};rows.sort((a,b)=>(order[a.g]??3)-(order[b.g]??3));
 return '<h4>Connections ('+rows.length+')</h4>'+rows.slice(0,40).map(r=>
  '<div class="connrow" title="'+esc(r.raw)+'" onclick="focusFromCard(\''+r.other.replace(/'/g,"\\'")+'\')">'+
  '<span class="cdot" style="background:'+(GCOL[r.g]||'#7e9cff')+'"></span>'+esc(r.other)+
  '<span class="cty">'+r.ty+'</span></div>').join('')+(rows.length>40?'<div class="gp" style="color:#5f6a8e;font-size:11px;padding:4px 6px">… +'+(rows.length-40)+' more</div>':'');}
function focusFromCard(id){
 if(byId[id]){setFocus(id);
  if(viewMode==='globe'){const c=byName[id];if(c&&c.geo){lam0=c.geo[1];phi0=c.geo[0];}}
  else{const m=byId[id];cx=m.x;cy=m.y;zoom=Math.max(zoom,1.4);}}
 else showCompany(id);}
function stageFromCard(n){const inp=document.getElementById('scnInput');if(inp){inp.value=n+' acquires ';inp.focus();}}
function showCompany(n){
 const c=byName[n];if(!c)return showExternal(n);
 const sc=SECCOL[c.sec]||'#9fb0cc';
 document.getElementById('dt').innerHTML=esc(c.n)+' <span class="pill" style="background:#1a2235;color:'+sc+';border:1px solid '+sc+'44">'+esc(c.sec)+'</span> '+pill(c.t);
 const r=(parseFloat(c.d)+parseFloat(c.ai))/2;
 const p=pillars(c.sig,c.ndc,c.mor);
 const pc=pctile(parseFloat(c.epi));
 let h='<div class="kv"><span>HQ <b>'+esc(c.hq||'–')+'</b></span><span>'+esc(c.pc||'–')+'</span><span>Horizon <b>'+esc(c.hz||'–')+'</b></span><span>Quadrant <b>'+esc(c.q||'–')+'</b></span><span>Action <b>'+esc(c.act||'–')+'</b></span></div>';
 h+='<div class="cardgrid"><div>';
 h+='<div class="gaugerow">'+gauge('EPI',c.epi,'#e74c5e',pc!=null?'top '+pc+'%':'')+gauge('Willing',c.w,'#e7a93c','')+gauge('Distrib',c.d,'#4f8edc','')+gauge('AI',c.ai,'#b388ff','')+'</div>';
 h+='<div class="chiprow">'+['demand','content','settlement'].map((k,i)=>{const on=[p.demand,p.content,p.settle][i];
  return '<span class="pchip '+(on?'onp':'offp')+'">'+(on?'✓ ':'✕ ')+k+'</span>'}).join('')+
  ['mcp','a2a','ucp','acp'].map(pr=>'<span class="pchip '+(c.protos[pr]?'onp':'')+'">'+pr.toUpperCase()+'</span>').join('')+'</div>';
 h+='</div>';
 // quadrant minimap: x = willingness, y = readiness
 const qx=Math.max(4,Math.min(96,parseFloat(c.w)||0)), qy=Math.max(4,Math.min(96,r||0));
 h+='<div class="qmap"><div class="gridl" style="left:50%;top:0;width:1px;height:100%"></div><div class="gridl" style="top:50%;left:0;height:1px;width:100%"></div>'+
  '<span class="ql" style="right:2px;top:2px">Imminent</span><span class="ql" style="left:2px;top:2px">Sleeping</span><span class="ql" style="right:2px;bottom:2px">Aspirant</span><span class="ql" style="left:2px;bottom:2px">Dormant</span>'+
  '<div class="qdot" style="left:'+qx+'%;bottom:'+qy+'%"></div></div>';
 h+='</div>';
 const cov=(c.jc||[]).reduce((a,b)=>a+(b?1:0),0);
 h+='<div class="jhead"><h4>Traveller journey</h4><span class="jcnt">covers <b style="color:#dde3ee">'+cov+'</b> of 7 stages</span></div>';
 h+='<div class="jflow">'+JSTAGES.map((s,i)=>{const on=c.jc&&c.jc[i];
  const st=on?('color:'+s[2]+';background:'+s[2]+'1f;border-color:'+s[2]+'66'):'';
  return '<div class="jstep'+(on?' on':'')+'" style="'+st+'" title="'+s[0]+(on?': covered':': gap')+'"><span class="ic">'+s[1]+'</span><span class="jl">'+s[0]+'</span></div>';}).join('')+'</div>';
 const gaps=JSTAGES.filter((s,i)=>!(c.jc&&c.jc[i])).map(s=>s[0]);
 if(cov===0)h+='<div class="jgap">No direct traveller-facing footprint in this dataset.</div>';
 else if(gaps.length)h+='<div class="jgap">Leans on partners for: <b>'+gaps.join(', ')+'</b></div>';
 else h+='<div class="jgap" style="color:#5fd99a">Owns the whole journey, inspiration to loyalty.</div>';
 h+='<h4>Capability signals (0–5)</h4>'+sigBars(c);
 h+='<h4>Financial</h4><div class="kv"><span>Survival <b>'+esc(c.sv||'–')+'</b></span><span>Health <b>'+esc(c.fin??'–')+'%</b></span></div>';
 if(c.fin!=null)h+='<div class="finbar"><i style="width:'+Math.min(100,parseFloat(c.fin)||0)+'%"></i></div>';
 if(c.rev)h+='<div class="callout" style="border-color:#3fbf7f">'+esc(c.rev)+'</div>';
 if(c.biz)h+='<div class="callout biz">'+esc(c.biz)+'</div>';
 if(c.imp)h+='<h4>Impact on Amadeus</h4><div class="callout imp">'+esc(c.imp)+'</div>';
 if(c.gap)h+='<h4>What they still need</h4><div class="callout gap">'+esc(c.gap)+'</div>';
 h+=connGroups(n);
 if(c.par)h+='<details style="margin-top:8px"><summary style="cursor:pointer;color:#6f7ba0;font-size:11px;text-transform:uppercase;letter-spacing:.6px">Partnership field (raw)</summary><p style="color:#8b94a7;font-size:12px;margin-top:4px">'+esc(c.par)+'</p></details>';
 h+='<div style="display:flex;gap:8px;margin:14px 0 6px"><button class="abtn" onclick="focusFromCard(\''+n.replace(/'/g,"\\'")+'\')">✦ Focus in sky</button><button class="abtn" onclick="stageFromCard(\''+n.replace(/'/g,"\\'")+'\')">⚗ Stage in scenario</button></div>';
 document.getElementById('dbody').innerHTML=h;
 drawer.classList.add('open');
}
function showExternal(n){
 document.getElementById('dt').innerHTML=esc(n)+' <span class="pill" style="background:#1a2235;color:#9fb0cc;border:1px solid #2a3245">external entity</span>';
 document.getElementById('dbody').innerHTML='<p style="color:#8b94a7;font-size:12.5px">Mentioned in landscape rows but not itself scored. Its links:</p>'+connGroups(n);
 drawer.classList.add('open');
}
window.addEventListener('keydown',e=>{if(e.key==='Escape')drawer.classList.remove('open')});
// ---------- threat board ----------
const tiers=new Set(['High','Medium']);let sortK='epi',sortAsc=false;
const secs=[...new Set(D.companies.map(c=>c.sec))].sort();
const quads=[...new Set(D.companies.map(c=>c.q).filter(Boolean))].sort();
secs.forEach(s=>{const o=document.createElement('option');o.value=o.textContent=s;document.getElementById('sec').append(o)});
quads.forEach(s=>{const o=document.createElement('option');o.value=o.textContent=s;document.getElementById('quad').append(o)});
document.getElementById('top10').innerHTML=D.top10.map((n,i)=>{const c=byName[n]||{};
 return '<div class="tcard" onclick="showCompany(\''+n.replace(/'/g,"\\'")+'\')"><div class="rk">#'+(i+1)+' act now</div><div class="nm">'+esc(n)+'</div><div><span class="epibar"><i style="width:'+(c.epi||0)+'%"></i></span><b>'+esc(c.epi??'–')+'</b> '+pill(c.t||'?')+'</div></div>'}).join('');
function num(v){const x=parseFloat(v);return isNaN(x)?-1:x}
function render(){
 const q=document.getElementById('q').value.toLowerCase(),sec=document.getElementById('sec').value,quad=document.getElementById('quad').value;
 let rows=D.companies.filter(c=>tiers.has(c.t)&&(!sec||c.sec===sec)&&(!quad||c.q===quad)&&
  (!q||(c.n+' '+c.hq+' '+c.imp+' '+c.par).toLowerCase().includes(q)));
 rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];if(['epi','w','d','ai'].includes(sortK)){x=num(x);y=num(y)}return (x>y?1:x<y?-1:0)*(sortAsc?1:-1)});
 document.getElementById('cnt').textContent=rows.length+' companies';
 document.getElementById('tb').innerHTML=rows.map(c=>'<tr onclick="showCompany(\''+c.n.replace(/'/g,"\\'")+'\')">'+
  '<td><b>'+esc(c.n)+'</b></td><td>'+esc(c.sec)+'</td><td><span class="epibar"><i style="width:'+(num(c.epi)>0?c.epi:0)+'%"></i></span>'+esc(c.epi??'–')+'</td>'+
  '<td>'+pill(c.t)+'</td><td>'+esc(c.q)+'</td><td>'+esc(c.w??'')+'</td><td>'+esc(c.d??'')+'</td><td>'+esc(c.ai??'')+'</td>'+
  '<td>'+esc(c.sv)+'</td><td>'+esc(c.hz)+'</td><td>'+esc(c.act)+'</td></tr>').join('');
}
document.getElementById('q').oninput=render;
document.getElementById('sec').onchange=render;document.getElementById('quad').onchange=render;
document.querySelectorAll('.tch').forEach(ch=>ch.onclick=()=>{ch.classList.toggle('on');ch.classList.contains('on')?tiers.add(ch.dataset.t):tiers.delete(ch.dataset.t);render()});
document.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sortK===k)sortAsc=!sortAsc;else{sortK=k;sortAsc=(k==='n'||k==='sec')}render()});
render();
// ---------- synergy + findings ----------
document.getElementById('combos').innerHTML=D.combos.map(c=>
 '<div class="combo"><span class="badge b'+c.risk+'">'+(c.risk==='high'?'ACT':'WATCH')+'</span><h3>'+c.id+' · '+esc(c.title)+'</h3>'+
 '<div class="sec"><b>Who:</b> '+esc(c.who)+'</div><div class="sec"><b>The combination:</b> '+esc(c.what)+'</div>'+
 '<div class="sec"><b>Leading signals:</b> '+esc(c.signals)+'</div><div class="sec"><b>Amadeus counter:</b> '+esc(c.counter)+'</div></div>').join('');
document.getElementById('findings').innerHTML=D.findings.map(f=>
 '<div class="fcard '+(f.s==='retracted'?'retracted':'')+'"><span class="badge b'+f.s+'">'+f.s.toUpperCase()+'</span><h3>'+f.id+' · '+esc(f.t)+'</h3><p>'+esc(f.x)+'</p></div>').join('');

// ================= CONSTELLATION =================
const SECCOL={'Travel-native':'#ff6b81','Big Tech platform':'#b388ff','Fintech & payments':'#4ade80','Retail':'#ffb74d','AI model provider':'#60a5fa','Other':'#9fb0cc'};
const EXTCOL='#7d88aa', AMACOL='#ffd54f';
const GCOL={acq:'#ff5252',inv:'#34d399',part:'#7e9cff',ama:'#ffd54f'};
const FILTERS=[
 {k:'all', label:'Everything', col:'#aab4d4'},
 {k:'acq', label:'Acquisitions', col:GCOL.acq},
 {k:'part',label:'Partnerships', col:GCOL.part},
 {k:'inv', label:'Investors', col:GCOL.inv},
 {k:'ama', label:'Linked to Amadeus', col:GCOL.ama},
];
let NET=null, filter='all', showExt=true, labelMode=1; // 0 none, 1 major, 2 all
let secOff=new Set(), quadOff=new Set(); // clickable sector/quadrant filters (change 6)
let nqList=[], nqSel=0; // search autocomplete state
let nodes=[], links=[], byId={}, focusId=null, hoverN=null;
let zoom=0.85, cx=0, cy=0, alpha=1.0, dragN=null, panning=false, px=0, py=0, downX=0, downY=0;
// globe state
let viewMode='sky', lam0=-30, phi0=24, autoRot=true, downN=null;
const RAD=Math.PI/180;
function projG(lat,lon,R){
 const lam=(lon-lam0)*RAD, phi=lat*RAD, p0=phi0*RAD, cphi=Math.cos(phi);
 const x=R*cphi*Math.sin(lam);
 const y=R*(Math.cos(p0)*Math.sin(phi)-Math.sin(p0)*cphi*Math.cos(lam));
 const z=Math.sin(p0)*Math.sin(phi)+Math.cos(p0)*cphi*Math.cos(lam);
 return [x,-y,z];
}
function setMode(m){viewMode=m;
 document.getElementById('mSky').classList.toggle('on',m==='sky');
 document.getElementById('mGlobe').classList.toggle('on',m==='globe');
 if(m==='sky')alpha=Math.max(alpha,0.12);
 updateFoot();}
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const bgStars=[]; for(let i=0;i<260;i++) bgStars.push([Math.random(),Math.random(),Math.random()*1.1+0.2,Math.random()*6.28]);

function edgeMatch(e){ if(filter==='all')return true; if(filter==='ama')return e.a===1; return e.g===filter; }
function passesCompanyFilter(n){
 if(n.ama)return true;
 if(!n.ds)return !secOff.has('__ext');
 if(secOff.has(n.sec))return false;
 const q=(byName[n.id]||{}).q;
 if(q&&quadOff.has(q))return false;
 return true;
}
function initNet(){
 if(NET){sizeCv();return}
 NET=true;
 byId={};
 nodes=D.nodes.filter(n=>n.ds||n.ama||true).map(n=>{
  const a=Math.random()*6.28, r=120+Math.random()*560;
  const geo=byName[n.id]?byName[n.id].geo:(n.is_amadeus||n.ama?[40.4,-3.7]:null); // Amadeus HQ Madrid
  return {id:n.id, ds:!!n.ds, ama:!!n.ama, sec:n.sec||'', tier:n.tier||'', sz:n.sz||2.2,
   x:Math.cos(a)*r, y:Math.sin(a)*r, vx:0, vy:0, deg:0, ph:Math.random()*6.28, geo};
 });
 nodes.forEach(n=>byId[n.id]=n);
 const amaN=byId['Amadeus']; if(amaN){amaN.x=0;amaN.y=0;}
 links=D.edges.filter(e=>byId[e.s]&&byId[e.t]).map(e=>({a:byId[e.s],b:byId[e.t],g:e.g,am:e.a===1,ty:e.ty}));
 links.forEach(l=>{l.a.deg++;l.b.deg++});
 // filter buttons with counts
 const counts={all:links.length,acq:0,part:0,inv:0,ama:0};
 links.forEach(l=>{counts[l.g]++;if(l.am)counts.ama++});
 document.getElementById('filters').innerHTML=FILTERS.map(f=>
  '<button class="fbtn'+(f.k==='all'?' on':'')+'" data-f="'+f.k+'"><span class="dot" style="background:'+f.col+'"></span>'+f.label+'<span class="cnt">'+counts[f.k]+'</span></button>').join('');
 document.querySelectorAll('#filters .fbtn').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#filters .fbtn').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); filter=b.dataset.f; alpha=Math.max(alpha,0.35); updateFoot();
 });
 const secCounts={};
 nodes.forEach(n=>{if(n.ds)secCounts[n.sec]=(secCounts[n.sec]||0)+1});
 document.getElementById('leg-sec').innerHTML=Object.entries(SECCOL).map(([s,c])=>
  '<div class="lgrow" data-sec="'+esc(s)+'"><span class="st" style="background:'+c+';color:'+c+'"></span>'+s+' <span style="margin-left:auto;color:#5f6a8e">'+(secCounts[s]||0)+'</span></div>').join('')+
  '<div class="lgrow" data-sec="__ext"><span class="st" style="background:'+EXTCOL+';color:'+EXTCOL+'"></span>External entity</div>'+
  '<div class="lgrow"><span class="st" style="background:'+AMACOL+';color:'+AMACOL+'"></span>Amadeus</div>';
 document.querySelectorAll('#leg-sec .lgrow[data-sec]').forEach(row=>row.onclick=()=>{
  const s=row.dataset.sec; if(secOff.has(s))secOff.delete(s);else secOff.add(s);
  row.classList.toggle('off',secOff.has(s));alpha=Math.max(alpha,0.3);updateFoot();});
 const qlist=[...new Set(D.companies.map(c=>c.q).filter(Boolean))];
 document.getElementById('leg-quad').innerHTML=qlist.map(q=>'<span class="qchip on" data-q="'+esc(q)+'">'+esc(q)+'</span>').join('');
 document.querySelectorAll('#leg-quad .qchip').forEach(ch=>ch.onclick=()=>{
  const q=ch.dataset.q; if(quadOff.has(q)){quadOff.delete(q);ch.classList.add('on')}else{quadOff.add(q);ch.classList.remove('on')}
  alpha=Math.max(alpha,0.3);updateFoot();});
 document.getElementById('labelsBtn').onclick=e=>{labelMode=(labelMode+1)%3;
  e.currentTarget.innerHTML='<span class="dot" style="background:#6f7ba0"></span>Labels: '+['off','major stars','all visible'][labelMode];};
 document.getElementById('extBtn').onclick=e=>{showExt=!showExt;alpha=Math.max(alpha,0.3);updateFoot();
  e.currentTarget.innerHTML='<span class="dot" style="background:#6f7ba0"></span>External entities: '+(showExt?'shown':'hidden');};
 const nqEl=document.getElementById('nq');
 nqEl.oninput=e=>{const q=e.target.value.toLowerCase().trim();
  if(!q){nqList=[];renderNqDrop();return;}
  const sD=[],sE=[],cD=[],cE=[];
  nodes.forEach(n=>{const id=n.id.toLowerCase(),ds=n.ds||n.ama;
   if(id.startsWith(q))(ds?sD:sE).push(n.id);
   else if(id.includes(q))(ds?cD:cE).push(n.id);});
  nqList=sD.concat(sE,cD,cE).slice(0,10);nqSel=0;renderNqDrop();};
 nqEl.onkeydown=e=>{
  if(e.key==='ArrowDown'){if(nqList.length){nqSel=(nqSel+1)%nqList.length;renderNqDrop();}e.preventDefault();return;}
  if(e.key==='ArrowUp'){if(nqList.length){nqSel=(nqSel-1+nqList.length)%nqList.length;renderNqDrop();}e.preventDefault();return;}
  if(e.key==='Escape'){nqList=[];renderNqDrop();return;}
  if(e.key==='Enter'){e.preventDefault();
   if(nqList.length){pickNq(nqSel);}
   else{const q=e.target.value.toLowerCase().trim();if(!q)return;const n=nodes.find(x=>x.id.toLowerCase().includes(q));if(n)goToNode(n.id);}}
 };
 nqEl.onblur=()=>setTimeout(()=>{const dd=document.getElementById('nqDrop');if(dd)dd.style.display='none';},120);
 initSandbox();
 document.getElementById('mSky').onclick=()=>setMode('sky');
 document.getElementById('mGlobe').onclick=()=>setMode('globe');
 const zClamp=()=>{zoom=Math.max(0.12,Math.min(6,zoom));};
 document.getElementById('zIn').onclick=()=>{zoom*=1.25;zClamp();};
 document.getElementById('zOut').onclick=()=>{zoom*=0.8;zClamp();};
 document.getElementById('zFit').onclick=()=>{zoom=viewMode==='globe'?1:0.85;cx=0;cy=0;};
 updateFoot(); sizeCv(); loop();
 window.addEventListener('resize',sizeCv);
}
function edgeOk(l){
 if(l.scen)return scnActive&&!showBefore;
 if(!edgeMatch({g:l.g,a:l.am?1:0}))return false;
 if(!passesCompanyFilter(l.a)||!passesCompanyFilter(l.b))return false;
 if(!showExt&&((!l.a.ds&&!l.a.ama)||(!l.b.ds&&!l.b.ama)))return false;
 if(focusId&&l.a.id!==focusId&&l.b.id!==focusId)return false;
 return true;
}
function recomputeVis(){
 let edgeN=0;
 if(filter==='all'&&!focusId){
  nodes.forEach(n=>{n.vis=showExt||n.ds||n.ama});
  links.forEach(l=>{if(edgeOk(l))edgeN++});
 } else {
  nodes.forEach(n=>{n.vis=false});
  links.forEach(l=>{if(edgeOk(l)){l.a.vis=true;l.b.vis=true;edgeN++}});
  if(focusId&&byId[focusId])byId[focusId].vis=true;
  if(!showExt)nodes.forEach(n=>{if(!n.ds&&!n.ama)n.vis=false});
 }
 nodes.forEach(n=>{if(n.vis&&!passesCompanyFilter(n))n.vis=false});
 document.getElementById('netfoot').textContent=nodes.filter(n=>n.vis).length+' stars visible · '+edgeN+' links lit'+
  (viewMode==='globe'?' · globe shows '+D.meta.geoN+' HQ-placed companies (externals hidden)':'');
}
function updateFoot(){recomputeVis()}
function setFocus(id){focusId=id;document.getElementById('focusname').textContent=id;
 document.getElementById('focusbar').style.display='flex';alpha=Math.max(alpha,0.25);updateFoot();showCompany(id);}
function clearFocus(){focusId=null;document.getElementById('focusbar').style.display='none';updateFoot();}
function goToNode(id){const n=byId[id];if(!n)return;setFocus(id);
 if(viewMode==='globe'&&n.geo){lam0=n.geo[1];phi0=n.geo[0];} // center on it but keep spinning
 else{cx=n.x;cy=n.y;zoom=Math.max(zoom,1.7);}}
function renderNqDrop(){const dd=document.getElementById('nqDrop');if(!dd)return;
 if(!nqList.length){dd.style.display='none';dd.innerHTML='';return;}
 dd.innerHTML=nqList.map((id,i)=>{const c=byName[id],n=byId[id];
  const hint=c?esc(c.sec):(n&&n.ama?'Amadeus':'external');
  return '<div class="nqitem'+(i===nqSel?' sel':'')+'" data-i="'+i+'">'+esc(id)+'<span class="nqh">'+hint+'</span></div>';}).join('');
 dd.style.display='block';
 dd.querySelectorAll('.nqitem').forEach(it=>it.onmousedown=ev=>{ev.preventDefault();pickNq(+it.dataset.i);});}
function pickNq(i){const id=nqList[i];if(!id)return;document.getElementById('nq').value=id;nqList=[];renderNqDrop();goToNode(id);}
// physics: grid repulsion + typed springs
const CELL=110;
function step(){
 const grid=new Map();
 nodes.forEach(n=>{const k=((n.x/CELL)|0)+':'+((n.y/CELL)|0);(grid.get(k)||grid.set(k,[]).get(k)).push(n)});
 nodes.forEach(a=>{
  const gx=(a.x/CELL)|0, gy=(a.y/CELL)|0;
  for(let i=gx-1;i<=gx+1;i++)for(let j=gy-1;j<=gy+1;j++){
   const cell=grid.get(i+':'+j); if(!cell)continue;
   for(const b of cell){ if(b===a||b.id<a.id)continue;
    let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+30; if(d2>CELL*CELL*2.2)continue;
    const f=(980+(a.sz+b.sz)*30)/d2, d=Math.sqrt(d2); dx/=d;dy/=d;
    a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f; }}});
 links.forEach(l=>{
  if(l.a.dead||l.b.dead)return;
  const rest=l.scen?40:(l.g==='acq'?34:(l.g==='inv'?170:135)), k=l.scen?0.06:(l.g==='acq'?0.05:0.006);
  let dx=l.b.x-l.a.x,dy=l.b.y-l.a.y;const d=Math.sqrt(dx*dx+dy*dy)+0.01,f=(d-rest)*k;
  dx/=d;dy/=d;l.a.vx+=dx*f;l.a.vy+=dy*f;l.b.vx-=dx*f;l.b.vy-=dy*f;});
 nodes.forEach(n=>{
  n.vx-=n.x*0.0007;n.vy-=n.y*0.0007;
  if(!REDUCE){n.vx+=Math.sin(T*0.22+n.ph)*0.22;n.vy+=Math.cos(T*0.18+n.ph*1.3)*0.22;} // calm, slow perpetual drift
  n.vx=Math.max(-26,Math.min(26,n.vx))*alpha;n.vy=Math.max(-26,Math.min(26,n.vy))*alpha;
  if(n!==dragN){n.x+=n.vx;n.y+=n.vy;n.vx*=0.85;n.vy*=0.85}});
 alpha=Math.max(REDUCE?0:0.05,alpha*0.992); // calm floor so motion keeps gliding (off under reduced-motion)
}
function starR(n){return n.ama?13:(0.9+n.sz*0.85)}
function starCol(n){return n.ama?AMACOL:(n.ds?(SECCOL[n.sec]||SECCOL.Other):EXTCOL)}
// scenario spotlight: everything not in the running scenario dims to 30% (change 2)
function inScn(n){return n.chg||n.jump||n.exp||n.mit||n.dead}
function nDim(n){return (scnActive&&!showBefore&&!inScn(n))?0.3:1}
function eDim(l){return (scnActive&&!showBefore&&!l.scen)?0.3:1}
let T=0;
function nodeRings(n,x,y,r,dm){dm=dm||1;
 if(n.tier==='High'&&n.ds){ctx.globalAlpha=0.85*dm;ctx.strokeStyle='#ff5b72';ctx.lineWidth=1.1;ctx.beginPath();ctx.arc(x,y,r+2.2,0,7);ctx.stroke();}
 if(n===hoverN||n.id===focusId){ctx.globalAlpha=1;ctx.strokeStyle='#ffffff';ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(x,y,r+3.4,0,7);ctx.stroke();}
 if(scnActive&&!showBefore){
  if(n.chg){ctx.globalAlpha=0.55+0.4*Math.sin(T*2.6+n.ph);ctx.strokeStyle='#ffd54f';ctx.lineWidth=1.6;ctx.beginPath();ctx.arc(x,y,r+4,0,7);ctx.stroke();}
  if(n.jump){ctx.globalAlpha=0.8;ctx.strokeStyle='#ffffff';ctx.lineWidth=1.2;ctx.beginPath();ctx.arc(x,y,r+7+2*Math.sin(T*2),0,7);ctx.stroke();}
  if(n.exp){ctx.globalAlpha=0.85;ctx.strokeStyle='#ffb74d';ctx.lineWidth=1.2;ctx.setLineDash([3,3]);ctx.beginPath();ctx.arc(x,y,r+3.5,0,7);ctx.stroke();ctx.setLineDash([]);}
  if(n.mit){ctx.globalAlpha=0.9;ctx.strokeStyle='#3fbf7f';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,r+3.5,0,7);ctx.stroke();}
 }
 ctx.globalAlpha=1;
}
function drawGlobe(){
 const W=cv.width,Hh=cv.height;ctx.clearRect(0,0,W,Hh);
 ctx.save();
 bgStars.forEach(s=>{ctx.globalAlpha=0.10+0.10*Math.sin(T*0.7+s[3]);ctx.fillStyle='#9fb4ff';
  ctx.fillRect(s[0]*W,s[1]*Hh,s[2],s[2]);});
 ctx.restore();
 ctx.save();ctx.translate(W/2,Hh/2);ctx.scale(devicePixelRatio,devicePixelRatio);
 const R=Math.min(W,Hh)/devicePixelRatio*0.42*zoom;
 // rim + subtle fill
 ctx.globalAlpha=1;ctx.fillStyle='#0a1020';ctx.beginPath();ctx.arc(0,0,R,0,7);ctx.fill();
 ctx.strokeStyle='#33508c';ctx.lineWidth=1.2;ctx.globalAlpha=0.9;ctx.stroke();
 ctx.globalAlpha=0.12;ctx.lineWidth=7;ctx.stroke();
 // graticule
 ctx.strokeStyle='#1c2a4a';ctx.lineWidth=0.5;ctx.globalAlpha=0.8;
 for(let lon=-180;lon<180;lon+=30){ctx.beginPath();let pen=false;
  for(let lat=-85;lat<=85;lat+=5){const p=projG(lat,lon,R);
   if(p[2]>0.001){pen?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);pen=true}else pen=false;}
  ctx.stroke();}
 for(let lat=-60;lat<=60;lat+=30){ctx.beginPath();let pen=false;
  for(let lon=-180;lon<=180;lon+=5){const p=projG(lat,lon,R);
   if(p[2]>0.001){pen?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);pen=true}else pen=false;}
  ctx.stroke();}
 // country wireframe
 ctx.strokeStyle='#2c3f6e';ctx.lineWidth=0.65;ctx.globalAlpha=0.95;
 D.world.forEach(line=>{ctx.beginPath();let pen=false;
  for(let i=0;i<line.length;i+=2){const p=projG(line[i+1],line[i],R);
   if(p[2]>0.001){pen?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);pen=true}else pen=false;}
  ctx.stroke();});
 // project nodes
 nodes.forEach(n=>{n.gv=false;
  if(!n.vis||!n.geo)return;
  if(n.dead&&scnActive&&!showBefore){/* still place, drawn dim */}
  const p=projG(n.geo[0],n.geo[1],R);
  if(p[2]>0.02){n.gx=p[0];n.gy=p[1];n.gv=true;}});
 // edges as lifted arcs
 ctx.globalCompositeOperation='lighter';
 const filtered=filter!=='all'||focusId;
 links.forEach(l=>{
  if(!edgeOk(l))return;
  if(!l.a.gv||!l.b.gv)return;
  const col=l.scen?'#ffd54f':(l.am&&filter==='ama'?GCOL.ama:GCOL[l.g]);
  const lit=l.scen||filtered, edm=eDim(l);
  const mx=(l.a.gx+l.b.gx)/2,my=(l.a.gy+l.b.gy)/2;
  const md=Math.sqrt(mx*mx+my*my)+0.01;
  const chord=Math.hypot(l.a.gx-l.b.gx,l.a.gy-l.b.gy);
  const lift=1+0.10*chord/R+8/md;
  ctx.strokeStyle=col;ctx.globalAlpha=(lit?(l.scen?0.9:0.6):0.28)*edm;ctx.lineWidth=l.scen?2:(lit?1.4:0.7);
  ctx.beginPath();ctx.moveTo(l.a.gx,l.a.gy);ctx.quadraticCurveTo(mx*lift,my*lift,l.b.gx,l.b.gy);ctx.stroke();
  if(lit){ctx.globalAlpha=0.15*edm;ctx.lineWidth=l.scen?6:4;ctx.stroke();}
 });
 ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;
 // stars
 let placed=0;
 nodes.forEach(n=>{
  if(!n.gv)return;placed++;
  const r=starR(n)*0.85, col=starCol(n), dm=nDim(n);
  const deadF=(n.dead&&scnActive&&!showBefore)?0.22:1;
  const tw=(n.sz<4?(0.82+0.18*Math.sin(T*1.4+n.ph)):1)*deadF*dm;
  ctx.globalAlpha=0.16*tw;ctx.fillStyle=(n.dead&&scnActive&&!showBefore)?'#777':col;
  ctx.beginPath();ctx.arc(n.gx,n.gy,r*2.4,0,7);ctx.fill();
  ctx.globalAlpha=tw;ctx.beginPath();ctx.arc(n.gx,n.gy,r,0,7);ctx.fill();
  if(n.ama||r>7){ctx.globalAlpha=0.5*tw;ctx.fillStyle='#ffffff';ctx.beginPath();ctx.arc(n.gx,n.gy,r*0.38,0,7);ctx.fill();}
  nodeRings(n,n.gx,n.gy,r,dm);
  const showLbl=labelMode===2||(labelMode===1&&(n.sz>7.4||n.ama))||n===hoverN||n.id===focusId||(focusId&&n.vis)||zoom>2.1||(scnActive&&!showBefore&&(n.chg||n.exp||n.mit||n.dead));
  if(showLbl){ctx.fillStyle=n.ama?AMACOL:'#c9d2ea';ctx.font=(n.ama?'bold ':'')+'9.5px Segoe UI';
   ctx.globalAlpha=0.92*dm;ctx.fillText(n.id.slice(0,26),n.gx+r+3,n.gy+3);ctx.globalAlpha=1;}
 });
 ctx.restore();
}
function draw(){
 T+=0.016;
 if(viewMode==='globe'){drawGlobe();return;}
 const W=cv.width,Hh=cv.height;ctx.clearRect(0,0,W,Hh);
 // decorative far-field
 ctx.save();
 bgStars.forEach(s=>{ctx.globalAlpha=0.10+0.10*Math.sin(T*0.7+s[3]);ctx.fillStyle='#9fb4ff';
  ctx.fillRect(s[0]*W,s[1]*Hh,s[2],s[2]);});
 ctx.restore();
 ctx.save();ctx.translate(W/2,Hh/2);ctx.scale(zoom*devicePixelRatio,zoom*devicePixelRatio);ctx.translate(-cx,-cy);
 const filtered=filter!=='all'||focusId;
 // edges
 ctx.globalCompositeOperation='lighter';
 links.forEach(l=>{
  if(!edgeOk(l))return;
  if(l.scen){
   ctx.strokeStyle='#ffd54f';ctx.globalAlpha=0.85+0.15*Math.sin(T*3);ctx.lineWidth=2;
   ctx.beginPath();ctx.moveTo(l.a.x,l.a.y);ctx.lineTo(l.b.x,l.b.y);ctx.stroke();
   ctx.globalAlpha=0.2;ctx.lineWidth=6;ctx.stroke();
   return;
  }
  const col=l.am&&(filter==='ama')?GCOL.ama:GCOL[l.g];
  const lit=filtered, edm=eDim(l);
  ctx.strokeStyle=col; ctx.globalAlpha=(lit?0.62:0.30)*edm; ctx.lineWidth=lit?1.5:0.7;
  ctx.beginPath();ctx.moveTo(l.a.x,l.a.y);ctx.lineTo(l.b.x,l.b.y);ctx.stroke();
  if(lit){ctx.globalAlpha=0.16*edm;ctx.lineWidth=4;ctx.stroke();}
 });
 ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;
 // stars
 nodes.forEach(n=>{
  if(!n.vis)return;
  const r=starR(n), col=starCol(n), dm=nDim(n);
  const deadF=(n.dead&&scnActive&&!showBefore)?0.22:1;
  const tw=(n.sz<4?(0.82+0.18*Math.sin(T*1.4+n.ph)):1)*deadF*dm;
  ctx.globalAlpha=0.16*tw;ctx.fillStyle=(n.dead&&scnActive&&!showBefore)?'#777':col;
  ctx.beginPath();ctx.arc(n.x,n.y,r*2.6,0,7);ctx.fill();
  ctx.globalAlpha=tw;ctx.beginPath();ctx.arc(n.x,n.y,r,0,7);ctx.fill();
  if(n.ama||r>7){ctx.globalAlpha=0.5*tw;ctx.fillStyle='#ffffff';ctx.beginPath();ctx.arc(n.x,n.y,r*0.38,0,7);ctx.fill();}
  if(n.tier==='High'&&n.ds){ctx.globalAlpha=0.85*dm;ctx.strokeStyle='#ff5b72';ctx.lineWidth=1.1;ctx.beginPath();ctx.arc(n.x,n.y,r+2.2,0,7);ctx.stroke();}
  if(n===hoverN||n.id===focusId){ctx.globalAlpha=1;ctx.strokeStyle='#ffffff';ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(n.x,n.y,r+3.4,0,7);ctx.stroke();}
  if(scnActive&&!showBefore){
   if(n.chg){ctx.globalAlpha=0.55+0.4*Math.sin(T*2.6+n.ph);ctx.strokeStyle='#ffd54f';ctx.lineWidth=1.6;ctx.beginPath();ctx.arc(n.x,n.y,r+4,0,7);ctx.stroke();}
   if(n.jump){ctx.globalAlpha=0.8;ctx.strokeStyle='#ffffff';ctx.lineWidth=1.2;ctx.beginPath();ctx.arc(n.x,n.y,r+7+2*Math.sin(T*2),0,7);ctx.stroke();}
   if(n.exp){ctx.globalAlpha=0.85;ctx.strokeStyle='#ffb74d';ctx.lineWidth=1.2;ctx.setLineDash([3,3]);ctx.beginPath();ctx.arc(n.x,n.y,r+3.5,0,7);ctx.stroke();ctx.setLineDash([]);}
   if(n.mit){ctx.globalAlpha=0.9;ctx.strokeStyle='#3fbf7f';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(n.x,n.y,r+3.5,0,7);ctx.stroke();}
  }
  ctx.globalAlpha=1;
  const showLbl=labelMode===2||(labelMode===1&&(n.sz>7.4||n.ama))||n===hoverN||n.id===focusId||(focusId&&n.vis)||zoom>2.1||(scnActive&&!showBefore&&(n.chg||n.exp||n.mit||n.dead));
  if(showLbl){ctx.fillStyle=n.ama?AMACOL:'#c9d2ea';ctx.font=(n.ama?'bold ':'')+'9.5px Segoe UI';
   ctx.globalAlpha=0.92*dm;ctx.fillText(n.id.slice(0,26),n.x+r+3,n.y+3);ctx.globalAlpha=1;}
 });
 ctx.restore();
}
let raf,frame=0;
function loop(){
 frame++;
 if(viewMode==='sky'){ step(); }
 else if(autoRot&&!panning) lam0+=0.05;
 draw();
 raf=requestAnimationFrame(loop);
}
function sizeCv(){const r=cv.parentElement.getBoundingClientRect();cv.width=r.width*devicePixelRatio;cv.height=r.height*devicePixelRatio}
function pick(mx,my){const r=cv.getBoundingClientRect();
 let best=null,bd=1e9;
 if(viewMode==='globe'){
  const x=mx-r.left-r.width/2, y=my-r.top-r.height/2;
  nodes.forEach(n=>{if(!n.gv)return;const dx=n.gx-x,dy=n.gy-y,d2=dx*dx+dy*dy;
   const rr=Math.pow(starR(n)*0.85+4,2); if(d2<rr&&d2<bd){bd=d2;best=n}});
  return best;}
 const x=(mx-r.left-r.width/2)/zoom+cx, y=(my-r.top-r.height/2)/zoom+cy;
 nodes.forEach(n=>{if(!n.vis)return;const dx=n.x-x,dy=n.y-y,d2=dx*dx+dy*dy;
  const rr=Math.pow(starR(n)+4,2); if(d2<rr&&d2<bd){bd=d2;best=n}});
 return best;}
cv.onmousedown=e=>{const n=pick(e.clientX,e.clientY);
 if(viewMode==='globe'){downN=n;panning=true;} // holding pauses spin; release resumes (autoRot stays on)
 else if(n){dragN=n}else{panning=true}
 px=downX=e.clientX;py=downY=e.clientY};
window.onmousemove=e=>{
 if(viewMode==='globe'&&panning){lam0+=(e.clientX-px)*0.28/zoom;phi0=Math.max(-80,Math.min(80,phi0+(e.clientY-py)*0.22/zoom));px=e.clientX;py=e.clientY}
 else if(dragN){dragN.x+=(e.clientX-px)/zoom;dragN.y+=(e.clientY-py)/zoom;px=e.clientX;py=e.clientY;alpha=Math.max(alpha,0.18)}
 else if(panning){cx-=(e.clientX-px)/zoom;cy-=(e.clientY-py)/zoom;px=e.clientX;py=e.clientY}
 else{const n=pick(e.clientX,e.clientY);hoverN=n;const tip=document.getElementById('tip');
  if(n){const wr=cv.parentElement.getBoundingClientRect();
   tip.style.display='block';tip.style.left=(e.clientX-wr.left+14)+'px';tip.style.top=(e.clientY-wr.top+10)+'px';
   const c=byName[n.id];
   tip.innerHTML='<b>'+esc(n.id)+'</b><div class="m">'+(n.ama?'The incumbent rail':(n.ds?esc(n.sec)+(c&&c.epi!=null?' · EPI '+c.epi:'')+(n.tier?' · '+n.tier+' tier':''):'external entity'))+' · '+n.deg+' links</div>';
   cv.style.cursor='pointer';}
  else{tip.style.display='none';cv.style.cursor='default'}}};
window.onmouseup=e=>{
 const moved=Math.abs(e.clientX-downX)>4||Math.abs(e.clientY-downY)>4;
 if(viewMode==='globe'&&!moved){
  if(downN)setFocus(downN.id);
  else if(e.target===cv){clearFocus();drawer.classList.remove('open')}}
 else if(dragN&&!moved){setFocus(dragN.id)}
 else if(panning&&!moved&&e.target===cv){clearFocus();drawer.classList.remove('open')}
 dragN=null;panning=false;downN=null;};
cv.onwheel=e=>{e.preventDefault();zoom*=e.deltaY<0?1.12:0.89;zoom=Math.max(0.12,Math.min(6,zoom))};

// ================= SCENARIO ENGINE =================
// scoring model from workbook 'Model Config' (verified 2026-06-12):
// W%=Σw·[.25,.25,.2,.2,.1]/5 · D%=Σd·[.25,.25,.15,.15,.1,.1]/5 · AI%=Σai·[.2,.25,.15,.1,.1,.15,.05]/5
// R=.5D+.5AI · EPI=.4W+.6R · bands High>=60 Med>=40 · quadrant = (W>=60)x(R>=60)
const WW=[.25,.25,.2,.2,.1],DW=[.25,.25,.15,.15,.1,.1],AIW=[.2,.25,.15,.1,.1,.15,.05];
const HAIRCUT=0.85;
function pctOf(v,w){let s=0;for(let i=0;i<w.length;i++)s+=(v[i]||0)*w[i];return s/5*100}
function scoreSig(sig,scale){const f=x=>Math.min(5,(x||0)*scale);
 const w=pctOf(sig.w.map(f),WW),d=pctOf(sig.d.map(f),DW),ai=pctOf(sig.ai.map(f),AIW),r=.5*d+.5*ai;
 return {w:Math.round(w),d:Math.round(d),ai:Math.round(ai),r:Math.round(r),epi:Math.round(.4*w+.6*r)};}
function band(e){return e>=60?'High':e>=40?'Medium':'Low'}
function quad(w,r){return w>=60?(r>=60?'Imminent threat':'Aspirant'):(r>=60?'Sleeping giant':'Dormant')}
function pillars(sig,ndc,mor){return {demand:sig.w[4]>=4,content:sig.d[0]>=4||!!ndc,settle:!!mor||sig.d[3]>=4}}
function pTxt(p){return (p.demand?1:0)+(p.content?1:0)+(p.settle?1:0)+'/3 ('+['demand','content','settlement'].filter((k,i)=>[p.demand,p.content,p.settle][i]).join('+')+')'}
const cloneSig=s=>({w:[...s.w],d:[...s.d],ai:[...s.ai]});

let staged=[], scnActive=false, scnReport=null, scnName='Custom scenario', scnNote='', showBefore=false;
let scnPhase=2, scnEntIdx=0, scnPhaseDates=[], scnTimer=null, scnAI=null;
// Amadeus shown as the incumbent benchmark: very strong distribution reach, moderate AI, low appetite to disrupt itself
const AMA={w:35,d:95,ai:45}; AMA.r=Math.round(.5*AMA.d+.5*AMA.ai); AMA.epi=Math.round(.4*AMA.w+.6*AMA.r);

function renderStaged(){
 const el=document.getElementById('staged'); if(!el)return;
 el.innerHTML=staged.map((m,i)=>{
  let t = m.type==='merge'?(esc(m.a)+(m.mode==='acquire'?' acquires ':' + ')+esc(m.b))
   : m.type==='adopt'?esc(m.a)+' adopts '+m.proto.toUpperCase()
   : m.type==='kill'?esc(m.a)+' shuts down'
   : m.kind==='acquire'?'Amadeus acquires '+esc(m.target)
   : m.kind==='agent-rail'?'Amadeus ships the agent rail':'Amadeus × OpenAI supply deal';
  return '<div class="mvrow">'+t+'<button class="rm" data-i="'+i+'">✕</button></div>';}).join('');
 document.querySelectorAll('#staged .rm').forEach(b=>b.onclick=()=>{staged.splice(+b.dataset.i,1);renderStaged()});
}
function runScenario(){
 resetScenario(false);
 if(!staged.length)return;
 scnActive=true;
 // --- merge components (union-find) so roll-ups (A buys B,C,D) form one entity ---
 const par={}; const find=x=>{while(par[x]!==undefined&&par[x]!==x)x=par[x];return x};
 const uni=(x,y)=>{x=find(x);y=find(y);if(x!==y)par[x]=y};
 const merges=staged.filter(m=>m.type==='merge'&&byName[m.a]&&byName[m.b]);
 merges.forEach(m=>{par[m.a]=par[m.a]??m.a;par[m.b]=par[m.b]??m.b;uni(m.b,m.a)});
 const comps={};
 Object.keys(par).forEach(k=>{const r=find(k);(comps[r]=comps[r]||new Set()).add(k);comps[r].add(r)});
 const entities=[], exposed=new Map(), mitigated=new Map(), killed=[];
 const touched=new Set();
 Object.values(comps).forEach(set=>{
  const members=[...set]; if(members.length<2)return;
  const lead=merges.find(m=>set.has(m.a))?.a||members[0];
  const anyAcq=merges.some(m=>set.has(m.a)&&m.mode==='acquire');
  const leadC=byName[lead]; const u=cloneSig(leadC.sig);
  let ndc=leadC.ndc, mor=leadC.mor;
  members.forEach(id=>{const c=byName[id];if(!c||id===lead)return;
   if(anyAcq){for(let i=0;i<5;i++)u.w[i]=Math.max(u.w[i],c.sig.w[i]);
    for(let i=0;i<6;i++)u.d[i]=Math.max(u.d[i],c.sig.d[i]);
    for(let i=0;i<7;i++)u.ai[i]=Math.max(u.ai[i],c.sig.ai[i]);
    ndc=ndc||c.ndc; mor=mor||c.mor;}
   else{[0,1,4].forEach(i=>u.d[i]=Math.max(u.d[i],c.sig.d[i]));
    u.ai[2]=Math.max(u.ai[2],c.sig.ai[2]); ndc=ndc||c.ndc;}});
  const before=scoreSig(leadC.sig,1), day1=scoreSig(u,HAIRCUT), ceil=scoreSig(u,1);
  const pB=pillars(leadC.sig,leadC.ndc,leadC.mor), pA=pillars(u,ndc,mor);
  entities.push({name:members.length>2?lead+' + '+(members.length-1)+' companies':members.join(' + '),
   members, lead, mode:anyAcq?'acquire':'partner',
   before, day1, ceil,
   tierB:band(before.epi), tierA:band(ceil.epi),
   quadB:quad(before.w,before.r), quadA:quad(ceil.w,ceil.r),
   pillB:pTxt(pB), pillA:pTxt(pA),
   membersBefore:members.map(id=>({id,epi:byName[id]?.epi}))});
  members.forEach(id=>touched.add(id));
  // visual: bond all members to lead, mark stars
  members.forEach(id=>{const n=byId[id];if(!n)return;n.chg=true;
   if(band(ceil.epi)!==band(before.epi)||quad(ceil.w,ceil.r)!==quad(before.w,before.r))n.jump=true;
   if(id!==lead&&byId[lead])links.push({a:byId[lead],b:n,g:'acq',am:false,ty:'scenario-bond',scen:true});});
 });
 staged.filter(m=>m.type==='adopt'&&byName[m.a]).forEach(m=>{
  const c=byName[m.a], u=cloneSig(c.sig); u.ai[2]=Math.max(u.ai[2],3);
  const before=scoreSig(c.sig,1), after=scoreSig(u,1);
  entities.push({name:m.a+' adopts '+m.proto.toUpperCase(),members:[m.a],lead:m.a,mode:'adopt',
   before,day1:after,ceil:after,tierB:band(before.epi),tierA:band(after.epi),
   quadB:quad(before.w,before.r),quadA:quad(after.w,after.r),
   pillB:pTxt(pillars(c.sig,c.ndc,c.mor)),pillA:pTxt(pillars(u,c.ndc,c.mor)),membersBefore:[{id:m.a,epi:c.epi}]});
  touched.add(m.a); const n=byId[m.a]; if(n){n.chg=true;if(band(after.epi)!==band(before.epi))n.jump=true;}
 });
 staged.filter(m=>m.type==='kill'&&byName[m.a]).forEach(m=>{
  killed.push(m.a); touched.add(m.a); const n=byId[m.a]; if(n)n.dead=true;});
 staged.filter(m=>m.type==='ama').forEach(m=>{
  if(m.kind==='agent-rail'){['Sabre (Mosaic)','Travelport','Expedia Group','Spotnana','PayPal'].forEach(id=>
   mitigated.set(id,'agent-rail first-mover advantage neutralized — Amadeus ships MCP/agent interfaces + Outpayce checkout first'));}
  else if(m.kind==='openai-supply'){D.companies.filter(c=>c.oai).forEach(c=>
   mitigated.set(c.n,'OpenAI-dependent booking surface — now routes Amadeus content via the supply deal'));}
  else if(m.kind==='acquire'&&byName[m.target]){mitigated.set(m.target,'acquired by Amadeus — its rails and mandates now feed the GDS');
   const n=byId[m.target], an=byId['Amadeus'];
   if(n&&an){n.mit=true;links.push({a:an,b:n,g:'acq',am:true,ty:'scenario-bond',scen:true});}}
 });
 // exposure: first-order neighbors of touched companies (numbers unchanged, flagged only)
 D.edges.forEach(e=>{
  if(e.ty==='scenario-bond')return;
  const hits=[e.s,e.t].filter(x=>touched.has(x));
  if(!hits.length)return;
  const other=touched.has(e.s)?e.t:e.s;
  if(touched.has(other)||other==='Amadeus')return;
  if(!exposed.has(other))exposed.set(other,other+' — '+e.ty+' link to '+hits[0]+(killed.includes(hits[0])?' (now gone)':' (now part of a new entity)'));
 });
 exposed.forEach((_,id)=>{const n=byId[id];if(n&&!n.chg)n.exp=true});
 mitigated.forEach((_,id)=>{const n=byId[id];if(n)n.mit=true});
 scnReport={entities,exposed:[...exposed.values()],exposedN:exposed.size,
  mitigated:[...mitigated.entries()].map(([k,v])=>k+' — '+v),mitigatedN:mitigated.size,killed,
  moves:staged.slice()};
 alpha=Math.max(alpha,0.7); updateFoot(); updateScnBar();
 // let the sky dim + the new bonds form first, then surface the report
 if(scnTimer)clearTimeout(scnTimer);
 scnTimer=setTimeout(showReport,1600);
}
function resetScenario(full=true){
 if(scnTimer){clearTimeout(scnTimer);scnTimer=null;}
 links=links.filter(l=>!l.scen);
 nodes.forEach(n=>{n.chg=n.jump=n.exp=n.mit=n.dead=false});
 scnActive=false; scnReport=null; scnAI=null; showBefore=false;
 document.getElementById('scnModal').classList.remove('open');
 updateScnBar();
 const bb=document.getElementById('baBtn'); if(bb)bb.textContent='Showing: after';
 if(full){staged=[];renderStaged();drawer.classList.remove('open');alpha=Math.max(alpha,0.25);updateFoot();
  const inp=document.getElementById('scnInput');if(inp)inp.value='';
  const fb=document.getElementById('scnFb');if(fb){fb.textContent='';fb.className='scnFb';}}
}
// ---- plain-language scenario pop-up (changes 3·4·5) ----
function joinNames(a){a=a.slice();if(a.length<=1)return a[0]||'';if(a.length===2)return a[0]+' and '+a[1];return a.slice(0,-1).join(', ')+' and '+a[a.length-1];}
function tierWord(epi){return epi>=60?'already a serious, present-day threat':epi>=40?'a moderate but rising threat':'not yet a real threat';}
function fmtMon(d){return d.toLocaleString('en-US',{month:'short',year:'numeric'});}
function phaseDates(){const n=new Date(),a=new Date(n),b=new Date(n);a.setMonth(a.getMonth()+6);b.setMonth(b.getMonth()+12);return [fmtMon(n),fmtMon(a),fmtMon(b)];}
function lerp(a,b,f){return Math.round(a+(b-a)*f);}
function phaseMetrics(e,f){return {w:lerp(e.before.w,e.ceil.w,f),d:lerp(e.before.d,e.ceil.d,f),ai:lerp(e.before.ai,e.ceil.ai,f),epi:lerp(e.before.epi,e.ceil.epi,f),r:lerp(e.before.r,e.ceil.r,f)};}
function pillarsCovered(str){const m=/\(([^)]*)\)/.exec(str||'');return m?m[1].split('+').map(s=>s.trim()):[];}
function pillarSentence(cov){const map={demand:'reaching customers directly',content:'their own travel content',settlement:'taking the payment'};
 if(cov.length>=3)return 'They now have all three things needed to run a booking by themselves — customers, travel content and payments — so a traveller could go from idea to paid trip without ever touching a system like Amadeus.';
 if(!cov.length)return '';
 const have=cov.map(c=>map[c]||c), miss=['demand','content','settlement'].filter(c=>!cov.includes(c)).map(c=>map[c]);
 return 'Together they now handle '+joinNames(have)+(miss.length?', but still need a partner for '+joinNames(miss):'')+'.';}
function amaCompare(m){const beats=[],behind=[];
 (m.w>AMA.w?beats:behind).push('willingness to shake up the market');
 (m.ai>AMA.ai?beats:behind).push('AI readiness');
 (m.d>AMA.d?beats:behind).push('distribution reach');
 let s='';
 if(beats.length)s+=' Next to Amadeus they now lead on '+joinNames(beats)+'.';
 if(behind.length)s+=' Amadeus still holds the edge on '+joinNames(behind)+'.';
 return s;}
function narr(e,pi){
 const f=[0,.5,1][pi], dates=scnPhaseDates;
 const mNow=phaseMetrics(e,0), m=phaseMetrics(e,f), mEnd=phaseMetrics(e,1);
 const names=joinNames(e.members), lead=e.lead, qNow=quad(mNow.w,mNow.r), qCur=quad(m.w,m.r);
 if(e.mode==='adopt'){const A=e.members[0];
  if(pi===0)return {tag:'Today — '+dates[0],headline:A+' works on its own for now.',
   story:A+' today scores '+mNow.epi+' out of 100 on our disruption scale — '+tierWord(mNow.epi)+'. It has not yet switched on the new technology that lets AI assistants search, book and pay through it automatically.'};
  if(pi===1)return {tag:'Around '+dates[1],headline:A+' starts letting AI assistants book through it.',
   story:'By '+dates[1]+', '+A+' has begun turning on automatic AI booking. Its disruption score climbs to about '+m.epi+' out of 100 and it edges toward the "'+qCur+'" position.'};
  return {tag:dates[2],headline:A+' becomes a full AI booking channel.',
   story:'By '+dates[2]+', '+A+' fully supports automatic AI booking. Its disruption score reaches '+mEnd.epi+' out of 100 — '+tierWord(mEnd.epi)+' — landing in the "'+quad(mEnd.w,mEnd.r)+'" position.'+amaCompare(mEnd)};
 }
 const verb=e.mode==='acquire'?'buying':'teaming up with';
 if(pi===0)return {tag:'Today — '+dates[0],
  headline:names+' are still separate companies.',
  story:'Right now, '+names+' run independently. On its own, the strongest of them scores '+mNow.epi+' out of 100 on our disruption scale ('+tierWord(mNow.epi)+') and sits in the "'+qNow+'" position. Apart, none of them gives a traveller a complete book-and-pay alternative to a system like Amadeus.'};
 if(pi===1)return {tag:'About '+dates[1],
  headline:'Six months in — the pieces start fitting together.',
  story:'By '+dates[1]+', '+lead+' is '+verb+' the others and the combination is taking shape. Early on, their combined disruption score rises to about '+m.epi+' out of 100 and they begin moving toward the "'+qCur+'" position'+(qCur!==qNow?', a clear shift from where they started':'')+'.'};
 return {tag:dates[2]+' — fully combined',
  headline:e.name+': one combined force.',
  story:'By '+dates[2]+', the combination is complete. Together they reach a disruption score of '+mEnd.epi+' out of 100 — '+tierWord(mEnd.epi)+' — landing in the "'+e.quadA+'" position. '+pillarSentence(pillarsCovered(e.pillA))+amaCompare(mEnd)};
}
function curEnt(){return scnReport?scnReport.entities[scnEntIdx]:null;}
function renderScnEnt(){const el=document.getElementById('scnEnt'),es=scnReport.entities;
 if(es.length<2){el.innerHTML='';return;}
 el.innerHTML=es.map((e,i)=>'<span class="ec'+(i===scnEntIdx?' on':'')+'" data-i="'+i+'">'+esc(e.lead)+'</span>').join('');
 el.querySelectorAll('.ec').forEach(c=>c.onclick=()=>{scnEntIdx=+c.dataset.i;renderScnEnt();renderScn();});}
function renderScnPhases(){const labs=['Now','In 6 months','In 12 months'];
 document.getElementById('scnPhases').innerHTML=labs.map((l,i)=>
  '<button class="phBtn'+(i===scnPhase?' on':'')+'" data-i="'+i+'"><div class="pt">'+l+'</div><div class="pd">'+(scnPhaseDates[i]||'')+'</div></button>').join('');
 document.querySelectorAll('#scnPhases .phBtn').forEach(b=>b.onclick=()=>{scnPhase=+b.dataset.i;renderScnPhases();renderScn();});}
function barsHtml(e,m,col){
 const rows=[['Willingness to disrupt','w'],['Distribution reach','d'],['AI readiness','ai'],['Disruption score (0–100)','epi']];
 return rows.map(function(rw){var lab=rw[0],k=rw[1],ev=m[k],av=AMA[k];
  return '<div class="cmpRow"><div class="lab"><span>'+lab+'</span><span><b style="color:'+col+'">'+ev+'</b> &nbsp;vs&nbsp; Amadeus '+av+'</span></div>'+
   '<div class="cmpTrack"><div class="ent" style="width:'+ev+'%;background:'+col+'"></div><div class="ama" style="left:'+av+'%"></div></div></div>';}).join('');}
function quadHtml(e,m){const cl=v=>Math.max(5,Math.min(95,v));
 const p0=phaseMetrics(e,0),p1=phaseMetrics(e,.5);
 let h='<div class="gl" style="left:50%;top:0;width:1px;height:100%"></div><div class="gl" style="top:50%;left:0;height:1px;width:100%"></div>';
 h+='<span class="qn" style="right:6px;top:5px;text-align:right">Imminent threat</span><span class="qn" style="left:6px;top:5px">Sleeping giant</span><span class="qn" style="right:6px;bottom:5px;text-align:right">Aspirant</span><span class="qn" style="left:6px;bottom:5px">Dormant</span>';
 h+='<div class="trail" style="left:'+cl(p0.w)+'%;bottom:'+cl(p0.r)+'%"></div><div class="trail" style="left:'+cl(p1.w)+'%;bottom:'+cl(p1.r)+'%"></div>';
 h+='<div class="dotA" style="left:'+cl(AMA.w)+'%;bottom:'+cl(AMA.r)+'%" title="Amadeus today"></div>';
 h+='<div class="dotE" style="left:'+cl(m.w)+'%;bottom:'+cl(m.r)+'%" title="'+esc(e.lead)+'"></div>';
 return h;}
function scnLists(){const r=scnReport;let h='';
 if(r.killed&&r.killed.length)h+='<div class="h">Companies that disappear</div>'+r.killed.map(esc).join(', ');
 if(r.mitigatedN)h+='<div class="h">What the Amadeus move defends against ('+r.mitigatedN+')</div>'+r.mitigated.slice(0,18).map(esc).join('<br>')+(r.mitigatedN>18?'<br>…and '+(r.mitigatedN-18)+' more':'');
 if(r.exposedN)h+='<div class="h">Who this puts under pressure ('+r.exposedN+')</div><span style="color:#8b94a7">'+r.exposed.slice(0,18).map(esc).join('<br>')+(r.exposedN>18?'<br>…and '+(r.exposedN-18)+' more':'')+'</span>';
 return h;}
function renderScn(){
 if(scnAI)return renderAIScn();
 const e=curEnt();
 document.getElementById('scnLists').innerHTML=scnLists();
 if(!e){
  document.getElementById('scnTag').style.display='none';
  document.getElementById('scnHeadline').textContent=scnName;
  document.getElementById('scnStory').textContent=scnNote||'This move reshapes the landscape without forming a single new combined company — see the impact list below.';
  document.getElementById('scnBars').innerHTML='<div style="color:#5f6a8e;font-size:12px">No single challenger to chart for this move.</div>';
  document.getElementById('scnQuad').innerHTML='';return;
 }
 const f=[0,.5,1][scnPhase], m=phaseMetrics(e,f), nv=narr(e,scnPhase);
 const col=SECCOL[(byName[e.lead]||{}).sec]||'#f0c84b';
 const tg=document.getElementById('scnTag');
 tg.style.display='inline-block'; tg.textContent=nv.tag;
 tg.style.background=scnPhase===0?'#1a2335':scnPhase===1?'#39301a':'#15301f';
 tg.style.color=scnPhase===0?'#9fb0cc':scnPhase===1?'#ffd479':'#5fd99a';
 document.getElementById('scnHeadline').textContent=nv.headline;
 document.getElementById('scnStory').textContent=nv.story;
 document.getElementById('scnBars').innerHTML=barsHtml(e,m,col);
 document.getElementById('legE').style.background=col;
 document.getElementById('legEn').textContent=e.lead;
 document.getElementById('scnQuad').innerHTML=quadHtml(e,m);
}
function showReport(){
 scnPhaseDates=phaseDates(); scnPhase=0; scnEntIdx=0;
 if(scnAI){
  document.getElementById('scnTitle').textContent=scnAI.title||'AI scenario';
  document.getElementById('scnSub').textContent=scnAI.confidence?('AI estimate · '+scnAI.confidence+' confidence'):'AI estimate';
  document.getElementById('scnEnt').innerHTML='';
  renderScnPhases(); renderScn(); updateScnBar();
  document.getElementById('scnModal').classList.add('open'); return;
 }
 if(!scnReport)return;
 scnReport.entities.sort((a,b)=>b.ceil.epi-a.ceil.epi);
 document.getElementById('scnTitle').textContent=scnName;
 document.getElementById('scnSub').textContent=scnNote||'';
 renderScnEnt(); renderScnPhases(); renderScn();
 updateScnBar();
 document.getElementById('scnModal').classList.add('open');
}
function openScn(){if(scnReport||scnAI){document.getElementById('scnModal').classList.add('open');}}
function closeScn(){document.getElementById('scnModal').classList.remove('open');updateScnBar();}
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.getElementById('scnModal').classList.contains('open'))closeScn();});
// ================= AI SCENARIO (Step 2) =================
function effLabel(e){return ({transformed:'transformed',rises:'rises',falls:'falls',exposed:'exposed',mitigated:'defended',removed:'removed'})[e]||e;}
function aiPrimaryEntity(){const p=scnAI&&scnAI.primary; if(!p||!p.before||!p.after)return null;
 const mk=o=>{const w=+o.w||0,d=+o.d||0,a=+o.ai||0;return {w,d,ai:a,epi:+o.epi||0,r:Math.round(.5*d+.5*a)};};
 return {lead:p.name||'The scenario', before:mk(p.before), ceil:mk(p.after)};}
function renderAIScn(){
 const pe=aiPrimaryEntity(), f=[0,.5,1][scnPhase];
 const ph=(scnAI.phases&&scnAI.phases[scnPhase])||{};
 const tg=document.getElementById('scnTag'); tg.style.display='inline-block';
 tg.textContent=(ph.label||['Now','In 6 months','In 12 months'][scnPhase])+(ph.date?(' · '+ph.date):'');
 tg.style.background=scnPhase===0?'#1a2335':scnPhase===1?'#39301a':'#15301f';
 tg.style.color=scnPhase===0?'#9fb0cc':scnPhase===1?'#ffd479':'#5fd99a';
 document.getElementById('scnHeadline').textContent=ph.headline||scnAI.title||'';
 document.getElementById('scnStory').textContent=ph.story||'';
 fadeSwapEl(document.getElementById('scnHeadline')); fadeSwapEl(document.getElementById('scnStory'));
 if(pe){const m=phaseMetrics(pe,f),col='#f0c84b';
  document.getElementById('scnBars').innerHTML=barsHtml(pe,m,col);
  document.getElementById('legE').style.background=col; document.getElementById('legEn').textContent=pe.lead;
  document.getElementById('scnQuad').innerHTML=quadHtml(pe,m);
 }else{document.getElementById('scnBars').innerHTML='<div style="color:#5f6a8e;font-size:12px">No single company at the centre of this scenario — see the ranked impact.</div>';document.getElementById('scnQuad').innerHTML='';}
 const am=scnAI.amadeus||{}; let h='';
 if(am.note){const hi=am.direction==='higher',lo=am.direction==='lower';
  const bg=hi?'#2a151b':lo?'#13251b':'#1a2030', bd=hi?'#5e2a33':lo?'#1f4a34':'#2a3245', cl=hi?'#ff8e9d':lo?'#5fd99a':'#9fb0cc';
  h+='<div class="amBanner" style="background:'+bg+';border-color:'+bd+';color:'+cl+'"><b>Impact on Amadeus</b>'+esc(hi?'Higher threat':lo?'Lower threat / defended':'Neutral')+' — <span style="color:#c3cce0">'+esc(am.note)+'</span></div>';}
 const aff=(scnAI.affected||[]).slice().sort((a,b)=>Math.abs((b.epiAfter||0)-(b.epiBefore||0))-Math.abs((a.epiAfter||0)-(a.epiBefore||0)));
 if(aff.length){h+='<div class="h">Most affected</div>'+aff.map(a=>{
   const eb=a.epiBefore,ea=a.epiAfter,up=(ea>eb),dn=(ea<eb);
   const col=up?'#ff8e9d':dn?'#5fd99a':'#9fb0cc', bg=up?'#2a151b':dn?'#13251b':'#1a2030';
   const delta=(eb!=null&&ea!=null)?((up?'↑':dn?'↓':'•')+' '+eb+'→'+ea):effLabel(a.effect);
   return '<div class="affRow"><span class="nm">'+esc(a.name)+'</span><span class="affChip" style="color:'+col+';background:'+bg+'">'+esc(delta)+'</span><span class="rsn">'+esc(a.reason||'')+'</span></div>';}).join('');}
 if(scnAI.caveats)h+='<div class="scnCaveat">'+esc(scnAI.caveats)+'</div>';
 document.getElementById('scnLists').innerHTML=h;
}
function resolveExactNode(name){if(!name)return null; if(byId[name])return name;
 const r=resolveCompany(name); return (r&&r.id&&byId[r.id])?r.id:null;}
function runAIScenario(payload,text){
 resetScenario(false);
 scnAI=payload; scnActive=true; scnName=payload.title||'AI scenario'; scnNote=text||'';
 (payload.affected||[]).forEach(a=>{const id=resolveExactNode(a.name); if(!id||!byId[id])return;
  const prop=a.effect==='exposed'?'exp':a.effect==='mitigated'?'mit':a.effect==='removed'?'dead':'chg';
  byId[id][prop]=true;});
 if(payload.primary&&payload.primary.name){const id=resolveExactNode(payload.primary.name); if(id&&byId[id])byId[id].chg=true;}
 (payload.newBonds||[]).forEach(pr=>{if(!Array.isArray(pr)||pr.length<2)return;
  const ia=resolveExactNode(pr[0]),ib=resolveExactNode(pr[1]);
  if(ia&&ib&&byId[ia]&&byId[ib]){byId[ia].chg=true;byId[ib].chg=true;links.push({a:byId[ia],b:byId[ib],g:'acq',am:false,ty:'scenario-bond',scen:true});}});
 alpha=Math.max(alpha,0.7); updateFoot(); updateScnBar();
 if(scnTimer)clearTimeout(scnTimer); scnTimer=setTimeout(showReport,1600);
}
function getPasscode(){let p=sessionStorage.getItem('scnPass'); if(p)return p;
 p=prompt('Enter the passcode to use the AI scenario simulator:'); if(p===null)return null;
 p=p.trim(); if(p)sessionStorage.setItem('scnPass',p); return p;}
let scnBusy=false, progMsgTimer=null, statusT=null;
const PROG_MSGS=['Reading the landscape…','Scoring the companies…','Tracing the ripple effects…','Writing the story…'];
function setStatus(txt){const fb=document.getElementById('scnFb'); if(statusT)clearTimeout(statusT);
 fb.style.opacity='0'; statusT=setTimeout(()=>{fb.textContent=txt; fb.className='scnFb think'; fb.style.opacity='1';},170);}
function startProg(){
 const bar=document.getElementById('scnProg'), fill=bar.querySelector('i'), fb=document.getElementById('scnFb');
 if(statusT){clearTimeout(statusT);statusT=null;}
 bar.classList.add('on'); bar.style.opacity='1';
 fill.style.transition='none'; fill.style.width='0%'; void fill.offsetWidth; // commit start before easing
 fill.style.transition='width 18s cubic-bezier(.05,.7,.1,1)'; fill.style.width='92%'; // smooth decelerating glide
 fb.textContent=PROG_MSGS[0]; fb.className='scnFb think'; fb.style.opacity='1';
 let mi=0; progMsgTimer=setInterval(()=>{mi=(mi+1)%PROG_MSGS.length; setStatus(PROG_MSGS[mi]);},2800);
}
function stopProg(done){
 const bar=document.getElementById('scnProg'), fill=bar.querySelector('i'), fb=document.getElementById('scnFb');
 if(progMsgTimer){clearInterval(progMsgTimer);progMsgTimer=null;}
 if(statusT){clearTimeout(statusT);statusT=null;}
 fb.style.opacity='1';
 if(done){fill.style.transition='width .35s cubic-bezier(.22,.61,.36,1)'; fill.style.width='100%';
  setTimeout(()=>{bar.style.opacity='0'; setTimeout(()=>{bar.classList.remove('on');fill.style.transition='none';fill.style.width='0%';bar.style.opacity='1';},300);},360);}
 else{bar.classList.remove('on');fill.style.transition='none';fill.style.width='0%';}
}
async function submitScenario(){
 if(scnBusy)return;
 const inp=document.getElementById('scnInput'),fb=document.getElementById('scnFb'),go=document.getElementById('scnGo');
 const text=inp.value.trim();
 if(!text){fb.textContent='Type a scenario — e.g. “GDS is bypassed by NDC aggregators”.';fb.className='scnFb err';return;}
 const pass=getPasscode(); if(pass===null)return;
 scnBusy=true; go.disabled=true; inp.disabled=true; startProg();
 try{
  const res=await fetch('/api/scenario',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:text,passcode:pass})});
  if(res.status===401){sessionStorage.removeItem('scnPass');stopProg(false);fb.textContent='Wrong passcode — click Run to try again.';fb.className='scnFb err';return;}
  let payload=null; try{payload=await res.json();}catch(e){}
  if(!res.ok||!payload||payload.error){stopProg(false);fb.textContent=(payload&&payload.error)||'The AI simulator is unavailable right now — please try again in a moment.';fb.className='scnFb err';return;}
  stopProg(true); fb.textContent=''; fb.className='scnFb'; runAIScenario(payload,text);
 }catch(err){
  stopProg(false); fb.textContent='Couldn’t reach the AI simulator — check your connection and try again.'; fb.className='scnFb err';
 }finally{scnBusy=false; go.disabled=false; inp.disabled=false;}
}
function briefMd(){
 const r=scnReport;if(!r)return '';
 const today=new Date().toISOString().slice(0,10);
 let md='# Scenario brief — '+scnName+'\n\n*Generated '+today+' from the landscape sandbox (viz/dashboard.html). EPI ranges = day-1 (85% integration haircut) → ceiling (full capability union), computed with the workbook Model Config weights.*\n\n';
 if(scnNote)md+='> '+scnNote+'\n\n';
 md+='## Moves\n\n'+r.moves.map(m=>'- '+(m.type==='merge'?m.a+(m.mode==='acquire'?' acquires ':' partners with ')+m.b:
  m.type==='adopt'?m.a+' adopts '+m.proto.toUpperCase():m.type==='kill'?m.a+' shuts down':
  'Amadeus move: '+m.kind+(m.target?' ('+m.target+')':''))).join('\n')+'\n\n## Headline deltas\n\n| Entity | EPI before | day-1 | ceiling | EPI band | Quadrant | Pillars |\n|---|---|---|---|---|---|---|\n';
 r.entities.forEach(e=>{md+='| '+e.name+' | '+e.before.epi+' | '+e.day1.epi+' | '+e.ceil.epi+' | '+e.tierB+' → '+e.tierA+' | '+e.quadB+' → '+e.quadA+' | '+e.pillB+' → '+e.pillA+' |\n'});
 if(r.killed.length)md+='\n## Removed\n\n'+r.killed.join(', ')+'\n';
 if(r.mitigatedN)md+='\n## Mitigated ('+r.mitigatedN+')\n\n'+r.mitigated.map(x=>'- '+x).join('\n')+'\n';
 if(r.exposedN)md+='\n## Exposed — first-order, scores unchanged ('+r.exposedN+')\n\n'+r.exposed.map(x=>'- '+x).join('\n')+'\n';
 md+='\n## Implications for Amadeus\n\n*(to be written — discuss with the team)*\n';
 return md;
}
async function saveBrief(){
 if(!scnReport){alert('Run a scenario first');return}
 const name=prompt('Scenario name for the brief:',scnName);if(!name)return;scnName=name;
 const payload={name:scnName,note:scnNote,moves:scnReport.moves,brief:briefMd()};
 try{
  const res=await fetch('/api/save-scenario',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!res.ok)throw new Error(res.status);
  const j=await res.json();
  alert('Saved: '+j.md+'\nIt will appear as a ★ preset after the next dashboard rebuild.');
 }catch(err){
  const blob=new Blob([briefMd()],{type:'text/markdown'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download=scnName.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'.md';a.click();
  alert('No sandbox server running — brief downloaded instead. Run: python scripts/sandbox_server.py');
 }
}
// ---- free-text scenario bar: parse a sentence into one engine move (Step 1, no AI) ----
function detectProto(s){const m=(s||'').toLowerCase().match(/\b(mcp|a2a|ucp|acp)\b/);return m?m[1]:null;}
function resolveCompany(str){
 let q=(str||'').trim().replace(/[.?!,]+$/,'').replace(/^the\s+/i,''); if(!q)return{error:'Missing a company name.'};
 const ql=q.toLowerCase();
 let hit=D.companies.find(c=>c.n.toLowerCase()===ql);
 if(!hit)hit=D.companies.filter(c=>c.n.toLowerCase().startsWith(ql)).sort((a,b)=>a.n.length-b.n.length)[0];
 if(!hit)hit=D.companies.filter(c=>c.n.toLowerCase().includes(ql)).sort((a,b)=>a.n.length-b.n.length)[0];
 if(hit)return{id:hit.n};
 const w=ql.split(/\s+/)[0];
 const sugg=D.companies.filter(c=>w&&c.n.toLowerCase().includes(w)).slice(0,4).map(c=>c.n);
 return{error:'Couldn’t find a company matching “'+q+'”.'+(sugg.length?' Did you mean: '+sugg.join(', ')+'?':' Check the spelling.')};
}
function parseScenario(text){
 const s=(text||'').trim(); if(!s)return{error:'Type a scenario — e.g. “Tata Neu acquires Hopper”.'};
 const low=s.toLowerCase();
 if(/^\s*amadeus\b/.test(low)){
  if(/(agent|agentic)\s+rail/.test(low))return{moves:[{type:'ama',kind:'agent-rail'}],label:'Amadeus ships the agent rail'};
  if(/openai/.test(low))return{moves:[{type:'ama',kind:'openai-supply'}],label:'Amadeus × OpenAI supply deal'};
  const m=low.match(/amadeus\s+(?:acquires?|buys?|acquire)\s+(.+)/);
  if(m){const t=resolveCompany(m[1]);if(t.error)return t;return{moves:[{type:'ama',kind:'acquire',target:t.id}],label:'Amadeus acquires '+t.id};}
 }
 let m=s.match(/^(.*?)\s+(?:adopts?|launches?|enables?|ships?|adds|rolls?\s+out)\s+(.*)$/i);
 if(m){const proto=detectProto(m[2]);if(proto){const c=resolveCompany(m[1]);if(c.error)return c;return{moves:[{type:'adopt',a:c.id,proto}],label:c.id+' adopts '+proto.toUpperCase()};}}
 m=s.match(/^(.*?)\s+(?:shuts?\s+down|shut\s+down|closes?|goes?\s+bankrupt|bankrupt|dies|fails|collapses?)\b/i);
 if(m){const c=resolveCompany(m[1]);if(c.error)return c;return{moves:[{type:'kill',a:c.id}],label:c.id+' shuts down'};}
 m=s.match(/^(.*?)\s+(?:acquires?|buys?|takes?\s+over|acquisition\s+of)\s+(.*)$/i);
 if(m){const a=resolveCompany(m[1]);if(a.error)return a;const b=resolveCompany(m[2]);if(b.error)return b;return{moves:[{type:'merge',a:a.id,b:b.id,mode:'acquire'}],label:a.id+' acquires '+b.id};}
 m=s.match(/^(.*?)\s+(?:partners?\s+with|teams?\s+up\s+with|partnership\s+with|allies?\s+with|\+)\s+(.*)$/i);
 if(m){const a=resolveCompany(m[1]);if(a.error)return a;const b=resolveCompany(m[2]);if(b.error)return b;return{moves:[{type:'merge',a:a.id,b:b.id,mode:'partner'}],label:a.id+' partners with '+b.id};}
 return{error:'Not sure how to simulate that. Try: “X acquires Y”, “X partners with Y”, “X adopts a2a”, “X shuts down”, or “Amadeus acquires Y”.'};
}
function updateScnBar(){const rb=document.getElementById('scnReportBtn'),rs=document.getElementById('scnResetBtn');
 if(rb)rb.style.display=scnActive?'inline-block':'none';
 if(rs)rs.style.display=scnActive?'inline-block':'none';}
function runScenarioText(){
 const inp=document.getElementById('scnInput'),fb=document.getElementById('scnFb');
 const r=parseScenario(inp.value);
 if(r.error){fb.textContent=r.error;fb.className='scnFb err';return;}
 staged=r.moves; scnName=r.label; scnNote='Typed scenario: “'+inp.value.trim()+'”';
 fb.textContent='Simulating: '+r.label; fb.className='scnFb ok';
 renderStaged(); runScenario();
}
function initSandbox(){
 // center-bottom free-text AI scenario bar (Step 2)
 const ex=['Tata Neu acquires Hopper','GDS is bypassed by NDC aggregators','Google launches a travel agent','Revolut buys Kiwi.com','A recession cuts corporate travel 30%'];
 document.getElementById('scnChips').innerHTML=ex.map(x=>'<button class="sbChip">'+esc(x)+'</button>').join('');
 document.querySelectorAll('#scnChips .sbChip').forEach(b=>b.onclick=()=>{document.getElementById('scnInput').value=b.textContent;submitScenario();});
 document.getElementById('scnGo').onclick=submitScenario;
 document.getElementById('scnInput').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();submitScenario();}};
 document.getElementById('scnReportBtn').onclick=openScn;
 document.getElementById('scnResetBtn').onclick=()=>resetScenario(true);
 updateScnBar();
}
initNet(); // boot straight into the Relationship Web (default view)
</script></body></html>"""

# ---- compact AI index for the scenario simulator (api/company_index.json) ----
def _pillars(c):
    s = c["sig"]
    demand = s["w"][4] >= 4
    content = s["d"][0] >= 4 or c["ndc"] == 1
    settle = c["mor"] == 1 or s["d"][3] >= 4
    return "".join(t for t, on in (("D", demand), ("C", content), ("S", settle)) if on) or "-"

ai_index = [{
    "n": c["n"], "sec": c["sec"], "w": c["w"], "d": c["d"], "ai": c["ai"], "epi": c["epi"],
    "q": c["q"], "t": c["t"], "mor": c["mor"], "sv": c["sv"], "pil": _pillars(c),
    "note": (c.get("biz") or "")[:90],
} for c in comp]
API = ROOT / "api"
API.mkdir(exist_ok=True)
(API / "company_index.json").write_text(json.dumps(ai_index, ensure_ascii=False), encoding="utf-8")
print(f"api/company_index.json written: {len(ai_index)} companies")

VIZ.mkdir(exist_ok=True)
out = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
(VIZ / "dashboard.html").write_text(out, encoding="utf-8")
print(f"viz/dashboard.html written: {len(out)//1024} KB, "
      f"{len(comp)} companies, {len(gedges)} edges, {len(gnodes)} nodes")
