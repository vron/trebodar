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

Resultat: `K-02_varmeflode_nockbalk.pdf`. Ändra bara i `indata.toml` för att räkna om. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/K-02revA%20Nocklbalk%20-%20temperatur%20i%20sta%CC%8Alpla%CC%8Atarna.pdf).

Typsnittet Carlito måste finnas installerat (Debian/Ubuntu: `fonts-crosextra-carlito`). Skriptet letar efter typsnitt i `/usr/share/fonts`.
