# Att ändra i modellen

Det som ska ändras i `trebodar.step` för att modellen ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant) och i Onshape (globalt): X = x − 12 147,7, Y = y − 1 292,1, Z = z + 13 939,9 (mm). Delarnas namn är modellträdets.

**När modellen är uppdaterad:** exportera till `modeller/trebodar.step` och kör kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Takstommen (K-01, K-03)

1. **Huvudstolpen LN1_3: strävor på båda sidor.** Grupperna `L3 Vert <1>`–`<4>` under nockbalk 1 (`HEA200 NV`), stolpen vid x 11 575–11 755, y 6 542–6 662 (Onshape X −573…−393, Y 5 250–5 370).
   - Lägg till fyra strävor 45×120 mot −y, spegelvända mot `R L3 VertDiag`: från stolpen vid z 2 825 upp till topregeln vid y ≈ 5 840 (Onshape Y 4 548).
   - Gör topregeln (`R L3 VertTop`) hel från y 5 842 till 7 362, alltså 1 520 mm, över stolpen.
   - Spikplåtar 100×400 som på den befintliga sidan.

2. **Stolpe B (LD4_1): GL30h 140×140.** Delen `L2M 115x115` i gruppen `L2M`, x 4 417–4 532, y 5 798–5 913 (Onshape X −7 731…−7 616, Y 4 506–4 621), z 0–2 404. Gör den 140×140 med samma centrum (4 475; 5 855).

3. **Stolpe LD4_2: 4 reglar.** Under dalbalk 4:s ände i gavelväggen `2SV`: `2SV vert [3]`, `[5]`, `[7]`, 3 st 45×95 vid x 4 370–4 505, y 10 945–11 040 (Onshape X −7 778…−7 643, Y 9 653–9 748). Lägg till en regel 45×95 bredvid, vid x 4 325–4 370 (Onshape X −7 823…−7 778), så att det blir 4 st sida vid sida, centrerade under balkänden. Flytta `2SV vert [1]` (x 4 245–4 290, Onshape X −7 903…−7 858) 35 mm så att den står tätt intill den nya, vid x 4 280–4 325 (Onshape X −7 868…−7 823).

4. **Ny stolpe LN1_1 under nockbalk 1, stöd B.** Saknas helt. 4 st 45×95 sida vid sida, x 11 565–11 745, y 2 747–2 843 (Onshape X −583…−403, Y 1 455–1 551), z 0–3 645, från bjälklaget till balkens underkant. Den står i innerväggen vid y ≈ 2 795 (gipsskivor `gyp_w_3_ev4`) och sticker ut 25 mm på var sida om väggens 70 mm.

5. **Toppklossar på alla sju takstolar.** En kloss 45 mm på var sida om toppen, lika hög som diagonalen och minst 600 mm lång. Toppen kapas plant under nock- eller dalbalken, som vilar på klossarna och diagonalerna, 135 mm. Vid `Stol L2M` vilar balken i modellen på innertakets gips; klossarna ska gå upp till balkens underkant.

   | Takstol | Topp x; y | Onshape X; Y |
   |---|---|---|
   | `Stol 1NO` | 2 155; 3 582 | −9 993; 2 290 |
   | `Stol 1SV` | 2 155; 15 907 | −9 993; 14 615 |
   | `Stol 2NO` | 6 905; −8 | −5 243; −1 300 |
   | `Stol L2M` | 6 905; 5 972 | −5 243; 4 680 |
   | `Stol 2SV` | 6 905; 11 005 | −5 243; 9 713 |
   | `Stol 3NO` | 11 655; 992 | −493; −300 |
   | `3SV` (i gavelväggen) | 11 655; 12 496 | −493; 11 204 |

6. **Kortlingar vid takfönstren.** En kortling 45×170 i öppningens mitt ovanför och nedanför varje fönster: från övre avväxlingen (`R TF t`) till nockbalken och från nedre avväxlingen till takfoten, med utsprång.

   | Fönster | Öppning x; y | Kortlingens y (Onshape Y) |
   |---|---|---|
   | TF1 | 647–1 601; 5 540–6 740 | 6 140 (4 848) |
   | TF2 | 10 237–11 191; 7 505–8 705 | 8 105 (6 813) |
   | TF3 | 647–1 601; 9 539–10 739 | 10 139 (8 847) |

