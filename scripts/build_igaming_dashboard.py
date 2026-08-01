"""Build viz/igaming.html — the iGaming disruption CONSTELLATION.

The identity of this artifact is the living star-sky from the travel project:
deep-space background, glowing sector-coloured stars, gentle perpetual drift,
ego-focus on click. Adapted to this dataset's strengths instead of fighting its
size: 25 deeply-researched companies (every one permanently labelled — impossible
at 553), ~70 external entities mined from the partnership fields as small
satellite stars, and faint sector ASTERISMS (constellation lines linking each
sector's stars). The evidence layer survives underneath: click any star and
every score opens into its written justification + cited sources.

Tabs: Constellation (hero) · Threat Board · Findings & Method.

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

AUTHOR = "Mukul Shrivas"
LINKEDIN_URL = ""   # <-- set to render the LinkedIn link (empty = name only)
GITHUB_URL = "https://github.com/mukewl/industry-ai-landscapes"

# signal vocabulary straight from the generator so nothing can drift
spec = importlib.util.spec_from_file_location("mw", ROOT / "scripts" / "make_workbook.py")
mw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mw)
IG = mw.INDUSTRIES[INDUSTRY]
W_LABELS = [n for n, _, _ in IG["w"]]
D_LABELS = [n for n, _, _ in IG["d"]]
AI_LABELS = [n for n, _, _ in mw.AI_SIGNALS]
W_DEFS = {n: a for n, _, a in IG["w"]}
D_DEFS = {n: a for n, _, a in IG["d"]}
AI_DEFS = {n: a for n, _, a in mw.AI_SIGNALS}
SECTORS = IG["sectors"]
STAGES = IG["stages"]

companies = json.loads((DATA / "companies.json").read_text(encoding="utf-8"))
meta = json.loads((DATA / "extract_meta.json").read_text(encoding="utf-8"))

AMA = {"w": 35, "d": 90, "ai": 40}
AMA["r"] = round(.5 * AMA["d"] + .5 * AMA["ai"])

# vivid sky palette — one hue per sector, every company star is permanently
# labelled so identity never rides on colour alone
SECCOL = {
    "Operator (B2C)": "#ff6b81",
    "B2B supplier & platform": "#ffb74d",
    "Data & odds": "#f0c84b",
    "Affiliate & media": "#22d3ee",
    "Payments & fintech": "#4ade80",
    "AI-native & prediction markets": "#60a5fa",
    "RegTech & compliance": "#e879f9",
    "Big Tech platform": "#b388ff",
}


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
    txt = str(c.get("evidence_notes") or "")
    out = {}
    for m in re.finditer(r"\b(W|D|AI|F)(\d+)=([0-9]+|None):\s*([^|]+)", txt):
        out[f"{m.group(1)}{m.group(2)}"] = m.group(4).strip()
    return out


def star_size(c):
    """Star radius: log $ scale (market cap → valuation → funding → FTE)."""
    for k in ("market_cap_valuation_mn", "post_money_valuation_mn",
              "total_funding_mn", "total_funding_raised_mn"):
        v = num(c.get(k))
        if v and v > 0:
            return 3.2 + min(9.0, math.log10(v + 1) * 1.9)
    fte = num(c.get("ftes"))
    if fte and fte > 0:
        return 3.0 + min(7.0, math.log10(fte + 1) * 1.4)
    return 3.4


def pillars(c, w, d):
    return {
        "player": (w[4] or 0) >= 4,
        "product": (d[0] or 0) >= 4 or str(c.get("direct_channel") or "").lower() == "y",
        "wallet": (str(c.get("merchant_of_record") or "").lower() == "y") or (d[3] or 0) >= 4,
    }


comp = []
for c in companies:
    w, d, ai, f = sig(c, "w", 5), sig(c, "d", 6), sig(c, "ai", 7), sig(c, "f", 5)
    links = [u.strip() for u in str(c.get("evidence_links") or "").split(";") if u.strip().startswith("http")]
    comp.append({
        "n": c.get("company"),
        "sec": c.get("source_sector_taxonomy") or "Other",
        "hq": c.get("hq") or "", "founded": c.get("founded"),
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
        "sz": round(star_size(c), 2),
        "sig": {"w": w, "d": d, "ai": ai, "f": f},
        "just": parse_justifications(c),
        "pill": pillars(c, w, d),
        "vc": [1 if str(c.get(f"vc{i+1}_{re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')}") or "").lower() == "y" else 0
               for i, s in enumerate(STAGES)],
        "links": links,
    })
comp.sort(key=lambda x: -(x["epi"] or 0))

# ---------------- relationship graph from the partnership fields -------------
def norm_name(s):
    s = re.sub(r"\([^)]*\)", " ", s.lower())
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    drop = {"plc", "inc", "ab", "publ", "group", "limited", "ltd", "as", "sa",
            "ag", "holdings", "the", "a", "s"}
    return " ".join(t for t in s.split() if t not in drop)


def split_top(s):
    out, buf, depth = [], "", 0
    for ch in s:
        if ch == "(":
            depth += 1
        if ch == ")":
            depth = max(0, depth - 1)
        if ch in ",;" and depth == 0:
            out.append(buf); buf = ""
        else:
            buf += ch
    out.append(buf)
    return [x.strip() for x in out if x.strip()]


JUNK = re.compile(r"\d+\+|customers|various|multiple|et al|others", re.I)
nmap = {norm_name(c["n"]): c["n"] for c in comp}
edges, externals = [], {}
seen_edges = set()
for c in companies:
    src = c["company"]
    for field in ("existing_partnerships", "gen_ai_platform_partnerships"):
        raw = str(c.get(field) or "")
        if not raw or raw.lower() in ("none", "null", "n/a"):
            continue
        for p in split_top(raw):
            note = ""
            m = re.match(r"^(.*?)\s*\((.*)\)\s*$", p)
            if m:
                p, note = m.group(1).strip(), m.group(2)
            p = p.split(" — ")[0].split(" - ")[0].strip()
            if len(p) < 3 or len(p) > 30 or JUNK.search(p):
                continue
            np_ = norm_name(p)
            hit = None
            for k, v in nmap.items():
                if v == src:
                    continue
                if np_ and (np_ == k or (len(np_) >= 5 and (np_ in k or k in np_))):
                    hit = v
                    break
            if hit:
                key = tuple(sorted((src, hit)))
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append({"s": src, "t": hit, "ext": 0, "note": note[:80]})
            else:
                ext = externals.setdefault(p, {"n": p, "deg": 0})
                ext["deg"] += 1
                key = (src, p)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append({"s": src, "t": p, "ext": 1, "note": note[:80]})

ext_nodes = sorted(externals.values(), key=lambda e: -e["deg"])
print(f"graph: {len(comp)} companies, {len(ext_nodes)} externals, {len(edges)} edges "
      f"({sum(1 for e in edges if not e['ext'])} company-to-company)")

payload = {
    "meta": {"count": len(comp), "date": meta.get("extracted_on"), "built": date.today().isoformat()},
    "author": AUTHOR, "linkedin": LINKEDIN_URL, "github": GITHUB_URL,
    "companies": comp, "externals": ext_nodes, "edges": edges,
    "sectors": SECTORS, "seccol": SECCOL, "stages": STAGES,
    "labels": {"w": W_LABELS, "d": D_LABELS, "ai": AI_LABELS},
    "defs": {"w": W_DEFS, "d": D_DEFS, "ai": AI_DEFS},
    "ama": AMA,
    "frame": {"title": IG["title"], "incumbent": IG["incumbent"], "pillars": IG["pillars"]},
}

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>iGaming AI Radar · the landscape from Betsson's bridge</title>
<style>
:root{color-scheme:dark;
 --bg:#070b18;--panel:rgba(9,13,26,.9);--panel2:#141b33;--line:#232c48;
 --tx:#dde3ee;--tx2:#8b94a7;--mut:#5f6a8e;--gold:#f0c84b;--ac:#6ea8fe;
 --hi:#ff5b72;
 --ease:cubic-bezier(.22,.61,.36,1);--t1:.15s;--t2:.28s;--t3:.42s}
@keyframes viewIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
*{box-sizing:border-box;margin:0;padding:0}
html{background:#04060e}
body{background:#04060e;color:var(--tx);font:14px/1.5 "Segoe UI",system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;gap:18px;padding:10px 18px;border-bottom:1px solid var(--line);background:rgba(9,13,26,.95);z-index:20}
header h1{font-size:15.5px;font-weight:600}
header .stamp{color:var(--mut);font-size:11.5px;margin-left:auto}
nav{display:flex;gap:4px}
nav button{background:none;border:1px solid transparent;color:var(--tx2);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px;transition:background var(--t1) var(--ease),color var(--t1) var(--ease),border-color var(--t1) var(--ease)}
nav button:hover{color:var(--tx);background:#141b33}
nav button.on{background:#1a2342;color:#fff;border-color:#33406e}
main{flex:1;overflow:hidden;display:flex}
.view{flex:1;overflow:auto;padding:18px;display:none}
.view.on{display:block;animation:viewIn var(--t2) var(--ease)}
#vSky.on{display:flex;padding:0;animation:none}
/* ================= SKY ================= */
#skywrap{flex:1;position:relative;background:radial-gradient(ellipse at 55% 42%, #0d1430 0%, #070b18 55%, #04060e 100%)}
#cv{position:absolute;inset:0;width:100%;height:100%}
#ctl{position:absolute;top:12px;left:12px;background:var(--panel);backdrop-filter:blur(6px);border:1px solid var(--line);border-radius:12px;padding:12px;z-index:5;width:250px;max-height:calc(100% - 24px);overflow:auto}
#ctl h5{font-size:10px;letter-spacing:1.4px;color:#6f7ba0;margin:11px 0 5px;text-transform:uppercase}
#ctl h5:first-child{margin-top:0}
#nq{width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--tx);padding:6px 10px;border-radius:8px;font-size:13px;outline:none}
#nq:focus{border-color:var(--ac)}
.lgrow{display:flex;align-items:center;gap:8px;font-size:11.5px;color:#9aa4c4;padding:3.5px 5px;border-radius:6px;cursor:pointer;transition:background var(--t1) var(--ease)}
.lgrow:hover{background:#141b33}
.lgrow.off{opacity:.35}
.lgrow .st{width:11px;height:11px;border-radius:50%;flex:none;box-shadow:0 0 7px currentColor}
.lgrow .cnt{margin-left:auto;color:var(--mut);font-size:11px}
.fbtn{display:flex;align-items:center;gap:8px;width:100%;text-align:left;background:none;border:1px solid transparent;border-radius:8px;color:#aab4d4;padding:5px 8px;cursor:pointer;font-size:12.5px;transition:background var(--t1) var(--ease)}
.fbtn:hover{background:#141b33}
.hint{font-size:11px;color:var(--mut);line-height:1.6;padding:2px 5px}
#tip{position:absolute;pointer-events:none;background:rgba(5,8,18,.94);border:1px solid #2b3454;padding:6px 10px;border-radius:8px;font-size:12px;display:none;z-index:6;max-width:270px}
#tip b{color:#fff}#tip .m{color:var(--tx2);font-size:11px}
#foot{position:absolute;bottom:10px;left:14px;color:var(--mut);font-size:11px;z-index:5}
#focusbar{position:absolute;top:12px;left:50%;transform:translateX(-50%);background:var(--panel);border:1px solid #33406e;border-radius:20px;padding:5px 14px;z-index:6;font-size:12.5px;display:none;align-items:center;gap:10px}
#focusbar b{color:var(--gold)}
#focusbar button{background:none;border:none;color:var(--tx2);cursor:pointer;font-size:14px}
#zoomctl{position:absolute;right:14px;bottom:12px;z-index:6;display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
#zoomctl button{background:none;border:none;color:#c3cce0;width:30px;height:28px;cursor:pointer;font-size:16px}
#zoomctl button+button{border-top:1px solid var(--line)}
#zoomctl button:hover{background:#1a2342;color:#fff}
/* lenses */
.lensbtn{display:block;width:100%;text-align:left;background:none;border:1px solid transparent;border-radius:8px;color:#aab4d4;padding:5px 8px;cursor:pointer;font-size:12.5px;transition:background var(--t1) var(--ease),border-color var(--t1) var(--ease)}
.lensbtn:hover{background:#141b33}
.lensbtn.on{background:#1a2342;border-color:#33406e;color:#fff}
.lensbtn .lc{margin-left:6px;color:var(--mut);font-size:11px}
.lenscap{font-size:11.5px;color:#aab4d4;line-height:1.55;background:#101728;border-left:2px solid var(--gold);border-radius:0 8px 8px 0;padding:8px 10px;margin-top:6px}
/* ask bar */
#askbar{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:7;width:min(620px,72%)}
.abRow{display:flex;gap:7px;background:var(--panel);backdrop-filter:blur(7px);border:1px solid #2f3c63;border-radius:13px;padding:7px 8px;box-shadow:0 10px 34px #0009}
#askInput{flex:1;background:#0e1626;border:1px solid #2a3550;color:var(--tx);border-radius:9px;padding:9px 12px;font-size:13.5px;outline:none}
#askInput:focus{border-color:var(--ac)}
#askGo{background:linear-gradient(180deg,#f6d56a,#d9ab2e);border:none;color:#241d05;font-weight:600;border-radius:9px;padding:9px 15px;cursor:pointer;font-size:13px;white-space:nowrap}
#askGo:hover{filter:brightness(1.06)}
#askClear{background:#1a2342;border:1px solid #33406e;color:#cdd6ea;border-radius:9px;padding:9px 11px;cursor:pointer}
.askfb{min-height:15px;font-size:11.5px;margin-top:5px;color:var(--tx2);text-align:center;transition:opacity .18s var(--ease)}
.askfb.err{color:#ff9aa6}.askfb.think{color:#9fb4ff}
#askProg{display:none;margin-top:6px;height:4px;background:#161f33;border-radius:3px;overflow:hidden;opacity:1;transition:opacity var(--t2) var(--ease)}
#askProg.on{display:block}
#askProg i{display:block;height:100%;width:0;border-radius:3px;background:linear-gradient(90deg,#f6d56a,#6ea8fe,#f6d56a);background-size:200% 100%;animation:shimmer 1.3s linear infinite}
@keyframes shimmer{from{background-position:0% 0}to{background-position:-200% 0}}
/* briefing card */
#briefing{position:fixed;inset:0;background:rgba(4,7,15,.72);backdrop-filter:blur(4px);z-index:40;display:flex;align-items:center;justify-content:center;padding:24px;opacity:0;visibility:hidden;pointer-events:none;transition:opacity var(--t2) var(--ease),visibility 0s linear var(--t2)}
#briefing.on{opacity:1;visibility:visible;pointer-events:auto;transition:opacity var(--t2) var(--ease)}
.bCard{width:min(680px,94vw);max-height:88vh;display:flex;flex-direction:column;background:linear-gradient(180deg,#121a2e,#0c1220);border:1px solid #2a3550;border-radius:15px;box-shadow:0 30px 90px #000b;overflow:hidden;transform:translateY(14px) scale(.985);transition:transform var(--t3) var(--ease)}
#briefing.on .bCard{transform:none}
.bHead{padding:15px 20px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:flex-start}
.bHead h3{font-size:16.5px}
.bMeta{font-size:11.5px;color:var(--mut);margin-top:3px}
.bBody{overflow:auto;padding:16px 20px}
#bText{font-size:13.5px;line-height:1.65;color:#c3cce0;white-space:pre-wrap}
.bFor{margin:13px 0;padding:10px 13px;background:#241d05;border-left:3px solid var(--gold);border-radius:0 9px 9px 0;color:#ffe9a8;font-size:13px}
.bFor b{color:var(--gold)}
.affrow{display:flex;align-items:center;gap:10px;padding:6px 2px;border-bottom:1px solid #131a2c;font-size:12.5px;cursor:pointer}
.affrow:hover{background:#131a2e}
.affrow .nm{font-weight:600;min-width:0}
.affrow .fx{font-size:10.5px;font-weight:700;padding:1px 8px;border-radius:10px;white-space:nowrap}
.affrow .rs{flex:1;color:var(--tx2);font-size:11.5px;text-align:right}
.bCav{margin-top:11px;font-size:11px;color:var(--mut);font-style:italic}
/* ================= BOARD ================= */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:16px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px}
.tile .v{font-size:25px;font-weight:600}
.tile .k{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.6px;margin-top:3px}
.tile .sub{font-size:11.5px;color:var(--tx2);margin-top:4px}
table.dt{width:100%;border-collapse:collapse;font-size:13px}
table.dt th{position:sticky;top:0;text-align:left;background:#0b101f;color:var(--tx2);font-weight:500;padding:8px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px}
table.dt td{padding:8px;border-bottom:1px solid #131a2c;white-space:nowrap;font-variant-numeric:tabular-nums}
table.dt tbody tr{cursor:pointer}
table.dt tbody tr:hover{background:#131a2e}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;vertical-align:0}
.pill{display:inline-block;padding:1px 9px;border-radius:12px;font-size:11px;font-weight:600}
.pHigh{background:#3a1820;color:#ff8e9d}.pMedium{background:#39301a;color:#ffd479}.pLow{background:#16263c;color:#7fb4f5}
.confbadge{display:inline-block;padding:1px 8px;border-radius:11px;font-size:10.5px;font-weight:600}
.chigh{background:#15301f;color:#5fd99a}.cmedium{background:#39301a;color:#ffd479}.clow{background:#3a1820;color:#ff8e9d}
/* ================= FINDINGS ================= */
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px}
.fcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 17px}
.fcard h3{font-size:14px;margin-bottom:6px}
.fcard p{color:var(--tx2);font-size:12.5px}
.fcard .ev{margin-top:8px;font-size:11px;color:var(--mut);border-top:1px solid #1a2235;padding-top:7px}
.prose{max-width:78ch;color:var(--tx2);font-size:13px}
.prose h3{color:var(--tx);font-size:14.5px;margin:18px 0 6px}
.prose p{margin-bottom:9px}
.prose ul{margin:0 0 9px 20px}
.prose code{background:var(--panel2);padding:1px 6px;border-radius:5px;font-size:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-top:12px}
footer{margin-top:22px;padding-top:14px;border-top:1px solid var(--line);color:var(--mut);font-size:12px;display:flex;gap:16px;flex-wrap:wrap}
footer a{color:var(--ac)}
h2.vt{font-size:18px;margin-bottom:4px}
p.vs{color:var(--tx2);font-size:13px;margin-bottom:14px;max-width:80ch}
/* ================= DRAWER ================= */
#scrim{position:fixed;inset:0;background:#0009;opacity:0;visibility:hidden;transition:opacity var(--t2) var(--ease),visibility 0s linear var(--t2);z-index:30}
#scrim.on{opacity:1;visibility:visible;transition:opacity var(--t2) var(--ease)}
#drawer{position:fixed;top:0;right:0;width:min(620px,100%);height:100vh;background:#0b101f;border-left:1px solid var(--line);z-index:31;display:flex;flex-direction:column;transform:translateX(103%);transition:transform var(--t3) var(--ease);box-shadow:-14px 0 44px #000b}
#drawer.on{transform:none}
.dh{padding:15px 20px;border-bottom:1px solid var(--line);display:flex;align-items:flex-start;gap:12px}
.dh h2{font-size:17px}.dh .sub{color:var(--mut);font-size:12px;margin-top:3px}
.x{margin-left:auto;background:none;border:none;color:var(--mut);font-size:22px;cursor:pointer;line-height:1}
.x:hover{color:var(--tx)}
.db{padding:15px 20px;overflow:auto}
.db h4{font-size:10.5px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut);margin:16px 0 6px}
.kv{display:flex;flex-wrap:wrap;gap:6px}
.kv span{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:3px 9px;font-size:12px;color:var(--tx2)}
.kv b{color:var(--tx)}
.gauges{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:8px 0 2px}
.g{text-align:center}
.g .ring{width:64px;height:64px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center}
.g .ring i{width:50px;height:50px;border-radius:50%;background:#0b101f;display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:600;font-size:15px}
.g .gl{font-size:10px;color:var(--mut);margin-top:4px;text-transform:uppercase;letter-spacing:.5px}
.sgrp{font-size:10px;letter-spacing:1px;color:#6f7ba0;text-transform:uppercase;margin:13px 0 4px}
.sr{margin:2.5px 0}
.sr .top{display:flex;align-items:center;gap:9px;padding:4px 6px;cursor:pointer;border-radius:7px;transition:background var(--t1) var(--ease)}
.sr .top:hover{background:#141b33}
.sr .lb{flex:1;font-size:12px;color:var(--tx2)}
.sr .bar{width:92px;height:6px;background:#1a2235;border-radius:3px;overflow:hidden;flex:none}
.sr .bar i{display:block;height:100%;border-radius:3px}
.sr .vl{width:14px;text-align:right;font-size:11px;color:var(--mut);font-variant-numeric:tabular-nums}
.sr .why{display:none;padding:7px 10px;font-size:12px;color:#b9c2d8;border-left:2px solid var(--ac);margin:2px 0 6px 6px;background:#101728;border-radius:0 7px 7px 0}
.sr.open .why{display:block}
.sr .why .def{color:var(--mut);font-size:11px;margin-top:5px}
.jstrip{display:flex;gap:3px;margin:6px 0}
.jseg{flex:1;text-align:center;font-size:9.5px;padding:5px 2px;border-radius:6px;background:#141b33;color:#4a5470;border:1px solid #1d2742}
.jseg.on{background:#152a3d;color:#7fb4f5;border-color:#27496b}
.callout{border-left:3px solid var(--ac);background:#111a2e;border-radius:0 8px 8px 0;padding:9px 12px;margin:7px 0;font-size:12.5px;color:#b9c2d8;white-space:pre-wrap}
.callout.imp{border-color:var(--hi)}.callout.gap{border-color:#e7a93c}
.srcs{list-style:none}
.srcs li{margin:4px 0;font-size:11.5px;word-break:break-all}
.srcs a{color:var(--ac)}
.connrow{display:flex;align-items:center;gap:7px;padding:4px 6px;border-radius:7px;cursor:pointer;font-size:12px;transition:background var(--t1) var(--ease)}
.connrow:hover{background:#141b33}
.connrow .cdot{width:8px;height:8px;border-radius:50%;flex:none}
.connrow .cty{margin-left:auto;font-size:10px;color:var(--mut);max-width:45%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style></head><body>

<header><h1>iGaming · AI Radar <span style="color:var(--mut);font-weight:400;font-size:12.5px">— the disruption landscape, seen from Betsson's bridge</span></h1>
<nav><button data-v="vSky" class="on">Constellation</button><button data-v="vBoard">Threat Board</button><button data-v="vFind">Findings &amp; Method</button></nav>
<span class="stamp" id="stamp"></span></header>

<main>
<div id="vSky" class="view on"><div id="skywrap">
  <canvas id="cv"></canvas><div id="tip"></div>
  <div id="focusbar"><span>Focused on <b id="focusname"></b></span><button onclick="clearFocus()">✕</button></div>
  <div id="ctl">
    <h5>Find</h5><input id="nq" placeholder="Type a company…" autocomplete="off">
    <h5>Radar lenses</h5><div id="lenses"></div><div id="lensCap" class="lenscap" style="display:none"></div>
    <h5>Constellations — click to spotlight</h5><div id="leg"></div>
    <h5>View</h5>
    <button class="fbtn" id="extBtn"><span class="st" style="width:10px;height:10px;border-radius:50%;background:#7d88aa"></span>Partner entities: shown</button>
    <button class="fbtn" id="linesBtn"><span style="width:14px;height:2px;background:#3d4a73;border-radius:2px"></span>Constellation lines: on</button>
    <h5>Reading the sky</h5>
    <div class="hint">gold star = Betsson, the vantage point<br>★ size = company scale (market cap / valuation / funding)<br>
    red ring = High threat tier<br>
    small grey stars = named partners from the research<br>
    click a star → its dossier · drag to pan · wheel to zoom</div>
  </div>
  <div id="zoomctl"><button id="zIn">+</button><button id="zFit">⤢</button><button id="zOut">−</button></div>
  <div id="askbar">
    <div class="abRow">
      <input id="askInput" type="text" autocomplete="off" placeholder="Ask the radar — e.g. what happens to Betsson if Kalshi gets EU licences?">
      <button id="askGo">◈ Ask</button>
      <button id="askClear" style="display:none" title="Clear">✕</button>
    </div>
    <div id="askFb" class="askfb"></div>
    <div id="askProg"><i></i></div>
  </div>
  <div id="briefing"><div class="bCard">
    <div class="bHead"><div style="flex:1"><h3 id="bTitle"></h3><div class="bMeta" id="bMeta"></div></div><button class="x" onclick="closeBriefing()">×</button></div>
    <div class="bBody"><div id="bText"></div><div id="bFor" class="bFor"></div><div id="bAff"></div><div id="bCav" class="bCav"></div></div>
  </div></div>
  <div id="foot"></div>
</div></div>

<div id="vBoard" class="view">
  <h2 class="vt">Threat board</h2>
  <p class="vs">Every company ranked by disruption score — 0.4 × willingness to attack the incumbent model + 0.6 × readiness to execute. Click a row for the full dossier.</p>
  <div class="tiles" id="tiles"></div>
  <table class="dt" id="dt"></table>
</div>

<div id="vFind" class="view">
  <h2 class="vt">What the sky is telling us</h2>
  <p class="vs">Findings computed from the scored dataset — each traceable to the companies that produce it.</p>
  <div class="fgrid" id="findings"></div>
  <div class="card"><div class="prose" id="method"></div><footer id="foot2"></footer></div>
</div>
</main>

<div id="scrim" onclick="closeDrawer()"></div>
<aside id="drawer"><div class="dh"><div style="flex:1"><h2 id="dt_"></h2><div class="sub" id="ds_"></div></div><button class="x" onclick="closeDrawer()">×</button></div><div class="db" id="db_"></div></aside>

<script>
const D=__DATA__;
const C=D.companies, byName={}; C.forEach(c=>byName[c.n]=c);
const SECCOL=D.seccol, EXTCOL="#7d88aa";
const RAMP=['#26436e','#2d5a99','#3987e5','#6da7ec','#9ec5f4','#cde2fb'];
const esc=s=>String(s??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const nn=v=>v==null?'–':v;
document.getElementById('stamp').textContent=D.meta.count+' companies · '+D.externals.length+' partner entities · every number sourced';

document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
 document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');document.getElementById(b.dataset.v).classList.add('on');
});

/* ================= CONSTELLATION ================= */
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const REDUCE=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
let nodes=[],links=[],byId={},secAnchor={},focusId=null,hoverN=null,secSpot=null;
let zoom=1,cx=0,cy=0,alpha=1,dragN=null,panning=false,px=0,py=0,downX=0,downY=0;
let showExt=true,showLines=true,T=0;
const bgStars=[];for(let i=0;i<240;i++)bgStars.push([Math.random(),Math.random(),Math.random()*1.1+0.2,Math.random()*6.28]);

function initSky(){
 // sector anchors on a ring — each constellation gets its own region of sky
 const secs=D.sectors.filter(s=>C.some(c=>c.sec===s));
 secs.forEach((s,i)=>{const a=(i/secs.length)*6.283-1.2;
  secAnchor[s]={x:Math.cos(a)*330,y:Math.sin(a)*250};});
 nodes=C.map(c=>{const an=secAnchor[c.sec]||{x:0,y:0};
  return {id:c.n,ds:1,sec:c.sec,tier:c.tier,sz:c.sz,
   gold:c.n.toLowerCase().startsWith('betsson'),   // the vantage star
   x:an.x+(Math.random()-.5)*220,y:an.y+(Math.random()-.5)*180,
   vx:0,vy:0,ph:Math.random()*6.28,deg:0};});
 D.externals.forEach(e=>{nodes.push({id:e.n,ds:0,sz:1.6+Math.sqrt(e.deg)*0.9,
  x:(Math.random()-.5)*900,y:(Math.random()-.5)*640,vx:0,vy:0,ph:Math.random()*6.28,deg:0});});
 nodes.forEach(n=>byId[n.id]=n);
 links=D.edges.filter(e=>byId[e.s]&&byId[e.t]).map(e=>({a:byId[e.s],b:byId[e.t],ext:e.ext,note:e.note||''}));
 links.forEach(l=>{l.a.deg++;l.b.deg++;});
 // externals start near their partner
 links.forEach(l=>{if(l.ext&&l.b.ds===0){l.b.x=l.a.x+(Math.random()-.5)*120;l.b.y=l.a.y+(Math.random()-.5)*120;}});
 // legend
 const cnt={};C.forEach(c=>cnt[c.sec]=(cnt[c.sec]||0)+1);
 document.getElementById('leg').innerHTML=secs.map(s=>
  '<div class="lgrow" data-s="'+esc(s)+'"><span class="st" style="background:'+SECCOL[s]+';color:'+SECCOL[s]+'"></span>'+esc(s)+'<span class="cnt">'+cnt[s]+'</span></div>').join('');
 document.querySelectorAll('#leg .lgrow').forEach(r=>r.onclick=()=>{
  secSpot=(secSpot===r.dataset.s)?null:r.dataset.s;
  document.querySelectorAll('#leg .lgrow').forEach(x=>x.classList.toggle('off',secSpot&&x.dataset.s!==secSpot));
  alpha=Math.max(alpha,.3);});
 document.getElementById('foot').textContent=C.length+' companies · '+D.externals.length+' partner entities · '+links.length+' links';
 sizeCv();loop();
 addEventListener('resize',sizeCv);
}
function sizeCv(){const r=cv.parentElement.getBoundingClientRect();
 if(r.width<2)return; // layout not ready yet — the loop guard will retry
 cv.width=r.width*devicePixelRatio;cv.height=r.height*devicePixelRatio;}
function neighbors(id){const s=new Set([id]);links.forEach(l=>{if(l.a.id===id)s.add(l.b.id);if(l.b.id===id)s.add(l.a.id);});return s;}
let focusSet=null;
function setFocus(id){focusId=id;focusSet=neighbors(id);
 document.getElementById('focusname').textContent=id;
 document.getElementById('focusbar').style.display='flex';
 alpha=Math.max(alpha,.25);
 if(byName[id])openCompany(id);else openExternal(id);}
function clearFocus(){focusId=null;focusSet=null;document.getElementById('focusbar').style.display='none';}

function step(){
 // pairwise repulsion (n≈100 → fine)
 for(let i=0;i<nodes.length;i++){const a=nodes[i];
  for(let j=i+1;j<nodes.length;j++){const b=nodes[j];
   let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+40;
   if(d2>90000)continue;
   const f=(a.ds&&b.ds?820:300)/d2,d=Math.sqrt(d2);dx/=d;dy/=d;
   a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f;}}
 // springs on edges
 links.forEach(l=>{
  const rest=l.ext?70:150,k=l.ext?0.012:0.008;
  let dx=l.b.x-l.a.x,dy=l.b.y-l.a.y;const d=Math.sqrt(dx*dx+dy*dy)+.01,f=(d-rest)*k;
  dx/=d;dy/=d;l.a.vx+=dx*f;l.a.vy+=dy*f;l.b.vx-=dx*f;l.b.vy-=dy*f;});
 nodes.forEach(n=>{
  if(n.ds){const an=secAnchor[n.sec];if(an){n.vx+=(an.x-n.x)*0.0016;n.vy+=(an.y-n.y)*0.0016;}}
  n.vx-=n.x*0.0004;n.vy-=n.y*0.0004;
  if(!REDUCE){n.vx+=Math.sin(T*0.22+n.ph)*0.2;n.vy+=Math.cos(T*0.18+n.ph*1.3)*0.2;}
  n.vx=Math.max(-22,Math.min(22,n.vx))*alpha;n.vy=Math.max(-22,Math.min(22,n.vy))*alpha;
  if(n!==dragN){n.x+=n.vx;n.y+=n.vy;n.vx*=0.85;n.vy*=0.85;}});
 alpha=Math.max(REDUCE?0:0.05,alpha*0.992);
}
function mstSector(sec){
 const pts=nodes.filter(n=>n.ds&&n.sec===sec);
 if(pts.length<2)return[];
 const inTree=[pts[0]],rest=pts.slice(1),segs=[];
 while(rest.length){let bi=0,bj=0,bd=1e18;
  for(let i=0;i<inTree.length;i++)for(let j=0;j<rest.length;j++){
   const dx=inTree[i].x-rest[j].x,dy=inTree[i].y-rest[j].y,d=dx*dx+dy*dy;
   if(d<bd){bd=d;bi=i;bj=j;}}
  segs.push([inTree[bi],rest[bj]]);inTree.push(rest[bj]);rest.splice(bj,1);}
 return segs;
}
/* lenses (D17 reframe): predicate-based spotlights over the same sky */
let lens=null, radarSet=null, radarFx={};
const LENSES={
 acq:{name:'Acquisition risk',
  test:c=>c.sec==='Affiliate & media'||(c.sig.w[4]||0)>=4,
  cap:'Betsson spends ~21% of B2C revenue on marketing + affiliates while AI search breaks the rail: organic clicks fall 61% under AI Overviews and 71% of affiliate sites were hit by the March 2026 core update. Lit stars either carry that affiliate risk or already own the player intent Betsson is paying to rent.'},
 ma:{name:'M&A radar',
  test:c=>Object.values(c.pill).filter(Boolean).length===2||['At-risk','Distressed'].includes(c.sv),
  cap:'Betsson holds a €75m facility earmarked for "entering new markets or acquiring valuable technologies." Lit stars are one pillar away from a full stack, or strategically valuable but financially at risk — the two classic acquisition profiles.'},
 watch:{name:'Watchtower',
  test:c=>c.sec==='AI-native & prediction markets'||c.hz==='0-12m',
  cap:'"A very interesting market segment… no plans to enter as of now" — CEO Pontus Lindwall on prediction markets, Feb 2026. Watching without entering needs a watchtower: these are the stars moving inside 12 months, led by the prediction-market flank.'}};
function dimOf(n){
 if(radarSet)return radarSet.has(n.id)?1:0.12;
 if(focusSet)return focusSet.has(n.id)?1:0.13;
 if(lens){const c=byName[n.id];
  if(n.gold)return 1;                       // the vantage star never dims
  return (c&&LENSES[lens].test(c))?1:(n.ds?0.14:0.08);}
 if(secSpot)return (n.ds&&n.sec===secSpot)?1:(n.ds?0.15:0.1);
 return 1;
}
function starR(n){return n.gold?(2.2+n.sz*0.95):n.ds?(1.2+n.sz*0.9):(0.8+n.sz*0.8);}
function draw(){
 T+=0.016;
 const W=cv.width,H=cv.height;ctx.clearRect(0,0,W,H);
 ctx.save();
 bgStars.forEach(s=>{ctx.globalAlpha=0.10+0.10*Math.sin(T*0.7+s[3]);ctx.fillStyle='#9fb4ff';ctx.fillRect(s[0]*W,s[1]*H,s[2],s[2]);});
 ctx.restore();
 ctx.save();ctx.translate(W/2,H/2);ctx.scale(zoom*devicePixelRatio,zoom*devicePixelRatio);ctx.translate(-cx,-cy);
 // asterisms — the constellation lines
 if(showLines){ctx.lineWidth=0.8;
  Object.keys(secAnchor).forEach(sec=>{
   const col=SECCOL[sec]||'#666';
   const spot=secSpot===sec;
   ctx.strokeStyle=col;
   mstSector(sec).forEach(([a,b])=>{
    const dm=Math.min(dimOf(a),dimOf(b));
    ctx.globalAlpha=(spot?0.5:0.22)*dm;
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();});});}
 // partnership edges
 ctx.globalCompositeOperation='lighter';
 links.forEach(l=>{
  if(!showExt&&(l.a.ds===0||l.b.ds===0))return;
  const dm=Math.min(dimOf(l.a),dimOf(l.b));
  if(dm<0.2&&!focusSet)return;
  ctx.strokeStyle=l.ext?'#4b5a86':'#7e9cff';
  ctx.globalAlpha=(l.ext?0.30:0.55)*dm;
  ctx.lineWidth=l.ext?0.7:1.3;
  ctx.beginPath();ctx.moveTo(l.a.x,l.a.y);ctx.lineTo(l.b.x,l.b.y);ctx.stroke();
  if(!l.ext){ctx.globalAlpha=0.14*dm;ctx.lineWidth=4;ctx.stroke();}});
 ctx.globalCompositeOperation='source-over';
 // stars
 nodes.forEach(n=>{
  if(!showExt&&!n.ds)return;
  const dm=dimOf(n);if(dm<0.05)return;
  const r=starR(n),col=n.gold?'#ffd54f':n.ds?(SECCOL[n.sec]||'#9fb0cc'):EXTCOL;
  const tw=(n.sz<4?(0.82+0.18*Math.sin(T*1.4+n.ph)):1)*dm;
  ctx.globalAlpha=(n.gold?0.22:0.16)*tw;ctx.fillStyle=col;
  ctx.beginPath();ctx.arc(n.x,n.y,r*(n.gold?3.1:2.6),0,7);ctx.fill();
  ctx.globalAlpha=tw;ctx.beginPath();ctx.arc(n.x,n.y,r,0,7);ctx.fill();
  if(r>6||n.gold){ctx.globalAlpha=0.5*tw;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(n.x,n.y,r*0.38,0,7);ctx.fill();}
  if(n.gold){ctx.globalAlpha=0.7*dm;ctx.strokeStyle='#ffd54f';ctx.lineWidth=1.2;
   ctx.beginPath();ctx.arc(n.x,n.y,r+4+1.2*Math.sin(T*1.2),0,7);ctx.stroke();}
  if(n.ds&&n.tier==='High'){ctx.globalAlpha=0.85*dm;ctx.strokeStyle='#ff5b72';ctx.lineWidth=1.1;
   ctx.beginPath();ctx.arc(n.x,n.y,r+2.4,0,7);ctx.stroke();}
  const fx=radarFx[n.id];
  if(fx){const fc={rises:'#ff8e9d',falls:'#7fb4f5',exposed:'#ffb74d',watch:'#e879f9',opportunity:'#5fd99a'}[fx]||'#fff';
   ctx.globalAlpha=0.6+0.35*Math.sin(T*2.4+n.ph);ctx.strokeStyle=fc;ctx.lineWidth=1.6;
   ctx.setLineDash(fx==='watch'?[3,3]:[]);
   ctx.beginPath();ctx.arc(n.x,n.y,r+5,0,7);ctx.stroke();ctx.setLineDash([]);}
  if(n===hoverN||n.id===focusId){ctx.globalAlpha=1;ctx.strokeStyle='#fff';ctx.lineWidth=1.4;
   ctx.beginPath();ctx.arc(n.x,n.y,r+3.6,0,7);ctx.stroke();}
  // labels: EVERY company star is named — the luxury of n=25
  const showLbl=n.ds||n===hoverN||n.id===focusId||(focusSet&&focusSet.has(n.id))||zoom>1.8;
  if(showLbl){ctx.fillStyle=n.gold?'#ffd54f':n.ds?'#c9d2ea':'#8a93ad';
   ctx.font=(n.ds?'600 ':'')+(n.gold?'11.5px ':n.ds?'10.5px ':'9px ')+'"Segoe UI"';
   ctx.globalAlpha=(n.ds?0.92:0.75)*dm;
   ctx.fillText(n.id.length>26?n.id.slice(0,25)+'…':n.id,n.x+r+4,n.y+3.5);}
  ctx.globalAlpha=1;});
 ctx.restore();
}
function loop(){
 // self-heal if layout wasn't ready at init (canvas 0x0) or the pane resized
 const r=cv.parentElement.getBoundingClientRect();
 if(Math.abs(cv.width-r.width*devicePixelRatio)>2)sizeCv();
 step();draw();requestAnimationFrame(loop);}
function pick(mx,my){const r=cv.getBoundingClientRect();
 const x=(mx-r.left-r.width/2)/zoom+cx,y=(my-r.top-r.height/2)/zoom+cy;
 let best=null,bd=1e9;
 nodes.forEach(n=>{if(!showExt&&!n.ds)return;
  const dx=n.x-x,dy=n.y-y,d2=dx*dx+dy*dy,rr=Math.pow(starR(n)+5,2);
  if(d2<rr&&d2<bd){bd=d2;best=n;}});
 return best;}
cv.onmousedown=e=>{const n=pick(e.clientX,e.clientY);
 if(n)dragN=n;else panning=true;
 px=downX=e.clientX;py=downY=e.clientY;};
addEventListener('mousemove',e=>{
 if(dragN){dragN.x+=(e.clientX-px)/zoom;dragN.y+=(e.clientY-py)/zoom;px=e.clientX;py=e.clientY;alpha=Math.max(alpha,.18);}
 else if(panning){cx-=(e.clientX-px)/zoom;cy-=(e.clientY-py)/zoom;px=e.clientX;py=e.clientY;}
 else{const n=pick(e.clientX,e.clientY);hoverN=n;
  const tip=document.getElementById('tip');
  if(n){const wr=cv.parentElement.getBoundingClientRect();
   tip.style.display='block';
   tip.style.left=Math.min(wr.width-280,e.clientX-wr.left+14)+'px';
   tip.style.top=(e.clientY-wr.top+10)+'px';
   const c=byName[n.id];
   tip.innerHTML='<b>'+esc(n.id)+'</b><div class="m">'+(c?esc(c.sec)+' · score '+nn(c.epi)+' · '+esc(c.quad):'partner entity · '+n.deg+' link'+(n.deg>1?'s':''))+'</div>';
   cv.style.cursor='pointer';}
  else{tip.style.display='none';cv.style.cursor='default';}}});
addEventListener('mouseup',e=>{
 const moved=Math.abs(e.clientX-downX)>4||Math.abs(e.clientY-downY)>4;
 if(dragN&&!moved)setFocus(dragN.id);
 else if(panning&&!moved&&e.target===cv){clearFocus();closeDrawer();}
 dragN=null;panning=false;});
cv.onwheel=e=>{e.preventDefault();zoom*=e.deltaY<0?1.12:0.89;zoom=Math.max(0.3,Math.min(5,zoom));};
document.getElementById('zIn').onclick=()=>{zoom=Math.min(5,zoom*1.25);};
document.getElementById('zOut').onclick=()=>{zoom=Math.max(0.3,zoom*0.8);};
document.getElementById('zFit').onclick=()=>{zoom=1;cx=0;cy=0;};
document.getElementById('extBtn').onclick=e=>{showExt=!showExt;
 e.currentTarget.innerHTML='<span class="st" style="width:10px;height:10px;border-radius:50%;background:#7d88aa"></span>Partner entities: '+(showExt?'shown':'hidden');};
document.getElementById('linesBtn').onclick=e=>{showLines=!showLines;
 e.currentTarget.innerHTML='<span style="width:14px;height:2px;background:#3d4a73;border-radius:2px"></span>Constellation lines: '+(showLines?'on':'off');};
document.getElementById('nq').onkeydown=e=>{
 if(e.key!=='Enter')return;
 const q=e.target.value.toLowerCase().trim();if(!q)return;
 const n=nodes.find(n=>n.id.toLowerCase().includes(q));
 if(n){cx=n.x;cy=n.y;zoom=Math.max(zoom,1.6);setFocus(n.id);}};
/* ================= LENSES ================= */
(function(){
 const box=document.getElementById('lenses');
 box.innerHTML=Object.keys(LENSES).map(k=>{
  const n=C.filter(c=>LENSES[k].test(c)).length;
  return '<button class="lensbtn" data-l="'+k+'">'+LENSES[k].name+'<span class="lc">'+n+' stars</span></button>';}).join('');
 box.querySelectorAll('.lensbtn').forEach(b=>b.onclick=()=>{
  lens=(lens===b.dataset.l)?null:b.dataset.l;
  secSpot=null;document.querySelectorAll('#leg .lgrow').forEach(x=>x.classList.remove('off'));
  box.querySelectorAll('.lensbtn').forEach(x=>x.classList.toggle('on',x.dataset.l===lens));
  const cap=document.getElementById('lensCap');
  if(lens){cap.style.display='block';cap.textContent=LENSES[lens].cap;}
  else cap.style.display='none';
  alpha=Math.max(alpha,.3);});
})();

/* ================= ASK THE RADAR ================= */
let askBusy=false,progMsgT=null;
const ASK_MSGS=['Sweeping the sky…','Reading the dossiers…','Writing the briefing…'];
function askProg(on){
 const p=document.getElementById('askProg'),f=p.querySelector('i'),fb=document.getElementById('askFb');
 if(on){p.classList.add('on');f.style.transition='none';f.style.width='0%';void f.offsetWidth;
  f.style.transition='width 16s cubic-bezier(.05,.7,.1,1)';f.style.width='92%';
  let i=0;fb.textContent=ASK_MSGS[0];fb.className='askfb think';
  progMsgT=setInterval(()=>{i=(i+1)%ASK_MSGS.length;fb.textContent=ASK_MSGS[i];},2600);}
 else{if(progMsgT){clearInterval(progMsgT);progMsgT=null;}
  f.style.transition='width .3s';f.style.width='100%';
  setTimeout(()=>{p.classList.remove('on');f.style.transition='none';f.style.width='0%';},320);}
}
function getPass(){let p=sessionStorage.getItem('radarPass');if(p)return p;
 p=prompt('Enter the radar passcode:');if(p===null)return null;
 p=p.trim();if(p)sessionStorage.setItem('radarPass',p);return p;}
function clearRadar(){radarSet=null;radarFx={};
 document.getElementById('askClear').style.display='none';
 document.getElementById('askInput').value='';
 document.getElementById('askFb').textContent='';}
function closeBriefing(){document.getElementById('briefing').classList.remove('on');}
function renderBriefing(q,out){
 document.getElementById('bTitle').textContent=out.title||'Radar briefing';
 document.getElementById('bMeta').textContent='“'+q+'” · '+(out.confidence||'')+' confidence · grounded in the scored dataset + researched Betsson facts';
 document.getElementById('bText').textContent=out.briefing||'';
 document.getElementById('bFor').innerHTML='<b>For Betsson:</b> '+esc(out.forBetsson||'');
 const FXC={rises:['#ff8e9d','#2a151b'],falls:['#7fb4f5','#152233'],exposed:['#ffb74d','#2a2213'],watch:['#e879f9','#26132a'],opportunity:['#5fd99a','#13251b']};
 const aff=(out.affected||[]).filter(a=>byName[a.name]);
 document.getElementById('bAff').innerHTML=aff.length?('<h4 style="font-size:10.5px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut);margin:14px 0 6px">On the sky</h4>'+
  aff.map(a=>{const fc=FXC[a.effect]||['#9fb0cc','#1a2030'];
   return '<div class="affrow" onclick="closeBriefing();jumpTo(\''+a.name.replace(/'/g,"\\'")+'\')">'+
    '<span class="nm">'+esc(a.name)+'</span><span class="fx" style="color:'+fc[0]+';background:'+fc[1]+'">'+esc(a.effect)+'</span>'+
    '<span class="rs">'+esc(a.reason||'')+'</span></div>';}).join('')):'';
 document.getElementById('bCav').textContent=out.caveats||'';
 document.getElementById('briefing').classList.add('on');
 radarFx={};aff.forEach(a=>{radarFx[a.name]=a.effect;});
 radarSet=new Set(aff.map(a=>a.name));
 nodes.forEach(n=>{if(n.gold)radarSet.add(n.id);});
 document.getElementById('askClear').style.display='inline-block';
 alpha=Math.max(alpha,.3);
}
async function askRadar(){
 if(askBusy)return;
 const inp=document.getElementById('askInput'),fb=document.getElementById('askFb'),go=document.getElementById('askGo');
 const q=inp.value.trim();
 if(!q){fb.textContent='Type a question — e.g. “which of these could Betsson buy with €75m?”';fb.className='askfb err';return;}
 const pass=getPass();if(pass===null)return;
 askBusy=true;go.disabled=true;inp.disabled=true;askProg(true);
 try{
  const res=await fetch('/api/radar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,passcode:pass})});
  if(res.status===401){sessionStorage.removeItem('radarPass');askProg(false);fb.textContent='Wrong passcode — ask again to retry.';fb.className='askfb err';return;}
  let out=null;try{out=await res.json();}catch(e){}
  if(!res.ok||!out||out.error){askProg(false);fb.textContent=(out&&out.error)||'The radar is unavailable right now.';fb.className='askfb err';return;}
  askProg(false);fb.textContent='';renderBriefing(q,out);
 }catch(e){askProg(false);fb.textContent='Couldn’t reach the radar — check your connection.';fb.className='askfb err';}
 finally{askBusy=false;go.disabled=false;inp.disabled=false;}
}
document.getElementById('askGo').onclick=askRadar;
document.getElementById('askInput').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();askRadar();}};
document.getElementById('askClear').onclick=clearRadar;

/* ================= DRAWER ================= */
function gauge(label,val,col){const v=Math.max(0,Math.min(100,val||0));
 return '<div class="g"><div class="ring" style="background:conic-gradient('+col+' '+(v*3.6)+'deg,#1a2235 0)"><i>'+(val==null?'–':Math.round(v))+'</i></div><div class="gl">'+label+'</div></div>';}
function sigRows(c,key,labels,prefix,col){
 const defs=D.defs[key]||{};
 return c.sig[key].map((v,i)=>{
  const lab=labels[i],j=c.just[prefix+(i+1)],anch=defs[lab];
  const pct=v==null?0:(v/5*100);
  return '<div class="sr" data-k="'+prefix+(i+1)+'"><div class="top"><span class="lb">'+esc(lab)+'</span>'+
   '<span class="bar"><i style="width:'+pct+'%;background:'+col+'"></i></span><span class="vl">'+(v==null?'–':v)+'</span></div>'+
   '<div class="why">'+(j?esc(j):'<span style="color:var(--mut)">No justification recorded.</span>')+
   (anch?'<div class="def"><b>Anchors:</b> '+esc(anch)+'</div>':'')+'</div></div>';}).join('');}
function connRows(id){
 const rows=links.filter(l=>l.a.id===id||l.b.id===id).map(l=>{
  const other=l.a.id===id?l.b:l.a;
  return {o:other.id,ds:other.ds,sec:other.ds?(byName[other.id]||{}).sec:null,note:l.note};});
 if(!rows.length)return '';
 return '<h4>Connections ('+rows.length+')</h4>'+rows.map(r=>
  '<div class="connrow" onclick="jumpTo(\''+r.o.replace(/'/g,"\\'")+'\')">'+
  '<span class="cdot" style="background:'+(r.ds?(SECCOL[r.sec]||'#9fb0cc'):EXTCOL)+'"></span>'+esc(r.o)+
  (r.note?'<span class="cty">'+esc(r.note)+'</span>':'')+'</div>').join('');}
function jumpTo(id){const n=byId[id];if(!n)return;cx=n.x;cy=n.y;zoom=Math.max(zoom,1.5);
 document.querySelector('nav button[data-v="vSky"]').click();setFocus(id);}
function openCompany(name){
 const c=byName[name];if(!c)return;
 const sc=SECCOL[c.sec]||'#9fb0cc';
 document.getElementById('dt_').textContent=c.n;
 document.getElementById('ds_').innerHTML='<span class="dot" style="background:'+sc+'"></span>'+esc(c.sec)+' · '+esc(c.hq||'—')+' · <span class="confbadge c'+c.conf+'">'+esc(c.conf)+' confidence</span>';
 let h='<div class="kv"><span>Score <b>'+nn(c.epi)+'</b></span><span>Tier <b>'+esc(c.tier)+'</b></span><span>Position <b>'+esc(c.quad)+'</b></span>'+
  (c.hz?'<span>Horizon <b>'+esc(c.hz)+'</b></span>':'')+(c.founded?'<span>Founded <b>'+c.founded+'</b></span>':'')+'</div>';
 h+='<div class="gauges">'+gauge('Willing',c.w,'#e7a93c')+gauge('Distrib',c.d,'#4f8edc')+gauge('AI',c.ai,'#b388ff')+gauge('Score',c.epi,'#f0c84b')+'</div>';
 const pk=[['player','Player'],['product','Product'],['wallet','Wallet']];
 h+='<h4>Pillars held</h4><div class="kv">'+pk.map(p=>'<span style="'+(c.pill[p[0]]?'color:#5fd99a;border-color:#1f4a34':'')+'">'+(c.pill[p[0]]?'✓ ':'✕ ')+p[1]+'</span>').join('')+'</div>';
 h+='<h4>Player journey covered</h4><div class="jstrip">'+D.stages.map((s,i)=>'<span class="jseg'+(c.vc[i]?' on':'')+'">'+esc(s)+'</span>').join('')+'</div>';
 if(c.biz)h+='<h4>Business model</h4><div class="callout">'+esc(c.biz)+'</div>';
 if(c.imp)h+='<h4>What this means for Betsson</h4><div class="callout imp">'+esc(c.imp)+'</div>';
 if(c.gap)h+='<h4>What it still lacks</h4><div class="callout gap">'+esc(c.gap)+'</div>';
 h+='<h4>Scored signals — click a row for the reasoning</h4>';
 h+='<div class="sgrp">Willingness</div>'+sigRows(c,'w',D.labels.w,'W','#e7a93c');
 h+='<div class="sgrp">Distribution readiness</div>'+sigRows(c,'d',D.labels.d,'D','#4f8edc');
 h+='<div class="sgrp">AI readiness</div>'+sigRows(c,'ai',D.labels.ai,'AI','#b388ff');
 const fin=[];if(c.rev)fin.push('<span>Revenue <b>'+esc(c.rev)+'</b></span>');
 if(c.sv)fin.push('<span>Survival <b>'+esc(c.sv)+'</b></span>');
 if(c.fin!=null)fin.push('<span>Health <b>'+c.fin+'%</b></span>');
 if(fin.length)h+='<h4>Financial</h4><div class="kv">'+fin.join('')+'</div>';
 if(c.lic)h+='<h4>Licensed in</h4><div class="callout">'+esc(c.lic)+'</div>';
 h+=connRows(c.n);
 if(c.links&&c.links.length)h+='<h4>Sources ('+c.links.length+')</h4><ul class="srcs">'+
  c.links.map(u=>'<li><a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+esc(u)+'</a></li>').join('')+'</ul>';
 const db=document.getElementById('db_');db.innerHTML=h;db.scrollTop=0;
 db.querySelectorAll('.sr .top').forEach(t=>t.onclick=()=>t.parentElement.classList.toggle('open'));
 document.getElementById('drawer').classList.add('on');
 document.getElementById('scrim').classList.add('on');
}
function openExternal(name){
 document.getElementById('dt_').textContent=name;
 document.getElementById('ds_').innerHTML='<span class="dot" style="background:'+EXTCOL+'"></span>partner entity — named in the research, not itself scored';
 document.getElementById('db_').innerHTML=connRows(name)||'<p style="color:var(--mut)">No recorded links.</p>';
 document.getElementById('drawer').classList.add('on');
 document.getElementById('scrim').classList.add('on');
}
function closeDrawer(){document.getElementById('drawer').classList.remove('on');document.getElementById('scrim').classList.remove('on');}
addEventListener('keydown',e=>{if(e.key==='Escape'){closeBriefing();closeDrawer();clearFocus();}});

/* ================= THREAT BOARD ================= */
(function(){
 const mean=k=>Math.round(C.reduce((a,c)=>a+(c[k]||0),0)/C.length);
 const full=C.filter(c=>c.pill.player&&c.pill.product&&c.pill.wallet).length;
 document.getElementById('tiles').innerHTML=
  '<div class="tile"><div class="v">'+C.length+'</div><div class="k">Companies</div><div class="sub">'+D.externals.length+' partner entities mapped</div></div>'+
  '<div class="tile"><div class="v">'+C.filter(c=>c.tier==='High').length+'</div><div class="k">High threat</div><div class="sub">score ≥ 60</div></div>'+
  '<div class="tile"><div class="v">'+full+'</div><div class="k">Full-stack</div><div class="sub">hold Player + Product + Wallet</div></div>'+
  '<div class="tile"><div class="v">'+mean('ai')+'%</div><div class="k">Mean AI readiness</div><div class="sub">the sector-wide blind spot</div></div>';
})();
let dtK='epi',dtAsc=false;
function drawDt(){
 const cols=[['n','Company'],['sec','Constellation'],['epi','Score'],['w','Will%'],['d','Dist%'],['ai','AI%'],['tier','Tier'],['quad','Position'],['conf','Confidence']];
 const rows=C.slice().sort((a,b)=>{let x=a[dtK],y=b[dtK];
  if(typeof x==='string'||typeof y==='string'){x=String(x||'');y=String(y||'');return (x>y?1:x<y?-1:0)*(dtAsc?1:-1);}
  return ((x||0)-(y||0))*(dtAsc?1:-1);});
 let h='<thead><tr>'+cols.map(c=>'<th data-k="'+c[0]+'">'+c[1]+(dtK===c[0]?(dtAsc?' ▲':' ▼'):'')+'</th>').join('')+'</tr></thead><tbody>';
 rows.forEach(c=>{h+='<tr data-n="'+esc(c.n)+'"><td><span class="dot" style="background:'+(SECCOL[c.sec]||'#999')+'"></span><b>'+esc(c.n)+'</b></td>'+
  '<td style="color:var(--tx2)">'+esc(c.sec)+'</td><td>'+nn(c.epi)+'</td><td>'+nn(c.w)+'</td><td>'+nn(c.d)+'</td><td>'+nn(c.ai)+'</td>'+
  '<td><span class="pill p'+esc(c.tier)+'">'+esc(c.tier)+'</span></td><td style="color:var(--tx2)">'+esc(c.quad)+'</td>'+
  '<td><span class="confbadge c'+c.conf+'">'+esc(c.conf)+'</span></td></tr>';});
 const t=document.getElementById('dt');t.innerHTML=h+'</tbody>';
 t.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;
  if(dtK===k)dtAsc=!dtAsc;else{dtK=k;dtAsc=(k==='n'||k==='sec');}drawDt();});
 t.querySelectorAll('tbody tr').forEach(tr=>tr.onclick=()=>openCompany(tr.dataset.n));
}
drawDt();

/* ================= FINDINGS & METHOD ================= */
(function(){
 const mean=a=>a.length?Math.round(a.reduce((x,y)=>x+y,0)/a.length):0;
 const ops=C.filter(c=>c.sec==='Operator (B2C)');
 const chal=C.filter(c=>c.sec==='AI-native & prediction markets');
 const b2b=C.filter(c=>c.sec==='B2B supplier & platform');
 const full=C.filter(c=>c.pill.player&&c.pill.product&&c.pill.wallet);
 const two=C.filter(c=>Object.values(c.pill).filter(Boolean).length===2);
 const aiTop=C.slice().sort((a,b)=>(b.ai||0)-(a.ai||0))[0];
 const F=[
  {t:'The incumbents are structurally unwilling to disrupt themselves',
   x:'The '+ops.length+' licensed operators average '+mean(ops.map(c=>c.w))+'% on willingness — the lowest of any constellation — while the prediction-market and AI-native entrants average '+mean(chal.map(c=>c.w))+'%. The operators are what is being disrupted, not the disruptors.',
   e:ops.slice().sort((a,b)=>(a.w||0)-(b.w||0)).slice(0,4).map(c=>c.n+' W'+c.w).join(', ')},
  {t:'AI readiness is the sector\'s shared blind spot',
   x:'Mean AI readiness across all '+C.length+' companies is '+mean(C.map(c=>c.ai))+'% — far below willingness and distribution. Not one company in the sample has adopted any agentic-commerce protocol. iGaming talks about AI far more than it ships it.',
   e:'highest: '+aiTop.n+' at '+aiTop.ai+'%'},
  {t:'Only '+full.length+' companies hold the full stack — and half are challengers',
   x:'Player + Product + Wallet together let a company run the betting relationship end to end. Just '+full.length+' of '+C.length+' hold all three: '+full.map(c=>c.n).join(', ')+'. Two are incumbent-scale; two assembled the same stack from outside the licensed model.',
   e:full.map(c=>c.n+' ('+c.sec+')').join(', ')},
  {t:two.length+' companies sit one move from a complete bypass',
   x:'They hold two of the three pillars — for most, the missing piece is the wallet or licensed supply, exactly the gap one acquisition or partnership closes. The next structural shift comes from here, not from the companies already at the top.',
   e:two.slice(0,5).map(c=>c.n+' (missing '+Object.keys(c.pill).filter(k=>!c.pill[k]).join('/')+')').join(', ')},
  {t:'The B2B rail owns the content but never touches the player',
   x:'The '+b2b.length+' suppliers score strongly on product and platform yet near-zero on owned audience — they arm the operators rather than competing with them, which makes them the quiet chokepoint of the whole sky.',
   e:b2b.slice(0,4).map(c=>c.n+' (W'+c.w+'/D'+c.d+')').join(', ')}];
 document.getElementById('findings').innerHTML=F.map((f,i)=>
  '<div class="fcard"><h3>'+(i+1)+'. '+esc(f.t)+'</h3><p>'+esc(f.x)+'</p><div class="ev"><b>Evidence:</b> '+esc(f.e)+'</div></div>').join('');
 document.getElementById('method').innerHTML=
  '<p><b>The question.</b> '+esc(D.frame.title)+'. The incumbent under threat: '+esc(D.frame.incumbent)+'.</p>'+
  '<h3>How the sky is drawn</h3>'+
  '<p>Each of the '+C.length+' companies is a star — sized by company scale, coloured by constellation (its role in the industry), ringed in red when it scores High threat. The faint lines join each constellation\'s stars; the small grey satellites are the '+D.externals.length+' partners, vendors and counterparties named in the research, connected to the companies that named them.</p>'+
  '<h3>How each company is scored</h3>'+
  '<p>18 signals, each 0–5 against fixed anchors defined before research began: willingness to disrupt (5), distribution readiness (6), AI readiness (7). They roll up with fixed weights:</p>'+
  '<ul><li><code>Readiness = ½ Distribution + ½ AI</code></li>'+
  '<li><code>Disruption score = 0.4 × Willingness + 0.6 × Readiness</code></li>'+
  '<li>Bands: ≥60 High · ≥40 Medium · below Low.</li></ul>'+
  '<p>The score measures fit to <i>this question</i>, not size — a giant with no appetite to attack its own funnel scores low by design.</p>'+
  '<h3>Why this exists</h3>'+
  '<p>Betsson is building an AI organisation — a Head of AI role (Malta, Center-of-Excellence remit with explicit '+
  'competitive-radar duties), an AI platform tech lead, AI engineers — and its Director of Data &amp; AI describes the goal as '+
  '<i>agents that answer questions in minutes instead of dashboards</i>. This radar is a working prototype of exactly that: '+
  'a scored, sourced map of who can take the player, with lenses for the three live questions (acquisition risk under AI '+
  'search, M&amp;A targets for the €75m facility, and the prediction-market flank the CEO says he is watching) — and a '+
  'question bar that answers in the language of the business.</p>'+
  '<h3>Where the numbers come from</h3>'+
  '<p>Every score carries a written justification and every company cites its sources — open any star and click a signal row to see the reasoning; the links sit at the bottom of the dossier. Rows carry a confidence grade for how much public evidence was available. These are researched estimates: transparent and traceable, not audited figures.</p>';
 let h='<span>Built by <b style="color:var(--tx2)">'+esc(D.author)+'</b></span>';
 if(D.linkedin)h+='<a href="'+esc(D.linkedin)+'" target="_blank" rel="noopener noreferrer">LinkedIn</a>';
 if(D.github)h+='<a href="'+esc(D.github)+'" target="_blank" rel="noopener noreferrer">Source &amp; data on GitHub</a>';
 h+='<span style="margin-left:auto">dataset '+D.meta.date+' · build '+D.meta.built+'</span>';
 document.getElementById('foot2').innerHTML=h;
})();

initSky();
</script></body></html>"""

# compact grounding index for the AI radar (api/radar.js reads this at cold start)
API = ROOT / "api"
API.mkdir(exist_ok=True)
radar_index = [{
    "n": c["n"], "sec": c["sec"], "w": c["w"], "d": c["d"], "ai": c["ai"], "epi": c["epi"],
    "tier": c["tier"], "quad": c["quad"], "hz": c["hz"], "sv": c["sv"],
    "pillars": "".join(k[0].upper() for k, v in c["pill"].items() if v) or "-",
    "biz": c["biz"][:160], "impact": c["imp"][:160], "gap": (c["gap"] or "")[:120],
} for c in comp]
(API / "company_index_igaming.json").write_text(json.dumps(radar_index, ensure_ascii=False), encoding="utf-8")
print(f"api/company_index_igaming.json written: {len(radar_index)} companies")

VIZ.mkdir(exist_ok=True)
out = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
(VIZ / f"{INDUSTRY}.html").write_text(out, encoding="utf-8")
print(f"viz/{INDUSTRY}.html written: {len(out)//1024} KB")
if not LINKEDIN_URL:
    print("NOTE: LINKEDIN_URL empty — footer renders name only.")
