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

Handlingen redovisar mellanbjälklaget mellan källaren och plan 1: en platsgjuten betongplatta, 150 mm, som vilar på källarens Lecaväggar och på stålrör VKR 80×80×4. Den del av vänstra huskroppen som saknar källare ligger på mark. Plattan bär sin egentyngd, golv, nyttig last och alla laster från trästommen på plan 1: stolparna under nock- och dalbalkar och takstolar (K-01, K-03), ytterväggarna med taket samt trappan. Kontrollerna avser böjning, genomstansning, tvärkraft, nedböjning, sprickbredd och rörens bärförmåga. Reaktionerna på Lecaväggarna och rören är underlag för grund och källarväggar (K-06).

Laster, regler och förutsättningar enligt F-01.

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

Trapphålet är 2 070 × 828 mm. Källarväggarna är Leca 350: Leca 100 + isolering 150 + Leca 100. Plattan gjuts ut till 30 mm från Lecans ytterliv; där utanför ligger kantisolering. Rören är 2,1 m långa från bottenplattan till mellanbjälklagets underkant. #for d in D.dubbel [Vid #d, i trapphålets hörn, står två rör tätt intill varandra (avsnitt 4). ]Fria kanter finns vid trapphålet och vid öppningarna i källarens ytterväggar.

#figure(
  image("../fig_geometri.svg", width: 90%),
  caption: [Mellanbjälklaget i plan med källarens Lecaväggar V1–V21 och rören P1–P19, mm. Måtten avser plattan, origo i plattans nedre vänstra hörn.],
)

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

Stolparna under nock- och dalbalkarna och takstolarna redovisas i K-03 och balkarna i K-01. Stolparnas laster och lägen är desamma som där (punktlasttabellen, kolumnen Ursprung):

