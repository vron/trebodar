# Balkplåtar – nock- och dalbalkar

Stålplåtar S355J2+N 200 × 10 mm till nock- och dalbalkarna enligt K-01 rev C. En STEP-fil (3D-solid) och en DXF-fil (2D-kontur) per plåt, för laserskärning. Hål Ø13 mm genomgående, cylindriska, utan försänkning, för skruv Rothoblaas HBS PLATE EVO 10×80 (HBSPLEVO1080).

## Namn och koordinater

`NB1-1-O` = **N**ock**b**alk **1**, bit **1**, **ö**verplåt (`U` = underplåt, `DB` = dalbalk).

Varje plåt är ritad sedd ovanifrån i monterat läge:

- x = 0 vid plåtens ände närmast balkens vänstra ände (samma vänster som i K-01)
- y = 0 vid plåtens kant mot balkens framsida
- z = 0 plåtens undersida, z = 10 ovansida (STEP)

Över- och underplåt har speglade hålbilder (y_under = 200 − y_över) och kan inte bytas mot varandra. Märk varje plåt efter skärning med sitt namn, med en pil mot balkens vänstra ände och med framsidans kant.

## Filer

| Fil | Innehåll |
|---|---|
| `*.step` | STEP AP214, enhet mm, en solid per fil, produktnamn = plåtens namn |
| `*.dxf` | DXF R2010, enhet mm. Lager `KONTUR` (ytterkontur) och `HAL` (hål) |
| `generera.py` | Skapar filerna från hålbilderna i `beräkningar/K-01/halbild_*.csv` |

Generera om efter ändring i K-01: `pip install cadquery ezdxf` och `python generera.py`. Plåtens mått och hålens diameter läses ur K-01:s `indata.toml` (hålet hör till skruven i `[skruv]`), lägena ur hålbilderna. Skriptet kontrollerar varje plåts volym och antal hål. Kontrollera sedan filerna med `verktyg/modellanalys/kontroll_balkplattor.py`, som läser STEP- och DXF-filerna oberoende och jämför hålen med K-01.

## Förteckning

| Fil | Balk | Bit | Läge | Längd (mm) | Läge i balken (mm) | Hål | Vikt (kg) |
|---|---|---|---|---|---|---|---|
| `DB2-1-O` | Dalbalk 2 | 1 | överplåt | 3733 | 6337–10070 | 48 | 58,1 |
| `DB2-1-U` | Dalbalk 2 | 1 | underplåt | 3733 | 6337–10070 | 48 | 58,1 |
| `DB4-1-O` | Dalbalk 4 | 1 | överplåt | 5540 | 1940–7480 | 98 | 86,0 |
| `DB4-1-U` | Dalbalk 4 | 1 | underplåt | 5540 | 1940–7480 | 98 | 86,0 |
| `NB1-1-O` | Nockbalk 1 | 1 | överplåt | 5970 | 5600–11570 | 86 | 92,8 |
| `NB1-1-U` | Nockbalk 1 | 1 | underplåt | 5970 | 5600–11570 | 86 | 92,8 |
| `NB3-1-O` | Nockbalk 3 | 1 | överplåt | 5235 | 5835–11070 | 57 | 81,6 |
| `NB3-1-U` | Nockbalk 3 | 1 | underplåt | 5235 | 5835–11070 | 57 | 81,6 |
| `NB5-1-O` | Nockbalk 5 | 1 | överplåt | 4825 | 0–4825 | 48 | 75,3 |
| `NB5-1-U` | Nockbalk 5 | 1 | underplåt | 4825 | 0–4825 | 48 | 75,3 |
| `NB5-2-O` | Nockbalk 5 | 2 | överplåt | 5145 | 7225–12370 | 56 | 80,2 |
| `NB5-2-U` | Nockbalk 5 | 2 | underplåt | 5145 | 7225–12370 | 56 | 80,2 |
| **Summa** | | | | **60896** | | **786** | **948** |
