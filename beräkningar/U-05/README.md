# U-05 rev A – Värmeförluster och energibehov

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Utredningen visar hur stor del av värmen som går ut genom varje byggdel och hur mycket energi huset behöver under ett år på platsen. Huset värms bara med golvvärmen i mellanbjälklaget, och källaren värms av bjälklaget ovanför. Utformningen är modellens: mineralull i gavelspetsarna och i ytterväggarnas installationsskikt, men ingen isolering i takets installationsskikt (U-03). Huset används helgerna, inne hålls minst 20 °C, och elens kostnad räknas med månadens elpris. Jämförelsefallen är räkneexempel. Värmen genom kantisoleringen vid mellanbjälklagets kanter redovisas för sig.

Beräkningen går i fyra steg:

1. Byggdelarna räknas i 2D med finita volymer och virkesandelen ur modellen.
2. Köldbryggorna räknas i 2D enligt SS-EN ISO 10211 med invändiga mått.
3. Marken, källaren, bottenplattan, plattan på mark och mellanbjälklaget med golvvärmen räknas i 3D.
4. Huset sätts ihop till ett nät av konduktanser och räknas stationärt och timme för timme med ERA5-väder 2014–2023, med bergvärmepumpens värmefaktor varje timme.

Verktygen är kontrollerade mot analytiska lösningar, SS-EN ISO 6946 och SS-EN ISO 13370 (`tester.py`).

| Fil | Innehåll |
|---|---|
| `indata.toml` | Material, ytmotstånd, uppbyggnader, mängderna ur modellen, öppningarna, fönsterdata, mark, drift och brukare (BEN), ventilation, lufttäthet, värmepump, BBR-krav, klimat, nät och fall |
| `data.py` | Indata med konturen och trapphålet ur `../K-05/bild/geometri.json` och fallens ändringar |
| `fv.py` | Stationär värmeledning med finita volymer i 2D och 3D: material, omgivningar med ytmotstånd, kopplingskoefficienter (LU i 2D, AMG-förbehandlad CG i 3D) |
| `komponenter.py` | Väggarnas, takets och gavelspetsarnas U i 2D med ISO 6946:s gränser, fönstren enligt ISO 10077-1 |
| `skarvar.py` | Köldbryggorna: mellanbjälklagets kant (över källarväggen och vid plattan på mark, med fyra omgivningar), takfoten, nocken, dalen, fönstrens anslutning (karmen som ett block anpassat till Uf) och hörnen |
| `mark3d.py` | 3D-modellen av husets nedre del (källarväggarna ur K-05, plintarna ur K-06, marken efter fasadernas marknivåer) |
| `byggnad.py` | Huset som nät av konduktanser mellan ute, markytan, källaren, plan 1 och golvvärmen; ventilation, infiltration (LBL), trapphålets luftutbyte; stationär värmebalans |
| `klimat.py` | ERA5-klimatet (U-03:s fil), solens läge och instrålningen mot husets ytor |
| `dynamik.py` | Timsimuleringen: plan 1, mellanbjälklaget och källaren, sol, internlast (BEN), golvvärmens styrning, markens tröghet (ISO 13370) |
| `varmepump.py` | Bergvärmepumpen timme för timme: värmefaktorn ur golvvärmens framledning och köldbärarens temperatur (borrhålet med bergets avkylning i tre tidsskalor), anpassad till produktens B0/W35 |
| `tester.py` | Kontrollerna av verktygen |
| `berakning.py` | Huvudskript: 3D-modellen med nätkontroll, skarvarna, fallen, kontrollerna, figurerna, `resultat.json` och PDF |
| `mall.typ` | Typst-mall för dokumentet |

Mängderna i `indata.toml` kontrolleras mot modellen med `verktyg/modellanalys/kontroll_u05.py` (`./ma kontroll_u05.py`). Kontrollen läser ytterväggarnas areor, takfallens omfång i plan, virkesandelarna, karmarnas mått, takfönstren, gavelspetsarnas och installationsskiktens isolering (väggarna och taket var för sig) och marknivåerna. Beräkningen läser inte modellen. `./ma varmebild_u05.py` ritar värmeflödets täthet genom husets yttre ytor som 3D-bilder (en kontroll för ögat av var värmen går ut).

## Köra

```
pip install -r requirements.txt
python berakning.py            # allt, cirka 10 minuter (3D-modellen med 3 miljoner celler och nätkontrollen)
python berakning.py rapport    # utan 3D-modellen: dess kopplingar ur resultat.json
```

Resultat: `U-05_varmeforluster.pdf`. Ändra bara i `indata.toml` för att räkna om. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. U-05 är ett tungt steg i bygget: det räknas lokalt (`./bygg U-05`), och `räknat.json` och rapporten i `rapporter/` checkas in (se [`verktyg/bygg`](../../verktyg/bygg/)).

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
