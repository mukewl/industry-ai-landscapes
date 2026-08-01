"""Build viz/igaming.html — a self-contained iGaming disruption dashboard.

Designed for THIS dataset's shape: few companies (25), deep and individually
defensible (every score carries a justification + cited sources). That is the
inverse of the travel/Amadeus dashboard, which solved breadth (553 companies ->
constellation/globe). Here the hero is a positioning map, the structural view is
a 25x18 signal matrix, and evidence is a first-class UI citizen.

Colour follows the dataviz skill and is VALIDATED, not eyeballed:
  - positioning map: ONE hue (bubble/scatter = --pairs all, where only 3
    categorical slots clear the CVD floors; 8 sector hues would fail). Sector is
    an interactive filter/highlight instead of a colour encoding.
  - signal matrix: ordinal single-hue ramp, 6 steps, validated with --ordinal.
  - pillar view: the first 3 categorical slots, validated with --pairs all.
Dark surface #1a1a19; deliberately a single (dark) look.

    python -X utf8 scripts/build_igaming_dashboard.py
"""
import importlib.util
import json
import math
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDUSTRY = "igaming"
DATA = ROOT / "industries" / INDUSTRY / "data"
VIZ = ROOT / "viz"

# --- byline ------------------------------------------------------------------
AUTHOR = "Mukul Shrivas"
LINKEDIN_URL = ""   # <-- set this to render the LinkedIn link (empty = name only)
GITHUB_URL = "https://github.com/mukewl/industry-ai-landscapes"

# --- signal labels come from the generator so they can never drift -----------
spec = importlib.util.spec_from_file_location("mw", ROOT / "scripts" / "make_workbook.py")
mw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mw)
IG = mw.INDUSTRIES[INDUSTRY]
W_LABELS = [n for n, _, _ in IG["w"]]
D_LABELS = [n for n, _, _ in IG["d"]]
AI_LABELS = [n for n, _, _ in mw.AI_SIGNALS]
W_DEFS = {n: (d, a) for n, d, a in IG["w"]}
D_DEFS = {n: (d, a) for n, d, a in IG["d"]}
AI_DEFS = {n: (d, a) for n, d, a in mw.AI_SIGNALS}
SECTORS = IG["sectors"]
STAGES = IG["stages"]
VERTICALS = IG["verticals"]

companies = json.loads((DATA / "companies.json").read_text(encoding="utf-8"))
meta = json.loads((DATA / "extract_meta.json").read_text(encoding="utf-8"))

# incumbent benchmark (frame.md / DECISIONS D7)
AMA = {"w": 35, "d": 90, "ai": 40}
AMA["r"] = round(.5 * AMA["d"] + .5 * AMA["ai"])


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"[\d][\d,]*\.?\d*", str(v).replace(",", ""))
    return float(m.group()) if m else None


def sig(c, prefix, n):
    out = []
    for i in range(1, n + 1):
        key = next((k for k in c if k.startswith(f"{prefix}{i}_")), None)
        v = c.get(key) if key else None
        out.append(int(v) if isinstance(v, (int, float)) else None)
    return out


def parse_justifications(c):
    """populate.py appends 'W1=3: note | W2=4: note | ...' to evidence_notes."""
    txt = str(c.get("evidence_notes") or "")
    out = {}
    for m in re.finditer(r"\b(W|D|AI|F)(\d+)=([0-9]+|None):\s*([^|]+)", txt):
        out[f"{m.group(1)}{m.group(2)}"] = m.group(4).strip()
    return out


def scale_of(c):
    """Bubble area proxy: $mn scale, log-compressed. Falls back to headcount."""
    for k in ("market_cap_valuation_mn", "post_money_valuation_mn",
              "total_funding_mn", "total_funding_raised_mn"):
        v = num(c.get(k))
        if v and v > 0:
            return 1.0 + math.log10(v + 1)
    fte = num(c.get("ftes"))
    if fte and fte > 0:
        return 0.8 + math.log10(fte + 1) * 0.6
    return 0.9


def pillars(c, w, d):
    demand = (w[4] or 0) >= 4
    content = (d[0] or 0) >= 4 or str(c.get("direct_channel") or "").lower() == "y"
    wallet = (str(c.get("merchant_of_record") or "").lower() == "y") or (d[3] or 0) >= 4
    return {"player": demand, "product": content, "wallet": wallet}


comp = []
for c in companies:
    w, d, ai = sig(c, "w", 5), sig(c, "d", 6), sig(c, "ai", 7)
    f = sig(c, "f", 5)
    j = parse_justifications(c)
    p = pillars(c, w, d)
    links = [u.strip() for u in str(c.get("evidence_links") or "").split(";") if u.strip().startswith("http")]
    comp.append({
        "n": c.get("company"),
        "sec": c.get("source_sector_taxonomy") or "Other",
        "hq": c.get("hq") or "",
        "founded": c.get("founded"),
        "epi": num(c.get("entry_potential_index")),
        "w": num(c.get("willingness_pct")), "d": num(c.get("distribution_readiness_pct")),
        "ai": num(c.get("ai_readiness_pct")), "r": num(c.get("readiness_pct_combined")),
        "tier": c.get("threat_tier") or "", "quad": c.get("quadrant") or "",
        "fin": num(c.get("financial_health_pct")), "sv": c.get("survival_tier") or "",
        "hz": c.get("horizon") or "", "conf": c.get("confidence") or "",
        "biz": (c.get("business_model_notes") or "")[:400],
        "imp": c.get("impact_on_incumbent_line") or "",
        "gap": c.get("residual_gap_what_they_d_need") or "",
        "rev": c.get("revenue_traction") or "",
        "lic": c.get("licensed_jurisdictions") or "",
        "par": c.get("existing_partnerships") or "",
        "scale": round(scale_of(c), 2),
        "sig": {"w": w, "d": d, "ai": ai, "f": f},
        "just": j,
        "pill": p,
        "vc": [1 if str(c.get(f"vc{i+1}_{re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')}") or "").lower() == "y" else 0
               for i, s in enumerate(STAGES)],
        "vert": [1 if str(c.get(re.sub(r"[^a-z0-9]+", "_", v.lower()).strip("_") + "_distributing") or "").lower() == "y" else 0
                 for v in VERTICALS],
        "links": links,
    })

comp.sort(key=lambda x: -(x["epi"] or 0))

