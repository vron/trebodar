# Beräkningar – Fritidshus Trebodar

Konstruktionsberäkningar för nock- och dalbalkarna (limträ GL30c 200×170 med stålplåtar S355 200×10 i över- och underkant).
Varje dokument genereras från en indatafil med Python och sätts ihop till PDF med Typst.

| Dokument | Innehåll | Källfiler | PDF |
|---|---|---|---|
| K-01 rev C | Nock- och dalbalkar: statik, partiell samverkan, skruv, plåt, limträ, stöd, stolpe, temperatur | [`K-01/`](K-01) | `K-01revC Nock- och dalbalkar.pdf` |
| K-02 rev A | Värmeflöde kring nockbalken, plåtarnas temperatur vintertid (2D FE) | [`K-02/`](K-02) | `K-02revA Nocklbalk - temperatur i stålplåtarna.pdf` |

## Köra

```
pip install -r requirements.txt
cd K-01 && python berakning.py
cd K-02 && python berakning.py
```

Typsnittet Carlito måste finnas installerat (i Debian/Ubuntu: `fonts-crosextra-carlito`). Skripten letar efter typsnitt i `/usr/share/fonts`.

Ändra bara i `indata.toml` för att räkna om. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i respektive mapp och är inte versionshanterade.
