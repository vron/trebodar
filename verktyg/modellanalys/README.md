# Modellanalys – verktyg för STEP-sammanställningar

Läser en STEP-fil (t.ex. Onshape-exporten av huset, `modeller/trebodar.step`) med exakt B-rep-geometri, delnamn och färger, och svarar på frågor om den: översikt, delträd, exakta koordinater, 3D-bilder från valfri vinkel med snittklipp, 2D-snittritningar med mm-koordinater, linjeprober (skikttjocklekar), avstånd, krockar och skillnader mellan versioner.

Standardfil: `../../modeller/trebodar.step`. Annan fil: `--fil väg/till.step`. Enhet mm, filens globala koordinatsystem.

## Installation

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Kör sedan allt via `./ma` (använder `.venv`). Första körningen mot en fil bygger en cache i `.cache/` (några sekunder); en ny export (annat innehåll) får automatiskt en ny cache.

## Kommandon

| Kommando | Gör |
|---|---|
| `./ma oversikt` | Omfång, grupper med storlek, delar och färger |
| `./ma trad [--djup N] [--under Källaren] [--grupper]` | Sammanställningsträdet med id, storlek och färg |
| `./ma delar "K Pillar" [--sortera x\|y\|z\|volym\|namn]` | Tabell: bbox, storlek, volym, färg |
| `./ma info "#6" [--horn]` | Exakt geometri: plana ytor med läge (x = …), cylindrar (axel, Ø), hörnpunkter |
| `./ma vy [--fran iso,ovan,fram] [--klipp "z<14500"] …` | 3D-bild, se nedan |
| `./ma snitt z=13865 [--bortom -3000] …` | 2D-snittritning med koordinater, se nedan |
| `./ma linje "x=-5000,y=6000"` | Alla delar längs en linje (här lodrätt): från, till, tjocklek, tomrum |
| `./ma linje x1,y1,z1 x2,y2,z2` | … mellan två godtyckliga punkter |
| `./ma punkt x,y,z` | Vilka delar punkten ligger i och de närmaste delarna (med närmaste punkt) |
| `./ma matt "urval A" "urval B"` | Minsta avstånd mellan två urval, med punkterna |
| `./ma krock [urval] [urval2] [--minvol mm³]` | Solider som överlappar (gemensam volym) |
| `./ma jamfor [annan.step]` | Nya, borttagna och ändrade delar mot annan fil eller föregående cachade version |

**Urval** (överallt där delar väljs, även `--delar`, `--utom`, `--spok`, `--markera`, `--etiketter`, `--fokus`): kommaseparerat, skiftlägesokänsligt. `#12` eller `#12-20` = id, text med `*` eller `?` = glob (hakparenteser är bokstavliga, som i `K Pillar [13]`), annars delsträng i sökvägen (`Källaren` väljer allt under Källaren).

### 3D-bilder (`vy`)

- `--fran`: `iso` (= `-x-y+z`), `iso-no`, `iso-so`, `iso-nv`, `ovan`, `under`, `fram` (`-y`), `bak`, `vanster`, `hoger`, valfri kombination `+x-y+z`, eller `az,el` i grader. Flera vyer med komma ger en bild med delbilder (`az,el`-par skiljs med `;`).
- `--klipp "z<14500"` behåller allt under z = 14 500 (`x>-3000` osv., godtyckligt plan `"o=x,y,z n=nx,ny,nz"`). Kan upprepas. Snittytorna får exakta lock i delens färg.
- `--delar`, `--utom`, `--spok` (genomskinligt), `--spok-ovriga URVAL` (allt annat genomskinligt), `--markera` (rött), `--etiketter`, `--fokus` (kameran ramar in urvalet), `--zoom`, `--rutnat` (koordinataxlar i mm), `--perspektiv`, `--storlek 1600x1200`, `--ut fil.png`.

### Snittritningar (`snitt`)

