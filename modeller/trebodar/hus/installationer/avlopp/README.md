# Avloppet

Husets avlopp som en egen installation (ärendena #52 och #49): avloppspunkterna på inredningens och installationernas
lägen ([`hus/badrum.py`](../../badrum.py), [`hus/inredning/koksbank.py`](../../inredning/koksbank.py), tappvattnets
tvätthon i källaren), ledningarna från dem till stammen och grundledningen, och grundledningen under bottenplattan ut
ur huset mot förbindelsepunkten. Allt går med självfall: förbindelsepunkten ligger längre ned åt nordost, med marken
på cirka +4,5. Inget annat i modellen bygger på ledningarnas lägen utom det som ska gå runt dem: golvvärmens slingor
går runt hålen och golvbrunnarna, och källarväggen KL8:s reglar runt stammen (`kallarens_innervaggar.AVLOPPSSTAM`).

```
cd verktyg/modellering
./mod avlopp kontroll     # fallet, att ledningarna går under mellanbjälklaget och under bottenplattans cellplast och
                          # ansluter ovanför vattengången, den fria höjden i källaren, hålen i bjälklaget nära rören
                          # och krockarna mot husets delar och de andra installationerna
./mod avlopp lista        # ledningarna (ut/avlopp/)
./mod avlopp ritning      # VS-02: källarens plan med ledningarna och höjderna, stammen och luftningen i sektion
                          # (kräver STEP-filen: ./mod bygg)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`ledningar.py`](ledningar.py) | Avloppspunkterna, ledningarna (rörets mitt längs vägen, dimension, vilken ledning de ansluter till), grundledningen, fallet, kontrollen och utdraget |
| [`avlopp.py`](avlopp.py) | Geometrin under `Hus/Installationer/Avlopp`: rören, golvbrunnarna (kropp, sil och i badrummet klämring), stammens rensning, luftningshuven och vattenlåsen |

## Badrummet

- **Golvbrunnen** i duschen (`GOLVBRUNN` i `hus/badrum.py`): kroppen ingjuten i mellanbjälklaget med flänsen i dess
  överkant, lodrätt utlopp Ø75. Golvets fall mot den står i `hus/badrum.py` och golvet i
  [`hus/invandigt/badrumsgolv.py`](../../invandigt/badrumsgolv.py).
- **WC:n**: S-låset till ett rör Ø110 genom golvet `WC_AVLOPP` från L9 (AV1), som blir samlingsledningen.
- **Tvättstället**: vattenlåset i skåpet till ett rör Ø50 genom golvet under tvättstället (AV2).
- **Badkaret**: vattenlåset under karet till ett rör Ø50 genom golvet under karets mitt (AV3).
- **Tvätten i skåpet** (#51, förberedd för tvättmaskin och torktumlare staplade): vattenlåset utanpå L10 i nischen
  (`TVATT_AVLOPP` i `hus/badrum.py`) till ett rör Ø50 ned i väggens regelfack och genom golvet (AV21).
- **Under bjälklaget**, `UPPHANG` under betongen: samlingsledningen Ø110 söderut i WC:ns linje, under KL1:s hammarband
  genom väggen, och österut längs KL8 till stammen; tvättställets ledning längs V7 till WC:ns lodräta rör, badkarets,
  golvbrunnens och tvättens till samlingsledningen (tvättens under KL2:s hammarband genom väggen).

Hålen genom bjälklaget ligger utanför rörens genomstansningszon (6d, `GENOMSTANSNING`) utom golvbrunnens, ca 0,5 m från
P4; kontrollen redovisar hål inom den. Järnen läggs om runt hålen.

## Köket

- **Diskhon**: avloppet i hons bakre del, `DISKHO_AVLOPP` från bakkanten (`hus/inredning/koksbank.py`), bakom
  diskbänksskåpets korta lådor (NL 350). Vattenlåset Ø40 står mellan hon och golvet, och röret Ø50 går rakt ned genom
  mellanbjälklaget, källaren (längs källarväggen V14:s gips) och bottenplattan till en gren Ø110 (AV5, AV6).
- **Diskmaskinen i ön** (#50): pumpat avlopp (AV20). Maskinens egen pump trycker vattnet genom ett rör PEX 25 utan
  fall, ingjutet i mellanbjälklaget på tappvattnets nivå, från anslutningen i golvet under maskinen
  (`koksbank.diskmaskinens_anslutningar`) förbi tappvattnets matning till underfördelaren UF1, upp i
  diskbänksskåpet bakom lådorna (`DM_DISKBANK`), där slangen går till diskhons vattenlås (anslutning för diskmaskin,
  med en ögla under bänkskivan). Ett avlopp med självfall ryms inte mellan armeringsnäten (#49). Diskmaskinen ska
  tillåta `DM_SLANG` m avloppsslang.

## Stammen och grundledningen

- **Stammen** Ø110 står i källarväggen KL8 (AV7) under badrummets vägg L11, från toppen (`Z_STAM`) ned genom
  bottenplattan, och går med en böj och en kort sträcka norrut till grundledningen. Rensningen sitter `RENSNING` över
  källargolvet, med locket genom KL8:s gips mot teknikrummet.
- **Grundledningen** Ø110 (AV8) under bottenplattan börjar i golvbrunnen GB1 vid tvätten, går österut genom GB2 i
  teknikrummet, norr om köldbärarens rör där de går upp genom plattan, och därifrån rakt mot nordost ut under
  källarväggen V9 (`UTLOPP`). Direkt utanför väggen faller den brant under dräneringen runt grunden (`UTLOPP_FALL`) och
  fortsätter åt nordost, längs dagvattnets utgående rör, mot förbindelsepunkten; `UTLOPP_L` av den ritas.
- Överkanten ligger `UNDER_CELLPLAST` under bottenplattans cellplast där den börjar. Grenarna går vinkelrätt mot den,
  de nära varandra något förskjutna (minst `GREN_AVSTAND` isär), och ansluter med vattengången `ANSLUTNING_OVER` över
  dess.

## Luftningen

Luftningen går rakt upp från stammens topp, dold i väggarna: i KL8, genom mellanbjälklaget och upp i badrummets vägg
L11 (Ø50, LU1, eftersom de lätta väggarnas stomme 70 mm inte rymmer Ø75), och från innertakets installationsskikt en
dimension större (Ø75, LU2, mot frost), isolerad genom takets isolering, ut genom taket till en luftningshuv av plåt
(`HUV`). Den står `LUFT_DY` från stammens mitt (excentrisk övergång), mellan takets ströläkt och fri från L11:s regel.
Hålet i mellanbjälklaget ligger 0,44 m från röret P4, inom dess genomstansningszon, som golvbrunnens; K-05 ska pröva
båda. `./mod avlopp kontroll` prövar luftningens väg med installationernas genomföringar (regelfacket, takbalkarna och
isoleringen); syll och hammarband urtas.

## Källaren

- **Golvbrunnarna** GB1–GB5 (`GOLVBRUNNAR_KALLARE`, efter skissen): kroppen ingjuten i bottenplattans betong med
  flänsen i dess överkant och lodrätt utlopp Ø110, GB1 och GB2 rakt ned i grundledningen och de andra med var sin
  gren. Tvättmaskinen töms i GB1 bredvid den; GB2 tar fördelarskåpets läckageindikering i teknikrummet. GB4 står vid
  tvätthoet KA-TH3 på V7, så att golvvärmens slinga ryms i rummet öster om KL2.
- **Tvätthona** (tappvattnets KA-TH1–KA-TH3, som inte är modellerade): var sin anslutning Ø50 i golvet framför
  väggdosan (`TVATTHO_AVSTAND`), rakt ned till en gren.

## Fall och nivåer

Fallet: Ø110 minst 10 ‰ och de klenare minst 17 ‰ (tillverkarnas anvisningar för avlopp i byggnad, t.ex. Pipelife),
lagt med `FALL`. Höjderna är rörets mitt i modellens z (plan 1:s golv är z 0, +8,50 i RH 2000).

Avloppet ingår inte i modellens krockkontroll (`kontrollregler.UTOM_KONTROLL`): rören går genom golvens skikt,
bjälklagen, skåpens botten och källarväggarnas gips utan håltagning i modellen. `./mod avlopp kontroll` prövar dem
mot husets delar: stommen (utom syll och hammarband för ledningarna lodrätt i väggarna, `I_VAGGEN`, som urtas), skåpens
lådor och de andra installationerna är fel, järnen och skikten redovisas. Det pumpade avloppet prövas inte för fall.
