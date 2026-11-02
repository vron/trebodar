# Tappvattnet

Kallvattnet och varmvattnet som data i modellen: tappställena, fördelarna i fördelarskåpet, rören (rör-i-rör från
fördelarskåpet till varje tappställe, ingjutna i mellanbjälklaget) och matarledningarna i teknikrummet. Samma data ger
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
| [`typer.py`](typer.py) | Produkttyperna: `Tappstalletyp` (normflöden), `Dosatyp` (väggdosa, golvdosa), `Rortyp` (PEX, med skyddsrör för rör-i-rör) och `Fordelartyp` |
| [`katalog.py`](katalog.py) | Produkterna, tills vidare allmänna typer med vanliga mått och normflöden (ej valda) |
| [`punkter.py`](punkter.py) | Tappställe, fördelare, rör och stråk, och hur rören dras: nivåerna i bjälklaget (`NIVA`), järnen under överkantsnätet (`HINDER`), `vag`, `till_tappstallet` och `ror` |
| [`teknikrum.py`](teknikrum.py) | Fördelarna, utgångarnas ordning (`UTGANGAR`), stråken (`STRAK`) och matarledningarna |
| `rum/<rum>.py` | Ett rums tappställen: typ, dosa, läge på väggen eller golvet och rörtyp |
| [`system.py`](system.py) | Allt ur rummen (`MODULER`), rören från fördelarna, kontrollen, genomföringarna och utdraget för ritningarna |
| [`vatten.py`](vatten.py) | Geometrin, ett montage per rum och ett för teknikrummet under `Hus/Installationer/Vatten` |

Teknikrummets utrustning (värmepumpen med varmvattenberedaren, fördelarskåpet, vattenmätaren och golvvärmens
fördelare) är gemensam för vattnet och värmen: [`../teknikrum.py`](../teknikrum.py), montaget
`Hus/Installationer/Teknikrum`, som ingår i modellens krockkontroll. Lägena på husets ytor
([`../montering.py`](../montering.py): `vagg`, `golv`, `kallarvagg`, `i_vaggen`) och genomföringarna
([`../genomforingar.py`](../genomforingar.py)) är gemensamma med el och ventilation.

## Begreppen

- **Tappställe** (`Tappstalle`): det som förbrukar vatten, med id `<rum>-<typ><n>` (t.ex. `BA-DU1`), typen med
  normflöden, anslutningen (väggdosa i väggen eller golvdosa i golvet), läget och rörtypen. Kallvattnet ansluter till
  höger och varmvattnet till vänster sett mot dosan; golvdosornas riktning från varmt till kallt är `kallt`.
- **Fördelare** (`Fordelare`): kallvattnets och varmvattnets stammar i fördelarskåpet, med numrerade utgångar uppåt;
  utgång 0 och utgången efter den sista är stammens ändar (inlopp och genomgång).
- **Rör** (`Ror`): från en fördelares utgång (`FD-KV:3`), en utrustning (`TK-VP:VV-ut`) eller ett tappställe till ett
  annat. Rören till tappställena har tappställets id och media (`BA-DU1-VV`) och dras ur stråken (`ror`);
  matarledningarna i teknikrummet (`VA-KV1` …) har sina brytpunkter i `teknikrum.py`.
- **Stråk** (`Strak`): en gemensam väg i mellanbjälklaget med en fil per tappställe, från fördelarskåpet. Filen går
  genom fördelarnas utgång (samma nummer på kallt och varmt): stråket förskjutet i sidled genom utgången.

## Dragningen

- Rören går ur fördelarskåpets öppna ovansida upp i mellanbjälklaget och gjuts in mellan armeringsnäten (R-06), i
  stråken: varmvattnet överst och kallvattnet under det i samma läge. Varmvattnets fördelare sitter bakom
  kallvattnets, så att den bakre radens rör går över den främre radens.
- Utgångarnas ordning (`UTGANGAR`, från söder) bestämmer filerna: rören viker av åt det håll där deras fil ligger
  ytterst, utan att korsa varandra. Stråket O går söderut väster om skåpet och österut till källarrummet och köket, S
  västerut och söderut till badrummet och V7, och V västerut och söderut längs V21.
- Röret lämnar filen i punkten närmast tappstället (eller förbi `via`) och går därifrån upp ur bjälklaget i väggens
  regelfack eller golvdosan på plan 1, eller ned ur bjälklaget i källarväggens cellplast bakom gipsen till väggdosan i
  källaren.
- Vinkeljärnen från ytterväggarnas kärna (pos 14) och diagonaljärnen vid trapphålet ligger under överkantsnätet, i
  varmvattnets nivå (`HINDER`, ur armeringen): där går varmvattnet i kallvattnets nivå, och stråken slutar utanför
  dem.

Ett tappställe flyttas i sin rummodul (läget följer väggen eller golvet). Ett nytt tappställe läggs i en rummodul (och
rummet i `MODULER`) och får en utgång i `UTGANGAR`, i den ordning där dess fil viker av utan att korsa de andra;
kontrollen visar rör som går i varandra eller mot järnen.

## Kontrollen

`./mod vatten kontroll` (fel stoppar, anmärkningar redovisas):

- utgångarna: varje tappställe har en utgång och varje utgång används en gång, inom fördelarens utgångar och ändar;
- anslutningarna: ett rör per media som tappstället har (normflöde över noll), referenserna till fördelare, utrustning
  och tappställen;
- tiden till varmvatten vid tappställets normflöde, ur volymen från beredaren (högst 10 s, BBR 6:62 och Säker Vatten;
  anmärkning över 8 s), och vattenhastigheten vid normflödet (fel över 2,5 m/s, anmärkning över 2,0 m/s);
- rören: sneda stycken, varmvatten mot järnen under överkantsnätet och rör som går i varandra;
- genomföringarna ur husets geometri: ingjutna rör ut ur bjälklagets över- och underkant, rör i väggarnas regelfack
  (syllen urtas) och i källarväggarnas cellplast (ska rymmas), hylsor eller kärnborrning där rör går genom en platta
  eller källarväggens kärna;
- krockar ur modellens geometri mot husets delar (stommen var för sig, skikten per rör) och mot elen, ventilationen
  och teknikrummets utrustning (fel).

## Ritningarna

`./mod vatten ritning` ritar serien VS-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3):

- **VS-01.1 rören i mellanbjälklaget** (1:50): stråken med varmvattnet över kallvattnet, var rören kommer ut ur
  bjälklaget (upp till plan 1, ned till källaren och fördelarskåpet) och tappställena, med plan 1:s väggar och
  källarväggarna; tabeller över tappställena, rören och genomföringarna med lägen;
- **VS-01.2 teknikrummet** (1:20): planen och vyn mot V19 med fördelarskåpet, fördelarna, rören upp i bjälklaget,
  matarledningarna, värmepumpen och ventilationens kanal.
