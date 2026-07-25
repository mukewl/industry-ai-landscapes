"""Quick peek at selected companies' key fields. Edit TARGETS or pass names as args.

    python -X utf8 scripts/peek.py [Company name] [Company name] ...
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "companies.json"

TARGETS = ['Accelya', 'TBO Tek', 'Yanolja', 'Naver / Line', 'Meituan', 'Spotnana',
           'Layla', 'Otto', 'Verteil Technologies', 'TPConnects', 'Mystifly',
           'Flipkart (+ Cleartrip)', 'Paytm (Checkin)', 'Ramp', 'Brex', 'Swifty',
           'Serko.ai', 'Tata Neu', 'Rippling', 'Nubank', 'Blockskye', 'Kiwi.com',
           'Hopper Cloud', 'Almosafer', 'RateHawk', 'Wego', 'Perplexity', 'OpenAI',
           'Klarna', 'PayPal', 'Amazon', 'Mindtrip']


def main():
    targets = sys.argv[1:] or TARGETS
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for c in data:
        if c["company"] in targets:
            head = (f"(EPI={c.get('entry_potential_index')}, {c.get('threat_tier')}, "
                    f"{c.get('quadrant')}, surv={c.get('survival_tier')})")
            print("####", c["company"], head)
            print("  impact:", str(c.get("impact_on_amadeus_line"))[:450])
            print("  partners:", str(c.get("existing_partnerships"))[:250])


if __name__ == "__main__":
    main()
