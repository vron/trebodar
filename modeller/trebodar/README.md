# Trebodar – kodgenererad modell

Husets 3D-modell som kod. Den här modellen är husets källmodell; Onshape-exporten som den byggdes efter finns kvar
som fryst referens i [`modeller/referens`](../referens/). Bygg, exportera och kontrollera med ramverket i
[`verktyg/modellering`](../../verktyg/modellering/):

```
cd verktyg/modellering
./mod bygg          # STEP, GLB, materiallista och index i modeller/trebodar/ut/
./mod kontroll      # krockar, kontakter, glipor och delar utan kontakt
./mod rendera       # bilder med Blender (Cycles), vyerna i vyer.py
./mod webb          # webbvisaren i docs/ (GitHub Pages)
```

Koordinater som i K-05 (mm): x och y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant.

## Hur koden är ordnad

Mappstrukturen följer modellträdet: varje montage är en mapp med en fil med samma namn som sätter ihop montaget
(`hus/stomme/stomme.py`), och delmontagen ligger i undermappar eller egna filer bredvid. Geometriskripten beskriver
bara geometri (rätblock, prismor med hål, plan som kapar, placeringar) och material; exportformaten sköter ramverket.

| Fil | Innehåll |
|---|---|
| [`skelett.py`](skelett.py) | Gemensam geometri: huskroppar, väggarnas lägen och system, takfallen, nock- och dalbalkarna, nivåer |
| [`material.py`](material.py) | Material: densitet, färg, rendering och materiallistans enhet |
| [`byggdelar/`](byggdelar/) | Regelväggar och plana stommar, takstolar, takbalkar, takets skikt, virke och skivor, referensdelar |
| [`vyer.py`](vyer.py) | Kameror för rendering och webbvisaren |
| [`kontrollregler.py`](kontrollregler.py) | Avsiktliga överlapp som kontrollen godtar, med motivering |
| [`referens.py`](referens.py) | Referensmodellen och transformen till K-05 (för `mod jamfor`) |

Varje del definieras i ett eget system och placeras av sitt montage. Väggarna har systemet u längs väggen, w genom
väggen (w = 0 stommens utsida) och z uppåt; deras delar skrivs som regel(u), syll(u0, u1), hammarband(u0, u1),
liggande(u0, u1, z) och profil([...]). Takets delar räknas fram ur takfallen i `skelett.py`: ändras takplanet,
väggarnas höjd eller balkarnas lägen följer takbalkar, takstolar, takets skikt, isolering och innertak med.

## Så ändrar du

| Ändring | Var |
|---|---|
| Takvinkel, väggarnas höjd, takets lyft, huskropparnas lägen | `skelett.py`; takbalkar, takstolar, takets skikt, isolering och innertak följer med |
| En regel, syll eller öppning i en vägg | väggens fil, t.ex. `hus/stomme/prefab/yttervaggar/v1so.py` (lägen i väggens u och z) |
| Ett fönster eller en dörr | `hus/fonster_och_dorrar/oppningar.py` och väggens regelverk; fasad, isolering och insida följer med |
| Takets uppbyggnad | `byggdelar/taklager.py` (skiktens tjocklek) och `hus/tak/tak.py` (ströläktens delning, uppehåll vid fönstren) |
| Fasadens uppbyggnad eller panelens kulör | `hus/fasad/fasad.py` (`PANEL` per huskropp) och `material.py` |
| Nock- och dalbalkarna | K-01:s `indata.toml` och hålbilder (modellen läser dem) |
| Ett nytt system, t.ex. el eller ventilation | en ny mapp under `hus/` med en fil som ger ett montage, och en rad i `hus/hus.py` |
| Ett nytt material eller utseende | `material.py`: densitet, färg och renderingens typ med parametrar |

Kör sedan `./mod kontroll` (krockar, glipor, lösa delar) och `./mod typ`.

## Material och rendering

