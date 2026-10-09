# Balkar – kompletta 3D-modeller

En STEP-sammanställning (AP214, enhet mm) per nock- och dalbalk enligt K-01 rev C. Varje del är ett eget underobjekt med namn och färg:

| Del | Namn i filen | Färg |
|---|---|---|
| Limträ GL30c 200×170 i hel längd | `NB1 limtra GL30c 200x170` | ljust trä |
| Stålplåtar 200×10 med skruvhål enligt `../balkplattor` | `NB1-1-O`, `NB1-1-U` … | grå |
| Distansreglar 200×10 där plåt saknas, 5 mm glipa mot plåtänden | `NB1 distansregel 1-O` … | blekt trä |

Stålplåtarna läses in från `../balkplattor/*.step`, så geometrin är exakt densamma som i skärfilerna. Skruvar och förborrade hål i limträet är inte modellerade.

Koordinater: x längs balken från vänster ände, y = 0 vid balkens framsida, z = 0 vid balkens underkant (balkhöjd 190 mm).

| Fil | Balk | Längd (mm) | Plåt (mm) | Distansreglar (mm) |
|---|---|---|---|---|
| `NB1.step` | Nockbalk 1 | 11 570 | 5 600–11 570 | 0–5 595 |
| `DB2.step` | Dalbalk 2 | 10 070 | 6 337–10 070 | 0–6 332 |
| `NB3.step` | Nockbalk 3 | 11 070 | 5 835–11 070 | 0–5 830 |
| `DB4.step` | Dalbalk 4 | 7 480 | 1 940–7 480 | 0–1 935 |
| `NB5.step` | Nockbalk 5 | 12 370 | 0–4 825 och 7 225–12 370 | 4 830–7 220 |

Generera om efter ändring i K-01: kör först `../balkplattor/generera.py` och sedan `python generera.py` (kräver `pip install cadquery`).
