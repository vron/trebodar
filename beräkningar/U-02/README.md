# U-02 rev A – Fasadsten på källarväggarna, infästning

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Ritning över hur granit 40 mm fästs på källarväggarnas ytterväggar av Sundolitt Kub 350-150 (betongkärna 150, cellplast 100 + 100) ovan mark. Stenen limmas mot armeringsbruk med nät, som är pluggat genom nätet in i betongkärnan, och står på en rostfri stödvinkel under nedersta skiftet. Vinkeln bärs av gängstänger M16 genom cellplasten och är dimensionerad för att ensam bära stenen om fästet mot cellplasten går förlorat. Inga infästningar i de enskilda stenarna, som i de godkända systemen för natursten på cellplast. Stenens framsida hamnar 55 mm utanför cellplasten.

| Blad | Innehåll | Skala |
|---|---|---|
| U-02.1 | Sektion A–A genom väggen, detalj B stödvinkeln på gängstång, detalj C armeringsbruk och isolerplugg genom nätet, anvisningar | 1:10, 1:2,5, 1:2 |
| U-02.2 | Fasad E (exempel 790 × 390 i halvstensförband), positionsförteckning, dimensionering | 1:20 |

| Fil | Innehåll |
|---|---|
| `indata.toml` | Väggen, skikten, stenen, stödvinkel, gängstänger (fischer FIS V, ETA-02/0024), isolerplugg (EJOT STR U 2G, ETA-04/0023), vind och lastfaktorer |
| `berakning.py` | Laster, gängstänger med hävarm genom cellplasten (SS-EN 1992-4), stödvinkel och isolerplugg; skriver `resultat.json` |
| `ritningar.py` | Bladen U-02.1 och U-02.2 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/) |

Stenhöjden på en stödvinkel (högst 2,0 m) och stenens läge följer beklädnaden i modellen (`Beklädnad stor`, `Beklädnad liten`), kontrollerad med `verktyg/modellanalys`. Beräkningen läser inte modellen.

## Köra

```
pip install -r requirements.txt
python berakning.py      # resultat.json
python ritningar.py      # ritningar/U-02 Fasadsten på källarväggarna.pdf
```

Ritningsserien blir en pdf i [`ritningar/`](../../ritningar/) med ett blad per sida. Bladen (`blad/`), `U-02.x.json` och `resultat.json` skapas här och versionshanteras inte. Ändra bara i `indata.toml` för att räkna om.
