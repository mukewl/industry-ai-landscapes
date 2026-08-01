"""Extract the iGaming workbook into industries/igaming/data/*.json.

Thin wrapper around the reference extractor (template/scripts/extract_excel.py) —
no logic changes, just repointed at this industry's workbook and data dir.

    python -X utf8 scripts/extract_igaming.py
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDUSTRY = sys.argv[1] if len(sys.argv) > 1 else "igaming"

spec = importlib.util.spec_from_file_location(
    "extract_excel", ROOT / "template" / "scripts" / "extract_excel.py"
)
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

ex.EXCEL_FILE = ROOT / "industries" / INDUSTRY / f"{INDUSTRY}_landscape.xlsx"
ex.DATA_DIR = ROOT / "industries" / INDUSTRY / "data"
ex.main()
