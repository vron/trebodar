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
#show math.equation: it => {
  show ",": math.class("normal", ",")
  it
}
#set heading(numbering: "1.1", supplement: [avsnitt])
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
#let A = D.sys.A
#let B = D.sys.B
#let P3 = D.platta.L300
#let P4 = D.platta.L400

#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Källarväggar av isolerade lättklinkerblock mot jord och bottenplatta på cellplast], [*Upprättad*], p.upprattad,
)

= Inledning

Handlingen redovisar källarens ytterväggar mot jord och bottenplattan. Väggarna muras av isolerade lättklinkerblock, 350 mm (100 Leca + 150 isolering + 100 Leca). Två system jämförs:
- *A:* Leca Isoblokk 35 från Leca Norge;
- *B:* LECA Isoblock 350 PUR från Benders.

För båda redovisas hur väggarna dimensioneras och armeras och hur de görs täta på ut- och insidan.

Bottenplattan är 100 mm på cellplast med kantbalkar i L-element, balkar under innerväggarna och plintar under rören. Två utföranden prövas: L300 med 200 mm hög kantbalk och L400 med 300 mm. Bottenplattan, Lecaväggarna, rören och mellanbjälklaget (K-05) räknas i en gemensam FE-modell. Därmed ingår skillnaden i sättning mellan rör och väggar, som K-05 hänvisade hit.

Regler: SS-EN 1990, SS-EN 1991-1-1, SS-EN 1992-1-1, SS-EN 1996-1-1 och SS-EN 1997-1 med EKS 12. Säkerhetsklass 2 ($gamma_d$ = 0,91), livslängd 50 år, geoteknisk kategori 1. Murverket utförs i utförandeklass II.

