# AR-02 rev A – Utsättning

Egen arbetsritning för utförandet, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Utsättningspunkter för huset i SWEREF 99 12 00 (Tanums kommun) och de kritiska höjderna i RH2000: fasadens utsida, bottenplattans kant och plattan på marks kant med koordinater, och en sektion med cellplastens underkant under bottenplattan, bottenplattans och mellanplattans överkant (= färdigt golv, betonggolv), medelmarknivån och byggnadshöjden (medelmarknivån till skärningspunkten mellan fasad och takplan på den nordvästra långsidan). Alla höjder anges i RH2000 och relativt fixpunkten FIX, en stålbult i berg vid tomtens västra hörn (+7,76 enligt situationsplanen), som höjderna mäts från på bygget.

| Blad | Innehåll | Skala |
|---|---|---|
| AR-02.1 | Plan med punkterna F1–F12 (fasadens utsida), B1–B12 (bottenplattans kant) och P1–P3 (plattan på mark), fasadens mått, koordinattabeller med höjder, översikt med fixpunkten och dess koordinater | 1:100, 1:500 |
| AR-02.2 | Sektion A–A med höjder, höjdtabell med underlag | 1:50 |

| Fil | Innehåll |
|---|---|
| `indata.toml` | Fasadens hörn i SWEREF ur utsättningsdatan (09_91), fasadens skikt, höjderna ur bygglovet (FG, MMN, byggnadshöjd, ny mark) och K-05/K-06/R-04, fixpunkten |
| `passning.py` | Kontroll: passar husets kontur mot bygglovets situationsplan (vektorerna i pdf:en: rutnätets kors och husets yta) |
| `ritningar.py` | Bladen AR-02.1 och AR-02.2 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/) |

Fasadens utsida ligger 95 mm utanför mellanbjälklagets kant runt hela huset: väggarnas regel (även gavlarnas) 30 mm, kontrollerat mot modellen med `verktyg/modellanalys`, och beklädnaden 65 mm (utvändig gips 10, spikläkt 12, bärläkt 21, panel 22). Bottenplattans kontur kommer ur R-05:s `kallare.py`, mellanbjälklagets ur K-05:s `bild/geometri.json`. Husets läge (vridning och förflyttning) passas in i `ritningar.py` mot utsättningsdatans hörn, som ska stämma med fasadens mått inom 2 mm; bottenplattans och plattan på marks punkter beräknas med samma läge. Fixpunktens läge är mätt ur situationsplanen (cirka ±0,1 m).

## Köra

```
pip install -r requirements.txt
python passning.py       # kräver bygglovets situationsplan i lokalt/bygglov/ (versionshanteras inte)
python ritningar.py      # ritningar/AR-02 Utsättning.pdf
```

Ritningsserien blir en pdf i [`ritningar/`](../../ritningar/) med ett blad per sida. Bladen (`blad/`) och `AR-02.x.json` skapas här och versionshanteras inte. Ändra bara i `indata.toml`.
