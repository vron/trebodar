# K-04 rev A – Trästomme och stabilisering

Lasterna genom trästommen ovanför bjälklaget och kontrollen av stommens alla delar och stabiliseringen, med en
balkmodell (FEM) av hela stommen som byggs ur modellen. Infällda stålband i kryss i väggarna och i takfallen
(modellens `hus/stomme/prefab/stalband/stalband.py`) och skjuvskivorna (utegipsen, OSB:n direkt på reglarna i de
bärande innerväggarna och i gaveln 1SV och råsponten i takfallen, `natverk.skjuvskivor`) tar de horisontella
lasterna. Nock- och dalbalkarna
kontrolleras i K-01, takets anslutningar i K-03 och bjälklaget i K-05.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Projektuppgifter, takets och väggarnas skikt utöver F-01, formfaktorer för vinden, material, kombinationer och kontrollernas faktorer, stålbanden och spiken, skjuvskivorna (utegipsen, OSB:n och råsponten med förband) |
| `natverk.py` | Balkmodellen ur modellens bärverk: delarna som balkar längs sina systemlinjer (delar som ligger an mot varandra längs en sträcka på en gemensam linje), knutpunkterna där linjerna möts, leder, upplag, takstolarnas ståndare och spikreglar utanför och gavlarnas bindningar i sidled; skjuvskivorna i väggarnas regelfack och i takfallens fack |
| `fem.py` | 3D-ramanalys: Timoshenkobalkar med leder, band som bara tar drag, bindningar mellan nodernas förskjutningar, fasta upplag |
| `laster.py` | Lastfallen: egentyngd, snö och vind (F-01) fördelade från takens och väggarnas ytor till delarna |
| `analys.py` | Lastkombinationerna och lösningarna |
| `kontroller.py` | Kontrollerna per grupp av delar (SS-EN 1995-1-1, 1993-1-3) och bruksgränstillståndet |
| `figurer.py` | Balkmodellen i 3D, planen med banden och snitten genom delar som inte klarar lasterna |
| `berakning.py` | Huvudskript: allt ovan, `resultat.json` och PDF |
| `mall.typ` | Typst-mall för rapporten |

## Modellen som underlag

Beräkningen läser modellens bärverk, `modeller/trebodar/ut/barverk.json`, som `./mod barverk` (i
`verktyg/modellering`) skriver ur modellen: stommens delar med läge, tvärsnitt och material och ytorna som lasterna
verkar på (takfallen och väggarna). Utdraget är gränssnittet mot modellen; beräkningen tolkar bara delarnas grupper,
koder, typer och stolpnamn i det. Ändras stommen räknas K-04 om i nästa bygge, utan handpåläggning.

## Köra

```
./bygg K-04                    # i repots rot: ./mod barverk och berakning.py (några sekunder)
python berakning.py            # här, med ett befintligt barverk.json
```

Resultat: `K-04_trastomme.pdf` (kopieras till `rapporter/` av `./bygg`). Figurer, `resultat.json` och PDF skapas i
mappen och versionshanteras inte. Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
