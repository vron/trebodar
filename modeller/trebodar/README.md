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

Varje läge skrivs på ett ställe. Det som handlingarna bestämmer (väggarnas, takbalkarnas, takstolarnas och
stolparnas lägen, öppningarna) står i `skelett.py` eller i montagets egen fil. Det som ska passa mot det (skikt,
isolering, fasad, läkt, syllar) räknas fram ur `skelett.py` eller ur stommens delar:
[`byggdelar/lagen.py`](byggdelar/lagen.py) ger delarnas lägen i huset ur montagen, t.ex. takstolarnas ytterbalkar
för ströläkten och delarna som de invändiga skikten går runt. Nya detaljer byggs på samma sätt, så att de följer med
när stommen ändras.

## Så ändrar du

| Ändring | Var |
|---|---|
| Takvinkel, väggarnas höjd, takets lyft, huskropparnas lägen | `skelett.py`; takbalkar, takstolar, takets skikt, isolering och innertak följer med |
| En väggs läge | `skelett.py` (`YTTERVAGGAR`, `INNERVAGGAR`) och väggens fil; fasadens hörn, isolering, insida och tak följer med |
| En regel, syll eller öppning i en vägg | väggens fil, t.ex. `hus/stomme/prefab/yttervaggar/v1so.py` (lägen i väggens u och z) |
| Ett fönster eller en dörr | `hus/fonster_och_dorrar/oppningar.py` (läge, modulmått och produkttyp) och väggens regelverk; fasad, isolering, insida och smyg följer med |
| Fönstrens och dörrarnas utförande | `byggdelar/fonster.py` (Elitfönsters profiler per produkttyp, karmen 20 mm mindre än modulen) och `hus/fonster_och_dorrar/fonster_och_dorrar.py` (läget i väggen, drevning, smyg och fönsterbänk) |
| En lätt innervägg eller innerdörr | `hus/invandigt/vaggar.py` (`LATTA`) och `oppningar.py` (`INNERDORRAR`); stomme, skikt och dörrar följer med |
| Badrummet | `hus/rum.py` (`BADRUM`): väggarnas skikt mot badrummet blir våtrumsskikt |
| Kaminen och skorstenen | `hus/kamin/kamin.py` (insatsens mått och läge, skorstenens läge); hålet i taket, isoleringen och innertaket skärs med `byggdelar/genomforing.py` |
| Trappan | `hus/trappa/trappa.py` (steg och vangstycken; läget följer trapphålet i `skelett.py`) |
| Takets uppbyggnad | `byggdelar/taklager.py` (skiktens tjocklek) och `hus/tak/tak.py` (ströläktens delning, uppehåll vid fönstren, plåtens banor och falsar) |
| Fasadens uppbyggnad eller panelens kulör | `hus/fasad/fasad.py` (`PANEL` per huskropp) och `material.py` (kulör, brädbredd, kvistar, skruvar) |
| Marken vid fasaden (panelens underkant) | `hus/fasad/fasad.py` (`MARKNIVA` per vägg, ur markmodellen; ändras när marknivåerna bestäms) |
| Fasadstenen | `hus/grund/fasadsten.py` (utbredning, mönstrets frö per vägg), AR-01:s `indata.toml` (stenens mått) och `byggdelar/sten.py` (den kluvna framsidan) |
| Nock- och dalbalkarna | K-01:s `indata.toml` och hålbilder (modellen läser dem) |
| Bottenplattan | `hus/grund/grund.py` (mått enligt K-06); plintarnas storlek läses ur K-06:s `resultat.json`, balkarna följer källarväggarna |
| Plattan på mark | `hus/grund/grund.py` (L-element, cellplast och makadam enligt AR-02); mellanbjälklagets betong slutar vid L-elementens rygg |
| Marken | `mark/mark.py`: schaktet runt plattan på mark och fyllnadshöjderna mot källarväggarna (`FYLLNAD`, K-06) |
| Ett nytt system, t.ex. el eller ventilation | en ny mapp under `hus/` med en fil som ger ett montage, och en rad i `hus/hus.py` |
| Ett nytt material eller utseende | `material.py`: densitet, CAD-färg, verklig färg och renderingens typ med parametrar |