7. **Nock- och dalbalkarna och takbalkarnas upplag som i K-01 och K-03.**
   - Balkarna `HEA200 NV`, `NVb`, `M`, `SEb` och `SE` är i modellen HEA 200. Modellera dem som K-01: limträ 200×170 med plåt 200×10 i över- och underkant, 200×190 totalt. Färdiga balkar med plåtar och skruvhål finns som STEP i `modeller/balkar/` och kan importeras.
   - Ta bort reglarna inuti profilen (`NN1_A` … `NN9_C`).
   - Sätt i stället en upplagsregel 45×45 längs balkens båda sidor, ovanpå underplåten.
   - Takbalkarna slutar mot balkens sida och vilar med ett hak på regeln (se K-03 figur 2).

## Källaren och grunden (K-05, K-06, R-04, R-05)

8. **Rören som VKR 80×80×4 med topplåt och fotplåt.** Alla `K Pillar [1]`–`[19]` är massiva 140 × 140. Modellera dem enligt R-05.5: rör VKR 80×80×4 från bottenplattans överkant till mellanbjälklagets underkant (z −2 250…−150), topplåt 80×80×8 ingjuten i bjälklagets underkant (z −150…−142) och fotplåt 200×200×15 ingjuten i plintens överkant (z −2 265…−2 250). Rörens mitt som i modellen nu (R-05.1, tabellen).
   - P7: `K Pillar [18]` vid (9 470; 5 950) (Onshape X −2 677,7, Y 4 657,9) står i trapphålets hörn. Lägg till ett likadant rör tätt intill i x-led, centrum (9 550; 5 950) (Onshape X −2 597,7, Y 4 657,9). Båda rören står på en gemensam fotplåt 280 × 200 × 15.

9. **P2 1,5 mm för högt.** `K Pillar [13]` vid (7 101,7; 9 154,8) (Onshape X −5 046,1, Y 7 862,7) går z −2 248,5…−148,5, mot −2 250…−150 för övriga rör. Sänk den 1,5 mm.

10. **Matkällarens bottenplatta som i resten av källaren.** `Bottenplatta matkällare`, x 4 370–9 470, y 7 490–11 040 (Onshape X −7 778…−2 678, Y 6 198–9 748). I modellen är golvet 200 mm lägre än i övriga källaren: 100 mm vid z −2 550…−2 450. Bottenplattan har samma uppbyggnad och nivå i hela källaren (K-06, R-04): överkant z −2 250, 300 mm (100 mm betong på 200 mm cellplast). Höj matkällarens golv till z −2 250, eller låt `Bottenplatta` gå igenom.

11. **Väggarnas kärnor går ihop i anslutningarna.** Där en vägg möter en genomgående vägg ligger det 200 mm cellplast (`Isoskal vägg 1`) mellan kärnorna:
    - V3 mot V19/V20 vid x 4 545, y 9 205 (Onshape X −7 602,7, Y 7 912,9): V3:s kärna (`Bkärna vägg 1`) slutar vid x 4 270, och V19/V20:s börjar vid x 4 470;
    - V15 mot V2 vid x 9 645, y 10 865 (Onshape X −2 502,7, Y 9 572,9): V15:s kärna slutar vid y 10 590, och V2:s börjar vid y 10 790.

    Kärnorna gjuts ihop (R-05.4 detalj D): skär bort cellplasten där väggarna möts, så att V3:s kärna går in i V19/V20:s och V15:s in i V2:s.

12. **Plattan på mark (plan 1): cellplast och fyllning.** Området under `Mittenplatta` vid x 0–4 545, y 9 205–15 900 (L-formen bakom V3 och V20; Onshape X −12 148…−7 603, Y 7 913–14 608). I modellen ligger berget 75 mm under plattan. Handlingarna (K-05, K-06) förutsätter 400 mm cellplast under plattan på dränerande fyllning upp till 1,7 m över bottenplattan.