- *Stolpe under en balk:* balkens stödreaktion enligt K-01. $R_d$ är K-01:s största dimensionerande reaktion (6.10b). Den delas upp i $G_k$ och $S_k$ i samma förhållande som balkens last i K-01 (nockbalk 2,01 + 3,75 kN/m, dalbalk 1,93 + 7,13 kN/m). Det ger rätt $R_d$ med snö som huvudlast och ligger på säker sida för övriga kombinationer.
- *Takstolens fot:* halva lasten i takstolens topp (balkens stödreaktion) och takstolens egen takremsa, (#D.enh.cc/2 + #D.enh.utspr) m × (nock–takfot + #D.enh.utspr) m, med takstolens egentyngd #D.enh.takstol kN. Gavlarnas takstolar står på hörnstolparna LA1–LA10, utom i mittre huskroppens övre gavel, där takstolen står på dalbalkarnas ändar (LD2_4 och LD4_2). Mittakstolen står på LD2_2 och LD4_1.
- *Vindlyft* $W_d$ är K-01:s minsta reaktion, $1,0 G + gamma_d 1,5 W$. Också dalbalkarna lyfter: vid vind längs nockarna är det sug över hela taket, även i dalarna (SS-EN 1991-1-4 7.2.7 och tabell 7.4b), och med invändigt övertryck är suget större än takets egentyngd.
- *Stolparnas yta:* minst 2 st 45×95. Stolpe B (LD4_1) är #D.stB_yta GL30h (K-03) och står direkt på plattan.

Övriga laster från plan 1:

- *Dalbalk 2* vilar på en bärande vägg (qD2) med dörröppning mot trappan. Karmstolparna LD2_1 och LD2_2 står intill trapphålets långsidor (upplagsyta 95 × 90 mm), och LD2_3 är väggens ände.
- *Ytterväggarna* (qY1–qY12): egentyngd #D.enh.g_vagg kN/m² väggyta, höjd #D.enh.h_vagg m till takfot och gavelspetsen upp till taket. Takfotsväggarna bär taket till halva takbalkens horisontella längd plus takutsprånget #D.enh.utspr m: #D.enh.t_sida m i vänstra och högra huskroppen, #D.enh.t_mitt m i mittre.
- *Trappan* (trä) hänger med halva sin vikt på trapphålets kortsida (qT): #D.enh.tr_l m horisontell längd, #D.enh.tr_b m bredd, egentyngd #D.enh.tr_g kN/m² och nyttig last #D.enh.tr_q kN/m² i plan.

Ytterväggarnas stomme har sitt centrum #D.enh.vagg_in mm innanför plattans kant, ovanför Lecaväggens yttre skikt. Plattan vilar på båda skikten. I modellen läggs lasterna över en Lecavägg på väggens upplagslinje i det inre skiktet, där de inte böjer plattan men ingår i väggens reaktion (avsnitt 6.1). Om även det yttre skiktet bär, blir största stödmoment intill lasterna över väggarna #D.ytter.med kNm/m mot #D.ytter.utan kNm/m (före faktorn #D.mat.konv), inom zon #D.ytter.zon, och zonens tilläggsjärn dimensioneras för #D.mat.zonf × det större värdet. Det yttre skiktet tar då #D.ytter.Y kN av lasten med snö som huvudlast. Största last som står över en vägg är LD4_2, 44 kN dimensionerande, cirka 0,6 MPa på Lecan (K-06). Över källarens öppningar (fria kanter) och på marken verkar lasterna på plattan.

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

#figure(image("../fig_tvarsnitt.svg", width: 70%), caption: [Plattans tvärsnitt, mm. Järnen i varje nät läggs i valfri ordning.])

#tab(
  columns: (auto, 1fr),
  align: (left, left),
  table.header([Del], [Utförande]),
  [Betong], [C25/30, exponeringsklass XC1. $f_"ck"$ = #D.mat.fck MPa, $f_"cd"$ = #D.mat.fcd MPa ($alpha_"cc"$ = 1,0), $f_"ctm"$ = #D.mat.fctm MPa, $E_"cm"$ = #D.mat.Ecm GPa],
  [Armering], [B500B, $f_"yd"$ = #D.mat.fyd MPa],
  [Underkant], [Nät #D.mat.nat_uk i båda riktningarna, täckskikt #D.mat.c_uk mm],
  [Överkant], [Nät #D.mat.nat_ok i båda riktningarna, täckskikt #D.mat.c_ok mm],
  [Fria kanter], [Båda näten går ut till kanten (trapphålet och öppningarna i källarens ytterväggar); nätet är kantarmering enligt 9.3.1.4(2). Täckskikt mot kanten enligt R-03],
  [Rör], [VKR 80×80×4 S235, kallformade (SS-EN 10219), L = 2,1 m, med topplåt 80×80×8 svetsad på röret och ingjuten kant i kant med plattans undersida. #for d in D.dubbel [#d: två rör tätt intill varandra i x-led, 160 × 80 mm, vart och ett med sin topplåt. ]],
)

*Täckskikt* (4.4.1, EKS tabell D-1): XC1 och 50 år ger $c_"min,dur"$ = 10 mm, $c_"min,b"$ = stångens diameter och $Delta c_"dev"$ = 10 mm, alltså $c_"nom"$ = 20 mm. Underkanten har 20 mm. Överkanten har 25 mm, vilket ger 5 mm marginal för glättning eller slipning. Brand R30 kräver axelavstånd 10 mm (SS-EN 1992-1-2 tabell 5.9).

== Lokala förstärkningar

Utöver näten läggs (lägen på R-03.2 och R-03.3):
- *vid varje rör* minst två underkantsjärn i vardera riktningen över röret (9.4.1(3)); där nätet inte gör det läggs 2 Ø10, L = 1,2 m;
- *tilläggsjärn i överkant* i zonerna #D.zon_namn.first()–#D.zon_namn.last(), i nätets lager i båda riktningarna, där nätet inte räcker för böjning eller genomstansning, och vid P7, P14 och P17 oavsett beräkningen (tabellen);
- *diagonaljärn* 2 Ø10, L = 1,2 m, i överkant vid plattans inåtgående hörn och trapphålets hörn.

#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, 1fr),
  align: (left, right, right, right, left, right, right, left),
  table.header([Zon], [x (m)], [y (m)], [Storlek (m)], [Tillägg], [$M_"Ed"$], [$M_"Rd"$], [Orsak]),
  ..D.zon.map(r => ([#r.namn], [#r.x], [#r.y], [#r.mat], [#r.jarn], [#r.MEd], [#r.MRd], [#r.orsak#if r.ror != "" [, #r.ror]])).flatten(),
)
Moment i kNm/m; $M_"Rd"$ med nät och tilläggsjärn. Zonerna omfattar området där nätet inte räcker plus 0,4 m förankring, och 1,5 × 1,5 m kring rör som behöver mer armering för genomstansning.

= Beräkningsmetod

Plattan räknas linjärelastiskt med finita element (plattelement, cirka 35 000 element, förfinat vid rör, stolpar, väggändar och hörn) med geometrin i figur 1. Lecaväggarna är upplag längs upplagslinjer, rören fjädrar med rörets axialstyvhet, och plattan på mark ligger på en bädd (cellplasten). Tre stödvarianter räknas: verklig rörstyvhet, som ger störst moment, styva rör, och styva rör med fjädrande Lecaväggar, som ger störst rörlaster. Alla resultat är det ogynnsammaste av de tre. Metodens detaljer står i beräkningsfilerna.

Kontrollerna enligt SS-EN 1992-1-1:
- *Böjning* (6.1) med dimensionerande moment enligt Wood–Armer, utjämnade över #D.mat.band mm. Stödmomenten i överkant multipliceras med #D.mat.konv (nätets inverkan vid väggändarna), och tilläggsjärnen dimensioneras för #D.mat.zonf × FE-värdet. Varje riktning räknas med det inre armeringslagrets höjd.
- *Genomstansning* (6.4) vid varje rör och stolpe med hela lasten på eget kontrollsnitt, reducerat vid trapphålet. Dessutom *lokalt tryck* under topplåten (6.7) och tryckbrott vid rörets kant.
- *Tvärkraft* (6.2) vid väggändar och längs väggarna.
- *Nedböjning* (7.4.3) och *sprickbredd* (7.3.4) för kvasipermanent last. Som försiktig gräns räknas plattan också helt sprucken med karakteristisk last.
- *Rörens knäckning* (SS-EN 1993-1-1 6.3.1).
- *Vindlyft:* rören är inte förankrade i plattan, så ett rör som får drag räknas som borttaget.

Varje rör och stolpe ska ha minst 5 % marginal och klara sig om överkantsarmeringen ligger #D.mat.sank mm för lågt. Samma krav gäller böjning i överkant.

*Kontroll av modellen.* FE-programmet ger samma resultat som kända lösningar (fritt upplagd platta, platta på pelarnät och strimla med sprickbildning), och summan av reaktionerna är lika med lasten (G #D.jv.G kN, S #D.jv.S kN). Nätets förfining, stödens styvhet och lastvägen över Lecans två skikt är prövade i beräkningsfilerna (validering).

= Resultat

== FE-beräkning

#figure(placement: auto,image("../fig_moment.svg", width: 100%),
  caption: [Dimensionerande moment i brottgränstillstånd, utjämnade över #D.mat.band mm (överkant × #D.mat.konv), omhyllande för alla kombinationer och de tre stödvarianterna (avsnitt 5). Heldragen linje: nätets bärförmåga. Streckat: zoner med tilläggsjärn.])

#block(breakable: false)[*Böjning.*
#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right),
  table.header([Läge], [Armering], [$d$ (mm)], [$A_s$ (mm²/m)], [$M_"Ed"$ (kNm/m)], [Topp (kNm/m)], [$M_"Rd"$ (kNm/m)], [Utn.]),
  ..D.boj.map(r => ([#r.lage], [#r.arm], [#r.d], [#r.As], [#r.MEd], [#r.topp], [#r.MRd], [#r.utn])).flatten(),
)]
Topp: största moment utan utjämning, direkt under en stolpe. Det är en lokal topp i FE-lösningen på en sträcka som är kortare än plattans tjocklek. Utjämnat över #D.mat.band mm är utnyttjandet #D.uk_max. I överkant är största moment utanför zonerna #D.ok_utan_M kNm/m: #D.ok_utan av nätets bärförmåga och #D.ok_utan_lag om armeringen ligger #D.mat.sank mm för lågt ($M_"Rd"$ = #D.ok_MRd_lag kNm/m). Största moment i en zon är #D.ok_zon_M kNm/m (#D.ok_zon_namn) mot #D.ok_zon_MRd kNm/m med #D.ok_zon_jarn som tillägg (#D.ok_zon).

*Genomstansning vid rören* ($V_"Ed"$ i kN, spänningar i MPa):
#liten(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, right, right, right, right, right, right, right, right, right, right, right),
  table.header([Rör], [$V_"Ed"$], [Stolpe inom 4$d$], [Netto (info)], [Tillägg ök], [$u_1$ (mm)], [$beta$], [$v_"Ed"$ ($beta$)], [$v_"Ed"$ (FE)], [$v_"Rd,c"$], [Utn.], [−#D.mat.sank mm], [Rörkant], [6.7]),
  ..D.pel.map(r => ([#r.namn], [#r.VEd], [#r.stolpar], [#r.Vnet], [#r.tillagg], [#r.u1], [#r.beta], [#r.vf], [#r.vfe], [#r.vRd], [#r.utn], [#r.lag], [#r.utn0], [#r.lokal])).flatten(),
)
#text(size: 8pt)[¹ Trapphålet inom 6$d$, $u_1$ reducerad. $rho_l$ ur överkantsarmeringen. −#D.mat.sank mm: utnyttjande om överkantsarmeringen ligger #D.mat.sank mm för lågt. 6.7: lokalt tryck under topplåten (80×80#for d in D.dubbel [, #d 160×80]), $F_"Rdu" = A_"c0" f_"cd" sqrt(A_"c1" slash A_"c0")$ med spridning till högst plattans tjocklek och trapphålet.]

Kontrollen använder hela rörlasten $V_"Ed"$. Nettokraften (info) visar att det mesta av en stolplast ovanpå ett rör går direkt ned i röret. FE-fördelningen är mest ojämn vid #D.fe_beta.namn: största tvärkraft längs snittet är #D.fe_beta.kvot gånger medelvärdet $V_"Ed" slash (u_1 d)$. FE-värdet styr vid #D.fe_beta.styr. #for d in D.dubbel [#d står i trapphålets hörn, där kontrollsnittet blir kort. Med ett rör räcker inte bärförmågan där, men två rör tätt intill varandra ger lastytan 160 × 80 mm, och de klarar kontrollen med samma rör och topplåtar som övriga. ]Tilläggsjärn i överkant vid rören: #D.pel_tillagg.join(", "). Topplåten måste vara minst #D.lokal.t mm tjock (brottlinjeteori, $f_y$ = 235 MPa); 8 mm väljs.

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

*Vindlyft.* Med styva rör får #D.lyft.namn #D.lyft.Rmin kN, alltså drag. Utan #D.lyft.utan lyfter plattan #D.lyft.w mm vid röret. Största moment är då #D.lyft.ok_u kNm/m i överkant och #D.lyft.uk_u kNm/m i underkant, högst #D.lyft.utn av nätets bärförmåga. Stolparna förankras i topp och fot för sin lyftkraft (K-03).

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

Utförandet anges på R-03: armering, täckskikt och distanser, rörens lägen och topplåtar, glidskikt på innerväggarnas krön, formrivning och last under byggtiden.

*Sättningar.* Plattan är känslig för olika sättning mellan rör och väggar. 1 mm större sättning av alla rör än av väggarna ger tillskottsmoment cirka 22 kNm/m i överkant och 24 kNm/m i underkant (långtid, osprucket, utjämnat över 250 mm), lika mycket som momenten av lasterna. K-06 räknar grunden, Lecaväggarna, rören och mellanbjälklaget i en gemensam modell, så att skillnaden i sättning ingår, och visar att armeringen räcker.

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
