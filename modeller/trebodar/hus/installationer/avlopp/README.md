# Avloppet

Badrummets avlopp som data i modellen (ärende #52): avloppspunkterna på inredningens lägen
([`hus/badrum.py`](../../badrum.py)) och ledningarna under mellanbjälklaget till stammen. Stammen Ø110 i källarväggen
KL8 öster om röret P4 och grundledningarna under bottenplattan är tills vidare Onshape-modellens (referensdelen
`avloppssystem.bbrep` i [`../installationer.py`](../installationer.py), kapad under bjälklaget i `Z_STAM`), och
resten av husets avlopp (köket, köksön, källaren och luftningen) läggs till i ärende #49.

```
cd verktyg/modellering
./mod avlopp kontroll     # fallet, att ledningarna går under bjälklaget och ansluter ovanför vattengången, den fria
                          # höjden i källaren och krockarna mot husets delar och de andra installationerna
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

Fallet: Ø110 minst 10 ‰ och de mindre minst 17 ‰ (tillverkarnas anvisningar för avlopp i byggnad), lagt med `FALL`.
Hålen genom bjälklaget ligger utanför rörens genomstansningszon (6d) utom golvbrunnens, ca 0,5 m från P4; järnen
läggs om runt hålen.

Avloppet ingår inte i modellens krockkontroll (`kontrollregler.UTOM_KONTROLL`): rören går genom golvets skikt,
bjälklaget, skåpens botten och källarväggarnas gips utan håltagning i modellen. `./mod avlopp kontroll` prövar dem
mot husets delar: stommen och de andra installationerna är fel, järnen och skikten redovisas.
