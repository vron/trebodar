# K-02 rev A – Värmeflöde kring nockbalken

Stationär 2D-värmeledning genom nocken vintertid (−20 °C i luftspalten, +25 °C inne) för att bestämma temperaturen i över- och underplåten. Modellen omfattar balken och 1000 mm tak på var sida, med symmetri i nockens mitt.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Geometri, värmekonduktiviteter, luftskikt (SS-EN ISO 6946), randvillkor, nätstorlek och känslighetsfall |
| `termik.py` | Geometri, triangelnät (paketet `triangle`) och FE-lösare med linjära element och konvektiva randvillkor |
| `berakning.py` | Huvudskript: materialdata, alla fall, nät- och 1D-kontroll, figurer, `resultat.json`, PDF |
| `mall.typ` | Typst-mall för dokumentet |

Kör: `python berakning.py` → `K-02_varmeflode_nockbalk.pdf`.
