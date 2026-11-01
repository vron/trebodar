# Modellering – ramverk för den kodgenererade modellen

Ramverket bygger husets 3D-modell ur geometriskripten i [`modeller/trebodar`](../../modeller/trebodar/), exporterar
den och kontrollerar den. Geometriskripten beskriver bara geometri som data (recept: rätblock, prismor med hål,
booleska operationer, plan som kapar, placeringar) och material; de vet inget om exportformaten.

## Installation

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Kör sedan allt via `./mod` (använder `.venv`). Rendering kräver Blender (`/Applications/Blender.app`).

## Kommandon

| Kommando | Gör |
|---|---|
| `./mod trad [--djup N] [--del VÄG]` | Modellträdet med antal delar |
| `./mod bygg [--del VÄG] [--format step,glb,lista,index] [--delade]` | Bygger och exporterar till `modeller/trebodar/ut/` |
| `./mod kontroll [--del VÄG]` | Krockar, kontakter, glipor och delar utan kontakt |
| `./mod jamfor [--urval TEXT] [--ny TEXT]` | Jämför med Onshape-modellen och skriver en namntabell |
| `./mod rendera [VY …] [--bredd 400] [--sampel 32] [--blend]` | Bilder med Blender (Cycles), vyerna i `modeller/trebodar/vyer.py`; `--blend` sparar scenen |
| `./mod webb` | Webbvisaren (three.js) med modellen i `docs/` för GitHub Pages |
| `./mod typ` | Typkontroll (mypy) av ramverket och modellen |

`--del` väljer ett delträd med sökvägen under roten, t.ex. `--del "Hus/Stomme/Stomme prefab"`, som exporteras som en
egen modell (t.ex. för beställning). Utdata:

| Fil i `modeller/trebodar/ut/` | Innehåll |
|---|---|
| `trebodar.step` | STEP AP242 med sammanställningar, namn och färger (Onshape, `./ma` i modellanalys) |
| `trebodar.glb` | glTF med delade nät, material och metadata (Blender, webben) |
| `trebodar-materiallista.md`, `.csv` | Materiallista per del och per material: antal, kapmått, volym, massa |
| `trebodar-index.json` | Alla delar med sökväg, material, omslutande låda, volym, massa och tyngdpunkt |
| `trebodar-kontroll.md` | Kontrollens rapport |
| `trebodar-jamforelse.md`, `-namntabell.csv` | Jämförelsen med Onshape-modellen |
| `bilder/*.png` | Renderingarna |

## Hur det fungerar

- **Recept** (`form.py`): oföränderliga, hashbara värden: rätblock, prismor med hål, cylindrar, polyedrar (fria former
  av plana ytor, t.ex. kluven sten), booleska operationer, plan som kapar, speglingar. Likadana delar får samma recept
  och blir samma nät i GLB, samma rad i materiallistan och (med `--delade`) samma produkt i STEP.
- **Modellträd** (`modell.py`): `Del` (recept och material) och `Montage` (placerade instanser av delar och
  montage, i montagets eget koordinatsystem). `Placering` (`placering.py`) är en stel transform, exakt för vridningar
  med multiplar av 90°.
- **Kärna** (`karna.py`): OCCT via OCP. Varje unikt recept byggs en gång; B-rep, egenskaper och triangelnät sparas i
  `.cache/former.sqlite`. Saknade recept byggs i parallella processer (alla kärnor). Hela huset byggs från tom cache
  på några sekunder, därefter på bråkdelen av en sekund.
- **Export** (`export/`): STEP AP242 (OCCT XCAF; varje placerad del en egen produkt med instansens namn, eller
  delade produkter med `--delade`; utan 2D-kurvor på ytorna, som läsarna räknar fram), GLB (eget skrivprogram: hierarki, delade nät, PBR-material, UV i delens system så
  att träets fibrer följer delens x, metadata i `extras`), materiallista och index.
- **Kontroll** (`kontroll.py`): grovsållning med omslutande lådor, sedan exakt kontroll per par i parallella
  processer: gemensam volym (krock över 5 mm³), anliggande plana ytor (kontaktarea), minsta avstånd (glipor 0,01–2
  mm, utom mellan delar som båda ligger an mot en tredje). Resultaten per par cachas med nyckel från recepten och
  deras relativa placering. Avsiktliga överlapp mellan material (t.ex. spikplåt under utegips) och numeriska skärvor
  under 5 mm³ (mot krökta ytor) redovisas för sig. Modellen anger avsiktliga överlapp i `trebodar/kontrollregler.py`.
- **Jämförelse** (`jamfor.py`, `referens.py`, `prisma.py`): varje referensdel paras med den genererade del som har
  störst gemensam volym; identisk, städad (minst 98 % gemensamt), ändrad, ersatt eller borttagen.
- **Rendering** (`blender/rendera.py`, `blender/material.py`): Blender i bakgrunden läser GLB och bygger ett
  procedurellt material för varje material i modellen ur dess typ och parametrar (`material.json`, som `mod rendera`
  skriver), utan bildtexturer: virke med årsringar, limträ med lameller, sågade brädor (täckfärg, järnvitriol,
  obehandlat; varje bräda sågad ur en stock med årsringar, kvistar, sågad yta och strimmor, skruvar i rader), plåt i
  banor, kluven granit (mineralkorn, brottytor), betong, bruk, berg, mark, glas m.fl. Riktningarna anges i delens eget
  system; det som skiljer delar av samma material åt (stenar, plåtbanor) slumpas per objekt. Himmel och sol eller
  mulet, en kamera per vy, Cycles på GPU, färgåtergivning Khronos PBR Neutral.
- **Webben** (`webb/index.html`): three.js (fast version från CDN) med modellträd, snitt i x, y och z, vyer och
  information om den del man klickar på.

STEP-filen analyseras med [`verktyg/modellanalys`](../modellanalys/) (`./ma …`, som läser den genererade modellen
som standard).
