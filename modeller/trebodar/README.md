# Trebodar – kodgenererad modell

Husets 3D-modell som kod. Den här modellen är husets källmodell. Den byggdes först efter husets Onshape-modell, som
finns kvar i git-historiken (`git log -- modeller/referens`) och i Onshape; där kommentarerna säger "som i
Onshape-modellen" anger de var ett mått kommer ifrån, och skillnaderna står i [Avsiktliga skillnader mot
Onshape-modellen](#avsiktliga-skillnader-mot-onshape-modellen). Bygg, exportera och kontrollera med ramverket i
[`verktyg/modellering`](../../verktyg/modellering/):

```
cd verktyg/modellering
./mod bygg          # STEP, GLB, materiallista och index i modeller/trebodar/ut/
./mod kontroll      # krockar, kontakter, glipor och delar utan kontakt
./mod rendera       # bilder med Blender (Cycles), vyerna i vyer.py (inomhusbilderna: renderingar/rendera.sh)
./mod webb          # webbvisaren i docs/modell/ (GitHub Pages)
```

Koordinater som i K-05 (mm): x och y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant.
Väderstrecken i texterna följer planen: norr = lågt y, söder = högt y, öster = högt x och väster = lågt x (planens
väderstreck; verklig norr är (0,751; −0,660), `vyer.sweref_passning`). Fasadernas väderstreck (1NO, 2SO …) är ett
eget system, och rummens, zonernas och stråkens koder (KS, KSV, ÖN, HN, stråket N …) är bara koder.

## Hur koden är ordnad

Mappstrukturen följer modellträdet: varje montage är en mapp med en fil med samma namn som sätter ihop montaget
(`hus/stomme/stomme.py`), och delmontagen ligger i undermappar eller egna filer bredvid. Geometriskripten beskriver
bara geometri (rätblock, prismor med hål, plan som kapar, placeringar) och material; exportformaten sköter ramverket.

| Fil | Innehåll |
|---|---|
| [`skelett.py`](skelett.py) | Gemensam geometri: huskroppar, väggarnas lägen och system, takfallen, nock- och dalbalkarna, nivåer |
| [`material.py`](material.py) | Material: densitet, färg, rendering och materiallistans enhet |
| [`byggdelar/`](byggdelar/) | Regelväggar och plana stommar, takstolar, takbalkar, takets skikt, virke och skivor |
| [`vyer.py`](vyer.py) | Kameror och dagsljus för rendering och webbvisaren, inomhusbilderna I01–I30, bildtexterna på webbplatsen, ljusportalerna och omgivningen |
| [`kontrollregler.py`](kontrollregler.py) | Avsiktliga överlapp som kontrollen godtar, med motivering |

Varje del definieras i ett eget system och placeras av sitt montage. Väggarna har systemet u längs väggen, w genom
väggen (w = 0 stommens utsida) och z uppåt; deras delar skrivs som regel(u), syll(u0, u1), hammarband(u0, u1),
liggande(u0, u1, z) och profil([...]). Takets delar räknas fram ur takfallen i `skelett.py`: ändras takplanet,
väggarnas höjd eller balkarnas lägen följer takbalkar, takstolar, takets skikt, isolering och innertak med.

Stommen byggs med regler. Väggarnas regelverk följer
[`hus/stomme/prefab/regelstomme.py`](hus/stomme/prefab/regelstomme.py): syll och hammarband med skarvar, karmreglar,
överstycken, bröstningar och kortlingar ur öppningarna i `oppningar.py`, reglar c/c 600 från ett raster, hörnstolpar,
stolpar, dalbalkarnas upplag på gavlarna och lutande hammarband under takfallen. Takstolarna följer
[`byggdelar/takstol.py`](byggdelar/takstol.py): ytterbalkar, diagonaler, underram, ståndare och säten ur takfallen,
nockbalken, dalbalkarna och väggens överkant. Varje vägg och takstol har en egen fil med sina egna data (rastrets
början, fria reglar, skarvar, öppningarnas utförande, stolpar, underramens höjd) och är ett eget montage.

Varje läge skrivs på ett ställe. Det som handlingarna bestämmer (väggarnas, takbalkarnas, takstolarnas och
stolparnas lägen, öppningarna) står i `skelett.py` eller i montagets egen fil. Det som ska passa mot det (skikt,
isolering, fasad, läkt, syllar) räknas fram ur `skelett.py` eller ur stommens delar:
[`hus/stomme/lagen.py`](hus/stomme/lagen.py) ger delarnas lägen i huset ur montagen, per element (`vagg(kod)`,
`stolpe(kod)`, `takstol(kod)`, med delens typ), t.ex. takstolarnas ytterbalkar för ströläkten och delarna som de
invändiga skikten går runt. Ingen modul tolkar gruppernas eller delarnas namn själv. Nya detaljer byggs på samma sätt, så att de följer med
när stommen ändras.

### Beroenden

Beroendena går i en riktning: `skelett.py` och `material.py` beror inte på något i paketet, `byggdelar/` (allmänna
byggsätt: regelväggar, takstolar, takets skikt, virke, fönsterprodukter) bara på dem och på varandra, och systemen
under `hus/` och `mark/` på `byggdelar/` och på varandras gemensamma underlag; huset beror inte på marken. `hus/hus.py` sätter ihop systemen och gör det som går
genom flera av dem (kaminens hål genom tak, isolering och innertak).

Det som flera system behöver står i en egen modul, så att systemen inte beror på varandras inre:

| Underlag | Innehåll | Används av |
|---|---|---|
| [`hus/stomme/lagen.py`](hus/stomme/lagen.py) | Stommens delar och lägen ur montagen, takets stomme som tvärsnitt, takets fack mellan takbalkarna | tak, fasad, isolering, invändigt, mark |
| [`hus/tak/takytor.py`](hus/tak/takytor.py) | Takfallens regioner, takfotens kant, takytan och dalarnas ändar | tak, takkanter, dalar, stommens balkar, fasad, invändigt |
| [`hus/fonster_och_dorrar/oppningar.py`](hus/fonster_och_dorrar/oppningar.py) | Öppningarna i ytterväggarna och innerdörrarna | fönster och dörrar, fasad, isolering, invändigt, mark |
| [`hus/rum.py`](hus/rum.py) | Badrummet och kaminkåpan | invändigt, kamin |
| [`hus/badrum.py`](hus/badrum.py) | Badrummets planering: väggarnas färdiga ytor, inredningens lägen och golvets fall mot golvbrunnen | inredning, invändigt (golvet), installationer (vatten, avlopp, el) |
| [`hus/fasad/markniva.py`](hus/fasad/markniva.py) | Marken vid fasaderna (genererad tabell) | fasad, takkanter, dalar |
| [`hus/invandigt/skikt.py`](hus/invandigt/skikt.py) | De invändiga skiktens uppbyggnad och innertakets underkant | invändigt, fönster och dörrar, kamin |
| [`hus/grund/kallarvaggar.py`](hus/grund/kallarvaggar.py) | Källarväggarna i plan, deras öppningar och kontur | grund, öppningar, fasad, invändigt, mark |

Reglerna kontrolleras med `./mod typ`: inga importcykler, inga privata namn (`_namn`) från en annan modul, inga
importer av paketets moduler inne i funktioner och lagerordningen i `kontrollregler.py` (`LAGER`). Behöver ett annat system en hjälpfunktion görs den publik med en
beskrivning, eller flyttas till underlaget den hör till.

## Så ändrar du

| Ändring | Var |
|---|---|
| Takvinkel, väggarnas höjd, takets lyft, huskropparnas lägen | `skelett.py`; takbalkar, takstolar, takets skikt, isolering och innertak följer med |
| En väggs läge | `skelett.py` (`YTTERVAGGAR`, `INNERVAGGAR`) och väggens fil; fasadens hörn, isolering, insida och tak följer med |
| Väggens regelverk | väggens fil, t.ex. `hus/stomme/prefab/yttervaggar/v1so.py`: rastrets början, fria reglar, skarvar, öppningarnas utförande (`Karm`: dubbla karmreglar, överstycke, kortlingar), hörnstolpar, stolpar och dalbalkarnas upplag; reglerna i `regelstomme.py` |
| Ett fönster eller en dörr | `hus/fonster_och_dorrar/oppningar.py` (läge, regelöppningens mått och produkttyp); regelverket (karmreglar, överstycke, bröstning, kortlingar), fasad, isolering, insida och smyg följer med |
| En takstol | stolens fil i `hus/stomme/prefab/takstolar/` (sätet, underramens höjd, ståndarnas lägen, spikreglar) och reglerna i `byggdelar/takstol.py` (delarna, säten, klossar och spikplåtar) |
| Takbalkarnas lägen och takfönstren | `hus/stomme/prefab/takbalkar/takbalkar.py` (`FALT`: följder c/c 600 per takfall; `TF1`–`TF3`); dubbla takbalkar och avväxlingar vid takfönstren följer med |
| En stolpe | fristående: `hus/stomme/prefab/stolpar/stolpar.py` (mitt som i K-03) och `ln1_3.py`; i en vägg: väggens fil (`regelstomme.stolpe`) |
| Fönstrens och dörrarnas utförande | `byggdelar/velfac.py` (fönstren och fönsterdörrarna, VELFAC 200 ENERGY: profilerna och produkterna), `byggdelar/ytterdorrar.py` (ytterdörrarna med panel) och `hus/fonster_och_dorrar/fonster_och_dorrar.py` (läget i väggen: indrag 20, fog 15, påföring, plåtar och fönsterbleck, fasaden 10 mm från karmen, smyg och fönsterbänk) |
| Smyglister: en bredare synlig träkant runt fönstren och dörrarna invändigt | `hus/fonster_och_dorrar/oppningar.py` (`SMYGLIST` i mm, 0 = bara smygen); skivorna slutar längre från karmen och listerna och fönsterbänkens öron följer med |
| En lätt innervägg eller innerdörr | `hus/invandigt/vaggar.py` (`LATTA`) och `oppningar.py` (`INNERDORRAR`); stomme, skikt och dörrar följer med |
| Köksbänken och ön | skåpen (stomme, lådor på Blum MOVENTO, fronter; varje skåp i sitt eget system för ritningar) i `hus/inredning/koksskap.py`, uppställningen (antal skåp, bänkens djup, ön, diskho, häll) i `hus/inredning/koksbank.py` |
| Kökets inbyggnad (kyl, frys, skafferi) | lägena, öppningarna och luckan i `hus/invandigt/lattvaggar.py` (`K_…`), stommen, skikten, förrådet och smygarna i `kokets_inbyggnad.py`; vitvarorna, skåpen, fronterna och skafferiet i `hus/inredning/kok.py` |
| En innervägg eller ett dörrhål i källaren | `hus/invandigt/kallarens_innervaggar.py` (`VAGGAR`, `DORRHAL`); reglarna, gipsen och urtagen vid rören följer med |
| Badrummet | `hus/rum.py` (`BADRUM`): väggarnas skikt mot badrummet blir våtrumsskikt och innertaket panel; `hus/badrum.py`: inredningens lägen (bänken, tvättstället, badkaret, WC:n, duschen, skåpet, spegeln, handdukstorken) och golvets fall; inredningen, golvet, tappvattnet, avloppet och elen följer med |
| Kaminen och skorstenen | `hus/kamin/kamin.py` (insatsens mått och läge, skorstenens läge); hålet i taket, isoleringen och innertaket skärs med `byggdelar/genomforing.py` |
| Trappan | `hus/trappa/trappa.py` (steg och vangstycken; läget följer trapphålet i `skelett.py`) |
| Takets uppbyggnad | `byggdelar/taklager.py` (skiktens tjocklek) och `hus/tak/tak.py` (ströläktens delning, uppehåll vid fönstren, plåtens banor och falsar) |
| Takfallens utbredning, takfoten och dalarnas ändar | `hus/tak/takytor.py` (`REGIONER`); taket, takkanterna, dalarna och innertaket följer med |
| Takkanterna och dalarna | `hus/tak/takkanter.py` (takfotsplåt, rännor, stuprör, vindskivor) och `hus/tak/dalar.py` (kilar, rändal, ändlådor) |
| De invändiga skikten | `hus/invandigt/skikt.py` (uppbyggnaden), `innertak.py`, `vagginsida.py` (ytterväggarnas insida och hörnen), `vaggar.py` (innerväggarna), `kallare.py` (källarväggarnas gips) och `kallarens_innervaggar.py` (källarens lätta väggar) |
| Fasadens uppbyggnad, panelens eller fönstrens kulör | `hus/fasad/fasad.py` (uppbyggnaden) och `material.py` (`PANEL` och `ALUMINIUM` per huskropp; kulör, brädbredd, kvistar, skruvar) |
| Marken vid fasaden (panelens underkant) | `hus/fasad/markniva.py` (`MARKNIVA` per vägg, ur den byggda modellen med `verktyg/modellanalys/marknivaer.py`; körs om när marken ändras) |
| Fasadstenen | `hus/grund/fasadsten.py` (utbredning, mönstrets frö per vägg), AR-01:s `indata.toml` (stenens mått) och `byggdelar/sten.py` (den kluvna framsidan) |
| Nock- och dalbalkarna | K-01:s `indata.toml` och hålbilder (modellen läser dem) |
| Stålbanden (stabiliseringen, K-04) | `hus/stomme/prefab/stalband/stalband.py`: väggarnas fält med kryss (`VAGGAR`, banden går till närmaste hela regel eller stolpe) och takfallens fält längs hela fallet (`FALT_TAK`, utom över takfönstren); bandet i `byggdelar/stalband.py`. Räkna om K-04 (`./bygg K-04`), som läser bärverket ur modellen (`hus/stomme/barverk.py`, `./mod barverk`) |
| Bottenplattan | `hus/grund/grund.py` (mått enligt K-06); plintarnas storlek läses ur K-06:s `resultat.json`, balkarna följer källarväggarna |
| Plattan på mark | `hus/grund/grund.py` (L-element, cellplast och makadam enligt AR-02); mellanbjälklagets betong slutar vid L-elementens rygg, vid de fria hörnen i ryggens urtag (`hornutkap`, samma regel som R-05:s `kallare.py`, R-06 detalj F) |
| Armeringen | ritningarna R-04, R-05 och R-06 (`beräkningar/R-0x/ritningar.py`, funktionerna som ritar järnen och räknar stålförteckningarna); `hus/armering/armering.py` läser dem och lägger järnen i höjdled |
| Marken | `mark/marken.json`: berget, uppfyllnaden och sovrumsavsatsen som data, ovansidans ytor med höjden i varje hörn (`mark/marken.py` gör kropparna; ändra en höjd i alla ytor som har hörnet); `mark/mark.py`: schaktet runt plattan på mark, återfyllningen där marken inte når fram (`ATERFYLLNING`), entréavsatsen och bänktrappan vid 2SO-D1 |
| Ett nytt system, t.ex. el eller ventilation | en ny mapp under `hus/` med en fil som ger ett montage, och en rad i `hus/hus.py` |
| Ett nytt material eller utseende | `material.py`: densitet, CAD-färg, verklig färg och renderingens typ med parametrar |
| En specialprodukt i inköpslistan (IN-01) | `produkt="KOD"` på delen eller montaget i geometriskriptet där det skapas (installationernas produkttyper: typens `produkt` i katalogen) och produkten med status i `beräkningar/IN-01/indata.toml`; `./mod kontroll` jämför koderna |

Kör sedan `./mod kontroll` (krockar, glipor, lösa delar) och `./mod typ`. Vid en omstrukturering som inte ska ändra
geometrin: `./mod avtryck spara` före och `./mod avtryck jamfor` efter.

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
  andra två med järnvitriol (`PANEL_JARNVITRIOL`), valda per huskropp i `material.py` (`PANEL`). Panelen är en skiva per vägg; renderingen ritar
  brädorna, var och en sågad ur en stock (årsringar i flammor, kvistar som ådringen böjer runt, sågad yta, strimmor,
  färgskiftning per bräda) och skruvarna i spikläktens rader (kontrolleras mot `fasad.py`).
- **Taket**: plåten är banor med falsar i modellen; varje bana skiftar något i ton och glans och buktar mellan falsarna.
- **Fasadstenen**: stenarna är egna delar med kluven framsida (triangelnät, 30–50 mm tjock); renderingen ger granitens
  mineralkorn, små brottytor och skiftningen mellan stenarna.
- **Fönstren och dörrarna**: aluminiumbeklädnaden pulverlackerad, RAL 3009 på den röda huskroppen och RAL 7012 på de
  grå, halvblank med fin apelsinyta (typen `pulverlack`); träet invändigt vitmålat och matt.

- **Träet**: virke, limträ och snickerier (`textur="virke"`) har träslag och ytbehandling (`art`: gran, furu, lärk,
  ask; `yta`: obehandlad, olja, lack, vitpigmenterad), och färgerna kommer ur träslaget. Asken (`ASK`, oljad) är
  avsedd för köket och snickerierna; `./mod materialprov Ask` visar den på luckor och skivor.
- **Insidan**: gipsen målad med rollens struktur, betonggolvet slipat (ballast, molnig ton, halvmatt), kaklet i
  plattor med fogar i väggens plan.

Vyerna (`vyer.py`) anger kamera, mål, objektiv och dagsljus som (månad, dag, klocka, väder), t.ex.
`(9, 15, "12:00", "mulet")` (mulet: jämnt ljus som på foton i mulet väder, bra för att bedöma material). Ljuset räknas
fram för platsen (`skelett.PLATS`) med `verktyg/modellering/modellering/dagsljus.py` (`./mod ljus`). Inomhusbilderna
I01–I30 (`INNE`, rummens namn i `RUMSNAMN`) renderas i 4K med [`renderingar/rendera.sh`](../../renderingar/), med
kameraplanen där. `./mod rendera --blend` sparar också scenen (`ut/trebodar.blend`) med materialen och en kamera per
vy, för egna justeringar i Blender; ändringar som ska vara kvar görs i `material.py` och `vyer.py`.

## Modellträdet

```
Trebodar
├── Mark                        berg, uppfyllnad och sovrumsavsats (marken.json), schaktet runt plattan på mark,
│                               återfyllning, entréavsatsen och bänktrappan vid 2SO-D1
└── Hus
    ├── Grund                   bottenplatta (kantbalk, balkar, plintar, L-element), källarväggar V1–V21, rör P1–P19,
    │                           plattan på mark (L-element 500, AR-02), fasadsten per vägg
    ├── Mellanbjälklag          betongplatta 150 med trapphål, kantisolering
    ├── Armering                bottenplattan (R-04), källarväggarna (R-05), mellanbjälklaget (R-06)
    ├── Stomme
    │   ├── Stomme prefab       trästommen ovanför bjälklaget, en beställning
    │   │   ├── Ytterväggar     Vägg 1NO … 3NV (regelverk 45×95)
    │   │   ├── Innerväggar     Vägg 1A–1D, 2A–2C
    │   │   ├── Takstolar       Takstol 1NO, 1SV, 2NO, 2C, 2SV, 3NO, 3SV
    │   │   ├── Stolpar         LN1_1, LN1_2, LN1_3, LD4_1
    │   │   └── Takbalkar       Takfall 1SO, 1NV, 2SO, 2NV, 3SO, 3NV (takbalkar, avväxlingar, kortlingar, upplagsreglar)
    │   └── Nock- och dalbalkar NB1, DB2, NB3, DB4, NB5 (K-01), en egen beställning
    ├── Tak                     per takfall: hårdboard, ströläkt, råspont, underlagspapp, takplåt i banor;
    │                           takkanter (takfotsplåt, rännor, stuprör, vindskivor), dalar, takfönster TF1–TF3
    ├── Fasad                   per vägg: Utsida 1NO … = utegips, ströläkt, spikläkt, panel
    ├── Fönster och dörrar      VELFAC:s fönster och fönsterdörrar (även källarens), ytterdörrar, innerdörrar
    ├── Installationer          avlopp (badrummet, köket, källaren, stammen och grundledningen), el,
    │                           ventilation, tappvatten, golvvärme, köldbärare, brandlarm, dränering och dagvatten och
    │                           teknikrummets utrustning (hus/installationer/avlopp, el, ventilation, vatten,
    │                           golvvarme, kollektor, brandlarm och dranering, se deras README)
    ├── Trappa                  brant trätrappa till källaren, i trapphålet
    ├── Altan                   trädäck framför skjutpartiet 2SV: trall, sarg, bjälkar, bärlinor och plintar (fria
    │                           från dräneringens och dagvattnets ledningar), lucka och trappsteg
    ├── Kamin                   Rais 600 i väggen 2C, rökrör och isolerad skorsten genom taket
    ├── Isolering               takets träfiber och väggarnas mineralull
    ├── Invändigt               innertak, ytterväggarnas insida (ångbroms, installationsskikt, OSB och gips),
    │                           innerväggarna: lätta väggar L1–L14 och L19 och skikten på alla innerväggar, kökets
    │                           inbyggnad (L15–L18, förrådet ovanför, smygar, lucka och galler), ändbrädor av ask
    │                           där väggarna slutar fritt, badrummets golv (fallavjämning, tätskikt och klinker),
    │                           källarväggarnas gips, källarens innerväggar KL1–KL10 (stomme och gips per vägg)
    └── Inredning               inbyggt, isär från husets system: garderoben i sovrummet (stomme, skikt, dörrar),
                                dubbelsängen där (160 × 200, huvudgaveln mot 2B),
                                köket (kylen, frysen, skåpen, fronterna, skafferiets dörr och hyllor, bänken längs 3NV
                                och 3SV och ön med lådskåp, bänkskiva, diskho, häll och diskmaskin), badrummet
                                (bänken med tvättstället, badkaret, WC:n, duschens dörrar och duschset, skåpet,
                                spegeln och handdukstorken)
```

`./mod bygg --del "Hus/Stomme/Stomme prefab"` exporterar prefabstommen som en egen modell, och på samma sätt nock- och
dalbalkarna och varje vägg eller takstol för sig (`--del "Hus/Stomme/Stomme prefab/Ytterväggar/Vägg 1NO"`).

## Namn

Namnen i modellen är kanoniska och följer handlingarnas beteckningar. Onshape-modellens namn står inom parentes där
handlingarnas källfiler har dem (K-03).

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
  källarens fönster F1–F3 (R-05); innerdörrar ID1–ID6. Delarna: KARM, KARMALU (aluminiumbeklädnad), LIST
  (tätningslister), BAGEALU, BAGEPROFIL (kompositprofilen), GLASLIST (invändig, plast), GLAS,
  TROSKEL och BOTTEN (fönsterdörrens tröskel och bågens bottenprofil),
  BLAD (ytterdörrarna); skjutdörrens partier FV och FH (fasta) och de skjutbara bågarna SV och SH med mittposten
  SH-POST och KOPPLING mellan partierna; i öppningen PAF (påföringen), DREV, FOG, PROFIL-O/V/H och PLAT-O/OU/V/H
  (anslutningsprofilen och plåtarna), BLECK, SMYG-V/H/O/U och BANK.
- **Delar**: `<montage>-<typ><nr>`, numrerade längs väggen eller takfallet. Väggar och takstolar: S syll, H
  hammarband, R regel, L liggande (överstycke, bröstning, topregel), D diagonal, U underram, X sned del under taket
  (takstolens ytterbalk), K kloss, P plåt. Takbalkar: T takbalk, A avväxling, K kortling, UR upplagsregel. Tak: HD
  hårdboard, SL ströläkt, RP råspont, UP underlagspapp, TP takplåt; takkanterna: TF takfotsplåt, HR hängränna, RG rännans gavel, VS vindskiva, VB vindskivebeslag, rännornas stuprör ST1–ST3, i dalarna DB2-KIL och DB2-RD
  (kilar och rändal) och vid ändarna DB2-LA1, -RS1 och -ST1 (ändlåda, rörstos och stuprör; 2 vid den södra änden).
  Fasad: UG utegips, SR ströläkt, SP
  spikläkt, PA panel. Invändigt: AB ångbroms, IL installationsläkt, GI gips (i innertaket den inre skivan), GY
  innertakets yttre gipsskiva (möts i skarpa linjer i nockarna och under dalbalkarna). Isolering: TI tak, IS
  isolerstoppet vid takfoten, VI vägg. Takplåtens banor heter TP och numreras längs takfallet.
- **Innerväggarna**: de lätta väggarna L1, L2 … (stomme med S, R, H och L som regelväggarna) och skikten på varje
  innervägg och ytterväggarnas insida: OS OSB, GI gips, PW plywood, TS tätskikt, KA kakel. Källarväggarnas gips
  heter efter väggen eller fönstret (V3-GI01, F1-GI01; bröstningarnas F1-GIB). Innerdörrarna ID1–ID6 är
  fickdörrar med BLAD, SKENA och smygen SMYG-L (låssidan), -F1, -F2 (vid fickan) och -O1, -O2 (överstycket)
  (BR brädorna på fickans sidor). Fönstren: BLECK fönsterblecket, BANK
  fönsterbänken, SMYG-V, -H och -O smygen. Garderoben: GA-, GB- och GC-delar som väggarna, GD1 och GD2 dörrarna
  (BLAD-V, -H, SMYG-V, -H, -O), G-TAK taket. Kökets inbyggnad: L15 fronten och L16 gaveln med delar som de lätta
  väggarna (K kortlingen under huvudstolpens strävor, insidans gips GI02, gavelns gipsskivor GI02 och GI03),
  gipsväggarna L17 och L18 (GI01, GI02),
  KYL-, FRYS- och SKAFFERI-SMYG-V, -H, -O smygen,
  LUCKA-SMYG-V, -H, -O, -U och LUCKA-BLAD luckan, KYL- och FRYS-GALLER, förrådets FG-L bärläkt, FG-R reglar och
  FG-OS01 golv, SKAFFERI-TAK; i köket KYL och FRYS vitvarorna med -SOCKEL-R, -B, -G (reglar, bottenskiva, galler),
  -SKAP- (S sidor, B botten, T tak, H hyllor), -FRONT1, -FRONT2 och -GANGJARN1 osv. (skåpets dörr), SKAFFERI-DORR,
  SKAFFERI-GANGJARN1–5 och SKAFFERI-HYLLA-L4-1 osv.
  Köksskåpen: B1–B7 längs 3NV norrifrån, B8–B10 längs 3SV österifrån, O1 (diskmaskinen)–O3 i ön norrifrån, med
  -SIDA-V, -SIDA-H, -BOTTEN, -TAK (eller -TAK-F och -TAK-B), -RYGG, -SKIVA, -FRONT1–4 nedifrån (i öns O2–O3 -FRONT1–3) och lådorna
  -LADA1-SIDA-V, -SIDA-H, -BOTTEN, -FRAM, -BAK, -SKENA-V, -SKENA-H; B-BRADA, B-FOG1–10, O-FOG1–4 fogbrädorna, B-SIDA,
  O-SIDA1–2 och O-RYGG de vita sidorna, B-SPARK1–2 och O-SPARK sparklisterna, B-SKIVA och O-SKIVA bänkskivorna,
  DISKHO, BLANDARE, HALL och HALL-KROPP.
- **Badrummet**: inredningen BA-BANK1–BANK3 (skåpen som köksskåpen, -DORR1 och -DORR2), BA-BANK-SKIVA, BA-BANK-SPARK,
  BA-TVATTSTALL och -BLANDARE, BA-BADKAR och -BLANDARE, BA-WC- (FOT, SKAL, SITS, LOCK, CISTERN), BA-DUSCH- (DORR-V,
  DORR-O, HANDTAG, PROFIL, BLANDARE, STANG, TAKDUSCH, HANDDUSCH), BA-SKAP (stommen, HYLLA1–4, DORR1–2), BA-SKAP-SPARK,
  BA-SPEGEL och BA-HANDDUKSTORK-; golvet BA-FB fallavjämningen, BA-TS tätskiktet och fixet och BA-KL klinkern, en per
  plan del av fallet; väggbiten L19 med ändens skikt L19-ANDE-PW, -GI, -TS och -KA; innertakets panel PA (i
  takfallets innertak); avloppet AV1–AV4 (ledningarnas rör), AV-GB golvbrunnen (-RING, -SIL) och AV-VL-TS, AV-VL-BK
  vattenlåsen; ID1-TROSKEL tröskeln.
- **Trappan**: TR-V1, TR-V2 vangstyckena, TR-S01 … TR-S10 stegen nerifrån. **Kaminen**: KM-INSATS, KM-RAM, KM-GLAS,
  KM-FRONT, KM-PLAT, KM-STOD1–2, KM-STOS, KM-ROR1–2, KM-SKORSTEN, KM-HUV, KM-KRAGE, KM-LUFT (flexslangen),
  KM-LUFT2 (den isolerade kanalen), KM-LUFTHUV, KM-LUFTKRAGE.
- **Bottenplattan** (K-06, L400): BP-B betongen, BP-KB kantbalken, BP-IB balkarna under innerväggarna, BP-PL-P1
  plinten under röret P1 osv., BP-FAS betongen i L-elementens fas, BP-L L-elementen, BP-CS cellplast S300 under balkar
  och plintar, BP-C1 och BP-C2 cellplasten S100 (undre lagret 100, lika tjockt som L-elementens fot, och övre 200).
- **Plattan på mark**: PM-L L-elementen, PM-FAS betongen i L-elementens fas, PM-C1 och PM-C2 cellplasten (undre och
  övre lagret), PM-M makadamen, PM-F den dränerande fyllningen. **Marken**: MA-1, MA-2 makadamen mellan L-elementen och schaktets kant, FK-V2 och FK-V9
  återfyllningen mot källarväggen; entréavsatsen E-DS (dörrsteget), E-AV (avsatsen), E-S1–E-S3 (trappstegen);
  bänktrappan BT-B1, BT-B2 (bänkens plank), BT-BB1–BT-BB6 (bänkens ben), BT-S1, BT-S2 (stegets plank),
  BT-SB1–BT-SB4 (stegets ben).
- **Fasadsten** (en grupp per vägg, efter väggen ovanför): `3NV-ST2-04` är sten 4 längs väggen i skift 2 (räknat
  nedifrån), `3NV-HS2` hörnstenen i skift 2 (i hörnet i väggens slut), FB fogbruk, FM armeringsbruk och fästmassa.
- **Armering**: `BPA` bottenplattan, `KVA` källarväggarna, `MBA` mellanbjälklaget, sedan ritningens positionsnummer
  och järnets nummer: `MBA-A1-046` är järn 46 i position 1 (R-06), `MBA-Ö3-002` ett tilläggsjärn i zon Ö3. Bockade
  järn är raka bitar (bockradierna förenklade bort). Kontrollen prövar inte armering mot betong eller mot annan
  armering, men mot allt annat; mot avloppet är överlapp tillåtna (järnen läggs om runt rören). Installationerna med
  egen kontroll (tappvattnet, golvvärmen) prövas där mot järnen: ingjutna rör ska gå fria från dem.
  Startjärnen under F3:s bröstning går upp till under bröstningens järn (R-04 pos 42). Mellanbjälklagets järn slutar
  vid plattan på marks fria kanter vid L-elementens rygg (AR-02), som på R-06.

## Avsiktliga skillnader mot Onshape-modellen

Skillnaderna mot Onshape-modellen som modellen först byggdes efter är dessa:

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
- **Dalarna**: kilar av plywood på råsponten med fall 1:60 från mitten mot ändarna (plåtslagaren, AMA minst 1:75)
  och rändal av plåt på underlagspapp över dem. Dalarna slutar vid den kortare kroppens gavel, där dallinjen ligger i
  den längre kroppens fasadliv. Där tar en ändlåda av plåt emot vattnet, 105 × 100 i hörnet mellan fasaderna under
  gavelutsticket med botten 40 mm under dalens botten, och en rörstos Ø75 falsad i botten leder det till ett eget
  stuprör Ø75 ned i hörnet, 20 mm från fasaderna (plåtslagarens detalj). Rändalen, den kortare kroppens utstick och
  den längre kroppens tak viks ned i lådan; lådans yttre kant är lägst (30 mm), så att vattnet rinner ut över den till
  grannkroppens takfot och ränna om stosen sätts igen, aldrig in under plåten. Den längre kroppens takfot och ränna
  slutar vid gavelutstickets kant, över lådan, och rinner dit: hörnets stuprör är det enda för takfoten och dalen (ett
  stuprör per hörn). Rännorna på takfötter som går från gavel till gavel har stuprör Ø87 i båda ändarna. Lövsilen i
  stosen är inte modellerad.
- **Väggarnas möte med snedtaket**: takfotsväggarnas insida går upp till innertaket och kapas längs det, så att
  innertakets gips möter väggens i en skarp linje, med läkt bakom båda skivornas kanter; vid gavlarna en läkt
  längs takfallet bakom innertakets gipskant.
- **Ytterhörnen inne vid dalarna** (1NO–2SO, 2SV–1NV, 2NV–3NO och 2SV–3SO), där en gavel går förbi en långsidas
  ände: insidans skikt går runt hörnet var för sig, gavelns fram till långsidans och långsidans förbi gaveln, så att
  ångbromsen är hel och bara gipsen syns. Gavelns insida går upp till takbalkarna under grannkroppens takfall, och
  innertaket slutar mot den.
- **Takkanterna** (planritning 201: takutstick 100 utanför panelen): vindskiva 22×145 ytterst i gavlarnas utstick
  med vindskivebeslag vikt runt den (över överkanten, ned över framsidan och in under den), takfotsplåt med
  droppnäsa, hängrännor Ø125 och stuprör Ø87 vid takfötternas ändar mot gavlarna (dalarna har egna stuprör).
- **Takfoten**: ingen takfotsbräda; takbalkarnas ändar är synliga och fasaden går upp mellan dem till takbalkarnas
  överkant i panelens utsida (en ströläkt mot varje takbalk och en spikläkt överst i facket), så att luftintaget är
  öppningen ovanför panelen. Isolerstopp, regel 45 bultad på hammarbandet i varje fack, upp till takbalkarnas
  överkant och kapat efter takplanet; hårdboarden slutar på det, råsponten, pappen och plåten 20 mm utanför
  takbalkarnas ände.
- **Luftspalten** 34 mm: ströläkt 34×45 på hårdboard 3 mm, på varje takbalk och takstol och två mellan i varje fack,
  uppehåll 600 mm ovanför och nedanför takfönstren (U-03).
- **Enligt handlingarna** (K-03, K-05, K-06, R-04, R-05): strävor på båda sidor om LN1_3, LD4_1 GL30h 140×140,
  LD4_2 fyra reglar, ny stolpe LN1_1, toppklossar på takstolarna, kortlingar vid takfönstren, rören VKR 80×80×4 med
  plåtar, bottenplattan på en nivå med kantbalk, balkar, plintar och L-element, källarväggarnas kärnor ihopgjutna,
  plattan på mark med cellplast och fyllning, fasadstenen 15 mm ut, dubbel takbalk vid TF1, karmstolparna LD2_1 och
  LD2_2 i väggen 2B: LD2_2 vid trapphålets långsida och LD2_1 vid fickdörren ID2:s fickas ände (dalbalk 2 spänner
  över dörren och fickan, K-01), LD4_1 12 mm norr om fickdörren ID6:s ficka.
- **Toppklossar**: en kloss per takstol, på gavelstolarnas insida (utsidan är fasad) och på mittstolen 2C:s nordöstra
  sida, inne i väggens tjocklek (på den sydvästra skulle den gå ut genom gipsen), så att balken vilar på 90 mm.
- **Innerväggar** enligt planritning 201 rev 02 med modellens bärande väggar: lätta väggar 45×70 med OSB och gips
  (i badrummet plywood, gips, tätskikt och kakel) och skikt på de bärande innerväggarna. 2B är sluten söder om
  trappan och 2C vid väggens början. Väggen mellan kontoret och köket går rakt genom huvudstolpen.
- **Innerdörrarna** är fickdörrar: ID1 (badrummet, fickan mot söder bakom badrummets skåp, med tröskel), ID2
  (källartrappan, fickan mot norr i 2B till karmstolpen
  LD2_1), ID3 och ID4 (korridoren i höger huskropp), ID5 (sovrummet i höger huskropp, blad 800 med fickan mot öster,
  före stolpen LN1_1, och 500 mm vägg väster om öppningen) och ID6 (sovrummet i mittre huskroppen, fickan från L12 in
  i 2C söder om stolpen LD4_1), blad 75 mm bredare än öppningen i en ficka 55 mm längre än bladet. Fickan är hela
  stommens tjocklek, med brädor 12 mm i stället för OSB (gips 13 + bräda 12 + ficka 70 + bräda 12 + gips 13), också
  där den går in i en annan vägg (lattvaggar.fickor). ID3 stängs mot L1:s gips och fickan slutar vid L3, ID4:s ficka
  vid L4; ID6 stängs mot L11:s gips och ID2:s öppning börjar vid trapphålets vägg L6. Öppningarna har smyg av oljad
  ask 22 mm upptill och på sidorna, genom hela väggen i liv med skivorna: hel på låssidan, där bladet stängs mot den,
  och delad vid fickan och i överstycket med en slits för bladet.
- **Badrummet** (ärende #52, hus/badrum.py, hus/inredning/badrum.py, hus/invandigt/badrumsgolv.py): efter
  användarens skiss duschen i nischen mellan 1B, 1C och L11 med två glasdörrar mot rummet, badkaret fristående längs
  1SO under takfönstret TF1, WC:n mot L9, en bred badrumsbänk av ask (som köket) längs 1NO med tvättstället under
  fönstret 1NO-F1, spegeln till höger om fönstret och en vägglampa över det, och väggbiten L19 med ett inbyggt skåp i
  nischen vid L10; kakel och klinker Bricmate Jura som köksbänkarna. Golvet: klinker på tätskikt och fix på en
  fallavjämning på bjälklaget (som inte ändras: röret P4 står under duschen), med fall enligt GVK Säkra Våtrum 2026
  (6.4): i duschen ett kuvert mot golvbrunnen (10–29 mm/m), på övrig yta 2,5 mm/m mot duschen och inget bakfall;
  golvbrunnens fläns i bjälklagets överkant, minst 20 mm under tröskeln (26 mm av granit, fasad mot allrummet, med
  bladet kortare). Fickdörren ID1:s ficka går mot söder, bakom skåpet, inte i duschens vägg, och öppningen 15 mm
  längre norrut. Innertaket: panel av gran, vitmålad, på den inre gipsskivan; inget tätskikt i taket (GVK), men
  ångbromsen hel med tejpade skarvar och spotarna i installationsskiktet. Avloppet, tappvattnet och elen på
  inredningens lägen (hus/installationer/avlopp, vatten och el).
- **Skiktens hörn och överkant**: där en innervägg slutar mot en annan möts skikten på hörnets utsida var för sig:
  väggens skikt går förbi änden fram till den andra väggens skikt på samma djup och den andra väggens skikt förbi sin
  ände över skikten innanför, så att gipsen (i badrummet tätskiktet och kaklet) går runt hörnet och OSB:n inte syns;
  på insidan slutar de mot den andra väggens skikt. Där en del bara når en bit in i ett skikt går skiktet över den med
  ett urtag: gipsen går över stolparna 45×95 i de lätta väggarna (12,5 mm utanför reglarna) och OSB:n slutar mot dem.
  Där två väggar i samma linje slutar mot varandra med en lucka mellan stommarna (L12 och 2C över fickdörren ID6) går
  båda väggarnas skikt halva luckan förbi änden på de sidor där ytorna ligger i samma plan, så att ytan är hel.
  Skikten går upp till innertaket, och där taket lutar tvärs över väggen är skivornas överkant sned som taket.
  Ytskiktens språng och springor kontrolleras med `./mod ytor` (ingår i `./mod kontroll`).
- **Garderoben i sovrummet** (hus/inredning, ärende #16): lätta väggar GC, GB och GA (lägena i
  invandigt/lattvaggar.py) från stolpen LD4_1 längs 2C, runt kaminens kåpa till L7, med fronten i linje med L6 och ett
  snett hörn 600 × 600 mot fickdörren ID6; OSB och gips mot rummet upp till innertaket, gips inuti, två par dörrar i
  smyg av vitmålad furu och garderobens tak på dörrarnas höjd med tomrum ovanför.
- **Sängen i sovrummet** (hus/inredning/sang.py, ärende #27): dubbelsäng med madrass 160 × 200, huvudgaveln av ask
  mot 2B:s gips och mitt mellan 2A:s och L6:s, för att se hur rummet räcker.
- **Altanen** (hus/altan/altan.py, ärende #30, #70): trädäck framför skjutpartiet 2SV mellan fasaderna 1NV och 3SO,
  från 2SV ut 250 mm förbi gaveln 1SV:s linje, överkanten i golvets höjd, med breda trappsteg ned till marken längs
  framkanten och sidan. Varje bräda (grånad tryckimpregnerad trall 34 × 135) är en egen del; `LANGS` väljer
  brädornas riktning (längs 2SV eller tvärs, ut från huset) och `RAM` om en ram av brädor går runt om. Bjälkar 45×145
  c/c 600 på bärlinor 2 × 45×145 och betongplintar Ø200 i borrade hål i berget (marken har hålen), utanför
  dräneringens schakt, sargbräda längs de fria kanterna, hål runt stuprören i de inre hörnen och en lucka över
  spolrören och spolbrunnen i det inre hörnet mot 1NV. Trappstegen är en bräda och en sargbräda höga (179) och tre
  brädor djupa, små däck staplade på varandra och nederst på plintar, så många som berget kräver (ett till tre längs
  framkanten, där berget faller österut, och tre längs sidan). Delarna heter AL-T (brädorna), AL-LU (luckans
  brädor), AL-RAM, AL-S (sargen), AL-B (bjälkarna), AL-L (bärlinorna), AL-P (plintarna) och AL-FS1-…, AL-SS1-…
  (trappstegen längs framkanten och sidan, steg 1 överst: -T brädorna, -B bjälkarna, -S sättsteget, -G gaveln).
- **Ändbrädorna** (hus/invandigt/andbrador.py, ärende #31): där väggarna 1B, 1D, 2A och 2B slutar fritt i ett rum
  en bräda av oljad ask 22 över änden (stommen och skikten på båda sidorna), från golvet till innertaket, som smygen
  runt fönstren; delarna heter `<vägg>-ANDE`.
- **Kökets inbyggnad** (hus/invandigt/kokets_inbyggnad.py och hus/inredning/kok.py, ärende #20 och #21; inte på
  planritning 201): kyl, frys och skafferi framför L4 mot köket, från L2:s linje till 3NV, bakom en vägg av gips
  från golvet till innertaket. Lätta väggar 45×70 (lägena i invandigt/lattvaggar.py) framför L4:s och 3NV:s färdiga
  skikt: fronten L15, 738 mm från L4:s yta, med gipsen mot huvudstolpen LN1_3:s strävor och topregel (som hamnar i
  förrådet; stommen och OSB:n har ett urtag runt deras toppar, med en kortling under dem), och gaveln L16 i L2:s
  linje: under förrådet bara två gipsskivor i L2:s yta mot gången, ovanför stomme på en syll med luckan; fronten har
  en egen ändregel innanför gipsskivorna. Mellan nischerna och mot skafferiet också bara två gipsskivor (L17 mot
  huvudstolpen och L18), upp till förrådets reglar. Tre öppningar i fronten från golvet till 2 100, med en regel emellan och smyg av vitmålad furu: nischerna
  för integrerad kyl (560 × 1 780) och frys (560 × 880, högskåp ovanför), 600 fria, och skafferiets dörr, 564 fri,
  så att bänken längs 3NV (700) ryms öster om den. Fronterna och dörren av oljad ask i liv med väggen. Förrådet ovanför: OSB 22 på bärläkt med överkanten
  2 167 och en lucka 500 × 600 i gavelns norra del. Vitvarornas luft tas in genom socklarnas galler och går upp
  bakom dem, genom en springa mellan förrådsgolvet och L4 och ut genom ett galler i fronten över varje nisch.
  Köksbelysningens dimmer och brytaren över den sitter på 2B mot gången, mitt emot gaveln, uttagen till kylen och frysen på
  L4 i förrådet.
- **Köket** (hus/inredning/koksskap.py och koksbank.py, ärende #21; inte på planritning 201): vinkelbänk efter
  användarens skiss längs 3NV från kökets inbyggnad till 3SV och längs 3SV västerut, 700 djup, och en ö 1 000 djup
  1 100 från bänken (fritt mellan bänkskivorna), mitt för hällen, med de tre Stav över sig. Skåpen byggs vart för sig av björkplywood 20 (600 djupa, från sparklisten 90 till bänkskivans
  underkant 888) med fyra lådor av massiv björk 14 och botten av björkplywood 4 på Blum MOVENTO 760H (SKW = LW − 42,
  SKL = NL − 10, urtag 13, NL 550; under diskhon 350; framstycket med bottnen i spår, för kopplingarnas skruvar 75°,
  bakstycket på botten, hålen för löparens hake i sidornas bakände) och fronter av fräst ask 22 (115, 115, 233 och 323 nedifrån räknat från toppen,
  i öns lådskåp tre lådor 115, 233 och 441, 3 mm spel, linsformat grepp); mellan skåpen fogbrädor av ask 22 och mot inbyggnaden en bräda 45. Längs 3NV sju skåp
  mellan brädan och hörnet, med hällen i B4 mitt mellan fönstren 3NV-F4 och 3NV-F5 under köksfläkten: B1–B3 633,4
  breda (fronterna 605,4), B4–B7 och skåpen längs 3SV 599,1 (571,1); hörnet är dött med en fogbräda 22 × 22. Diskhon
  i B2, med kopparrören från underfördelaren UF1 genom två hylsor bakom lådorna (KO-DB1, #83). Ön: diskmaskinen (vanlig integrerad 60, fronten 596 och fritt 602 mellan fogbrädorna)
  och två lådskåp med tre lådor, alla 624 breda, mot bänken, vita sidor och rygg, öppen för benen mot väster. Bänkskivorna
  Bricmate Jura 12.
- **Fönster och fönsterdörrar** från VELFAC (VELFAC 200 ENERGY) efter systemritningarna (utgåva 15, 07.26), med
  profilerna förenklade till ytterkonturerna och svepta med gering: vändfönster (vändbart fönster), fast fönster med
  båge, 1-luft fönsterdörr med 24 mm tröskel och en 2-luft skjutdörr med 24 mm tröskel mellan två fasta partier
  (2SV-D1, de mittre bågarna skjutbara, kopplade med kopplingslist och lika breda rutor). Typerna: vändfönster
  10×10 och 8×8 och i källaren 8×6 och 6×12, fasta fönster 6×21 (1NO, 3NO), 21×21,86 (1SV), 9×21 (3SV-F2) och 6×6
  (1SO), fönsterdörrar 9×21, 10×21 och 11×21 och skjutdörren 48×23,6 (2SV). Monteringen enligt VELFAC:s
  montageanvisning och träfasaddetaljer: aluminiumets utsida 20 mm innanför panelens utsida, så att karmträet ligger i
  utegipsens utsida; fog 15 mm mot regelverket med drevning och lufttät fog inifrån; fönstren på en påföring 18×114
  med fönsterbleck (fall 1:4, droppnäsa 30 mm utanför panelen), dörrarna på en bädd 10; anslutningsprofil på karmen
  upptill och vid sidorna med 1 mm plåt i fönstrens kulör ut och upp bakom läkten (vid vändfönstrens sidor utanför
  beslagets zon); panelen och läkten 10 mm från karmen. Invändigt går väggens skikt och installationsläkten fram till
  karmens linje, och smygen är oljad ask 20 mm med fibrerna längs varje bit, fönsterbänken under bottenkarmen och vid
  fönstren från golvet en bräda av ask från golvet till karmen (med smyglister, `SMYGLIST` > 0, lister av ask runt
  smygen i skivornas tjocklek); i badrummet kakel, i källaren gips (källarens fönster i cellplastens smyg). Beslagen
  och handtagen är inte modellerade.
- **Ytterdörrarna** (ärende #33): huvudentrén 1SO-D1 och källarens pardörr D1 (i 3NO:s system under bjälklaget, ett
  blad 900 till höger sett utifrån och ett smalare som öppnas ibland) har en karm efter Elitfönsters altandörr (Original
  Alu 100), 20 mm mindre än öppningen och 22 mm innanför panelens utsida, och blad av en plywoodkärna 44, liggande läkt
  och stående panel utanpå, i den andra kulören än fasaden runt dem (grå järnvitriol i det röda huset, falu rödfärg i
  det grå). Panelen ligger i liv med fasadpanelen och täcker karmen fram till en fog 4 mm mot den, så att ingen karm
  syns utifrån; smygen av ask går från golvet.
- **Källarväggarnas insida**: gips 13 direkt på cellplasten (brandskydd), från bottenplattan till bjälklaget, på
  ytterväggarnas insida och båda sidor av innerväggarna, runt väggändarna i D2 och D3, i fönstrens smyg från karmen
  och på bröstningen. Källardörren D1 (pardörren) sitter i det yttre cellplastlagret; smygens gips går till kärnans
  utsida.
- **Källarens innerväggar KL1–KL10**: lätta väggar 45×95 C24 c/c 600 med gips 13 på båda sidor från bottenplattan
  till bjälklaget, i rörens linjer så att rören står i stommen (KL8 45×120 för avloppsstammen Ø110 bredvid P4), med
  dörrhålen KD1–KD5 för M9×20 och M8×20 (rumshöjden 2 100 rymmer inte M×21). Teknikrummet avgränsas av KL8–KL10 med
  en knyck runt värmepumpen; KL5 börjar vid KL4, eftersom trappan går ut över dess linje söder därom.
- **Huvudentrén 1SO-D1** (planritning 201): i Onshape-modellen fanns bara öppningen i regelverket. Dörren har
  en karm som Elitfönsters altandörr och ett tätt dörrblad med panel (produkten inte vald).
- **Plattan på mark** enligt AR-02: mellanbjälklaget i L-element 500 (ytterkanten i väggarnas ytterliv) med betongen
  fram till L-elementens rygg, 70 mm innanför K-05:s kontur vid de fria kanterna, och i ryggens fas (20 mm innanför
  konturen i överkant), vid de fria hörnen ut till konturen i ryggens urtag (R-06 detalj F), cellplast 100 + 250,
  makadam 150 och dränerande fyllning i ett schakt i berget 100 mm utanför plattan.
- **Marken** är Onshape-modellens mark (`mark/marken.json`, de färdiga höjderna efter markarbetena) fram till huset
  (inte K-06:s högre fyllnadshöjder). Där den inte når fram ligger återfyllning: framför 2SV upp till markens nivå
  intill och vid nedgången till källardörren D1 från källargolvets nivå (K-06); över nedgången är uppfyllnaden
  borttagen. Två separata avsatser av granit: sovrumsavsatsen (Onshape-modellen, breddad västerut till 1SO:s fasad)
  och entréavsatsen vid 1SO-D1 (dörrsteg, avsats och tre trappsteg längs fasaden mot NO, sex lika steghöjder till
  marken), och en bänktrappa av lärk vid 2SO-D1: bänk längs fasaden ett steg ned från dörren och ett steg framför
  dörren, tre lika steghöjder till sovrumsavsatsen. Källartrappan går från avsatsen framför D1 upp till husets östra
  fasad.
- **Trappan** till källaren är brant (45°, 11 steghöjder) och ryms i trapphålet, med fri höjd över hela trappan
  (K-05 räknar med en 3,0 m lång trappa).
- **Kaminen** enligt planritning 201 och Rais måttritning och monteringsanvisning (11-6520): insatsen i öppningen i 2C
  mot allrummet, inbyggd i en innbyggingskasse av 50 mm kalciumsilikat (kåpan av de lätta väggarna L7, L13 och L14 och
  fronten i öppningen, minst 920 × 498 × 1 600) med konvektionsöppningar 300 och 550 cm² och plåt över den övre;
  skorstenens isolerade del börjar i kassen och går genom plåten. Förbränningsluften (AirSystem) går upp genom taket:
  flexslang Ø100 från anslutningen under insatsen till kåpans västra del (kåpan 220 mm bredare mot väster än
  planritningen), genom plåten, och isolerad kanal Ø100/Ø160 bredvid skorstenen genom innertaket och taket, med huv
  på stag; ca 4,7 m (anvisningen: Ø100 upp till 5 m). Underkanten 450 över golvet och skorstenen 800 mm över nocken
  (antaget).
- **Fasadstenen** enligt AR-01: enskilda stenar i 400 mm skift med slumpade längder 600–1 200, fog 10, hörnstenar 400
  och 200 i varannat skift och kluven framsida 30–50 mm, med fogbruk och armeringsbruk; utbredningen som i
  Onshape-modellen.
- **Nytt**: tak- och fasadskikt, takplåten i banor med falsar, isolering, invändiga skikt, källarväggarna V1–V21
  enligt K-05, rören P1–P19 och armeringen ur R-04, R-05 och R-06.
