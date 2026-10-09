#let p = json("projekt.json")
#set document(title: p.objekt, author: p.upprattad)
#set page(
  paper: "a4",
  margin: (x: 18mm, top: 20mm, bottom: 16mm),
  header: context [
    #set text(8pt)
    #grid(columns: (1fr, auto), p.namn, [#p.dokument rev #p.revision · Sida #counter(page).display() av #counter(page).final().first()])
    #v(-2pt)
    #line(length: 100%, stroke: 0.4pt)
  ],
)
#set text(font: "Carlito", size: 9.5pt, lang: "sv")
#set par(justify: false, leading: 0.55em, spacing: 0.75em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  v(5pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => block(above: 8pt, below: 4pt, text(size: 9.8pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
#show figure.caption: set text(size: 8pt)
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#let D = json("data.json")
#let tab(..args) = text(size: 8.6pt, table(..args))
#let liten(..args) = text(size: 7.9pt, table(..args))

#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Betongbjälklag 150 mm på Lecaväggar och stålrör i källaren], [*Upprättad*], p.upprattad,
)

= Inledning

Handlingen redovisar mellanbjälklaget mellan källaren och plan 1: en platsgjuten betongplatta, 150 mm, som vilar på källarens Lecaväggar och på 19 stålrör VKR 80×80×4. Den del av vänstra huskroppen som saknar källare ligger på mark. Plattan bär sin egentyngd, golv, nyttig last och alla laster från trästommen på plan 1: nock- och dalbalkarnas stöd enligt K-01, ytterväggarna och taket på dem samt trappan. Kontrollerna avser böjning, genomstansning, tvärkraft, nedböjning, sprickbredd och rörens bärförmåga. Reaktionerna på Lecaväggarna och rören är underlag för grund och källarväggar (K-06).

Regler: SS-EN 1990, SS-EN 1991-1-1, SS-EN 1992-1-1 och SS-EN 1993-1-1 med EKS 12. Säkerhetsklass 2 ($gamma_d$ = 0,91), livslängd 50 år. Laster och förutsättningar enligt F-01.

*Resultat.* Plattan och rören klarar alla kontroller med armering enligt avsnitt 4. Största utnyttjande:

