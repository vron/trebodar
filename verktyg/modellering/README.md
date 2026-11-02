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
| `./mod avtryck spara\|jamfor [--del VÄG]` | Modellens fingeravtryck (varje dels låda, volym och tyngdpunkt): spara före en omstrukturering och jämför efter, så syns att geometrin är oförändrad (flyttade delar paras på namn, delar med samma geometri och nytt delnamn redovisas för sig; `ut/<modell>-avtryck.json`) |
| `./mod jamfor [--urval TEXT] [--ny TEXT]` | Jämför med Onshape-modellen och skriver en namntabell |
| `./mod rendera [VY …] [--serie ute\|inne\|alla] [--kvalitet skiss\|utkast\|normal\|slutlig] [--ljus M D HH:MM VÄDER] [--ev EV] [--bredd PX] [--ut MAPP] [--blend]` | Bilder med Blender (Cycles), vyerna i `modeller/trebodar/vyer.py` (VY: namn eller början av namn, t.ex. `I05`; serien `ute` är `VYER`, `inne` inomhusbilderna I01–I30). Kvaliteterna: skiss 640 px, utkast 1 280, normal 1 920 och slutlig 3 840 (4K). Dagsljuset är vyns om inte `--ljus` anges; exponeringen räknas fram ur en förhandsbild om inte `--ev` anges. `--blend` sparar scenen |
| `./mod ljus MÅNAD DAG [HH:MM] [VÄDER] [--steg MIN] [--diagram PNG]` | Dagsljuset på platsen (`modellering/dagsljus.py`): solens riktning och höjd, solens och himlens färg (CIE-färg och färgtemperatur) och belysning för en tidpunkt eller hela dagen; väder `sol`, `lätt mulet`, `mulet` (eller `sunny`, `slightlyovercast`, `overcast`); `--diagram` ritar solens bana under året med fasadernas riktningar |
| `./mod omgivning [--hamta]` | Omgivningen för renderingen ur öppna geodata (`modellering/geodata.py`): höjdmodell och marktäcke (berg, skog, vatten, åker, våtmark, vägar, trädgård, hav, byggnader) inom 2,3 km, i modellens koordinater via fasadens hörn i SWEREF 99 12 00 (AR-02); `--hamta` laddar ner det som saknas (OpenStreetMap via Overpass, Terrarium-höjdrutor). Allt i `lokalt/omgivning/` (versionshanteras inte) |
| `./mod materialprov MATERIAL [--param K=V …] [--nara] [--bredd PX] [--sampel N]` | Ett material ur modellen på tolv skåpluckor, en bänkskiva och brädor (Blender), för att bedöma det och att bitarna inte blir lika; `--nara` en lucka på nära håll, `--param` ändrar parametrar (t.ex. `yta=lack`) |
| `./mod kameraplan [--ut PNG]` | Ritningen över inomhusbildernas kameror (A3, 1:75) på plan 1 och i källaren ur STEP-filens snitt (kräver `./mod bygg` och `verktyg/modellanalys`); standard `renderingar/kameraplan.png` |
| `./mod webb` | Webbvisaren (three.js) med modellen i `docs/` för GitHub Pages |
| `./mod typ` | Typkontroll (mypy) av ramverket och modellen, och modellens struktur: inga importcykler, privata namn från andra moduler, importer i funktioner eller brott mot modellens lagerordning (`modellering/struktur.py`, `LAGER` i `trebodar/kontrollregler.py`) |
| `./mod onshape [--del VÄG] [--dokument NAMN] [--mapp NAMN] [--publik]` | Bygger STEP och laddar upp den till ett nytt dokument i en mapp i Onshape (standard `TrebodarAuto`) via Onshapes API, väntar på importen och redovisar flikar och delar |

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
| `bilder/*.png` | Renderingarna (`mod rendera`, `mod materialprov`) |
| `trebodar-rendering.glb`, `scen.json` | Modellen och scenens beskrivning (vyer, dagsljus, material, portaler, omgivning) till Blender |

## Hur det fungerar