Kör sedan `./mod kontroll` (krockar, glipor, lösa delar) och `./mod typ`.

## Material och rendering

Varje material (`material.py`) har densitet, materiallistans enhet och två utseenden. CAD-färgen (`cad`) används i
STEP, Onshape och webbvisaren och är vald så att olika slags delar skiljer sig åt, i stil med ritningarna: stommens
virke gulbrunt, läkt ljusgul (eget material, `C24_LAKT`), limträ bärnsten, isolering rosa och laxröd, cellplast
ljusblå, gips vit och utegips grågrön, ångbromsen blå, betong gråbeige, stål blågrått, mark grön. Det verkliga
utseendet (`farg` och renderingens typ med parametrar) används i renderingen, t.ex. `textur="bradpanel", rendering=rendering(riktning="y", tvars="x", bredd=145, kvistar=3.5,
behandling="jarnvitriol", ...)`. Renderingen bygger materialen procedurellt i Blender (inga bildtexturer); typerna och
deras parametrar står i [`verktyg/modellering/blender/material.py`](../../verktyg/modellering/blender/material.py).
Riktningarna gäller delens eget system: virke har x längs fibrerna; fasadens skivor x längs väggen och y uppåt (stående
brädor: `riktning="y"`); takets skikt x längs takfallet och z längs nocken (råspont `riktning="z"`).

- **Fasaden**: stående sågade granbrädor 22×145, den södra huskroppen (1) med Falu rödfärg (`PANEL_FALUROD`) och de
  andra två med järnvitriol (`PANEL_JARNVITRIOL`), valda per huskropp i `hus/fasad/fasad.py`. Panelen är en skiva per vägg; renderingen ritar
  brädorna, var och en sågad ur en stock (årsringar i flammor, kvistar som ådringen böjer runt, sågad yta, strimmor,
  färgskiftning per bräda) och skruvarna i spikläktens rader (kontrolleras mot `fasad.py`).
- **Taket**: plåten är banor med falsar i modellen; varje bana skiftar något i ton och glans och buktar mellan falsarna.
- **Fasadstenen**: stenarna är egna delar med kluven framsida (triangelnät, 30–50 mm tjock); renderingen ger granitens
  mineralkorn, små brottytor och skiftningen mellan stenarna.

Vyerna (`vyer.py`) har sol eller `molnigt` (jämnt ljus som på foton i mulet väder, bra för att bedöma material).
`./mod rendera --blend` sparar också scenen (`ut/trebodar.blend`) med materialen och en kamera per vy, för egna
justeringar i Blender; ändringar som ska vara kvar görs i `material.py`.

## Modellträdet