Varje material (`material.py`) har densitet och färg (STEP, Onshape, materiallistan) och för renderingen en typ med
parametrar, t.ex. `textur="bradpanel", rendering=rendering(riktning="y", tvars="x", bredd=145, fog=4,
behandling="tackfarg")`. Renderingen bygger materialen procedurellt i Blender (inga bildtexturer); typerna och deras
parametrar står i [`verktyg/modellering/blender/material.py`](../../verktyg/modellering/blender/material.py).
Riktningarna gäller delens eget system: virke har x längs fibrerna; fasadens skivor x längs väggen och y uppåt (stående
brädor: `riktning="y"`); takets skikt x längs takfallet och z längs nocken (råspont `riktning="z"`, falsad plåt
`riktning="x"`).

Fasaden har stående sågade granbrädor 22 mm med Falu rödfärg (`PANEL_FALUROD`) eller järnvitriol
(`PANEL_JARNVITRIOL`), valda per huskropp i `hus/fasad/fasad.py`. `./mod rendera --blend` sparar också scenen
(`ut/trebodar.blend`) med materialen och en kamera per vy, för egna justeringar i Blender.

## Modellträdet

```
Trebodar
├── Mark                        berg, uppfyllnad, sovrumsavsats (ur Onshape-modellen)
└── Hus
    ├── Grund                   bottenplatta, källarväggar V1–V21, rör P1–P19, plattan på mark, fasadsten
    ├── Mellanbjälklag          betongplatta 150 med trapphål, kantisolering
    ├── Stomme
    │   ├── Stomme prefab       trästommen ovanför bjälklaget, en beställning
    │   │   ├── Ytterväggar     Vägg 1NO … 3NV (regelverk 45×95)
    │   │   ├── Innerväggar     Vägg 1A–1D, 2A–2C, syllar för lätta väggar
    │   │   ├── Takstolar       Takstol 1NO, 1SV, 2NO, 2C, 2SV, 3NO, 3SV
    │   │   ├── Stolpar         LN1_1, LN1_2, LN1_3, LD4_1
    │   │   └── Takbalkar       Takfall 1SO, 1NV, 2SO, 2NV, 3SO, 3NV (takbalkar, avväxlingar, kortlingar, upplagsreglar)
    │   └── Nock- och dalbalkar NB1, DB2, NB3, DB4, NB5 (K-01), en egen beställning
    ├── Tak                     per takfall: hårdboard, ströläkt, råspont, underlagspapp, takplåt; takfönster TF1–TF3
    ├── Fasad                   per vägg: Utsida 1NO … = utegips, ströläkt, spikläkt, panel
    ├── Fönster och dörrar      ytterväggarnas fönster och dörrar, innerdörrar
    ├── Installationer          VVS (ur Onshape-modellen); el och ventilation läggs till här
    ├── Isolering               takets träfiber och väggarnas mineralull
    └── Invändigt               innertak och ytterväggarnas insida: ångbroms, installationsskikt, gips
```

`./mod bygg --del "Hus/Stomme/Stomme prefab"` exporterar prefabstommen som en egen modell (och på samma sätt
nock- och dalbalkarna).

## Namn

Namnen i modellen är kanoniska och följer handlingarnas beteckningar. Onshape-modellens namn finns bara i
[`modeller/referens/namntabell.csv`](../referens/namntabell.csv).

- **Huskroppar** 1 (vänster), 2 (mittre), 3 (höger), som V, M och H i K-05.
- **Ytterväggar**: kropp och väderstreck: 1NO, 1SO, 1SV, 1NV, 2NO, 2SO, 2NV, 2SV, 3NO, 3NV, 3SV, 3SO (gavlarna mot
  NO och SV). **Bärande innerväggar**: kropp och bokstav i växande y: 1A–1D och 2A–2C (Onshape: L1 B2, L1L, L1 B,
  L1V, L2 NO, L23, L2M). **Takstolar** heter som väggen de står på (K-03:s Stol L2M är takstol 2C). **Takfall** heter
  som takfotsväggen.
- **Balkar** NB1, DB2, NB3, DB4, NB5 och plåtarna NB1-1-U osv. (K-01). **Stolpar** LN1_1 … LD4_2 och hörnstolparna
  LA1–LA10 (K-03, K-05); reglar som bildar en stolpe heter som stolpen (LD2_1-1, LA5-2). **Takfönster** TF1–TF3.
  **Källarväggar** V1–V21, bröstningarna F1-B–F3-B, **rör** P1–P19 (P7 två rör) (K-05, K-06, R-05).