13. **Fasadstenen 15 mm ut från cellplasten (AR-01).** `Beklädnad stor` och `Beklädnad liten` är 50 mm och ligger direkt på källarväggarnas cellplast. Stenen är beklädnadsgranit Bohus Grå 600–1 200 × 400 × 30/50 mm (Stengrossen): sågad baksida och kluven framsida. Enligt AR-01 ligger baksidan 15 mm utanför cellplasten (armeringsbruk och fästmassa) och framsidan 45–65 mm. Flytta beklädnaden 15 mm utåt och behåll 50 mm, så visar modellen stenens yttersta läge, 65 mm utanför cellplasten:
    - östra fasaden: cellplasten vid Onshape X = 1 692,3, stenen X 1 707,3 … 1 757,3;
    - norra fasaden: cellplasten vid Y = −322,1, stenen Y −387,1 … −337,1;
    - södra fasaden: cellplasten vid Y = 11 247,9, stenen Y 11 262,9 … 11 312,9;
    - västra fasaden (`Beklädnad liten`): cellplasten vid X = −12 177,7, stenen X −12 242,7 … −12 192,7.

    Skifthöjden är 400 mm och stenens underkant ligger 50 mm under färdig mark (stödvinkeln döljs). Stenens höjd på en stödvinkel är högst 2,0 m; vinkeln och gängstängerna behöver inte modelleras.

14. **Valfritt: bottenplattans uppbyggnad.** `Bottenplatta` är en massiv kropp, 300 mm. Enligt R-04 är den 100 mm betong på 200 mm cellplast S100, med kantbalkar och balkar under innerväggarna 450 × 200 och plintar under rören (600–1 200 mm, R-04.1), alla på 100 mm S300. Längs kanten L-element S300, höjd 300 och bredd 600 (ryggen 100, avfasad upptill), med ytterkanten i väggarnas ytterliv (= bottenplattans kant i modellen); betongen börjar 100 mm innanför, i kärnans yttre yta.

## Kontrollera och bestäm

15. **Stolparnas lägen under nockbalk 1 mot K-01.**

    | Stöd | K-01 | Modellen |
    |---|---|---|
    | B | y 2 870 | LN1_1, ny, i väggen vid 2 795 |
    | C | y 4 770 | `RL3 Ver Pin` vid 4 686 |
    | D | y 6 670 | huvudstolpen vid 6 602 |

    Skillnaden är 68–84 mm. Antingen flyttas stolparna, eller så räknas K-01 om med modellens lägen; säg till vilket.

16. **Syll utan vägg vid LN1_2.** `R L3 T2 btm`, x 10 980–13 745, y 4 651–4 721 (Onshape X −1 168…1 597, Y 3 359–3 429), ligger utan vägg och gips. Stolpen `RL3 Ver Pin` står därför fristående, och K-03 räknar den så. Finns en vägg där, modellera den.

17. **Marken mot källarväggarna.** Glipor mellan fyllning och berg vid V2 (y 10 865, x 4 545–9 645) och V16 (x 9 645, y 10 865–12 365). Ingen mark vid V9 (y 1 145, x 11 240–13 665) och V17 (x 9 165, y 145–1 145). Modellera marken där; fyllnadshöjderna i K-06 kontrolleras mot den.

18. **Valfritt: dubbel takbalk vid TF1.** Takbalken vid TF1:s sida y 6 740 (`ÅYY [6]`) är enkel, de andra fönstren har dubbla. Den räcker (K-03), men dubbel blir som de andra.

19. **Karmstolparna vid trapphålet (LD2_1, LD2_2).** Dörröppningen i dalbalk 2:s bärande vägg vid trapphålet. `R L23 vert door [1]` (x 9 370–9 440, y 5 027–5 072; Onshape X −2 778…−2 708, Y 3 735–3 780) går 12,5 mm ut över trapphålets kant (y 5 059,5). `L2M vert [1]`, `[2]`, `[4]` (x 9 212–9 370, y 5 900–5 995; Onshape X −2 936…−2 778, Y 4 608–4 703) står väster om väggens linje (x ≈ 9 405). K-05 räknar med karmstolpar 95 × 90 i väggens linje x 9 370, direkt utanför hålets långsidor (y 5 012 och 5 936). Flytta stolparna dit eller säg till om modellen är rätt.
