# Modellering – ramverk för den kodgenererade modellen

Ramverket bygger husets 3D-modell ur geometriskripten i [`modeller/trebodar`](../../modeller/trebodar/) och exporterar
den. Geometriskripten beskriver bara geometri som data (recept: rätblock, prismor med hål, booleska operationer,
plan som kapar, placeringar) och vet inget om exportformaten.

## Installation

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Kör sedan allt via `./mod` (använder `.venv`).

## Kommandon

| Kommando | Gör |
|---|---|
| `./mod trad [--djup N] [--del VÄG]` | Modellträdet med antal delar |
| `./mod bygg [--del VÄG] [--format step,glb,lista,index] [--delade]` | Bygger och exporterar till `modeller/trebodar/ut/` |
| `./mod kontroll [--del VÄG]` | Krockar (gemensam volym), kontakter (anliggande ytor), glipor 0,01–2 mm och delar utan kontakt |
| `./mod jamfor [--urval TEXT] [--ny TEXT]` | Jämför med referensmodellen (Onshape) och skriver en namntabell |

`--del` väljer ett delträd med sökvägen under roten, t.ex. `--del "Hus/Stomme/Stomme prefab"` (exporteras som en egen
modell, t.ex. för beställning).

## Hur det fungerar

- **Recept** (`form.py`): oföränderliga, hashbara värden. Likadana delar får samma recept och blir samma produkt i STEP
  och samma nät i GLB.
- **Modellträd** (`modell.py`): `Del` (recept + material) och `Montage` (placerade instanser av delar och montage, i
  montagets eget koordinatsystem). `Placering` (`placering.py`) är en stel transform, exakt för 90°-vridningar.
- **Kärna** (`karna.py`): OCCT via OCP. Varje unikt recept byggs en gång; resultatet (B-rep, egenskaper och
  triangelnät) sparas i `.cache/former.sqlite`. Saknade recept byggs i parallella processer (alla kärnor).
- **Export** (`export/`): STEP AP242 med sammanställningar, namn och färger; GLB med delade nät, PBR-material och
  metadata; materiallista (CSV och Markdown); index över alla delar (JSON).
- **Kontroller** (`kontroll.py`): grovsållning med omslutande lådor, sedan exakt kontroll per par i parallella
  processer. Resultaten per par cachas (nyckel: recepten och deras relativa placering).
- **Jämförelse** (`jamfor.py`): varje referensdel paras med den genererade del som har störst gemensam volym.

STEP-filen kan analyseras med [`verktyg/modellanalys`](../modellanalys/) (`./ma ... --fil ../../modeller/trebodar/ut/trebodar.step`).