*Resultat.*
#tab(
  columns: (44mm, 1fr),
  align: (left, left),
  table.header([Del], [Resultat]),
  [Väggar mot jord, system A (Leca)], [Sikksakk-armering i varje liggfog. #D.nstolp.A stålstolpar: #D.stolp_vagg.A. Minsta lastfaktor #D.lamA.min.],
  [Väggar mot jord, system B (Benders)], [Bistål i varje skift i båda vangerna. #D.nstolp.B stålstolpar: #D.stolp_vagg.B. Minsta lastfaktor #D.lamB.min.],
  [Väggar, vertikal last], [Högst #D.vert.A.utn (A, #D.vert.A.namn) och #D.vert.B.utn (B, #D.vert.B.namn)],
  [Bottenplatta L300, cellplast], [S200 under balkar och plintar #P3.eps_b.utn. S300 under kantbalken vid hörnet V2/V20, 1,0 m åt båda håll, #P3.eps_3.utn. S100 under plattan #P3.eps_f.utn],
  [Bottenplatta L300, betong], [Kantbalk 450 × 200 med 2 Ø10 i under- och överkant (#P3.kant.utnM). Platta Ø6 s150 i båda lagren (#P3.falt.utn). Plintar #D.plint_bredd mm, genomstansning högst #P3.plint.max],
  [Mellanbjälklaget (K-05) med sättningar], [Överkant #P3.topp.ok och underkant #P3.topp.uk av K-05:s armering. K-05:s modell ger #P3.topp.ok5 och #P3.topp.uk5],
  [Plattan på mark (plan 1), 400 mm S100], [#P3.mark.utn],
  [Glidning], [#D.glid.utn],
)

L300 räcker med S300 under kantbalken vid ett hörn. L400 sänker cellplasttrycket under balkarna något men behövs inte för bärförmågan. System A rekommenderas: Leca har en dokumenterad regel för grundmurar av Isoblokk, och väggarna behöver bara två stolpar. Benders anvisningar för LECA Isoblock gäller väggar ovan mark, så med system B behövs fler stolpar.

= Förutsättningar

#figure(placement: auto,
  image("../fig_kallare.svg", width: 90%),
  caption: [Källaren med Lecaväggarna V1–V21, rören P1–P19, fyllningens höjd mot väggarna och stålstolparna för de två systemen. Mått i mm, samma koordinater som i K-05.],
) <fig-kallare>

- *Grund:* sprängt berg som avjämnas med makadam. Grunden dräneras runt huset, och det finns inget vattentryck mot väggar eller platta. Berget och den dränerade makadamen är inte tjälfarliga.
- *Höjder:* fri höjd #D.mat.H mm från bottenplattans överkant till mellanbjälklagets underkant (rörens längd). Mellanbjälklaget är 150 mm.
- *Fyllning:* höjden över bottenplattans överkant enligt @fig-kallare[figur]. Den är 2,0 m mot de slutna fasaderna. Mot V14 faller den från 1,8 till 0,8 m, och mot V18 och V9 från 2,0 respektive 0,8 m till noll vid fasaden med öppningarna. Bakom V3 och V20 ligger plattan på mark på plan 1 (K-05) på #D.mat.eps_mark mm cellplast. Där går fyllningen till #D.mat.hfm m och plattan räknas som ytlast, #D.mat.gmark kN/m² permanent och #D.mat.qmark kN/m² nyttig.
- *Jordtryck:* vilojordtryck, eftersom väggarna hålls i topp och botten. $K_0 = 1 - sin phi'$ = #D.mat.K0 med $phi'$ = #D.mat.fi° för dränerande krossmaterial, $gamma$ = #D.mat.gamma kN/m³. Last på marken intill väggarna är #D.mat.q kN/m² (gångyta). Inga fordon får köra närmare än 2 m, och fyllningen packas inte närmare än 1 m från väggen.
- *Användning:* källaren är uppvärmd och har golvvärme i bottenplattan.
- *Laster från plan 1 och mellanbjälklaget* enligt K-05: samma punktlaster, väggar, kombinationer och mönster för nyttig last. Laster som står över en Lecavägg sprids 60° genom väggen ned till bottenplattan. Nyttig last i källaren är 2,0 + 0,7 kN/m².
- *Kombinationer:* jordtrycket är permanent last, 6.10a med $0,91 dot 1,35$ och 6.10b med $0,91 dot 1,2$. Last på marken är nyttig last. Lecaväggarnas krympning är en påtvingad deformation med faktorn 1,0.

#tab(
  columns: (auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right),
  table.header([Material], [], [$f_k$ (MPa)], [$f_"xk1"$ / $f_"xk2"$ (MPa)], [$E$ (MPa)], [$gamma_M$]),
  [Murverk A], [Leca Isoblokk 35, 5 MPa, weber M5 (EKS tabell H-4, H-6)], [#A.fk], [#A.fxk1 / #A.fxk2], [#A.E], [#D.mat.gM],
  [Murverk B], [LECA Isoblock 350, 5 MPa, tunnfogsbruk Flexoheft], [#B.fk], [#B.fxk1 / #B.fxk2], [#B.E], [#D.mat.gM],
  [Armering i fogar], [Sikksakk (A) 500 MPa, bistål (B) räknas som 500 MPa], [], [], [], [#D.mat.gS],
  [Betong], [C25/30, B500B, täckskikt 30 mm mot cellplast och 25 mm i överkant], [], [], [], [1,5 / 1,15],
)
$gamma_M$ för murverk enligt EKS tabell H-1 (block kategori I, specialmurbruk, utförandeklass II). $E = K_E f_k$, $K_E$ = 1 000. Lecans slutliga krympning är #D.mat.svinn mm/m (deklarerat värde) och kryptalet #D.mat.kryp (SS-EN 1996-1-1 tabell 3.3).

#block(breakable: false, tab(
  columns: (auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  table.header([Cellplast], [$f_"ck"$ (kPa)], [$E_k$ (kPa)], [$f_d$ permanent], [$f_d$ med snö/nyttig], [Långtid 2 %]),
  [S100], [90], [3 000], [28], [35], [30],
  [S200], [180], [6 000], [62], [76], [60],
  [S300], [280], [9 000], [97], [118], [90],
))
Dimensionerande hållfasthet $f_d = k_r f_"ck" slash gamma_m$ med $gamma_m$ = 1,3 och $k_r$ efter lastens varaktighet (EPS-Sverige, WSP 10221233). Långtidslast vid 2 % deformation enligt tillverkaren. Styvhet i modellen: $E_k$ för korttidslast och $0,4 E_k$ för långtidslast.

= Källarväggar

== Två system

#tab(
  columns: (auto, 1fr, 1fr),
  align: (left, left, left),
  table.header([], [A: Leca Isoblokk 35 (Leca Norge)], [B: LECA Isoblock 350 PUR (Benders)]),
  [Block], [349 × 197 × 499, 100 + 150 PUR + 100, 5 MPa], [350 × 197 × 500, 100 + 150 PUR + 100, 5 MPa],
  [Bruk och fog], [weber Murmørtel M5, 10 mm fog under mark], [Flexoheft M2,5, tunnfog],
  [Armering i fogarna], [Leca Sikksakk-armering: 2 Ø5 i var sin vange, sammanbundna med diagonaler (fackverk)], [Bistål Bi 40 ob (inre vangen) och Bi 37 rf (yttre), ett i varje vange, inte sammanbundna],
  [Tillverkarens regler under mark], [Leca Teknisk håndbok, tabell 7.7a–c: Sikksakk i minst varannan fog, fyllning ≤ 2,0 m, fri höjd ≤ 2,6 m, avstivande väggar högst 6,0 m isär. SINTEF Teknisk godkjenning 20031 och Byggdetaljblad 523.133], [Benders anvisningar för Isoblock gäller väggar ovan mark. Benders källaranvisning (projekteringsanvisning LECA block, 2.6) gäller massiva LECA block med utvändig isolering],
)

Leca kräver Sikksakk-armering under mark för att vangerna ska samverka vid långvarig last. För system B finns ingen sådan förbindelse mellan vangerna. Vangerna räknas därför var för sig, som två 100 mm väggar som får jordtrycket via isoleringen.

== Bärförmåga mot jordtryck <barformaga>

Väggen bärs i botten av bottenplattan (urtag, @ansl), i toppen av mellanbjälklaget och på sidorna av hörnen, där armeringen förs runt, eller av stålstolpar. Bärförmågan räknas med brottlinjeteori (SS-EN 1996-1-1 5.5.5 och 6.6.2, Leca Teknisk håndbok 7.4.4). Mönstret är diagonaler från hörnen och en vågrät linje på höjden $y_0$, och både $y_0$ och läget längs väggen varieras. Jordtrycket är triangulärt, med fyllningens höjd längs väggen.
- *Vågrätt moment* från armeringen i liggfogarna, $m_h = A_s f_"yd" z$, både i fält och över hörn och stolpar:
  - A: en Ø5 i den dragna vangen, $d$ = #A.d mm (Sikksakk 225 mm bred). Det ger $m_h$ = #A.mh1 kNm/m med armering i varje fog och #A.mh2 kNm/m i varannan.
  - B: en tråd Ø4 i bistålet, $d$ = #B.d mm i varje vange. Det ger $m_h$ = #B.mh1 kNm/m i varje skift och #B.mh2 kNm/m i vartannat, för båda vangerna tillsammans.
- *Lodrätt moment:* $(f_"xd1" + sigma_d) t^2 slash 6$ för varje vange, med $t$ = 100 mm. $sigma_d$ kommer av vangens egentyngd och 75 % av den permanenta lasten från bjälklaget, på den inre vangen.

#figure(placement: auto,
  image("../fig_kapacitet.svg", width: 82%),
  caption: [Lastfaktor $lambda$ (bärförmåga / dimensionerande last) för en vägg med 2,0 m fyllning, hörn i båda ändar och V1:s normalkraft. Väggarna med 1,7–2,0 m fyllning är markerade.],
) <fig-kapacitet>

Med 2,0 m fyllning klarar system A #D.Lgrans.A2 m mellan hörn eller stolpar med Sikksakk i varannan fog och #D.Lgrans.A1 m med Sikksakk i varje fog. Lecas förhandsgodkända regel tillåter 6,0 m med armering i varannan fog. Beräkningen med EKS faktorer ($gamma_M$ = 1,3 för armeringen) är alltså strängare än Lecas regel, och den styr. System B klarar #D.Lgrans.B1 m med bistål i varje skift och #D.Lgrans.B2 m i vartannat.

#liten(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, left, center, right, right, center, right, right, center, right),
  table.header([Vägg], [$L$ (m)], [Fyllning (m)], [Ändar], [Lecaregel], [A var 2:a], [A varje], [Stolpar A], [B var 2:a], [B varje], [Stolpar B], [$R_"topp"$ / $R_"botten"$]),
  ..D.vagg_fyllda.map(r => ([#r.namn], [#r.L], [#r.fyll], [#r.ande], [#r.regel], [#r.A2], [#r.A1], [#r.nA], [#r.B2], [#r.B1], [#r.nB], [#r.Rt / #r.Rb])).flatten(),
)
#text(size: 8pt)[$lambda$ utan stolpar för armering i varannan respektive varje fog. Stolpar: antal stolpar som behövs med armering i varje fog, jämnt fördelade. Lecaregel: väggen uppfyller Leca tabell 7.7a. $R$: dimensionerande reaktion mot bjälklaget och bottenplattan (kN/m). Övriga väggar (#D.vagg_ovriga) har ingen fyllning.]

== Stålstolpar <stolpar>

Där väggen är längre än vad armeringen bär, sätts en stålstolpe mot väggens insida. Stolpen går från bottenplattan till bjälklaget, och väggen spänner kontinuerligt över den. Stolpen räknas fritt upplagd för jordtrycket på fackbredden med faktorn 1,25 för kontinuitet.

#tab(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (center, left, right, right, right, left, right, right, right),
  table.header([System], [Vägg], [Antal], [Fack (m)], [$lambda$], [Profil S355], [$M_"Ed"$ / $M_"Rd"$ (kNm)], [$R_"topp"$ (kN)], [$R_"botten"$ (kN)]),
  ..D.stolp.map(r => ([#r.sys], [#r.vagg], [#r.n], [#r.Lf], [#r.lam], [#r.vkr], [#r.M / #r.MRd], [#r.Rt], [#r.Rb])).flatten(),
)
Stolparna tar bara vågrät last (@fig-lokala[figur]). De får inte bära bjälklaget, eftersom Lecaväggarna sätter sig mer än stålet (@cellplast). Reaktionerna går som skivkrafter in i bjälklaget och bottenplattan.
- *Fot:* stolpen står i en ficka i kantbalken. Där förlängs urtaget till balkens innerkant på 200 mm längd, och stolpen trycker mot fickans inre kant. Största reaktion #D.stolpfast.Rb kN på 100 × 50 mm ger #D.stolpfast.sig MPa mot $f_"cd"$ = #D.stolpfast.fcd MPa (#D.stolpfast.utn_fot). Fickan gjuts igen med cementbruk när stolpen står.
- *Topp:* en plåt 200 × 200 × 15 S355 med fyra svetsbultar Ø13, L = 75 mm, gjuts in i bjälklagets underkant över stolpen. Två flattstål 80 × 10 svetsas på plåten, ett på var sida om stolpen. En M12 8.8 går genom flattstålen och stolpen i avlånga hål (lodrätt, 40 mm), och mellan stolpens topp och plåten lämnas 20 mm. Största reaktion #D.stolpfast.Rt kN mot #D.stolpfast.Fv kN för skruven (två skär) och #D.stolpfast.dym kN för svetsbultarna (SS-EN 1994-1-1 6.6.3.1), alltså #D.stolpfast.utn_topp.
- Väggen binds till stolpen med en murkramla i var tredje fog. Stolparna ska stå när fyllningen läggs.

== Vertikal last <vert>

Lasten är det största av K-05:s värde över 1 m (med det som står direkt på väggen) och väggens last per meter i den samverkande modellen (@botten). Den läggs i sin helhet på den inre vangen för ytterväggar och fördelas lika på båda vangerna för innerväggar. Vid korta pelare sprids lasten 60° in i anslutande vägg ned till halva höjden. Bärförmågan är $Phi t f_d$ med $h_"ef" = 0,75 h$ och $t$ = 100 mm (bilaga G). Största utnyttjande: system A #D.vert.A.utn (#D.vert.A.namn, $N_"Ed"$ = #D.vert.A.N mot #D.vert.A.NRd kN/m) och system B #D.vert.B.utn (#D.vert.B.namn).
- *Yttre vangen:* enligt K-05 tar den yttre vangen ungefär #D.ld42.andel av lasten från bjälklaget. Kontrollen ovan lägger hela lasten på den inre vangen, så den täcker båda vangerna. I kontrollen mot jordtryck räknas den inre vangen med 75 % av den permanenta lasten, vilket stämmer med fördelningen.
- *Punktlast LD4_2* (K-05, #D.ld42.F kN) står i hörnet V2/V20 ovanför de yttre vangerna. Under bjälklaget och det gjutna U-blocket (#D.ld42.h mm) har den spridits 45° till #D.ld42.A $dot 10^3$ mm² av vangerna, alltså #D.ld42.sig MPa. Läggs det ovanpå V2:s största last på den inre vangen (#D.ld42.sigV2 MPa, som redan innehåller LD4_2) blir det #D.ld42.tot MPa mot $f_d$ = #D.ld42.fdA MPa (A) och #D.ld42.fdB MPa (B), alltså #D.ld42.utnA och #D.ld42.utnB (SS-EN 1996-1-1 6.1.3 med $beta$ = 1). Direkt under bjälklaget bärs lasten främst av betongen i U-blocket, som är ungefär tio gånger styvare än Lecan.

== Anslutningar och hörn <ansl>

- *Topp:* översta skiftet är Leca Iso U-blokk (A) eller LECA balkblock (B), armerat med 2 Ø10. Det gjuts samtidigt med bjälklaget, så att bjälklaget håller väggens topp. Bjälklaget förankras i U-blocket med Ø10 s#D.topp.s, bockade. Största reaktion är #D.topp.Rt kN/m, vilket ger #D.topp.utn av en stångs skjuvkapacitet #D.topp.VRd kN.
- *Botten:* väggen står i ett 50 mm djupt urtag i kantbalken, så att plattans kant håller väggens fot. Det motsvarar Lecas krav att golvet ska gå minst 20 mm upp på nedersta skiftet och Benders klack på minst 45 mm. Största reaktion är #D.Rbot_max kN/m. Under första skiftet läggs glidskikt av papp.
- *Hörn:* armeringen i fogarna förs runt hörnen (A: Sikksakk klipps och bockas enligt Leca figur 4.21; B: bistål bockas eller skarvas med minst 500 mm omlott), så att väggen är inspänd i hörnet.
- *Öppningar:* armering över och under öppningar (en extra fog under fönsterbröstningen och en över avväxlingen), 1 m förbi öppningens kant.

== Utförande, system A (Leca Isoblokk 35) <utfA>

- *Murning:* weber Murmørtel M5, 10 mm fogar under mark (skifthöjd 207 mm), förband minst 80 mm. Mura inte under +5 °C.
- *Armering:* Leca Sikksakk-armering i varje liggfog i väggarna med fyllning (#D.vagg_fyllda.map(r => r.namn).join(", ")), med laftestrimmel i de armerade fogarna. Skarvar minst 300 mm, hörn enligt Leca figur 4.21. Övriga väggar: Leca Fugearmering (2 stänger) över första skiftet och i varannan fog.
- *Stolpar:* #D.stolp_vagg.A, enligt @stolpar.
- *Utsida under mark:* Weber Grå Slemming i två strykningar från foten till över mark. Utanpå sätts Platon grunnmursplate med knopparna mot väggen och en avslutningslist upptill. Dränledning runt huset med fall minst 1:200. Ledningens högsta punkt ska ligga minst 200 mm under golvets överkant och under plattans cellplast. Ledningen och väggen omges med dränerande material, med fiberduk mot jorden.
- *Utsida ovan mark:* sockelputs (weber.base 261) från marken upp.
- *Insida:* puts eller slamning, minst 4 mm (krävs för brand och lufttäthet), utan ångspärr. Väggar mot jord ska kunna torka inåt. Tilläggsisoleras väggen invändigt används ingen plastfolie.
- *Återfyllning:* tidigast när bjälklaget är gjutet och har härdat och murverket är minst 28 dygn. Fyll försiktigt med dränerande massor. Packa inte, och kör inte med maskin närmare än 2 m. Marken ska falla från huset, helst 1:20 och minst 1:50, över 3 m.

== Utförande, system B (LECA Isoblock 350 PUR) <utfB>

- *Murning:* Flexoheft M2,5, tunnfog, förband minst 80 mm. Första skiftet läggs i våg i styvare bruk på glidskikt av bitumenpapp. Mura inte under +5 °C.
- *Armering:* bistål Bi 40 ob i inre vangen och Bi 37 rf (rostfritt) i yttre vangen, i varje skift i väggarna med fyllning, med skarvar minst 500 mm. I övriga väggar läggs bistål i första skiftet och enligt Benders anvisning.
- *Stolpar:* #D.stolp_vagg.B, enligt @stolpar.
- *Utsida under mark* enligt Benders projekteringsanvisning 2.6: Weber grundningsbruk KC (A-bruk) heltäckande. Därpå antingen Isodrän-skivor med geotextil utanför, eller Platonmatta med cellplast utanför. Dränledning och dränerande fyllning som för system A.
- *Insida:* grundning KC och puts, utan ångspärr.
- *Återfyllning* som för system A, tidigast 28 dygn efter murningen.

== Val av system

Båda systemen går att använda. System A har en dokumenterad regel för grundmurar av just detta block, och vangerna är förbundna med fackverksarmering. Det behöver #D.nstolp.A stolpar. System B behöver #D.nstolp.B stolpar, eftersom vangerna bara samverkar via isoleringen och bistålet i varje vange har liten hävarm. Väljs Benders, kan källarväggarna mot jord alternativt muras av massiva LECA block 350 med utvändig isolering enligt Benders källaranvisning, och Isoblock används ovan mark.

= Bottenplatta <botten>

== Uppbyggnad

#figure(placement: auto,
  image("../fig_detalj_A.svg", width: 100%),
  caption: [System A: yttervägg mot jord på kantbalk i L-element (L300). Mått i mm.],
) <fig-detA>
#figure(placement: auto,
  image("../fig_detalj_B.svg", width: 100%),
  caption: [System B: samma sektion med LECA Isoblock 350 PUR och Isodrän.],
) <fig-detB>

- *Underlag:* makadam på sprängt berg, avjämnat och packat.
- *Under plattan:* cellplast S100 i två skikt, 200 mm (L300) eller 300 mm (L400), med radonfolie mellan skikten (Plattor.pdf).
- *Längs ytterkanten:* L-element L300 eller L400 med 100 mm fot av S200 under kantbalken. För L300 används S300 i stället för foten 1,0 m åt båda håll från hörnet V2/V20 (@fig-platta[figur]). Kantbalken är 450 mm bred och 200 (L300) eller 300 mm (L400) hög inklusive plattan.
- *Under innerväggarna* V4–V6, V15 och V19: balkar 450 mm breda med samma höjd och 100 mm S200 under.
- *Under rören:* kvadratiska plintar med samma höjd, sida #D.plint_bredd mm (@fig-platta[figur]). Storleken är vald så att trycket på cellplasten under plintarna blir ungefär lika stort som under väggarna, så att rören och väggarna sätter sig lika mycket. Röret svetsas på en fotplåt 200 × 200 × 15 S355 med fyra svetsbultar Ø13, L = 75 mm, som gjuts in i plintens överkant. Röret bär bara tryck, och bultarna håller det på plats.
- *Platta:* 100 mm C25/30 med Ø6 s150 i över- och underkant. Golvvärmeslangarna fästs i underkantsnätet.

== Beräkningsmodell

- *Bottenplattan:* plattelement (DKT) med verklig tjocklek, 100 mm i fält och 200/300 mm i balkar och plintar. Plattan står på en bädd $k = E slash t$, med $E_k$ eller $0,4 E_k$ och olika tjocklek och kvalitet under plattan och under balkar och plintar.
- *Mellanbjälklaget:* K-05:s nät och laster. Plattan på mark (plan 1) ligger på 400 mm S100.
- *Lecaväggarna:* fjädrar $E t slash h$ längs K-05:s upplagslinjer, med den inre vangen för ytterväggar och båda vangerna för innerväggar.
- *Rören:* fjädrar $E A slash L$ mellan plåtarna i de två plattorna.
- *Styvheter, två omgångar:*
  - kort: $E_k$ för cellplasten, $E_"cm"$ för betongen och $E$ för Lecan;
  - lång: $0,4 E_k$ för cellplasten, $E_"cm" slash (1 + 2,8)$ för betongen, $E slash (1 + 2,0)$ för Lecan, och Lecans krympning, #D.mat.sv_mm mm över väggens höjd.
- *Ytterväggarnas två vangar:* i grundmodellen bär den inre vangen bjälklaget, och lasterna som står över väggarna sprids längs väggens mittlinje. I en variant bär också den yttre vangen (fjäder längs vangens mitt), och lasterna över väggarna sprids längs en linje genom sitt verkliga läge. LD4_2 står då över de yttre vangerna i hörnet V2/V20. Bjälklaget lämnar nästan ingen last på den yttre vangen, men lasterna som står över den går ned i den.
- *Lastfall och kombinationer* som i K-05. Lecaväggarnas egentyngd (2,1 kN/m², B, det tyngre blocket) och bottenplattans egentyngd ingår. Resultaten är det ogynnsammaste av omgångarna och modellerna.

== Cellplast och sättningar <cellplast>

#figure(placement: auto,
  image("../fig_tryck.svg", width: 100%),
  caption: [L300: största tryck mot cellplasten i brottgränstillstånd (omhyllande av omgångarna och modellerna) och sättning av bottenplattan för kvasipermanent last, långtid. Tunna linjer: balkar och plintar.],
) <fig-tryck>

#tab(
  columns: (1fr, auto, auto, auto),
  align: (left, right, right, right),
  table.header([Tryck (kPa)], [L300], [L400], [Gräns]),
  [S200 under balkar och plintar, brottgräns (medel inom $r$ = 150 mm vid toppen)], [#P3.eps_b.uls (#P3.eps_b.medel)], [#P4.eps_b.uls (#P4.eps_b.medel)], [#P3.eps_b.fdM],
  [S200, bara permanent last], [#P3.eps_b.perm], [#P4.eps_b.perm], [#P3.eps_b.fdP],
  [S200, kvasipermanent långtid], [#P3.eps_b.qp], [#P4.eps_b.qp], [#P3.eps_b.kryp],
  [S300 vid hörnet V2/V20: brottgräns / permanent / långtid], [#P3.eps_3.uls / #P3.eps_3.perm / #P3.eps_3.qp], [–], [#P3.eps_3.fdM / #P3.eps_3.fdP / #P3.eps_3.kryp],
  [S100 under plattan, brottgräns], [#P3.eps_f.uls], [#P4.eps_f.uls], [#P3.eps_f.fdM],
  [S100 under plattan, kvasipermanent långtid], [#P3.eps_f.qp], [#P4.eps_f.qp], [#P3.eps_f.kryp],
  [Sättning av bottenplattan, långtid (mm)], [#P3.w.min–#P3.w.max], [#P4.w.min–#P4.w.max], [],
)
Det största trycket ligger i det yttre hörnet mellan V2 och V20, där LD4_2 står över de yttre vangerna. Med L300 räcker S200 inte där, och under kantbalken läggs S300 på 1,0 m åt båda håll från hörnet. Med L400 är medelvärdet inom radien 150 mm under gränsen för S200. Utanför hörnet räcker S200 i båda utförandena.

Mellanbjälklagets stöd sätter sig långtid #P3.w.ror mm vid rören och #P3.w.vagg mm vid väggarna. Väggarna sätter sig alltså cirka #P3.w.skillnad mm mer än rören, och det mesta av skillnaden är Lecans krympning och krypning. Krympningen ensam ger högst #P3.svinn kNm/m i mellanbjälklaget. Effekten finns med i kontrollen i @samverkan.

*Plattan på mark på plan 1* (K-05, 400 mm S100): största tryck är #P3.mark.uls kPa mot $f_d$ = #P3.mark.fdM kPa i brottgränstillstånd och #P3.mark.qp kPa långtid mot #P3.mark.kryp kPa, alltså #P3.mark.utn. S100 räcker där. Tjockleken bestäms av värmeisoleringen, inte av tryckklassen.

== Platta, balkar och plintar

#figure(placement: auto,
  image("../fig_bottenplatta.svg", width: 88%),
  caption: [Bottenplattan, utförande L300: kantbalkar och balkar under innerväggarna, plintar under rören med sida i mm, och diagonaljärn vid inåtgående hörn.],
) <fig-platta>

- *Platta 100 mm:* största moment utanför balkar och plintar är #P3.falt.mu kNm/m i underkant och #P3.falt.mo kNm/m i överkant. Det motsvarar #P3.falt.utn av Ø6 s150 ($M_"Rd"$ = #P3.falt.MRu / #P3.falt.MRo kNm/m).
- *Kantbalkar:* balkmoment (plattans moment integrerat över 450 mm) högst #P3.kant.Ms kNm i underkant och #P3.kant.Mh kNm i överkant. 2 Ø10 i under- och överkant ger $M_"Rd"$ = #P3.kant.MRd / #P3.kant.MRo kNm (#P3.kant.utnM).
  - Tvärkraft högst #P3.kant.V kN, #P3.kant.utnV av $V_"Rd,c"$. Ingen tvärkraftsarmering behövs.
  - U-byglar Ø6 s600 håller längsjärnen på plats. Balken är en förtjockning av en platta på bädd, så minimiarmering för byglar behövs inte (6.2.1(4)).
  - Urtaget och stolparnas fickor sänker kantbalkens överkant 50 mm under väggen. Kantbalken räknas därför med 50 mm lägre höjd ($d$ = #P3.kant_d.uk mm i underkant och #P3.kant_d.ok mm i överkant för L300), och överkantsjärnen ligger under urtaget.
- *Balkar under innerväggarna* (@fig-lokala[figur]): #P3.inre.utnM av samma armering, tvärkraft #P3.inre.utnV.
- *Plintar* (@fig-lokala[figur]): Ø8 s150 i underkant i båda riktningarna. Lastytan är fotplåtens effektiva yta, #P3.plint.beff × #P3.plint.beff mm (SS-EN 1993-1-8 6.2.5 med $f_"jd" = 2 f_"cd"$). Genomstansning räknas med hela rörlasten, utan avdrag för cellplastens tryck innanför snittet:
  - i plinten enligt 6.4.4, snitt från 0,5$d$ till 2$d$ som ligger inom plinten ($d$ = #P3.plint.d mm): högst #P3.plint.stans (#P3.plint.namn);
  - i den tunna plattan, 2$d$ från plintens kant ($d$ = #P3.plint.dt mm, Ø6 s150): högst #P3.plint.ute (#P3.plint.ute_namn).
  - Böjning med jämnt tryck under plinten och konsol från lastytans kant: högst #P3.plint.boj.
- *Hörn:* 2 Ø10, L = 1,2 m, i överkant diagonalt vid plattans inåtgående hörn.
- *Sprickor:* krympningen hålls av cellplasten bara med friktion. Plattan behöver inga fogar, men golvbeläggning och tätskikt ska tåla krympsprickor.

#block(breakable: false, liten(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right),
  table.header([Rör], [Plint (mm)], [$N_"Ed"$ (kN)], [Tryck $N slash b^2$ (kPa)], [Stansning i plinten], [i plattan], [Böjning]),
  ..D.plintar.map(r => ([#r.namn], [#r.b], [#r.N], [#r.p], [#r.stans], [#r.ute], [#r.boj])).flatten(),
))

#figure(placement: auto,
  image("../fig_lokala.svg", width: 100%),
  caption: [Lokal armering och infästningar, L300, ungefär skala 1:20. Mått i mm. a) Plint under rör. b, c) Stålstolpe vid yttervägg mot jord: topp med glidförband och fot i ficka. d) Balk under innervägg. Kantbalkens armering visas i @fig-detA[figur].],
) <fig-lokala>


== Mellanbjälklaget och rören i samverkan <samverkan>

Med väggarna och rören som fjädrar på en bottenplatta som sätter sig blir K-05:s stödmoment vid väggändarna mindre, eftersom de är toppar från stela upplagslinjer. Lasterna fördelas också om något mellan rör och väggar.
- *Böjning:* moment utjämnat över 250 mm mot K-05:s armering med tilläggsjärn ger #P3.topp.ok i överkant och #P3.topp.uk i underkant. Samma mått med K-05:s egen omhyllning ger #P3.topp.ok5 och #P3.topp.uk5. K-05:s armering räcker alltså även med sättningar och Lecans krympning.
- *Rörlaster:* de blir högst #D.ror.max_kvot större än i K-05 (#D.ror.namn), för de lätt belastade rören #D.ror.okade (kN, samverkan / K-05). Genomstansningen i K-05 har stor marginal vid dessa rör. Största utnyttjande med armeringen 10 mm för lågt blir oförändrat #D.ror.lag (#D.ror.lag_namn).
- *Väggarna:* lasten fördelas om mellan väggarna. De flesta får mindre last än med K-05:s stela upplagslinjer, medan V15, V17 och V19 får något mer. Kontrollen i @vert använder det största av de två.

== Glidning, tjäle och fukt

- *Glidning:* fasaden med öppningarna har ingen fyllning, så jordtrycket på huset är ojämnt. Karakteristiskt blir det netto #D.glid.Fy kN söderut och #D.glid.Fx kN åt höger i @fig-kallare[figur]. Dimensionerande är det #D.glid.Fd kN mot friktionen $mu G$ = #D.glid.my × #D.glid.G = #D.glid.Rd kN i det svagaste skiktet (plastfolien mellan cellplastskikten), alltså #D.glid.utn. Kraften förs genom mellanbjälklaget och bottenplattan som skivor.
- *Tjäle:* grundläggning på dränerad makadam på berg och uppvärmd källare. Ingen markisolering behövs mot tjäle, inte heller vid fasaden med öppningarna.
- *Fukt:* dränering och fuktskydd enligt @utfA och @utfB. Radonfolien mellan cellplastskikten ligger kvar som i Plattor.pdf.

== L300 eller L400

Båda utförandena klarar alla kontroller med samma armering. Skillnaden är cellplasten vid hörnet V2/V20, där LD4_2 står. Med L300 behövs S300 under kantbalken där, 1,0 m åt båda håll (#P3.eps_3.utn). Med L400 räcker S200, eftersom den högre balken sprider lasten bättre (medel #P4.eps_b.medel mot #P4.eps_b.fdM kPa). I övrigt ger L400 något lägre tryck på cellplasten men större moment i plattan vid övergången till balkarna. Sättningarna är lika. *L300 räcker, med S300 vid hörnet.* L400 kan väljas för värmeisoleringen men behövs inte för bärförmågan.

= Utförande och kontroll

1. Spräng och avjämna berget och lägg makadam. Lägg dränledningen runt huset innan cellplasten läggs.
2. Lägg L-element, cellplast S200 under balkar och plintar och S100 under plattan i två skikt med radonfolie emellan. Skär ur cellplasten för balkar och plintar. L300: under kantbalken vid hörnet V2/V20 ska cellplasten vara S300, 1,0 m åt båda håll.
3. Armera: nät Ø6 s150 i båda lagren, kantbalkar och balkar 2 Ø10 + 2 Ø10 med U-byglar Ø6 s600, plintar Ø8 s150 i underkant och diagonaljärn. Gjut in fotplåtarna för rören i plintarna. Lägg golvvärmeslangarna.
4. Gjut bottenplattan med urtag 50 mm under ytterväggarna och fickor för stålstolparna.
5. Mura väggarna enligt system A eller B med armering i fogarna, ställ stålstolparna i fickorna och gjut igen dem, och mura det översta skiftet med U-block.
6. Ställ rören, sätt stolparnas toppinfästning och gjut mellanbjälklaget (K-05) tillsammans med U-blocken.
7. Slamma eller grunda väggarna utvändigt och sätt grundmursskiva eller Isodrän. Fyll tidigast när bjälklaget har härdat och murverket är minst 28 dygn, försiktigt och utan packning.
8. Kontrollera före gjutning: armeringens läge och täckskikt (distanser), plintarnas läge och storlek, urtagets höjd. Kontrollera under murning: armering i rätt fogar, skarvar och hörn.

#v(6pt)
#counter(heading).update(0)
#set heading(numbering: "A.1")
#show heading.where(level: 1): it => {
  v(5pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[Bilaga #counter(heading).display() #h(4pt) #it.body])
}

= Kontroll av beräkningarna

- *Brottlinjeberäkningen* ger kända lösningar:
  - fritt upplagd kvadratisk platta med lika moment: $lambda q L^2 slash m$ = #D.valid.l1 (exakt 24);
  - rektangel 2 : 1: #D.valid.l2 (Johansen #D.valid.l2x);
  - vågrät strimla inspänd i båda ändar: $lambda$ dividerat med den exakta lösningen $16 m slash (q L^2)$ = #D.valid.l3.
- *Sättning under balkarna* för hand: $w = sigma t slash E$ = #D.valid.sig kPa × 100 mm / #D.valid.Ed kPa = #D.valid.w_hand mm. FE-modellen ger högst #D.valid.w_fe mm.
- *Jämvikt i den samverkande modellen:* summan av lasten är lika med reaktionen från cellplasten under bottenplattan och plattan på mark (kN): #D.jamvikt.map(r => [#r.namn #r.last = #r.R]).join(", ").
#if D.nat != none [
- *Nätet:* grundnät 140 mm i stället för 200 mm (#D.nat.ne2 mot #D.nat.ne1 element i bottenplattan) ändrar största cellplasttryck (kvasipermanent last) från #D.nat.p1 till #D.nat.p2 kPa, #if D.nat.w1 == D.nat.w2 [sättningen inte alls (#D.nat.w1 mm)] else [sättningen från #D.nat.w1 till #D.nat.w2 mm] och rörlasterna högst #D.nat.dr %.
]
- *Kopplingen till K-05:* mellanbjälklagets nät, laster och lastmönster hämtas direkt från K-05:s program, så nätet är detsamma nod för nod.
