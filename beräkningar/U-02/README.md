# U-02 rev A – Nock- och dalbalkar, lyft i två punkter

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Kontrollerar att nock- och dalbalkarnas egentyngd (K-01: limträ GL30c 200 × 170 med limmade stålplåtar på delar av längden) inte skadar dem vid lyft i två punkter med stroppar i en triangel upp till kroken. Avståndet mellan lyftpunkterna itereras för varje balk tills utnyttjandet, med lastfaktor 1,35 och dynamisk faktor 2,0, är högst 50 %; det största avrundas uppåt och redovisas som ett gemensamt avstånd. Lyft i en punkt och med gaffeltruck i mitten räknas som jämförelse och sparas i `resultat.json` men redovisas inte.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Lastfaktorer, materialfaktorer, stroppvinkel, krav och iterationssteg |
| `berakning.py` | Balkarna ur `../K-01/indata.toml`, egentyngd och styvhet längs balken, snittkrafter, spänningar och nedböjning, iterationen, figur, `resultat.json` och PDF |
| `mall.typ` | Typst-mall för dokumentet (en sida) |

## Köra

```
python berakning.py      # U-02_lyft_balkar.pdf
```

Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).