- **Recept** (`form.py`): oföränderliga, hashbara värden: rätblock, prismor med hål, cylindrar, polyedrar (fria former
  av plana ytor, t.ex. kluven sten), booleska operationer, plan som kapar, speglingar. Likadana delar får samma recept
  och blir samma nät i GLB, samma rad i materiallistan och (med `--delade`) samma produkt i STEP.
- **Modellträd** (`modell.py`): `Del` (recept och material) och `Montage` (placerade instanser av delar och
  montage, i montagets eget koordinatsystem). Ett `Material` har två utseenden: CAD-färgen (`cad`) för STEP, GLB
  och webbvisaren och det verkliga utseendet (färg, grovhet, metall och ett procedurellt material) för renderingen. `Placering` (`placering.py`) är en stel transform, exakt för vridningar
  med multiplar av 90°.
- **Kärna** (`karna.py`): OCCT via OCP. Varje unikt recept byggs en gång; B-rep, egenskaper och triangelnät sparas i
  `.cache/former.sqlite`. Saknade recept byggs i parallella processer (alla kärnor). Hela huset byggs från tom cache
  på några sekunder, därefter på bråkdelen av en sekund.
- **Export** (`export/`): STEP AP242 (OCCT XCAF; varje placerad del en egen produkt med instansens namn, eller
  delade produkter med `--delade`; utan 2D-kurvor på ytorna, som läsarna räknar fram), GLB (eget skrivprogram: hierarki, delade nät, material i CAD-färgerna med det verkliga
  utseendet i `extras`, UV i delens system så att träets fibrer följer delens x, metadata i `extras`), materiallista och index.
- **Kontroll** (`kontroll.py`): grovsållning med omslutande lådor, sedan exakt kontroll per par i parallella
  processer: gemensam volym (krock över 5 mm³), anliggande plana ytor (kontaktarea), minsta avstånd (glipor 0,01–2
  mm, utom mellan delar som båda ligger an mot en tredje). Resultaten per par cachas med nyckel från recepten och
  deras relativa placering. Materialpar som inte ska prövas alls (modellens `IGNORERADE`, t.ex. armering i betong)
  sållas bort före den exakta kontrollen och räknas som anliggande. Avsiktliga överlapp mellan material (t.ex. spikplåt
  under utegips) och numeriska skärvor under 5 mm³ (mot krökta ytor) redovisas för sig. Modellen anger båda i
  `trebodar/kontrollregler.py`.
- **Jämförelse** (`jamfor.py`, `referens.py`, `prisma.py`): varje referensdel paras med den genererade del som har
  störst gemensam volym; identisk, städad (minst 98 % gemensamt), ändrad, ersatt eller borttagen.
- **Rendering** (`blender/rendera.py`, `blender/material.py`): Blender i bakgrunden läser GLB och bygger ett
  procedurellt material för varje material i modellen ur dess typ och parametrar (`scen.json`, som `mod rendera`
  skriver), utan bildtexturer (`tra.py`, `ytor.py`): virke ur en stock (varje bit och lamell sågad ur en egen stock
  med märgen på ett slumpat avstånd och håll, så att flader, halvkvarter och kvarter blandas och inga två bitar blir
  lika; årsringar som varierar år från år, sommarved eller porband för ringporigt trä som ask, kvistar ur märgen,
  kärnved; träslag och ytbehandling i `ARTER` och `YTOR`), sågade brädor (täckfärg, järnvitriol, obehandlat; skarvar,
  kvistar, strimmor och skruvar i rader), målad gips, betong (slipat golv uppåt, gjuten yta annars), kakel, plåt i
  banor, kluven granit, bruk, berg, mark och glas (genomskinligt med reflex på den första ytan; skugg- och diffusa
  strålar går rakt igenom). Det som skiljer delar av samma material åt slumpas per objekt.
