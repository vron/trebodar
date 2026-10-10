# U-02 rev A – Fasadsten på källarväggarna, infästning

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Ritning över hur granit 40 mm fästs på källarväggarnas ytterväggar av Sundolitt Kub 350-150 (betongkärna 150, cellplast 100 + 100) ovan mark: armeringsbruk med nät och isolerplugg på cellplasten, fästmassa, stödvinkel på konsoler under nedersta skiftet och Halfen UHA-ankare i liggfogarna. Stenen bärs av fästmassan; stålet är dimensionerat för att ensamt bära stenen om fästet mot cellplasten går förlorat. Stenens framsida hamnar 55 mm utanför cellplasten.

| Blad | Innehåll | Skala |
|---|---|---|
| U-02.1 | Sektion A–A genom väggen, detalj B nedre stöd (konsol och stödvinkel), detalj C kvarhållning i liggfog, anvisningar | 1:10, 1:2,5, 1:2 |
| U-02.2 | Fasad E (exempel 790 × 390 i halvstensförband), konsol K för tillverkning, positionsförteckning, dimensionering | 1:20, 1:2,5, 1:5 |

| Fil | Innehåll |
|---|---|
| `indata.toml` | Väggen, skikten, stenen, stödvinkel, konsol, gängstänger (fischer FIS V, ETA-02/0024), Halfen UHA-7 (FS 12/2024), isolerplugg (EJOT STR U 2G, ETA-04/0023), vind och lastfaktorer |
| `berakning.py` | Laster, stödvinkel, konsol och svets, gängstänger, Halfen-ankare och isolerplugg; skriver `resultat.json` |
| `ritningar.py` | Bladen U-02.1 och U-02.2 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/) |

Stenhöjden på en stödvinkel (högst 2,0 m) och stenens läge följer beklädnaden i modellen (`Beklädnad stor`, `Beklädnad liten`), kontrollerad med `verktyg/modellanalys`. Beräkningen läser inte modellen.

## Köra

```
pip install -r requirements.txt
python berakning.py      # resultat.json
python ritningar.py      # ritningar/U-02 Fasadsten på källarväggarna.pdf
```

Ritningsserien blir en pdf i [`ritningar/`](../../ritningar/) med ett blad per sida. Bladen (`blad/`), `U-02.x.json` och `resultat.json` skapas här och versionshanteras inte. Ändra bara i `indata.toml` för att räkna om.