```
Trebodar
├── Mark                        berg, uppfyllnad, sovrumsavsats (ur Onshape-modellen), schaktet runt plattan på mark,
│                               fyllningen mot källarväggarna (K-06)
└── Hus
    ├── Grund                   bottenplatta (kantbalk, balkar, plintar, L-element), källarväggar V1–V21, rör P1–P19,
    │                           plattan på mark (L-element 500, AR-02), fasadsten per vägg
    ├── Mellanbjälklag          betongplatta 150 med trapphål, kantisolering
    ├── Stomme
    │   ├── Stomme prefab       trästommen ovanför bjälklaget, en beställning
    │   │   ├── Ytterväggar     Vägg 1NO … 3NV (regelverk 45×95)
    │   │   ├── Innerväggar     Vägg 1A–1D, 2A–2C
    │   │   ├── Takstolar       Takstol 1NO, 1SV, 2NO, 2C, 2SV, 3NO, 3SV
    │   │   ├── Stolpar         LN1_1, LN1_2, LN1_3, LD4_1
    │   │   └── Takbalkar       Takfall 1SO, 1NV, 2SO, 2NV, 3SO, 3NV (takbalkar, avväxlingar, kortlingar, upplagsreglar)
    │   └── Nock- och dalbalkar NB1, DB2, NB3, DB4, NB5 (K-01), en egen beställning
    ├── Tak                     per takfall: hårdboard, ströläkt, råspont, underlagspapp, takplåt i banor; TF1–TF3
    ├── Fasad                   per vägg: Utsida 1NO … = utegips, ströläkt, spikläkt, panel
    ├── Fönster och dörrar      Elitfönsters fönster och dörrar (även källarens), innerdörrar
    ├── Installationer          VVS (ur Onshape-modellen); el och ventilation läggs till här
    ├── Trappa                  brant trätrappa till källaren, i trapphålet
    ├── Kamin                   Rais 600 i väggen 2C, rökrör och isolerad skorsten genom taket
    ├── Isolering               takets träfiber och väggarnas mineralull
    └── Invändigt               innertak, ytterväggarnas insida (ångbroms, installationsskikt, OSB och gips),
                                innerväggarna: lätta väggar L1–L12 och skikten på alla innerväggar
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
- **Balkar** NB1, DB2, NB3, DB4, NB5 och plåtarna NB1-1-U osv. (K-01), reglarna ovanpå: nockreglarna NB1-NR osv.
  och dalreglarna DB2-DR1, DB2-DR2 osv. **Stolpar** LN1_1 … LD4_2 och hörnstolparna
  LA1–LA10 (K-03, K-05); reglar som bildar en stolpe heter som stolpen (LD2_1-1, LA5-2). **Takfönster** TF1–TF3.
  **Källarväggar** V1–V21, bröstningarna F1-B–F3-B, **rör** P1–P19 (P7 två rör) (K-05, K-06, R-05).
- **Fönster och dörrar** i ytterväggarna: väggen och F eller D med nummer längs väggen (1SO-F1, 2SV-D1);
  källarens fönster F1–F3 (R-05); innerdörrar ID1–ID6. Delarna: KARM, KARMALU (aluminiumbeklädnad), BOTTEN
  (bottenstyckets eller tröskelns aluminiumprofil), BAGE, BAGEALU, GLAS, BLAD (ytterdörren), TROSKEL; skjutdörrens
  delar FV, SV, SH, FH (fast och skjutbar, vänster och höger); i öppningen DREV, SMYG-V/H/O/U och BANK.
- **Delar**: `<montage>-<typ><nr>`, numrerade längs väggen eller takfallet. Väggar och takstolar: S syll, H
  hammarband, R regel, L liggande (överstycke, bröstning, topregel), D diagonal, U underram, X sned del under taket
  (takstolens ytterbalk), K kloss, P plåt. Takbalkar: T takbalk, A avväxling, K kortling, UR upplagsregel. Tak: HD
  hårdboard, SL ströläkt, RP råspont, UP underlagspapp, TP takplåt. Fasad: UG utegips, SR ströläkt, SP spikläkt, PA
  panel. Invändigt: AB ångbroms, IL installationsläkt, GI gips (i innertaket den inre skivan), GY innertakets yttre
  gipsskiva (möts i skarpa linjer i nockarna och under dalbalkarna). Isolering: TI tak, IS isolerstoppet vid takfoten, VI vägg. Takplåtens banor heter
  TP och numreras längs takfallet.
- **Innerväggarna**: de lätta väggarna L1, L2 … (stomme med S, R, H och L som regelväggarna) och skikten på varje
  innervägg och ytterväggarnas insida: OS OSB, GI gips, PW plywood, TS tätskikt, KA kakel. Innerdörrarna ID1–ID6 är
  skjutdörrar med BLAD och SKENA.
- **Trappan**: TR-V1, TR-V2 vangstyckena, TR-S01 … TR-S12 stegen nerifrån. **Kaminen**: KM-INSATS, KM-RAM, KM-GLAS,
  KM-OMFATTNING, KM-STOS, KM-ROR1–3, KM-SKORSTEN, KM-HUV, KM-KRAGE.
- **Bottenplattan**: BP-B betongen, BP-KB kantbalken, BP-IB balkarna under innerväggarna, BP-PL-P1 plinten under
  röret P1 osv., BP-L L-elementen, BP-CS cellplast S300 under balkar och plintar, BP-C1 och BP-C2 cellplasten S100
  (undre och övre lagret).
- **Plattan på mark**: PM-L L-elementen, PM-C1 och PM-C2 cellplasten (undre och övre lagret), PM-M makadamen, PM-F
  den dränerande fyllningen. **Marken**: MA-1, MA-2 makadamen mellan L-elementen och schaktets kant, FK-V2 osv.
  fyllningen mot källarväggen.
- **Fasadsten** (en grupp per vägg, efter väggen ovanför): `3NV-ST2-04` är sten 4 längs väggen i skift 2 (räknat
  nedifrån), `3NV-HS2` hörnstenen i skift 2 (i hörnet i väggens slut), FB fogbruk, FM armeringsbruk och fästmassa.

## Avsiktliga skillnader mot Onshape-modellen

`./mod jamfor` jämför delarna med Onshape-modellen och skriver namntabellen. Skillnaderna är dessa:

- **Fickor**: plåtarna (syll, hammarband) har inga 2 mm fickor för reglarna; reglarna är 2 400 i stället för
  2 404, och stolpar står på bjälklaget (z 0) i stället för 2 mm ner i det.
- **Nock- och dalbalkarna** enligt K-01: limträ GL30c 190×180, plåtar 190×10 med hålbilden ur K-01, distansreglar.
  Underkanten som HEA 200:s, så att stolparna är oförändrade; reglarna inuti profilen är borttagna. Ovanpå limmade
  reglar 45 som hårdboarden landar på: i nockarna en i mitten, fasad efter de två takplanen, och i dalarna en längs
  vardera kanten, med urtag för skruvhuvudena.
- **Takplanen 10 mm högre** (`skelett.TAKLYFT`), så att hårdboard och luftspalt går fritt över dalbalkarna, vars
  överkant ligger i takplanens skärning. Takbalkarnas underkant går 10 mm över takfotsväggens hammarband vid dess
  insida; vid nockbalkarna ligger takbalkarna 2,9 mm över balkens överkant. Takstolarnas sneda delar lyfts lika
  mycket. Onshape-modellens takbalkar i höger huskropp och vänstra kroppens dalsida (ÅYI) låg 1 mm för högt.
- **Takbalkarnas upplag** mot nock- och dalbalkarna: upplagsregel 45×45 och hak (K-03 figur 2); vid dalbalkarna sitter
  regeln så högt att haket får fullt säte.
- **Takfoten**: isolerstopp, regel 45 bultad på hammarbandet i varje fack, upp till takbalkarnas överkant och kapat efter
  takplanet; hårdboarden slutar på det, råsponten, pappen och plåten 20 mm utanför takbalkarnas ände.
- **Luftspalten** 34 mm: ströläkt 34×45 på hårdboard 3 mm, på varje takbalk och takstol och två mellan i varje fack,
  uppehåll 600 mm ovanför och nedanför takfönstren (U-03).
- **Enligt handlingarna** (K-03, K-05, K-06, R-04, R-05): strävor på båda sidor om LN1_3, LD4_1 GL30h 140×140,
  LD4_2 fyra reglar, ny stolpe LN1_1, toppklossar på takstolarna, kortlingar vid takfönstren, rören VKR 80×80×4 med
  plåtar, bottenplattan på en nivå med kantbalk, balkar, plintar och L-element, källarväggarnas kärnor ihopgjutna,
  plattan på mark med cellplast och fyllning, fasadstenen 15 mm ut, dubbel takbalk vid TF1, karmstolparna LD2_1 och
  LD2_2 i väggen 2B vid trapphålets långsidor.
- **Toppklossar**: en kloss per takstol, på gavelstolarnas insida (utsidan är fasad) och på mittstolen 2C:s nordöstra
  sida, inne i väggens tjocklek (på den sydvästra skulle den gå ut genom gipsen), så att balken vilar på 90 mm.
- **Innerväggar och innerdörrar** enligt planritning 201 rev 02 med modellens bärande väggar: lätta väggar 45×70 med
  OSB och gips (i badrummet plywood, gips, tätskikt och kakel), skikt på de bärande innerväggarna och skjutdörrar
  utanpå väggarna. 2B är sluten söder om trappan (skjutdörren ID2 vid trappan) och 2C vid väggens början (ID6 i den
  lätta väggen L12). I korridorens hörn i höger huskropp går ID3 90 mm längre söderut och ID5 slutar före korridorväggen,
  så att bladen går fria. Väggen mellan kontoret och köket går rakt genom huvudstolpen.
- **Fönster och dörrar** enligt Elitfönsters snittritningar (Original Alu 100 vridfönster, fast karm och altandörr
  helglasad; Skjutdörr Alu ASP4), i Onshape-modellens öppningar som modulmått: karmen 20 mm mindre, med
  aluminiumbeklädnaden i panelens utsida och panelen fram till karmen. Typerna: vridfönster 10×10 och 8×8 och i
  källaren 8×6 och 6×12, fasta fönster 6×21 (1NO, 3NO), 21×21,86 (1SV), 9×21 (3SV-F2) och 6×6 (1SO), fönsterdörrar
  9×21, 10×21 och 11×21 och skjutdörren 48×23,6 (2SV, fyra delar, de mittre öppnas åt sidorna). Invändigt
  smygbrädor och fönsterbänk av vitmålad furu, i badrummet kakel.
- **Huvudentrén 1SO-D1** (planritning 201): i Onshape-modellen fanns bara öppningen i regelverket. Dörren har
  fönsterdörrens karm och ett tätt dörrblad (produkten inte vald).
- **Plattan på mark** enligt AR-02: mellanbjälklaget i L-element 500 (ytterkanten i väggarnas ytterliv) med betongen
  fram till L-elementens rygg, 70 mm innanför K-05:s kontur vid de fria kanterna, cellplast 100 + 250, makadam 150 och
  dränerande fyllning i ett schakt i berget 100 mm utanför plattan. Marken mot källarväggarna upp till K-06:s
  fyllnadshöjder.
- **Trappan** till källaren är brant (45°, 11 steghöjder) och ryms i trapphålet, med fri höjd över hela trappan
  (K-05 räknar med en 3,0 m lång trappa).
- **Kaminen** enligt planritning 201 och Rais ritning 11-0000-6550: insatsen i öppningen i 2C mot allrummet, kroppen i
  en kåpa av kalciumsilikat (de lätta väggarna L7, L13 och L14) och väggarna runt trapphålet (L6, L7); underkanten
  450 över golvet, skorstenen 800 mm över nocken (antaget).
- **Fasadstenen** enligt AR-01: enskilda stenar i 400 mm skift med slumpade längder 600–1 200, fog 10, hörnstenar 400
  och 200 i varannat skift och kluven framsida 30–50 mm, med fogbruk och armeringsbruk; utbredningen som i
  Onshape-modellen.
- **Nytt**: tak- och fasadskikt, takplåten i banor med falsar, isolering, invändiga skikt, källarväggarna V1–V21
  enligt K-05, rören P1–P19.

## Inte modellerat ännu

Våtrummets golv (golvet på plan 1 är betongplattan, AR-02), badrummets inredning, trappans räcke och ledstång, fönsterbleck och droppbleck vid fönstren, takutsprång och vindskivor vid gavlarna, takfotsplåtar, hängrännor, el och
ventilation (se `modeller/modell-todo.md`). Marken, avloppet och golvvärmen läses ur Onshape-modellen
(`modeller/referens/delar/`). L-elementens avfasning (50 mm i ryggens överkant, som betongen fyller) är förenklad bort.
