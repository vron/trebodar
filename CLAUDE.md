# Trebodar – instruktioner för Claude

Konstruktionshandlingar för Fritidshus Trebodar, Resö, Tanum: beräkningar, rapporter och ritningar.

## Vid start av en ny session

Läs F-01, förutsättningarna (`rapporter/F-01revA …pdf`, källa i `beräkningar/F-01/`), för en översikt över huset, det bärande systemet, lasterna och handlingarna.

## Källmodell

Husets modell är koden i `modeller/trebodar/` (se dess README): geometriskript per montage, i K-05:s koordinater. Den är husets verkliga geometri. Bygg, exportera och kontrollera den med `verktyg/modellering` (`./mod bygg`, `./mod kontroll`, `./mod rendera`, `./mod webb`); STEP-filen hamnar i `modeller/trebodar/ut/trebodar.step` (versionshanteras inte) och analyseras med `verktyg/modellanalys` (`./ma`, se README). Onshape-modellen som koden byggdes efter är fryst i `modeller/referens/` (med namntabell från Onshapes namn till modellens). Modellens namn är kanoniska och följer handlingarnas beteckningar.

**Beräkningarna läser aldrig modellen.** Varje beräkning har sina koordinater och mått i sina egna källfiler (indata, `geometri.json`, konstanter i koden). En direkt koppling vore skör: när modellens struktur ändras (delnamn, grupper, hur delar är uppdelade) skulle beräkningarna gå sönder eller tyst få fel indata. Källfilerna kontrolleras i stället mot modellen med kontrollerna i `verktyg/modellanalys` (`kontroll_*.py`). De läser både modellen och källfilerna och redovisar avvikelser, men skriver ingenting. Avvikelser rättas för hand i källfilerna eller läggs i `modeller/modell-todo.md`.

## Mappar

- `beräkningar/<nr>/` – källor per handling: indata, beräkning, rapportmall. `beräkningar/ritningsmall/` är den gemensamma A3-mallen. U-xx är egna underlag (utredningar) och AR-xx egna arbetsritningar för utförandet, i samma A3-mall som R-ritningarna. Ingen av dem ingår i handlingarna till tekniskt samråd; de listas i F-01 avsnitt 6.
- `rapporter/` – utgivna rapporter (pdf), kopior av beräkningarnas `rapport/*.pdf`.
- `ritningar/` – en pdf per ritningsserie med ett blad per sida (t.ex. `R-06 Mellanbjälklag.pdf`). Varje blad har egen källa i `beräkningar/R-xx/` (arbetsritningarna i `beräkningar/AR-xx/`). Reviderade bygglovsritningar (`200 Situationsplan.pdf` osv.) är färdiga pdf:er utan källa här; de listas i F-01 avsnitt 5.1.
- `modeller/` – `trebodar/` den kodgenererade modellen, `referens/` Onshape-modellen (fryst), balkar och balkplåtar som STEP (med DXF). `modeller/modell-todo.md` listar det som ska ändras i modellen för att stämma med handlingarna. Lägg till punkter när handlingarna kräver något som modellen saknar, och ta bort dem när modellen är uppdaterad.
- `verktyg/modellering/` – ramverket som bygger modellen: kärna (OCCT, cache, parallellt), export (STEP, GLB, materiallista), kontroll av krockar och kontakter, jämförelse med referensen, rendering (Blender) och webbvisaren.
- `verktyg/modellanalys/` – verktyg för STEP-modellen och kontroller av handlingarna mot den (`kontroll_*.py`, redovisning i `granskning/`). Kontrollerna läser den kodgenererade modellen (bygg den först med `./mod bygg`).
- `docs/` – webbvisaren (three.js) med modellen, publicerad med GitHub Pages på https://vron.github.io/trebodar/ (det som är incheckat på `main`); byggs med `./mod webb` och checkas in när modellen ändras.

## Arbetssätt

- Handlingarna visar alltid bara det senaste, korrekta läget. Ingen historik, inga avsnitt om "åtgärder" eller "ändringar" i rapporter, ritningar, README eller granskningar. Revisionen ändras bara när användaren ber om det.
- Vid alla ändringar som inte är obetydliga: rendera de berörda rapporterna och ritningarna till bilder (t.ex. med pymupdf) och titta på dem, så att de ser bra ut, innan arbetet är klart.
- När modellen ändras: kör `./mod kontroll` i `verktyg/modellering` (inga krockar, glipor eller lösa delar) och `./mod typ`, bygg STEP-filen med `./mod bygg` och kör kontrollerna i `verktyg/modellanalys` (`kontroll_geometri05.py`, `kontroll_k03.py`, `kontroll_r061.py`, `kontroll_r045.py`, `kontroll_laster.py`), och bygg webbvisaren med `./mod webb` (checkas in, så att GitHub Pages visar den). Rätta källfilerna för hand där handlingarna ska följa modellen och kör sedan de berörda beräkningarna och ritningarna, K-03, K-05, K-06, R-04, R-05, R-06 och R-03, i den ordning som deras README anger. K-03 hämtar stolparnas laster ur K-05:s `laster.py`, som bygger på K-01. När K-01 ändras: uppdatera stödreaktionerna i `K-05/laster.py` och kör K-03, K-05 och följande. Generera också om balkplåtarna (`modeller/balkplattor/generera.py`, sedan `modeller/balkar/generera.py`) och kör `kontroll_balkplattor.py`. Kör sedan R-01, ritningen av balkarna. Hålens diameter hör till skruven i K-01:s `[skruv]`.
- Python: `beräkningar/.venv` för beräkningarna, `verktyg/modellering/.venv` för den kodgenererade modellen och `verktyg/modellanalys/.venv` för analysen av STEP-filer (skapa dem med `uv` och respektive `requirements.txt`). Typsnittet Carlito läses från `beräkningar/.fonts` om det inte är installerat.
- Git: commita och pusha självständigt till `main` och arbeta bara på `main`, inga andra grenar. Historiken är linjär (GitHub kräver det för `main`): har `origin/main` nya commits läggs de egna, opushade commitsen ovanpå med `git pull --rebase`, aldrig en merge-commit. Pushad historik skrivs inte om (ingen amend av pushade commits, ingen force push).