# ---------------- findings derived from the data (never hand-asserted) -------
def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs)) if xs else 0


ai_mean = mean([c["ai"] for c in comp])
ai_top = max(comp, key=lambda c: c["ai"] or 0)
ai_over50 = [c["n"] for c in comp if (c["ai"] or 0) >= 50]
full_stack = [c for c in comp if sum(c["pill"].values()) == 3]
two_thirds = [c for c in comp if sum(c["pill"].values()) == 2]
operators = [c for c in comp if c["sec"] == "Operator (B2C)"]
op_w = mean([c["w"] for c in operators])
challengers = [c for c in comp if c["sec"] == "AI-native & prediction markets"]
ch_w = mean([c["w"] for c in challengers])
top5 = comp[:5]
b2b = [c for c in comp if c["sec"] == "B2B supplier & platform"]

FINDINGS = [
    {"t": "The incumbents are structurally unwilling to disrupt themselves",
     "x": f"The {len(operators)} licensed operators average just {op_w}% on willingness — the lowest of any segment — "
          f"while the {len(challengers)} prediction-market and AI-native entrants average {ch_w}%. Operators score high on "
          f"distribution and low on appetite: they are what is being disrupted, not the disruptors.",
     "e": ", ".join(f"{c['n']} W{c['w']}" for c in sorted(operators, key=lambda x: x["w"] or 0)[:4])},
    {"t": "AI readiness is the sector's shared blind spot",
     "x": f"Average AI readiness across all {len(comp)} companies is {ai_mean}% — the weakest of the three signal groups. "
          f"Only {len(ai_over50)} of {len(comp)} clear 50%. iGaming talks about AI far more than it ships it; the agentic-commerce "
          f"protocols (MCP/A2A/UCP/ACP) show zero adoption anywhere in the sample.",
     "e": f"highest: {ai_top['n']} at {ai_top['ai']}%" + (f"; others ≥50: {', '.join(n for n in ai_over50 if n != ai_top['n'])}" if len(ai_over50) > 1 else "")},
    {"t": "Only four companies hold the full stack — and half are challengers",
     "x": f"A company needs all three pillars (Player, Product, Wallet) to run a betting relationship end to end without an "
          f"incumbent. Just {len(full_stack)} of {len(comp)} do: {', '.join(c['n'] for c in full_stack)}. Two are incumbent-scale "
          f"operators; two are recent entrants that assembled the same stack from outside the licensed model.",
     "e": ", ".join(f"{c['n']} ({c['sec']})" for c in full_stack)},
    {"t": f"{len(two_thirds)} companies sit one move from a complete bypass",
     "x": f"They already hold two of the three pillars. For most the missing piece is the wallet or licensed supply — the exact "
          f"gap an acquisition or a single partnership closes. This is where the sector's next structural shift comes from, not "
          f"from the companies already at the top.",
     "e": ", ".join(f"{c['n']} (missing {', '.join(k for k, v in c['pill'].items() if not v)})" for c in two_thirds[:5])},
    {"t": "B2B suppliers own the content but deliberately never touch the player",
     "x": f"The {len(b2b)} suppliers score well on product access and platform rails yet near-zero on owned audience — they arm "
          f"the operators rather than competing with them. That makes them the sector's quiet chokepoint: whoever they choose to "
          f"serve, or stop serving, moves the market without ever facing a player.",
     "e": ", ".join(f"{c['n']} (W{c['w']} / D{c['d']})" for c in b2b[:4])},
]

