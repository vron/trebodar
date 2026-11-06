# Modellanalys – verktyg för STEP-sammanställningar

Läser en STEP-fil (som standard den kodgenererade modellen, `modeller/trebodar/ut/trebodar.step`, som byggs med `verktyg/modellering/mod bygg`) med exakt B-rep-geometri, delnamn och färger, och svarar på frågor om den: översikt, delträd, exakta koordinater, 3D-bilder från valfri vinkel med snittklipp, 2D-snittritningar med mm-koordinater, linjeprober (skikttjocklekar), avstånd, krockar och skillnader mellan versioner.

Standardfil: `../../modeller/trebodar/ut/trebodar.step` (kodgenererad, K-05:s koordinater). Onshape-modellen: `--fil ../../modeller/referens/trebodar-onshape.step`. Annan fil: `--fil väg/till.step`. Enhet mm, filens globala koordinatsystem.

## Installation

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Kör sedan allt via `./ma` (använder `.venv`).

## Tjänsten, cachen och modellens senaste bygge

`./ma` skickar kommandot till **ma-tjänsten** ([`tjanst.py`](tjanst.py), via [`klient.py`](klient.py)): en process som
ligger kvar med biblioteken och modellen inlästa, så att ett anrop tar en bråkdel av en sekund i stället för
sekunder. Tjänsten startas av första anropet och avslutar sig själv efter 20 minuter utan anrop, eller när
modellanalysens kod ändras (nästa anrop startar en ny). Den kör ett anrop i taget, i anroparens mapp, och
utdata och slutkod blir desamma som utan tjänsten. Snitten räknas per del och sparas i tjänsten (`geometri.snitt`),
så att ett nytt snitt i samma plan bara räknar om de delar som har ändrats, även efter att modellen har byggts om.

```
./ma tjanst            # körs tjänsten?
./ma tjanst stopp      # avsluta den
MA_TJANST=0 ./ma …     # utan tjänsten, i en egen process
```

Varje fil som läses får en **cache** i `.cache/<filnamn>-<hash>/` (`index.json`, `nat.npz`, `former.bin`); en ny
export (annat innehåll) får en ny cache och de fyra senast använda per filnamn sparas. Att bygga cachen ur en STEP-fil
tar en halv minut.

Den **kodgenererade modellen** (standardfilen) läses i sitt senaste bygge: `mod bygg` skriver cachen direkt ur
modellen (samma innehåll, men egenskaperna och näten räknas bara för de delar som har ändrats), för STEP-filen eller
med `mod bygg --format analys` utan att skriva STEP-filen, och pekar ut den i `ut/trebodar.analys.json`. Har
modellens källor (modellen, modelleringsverktyget och beräkningarna som modellen läser) ändrats sedan dess bygger
`./ma` först om analysen (`mod bygg --format analys`, några sekunder), så att snitt och kontroller alltid gäller
den aktuella koden. `MA_BYGG=0` varnar bara.

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

**Urval** (överallt där delar väljs, även `--delar`, `--utom`, `--spok`, `--markera`, `--etiketter`, `--fokus`): kommaseparerat, skiftlägesokänsligt. `#12` eller `#12-20` = id, text med `*` eller `?` = glob mot hela delens namn eller en grupp i sökvägen (`V*-K` väljer källarväggarnas kärnor), med `/` mot sökvägen (hakparenteser är bokstavliga, som i `K Pillar [13]`), annars delsträng i sökvägen (`Källaren` väljer allt under Källaren).

### 3D-bilder (`vy`)

- `--fran`: `iso` (= `-x-y+z`), `iso-no`, `iso-so`, `iso-nv`, `ovan`, `under`, `fram` (`-y`), `bak`, `vanster`, `hoger`, valfri kombination `+x-y+z`, eller `az,el` i grader. Flera vyer med komma ger en bild med delbilder (`az,el`-par skiljs med `;`).
- `--klipp "z<14500"` behåller allt under z = 14 500 (`x>-3000` osv., godtyckligt plan `"o=x,y,z n=nx,ny,nz"`). Kan upprepas. Snittytorna får exakta lock i delens färg.
- `--delar`, `--utom`, `--spok` (genomskinligt), `--spok-ovriga URVAL` (allt annat genomskinligt), `--markera` (rött), `--etiketter`, `--fokus` (kameran ramar in urvalet), `--zoom`, `--rutnat` (koordinataxlar i mm), `--perspektiv`, `--storlek 1600x1200`, `--ut fil.png`.

### Snittritningar (`snitt`)

