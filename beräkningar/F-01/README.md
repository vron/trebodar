# F-01 rev A – Förutsättningar, referenser och laster

Översiktshandling inför tekniskt samråd: objekt, bärande system, regelverk och klasser, karakteristiska laster samt förteckning över handlingarna till samrådet och över övriga handlingar, egna underlag som inte lämnas in. Detaljhandlingarna (K-01, K-02 …) bygger på förutsättningarna här.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Objektuppgifter, takets egenvikt per skikt, bjälklag, nyttig last, snö, vind, klasser, handlingar till tekniskt samråd och övriga handlingar (egna underlag) |
| `berakning.py` | Summerar egenvikter, räknar snölast och vindens hastighetstryck, skriver `resultat.json` och bygger PDF |
| `mall.typ` | Typst-mall för dokumentet |

## Köra

```
pip install -r requirements.txt
python berakning.py
```

Resultat: `F-01_forutsattningar.pdf`. Ändra bara i `indata.toml` för att räkna om, även handlingsförteckningen och dess status. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito måste finnas installerat (Debian/Ubuntu: `fonts-crosextra-carlito`). Skriptet letar efter typsnitt i `/usr/share/fonts`.
