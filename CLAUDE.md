# Trebodar – instruktioner för Claude

Konstruktionshandlingar för Fritidshus Trebodar, Resö, Tanum: beräkningar, rapporter och ritningar.

## Vid start av en ny session

Läs F-01, förutsättningarna (`rapporter/F-01revA …pdf`, källa i `beräkningar/F-01/`), för en översikt över huset, det bärande systemet, lasterna och handlingarna.

## Källmodell

Husets Onshape-modell är `modeller/trebodar.step` (STEP AP242, mm). Den är husets verkliga geometri. Trästommen under nock- och dalbalkarna och balkarna själva är inte fullständigt modellerade. Analysera modellen med `verktyg/modellanalys` (`./ma`, se README).

**Beräkningarna läser aldrig modellen.** Varje beräkning har sina koordinater och mått i sina egna källfiler (indata, `geometri.json`, konstanter i koden). En direkt koppling vore skör: när modellens struktur ändras (delnamn, grupper, hur delar är uppdelade) skulle beräkningarna gå sönder eller tyst få fel indata. Källfilerna kontrolleras i stället mot modellen med kontrollerna i `verktyg/modellanalys` (`kontroll_*.py`). De läser både modellen och källfilerna och redovisar avvikelser, men skriver ingenting. Avvikelser rättas för hand i källfilerna eller läggs i `modeller/modell-todo.md`.

## Mappar

- `beräkningar/<nr>/` – källor per handling: indata, beräkning, rapportmall. `beräkningar/ritningsmall/` är den gemensamma A3-mallen. U-xx är egna underlag (utredningar) som inte ingår i handlingarna till tekniskt samråd. De listas i F-01 avsnitt 6.
- `rapporter/` – utgivna rapporter (pdf), kopior av beräkningarnas `rapport/*.pdf`.
- `ritningar/` – en pdf per ritningsserie med ett blad per sida (t.ex. `R-03 Mellanbjälklag.pdf`). Varje blad har egen källa i `beräkningar/R-xx/`.
- `modeller/` – STEP-modeller: huset, balkar och balkplåtar (med DXF). `modeller/modell-todo.md` listar det som ska ändras i modellen för att stämma med handlingarna. Lägg till punkter när handlingarna kräver något som modellen saknar, och ta bort dem när modellen är uppdaterad.
- `verktyg/modellanalys/` – verktyg för STEP-modellen och kontroller av handlingarna mot den (`kontroll_*.py`, redovisning i `granskning/`).

## Arbetssätt

- Handlingarna visar alltid bara det senaste, korrekta läget. Ingen historik, inga avsnitt om "åtgärder" eller "ändringar" i rapporter, ritningar, README eller granskningar. Revisionen ändras bara när användaren ber om det.
- Vid alla ändringar som inte är obetydliga: rendera de berörda rapporterna och ritningarna till bilder (t.ex. med pymupdf) och titta på dem, så att de ser bra ut, innan arbetet är klart.
- När modellen ändras: kör kontrollerna i `verktyg/modellanalys` (`kontroll_geometri05.py`, `kontroll_k03.py`, `kontroll_r031.py`, `kontroll_laster.py`). Rätta källfilerna för hand där handlingarna ska följa modellen och kör sedan de berörda beräkningarna, K-03, K-05, K-06 och R-03, i den ordning som deras README anger. K-03 hämtar stolparnas laster ur K-05:s `laster.py`, som bygger på K-01. När K-01 ändras: uppdatera stödreaktionerna i `K-05/laster.py` och kör K-03, K-05 och följande. Generera också om balkplåtarna (`modeller/balkplattor/generera.py`, sedan `modeller/balkar/generera.py`) och kör `kontroll_balkplattor.py`. Hålens diameter hör till skruven i K-01:s `[skruv]`.
- Python: `beräkningar/.venv` för beräkningarna och `verktyg/modellanalys/.venv` för modellen (skapa dem med `uv` och respektive `requirements.txt`). Typsnittet Carlito läses från `beräkningar/.fonts` om det inte är installerat.
- Git: commita och pusha självständigt till `main`. Skriv aldrig om historiken (ingen rebase, amend eller force push) och arbeta bara på `main`, inga andra grenar.