- **Ljuset** (`modellering/dagsljus.py`, `blender/scen.py`): solens läge (NOAA) för platsen (`skelett.PLATS`) och
  tidpunkten, och ett spektralt dagsljus: solens spektrum genom atmosfären (Rayleigh, aerosol efter Ångström, ozon,
  vattenånga) och den diffusa himlen, molnighet efter Kasten–Czeplak och färgerna som CIE 1931 → linjär Rec.709.
  `dagsljus(månad, dag, klocka, väder)` ger solens riktning, färg och belysning och himlens färg och belysning. I
  Blender blir solen en sollampa med belysningen (lux / 683) och solskivans storlek efter vädret, och himlen skalas så
  att dess belysning på en horisontell yta och dess färg blir dagsljusets (mäts med en liten panoramarendering);
  mulet är en CIE-himmel. Ljusportaler i fönster, glasdörrar och takfönster i inomhusbilderna. Exponeringen (EV100)
  räknas fram ur en snabb förhandsbild; inne också vitbalansen, som ögats anpassning till rummets ljus (medelfärgen
  utan fönstren blir nästan neutral), ute efter dagsljusets färgtemperatur (solens och himlens, med en del kvar av
  kvällssolens värme). Cycles på GPU med brusreducering (OIDN),
  färgåtergivning Khronos PBR Neutral.
- **Omgivningen** (`modellering/geodata.py`, `blender/omgivning.py`): marken från modellens terräng ut till
  höjdmodellen (2,3 km), havet, grannhusen (valmade tak i slumpade färger) och träd (tall, gran, björk, en) efter
  marktäcket, så att fönstren och utsikterna visar skärgården runt tomten.
- **Kameror** (`modeller/trebodar/vyer.py`): kameran hålls vågrät med objektivförskjutning, så att lodräta linjer
  blir lodräta. Inomhusbilderna I01–I30 heter `<nummer>-<rum>-<vy>-<objektiv>` med objektiven `öga` (40 mm i
  ögonhöjd 1,60 m: bildvinkeln och perspektivet som när man står i rummet) och `vid` (20 mm på 1,45 m); se
  [`renderingar/`](../../renderingar/).
- **Webben** (`webb/index.html`): three.js (fast version från CDN) med modellträd (med sökning), vyer, delarnas kanter
  och snitt i x, y och z. Materialen listas med sina CAD-färger och kan döljas var för sig (t.ex. isolering och gips
  för att se stommen); en ruta växlar till de verkliga färgerna. Där ett snitt skär en del räknas tvärsnittet ut ur
  nätet och ritas i delens färg med svart kontur, som i en sektionsritning. Klick visar delens namn, sökväg och
  material. Navigeringen som i CAD-program: hjulet för kameran mot punkten under pekaren (ett steg är en andel av
  avståndet dit, och rotationscentrum följer med, så att man kommer hur nära som helst och genom väggar), vridning och
  panorering sker kring djupet för punkten där man tar tag, dubbelklick sätter rotationscentrum och piltangenterna och
  PgUp/PgDn går genom huset. Högerklick på en del (delen och
  grupperna den ingår i), en grupp i trädet eller ett material ger en meny: visa bara, tona ner resten (90 %
  genomskinligt), dölj, zooma, visa i trädet och visa allt; Esc avslutar. Fokus står i adressen (`#bara=<sökväg>`,
  `#tona=<sökväg>`, `#bara=material:<namn>`), så att en vy kan delas med en länk. Mätverktygen uppe till höger mäter
  en rak kant (K), avståndet mellan två punkter (A) och det vinkelräta avståndet mellan två parallella kanter (P),
  också på snittets konturer, och visar den senaste mätningen med Δx, Δy och Δz i en ruta under knapparna; pekaren snäpper till hörn, kanters mitt, kanter och ytor, och
  kanter som delas upp i nätet räknas som en.

`mod onshape` läser API-nycklarna ur `lokalt/onshape.json` i repot (versionshanteras inte; `access_key`,
`secret_key` och eventuellt `mapp`) eller ur miljövariablerna `ONSHAPE_ACCESS_KEY` och `ONSHAPE_SECRET_KEY`. Ett
gratiskonto i Onshape kan bara skapa publika dokument; då krävs `--publik`. Onshape behåller högst 100
sammanställningar per import och slår ihop de djupaste nivåerna i större modeller (hela huset har drygt 300); ladda
upp delträd med `--del` (t.ex. `"Hus/Stomme/Stomme prefab"`) för att få hela strukturen.

STEP-filen analyseras med [`verktyg/modellanalys`](../modellanalys/) (`./ma …`, som läser den genererade modellen
som standard).