- **Fönster och dörrar** i ytterväggarna: väggen och F eller D med nummer längs väggen (1SO-F1, 2SV-D1);
  innerdörrar ID1–ID6.
- **Delar**: `<montage>-<typ><nr>`, numrerade längs väggen eller takfallet. Väggar och takstolar: S syll, H
  hammarband, R regel, L liggande (överstycke, bröstning, topregel), D diagonal, U underram, X sned del under taket
  (takstolens ytterbalk), K kloss, P plåt. Takbalkar: T takbalk, A avväxling, K kortling, UR upplagsregel. Tak: HD
  hårdboard, SL ströläkt, RP råspont, UP underlagspapp, TP takplåt. Fasad: UG utegips, SR ströläkt, SP spikläkt, PA
  panel. Invändigt: AB ångbroms, IL installationsläkt, GI gips. Isolering: TI tak, VI vägg.

## Avsiktliga skillnader mot Onshape-modellen

`./mod jamfor` jämför delarna med Onshape-modellen och skriver namntabellen. Skillnaderna är dessa:

- **Fickor**: plåtarna (syll, hammarband) har inga 2 mm fickor för reglarna; reglarna är 2 400 i stället för
  2 404, och stolpar står på bjälklaget (z 0) i stället för 2 mm ner i det.
- **Nock- och dalbalkarna** enligt K-01: limträ GL30c 190×180, plåtar 190×10 med hålbilden ur K-01, distansreglar.
  Underkanten som HEA 200:s, så att stolparna är oförändrade; reglarna inuti profilen är borttagna.
- **Takplanen 10 mm högre** (`skelett.TAKLYFT`), så att hårdboard och luftspalt går fritt över dalbalkarna, vars
  överkant ligger i takplanens skärning. Takbalkarnas underkant går 10 mm över takfotsväggens hammarband vid dess
  insida; vid nockbalkarna ligger takbalkarna 2,9 mm över balkens överkant. Takstolarnas sneda delar lyfts lika
  mycket. Onshape-modellens takbalkar i höger huskropp och vänstra kroppens dalsida (ÅYI) låg 1 mm för högt.
- **Takbalkarnas upplag** mot nock- och dalbalkarna: upplagsregel 45×45 och hak (K-03 figur 2); vid dalbalkarna sitter
  regeln så högt att haket får fullt säte.
- **Luftspalten** 34 mm: ströläkt 34×45 på hårdboard 3 mm, på varje takbalk och takstol och två mellan i varje fack,
  uppehåll 600 mm ovanför och nedanför takfönstren (U-03).
- **Modell-todo** 1–13, 18 och 19: strävor på båda sidor om LN1_3, LD4_1 GL30h 140×140, LD4_2 fyra reglar, ny
  stolpe LN1_1, toppklossar på takstolarna, kortlingar vid takfönstren, rören VKR 80×80×4 med plåtar, bottenplattan
  på en nivå, källarväggarnas kärnor ihopgjutna, plattan på mark med cellplast och fyllning, fasadstenen 15 mm ut,
  dubbel takbalk vid TF1, karmstolparna LD2_1 och LD2_2 i väggen 2B vid trapphålets långsidor (K-05).
- **Toppklossar på gavelstolarna**: en kloss på insidan (utsidan är fasad), så att balken vilar på 90 mm.
- **Innerdörrar**: ID2 börjar efter karmstolpen LD2_2, ID5 slutar före den nya stolpen LN1_1 och ID6 börjar vid
  stolpen LD4_1.
- **Nytt**: tak- och fasadskikt, isolering, invändiga skikt, källarväggarna V1–V21 enligt K-05, rören P1–P19.

## Inte modellerat ännu

Lätta innerväggar (bara syllarna finns), golv, vindskivor, takfotsplåtar, hängrännor, el och ventilation. Marken,
avloppet och golvvärmen läses ur Onshape-modellen (`modeller/referens/delar/`). Bottenplattans balkar, plintar och
L-element (modell-todo 14) och marken mot källarväggarna (modell-todo 17) är förenklade bort.
