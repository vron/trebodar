"""
AV-01: avfallshanteringsplan.

    python bygg.py            -> AV-01_avfallshanteringsplan.pdf

Läser indata.toml och sätter ihop PDF via Typst (mall.typ). Kräver: pip install typst
"""
import json
import tomllib
from pathlib import Path

import typst

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
(HERE / "resultat.json").write_text(json.dumps(IN, ensure_ascii=False, indent=1), encoding="utf-8")
pdf = HERE / f"{IN['projekt']['dokument']}_avfallshanteringsplan.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts"])
print(pdf.name)
