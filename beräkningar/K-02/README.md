# K-02 rev A – Värmeflöde kring nockbalken

Stationär 2D-värmeledning genom nocken vintertid (−20 °C i luftspalten, +25 °C inne) för att bestämma temperaturen i över- och underplåten. Modellen omfattar balken och 1000 mm tak på var sida, med symmetri i nockens mitt.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Geometri, värmekonduktiviteter, luftskikt (SS-EN ISO 6946), randvillkor, nätstorlek och känslighetsfall |
| `termik.py` | Geometri, triangelnät (paketet `triangle`) och FE-lösare med linjära element och konvektiva randvillkor |
| `berakning.py` | Huvudskript: materialdata, alla fall, nät- och 1D-kontroll, figurer, `resultat.json`, PDF |
| `mall.typ` | Typst-mall för dokumentet |

## Köra

```
pip install -r requirements.txt
python berakning.py
```

Resultat: `K-02_varmeflode_nockbalk.pdf`. Ändra bara i `indata.toml` för att räkna om. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. Rapporten byggs till `rapporter/` med `./bygg K-02` och publiceras på https://vron.github.io/trebodar/handlingar/.

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
