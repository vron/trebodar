# AV-01 rev A – Avfallshanteringsplan

Avfallshanteringsplan inför tekniskt samråd, i två delar: rivning av det befintliga fritidshuset och nybyggnaden. Rivningsdelen bygger på materialinventeringen från CTP Entreprenad AB (2025-11-16), som hör till lovbeslutet, och innehåller en begäran om dispens enligt avfallsförordningen 3 kap. 33 § för att lämna byggnadsdelar med isoleringen kvar.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Projektuppgifter, ansvar, rivningsavfall och avfallsslag för nybyggnaden |
| `mall.typ` | Typst-mall med dokumentets text |
| `bygg.py` | Läser `indata.toml` och bygger PDF |

## Köra

```
pip install -r requirements.txt
python bygg.py
```

Resultat: `AV-01_avfallshanteringsplan.pdf`. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito måste finnas installerat (Debian/Ubuntu: `fonts-crosextra-carlito`).
