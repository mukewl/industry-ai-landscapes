# ============================================================
# TEMPLATE REFERENCE COPY (from the Amadeus travel-distribution project).
# This is WORKING code for the travel industry, shipped as the reference
# implementation. To adapt it to a new industry, follow the numbered steps
# in ../ADAPTATION-CHECKLIST.md (or ADAPTATION-CHECKLIST.md at template root)
# -- every industry-specific marker in this file is listed there by name.
# ============================================================
"""Build data/relationships.json (graph dataset) from partnership free text.

v1 heuristic parser. Every edge keeps the raw source snippet so a human (or a
later session) can verify/correct. Curated corrections go in
data/relationships_manual.json (same edge schema, field "override": true) and
are merged on top at load time by consumers.

    python -X utf8 scripts/extract_relationships.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# fields mined for edges, with default edge type
SOURCE_FIELDS = [
    ("existing_partnerships", "partner"),
    ("gen_ai_platform_partnerships", "ai_platform"),
]

TYPE_RULES = [
    (r"acquir|acquisition|bought|merged|integrated\)", "acquired"),
    (r"investor|ventures|backed|capital|equity|owner|owns|majority|shareholder|lead series", "investor"),
    (r"power|white.?label|built on|runs on|engine|provides|supplies|infrastructure", "powers"),
    (r"\bgds\b|distribution agreement|ndc (content|distribution|aggregat)", "gds_or_content_link"),
    (r"payment|checkout|wallet|card", "payments"),
]

# strings that are not entities
NOISE = re.compile(
    r"^(yes|no|n/a|none|various|multiple|other|etc\.?|and other.*|plus .*|including|incl\.?|"
    r"\d+\+? (banks?|airlines?|hotels?|properties|partners?|carriers?|customers?|agents?).*|"
    r"~?\d[\d,.]*\s*$)", re.I)

LEADING_LABEL = re.compile(r"^(gds|ota|investors?|backers?|partners?|content|payments?|hotels?|air(lines)?)\s*:\s*", re.I)

# manual aliases → dataset company names (extend as found)
ALIASES = {
    "expedia": "Expedia Group",
    "trip.com": "Trip.com Group",
    "sabre": "Sabre (Mosaic)",
    "sabremosaic": "Sabre (Mosaic)",
    "booking holdings": "Booking.com",
    # "priceline" deliberately NOT aliased: it acts as a distinct B2B supply rail
    # (powers Ramp etc.) — own node per user decision D11; parent edge added in
    # relationships_manual.json
    "alibaba": "Alibaba / Fliggy",
    "fliggy": "Alibaba / Fliggy",
    "alipay": "Alibaba / Fliggy",
    "google gemini": "Google",
    "gemini": "Google",
    "walmart": "Walmart (Sparky + Gemini partnership)",
    "rakuten": "Rakuten (Rakuten AI + Travel)",
    "klook": "Klook",
    "uber": "Uber (Hopper-powered travel + Uber One)",
    "kiwi.com": "Kiwi.com",
    "hopper technology solutions": "Hopper Cloud",
    "hts": "Hopper Cloud",
    "paytm": "Paytm (Checkin)",
    "visa": "Visa Intelligent Commerce + Connect",
    "mastercard": "Mastercard Agent Pay",
    "naver": "Naver / Line",
    "line": "Naver / Line",
}


def classify(fragment, default):
    low = fragment.lower()
    for pat, etype in TYPE_RULES:
        if re.search(pat, low):
            return etype
    return default


def split_entities(text):
    """Split a fragment into entity names, keeping parenthetical notes attached."""
    # protect commas inside parentheses
    out, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch in ",;" and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [e.strip(" .;") for e in out if e.strip(" .;")]


def entity_name(raw):
    """Strip role notes to get the bare entity name."""
    name = re.sub(r"\([^)]*\)", "", raw).strip(" .,'\"")
    name = LEADING_LABEL.sub("", name).strip()
    name = re.sub(r"^(and|with|via|through|plus|also|formerly)\s+", "", name, flags=re.I)
    # strip leading verb phrases so 'acquired itinerary service Pluto' -> 'Pluto' is NOT
    # attempted (too lossy); instead drop the verb words and keep the tail noun phrase
    name = re.sub(r"^(was\s+)?(acquired( by)?|acquirer|merged( with)?|bought|owns|owned by|"
                  r"agreed( to be)? acquisition by|agreed to be acquired by|integrated|"
                  r"powered by|powers|backed by|invested in)\s+", "", name, flags=re.I)
    # drop trailing clauses after ' - ' or ' in 20xx'
    name = re.sub(r"\s+in\s+(19|20)\d\d.*$", "", name)
    name = re.sub(r"\s+-\s+.*$", "", name)
    return name.strip(" .,'\"")


# direction: these markers mean the *target text* is the acquirer of the source company
ACQUIRED_BY = re.compile(
    r"acquired by|acquirer|acquirer/parent|parent since|owned by|owner|majority owner|"
    r"agreed( to be)? acquisi|being acquired by|merged into|bought by", re.I)
ACQUIRED_OTHER = re.compile(r"^\s*acquired\s+(?!by)|\bacquired\s+\w|\(acquired", re.I)


def acquisition_direction(raw):
    """Return 'inbound' if the named entity acquired the row company,
    'outbound' if the row company acquired the named entity, else 'unclear'."""
    if ACQUIRED_BY.search(raw):
        return "inbound"
    if ACQUIRED_OTHER.search(raw):
        return "outbound"
    return "unclear"


def main():
    companies = json.loads((DATA / "companies.json").read_text(encoding="utf-8"))
    by_norm = {}
    for c in companies:
        n = c["company"]
        by_norm[n.lower()] = n
        # also index the head word(s) before slashes/parens, e.g. "Alibaba / Fliggy"
        for part in re.split(r"[/(+]", n):
            p = part.strip().lower()
            if len(p) > 3:
                by_norm.setdefault(p, n)

    def resolve(name):
        low = name.lower()
        if low in ALIASES:
            ali = ALIASES[low]
            return ali, ali.lower() in by_norm or any(c["company"] == ali for c in companies)
        if low in by_norm:
            return by_norm[low], True
        return name, False

    edges = []
    for c in companies:
        src = c["company"]
        for field, default in SOURCE_FIELDS:
            text = c.get(field)
            if not text or str(text).strip().lower() in ("y", "n", "yes", "no", "none"):
                continue
            # split on ';' first (major groups), then entities within
            for group in str(text).split(";"):
                group = group.strip()
                if not group:
                    continue
                etype_hint = classify(group, default)
                for raw in split_entities(group):
                    name = entity_name(raw)
                    if not name or len(name) < 2 or NOISE.match(name):
                        continue
                    target, internal = resolve(name)
                    if target == src:
                        continue
                    etype = classify(raw, etype_hint)
                    edge = {
                        "source": src,
                        "target": target,
                        "type": etype,
                        "target_in_dataset": internal,
                        "field": field,
                        "raw": raw[:200],
                    }
                    if etype == "acquired":
                        d = acquisition_direction(raw)
                        edge["direction"] = d
                        if d == "inbound":
                            # normalize: source = acquirer, target = acquired company
                            edge["source"], edge["target"] = target, src
                            edge["target_in_dataset"] = True
                            edge["source_in_dataset"] = internal
                    edges.append(edge)

    # apply curated overrides
    manual_path = DATA / "relationships_manual.json"
    if manual_path.exists():
        manual = json.loads(manual_path.read_text(encoding="utf-8"))
        drops = {(d["source"], d["target"], d["type"]) for d in manual.get("drop", [])}
        before = len(edges)
        edges = [e for e in edges if (e["source"], e["target"], e["type"]) not in drops]
        edges += manual.get("add", [])
        print(f"manual overrides: dropped {before - len(edges) + len(manual.get('add', []))}, "
              f"added {len(manual.get('add', []))}")

    # nodes: all companies + external entities seen >= 2 times (cuts noise)
    from collections import Counter
    ext_count = Counter(e["target"] for e in edges if not e["target_in_dataset"])
    nodes = [{"id": c["company"], "in_dataset": True,
              "sector": c.get("source_sector_taxonomy"),
              "epi": c.get("entry_potential_index"),
              "threat_tier": c.get("threat_tier")} for c in companies]
    nodes += [{"id": name, "in_dataset": False, "mentions": n,
               "is_amadeus": name.lower().startswith("amadeus")}
              for name, n in ext_count.items() if n >= 2]

    out = {"nodes": nodes, "edges": edges,
           "note": "v1 heuristic extraction - verify edges via 'raw' field; "
                   "curated fixes go in relationships_manual.json"}
    (DATA / "relationships.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    internal = sum(1 for e in edges if e["target_in_dataset"])
    print(f"edges: {len(edges)} ({internal} between dataset companies)")
    print(f"nodes: {len(nodes)} ({sum(1 for n in nodes if not n.get('in_dataset'))} external with >=2 mentions)")
    print("top external hubs:", ext_count.most_common(15))
    types = Counter(e["type"] for e in edges)
    print("edge types:", dict(types))


if __name__ == "__main__":
    main()
