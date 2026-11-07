# Tappvattnet

Kallvattnet och varmvattnet som data i modellen: tappställena, fördelarna i fördelarskåpet och underfördelarna i
källaren, rören (rör-i-rör från fördelarna till varje tappställe, ingjutna i mellanbjälklaget) och matarledningarna i
teknikrummet. Samma data ger
modellens geometri (rören, dosorna och fördelarna i 3D), genomföringarna genom husets delar, kontrollen och
tappvattenritningarna. Vattnet är fristående: det tar inga hål i andra delar och ingår inte i modellens krockkontroll;
det har en egen kontroll som redovisar genomföringarna och krockarna mot husets delar och de andra installationerna.

```
cd verktyg/modellering
./mod vatten kontroll     # utgångarna, anslutningarna, tiden till varmvatten, hastigheterna, järnen, rören i varandra,
                          # genomföringarna och krockarna mot husets delar och de andra installationerna
./mod vatten lista        # tappställen, rör, genomföringar och krockar (ut/vatten/)
./mod vatten ritning      # ritningarna VS-01 (ut/vatten/VS-01 Tappvatten.pdf, kräver STEP-filen: ./mod bygg)
./mod rendera detalj-teknikrum   # fördelarskåpet och rören upp i bjälklaget i bild
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Tappstalletyp` (normflöden), `Dosatyp` (väggdosa, golvdosa, hylsor), `Rortyp` (PEX, med skyddsrör för rör-i-rör, och koppar) och `Fordelartyp` |
| [`katalog.py`](katalog.py) | Produkterna, tills vidare allmänna typer med vanliga mått och normflöden (ej valda) |
| [`punkter.py`](punkter.py) | Tappställe, fördelare och rör, och hur rören dras: nivån i bjälklaget (`Z_ROR`), filerna (`FIL`), `till_tappstallet` och `ror` |
| [`teknikrum.py`](teknikrum.py) | Fördelarna, tappställenas ordning (`ORDNING`), stråken (`strak`) och matarledningarna |
| [`underfordelare.py`](underfordelare.py) | Underfördelarna UF1 (under köket) och UF2 (under badrummet): läget på väggen, stammarna, matningen och deras tappställen (UF2 i ett eget stråk, UF1 med kopparrör till hylsor) |
| `rum/<rum>.py` | Ett rums tappställen: typ, dosa, läge på väggen eller golvet och rörtyp |
| [`system.py`](system.py) | Allt ur rummen (`MODULER`), rören från fördelarna, kontrollen, genomföringarna och utdraget för ritningarna |
| [`vatten.py`](vatten.py) | Geometrin, ett montage per rum och ett för teknikrummet under `Hus/Installationer/Vatten` |

Teknikrummets utrustning (värmepumpen med varmvattenberedaren, fördelarskåpet och vattenmätaren) är gemensam för
vattnet och värmen: [`../teknikrum.py`](../teknikrum.py), montaget `Hus/Installationer/Teknikrum`, som ingår i
modellens krockkontroll. Lägena på husets ytor ([`../montering.py`](../montering.py): `vagg`, `golv`, `kallarvagg`,
`i_vaggen`, nivåerna i betongen `I_BETONGEN`), stråken ([`../strak.py`](../strak.py): `Strak`, `vag`, `filer`) och
genomföringarna ([`../genomforingar.py`](../genomforingar.py)) är gemensamma med de andra installationerna.

## Begreppen

- **Tappställe** (`Tappstalle`): det som förbrukar vatten, med id `<rum>-<typ><n>` (t.ex. `BA-DU1`), typen med
  normflöden, anslutningen (väggdosa i väggen, golvdosa i golvet eller hylsor i bjälklaget), läget och rörtypen.
  Kallvattnet ansluter till höger och varmvattnet till vänster sett mot dosan; golvdosornas riktning från varmt till
  kallt är `kallt`.
- **Fördelare** (`Fordelare`): kallvattnets och varmvattnets stammar i fördelarskåpet, med numrerade utgångar uppåt;
  utgång 0 och utgången efter den sista är stammens ändar (inlopp och genomgång).
- **Underfördelare** (`Underfordelare`): en liten fördelare öppet på en vägg i källaren i ett rum med golvbrunn,
  matad från fördelarskåpet med ett rör per media som ett tappställe i `ORDNING` (rören rakt ned ur bjälklaget till
  stammarnas början, utgång 0), med egna utgångar till sina tappställen. UF1 under köket på V14 (diskbänken och
  diskmaskinen i ön, #50, med kopparrör till hylsor, #83) och UF2 under badrummet på KL1 (WC:n och tvättmaskinen i
  skåpet, #51, i ett eget stråk): fördelarskåpets filer räcker inte till fler rör (ett sjuttonde krockar med
  ventilationens kanal FF3-K2).
