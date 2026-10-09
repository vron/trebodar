# Trebodar – instruktioner för Claude

Konstruktionshandlingar för Fritidshus Trebodar, Resö, Tanum: beräkningar, rapporter och ritningar.

## Vid start av en ny session

Läs F-01, förutsättningarna (`rapporter/F-01revA …pdf`, källa i `beräkningar/F-01/`), för en översikt över huset, det bärande systemet, lasterna och handlingarna.

## Källmodell

Husets Onshape-modell är `modeller/trebodar.step` (STEP AP242, mm). Den är husets verkliga geometri. Trästommen under nock- och dalbalkarna och balkarna själva är inte fullständigt modellerade. Analysera modellen med `verktyg/modellanalys` (`./ma`, se README). Mellanbjälklagets geometri (kontur, trapphål, rör, Lecaväggar) hämtas exakt ur modellen av `beräkningar/K-05/bild/geometri.py`.

## Mappar

- `beräkningar/<nr>/` – källor per handling: indata, beräkning, rapportmall. `beräkningar/ritningsmall/` är den gemensamma A3-mallen.
- `rapporter/` – utgivna rapporter (pdf), kopior av beräkningarnas `rapport/*.pdf`.
- `ritningar/` – en pdf per ritningsserie med ett blad per sida (t.ex. `R-03 Mellanbjälklag.pdf`). Varje blad har egen källa i `beräkningar/R-xx/`.
- `modeller/` – STEP-modeller: huset, balkar och balkplåtar (med DXF).
- `verktyg/modellanalys/` – verktyg för STEP-modellen och kontroller av handlingarna mot den (`kontroll_*.py`, redovisning i `granskning/`).

## Arbetssätt

- Handlingarna visar alltid bara det senaste, korrekta läget. Ingen historik, inga avsnitt om "åtgärder" eller "ändringar" i rapporter, ritningar, README eller granskningar. Revisionen ändras bara när användaren ber om det.
- Vid alla ändringar som inte är obetydliga: rendera de berörda rapporterna och ritningarna till bilder (t.ex. med pymupdf) och titta på dem, så att de ser bra ut, innan arbetet är klart.
- När modellen ändras: kör `geometri.py`, sedan K-05, K-06 och R-03 i den ordning som deras README anger, och kontrollerna i `verktyg/modellanalys`.
- Python: `beräkningar/.venv` för beräkningarna och `verktyg/modellanalys/.venv` för modellen (skapa dem med `uv` och respektive `requirements.txt`). Typsnittet Carlito läses från `beräkningar/.fonts` om det inte är installerat.
- Git: commita och pusha självständigt till `main`. Skriv aldrig om historiken (ingen rebase, amend eller force push) och arbeta bara på `main`, inga andra grenar.