- Plan: `z=13865`, `x=-5000`, `y=6000` eller `"o=x,y,z n=nx,ny,nz"`. Axlarna är globala koordinater (för `x=` är vågrätt y och lodrätt z).
- Snittytorna beräknas exakt ur B-rep och fylls i delens färg; tabellen under bilden ger varje dels utbredning i snittet.
- `--bortom -3000` ritar även det som syns upp till 3 m bortom snittet (tecknet anger åt vilket håll man tittar), skuggat och ljusare med avståndet.
- `--origo u,v` mäter i ett lokalt system (t.ex. en ritnings origo i globala koordinater); `--omrade` och alla utskrivna koordinater blir relativa.
- `--omrade u0,u1,v0,v1` beskär, `--rutnat 500` rutnät var 500 mm, `--koordinater` skriver ut snittytornas hörn, `--json fil` sparar all snittgeometri, `--inga-etiketter`.

Bilder hamnar i `ut/` om inte `--ut` anges.

## Underlag till beräkningarna

Beräkningarna läser aldrig modellen. De har sina koordinater i sina egna källfiler (t.ex. `beräkningar/K-05/bild/geometri.json` och `beräkningar/K-03/geometri.json`), som uppdateras för hand. Kontrollerna här läser modellen och källfilerna och redovisar avvikelserna, men skriver ingenting. Kör dem när modellen har ändrats:

```
.venv/bin/python kontroll_geometri05.py   # K-05:s geometri.json: kontur, trapphål, väggar, rör, mark, fria kanter
.venv/bin/python kontroll_k03.py          # K-03:s geometri.json och K-05:s stolplägen
.venv/bin/python kontroll_r031.py         # geometri.json och R-03.1:s måttkedjor
.venv/bin/python kontroll_laster.py       # lastgeometrin i F-01, K-01, K-05 och K-06
.venv/bin/python kontroll_balkplattor.py  # balkplåtarnas skärfiler mot K-01
```

## Python

```python
from modell import Modell
from geometri import Plan, snitt, linjeprob, ytanalys
m = Modell()
platta = m.valj("Mittenplatta")[0]
form = m.form(platta)          # OCP TopoDS_Shape, exakt
V, F = m.nat(platta)           # triangelnät
```

## Filer

| Fil | Innehåll |
|---|---|
| `ma`, `ma.py` | Kommandoraden |
| `modell.py` | Inläsning av STEP (namn, färg, placering), cache, urval |
| `geometri.py` | Exakta frågor: plansnitt, linjeprob, punkt, avstånd, krock, ytanalys |
| `vy.py` | 3D-rendering (pyvista/VTK, offscreen) |
| `ritning.py` | 2D-snittritningar (matplotlib) |
| `jamfor.py` | Jämförelse av en källfils data med modellens och redovisning av avvikelserna |
| `kontroll_geometri05.py` | Kontroll av K-05:s `bild/geometri.json` (kontur, trapphål, Lecaväggar och upplagslinjer, rör, platta på mark, fria kanter) mot modellen |
| `kontroll_k03.py` | Kontroll av K-03:s `geometri.json` (takbalkar, takfönster, takstolar, stolpar, huvudstolpen) och K-05:s stolplägen mot modellen |
| `kontroll_r031.py` | Kontroll av mellanbjälklagets geometri i K-05/R-03 (`beräkningar/K-05/bild/geometri.json`: kontur, trapphål, rör, Lecaväggar) och R-03.1:s måttkedjor mot modellen |
| `kontroll_laster.py` | Kontroll av lastgeometrin i F-01, K-01, K-05 och K-06 mot modellen (lastbredder, lastytor, höjder, fyllning) |
| `kontroll_balkplattor.py` | Kontroll av balkplåtarnas skärfiler (`modeller/balkplattor`, STEP och DXF) mot K-01: hålens lägen och diameter och plåtarnas mått |
| `granskning/` | Redovisade granskningar, t.ex. [`lastgeometri.md`](granskning/lastgeometri.md) |