- Plan: `z=13865`, `x=-5000`, `y=6000` eller `"o=x,y,z n=nx,ny,nz"`. Axlarna är globala koordinater (för `x=` är vågrätt y och lodrätt z).
- Snittytorna beräknas exakt ur B-rep och fylls i delens färg; tabellen under bilden ger varje dels utbredning i snittet.
- `--bortom -3000` ritar även det som syns upp till 3 m bortom snittet (tecknet anger åt vilket håll man tittar), skuggat och ljusare med avståndet.
- `--origo u,v` mäter i ett lokalt system (t.ex. en ritnings origo i globala koordinater); `--omrade` och alla utskrivna koordinater blir relativa.
- `--omrade u0,u1,v0,v1` beskär, `--rutnat 500` rutnät var 500 mm, `--koordinater` skriver ut snittytornas hörn, `--json fil` sparar all snittgeometri, `--inga-etiketter`, `--ingen-bild` (bara tabellen och `--json`, som ritningarna i `verktyg/modellering` använder).

Bilder hamnar i `ut/` om inte `--ut` anges.

## Underlag till beräkningarna

Beräkningarna läser aldrig modellen. De har sina koordinater i sina egna källfiler (t.ex. `beräkningar/K-05/bild/geometri.json` och `beräkningar/K-03/geometri.json`), som uppdateras för hand. Kontrollerna här läser modellen och källfilerna och redovisar avvikelserna, men skriver ingenting. De läser den kodgenererade modellen i dess senaste bygge (se ovan). Där källfilerna har Onshape-modellens namn (K-03:s takbalkstyper och takstolsstavar) paras delarna på läget och namnen jämförs inte. Kör dem när modellen har ändrats:

```
./ma kontroll_geometri05.py   # K-05:s geometri.json: kontur, trapphål, väggar, rör, mark, fria kanter
./ma kontroll_k03.py          # K-03:s geometri.json och K-05:s stolplägen
./ma kontroll_r061.py         # geometri.json och R-06.1:s måttkedjor
./ma kontroll_r045.py         # R-04/R-05: öppningar, bröstningar, bottenplattans kontur, väggarnas höjd
./ma kontroll_laster.py       # lastgeometrin i F-01, K-01, K-05 och K-06
./ma kontroll_balkplattor.py  # balkplåtarnas skärfiler mot K-01
```

`./ma skript.py` kör skriptet i tjänsten (med modellen redan inläst); `.venv/bin/python skript.py` fungerar också.

`marknivaer.py` går åt andra hållet, för modellen: den skriver tabellen `MARKNIVA` för
`modeller/trebodar/hus/fasad/markniva.py` (marken vid fasaderna, panelens underkant) ur den byggda modellen. Kör den när
marken ändras och klistra in tabellen.

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
| `klient.py`, `tjanst.py` | ma-tjänsten: klienten som `./ma` kör (startar tjänsten vid behov) och tjänsten som kör kommandona |
| `modell.py` | Inläsning av STEP (namn, färg, placering), cache (även den som `mod bygg` skriver), modellens senaste bygge, urval |
| `geometri.py` | Exakta frågor: plansnitt, linjeprob, punkt, avstånd, krock, ytanalys |
| `vy.py` | 3D-rendering (pyvista/VTK, offscreen) |
| `ritning.py` | 2D-snittritningar (matplotlib) |
| `jamfor.py` | Jämförelse av en källfils data med modellens och redovisning av avvikelserna |
| `kontroll_geometri05.py` | Kontroll av K-05:s `bild/geometri.json` (kontur, trapphål, källarväggar och upplagslinjer, rör, platta på mark, fria kanter) mot modellen |
| `kontroll_k03.py` | Kontroll av K-03:s `geometri.json` (takbalkar, takfönster, takstolar, stolpar, huvudstolpen) och K-05:s stolplägen mot modellen |
| `kontroll_r061.py` | Kontroll av mellanbjälklagets geometri i K-05/R-06 (`beräkningar/K-05/bild/geometri.json`: kontur, trapphål, rör, källarväggar) och R-06.1:s måttkedjor mot modellen |
| `kontroll_r045.py` | Kontroll av källarstommen och bottenplattan i R-04 och R-05 (`beräkningar/R-05/kallare.py`: öppningarna i betongkärnan och bröstningarnas höjd, bottenplattans kontur och betong, kantbalk, balkar, plintar och L-element, bottenplattans höjder med cellplastens skikt och L-elementens fas, väggarnas höjd, rören, matkällarens golv, kärnornas anslutningar) mot modellen |
| `kontroll_laster.py` | Kontroll av lastgeometrin i F-01, K-01, K-05 och K-06 mot modellen (lastbredder, lastytor, höjder, fyllning) |
| `marknivaer.py` | Marken vid fasaderna (tabellen `MARKNIVA` i `hus/fasad/markniva.py`) ur den byggda modellen |
| `kontroll_balkplattor.py` | Kontroll av balkplåtarnas skärfiler (`modeller/balkplattor`, STEP och DXF) mot K-01: hålens lägen och diameter och plåtarnas mått |
| `granskning/` | Redovisade granskningar, t.ex. [`lastgeometri.md`](granskning/lastgeometri.md) |
