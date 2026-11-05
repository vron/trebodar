# Att ändra i modellen

Det som ska ändras i modellen (`modeller/trebodar`) för att den ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant), samma som modellens. Delarnas namn är modellens (Onshape-modellens namn finns i `modeller/referens/namntabell.csv`).

**När modellen är uppdaterad:** kör `./mod kontroll` i `verktyg/modellering` och kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Handlingarna (uppdateras när modellen är klar)

1. **K-01 med modellens stolplägen under nockbalk 1** (stöd B, C och D: LN1_1 y 2 795, LN1_2 4 686 och huvudstolpen
   6 602 i stället för 2 870, 4 770 och 6 670), sedan K-05:s `laster.py` och följande.
2. **K-03:s `geometri.json` efter modellen** (`kontroll_k03.py` redovisar skillnaderna): takets lyft 10 mm,
   takstolarnas diagonaler till balkens underkant, delarna fram till balkarnas sidor (balken 190 bred;
   Onshape-modellens takstolar var gjorda för HEA 200) och 2NO med 7 stavar, stolparna LN1_1 (ny), LD2_1, LD2_2 och
   LD4_2, reglarna 45–2 445, huvudstolpen med strävor på båda sidor och dalbalkarnas överkant i takplanens skärning
   (U-03).
   K-05:s `laster.STOLPLAGEN` för LD4_2: 4 438 → 4 392. Toppklossarna: en kloss per takstol, på gavelstolarnas insida
   och på mittstolen 2C:s nordöstra sida (på den sydvästra skulle den gå ut genom gipsen), så att balken vilar på 90 mm.
   Gavelstolarna klarar det med K-03:s kontroll (högst 63 %, 3SV); 2C (36,7 kN) ger 109 % med K-03:s förenklade
   kontroll och omkring 86 % med effektiv upplagslängd (+30 mm) och k_c,90 = 1,5 (EN 1995-1-1 6.1.5), som K-03 då
   ska redovisa.
3. **U-03:** texten hänvisar till en punkt i modell-todo som är gjord.
4. **R-04 mot armeringen i modellen:** R-04:s startjärn under F3:s bröstning (800) går 1 200 upp, genom bröstningen:
   korta dem till under bröstningens järn (modellen gör det), och startjärnens fördelning lägger ett järn vid F3:s kant
   (2 mm in i kärnan; modellen flyttar det 40 mm in).

## Kontrollera och bestäm

5. **Marken mot K-06.** Modellen följer Onshape-modellens mark fram till huset (användarens beslut: inga fyllningar
   eller ramper längs huset, bara entréavsatsen och sovrumsavsatsen). K-06:s fyllnadshöjder ligger högre vid V1
   (−450; marken −947 … −679), V7 och V18 (−250; sovrumsavsatsen −742 … −841 och marken −1 445), V14 (−1 450 … −450;
   marken −1 414 … −1 071), V16 (−250 … −682; marken −773) och V21 (−250; marken −1 335 … −695). K-06 ligger på säker
   sida (högre jordtryck, `kontroll_laster.py`); fyllnadshöjderna kan sänkas till marken. AR-01: fasadstenen syns ned
   till marken. Framför skjutpartiet 2SV ligger berget 600 mm under golvet (K-06 räknade med fyllning till −250);
   där står altanen (hus/altan, ärende #30), med överkanten i golvets höjd.
   Panelen följer `markniva.MARKNIVA`, som körs om med `verktyg/modellanalys/marknivaer.py` när marken ändras.
6. **Kaminöppningen i 2C.** Insatsen sitter i öppningen x 6 400–7 236 i 2C, under takstolen 2C:s topp (nockbalk 3:s
   stöd C, 36,7 kN, vid x 6 905). Överstycket är en liggande regel 45 mm över 836 mm; kontrollera lastvägen i K-03.
7. **Stolparna LN3_1 och LN5_2 står till hälften utanför balken.** Stolparna (fyra reglar 45×95 i änden av väggarna
   2A och 1D) står med 83 av 180 mm under nockbalk 3 respektive 5, som i Onshape-modellen: väggarna slutar 12 mm före
   balkens mittlinje (2A vid x 6 917, balken x 6 810–7 000; 1D vid x 2 143, balken x 2 060–2 250). K-03 räknar med att
   alla fyra reglarna bär (65 % och 82 %), men balken vilar bara på de två närmast väggen. Förslag: förläng väggarna
   102 mm (2A till x 6 815, 1D till x 2 245) så att stolparna står mitt under balkarna; K-03:s `geometri.json` och
   K-05:s `laster.STOLPLAGEN` (LN3_1 x 7 007 → 6 905, LN5_2 x 2 053 → 2 155) följer med. Annars räknar K-03 stolparna
   med två reglar och excentrisk last.
8. **Hörnstolparna LA9 och LA10 vid plattan på marks fria hörn.** Stolparna står 40 mm innanför båda de fria kanterna
   (K-05: 3,6 kN egentyngd och 6,5 kN snö, 12,8 kN dimensionerande, lyft 3,2 kN). Den yttre regeln (LA9-1, LA10-1,
   x −30…15 vid LA9) står helt utanför betongen, på L-elementens rygg av cellplast, och den inre på fasens tunna betong;
   plattan har full tjocklek först 70 mm in. Förslag: kapa L-elementens rygg vid hörnen, cirka 300 mm åt var håll, och
   gjut plattan i full tjocklek ut till plattans kant med 30 mm kantisolering utanför, som vid källarens hörn; annars
   en stålplåt under syllen som för lasten till plattan. Ytterväggarnas syll mellan hörnen står 45 mm på betongen
   (K-06 kontrollerar den även med hela lasten på ryggen).

## Köket (ärende #21)

9. **Vatten och avlopp till diskmaskinen i ön.** Diskmaskinen står i öns nordligaste skåp (O1, mitt i y 8 540, x
   11 293–11 843; hus/inredning/koksbank.py). Kallvatten (en golvdosa under diskmaskinens bakkant, från stråket O i
   mellanbjälklaget, `hus/installationer/vatten`; kallvattenfördelarens tionde utgång) och avlopp från ön till
   stammen, ingjutna i mellanbjälklaget innan det gjuts. Avloppet läses ur Onshape-modellen och måste läggas till där.
10. **El i köket.** Hällen (400 V) i skåpet B4, diskmaskinen i ön, uttag till bänken och ön
    (`hus/installationer/el/rum/kok.py`).