- **Hylsor** (dosans slag `hylsa`, #83): köket har inga golvdosor och inga rör i bjälklaget. Kopparrör 15 går från
  UF1:s utgångar rakt upp till under källarens tak (`Z_TAKET`, varmvattnet överst), där först i x och sedan i y till
  under sin hylsa och rakt upp genom den: Ø50 (PP-avloppsrör), en per rör, ingjuten mellan armeringsjärnen
  (`punkter.hylsa` flyttar den längs `kallt` så lite som behövs). Diskbänkens två står bakom diskbänksskåpets korta
  lådor intill V14:s gips, i samma maska i nätet (över V14 ligger nätet och stödjärnen så tätt att två Ø75 inte ryms),
  och rören går upp till blandarens slangar; diskmaskinens bakom maskinen i nischens ände längst från röret P3,
  utanför dess genomstansningszon. Alla kopplingar och avstängningar sitter vid UF1, åtkomliga i källaren.
- **Rör** (`Ror`): från en fördelares utgång (`FD-KV:3`), en utrustning (`TK-VP:VV-ut`) eller ett tappställe till ett
  annat. Rören till tappställena har tappställets id och media (`BA-DU1-VV`) och dras ur stråken (`ror`);
  matarledningarna i teknikrummet (`VA-KV1` …) har sina brytpunkter i `teknikrum.py`.
- **Stråk** (`Strak`): en gemensam väg i mellanbjälklaget med en fil per rör, från fördelarskåpet. Filen går genom
  rörets utgång: stråket förskjutet i sidled genom utgången.

## Dragningen

- Rören går ur fördelarskåpets öppna ovansida upp i mellanbjälklaget och gjuts in mellan armeringsnäten (R-06), alla
  i en nivå närmast underkantsnätet (`Z_ROR`; golvvärmen går ovanför), en fil per rör c/c 50 som nätens maskor:
  kallt och varmt bredvid varandra. Varmvattnets fördelare sitter bakom kallvattnets, och utgångarna sitter i sina
  rörs filer, mellan underkantsnätets järn och söder om ventilationens kanal FF3.
- Där rören går upp eller ned genom bjälklaget går de mellan armeringsjärnen (`forskjutning`, med
  `../strak.mellan_jarnen`): golvdosan flyttas så lite som behövs (fri från väggarna), och rören i väggen flyttas längs
  väggen (och tvärs den inom regelfacket eller cellplasten) och går därifrån till väggdosan.
- Tappställenas ordning (`ORDNING`, från söder, med stråkets ben där rören viker av) bestämmer filerna: ett
  tappställes två rör ligger bredvid varandra, det som viker av först ytterst mot sin sida, så att rören inte korsar
  varandra. Stråket O går österut över V19 till källarrummet och köket, S västerut och söderut till badrummet och
  längs V7, och V västerut och söderut längs V21. Där stråken går över källarväggarnas lodräta järn går de mellan
  dem.
- Röret lämnar filen i punkten närmast tappstället (eller förbi `via`) och går därifrån upp ur bjälklaget i väggens
  regelfack eller golvdosan på plan 1, eller ned ur bjälklaget i källarväggens cellplast bakom gipsen till väggdosan i
  källaren. Kopparrören till hylsorna (`ror_hylsa`) går inte i stråken.

Ett tappställe flyttas i sin rummodul (läget följer väggen eller golvet). Ett nytt tappställe läggs i en rummodul (och
rummet i `MODULER`) och får en plats i `ORDNING`, där dess filer viker av utan att korsa de andra; kontrollen visar
rör som går i varandra och krockarna mot järnen.

## Kontrollen

`./mod vatten kontroll` (fel stoppar, anmärkningar redovisas):

- utgångarna: varje tappställe har en utgång och varje utgång används en gång, inom fördelarens utgångar och ändar;
  varje tappställe står i en ordning (fördelarskåpets eller en underfördelares);
- anslutningarna: ett rör per media som tappstället har (normflöde över noll), referenserna till fördelare, utrustning
  och tappställen;
- tiden till varmvatten vid tappställets normflöde, ur volymen från beredaren (högst 10 s, BBR 6:62 och Säker Vatten;
  anmärkning över 8 s; genom en underfördelare räknas dess matning med), och vattenhastigheten vid normflödet (fel
  över 2,5 m/s, anmärkning över 2,0 m/s; underfördelarnas matning vid det dimensionerande flödet);
- rören: var de lämnar stråket (kallt och varmt inte på samma ställe), sneda stycken och rör som går i varandra;
- genomföringarna ur husets geometri: ingjutna rör ut ur bjälklagets över- och underkant, rör i väggarnas regelfack
  (syllen urtas) och i källarväggarnas cellplast (ska rymmas), hylsor eller kärnborrning där rör går genom en platta
  eller källarväggens kärna;
- krockar ur modellens geometri mot husets delar (stommen var för sig, skikten per rör), mot armeringen och mot elen,
  ventilationen, golvvärmen och teknikrummets utrustning (fel).

## Ritningarna

`./mod vatten ritning` ritar serien VS-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3):

- **VS-01.1 rören i mellanbjälklaget** (1:50): stråken med kallt och varmt bredvid varandra, var rören kommer ut ur
  bjälklaget (upp till plan 1, ned till källaren och fördelarskåpet) och tappställena, med plan 1:s väggar och
  källarväggarna; tabeller över tappställena, rören och genomföringarna med lägen;
- **VS-01.2 teknikrummet** (1:20): planen och vyn mot V19 med fördelarskåpet, fördelarna, rören upp i bjälklaget,
  matarledningarna, värmepumpen och ventilationens kanal.