#tab(
  columns: (1fr, auto, auto),
  align: (left, left, right),
  table.header([Kontroll], [Var], [Utnyttjande]),
  [Böjning, underkant], [fält], [#D.uk_max],
  [Böjning, överkant, bara nät], [utanför zonerna], [#D.ok_utan],
  [Böjning, överkant, armering #D.mat.sank mm för lågt], [utanför zonerna], [#D.ok_utan_lag],
  [Böjning, överkant med tilläggsjärn], [#D.ok_zon_namn], [#D.ok_zon],
  [Genomstansning vid rören], [#D.max_stans.namn], [#D.max_stans.utn],
  [Genomstansning, överkantsarmering #D.mat.sank mm för lågt], [#D.max_lag.namn], [#D.max_lag.utn],
  [Lokalt tryck under röret (6.7)], [#D.lokal.namn], [#D.lokal.utn],
  [Genomstansning under stolpar på plattan (−#D.mat.sank mm)], [#D.stolp_max.namn], [#D.stolp_max.lag],
  [Tvärkraft vid väggändar], [#D.andar.at(0).vagg], [#D.andar.at(0).utn],
  [Tvärkraft längs väggar], [#D.langs.vagg], [#D.langs.utn],
  [Nedböjning, EC2 7.4.3 ($L slash 250$)], [], [#D.ned.utn],
  [Nedböjning, helt sprucken ($L slash 250$)], [], [#D.ned.utn2],
  [Sprickbredd ($w_"max"$ = 0,4 mm)], [], [#D.spr_max mm],
  [Böjning vid vindlyft], [], [#D.lyft.utn],
  [Knäckning, rör VKR 80×80×4 S235], [#D.max_pel], [#D.max_knack],
)

= Husets geometri

#figure(placement: auto,
  image("../fig_geometri.svg", width: 96%),
  caption: [Mellanbjälklaget i plan med källarens Lecaväggar V1–V21 och rören P1–P19, mm. Måtten avser plattan, origo i plattans nedre vänstra hörn.],
)

Trapphålet är 2 070 × 828 mm. Källarväggarna är Leca 350: Leca 100 + isolering 150 + Leca 100. Plattan gjuts ut till 30 mm från Lecans ytterliv; där utanför ligger kantisolering. Plattans kontur, trapphålet, Lecaväggarna och rören har de exakta lägena i husets Onshape-modell. Rören vid trapphålet (P6, P7, P13, P14) står #D.yta.ror_hal mm från hålkanten (rörets centrum). Rören är 2,1 m långa från bottenplattan till mellanbjälklagets underkant. Den del av vänstra huskroppen som saknar källare, #D.yta.mark m² av plattans #D.yta.tot m², ligger på cellplast på mark. Riktningar (övre, nedre, vänster, höger) avser figur 1.

= Laster

== Utbredda laster

#tab(
  columns: (1fr, auto, 1fr),
  align: (left, right, left),
  table.header([Last], [kN/m²], [Referens]),
  [Betong 150 mm, 25 kN/m³], [#D.enh.g_betong], [SS-EN 1991-1-1 tabell A.1],
  [Golvuppbyggnad (trägolv; klinker i våtrum)], [#D.enh.g_golv], [F-01],
  [*Permanent last $g_k$*], [*#D.enh.gk*], [],
  [Nyttig last, kategori A], [#D.enh.q], [EKS tabell C-1],
  [Lätta mellanväggar], [#D.enh.qv], [SS-EN 1991-1-1 6.3.1.2(8), F-01],
)
Lätta mellanväggar räknas som nyttig last i brottgränstillstånd, som 6.3.1.2(8) anger, och som permanent last i bruksgränstillstånd (på säker sida). Mellanväggar på plan 1 som inte bär tak, även väggen kring trappan, ingår i 0,7 kN/m².

== Laster från trästommen

Lasterna förs ned från taket på samma sätt som i trästommens beräkning:

- *Nock- och dalbalkar:* stödreaktioner enligt K-01. $R_d$ är K-01:s största dimensionerande reaktion (6.10b). Den delas upp i $G_k$ och $S_k$ i samma förhållande som balkens last i K-01: nockbalk 2,01 + 3,75 kN/m, dalbalk 1,93 + 7,13 kN/m. K-01:s största reaktion kommer från fältvis snö eller fritt upplagda fält, där snöns andel är minst lika stor som i lastförhållandet. Uppdelningen ger därför rätt $R_d$ med snö som huvudlast och på säker sida för övriga kombinationer och för bruksgränstillstånd, som får för stor $G_k$-andel. $W_d$ är K-01:s minsta reaktion vid vindlyft, $1,0 G + gamma_d 1,5 W$.
- *Gavlar:* nockbalkens ände vilar på gaveltakstolen, som för hälften var till de två hörnstolparna LA1–LA10, eller till dalbalkens ände (LD2_4, LD4_2). Hörnstolpen bär också takstolens egen takremsa, (#D.enh.cc/2 + #D.enh.utspr) m × (nock–takfot + #D.enh.utspr) m, och takstolens egentyngd #D.enh.takstol kN.
- *Mittakstolen* i mittre huskroppen för nockbalk 3:s stöd C till LD2_2 och LD4_1, hälften till var.
- *Dalbalk 2* vilar på en bärande vägg på plan 1 (träregelverk med gips på båda sidor). Väggens reaktion enligt K-01 ger linjelasten qD2 och LD2_3 vid väggänden. Väggens egentyngd, #D.enh.g_vagg kN/m² × #D.enh.h_vagg m, läggs till qD2. Vid trapphålet har väggen en dörröppning mot trappan, och karmstolparna LD2_1 och LD2_2 står direkt intill hålets långsidor (upplagsyta 95 × 90 mm). LD2_2 bär också den del av väggen som K-01 fördelar över hålet och halva nockbalk 3:s stöd C.
- *Takfotsväggar:* takbalkarna (c/c #D.enh.cc m) vilar på hammarbandet. Väggen bär halva takbalkens horisontella längd plus takutsprånget #D.enh.utspr m: #D.enh.t_sida m i vänstra och högra huskroppen, #D.enh.t_mitt m i mittre.
- *Ytterväggarnas egentyngd* #D.enh.g_vagg kN/m² väggyta (fönster räknas som vägg). Höjd #D.enh.h_vagg m till takfot. Gavelväggar dessutom gavelspetsen upp till taket ($#D.enh.vinkel degree$).
- *Trappan* (trä) hänger med halva sin vikt på trapphålets kortsida. Trappan har #D.enh.tr_l m horisontell längd och #D.enh.tr_b m bredd, egentyngd #D.enh.tr_g kN/m² och nyttig last #D.enh.tr_q kN/m² i plan. Vilken kortsida som bär är inte bestämt, så lasten läggs på båda.
- *Stolpar:* stolparna redovisas i K-03 och räknas här med minst ytan av 2 st 45×95. Stolpe B (LD4_1, över P10) är #D.stB.stolpe×#D.stB.stolpe GL30h (K-03) och står på en fotplåt #D.stB.L × #D.stB.B × #D.stB.t mm, S355, förankrad i plattan. Dalbalk 4:s centrumlinje ligger #D.stB.havarm mm från stolpens centrum, mittakstolen centriskt. Med dagens laster blir excentriciteten $e$ = #D.stB.e mm och momentet #D.stB.M kNm (dimensionerande). Lasten läggs med den excentriciteten, bort från röret. LN1_1 står 250 mm från P17, i väggen vid y ≈ 2 795.

Ytterväggarnas stomme, 95 mm, står från 30 mm utanför till 65 mm innanför plattans kant, med centrum #D.enh.vagg_in mm innanför kanten, alltså ovanför Lecaväggens yttre skikt. Plattan vilar på båda skikten. I modellen läggs lasterna över en Lecavägg på väggens upplagslinje i det inre skiktet, där de inte böjer plattan men ingår i väggens reaktion (avsnitt 6.1). Den förenklingen är kontrollerad med en modell där också det yttre skiktet bär (bara tryck) och lasterna står där de står. Största stödmoment intill lasterna över väggarna blir då #D.ytter.med kNm/m mot #D.ytter.utan kNm/m (före faktorn #D.mat.konv), inom zon #D.ytter.zon. Zonens tilläggsjärn dimensioneras för #D.mat.zonf × det större värdet. Övriga resultat ändras inte. Det yttre skiktet tar då #D.ytter.Y kN av lasten med snö som huvudlast, vilket K-06 ska ta hänsyn till. Största last som står över en vägg är LD4_2, 44 kN dimensionerande. Spridd genom plattan (45°) till båda skikten ger den cirka 0,6 MPa på Lecan, som kontrolleras i K-06. Över källarens öppningar (fria kanter) och på marken verkar lasterna på plattan.

#tab(
  columns: (1fr, auto, 1fr),
  align: (left, right, left),
  table.header([Last], [Värde], [Referens]),
  [Takets egentyngd per m² takyta], [#D.enh.g_tak kN/m²], [F-01 (57 kg/m²)],
  [d:o per m² horisontell yta, takvinkel #D.enh.vinkel°], [#D.enh.g_tak_h kN/m²], [],
  [Snö, formfaktor 1,0 (på säker sida mot 0,8)], [#D.enh.s kN/m²], [F-01, K-01],
  [Ytterväggens egentyngd per m² väggyta], [#D.enh.g_vagg kN/m²], [antaget, på säker sida],
  [Takutsprång vid takfot och gavel], [#D.enh.utspr m], [],
)

#figure(placement: auto,
  image("../fig_laster.svg", width: 92%),
  caption: [Laster från plan 1. Punktlasterna heter efter balken de kommer från (LN1_1 = nockbalk 1, första stolpen räknat från balkens början vid lägst y), LA1–LA10 är hörnstolpar. Linjelaster: ytterväggar qY1–qY12, dalbalk 2 via vägg qD2, trappan qT.],
)

#text(size: 9pt)[*Punktlaster.* Karakteristiska värden $G_k$ och $S_k$, dimensionerande $R_d = 0,91 (1,2 G_k + 1,5 S_k)$ och vindlyft $W_d$ (kN). Lägen i mm.]
#liten(
  columns: (auto, 1fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right, left),
  table.header([Last], [Ursprung], [x], [y], [$G_k$], [$S_k$], [$R_d$], [$W_d$], [Står på]),
  ..D.punkter.map(r => ([#r.namn], [#r.delar], [#r.x], [#r.y], [#r.Gk], [#r.Sk], [#r.Rd], [#r.Wd], [#r.plats])).flatten(),
)

#text(size: 9pt)[*Linjelaster.* $g_k$ och $s_k$ i kN/m; gavelväggarnas $g_k$ varierar med gavelspetsens höjd. Summa $G_k$ och $S_k$ för hela väggen i kN.]
#liten(
  columns: (auto, 1fr, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, right, right, right, left),
  table.header([Last], [Vägg], [Läge (mm)], [$g_k$], [$s_k$], [$Sigma G_k$], [$Sigma S_k$], [Står på]),
  ..D.vaggar.map(r => ([#r.namn], [#r.text], [#r.str], [#r.gk], [#r.sk], [#r.G], [#r.S], [#r.plats])).flatten(),
  [qD2], [dalbalk 2 via bärande vägg], [x = #D.qD2.x, y #D.qD2.str], [#D.qD2.gk], [#D.qD2.sk], [], [], [plattan],
  [qT], [trappan, hålets kortsidor], [x = #D.qT.x], [#D.qT.gk], [$q_k$ #D.qT.qk], [], [], [plattan],
)
Vindlyft på dalbalk 2:s vägg: #D.qD2.wd kN/m längs qD2 (K-01: −18,6 kN för hela väggen). Totalt från plan 1: $G_k$ = #D.tot.ovanG kN och $S_k$ = #D.tot.ovanS kN. Snölasten är större än snö på hela taket, #D.snotak kN, eftersom K-01 räknar med att snön samlas i dalarna och med 2,5 m lastbredd för nockbalkarna (på säker sida).

== Lastkombinationer

Brottgränstillstånd enligt EKS:
- 6.10a: $0,91 dot 1,35 G + 0,91 dot 1,5 (0,7 Q + 0,6 S)$
- 6.10b: $0,91 dot 1,2 G + 0,91 dot 1,5 Q + 0,91 dot 1,5 dot 0,6 S$
- 6.10b: $0,91 dot 1,2 G + 0,91 dot 1,5 dot 0,7 Q + 0,91 dot 1,5 S$

$Q$ omfattar nyttig last, lätta väggar och trappans nyttiga last. Den läggs på hela plattan, i schackmönster och i rader (25 fält om cirka 2,8 × 3,2 m), och snön ligger på alla huskroppar, på en eller två av dem eller inte alls (ojämn snö mellan huskropparna; dalbalkarnas snö delas lika mellan de två huskroppar de bär från). K-01:s reaktioner ger redan största snö på varje balk, med snöficka i dalarna. Vid vindlyft gäller $1,0 G_"platta" + W_d$, där $G_"platta"$ är plattans egentyngd och golvet. Bruksgränstillstånd: kvasipermanent $G + 0,7 + 0,3 Q + 0,1 S$ och karakteristisk $G + 0,7 + Q + S$ (EKS tabell B-1: $psi_2$ = 0,3 för nyttig last och 0,1 för snö).

= Plattans utformning

#figure(image("../fig_tvarsnitt.svg", width: 70%), caption: [Plattans tvärsnitt, mm. x-järnen ligger ytterst i båda näten.])

#tab(
  columns: (auto, 1fr),
  align: (left, left),
  table.header([Del], [Utförande]),
  [Betong], [C25/30, exponeringsklass XC1. $f_"ck"$ = #D.mat.fck MPa, $f_"cd"$ = #D.mat.fcd MPa ($alpha_"cc"$ = 1,0), $f_"ctm"$ = #D.mat.fctm MPa, $E_"cm"$ = #D.mat.Ecm GPa],
  [Armering], [B500B, $f_"yd"$ = #D.mat.fyd MPa],
  [Underkant], [Nät #D.mat.nat_uk i båda riktningarna, täckskikt #D.mat.c_uk mm. Minst två underkantsjärn i vardera riktningen passerar över varje rör (9.4.1(3)); där nätet inte gör det läggs 2 Ø10, L = 1,2 m],
  [Överkant], [Nät #D.mat.nat_ok i båda riktningarna, täckskikt #D.mat.c_ok mm],
  [Tilläggsjärn i överkant], [Zonerna #D.zon_namn.join(", ") enligt figur 4, i nätets lager, båda riktningarna],
  [Hörn], [2 Ø10, L = 1,2 m, diagonalt i överkant vid plattans inåtgående hörn och trapphålets hörn],
  [Fria kanter], [Båda näten går ut till kanten (öppningarna i källarväggen och trapphålet); nätet är kantarmering enligt 9.3.1.4(2)],
  [Rör], [VKR 80×80×4 S235, kallformade (SS-EN 10219), L = 2,1 m. Topplåt 80×80×8 svetsas på röret, som gjuts in kant i kant med plattans undersida. Ingen huvudplåt. #for r in D.plat [#r.namn: topplåt #r.b × #r.b × #r.t mm S#r.fy, centrerad på röret. ]],
)

*Täckskikt* (4.4.1, EKS tabell D-1): XC1 och 50 år ger $c_"min,dur"$ = 10 mm, $c_"min,b"$ = stångens diameter och $Delta c_"dev"$ = 10 mm, alltså $c_"nom"$ = 20 mm. Underkanten har 20 mm. Överkanten har 25 mm, vilket ger 5 mm marginal för glättning eller slipning. Brand R30 kräver axelavstånd 10 mm (SS-EN 1992-1-2 tabell 5.9).

#figure(placement: auto,image("../fig_armering.svg", width: 76%),
  caption: [Tilläggsjärn i överkant och diagonaljärn. Zonerna omfattar området där nätet inte räcker plus 0,4 m förankring, och 1,5 × 1,5 m kring rör som behöver mer armering för genomstansning eller där tillägg föreskrivs (P7, P14, P17).])

#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, 1fr),
  align: (left, right, right, right, left, right, right, left),
  table.header([Zon], [x (m)], [y (m)], [Storlek (m)], [Tillägg], [$M_"Ed"$], [$M_"Rd"$], [Orsak]),
  ..D.zon.map(r => ([#r.namn], [#r.x], [#r.y], [#r.mat], [#r.jarn], [#r.MEd], [#r.MRd], [#r.orsak#if r.ror != "" [, #r.ror]])).flatten(),
)
Moment i kNm/m; $M_"Rd"$ med nät och tilläggsjärn.

= Beräkningsmetod

Plattan räknas linjärelastiskt med finita element: DKT-plattelement, cirka 35 000 element, grundnät 200 mm som förfinas till 50 mm vid rören, 60 mm vid stolparna på plattan och 80 mm vid väggändar och hörn. Geometrin är den i figur 1.

- *Lecaväggar:* fritt upplag längs upplagslinjer. Ytterväggarnas linje ligger 75 mm in från väggens insida (5.3.2.2), innerväggarnas i väggens mitt.
- *Rör:* fjädrar med rörets axialstyvhet $E A slash L$ över 200 × 200 mm (röret och plattans lastspridning). Rören räknas också som helt styva, och som helt styva med Lecaväggarna som fjädrar ($E t slash h$ med $E$ = 2 000 MPa, inre skiktet 100 mm, höjd 2,6 m). Mjuka rör ger störst moment i plattan, styva rör med fjädrande väggar störst rörlaster (#D.vaggfall.namn #D.vaggfall.vagg kN mot #D.vaggfall.styv kN med stela väggar). Alla resultat är det ogynnsammaste av de tre; väggarnas reaktioner tas ur modellerna med stela väggar.
- *Plattan på mark:* bädd med bäddmodulen 0,01 N/mm³ ($E slash t$, till exempel 400 mm cellplast med $E$ = 4 MPa). En mjuk bädd ger störst moment i plattan. Med 0,02 och 0,05 N/mm³ minskar stödmomentet vid hörnet mellan plattan på mark och källaren; övriga resultat ändras inte. Cellplastens tjocklek och tryckklass bestäms i K-06.
- *Laster:* utbredda laster på element, punktlaster i noder, linjelaster längs nätets linjer. Laster över Lecaväggar läggs på närmaste upplagslinje.
- *Moment:* dimensionerande moment enligt Wood–Armer, med toppar utjämnade över #D.mat.band mm (ungefär 2$d$) tvärs momentets riktning. EC2 ger ingen uttrycklig regel för att jämna ut toppar i en FE-lösning. Bredden är därför vald så liten att den bara tar bort de lokala topparna under punktlaster och vid stödens kanter (lastytans bredd plus ungefär plattans tjocklek), utan att räkna med omfördelning enligt 5.5 eller 5.6. Stödmomenten i överkant multipliceras med #D.mat.konv när zonerna avgränsas, och tilläggsjärnen dimensioneras för #D.mat.zonf × FE-värdet, eftersom stela upplagslinjer ger nätberoende toppar vid väggändarna (se kontroll av modellen nedan). Böjning: $M_"Rd" = A_s f_"yd" (d - 0,4 x)$, $x = A_s f_"yd" slash (0,8 f_"cd")$.
- *Genomstansning* (6.4): $v_"Rd,c" = 0,18 slash gamma_c dot k (100 rho_l f_"ck")^(1 slash 3) >= v_"min" = 0,035 k^(3 slash 2) f_"ck"^(1 slash 2)$, $k = 1 + sqrt(200 slash d) <= 2$.
  - Varje rör och varje stolpe på plattan kontrolleras för sig med hela sin last på sitt eget kontrollsnitt $u_1$, 2$d$ från den belastade ytan: $v_"Ed" = beta V_"Ed" slash (u_1 d)$, $beta$ = 1,15 (1,4 inom 2$d$ från trapphålet). Ingen avlastning från närliggande laster och ingen förhöjd bärförmåga för närmare snitt räknas.
  - Inom 6$d$ från trapphålet dras den del av $u_1$ bort som ligger mellan tangenterna från rörets mitt till hålet (6.4.2(3)).
  - $rho_l$ och $d$ tas ur överkantsarmeringen (nät och tillägg), som är svagare än underkantsnätet. Det täcker båda riktningarna för kraften genom snittet; vid rör med en stolpe ovanpå är den dimensionerande nettokraften ofta nedåt (dragen underkant).
  - För rören är $v_"Ed"$ dessutom minst FE-modellens största tvärkraft längs snittet, medelvärde över längden $d$, delat med $d$. Det täcker ojämn fördelning och moment som förs över i plattan, t.ex. av närliggande stolpar och linjelaster (rören är ledade och tar inget moment). Där en stolpes lastyta ligger inom 2$d$ från röret går rörets snitt genom eller intill stolpens lastyta, där tvärkraften i FE-modellen är singulär. Där tas FE-tvärkraften längs snittet 2$d$ runt röret och stolpen tillsammans: #D.gemensam.
  - Den belastade ytan är topplåten. För en topplåt som är större än röret räknas bara den effektiva bredden enligt SS-EN 1993-1-8 6.2.5, $c = t sqrt(f_y slash (3 f_"jd"))$ utanför rörets liv, med $f_"jd" = 2 f_"cd"$ (största möjliga värde, ger minst yta).
  - Som information redovisas nettokraften genom rörens snitt ur jämvikt (rörets reaktion minus lasterna inom snittet). Den visar hur mycket av en stolplast som går direkt ned i röret men används inte i kontrollen. För rören utan hål och utan stolpe inom 2$d$ stämmer den med tvärkraften som integreras ur FE-modellen (kvot #D.kn.min–#D.kn.max).
  - Vid rörets kant gäller $v_"Ed,0" = beta V_"Ed" slash (u_0 d) <= 0,4 nu f_"cd"$ med hela rörlasten.
  - Varje rör och stolpe ska ha minst 5 % marginal och klara sig om överkantsarmeringen ligger #D.mat.sank mm för lågt. Med lägre armering ritas snitten om för den mindre höjden. Annars läggs tilläggsjärn, 1,5 × 1,5 m. Vid P7, P14 och P17 läggs Ø10 s150 i överkant oavsett beräkningen. Samma krav på −#D.mat.sank mm gäller böjning i överkant.
- *Tvärkraft* ur momentfältets lutning, integrerad längs kontrollsnitt. Vid väggändar räknas sista 0,5 m av upplagslinjen som belastad yta med snitt 2$d$ utanför ($v_"Ed" = 1,15 V slash (u d)$). Längs väggarna används snitt $d$ från väggens insida i bitar om 1 m, mot $v_"min" d$.
- *Nedböjning* enligt 7.4.3 för kvasipermanent last, element för element och i båda riktningarna. Krökningen interpoleras mellan osprucket och sprucket tvärsnitt, $1 slash r = zeta slash r_"II" + (1 - zeta) slash r_"I"$ med $zeta = 1 - 0,5 (M_"cr" slash M)^2$. $E_"c,eff" = E_"cm" slash (1 + phi)$ = #D.ned.Eeff GPa ($phi$ = #D.ned.phi, RH 50 %, belastning efter 28 dygn) och krympkrökning med $epsilon_"cs"$ = #D.ned.ecs ‰ (bilaga B). Alla armeringslager ingår. Som försiktig gräns räknas plattan också helt sprucken med karakteristisk last och $phi$ = 3 utan krympning. Den metoden återger SINTEF:s tabeller (avsnitt 7).
- *Sprickbredd* enligt 7.3.4 för kvasipermanent last och moment utan utjämning.
- *Vindlyft:* rören är inte förankrade i plattan. Ett rör som får drag räknas som borttaget, och lyftfallet räknas om.

*Kontroll av modellen.* FE-programmet ger samma resultat som kända lösningar:
- fritt upplagd kvadratisk platta (Navier), avvikelse under 0,1 %;
- oändlig platta på pelarnät (Timoshenko), 0,00580 mot 0,00581 $q a^4 slash D$;
- strimla med sprickbildning och krympning, samma som handintegrering.

Summan av reaktionerna är lika med lasten (G #D.jv.G kN, S #D.jv.S kN). #D.konv Med mjuka rör blir väggarna V17 och V19 nästan obelastade (plattan kan lyfta från dem). Räknade utan de väggarna ändras momenten mindre än 0,1 kNm/m och rörlasterna högst 2 kN.

= Resultat

== FE-beräkning

#figure(placement: auto,image("../fig_moment.svg", width: 100%),
  caption: [Dimensionerande moment i brottgränstillstånd, utjämnade över #D.mat.band mm (överkant × #D.mat.konv), omhyllande för alla kombinationer och de tre stödvarianterna (avsnitt 5). Heldragen linje: nätets bärförmåga. Streckat: zoner med tilläggsjärn.])

*Böjning.*
#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right),
  table.header([Läge], [Armering], [$d$ (mm)], [$A_s$ (mm²/m)], [$M_"Ed"$ (kNm/m)], [Topp (kNm/m)], [$M_"Rd"$ (kNm/m)], [Utn.]),
  ..D.boj.map(r => ([#r.lage], [#r.arm], [#r.d], [#r.As], [#r.MEd], [#r.topp], [#r.MRd], [#r.utn])).flatten(),
)
Topp: största moment utan utjämning, direkt under en stolpe. Det är en lokal topp i FE-lösningen på en sträcka som är kortare än plattans tjocklek. Utjämnat över #D.mat.band mm är utnyttjandet #D.uk_max. I överkant är största moment utanför zonerna #D.ok_utan_M kNm/m: #D.ok_utan av nätets bärförmåga och #D.ok_utan_lag om armeringen ligger #D.mat.sank mm för lågt ($M_"Rd"$ = #D.ok_MRd_lag kNm/m). Största moment i en zon är #D.ok_zon_M kNm/m (#D.ok_zon_namn) mot #D.ok_zon_MRd kNm/m med #D.ok_zon_jarn som tillägg (#D.ok_zon).

*Genomstansning vid rören* ($V_"Ed"$ i kN, spänningar i MPa):
#liten(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, right, right, right, right, right, right, right, right, right, right, right),
  table.header([Rör], [$V_"Ed"$], [Stolpe inom 4$d$], [Netto (info)], [Tillägg ök], [$u_1$ (mm)], [$beta$], [$v_"Ed"$ ($beta$)], [$v_"Ed"$ (FE)], [$v_"Rd,c"$], [Utn.], [−#D.mat.sank mm], [Rörkant], [6.7]),
  ..D.pel.map(r => ([#r.namn], [#r.VEd], [#r.stolpar], [#r.Vnet], [#r.tillagg], [#r.u1], [#r.beta], [#r.vf], [#r.vfe], [#r.vRd], [#r.utn], [#r.lag], [#r.utn0], [#r.lokal])).flatten(),
)
#text(size: 8pt)[¹ Trapphålet inom 6$d$, $u_1$ reducerad. $rho_l$ ur överkantsarmeringen. −#D.mat.sank mm: utnyttjande om överkantsarmeringen ligger #D.mat.sank mm för lågt. 6.7: lokalt tryck under topplåten (80×80#for r in D.plat [, #r.namn #r.beff×#r.beff]), $F_"Rdu" = A_"c0" f_"cd" sqrt(A_"c1" slash A_"c0")$ med spridning till högst plattans tjocklek och trapphålet.]

Kontrollen använder hela rörlasten $V_"Ed"$. Nettokraften (info) visar att det mesta av en stolplast ovanpå ett rör går direkt ned i röret. FE-fördelningen är mest ojämn vid #D.fe_beta.namn: största tvärkraft längs snittet är #D.fe_beta.kvot gånger medelvärdet $V_"Ed" slash (u_1 d)$. FE-värdet styr vid #D.fe_beta.styr. #for r in D.plat [Vid #r.namn, i trapphålets hörn, behövs topplåten #r.b × #r.b × #r.t mm S#r.fy, där den effektiva bredden är hela plåten ($80 + 2c >= #r.b$ mm). ]Tilläggsjärn i överkant vid rören: #D.pel_tillagg.join(", "). Topplåten måste vara minst #D.lokal.t mm tjock (brottlinjeteori, $f_y$ = 235 MPa); 8 mm väljs.

*Stolpe B* (LD4_1) står på en fotplåt #D.stB.L × #D.stB.B × #D.stB.t mm med $N_d$ = #D.stB.N kN och $e$ = #D.stB.e mm, alltså inom fotplåten ($e < L slash 2$), så att lasten inte ger drag i förankringen. Med tryckytan (#D.stB.L − 2$e$) × #D.stB.B = #D.stB.b1 × #D.stB.B mm blir trycket #D.stB.s MPa. Lokalt tryck enligt 6.7 med spridning till plattans tjocklek ($sqrt(A_"c1" slash A_"c0")$ = #D.stB.kf) ger #D.stB.utn. Fotplåten behöver $t >=$ #D.stB.tmin mm (utsprång från stolpen som konsol); #D.stB.t mm väljs. Förankringen ska ta vindlyftet #D.stB.Wd kN och redovisas med stolpen i K-04. Stolpens last kontrolleras för genomstansning med fotplåtens yta och, separat, rörets reaktion P10 med hela lasten.

*Stolpar på plattan* ($R_d$ i kN, spänningar i MPa), med hela lasten på eget kontrollsnitt och överkantsarmeringen:
#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right, left, left),
  table.header([Last], [$R_d$], [Yta (mm)], [$u_1$ (mm)], [$beta$], [$v_"Ed"$], [$v_"Rd,c"$], [Utn.], [−#D.mat.sank mm], [Tillägg ök], [Rör intill]),
  ..D.stolp.map(r => ([#r.namn], [#r.Rd], [#r.yta], [#r.u1], [#r.beta], [#r.vEd], [#r.vRd], [#r.utn], [#r.lag], [#r.tillagg], [#r.ror])).flatten(),
)

*Tvärkraft vid väggarna.* De fem mest belastade väggändarna:
#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right),
  table.header([Vägg], [x (m)], [y (m)], [$V$ (kN)], [$u$ (mm)], [$v_"Ed"$ (MPa)], [$v_"Rd,c"$ (MPa)], [Utn.]),
  ..D.andar.map(r => ([#r.vagg], [#r.x], [#r.y], [#r.V], [#r.u], [#r.vEd], [#r.vRd], [#r.utn])).flatten(),
)
Längs väggarna är största $v_"Ed"$ #D.langs.vEd kN/m (#D.langs.vagg) mot $v_"min" d$ = #D.langs.vRd kN/m ($d$ = #D.langs.d mm), alltså #D.langs.utn. Ingen tvärkraftsarmering behövs.

#figure(placement: auto,image("../fig_nedbojning.svg", width: 100%),
  caption: [Långtidsnedböjning (mm). Rörens hoptryckning ingår.])

*Nedböjning.*
#tab(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  table.header([Metod], [$w_"max"$ (mm)], [Styrande $w$ (mm)], [$L$ (mm)], [$L slash 250$ (mm)], [Utn.]),
  [EC2 7.4.3, kvasipermanent last], [#D.ned.wmax], [#D.ned.w], [#D.ned.L], [#D.ned.lim], [#D.ned.utn],
  [Helt sprucken, karakteristisk last, $phi$ = 3], [#D.ned.wspr], [#D.ned.w2], [#D.ned.L2], [#D.ned.lim2], [#D.ned.utn2],
)
$L$ är det kortaste avståndet mellan stöd genom punkten i x- eller y-led. Tabellen visar den punkt som har störst $w slash L$. Plattan på mark ingår inte; dess sättning i cellplasten redovisas i K-06. Plattan är osprucken i fälten under kvasipermanent last. Sättningar i grunden ingår inte (avsnitt 8).

*Sprickbredd* (kvasipermanent last, gränsvärde 0,4 mm för XC1):
#tab(
  columns: (1fr, auto, auto, auto),
  align: (left, right, right, right),
  table.header([Läge], [$M_"qp"$ (kNm/m)], [$sigma_s$ (MPa)], [$w_k$ (mm)]),
  ..D.spr.map(r => ([#r.lage], [#r.M], [#r.s], [#r.wk])).flatten(),
)
Minimiarmering (9.3.1.1): underkant #D.min.uk mm²/m (finns #D.min.uk_har), överkant #D.min.ok mm²/m (finns #D.min.ok_har). Största avstånd 2$h$ = 300 mm uppfyllt med s150.

*Rör.* VKR 80×80×4 S235 är kallformade (knäckkurva c), ledade i båda ändar och har knäcklängden 2 100 mm. Det ger $overline(lambda)$ = #D.ror.lam, $chi$ = #D.ror.chi och $N_"b,Rd"$ = #D.ror.NbRd kN (SS-EN 1993-1-1 6.3.1). Största rörlast #D.max_VEd kN (#D.max_pel) ger #D.max_knack.

*Vindlyft.* Med styva rör får #D.lyft.namn #D.lyft.Rmin kN, alltså drag. Utan #D.lyft.utan lyfter plattan #D.lyft.w mm vid röret. Största moment är då #D.lyft.ok_u kNm/m i överkant och #D.lyft.uk_u kNm/m i underkant, högst #D.lyft.utn av nätets bärförmåga. Stolparnas förankring i plattan redovisas i K-04.

*Reaktioner på Lecaväggarna* (underlag för K-06). Karakteristiska summor i kN, med det som står direkt på väggen från plan 1 inräknat. Största dimensionerande last över 1 m (eller hela väggen om den är kortare) är omhyllande för kombinationerna med full nyttig last.
#liten(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, right, right, right, right, right, right),
  table.header([Vägg], [$L$ (m)], [Typ], [$G_k$], [$Q_k$], [$S_k$], [varav plan 1, $G_k$ / $S_k$], [$G_k slash L$ (kN/m)], [max $q_d$ (kN/m)]),
  ..D.vr.map(r => ([#r.namn], [#r.L], [#r.typ], [#r.Gk], [#r.Qk], [#r.Sk], [#r.oG / #r.oS], [#r.gm], [#r.qd])).flatten(),
)
De korta väggbitarna V4, V6 och V8 bär last från stora delar av plattan och från LD2_3. Rörens reaktioner finns i tabellen för genomstansning. Lecaväggarnas egentyngd och jordtryck ingår inte här.

== Handberäkning

Rörlasterna kontrolleras med belastningsytor: varje punkt på plattan bärs av närmaste stöd (rör, upplagslinje eller mark). Lasterna från plan 1 inom ytan läggs till. $R_d$ är det största värdet av de tre kombinationerna. Moment och nedböjning kontrolleras med strimlor, $L$ = #D.hand.L m (typisk spännvidd mellan rör och väggar), $q_d$ = #D.hand.qd kN/m² (6.10b med nyttig last som huvudlast).

#tab(
  columns: (1fr, auto, auto, auto),
  align: (left, left, right, right),
  table.header([Storhet], [Handberäkning], [Hand], [FE]),
  ..D.hand.ror.map(r => ([Rörlast #r.namn], [belastningsyta #r.A m² + #r.stolpar], [#r.Rd kN], [#r.FE kN])).flatten(),
  [Fältmoment, fält utan stolplast], [fritt upplagd strimla, $q_d L^2 slash 8$], [#D.hand.Mf kNm/m], [#D.hand.FEf kNm/m],
  [Stödmoment vid inre rör], [50 % av stödmomentet inom 0,25 $L$ (9.4.1(2)): $1,3 q_d L^2 slash 8$], [#D.hand.Ms kNm/m], [#D.hand.FEs kNm/m],
  [Nedböjning, helt sprucken], [fritt upplagd strimla $5 q_k L^4 slash (384 E I_"II")$, $q_k$ = #D.hand.qk kN/m², $E I_"II"$ = #D.hand.EI2 MNm²/m], [#D.hand.w mm], [#D.hand.wFE mm],
)
FE ger större rörlaster än belastningsytorna, eftersom rörlasterna i 6.1 är det största av alla modellerna: styva rör drar till sig last från grannfälten, och med fjädrande väggar går ännu mer last till rören nära väggarna. Det är på säker sida. FE ger mindre fältmoment och nedböjning än den fritt upplagda strimlan, eftersom plattan är kontinuerlig och bär i två riktningar. Stödmomentet över inre rör (#D.hand.inre) varierar med rörens avstånd och stolplasterna. Det största FE-värdet är ungefär dubbelt så stort som regeln, eftersom FE-värdet är utjämnat över bara 250 mm och multiplicerat med 1,2. De högsta värdena ligger vid #D.hand.stod_namn#if D.hand.stod_zon [, som alla ligger i zoner med tilläggsjärn].

= Jämförelse med SINTEF

SINTEF Byggforsk 522.871 tabell 24a anger 150 mm platta för 3,0 m spännvidd i ett fält, med Ø8 s200 i underkant (B30, nyttig last 2,0 kN/m², $L slash 250$). Tabell 24b godtar 150 mm upp till 4,0 m spännvidd över flera fält. Samma platta som i tabell 24a, räknad med rapportens metoder:
- EC2 7.4.3 ger #D.sintef.w1 mm (#D.sintef.u1 av $L slash 250$ = #D.sintef.lim mm);
- den försiktiga metoden, helt sprucken med karakteristisk last och $phi$ = 3, ger #D.sintef.w2 mm (#D.sintef.u2).

Den försiktiga metoden återger alltså SINTEF:s gräns. Mellanbjälklaget har största spännvidd cirka 2,6 m, är kontinuerligt över rör och väggar och har mer armering (#D.mat.nat_uk mot Ø8 s200). Det ligger på #D.ned.utn2 med samma metod. Enligt SINTEF räcker alltså 150 mm med god marginal. Tabellerna förutsätter dock jämnt utbredd last, så punktlasterna från plan 1 (genomstansning) och väggändarna (stödmoment) kräver kontrollerna i avsnitt 6.

= Utförande och sättningar

- *Överkantsarmering:* täckskikt #D.mat.c_ok mm. Kontrollera höjden vid rören före gjutning (distanser). Genomstansning och böjning klarar att armeringen ligger högst #D.mat.sank mm för lågt.
- *Rör:* topplåt 80×80×8 svetsad på röret, så att betong inte rinner ned i röret och trycket sprids#for r in D.plat [; #r.namn: #r.b × #r.b × #r.t mm S#r.fy]. Rörens lägen enligt figur 1, ±40 mm.
- *Glidskikt* (t.ex. byggpapp) på innerväggarnas krön, så att plattan kan krympa med mindre tvång. Ytterväggarna stöds mot jordtrycket av plattan; förbindningen mellan vägg och platta redovisas i K-06.
- *Formrivning* tidigast när betongen nått cirka 70 % av $f_"ck"$ (provkroppar eller mognadsberäkning).
- *Upplag under byggtiden:* högst 5 kN/m² på plattan, punktlaster under rör eller vägg.
- *Trägolv:* limmas först när betongens relativa fuktighet är under golvlimmets gräns, mätt enligt RBK.
- *Våtrum:* sprickupptagande tätskikt (krympsprickor upp till cirka 0,2 mm).
- *Sättningar:* plattan är känslig för olika sättning mellan rör och väggar. 1 mm större sättning av alla rör än av väggarna ger tillskottsmoment cirka 22 kNm/m i överkant och 24 kNm/m i underkant (långtid, osprucket, utjämnat över 250 mm), lika mycket som momenten av lasterna. Rörens plintar och väggarnas grund utförs därför med samma cellplast (tjocklek och tryckklass) och ungefär samma långtidstryck, så att sättningarna blir likartade. Skillnaden i sättning beräknas i K-06 och jämförs med känsligheten ovan.

#pagebreak(weak: true)
#counter(heading).update(0)
#set heading(numbering: "A.1")
#show heading.where(level: 1): it => {
  v(5pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[Bilaga #counter(heading).display() #h(4pt) #it.body])
}

= Golvvärme i plattan

Golvvärmeslangarnas läge i höjdled jämförs med en tvärsnittsmodell: stationär värmeledning i 2D (finita element) genom en halv slangdelning med symmetri. Uppifrån: rumsluft 20 °C ($h$ = 10,8 W/m²K, SS-EN 1264), limmat trägolv 20 mm ($lambda$ 0,13 W/mK), betong 150 mm ($lambda$ 1,7 W/mK), källarluft ($h$ = 5,9 W/m²K, värmeflöde nedåt, $R_"si"$ = 0,17 m²K/W). Slang PE-X 17×2 mm c/c 200, vattentemperatur så att golvet ger 40 W/m² uppåt.

#figure(image("../fig_golvvarme.svg", width: 62%),
  caption: [Temperatur i tvärsnittet med slangen högt (under överkantsnätet) och lågt (på underkantsnätet), källare 20 °C.])

#tab(
  columns: (auto, 1fr, auto, auto, auto, auto),
  align: (left, left, right, right, right, right),
  table.header([Källare], [Slangens läge (centrum under ovansidan)], [Vatten (°C)], [Nedåt (W/m²)], [Andel nedåt], [Golvyta (°C)]),
  ..D.varme.map(r => ([#r.Tk °C], [#r.lage], [#r.Tw], [#r.qn], [#r.andel], [#r.Ty])).flatten(),
)
Utan isolering under plattan går mer än hälften av värmen nedåt, oavsett slangens läge. Det beror på att trägolvet ($R$ ≈ 0,15 m²K/W) har större motstånd än betongen och takytan i källaren tillsammans. Slangens läge ändrar andelen nedåt med bara 5 procentenheter (en 1D-kontroll med skiktens motstånd ger samma andelar). Värmen nedåt stannar i huset och värmer källaren. Högt lagda slangar behöver cirka 2 °C lägre vattentemperatur för samma effekt, vilket ger något bättre värmefaktor i bergvärmepumpen (storleksordning 5 %). Golvytans temperatur blir jämn i alla fall (variation under 0,5 °C). Slangar högt läggs under överkantsnätet. I zonerna med tilläggsjärn och inom 0,3 m från rören läggs de inte i armeringens lager.