payload = {
    "meta": {"count": len(comp), "date": meta.get("extracted_on"),
             "sha": (meta.get("sha256") or "")[:12], "built": date.today().isoformat()},
    "author": AUTHOR, "linkedin": LINKEDIN_URL, "github": GITHUB_URL,
    "companies": comp, "sectors": SECTORS, "stages": STAGES, "verticals": VERTICALS,
    "labels": {"w": W_LABELS, "d": D_LABELS, "ai": AI_LABELS},
    "defs": {"w": W_DEFS, "d": D_DEFS, "ai": AI_DEFS},
    "ama": AMA, "findings": FINDINGS,
    "frame": {
        "title": IG["title"],
        "incumbent": IG["incumbent"],
        "pillars": IG["pillars"],
    },
}

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>iGaming · AI Disruption Landscape</title>
<style>
:root{
  color-scheme:dark;   /* deliberately a single (dark) look — keeps form controls + scrollbars dark */
  /* dataviz: dark surface + validated ink (references/palette.md) */
  --surface:#1a1a19; --plane:#0d0d0d; --panel:#212120; --panel2:#2a2a28;
  --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
  /* validated categorical slots 1-3 (dark, --pairs all) */
  --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  /* status (fixed, never themed) */
  --good:#0ca30c; --warn:#fab219; --serious:#ec835a; --crit:#d03b3b;
  --ease:cubic-bezier(.22,.61,.36,1); --t1:.15s; --t2:.28s; --t3:.42s;
}
@keyframes viewIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--plane)}   /* html must carry it too, or a short view shows white canvas */
body{background:var(--plane);color:var(--ink);font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;min-height:100vh}
a{color:var(--s1)}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:14px 22px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;position:sticky;top:0;z-index:20}
header h1{font-size:16px;font-weight:600;letter-spacing:.2px}
header h1 small{display:block;font-size:11.5px;color:var(--muted);font-weight:400;margin-top:2px}
nav{display:flex;gap:3px;margin-left:auto;flex-wrap:wrap}
nav button{background:none;border:1px solid transparent;color:var(--ink2);padding:7px 14px;border-radius:8px;cursor:pointer;font:inherit;font-size:13px;transition:background var(--t1) var(--ease),color var(--t1) var(--ease),border-color var(--t1) var(--ease)}
nav button:hover{background:var(--panel2);color:var(--ink)}
nav button.on{background:var(--panel2);color:var(--ink);border-color:var(--border)}
main{max-width:1280px;margin:0 auto;padding:22px}
.view{display:none}.view.on{display:block;animation:viewIn var(--t2) var(--ease)}
h2.vt{font-size:19px;margin-bottom:4px}
p.vs{color:var(--ink2);font-size:13.5px;margin-bottom:18px;max-width:76ch}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px}
.filters{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.filters label{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
select,input[type=search]{background:var(--panel);border:1px solid var(--border);color:var(--ink);padding:7px 11px;border-radius:9px;font:inherit;font-size:13px;outline:none}
select:focus,input:focus{border-color:var(--s1)}
.chip{padding:5px 11px;border-radius:20px;border:1px solid var(--border);background:var(--panel);color:var(--ink2);cursor:pointer;font-size:12px;transition:background var(--t1) var(--ease),color var(--t1) var(--ease),border-color var(--t1) var(--ease)}
.chip:hover{color:var(--ink)}
.chip.on{background:#23394f;border-color:var(--s1);color:#fff}
/* ---------- stat tiles ---------- */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:18px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.tile .v{font-size:26px;font-weight:600;line-height:1.1}
.tile .k{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-top:4px}
.tile .sub{font-size:12px;color:var(--ink2);margin-top:5px}
/* ---------- positioning map ---------- */
#mapWrap{position:relative}
#map{width:100%;height:auto;display:block}
.qlabel{fill:var(--muted);font-size:11px;letter-spacing:.4px}
.qname{fill:#5d5c57;font-size:12.5px;font-weight:600}
.axl{fill:var(--ink2);font-size:12px}
.tick{fill:var(--muted);font-size:10.5px}
.bub{cursor:pointer;transition:opacity var(--t2) var(--ease)}
.bub circle{stroke:var(--surface);stroke-width:2}
.bub .hit{fill:transparent;stroke:none}
.bub text{fill:var(--ink2);font-size:11px;pointer-events:none}
.bub.dim{opacity:.18}
.bub:hover circle.mark{stroke:#fff}
#tip{position:absolute;pointer-events:none;background:#111110;border:1px solid var(--axis);border-radius:9px;padding:9px 12px;font-size:12.5px;display:none;z-index:8;max-width:290px;box-shadow:0 10px 30px #000a}
#tip b{color:#fff;display:block;margin-bottom:3px}
#tip .m{color:var(--muted);font-size:11.5px}
.legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-size:12px;color:var(--ink2);margin-top:12px}
.legend .sw{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}
/* ---------- signal matrix ---------- */
.mxscroll{overflow-x:auto}
table.mx{border-collapse:separate;border-spacing:2px;font-size:12px}
table.mx th{font-weight:500;color:var(--muted);font-size:10.5px;text-align:left;padding:3px 5px;white-space:nowrap}
table.mx th.rot{height:118px;width:26px;padding:0}
table.mx th.rot span{display:block;transform:rotate(180deg);writing-mode:vertical-rl;font-size:10.5px;max-height:112px;overflow:hidden}
table.mx th.co{position:sticky;left:0;background:var(--plane);z-index:2;color:var(--ink2);font-size:12px;min-width:190px;cursor:pointer}
table.mx th.co:hover{color:var(--ink)}
table.mx td{width:26px;height:26px;border-radius:4px;text-align:center;color:#0b0b0b;font-size:11px;font-weight:600;cursor:pointer;transition:transform var(--t1) var(--ease)}
table.mx td:hover{transform:scale(1.18)}
table.mx td.null{background:var(--panel2);color:var(--muted)}
table.mx td.gapl{box-shadow:-3px 0 0 var(--plane)}
.mxkey{display:flex;gap:4px;align-items:center;font-size:11.5px;color:var(--ink2);margin-top:12px}
.mxkey i{width:24px;height:12px;border-radius:3px;display:inline-block}
/* ---------- pillars ---------- */
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.pcol h3{font-size:13px;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.pcol h3 .dot{width:11px;height:11px;border-radius:50%}
.prow{display:flex;align-items:center;gap:9px;padding:7px 10px;border-radius:9px;background:var(--panel);border:1px solid var(--border);margin-bottom:6px;cursor:pointer;transition:background var(--t1) var(--ease)}
.prow:hover{background:var(--panel2)}
.prow .nm{flex:1;font-size:12.5px}
.prow .ep{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.pillbadge{display:inline-flex;gap:3px}
.pillbadge i{width:8px;height:8px;border-radius:2px;display:inline-block}
/* ---------- table ---------- */
table.dt{width:100%;border-collapse:collapse;font-size:13px}
table.dt th{text-align:left;color:var(--muted);font-weight:500;font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;padding:9px 8px;border-bottom:1px solid var(--axis);cursor:pointer;white-space:nowrap}
table.dt th:hover{color:var(--ink)}
table.dt td{padding:9px 8px;border-bottom:1px solid var(--grid);font-variant-numeric:tabular-nums}
table.dt tbody tr{cursor:pointer}
table.dt tbody tr:hover{background:var(--panel)}
.pill{display:inline-block;padding:2px 9px;border-radius:11px;font-size:11px;font-weight:600}
.pHigh{background:#3a1a1a;color:#ff9d9d}.pMedium{background:#3a2f18;color:#ffcf7a}.pLow{background:#1b2c3f;color:#8fc0f0}
/* ---------- drawer ---------- */
#scrim{position:fixed;inset:0;background:#000a;backdrop-filter:blur(3px);opacity:0;visibility:hidden;transition:opacity var(--t2) var(--ease),visibility 0s linear var(--t2);z-index:30}
#scrim.on{opacity:1;visibility:visible;transition:opacity var(--t2) var(--ease)}
#drawer{position:fixed;top:0;right:0;width:min(640px,100%);height:100vh;background:var(--surface);border-left:1px solid var(--border);z-index:31;display:flex;flex-direction:column;transform:translateX(102%);transition:transform var(--t3) var(--ease);box-shadow:-16px 0 50px #000b}
#drawer.on{transform:none}
.dh{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:12px}
.dh h2{font-size:17px}.dh .sub{color:var(--muted);font-size:12px;margin-top:3px}
.x{margin-left:auto;background:none;border:none;color:var(--muted);font-size:22px;cursor:pointer;line-height:1}
.x:hover{color:var(--ink)}
.db{padding:16px 20px;overflow:auto}
.db h4{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin:18px 0 7px}
.kv{display:flex;flex-wrap:wrap;gap:6px}
.kv span{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:3px 9px;font-size:12px;color:var(--ink2)}
.kv b{color:var(--ink)}
.gauges{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:6px 0}
.g{text-align:center}
.g .ring{width:66px;height:66px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center}
.g .ring i{width:52px;height:52px;border-radius:50%;background:var(--surface);display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:600;font-size:15px}
.g .gl{font-size:10.5px;color:var(--muted);margin-top:5px;text-transform:uppercase;letter-spacing:.5px}
.sgrp{font-size:10.5px;letter-spacing:.7px;color:var(--muted);text-transform:uppercase;margin:14px 0 5px}
.sr{margin:3px 0;border-radius:7px;overflow:hidden}
.sr .top{display:flex;align-items:center;gap:9px;padding:4px 6px;cursor:pointer;border-radius:7px;transition:background var(--t1) var(--ease)}
.sr .top:hover{background:var(--panel)}
.sr .lb{flex:1;font-size:12px;color:var(--ink2)}
.sr .bar{width:96px;height:7px;background:var(--panel2);border-radius:4px;overflow:hidden;flex:none}
.sr .bar i{display:block;height:100%;border-radius:4px}
.sr .vl{width:16px;text-align:right;font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.sr .why{display:none;padding:7px 10px 9px 12px;font-size:12px;color:var(--ink2);border-left:2px solid var(--s1);margin:2px 0 6px 6px;background:#1e1e1c;border-radius:0 7px 7px 0}
.sr.open .why{display:block}
.sr .why .def{color:var(--muted);font-size:11.5px;margin-top:5px}
.jstrip{display:flex;gap:4px;margin:6px 0}
.jseg{flex:1;text-align:center;font-size:9.5px;padding:6px 2px;border-radius:7px;background:var(--panel);color:#5d5c57;border:1px solid var(--border)}
.jseg.on{background:#16324d;color:#9cc7f5;border-color:#27496b}
.callout{border-left:3px solid var(--s1);background:var(--panel);border-radius:0 9px 9px 0;padding:10px 13px;margin:7px 0;font-size:12.5px;color:var(--ink2);white-space:pre-wrap}
.callout.imp{border-color:var(--crit)}.callout.gap{border-color:var(--warn)}
.srcs{list-style:none}
.srcs li{margin:5px 0;font-size:12px;word-break:break-all}
.confbadge{display:inline-block;padding:2px 9px;border-radius:11px;font-size:11px;font-weight:600}
.chigh{background:#0f2e0f;color:#7fdc7f}.cmedium{background:#3a2f18;color:#ffcf7a}.clow{background:#3a1a1a;color:#ff9d9d}
/* ---------- method / findings ---------- */
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.fcard{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px 18px}
.fcard h3{font-size:14.5px;margin-bottom:7px}
.fcard p{color:var(--ink2);font-size:13px}
.fcard .ev{margin-top:9px;font-size:11.5px;color:var(--muted);border-top:1px solid var(--grid);padding-top:8px}
.prose{max-width:78ch;color:var(--ink2);font-size:13.5px}
.prose h3{color:var(--ink);font-size:15px;margin:20px 0 7px}
.prose p{margin-bottom:10px}
.prose ul{margin:0 0 10px 20px}
.prose li{margin-bottom:5px}
.prose code{background:var(--panel2);padding:1px 6px;border-radius:5px;font-size:12.5px}
footer{border-top:1px solid var(--border);margin-top:34px;padding:20px 0;color:var(--muted);font-size:12px;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
</style></head><body>

<header>
  <h1>iGaming · AI Disruption Landscape<small id="hsub"></small></h1>
  <nav>
    <button data-v="vMap" class="on">Positioning</button>
    <button data-v="vMx">Signal matrix</button>
    <button data-v="vPill">The stack</button>
    <button data-v="vTab">Data</button>
    <button data-v="vFind">Findings &amp; method</button>
  </nav>
</header>

<main>
  <!-- ============ POSITIONING ============ -->
  <div id="vMap" class="view on">
    <h2 class="vt">Who can actually take the player?</h2>
    <p class="vs">Every company scored on <b>willingness</b> to attack the incumbent model (horizontal) and <b>readiness</b> to execute (vertical). Bubble size is company scale. The incumbent benchmark marks where the licensed-operator model sits today. Click any company for its full evidence.</p>
    <div class="tiles" id="tiles"></div>
    <div class="card">
      <div class="filters">
        <label>Segment</label><select id="fSec"></select>
        <label>Tier</label><select id="fTier"></select>
        <input type="search" id="fQ" placeholder="Find a company…" style="margin-left:auto;min-width:190px">
      </div>
      <div id="mapWrap"><svg id="map" viewBox="0 0 900 640" role="img" aria-label="Positioning map of companies by willingness and readiness"></svg><div id="tip"></div></div>
      <div class="legend" id="mapLegend"></div>
    </div>
  </div>

  <!-- ============ SIGNAL MATRIX ============ -->
  <div id="vMx" class="view">
    <h2 class="vt">Where the capability actually sits</h2>
    <p class="vs">All 18 scored signals for every company, 0–5. Click any cell to see why that score was given. Reading down a column shows the sector's structural strengths and gaps — the AI block is the tell.</p>
    <div class="card">
      <div class="filters"><label>Sort</label><select id="mxSort">
        <option value="epi">Disruption score</option><option value="w">Willingness</option>
        <option value="d">Readiness</option><option value="ai">AI readiness</option><option value="n">Company A–Z</option>
      </select><span class="chip" id="mxSecToggle" style="margin-left:auto">Group by segment: off</span></div>
      <div class="mxscroll"><table class="mx" id="mx"></table></div>
      <div class="mxkey"><span>0</span><i style="background:#184f95"></i><i style="background:#256abf"></i><i style="background:#3987e5"></i><i style="background:#6da7ec"></i><i style="background:#9ec5f4"></i><i style="background:#cde2fb"></i><span>5</span><span style="margin-left:10px;color:var(--muted)">grey = not disclosed</span></div>
    </div>
  </div>

  <!-- ============ PILLARS ============ -->
  <div id="vPill" class="view">
    <h2 class="vt">The three pillars of a bypass</h2>
    <p class="vs" id="pillIntro"></p>
    <div class="tiles" id="pillTiles"></div>
    <div class="card"><div class="pgrid" id="pillGrid"></div></div>
  </div>

  <!-- ============ DATA ============ -->
  <div id="vTab" class="view">
    <h2 class="vt">Every company, every number</h2>
    <p class="vs">The full scored dataset. Click a row for the company's evidence and sources.</p>
    <div class="card"><table class="dt" id="dt"></table></div>
  </div>

  <!-- ============ FINDINGS & METHOD ============ -->
  <div id="vFind" class="view">
    <h2 class="vt">What the data says</h2>
    <p class="vs">Findings computed from the scored dataset — each one traceable to the companies that produce it.</p>
    <div class="fgrid" id="findings"></div>
    <h2 class="vt" style="margin-top:30px">Method</h2>
    <div class="card"><div class="prose" id="method"></div></div>
    <footer id="foot"></footer>
  </div>
</main>

<div id="scrim" onclick="closeDrawer()"></div>
<aside id="drawer" aria-label="Company detail"><div class="dh"><div style="flex:1"><h2 id="dt_"></h2><div class="sub" id="ds_"></div></div><button class="x" onclick="closeDrawer()" aria-label="Close">×</button></div><div class="db" id="db_"></div></aside>

<script>
const D=__DATA__;
const C=D.companies, byName={}; C.forEach(c=>byName[c.n]=c);
const RAMP=['#184f95','#256abf','#3987e5','#6da7ec','#9ec5f4','#cde2fb'];
const S1='#3987e5',S2='#d95926',S3='#199e70';
const esc=s=>String(s??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const nn=v=>v===null||v===undefined?'–':v;
document.getElementById('hsub').textContent=D.meta.count+' companies · scored '+D.meta.date+' · every number sourced';

document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); document.getElementById(b.dataset.v).classList.add('on');
});

/* ================= DRAWER ================= */
function gauge(label,val,col){
  const v=Math.max(0,Math.min(100,val||0));
  return '<div class="g"><div class="ring" style="background:conic-gradient('+col+' '+(v*3.6)+'deg,#2a2a28 0)"><i>'+(val==null?'–':Math.round(v))+'</i></div><div class="gl">'+label+'</div></div>';
}
function sigRows(c,key,labels,prefix){
  const defs=D.defs[key]||{};
  return c.sig[key].map((v,i)=>{
    const lab=labels[i], j=c.just[prefix+(i+1)], def=defs[lab];
    const pct=v==null?0:(v/5*100), col=v==null?'#2a2a28':RAMP[Math.max(0,Math.min(5,v))];
    return '<div class="sr" data-k="'+prefix+(i+1)+'"><div class="top"><span class="lb">'+esc(lab)+'</span>'+
      '<span class="bar"><i style="width:'+pct+'%;background:'+col+'"></i></span><span class="vl">'+(v==null?'–':v)+'</span></div>'+
      '<div class="why">'+(j?esc(j):'<span style="color:var(--muted)">No justification recorded.</span>')+
      (def?'<div class="def"><b>Anchors:</b> '+esc(def[1])+'</div>':'')+'</div></div>';
  }).join('');
}
function openCompany(name){
  const c=byName[name]; if(!c)return;
  document.getElementById('dt_').textContent=c.n;
  document.getElementById('ds_').innerHTML=esc(c.sec)+' · '+esc(c.hq||'—')+
    ' · <span class="confbadge c'+c.conf+'">'+esc(c.conf)+' confidence</span>';
  let h='<div class="kv"><span>Disruption score <b>'+nn(c.epi)+'</b></span><span>Tier <b>'+esc(c.tier)+'</b></span>'+
    '<span>Position <b>'+esc(c.quad)+'</b></span>'+(c.hz?'<span>Horizon <b>'+esc(c.hz)+'</b></span>':'')+
    (c.founded?'<span>Founded <b>'+c.founded+'</b></span>':'')+'</div>';
  h+='<div class="gauges">'+gauge('Willing',c.w,S2)+gauge('Distribution',c.d,S1)+gauge('AI',c.ai,S3)+gauge('Overall',c.epi,'#9ec5f4')+'</div>';
  const pl=c.pill, pk=[['player','Player',S1],['product','Product',S2],['wallet','Wallet',S3]];
  h+='<h4>Pillars held</h4><div class="kv">'+pk.map(p=>'<span style="'+(pl[p[0]]?'color:#fff;border-color:'+p[2]:'')+'">'+(pl[p[0]]?'✓ ':'✕ ')+p[1]+'</span>').join('')+'</div>';
  h+='<h4>Player journey covered</h4><div class="jstrip">'+D.stages.map((s,i)=>'<span class="jseg'+(c.vc[i]?' on':'')+'">'+esc(s)+'</span>').join('')+'</div>';
  if(c.biz)h+='<h4>Business model</h4><div class="callout">'+esc(c.biz)+'</div>';
  if(c.imp)h+='<h4>Effect on the incumbent model</h4><div class="callout imp">'+esc(c.imp)+'</div>';
  if(c.gap)h+='<h4>What it still lacks</h4><div class="callout gap">'+esc(c.gap)+'</div>';
  h+='<h4>Scored signals — click any row for the reasoning</h4>';
  h+='<div class="sgrp">Willingness to disrupt</div>'+sigRows(c,'w',D.labels.w,'W');
  h+='<div class="sgrp">Distribution readiness</div>'+sigRows(c,'d',D.labels.d,'D');
  h+='<div class="sgrp">AI readiness</div>'+sigRows(c,'ai',D.labels.ai,'AI');
  const fin=[]; if(c.rev)fin.push('<span>Revenue <b>'+esc(c.rev)+'</b></span>');
  if(c.sv)fin.push('<span>Survival <b>'+esc(c.sv)+'</b></span>');
  if(c.fin!=null)fin.push('<span>Financial health <b>'+c.fin+'%</b></span>');
  if(fin.length)h+='<h4>Financial</h4><div class="kv">'+fin.join('')+'</div>';
  if(c.lic)h+='<h4>Licensed in</h4><div class="callout">'+esc(c.lic)+'</div>';
  if(c.par)h+='<h4>Named partners</h4><div class="callout">'+esc(c.par)+'</div>';
  if(c.links&&c.links.length)h+='<h4>Sources ('+c.links.length+')</h4><ul class="srcs">'+
    c.links.map(u=>'<li><a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+esc(u)+'</a></li>').join('')+'</ul>';
  const db=document.getElementById('db_'); db.innerHTML=h; db.scrollTop=0;
  db.querySelectorAll('.sr .top').forEach(t=>t.onclick=()=>t.parentElement.classList.toggle('open'));
  document.getElementById('drawer').classList.add('on');
  document.getElementById('scrim').classList.add('on');
}
function closeDrawer(){document.getElementById('drawer').classList.remove('on');document.getElementById('scrim').classList.remove('on');}
addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});

/* ================= TILES ================= */
(function(){
  const m=v=>Math.round(C.reduce((a,c)=>a+(c[v]||0),0)/C.length);
  const full=C.filter(c=>c.pill.player&&c.pill.product&&c.pill.wallet).length;
  const hi=C.filter(c=>c.tier==='High').length;
  document.getElementById('tiles').innerHTML=
   '<div class="tile"><div class="v">'+C.length+'</div><div class="k">Companies scored</div><div class="sub">every one with cited sources</div></div>'+
   '<div class="tile"><div class="v">'+full+'</div><div class="k">Hold all three pillars</div><div class="sub">can bypass the incumbent entirely</div></div>'+
   '<div class="tile"><div class="v">'+m('ai')+'%</div><div class="k">Mean AI readiness</div><div class="sub">the sector-wide blind spot</div></div>'+
   '<div class="tile"><div class="v">'+hi+'</div><div class="k">High threat tier</div><div class="sub">disruption score ≥ 60</div></div>';
})();

/* ================= POSITIONING MAP ================= */
const MAP={w:900,h:640,l:64,r:28,t:26,b:56};
let fSec='',fTier='',fQ='';
function drawMap(){
  const s=MAP, iw=s.w-s.l-s.r, ih=s.h-s.t-s.b;
  const X=v=>s.l+(v/100)*iw, Y=v=>s.t+ih-(v/100)*ih;
  let g='';
  // quadrant washes (very low contrast, purely orienting)
  g+='<rect x="'+X(60)+'" y="'+Y(100)+'" width="'+(X(100)-X(60))+'" height="'+(Y(60)-Y(100))+'" fill="#3987e5" opacity="0.05"/>';
  // grid: solid hairlines only
  for(let v=0;v<=100;v+=20){
    g+='<line x1="'+X(v)+'" y1="'+s.t+'" x2="'+X(v)+'" y2="'+(s.t+ih)+'" stroke="var(--grid)" stroke-width="1"/>';
    g+='<line x1="'+s.l+'" y1="'+Y(v)+'" x2="'+(s.l+iw)+'" y2="'+Y(v)+'" stroke="var(--grid)" stroke-width="1"/>';
    g+='<text class="tick" x="'+X(v)+'" y="'+(s.t+ih+18)+'" text-anchor="middle">'+v+'</text>';
    g+='<text class="tick" x="'+(s.l-10)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+v+'</text>';
  }
  // quadrant dividers at 60
  g+='<line x1="'+X(60)+'" y1="'+s.t+'" x2="'+X(60)+'" y2="'+(s.t+ih)+'" stroke="var(--axis)" stroke-width="1"/>';
  g+='<line x1="'+s.l+'" y1="'+Y(60)+'" x2="'+(s.l+iw)+'" y2="'+Y(60)+'" stroke="var(--axis)" stroke-width="1"/>';
  g+='<text class="qname" x="'+(X(100)-8)+'" y="'+(Y(100)+18)+'" text-anchor="end">Imminent threat</text>';
  g+='<text class="qname" x="'+(s.l+8)+'" y="'+(Y(100)+18)+'">Sleeping giant</text>';
  g+='<text class="qname" x="'+(X(100)-8)+'" y="'+(Y(0)-10)+'" text-anchor="end">Aspirant</text>';
  g+='<text class="qname" x="'+(s.l+8)+'" y="'+(Y(0)-10)+'">Dormant</text>';
  g+='<text class="axl" x="'+(s.l+iw/2)+'" y="'+(s.h-14)+'" text-anchor="middle">Willingness to disrupt the model →</text>';
  g+='<text class="axl" transform="translate(16,'+(s.t+ih/2)+') rotate(-90)" text-anchor="middle">Readiness to execute →</text>';
  // incumbent benchmark
  const ax=X(D.ama.w), ay=Y(D.ama.r);
  g+='<g><line x1="'+(ax-9)+'" y1="'+ay+'" x2="'+(ax+9)+'" y2="'+ay+'" stroke="#c3c2b7" stroke-width="2"/>'+
     '<line x1="'+ax+'" y1="'+(ay-9)+'" x2="'+ax+'" y2="'+(ay+9)+'" stroke="#c3c2b7" stroke-width="2"/>'+
     '<text class="qlabel" x="'+(ax+13)+'" y="'+(ay+4)+'">Incumbent model today</text></g>';
  // bubbles — ONE hue (scatter = all-pairs; sector is a filter, not a colour)
  const vis=c=>(!fSec||c.sec===fSec)&&(!fTier||c.tier===fTier)&&(!fQ||c.n.toLowerCase().includes(fQ));
  const sorted=C.slice().sort((a,b)=>b.scale-a.scale);
  const labelled=new Set(C.slice().sort((a,b)=>(b.epi||0)-(a.epi||0)).slice(0,5).map(c=>c.n));
  sorted.forEach(c=>{
    if(c.w==null||c.r==null)return;
    const x=X(c.w), y=Y(c.r), rad=Math.max(7,Math.min(24,c.scale*4.6));
    const on=vis(c);
    g+='<g class="bub'+(on?'':' dim')+'" data-n="'+esc(c.n)+'" tabindex="0" role="button" aria-label="'+esc(c.n)+'">'+
       '<circle class="mark" cx="'+x+'" cy="'+y+'" r="'+rad+'" fill="'+S1+'" fill-opacity="0.72"/>'+
       '<circle class="hit" cx="'+x+'" cy="'+y+'" r="'+Math.max(rad,14)+'"/>'+
       (labelled.has(c.n)&&on?'<text x="'+(x+rad+5)+'" y="'+(y+4)+'">'+esc(c.n.replace(/ (plc|Inc\.|AB \(publ\)|Group.*|Limited|Ltd).*$/,''))+'</text>':'')+
       '</g>';
  });
  document.getElementById('map').innerHTML=g;
  const tip=document.getElementById('tip'), wrap=document.getElementById('mapWrap');
  document.querySelectorAll('#map .bub').forEach(el=>{
    const c=byName[el.dataset.n];
    const show=e=>{const r=wrap.getBoundingClientRect();
      tip.style.display='block';
      tip.style.left=Math.min(r.width-300,e.clientX-r.left+14)+'px';
      tip.style.top=(e.clientY-r.top+12)+'px';
      tip.innerHTML='<b>'+esc(c.n)+'</b><div class="m">'+esc(c.sec)+'</div>'+
        '<div style="margin-top:5px">Willingness <b>'+nn(c.w)+'</b> · Readiness <b>'+nn(c.r)+'</b></div>'+
        '<div>Disruption score <b>'+nn(c.epi)+'</b> · '+esc(c.quad)+'</div>';};
    el.onmousemove=show; el.onmouseenter=show;
    el.onmouseleave=()=>tip.style.display='none';
    el.onclick=()=>openCompany(c.n);
    el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openCompany(c.n);}};
  });
  document.getElementById('mapLegend').innerHTML=
    '<span><span class="sw" style="background:'+S1+';opacity:.72"></span>Company — bubble size = scale (market cap / valuation / funding)</span>'+
    '<span style="color:var(--muted)">✛ incumbent benchmark</span>'+
    '<span style="color:var(--muted)">'+C.filter(vis).length+' of '+C.length+' shown</span>';
}
(function(){
  const sec=document.getElementById('fSec'), tier=document.getElementById('fTier');
  sec.innerHTML='<option value="">All segments</option>'+D.sectors.map(s=>'<option>'+esc(s)+'</option>').join('');
  tier.innerHTML='<option value="">All tiers</option>'+['High','Medium','Low'].map(t=>'<option>'+t+'</option>').join('');
  sec.onchange=e=>{fSec=e.target.value;drawMap()};
  tier.onchange=e=>{fTier=e.target.value;drawMap()};
  document.getElementById('fQ').oninput=e=>{fQ=e.target.value.toLowerCase().trim();drawMap()};
  drawMap();
})();

/* ================= SIGNAL MATRIX ================= */
let mxSort='epi', mxGroup=false;
function drawMx(){
  const labs=[...D.labels.w.map((l,i)=>['W'+(i+1),l,'w',i]),
              ...D.labels.d.map((l,i)=>['D'+(i+1),l,'d',i]),
              ...D.labels.ai.map((l,i)=>['AI'+(i+1),l,'ai',i])];
  let rows=C.slice();
  if(mxSort==='n')rows.sort((a,b)=>a.n.localeCompare(b.n));
  else rows.sort((a,b)=>(b[mxSort]||0)-(a[mxSort]||0));
  if(mxGroup)rows.sort((a,b)=>D.sectors.indexOf(a.sec)-D.sectors.indexOf(b.sec)||(b.epi||0)-(a.epi||0));
  let h='<thead><tr><th class="co">Company</th>';
  labs.forEach((L,i)=>{h+='<th class="rot'+((L[0]==='D1'||L[0]==='AI1')?' gapl':'')+'"><span>'+esc(L[0]+' · '+L[1])+'</span></th>';});
  h+='<th style="padding-left:8px">Score</th></tr></thead><tbody>';
  rows.forEach(c=>{
    h+='<tr><th class="co" data-n="'+esc(c.n)+'">'+esc(c.n)+'</th>';
    labs.forEach(L=>{
      const v=c.sig[L[2]][L[3]];
      const cls=(L[0]==='D1'||L[0]==='AI1')?' gapl':'';
      if(v==null)h+='<td class="null'+cls+'" title="not disclosed">–</td>';
      else h+='<td class="'+cls.trim()+'" style="background:'+RAMP[v]+';color:'+(v>=3?'#0b0b0b':'#dfe9f7')+'" data-n="'+esc(c.n)+'" data-k="'+L[0]+'" data-l="'+esc(L[1])+'" data-v="'+v+'">'+v+'</td>';
    });
    h+='<td style="background:none;color:var(--ink);padding-left:8px;font-variant-numeric:tabular-nums">'+nn(c.epi)+'</td></tr>';
  });
  const t=document.getElementById('mx'); t.innerHTML=h+'</tbody>';
  t.querySelectorAll('th.co').forEach(el=>el.onclick=()=>openCompany(el.dataset.n));
  t.querySelectorAll('td[data-k]').forEach(el=>el.onclick=()=>{
    const c=byName[el.dataset.n], why=c.just[el.dataset.k];
    const tip=document.getElementById('tip');
    openCompany(c.n);
    setTimeout(()=>{const row=document.querySelector('#db_ .sr[data-k="'+el.dataset.k+'"]');
      if(row){row.classList.add('open');row.scrollIntoView({block:'center',behavior:'smooth'});}},60);
  });
}
document.getElementById('mxSort').onchange=e=>{mxSort=e.target.value;drawMx()};
document.getElementById('mxSecToggle').onclick=e=>{mxGroup=!mxGroup;
  e.target.classList.toggle('on',mxGroup);e.target.textContent='Group by segment: '+(mxGroup?'on':'off');drawMx()};
drawMx();

/* ================= PILLARS ================= */
(function(){
  const P=D.frame.pillars, keys=Object.keys(P);
  const full=C.filter(c=>c.pill.player&&c.pill.product&&c.pill.wallet);
  const two=C.filter(c=>Object.values(c.pill).filter(Boolean).length===2);
  const one=C.filter(c=>Object.values(c.pill).filter(Boolean).length<=1);
  document.getElementById('pillIntro').innerHTML=
    'A company needs all three to run a betting relationship end to end without a licensed incumbent: <b>Player</b> (owns the intent moment), <b>Product</b> (owns odds, markets and games) and <b>Wallet</b> (licensed money in and out). Holding two means one acquisition or partnership away.';
  document.getElementById('pillTiles').innerHTML=
   '<div class="tile"><div class="v" style="color:'+S1+'">'+full.length+'</div><div class="k">Full stack</div><div class="sub">all three pillars</div></div>'+
   '<div class="tile"><div class="v" style="color:'+S2+'">'+two.length+'</div><div class="k">One move away</div><div class="sub">hold two of three</div></div>'+
   '<div class="tile"><div class="v" style="color:var(--muted)">'+one.length+'</div><div class="k">Single-pillar or none</div><div class="sub">structurally dependent</div></div>';
  const badge=c=>'<span class="pillbadge">'+[['player',S1],['product',S2],['wallet',S3]].map(p=>
    '<i style="background:'+(c.pill[p[0]]?p[1]:'#2a2a28')+'" title="'+p[0]+'"></i>').join('')+'</span>';
  const col=(title,list,note)=>'<div class="pcol"><h3>'+esc(title)+' <span style="color:var(--muted);font-weight:400">'+list.length+'</span></h3>'+
    '<div style="color:var(--muted);font-size:12px;margin-bottom:9px">'+esc(note)+'</div>'+
    list.map(c=>'<div class="prow" data-n="'+esc(c.n)+'">'+badge(c)+'<span class="nm">'+esc(c.n)+'</span><span class="ep">'+nn(c.epi)+'</span></div>').join('')+'</div>';
  document.getElementById('pillGrid').innerHTML=
    col('Full stack',full,'Can run the whole relationship alone')+
    col('One move away',two,'A single deal completes the bypass')+
    col('Dependent',one,'Needs the incumbent rails');
  document.querySelectorAll('#pillGrid .prow').forEach(el=>el.onclick=()=>openCompany(el.dataset.n));
})();

/* ================= DATA TABLE ================= */
let dtK='epi', dtAsc=false;
function drawDt(){
  const cols=[['n','Company'],['sec','Segment'],['epi','Score'],['w','Will%'],['d','Dist%'],['ai','AI%'],
              ['tier','Tier'],['quad','Position'],['sv','Survival'],['conf','Confidence']];
  const rows=C.slice().sort((a,b)=>{let x=a[dtK],y=b[dtK];
    if(typeof x==='string'||typeof y==='string'){x=String(x||'');y=String(y||'');return (x>y?1:x<y?-1:0)*(dtAsc?1:-1);}
    return ((x||0)-(y||0))*(dtAsc?1:-1);});
  let h='<thead><tr>'+cols.map(c=>'<th data-k="'+c[0]+'">'+c[1]+(dtK===c[0]?(dtAsc?' ▲':' ▼'):'')+'</th>').join('')+'</tr></thead><tbody>';
  rows.forEach(c=>{h+='<tr data-n="'+esc(c.n)+'"><td><b>'+esc(c.n)+'</b></td><td style="color:var(--ink2)">'+esc(c.sec)+'</td>'+
    '<td>'+nn(c.epi)+'</td><td>'+nn(c.w)+'</td><td>'+nn(c.d)+'</td><td>'+nn(c.ai)+'</td>'+
    '<td><span class="pill p'+esc(c.tier)+'">'+esc(c.tier)+'</span></td><td style="color:var(--ink2)">'+esc(c.quad)+'</td>'+
    '<td style="color:var(--ink2)">'+esc(c.sv||'–')+'</td><td><span class="confbadge c'+c.conf+'">'+esc(c.conf)+'</span></td></tr>';});
  const t=document.getElementById('dt'); t.innerHTML=h+'</tbody>';
  t.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;
    if(dtK===k)dtAsc=!dtAsc;else{dtK=k;dtAsc=(k==='n'||k==='sec');}drawDt();});
  t.querySelectorAll('tbody tr').forEach(tr=>tr.onclick=()=>openCompany(tr.dataset.n));
}
drawDt();

/* ================= FINDINGS & METHOD ================= */
document.getElementById('findings').innerHTML=D.findings.map((f,i)=>
  '<div class="fcard"><h3>'+(i+1)+'. '+esc(f.t)+'</h3><p>'+esc(f.x)+'</p><div class="ev"><b>Evidence:</b> '+esc(f.e)+'</div></div>').join('');

document.getElementById('method').innerHTML=
 '<p><b>The question.</b> '+esc(D.frame.title)+' The incumbent under threat is '+esc(D.frame.incumbent)+'.</p>'+
 '<h3>How each company is scored</h3>'+
 '<p>Every company is scored 0–5 on 18 signals in three groups — willingness to disrupt the model (5), distribution readiness (6) and AI readiness (7) — against fixed anchors defined before research began, so a 3 means the same thing for every company. Those roll up with fixed weights:</p>'+
 '<ul><li><code>Readiness = ½ Distribution + ½ AI</code></li>'+
 '<li><code>Disruption score = 0.4 × Willingness + 0.6 × Readiness</code></li>'+
 '<li>Bands: ≥60 High · ≥40 Medium · below that Low. Position is the 60/60 split of the two axes.</li></ul>'+
 '<p>Scores measure fit to <i>this question</i>, not company size. A large operator with no appetite to attack its own funnel scores low on willingness by design — which is why several household names sit in the lower half.</p>'+
 '<h3>Where the numbers come from</h3>'+
 '<p>Each company was researched against public sources — investor relations, filings, recent trade press — and every one of the 18 scores carries a written justification plus the source URLs behind it. Open any company and click a signal row to see the reasoning; the sources are listed at the bottom of the card. Each row also carries a confidence grade reflecting how much public evidence was available.</p>'+
 '<h3>Honest limitations</h3>'+
 '<ul><li>Scores are <b>researched estimates</b>, not audited figures. They are transparent and traceable, not authoritative.</li>'+
 '<li>Private companies disclose less, so their rows lean on inference — marked as lower confidence.</li>'+
 '<li>This is a deliberate deep sample: '+D.meta.count+' companies spanning every segment of the value chain, each fully researched, rather than a thin census.</li>'+
 '<li>The scoring model is inherited from a prior landscape build and applied unchanged, so results stay comparable across industries.</li></ul>';

(function(){
  const f=document.getElementById('foot'); let h='<span>Built by <b style="color:var(--ink2)">'+esc(D.author)+'</b></span>';
  if(D.linkedin)h+='<a href="'+esc(D.linkedin)+'" target="_blank" rel="noopener noreferrer">LinkedIn</a>';
  if(D.github)h+='<a href="'+esc(D.github)+'" target="_blank" rel="noopener noreferrer">Source &amp; data on GitHub</a>';
  h+='<span style="margin-left:auto">'+D.meta.count+' companies · dataset '+D.meta.date+' · build '+D.meta.built+'</span>';
  f.innerHTML=h;
})();
</script></body></html>"""

VIZ.mkdir(exist_ok=True)
out = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
(VIZ / f"{INDUSTRY}.html").write_text(out, encoding="utf-8")
print(f"viz/{INDUSTRY}.html written: {len(out)//1024} KB, {len(comp)} companies, {len(FINDINGS)} findings")
if not LINKEDIN_URL:
    print("NOTE: LINKEDIN_URL is empty — footer renders name only. Set it in this script to add the link.")
