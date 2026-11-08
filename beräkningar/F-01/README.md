# F-01 rev A – Förutsättningar, referenser och laster

Översiktshandling inför tekniskt samråd: objekt, bärande system, regelverk och klasser, karakteristiska laster samt förteckning över reviderade bygglovsritningar, handlingarna till samrådet och nummerserierna. Detaljhandlingarna (K-01, K-02 …) bygger på förutsättningarna här.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Objektuppgifter, takets egenvikt per skikt, bjälklag, nyttig last, snö, vind, klasser, uppdaterade revisioner av bygglovsdokument och **registret** över alla handlingar: nummerserierna (`[[serie]]`, med betydelse, avsnitt och om de lämnas in till tekniskt samråd) och handlingarna (`[[handling]]`). Pdf:en listar bara handlingarna till samrådet; webbplatsen (`verktyg/bygg/startsida.py`) visar allt |
| `berakning.py` | Summerar egenvikter, räknar snölast och vindens hastighetstryck, skriver `resultat.json` och bygger PDF |
| `mall.typ` | Typst-mall för dokumentet |

## Köra

```
pip install -r requirements.txt
python berakning.py
```

Resultat: `F-01_forutsattningar.pdf`. Ändra bara i `indata.toml` för att räkna om, även handlingsförteckningen och dess status. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito måste finnas installerat (Debian/Ubuntu: `fonts-crosextra-carlito`). Skriptet letar efter typsnitt i `/usr/share/fonts`.
