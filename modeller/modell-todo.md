# Att ändra i modellen

Det som ska ändras i modellen (`modeller/trebodar`) för att den ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant), samma som modellens. Delarnas namn är modellens (Onshape-modellens namn finns i `modeller/referens/namntabell.csv`).

**När modellen är uppdaterad:** kör `./mod kontroll` i `verktyg/modellering` och kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Handlingarna (uppdateras när modellen är klar)

1. **K-01 med modellens stolplägen under nockbalk 1** (stöd B, C och D: LN1_1 y 2 795, LN1_2 4 686 och huvudstolpen
   6 602 i stället för 2 870, 4 770 och 6 670), sedan K-05:s `laster.py` och följande.
2. **K-03:s `geometri.json` efter modellen** (`kontroll_k03.py` redovisar skillnaderna): takets lyft 10 mm,
   takstolarnas diagonaler till balkens underkant och 2NO med 7 stavar, stolparna LN1_1 (ny), LD2_1, LD2_2 och LD4_2,
   reglarna 45–2 445, huvudstolpen med strävor på båda sidor och dalbalkarnas överkant i takplanens skärning (U-03).
   K-05:s `laster.STOLPLAGEN` för LD4_2: 4 438 → 4 392. Toppklossarna: en kloss per takstol, på gavelstolarnas insida
   och på mittstolen 2C:s nordöstra sida (på den sydvästra skulle den gå ut genom gipsen), så att balken vilar på 90 mm.
   Gavelstolarna klarar det med K-03:s kontroll (högst 63 %, 3SV); 2C (36,7 kN) ger 109 % med K-03:s förenklade
   kontroll och omkring 86 % med effektiv upplagslängd (+30 mm) och k_c,90 = 1,5 (EN 1995-1-1 6.1.5), som K-03 då
   ska redovisa.
3. **Plattan på mark med L-element 500 (AR-02):** K-06 (cellplast 350, fyllningen bakom V3 och V20 upp till
   makadamens underkant −650), R-05 och R-03, och K-05 och R-06: betongen slutar vid L-elementens rygg, 70 mm
   innanför konturen vid de fria kanterna.
4. **U-03:** texten hänvisar till modell-todo punkt 7, som är gjord.
5. **R-04 och R-06 mot armeringen i modellen:** R-06:s järn går ut till K-05:s kontur även vid plattan på marks fria
   kanter, där betongen slutar vid L-elementens rygg (punkt 3); modellen klipper dem där. R-04:s startjärn under F3:s
   bröstning (800) går 1 200 upp, genom bröstningen: korta dem till under bröstningens järn (modellen gör det), och
   startjärnens fördelning lägger ett järn vid F3:s kant (2 mm in i kärnan; modellen flyttar det 40 mm in).
6. **K-05:s trappa:** modellens trappa är brant (45°, 11 steghöjder à 204,5, stegdjup 202) och ryms i trapphålet,
   2,07 × 0,83 m; `laster.TRAPPA` räknar med 3,0 m (på säkra sidan).

## Kontrollera och bestäm

7. **Marken mot K-06.** Modellen följer Onshape-modellens mark fram till huset (användarens beslut: inga fyllningar
   eller ramper längs huset, bara entréavsatsen och sovrumsavsatsen). K-06:s fyllnadshöjder ligger högre vid V1
   (−450; marken −947 … −679), V7 och V18 (−250; sovrumsavsatsen −742 … −841 och marken −1 445), V14 (−1 450 … −450;
   marken −1 414 … −1 071), V16 (−250 … −682; marken −773) och V21 (−250; marken −1 335 … −695). K-06 ligger på säker
   sida (högre jordtryck, `kontroll_laster.py`); fyllnadshöjderna kan sänkas till marken. AR-01: fasadstenen syns ned
   till marken. Framför skjutpartiet 2SV
   ligger berget 600 mm under golvet (K-06 räknade med fyllning till −250): bestäm marken eller ett trädäck där.
   Panelen följer `fasad.MARKNIVA`, som körs om med `verktyg/modellanalys/marknivaer.py` när marken ändras.
8. **Kaminöppningen i 2C.** Insatsen sitter i öppningen x 6 400–7 410 i 2C, under takstolen 2C:s topp (nockbalk 3:s
   stöd C, 36,7 kN). Överstycket är en liggande regel 45 mm över 1 010 mm; kontrollera lastvägen i K-03.
9. **Fickdörrarna ID2, ID5 och ID6.** ID1, ID3 och ID4 är fickdörrar som i Onshape-modellen. De tre andras fickor i
   Onshape-modellen går genom stolpar som K-03 och K-05 lagt till efteråt: ID5:s (L1, x 10 900–11 880) genom LN1_1
   (nockbalk 1 stöd B, x 11 565–11 745), ID2:s (2B, y 5 892–6 872) genom LD2_2 (mittakstolen 2C:s stöd) och ID6:s
   (2C, x 4 417–5 617) genom LD4_1 (dalbalk 4 stöd B). De är skjutdörrar utanpå väggen tills det är bestämt. Möjligt:
   ID5 565 mm längre västerut (öppningen x 9 485–10 335, fickan till x 11 315, före LN1_1); ID2 med fickan mot söder
   och LD2_1 flyttad till fickans ände (y ≈ 4 030; K-03, K-05); ID6 bara om LD4_1 flyttas.
