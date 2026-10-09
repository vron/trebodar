# U-01 rev A – Bottenplattan, temperatur och fukt under året

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Transient 2D-värmeledning genom källaren i sektion A–A (y = 6 000 i K-05:s koordinater, husets största bredd) under ett år med golvvärme oktober–april och ingen golvvärme på sommaren. Resultatet är det periodiska tillståndet, alltså det som marken når efter många år. Plattans och markens temperatur bedöms mot tre fuktkriterier: årsmedel, varje dygn och kondens enligt Glaser när gradienten vänder. Antagandena ligger på säker sida, och känslighetsfall visar vad som avgör.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Sektionen (markytans nivåer ur modellen, plintarnas storlek ur K-06), uppbyggnad L300/L400, material, klimat, drift, fuktdata, nät och känslighetsfall |
| `mark2d.py` | Nät, finita volymer, tidsstegning (implicit Euler), periodiskt tillstånd med GMRES och värmebalans |
| `berakning.py` | Huvudskript: alla fall och kontroller, fuktbalans, figurer, `resultat.json`, PDF |
| `mall.typ` | Typst-mall för dokumentet |

Väggarnas och rörens lägen läses ur `../K-05/bild/geometri.json` (modellen). Markytans nivå utanför väggarna är mätt i modellen med `verktyg/modellanalys` (`./ma linje`).

## Köra

```
pip install -r requirements.txt
python berakning.py            # alla fall, kontroller och PDF, några minuter
python berakning.py figurer    # bara grundfallet och figurerna
```

Resultat: `U-01_bottenplatta_fukt.pdf`. Ändra bara i `indata.toml` för att räkna om. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
