# Avloppet

Badrummets och kökets avlopp som data i modellen (ärendena #52 och #49): avloppspunkterna på inredningens lägen
([`hus/badrum.py`](../../badrum.py), [`hus/inredning/koksbank.py`](../../inredning/koksbank.py)), badrummets
ledningar under mellanbjälklaget till stammen och kökets rakt ned till grundledningen under bottenplattan. Stammen
Ø110 i källarväggen KL8 öster om röret P4 och grundledningarna under bottenplattan är tills vidare Onshape-modellens
(referensdelen `avloppssystem.bbrep` i [`../installationer.py`](../installationer.py), kapad under bjälklaget i
`Z_STAM`), och resten av husets avlopp (källaren, grundledningarna och luftningen) läggs till i ärende #49.

```
cd verktyg/modellering
./mod avlopp kontroll     # fallet, att ledningarna går under bjälklaget och ansluter ovanför vattengången, den fria
                          # höjden i källaren, hålen i bjälklaget nära rören och krockarna mot husets delar och de
                          # andra installationerna
./mod avlopp lista        # ledningarna och golvbrunnen (ut/avlopp/)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`ledningar.py`](ledningar.py) | Ledningarna (rörets mitt längs vägen, dimension, vilken ledning de ansluter till), fallet, golvbrunnen, kontrollen och utdraget |
| [`avlopp.py`](avlopp.py) | Geometrin under `Hus/Installationer/Avlopp`: rören, golvbrunnen (kropp, klämring och sil) och vattenlåsen |

## Badrummet

- **Golvbrunnen** i duschen (`GOLVBRUNN` i `hus/badrum.py`): kroppen ingjuten i mellanbjälklaget med flänsen i dess
  överkant, lodrätt utlopp Ø75. Golvets fall mot den står i `hus/badrum.py` och golvet i
  [`hus/invandigt/badrumsgolv.py`](../../invandigt/badrumsgolv.py).
- **WC:n**: S-låset till ett rör Ø110 genom golvet `WC_AVLOPP` från L9 (AV1), som blir samlingsledningen.
- **Tvättstället**: vattenlåset i skåpet till ett rör Ø50 genom golvet under tvättstället (AV2).
- **Badkaret**: vattenlåset under karet till ett rör Ø50 genom golvet under karets mitt (AV3).
- **Under bjälklaget**, `UPPHANG` under betongen: samlingsledningen Ø110 norrut i WC:ns linje, under KL1:s hammarband
  genom väggen, och österut längs KL8 till stammen; tvättställets ledning längs V7 till WC:ns lodräta rör, badkarets
  och golvbrunnens till samlingsledningen.

## Köket

- **Diskhon**: avloppet i hons bakre del, `DISKHO_AVLOPP` från bakkanten (`hus/inredning/koksbank.py`), bakom
  diskbänksskåpets korta lådor (NL 350). Vattenlåset Ø40 står mellan hon och golvet, och röret Ø50 går rakt ned genom
  mellanbjälklaget, källaren (längs källarväggen V14:s gips) och bottenplattan (AV5).
- **Diskmaskinen i ön**: vattenlåset Ø40 i sockeln under skåpet O2, dit slangen går, och röret Ø50 rakt ned (AV7). Det
  står i källaren i linje med rören P1, P3 och P5, mitt emellan P3 och P1.
- **Under bottenplattan** går de med en böj till var sin gren Ø110 (AV6, AV8), vinkelrätt mot grundledningen och med
  fallet 10 ‰ till den. Grundledningen är tills vidare Onshape-modellens (`GRUNDLEDNING`, utan fall); grenarna ansluter
  med vattengången `ANSLUTNING_OVER` över dess och går därför med överkanten upp till ca 20 mm i cellplasten under
  bottenplattan.
- Kökets luftning hör till luftningen i ärende #49.

Golvvärmens slingor i mellanbjälklaget och bottenplattan går runt rören (`golvvarme/system.py`).

Fallet: Ø110 minst 10 ‰ och de mindre minst 17 ‰ (tillverkarnas anvisningar för avlopp i byggnad), lagt med `FALL`.
Hålen genom bjälklaget ligger utanför rörens genomstansningszon (6d, `GENOMSTANSNING`) utom golvbrunnens, ca 0,5 m från
P4; kontrollen redovisar hål inom den. Järnen läggs om runt hålen.

Avloppet ingår inte i modellens krockkontroll (`kontrollregler.UTOM_KONTROLL`): rören går genom golvets skikt,
bjälklagen, skåpens botten och källarväggarnas gips utan håltagning i modellen. `./mod avlopp kontroll` prövar dem
mot husets delar: stommen, skåpens lådor och de andra installationerna är fel, järnen och skikten redovisas.
