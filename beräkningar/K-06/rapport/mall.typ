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
#let M = D.mat
#let A = D.arm
#let BY = D.bygg
#let P3 = D.platta.L300

#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Källarväggar av Sundolitt Kub 350-150 mot jord, byggskedet och bottenplatta på cellplast], [*Upprättad*], p.upprattad,
)

= Inledning

Handlingen redovisar källarens väggar och bottenplattan. Väggarna gjuts i Sundolitt Kub 350-150 (U17). Kub är element av cellplast EPS 120, 100 mm på var sida, som är kvarsittande form för en armerad betongkärna, 150 mm (SINTEF Teknisk Godkjenning TG 2216). Kärnan räknas som en vanlig betongvägg med samma tvärsnitt. Ytterväggarna mot jord hålls i botten av bottenplattan och i toppen av mellanbjälklaget, som gjuts samtidigt med väggarnas översta skift.

Handlingen redovisar också byggskedet innan mellanbjälklaget har gjutits:
- i vilken ordning väggarna gjuts och fylls;
- hur V3 och V20 bär fyllningen innan bjälklaget finns;
- vilken hållfasthet betongen behöver när det fylls mot väggarna, och hur många dygn den då ska härda.

Bottenplattan är 100 mm på 200 mm cellplast med kantbalkar i L-element L300, balkar under innerväggarna och plintar under rören. Bottenplattan, väggarna, rören och mellanbjälklaget (K-05) räknas i en gemensam FE-modell, så att skillnaden i sättning mellan rör och väggar ingår.

Regler: SS-EN 1990, SS-EN 1991-1-1, SS-EN 1991-1-6, SS-EN 1992-1-1, SS-EN 1992-1-2 och SS-EN 1997-1 med EKS 12, samt TG 2216 och Sundolitts monteringsanvisning för Kub (2022). Säkerhetsklass 2 ($gamma_d$ = 0,91), livslängd 50 år, geoteknisk kategori 1.

*Resultat.*
#tab(
  columns: (44mm, 1fr),
  align: (left, left),
  table.header([Del], [Resultat]),
  [Väggar mot jord, färdigt läge], [Lodräta järn #A.txt på insidan i alla ytterväggar. Böjning högst #D.vmax.utn (#D.vmax.namn), tvärkraft #D.vmax.utnV, fogen mot bottenplattan #D.fog.utnb],
  [Fasaden med öppningarna], [Pelarna #D.fasad.utn, bröstningen med 2 Ø12 under öppningarna],
  [Vertikal last], [Ytterväggar #D.vert.yutn (#D.vert.ynamn, med jordtrycket), innerväggar #D.vert.iutn],
  [LD4_2 i hörnet V2/V20], [#D.horn.utn],
  [Byggskedet], [V3 bär fyllningen vågrätt mellan hörnen med #BY.hor3 i båda ytorna ($lambda$ = #BY.lam3). Fyll mot väggarna när betongen har nått $f_"ck" (t)$ ≥ #BY.regel MPa: #BY.d10N dygn vid 10 °C (#BY.d10R med snabbhärdande cement), se @hardning],
  [Bottenplatta L300, cellplast], [S200 under balkar och plintar #P3.eps_b.utn. S300 under kantbalken vid de #D.horn_s300 yttre hörnen, 1,0 m åt båda håll, #P3.eps_3.utn. S100 under plattan #P3.eps_f.utn],
  [Bottenplatta L300, betong], [Kantbalk 450 × 200 med 2 Ø10 i under- och överkant (#P3.kant.utnM). Platta Ø6 s150 i båda lagren (#P3.falt.utn). Plintar #D.plint_bredd mm, genomstansning högst #P3.plint.max],
  [Mellanbjälklaget (K-05) med sättningar], [Överkant #P3.topp.ok och underkant #P3.topp.uk av K-05:s armering. K-05:s modell ger #P3.topp.ok5 och #P3.topp.uk5],
  [Plattan på mark (plan 1), 400 mm S100], [#P3.mark.utn],
  [Glidning], [#D.glid.utn],
)

Det som styr väggarna är packningen intill dem, inte vilojordtrycket. Sundolitts armering för väggar som hålls i topp och botten (Ø10 s300) räcker för jordtrycket men inte för packningstrycket från en vanlig lätt vibroplatta, så de lodräta järnen läggs tätare. Bottenplattan L300 räcker, med S300 under kantbalken vid de yttre hörnen.

= Förutsättningar

#figure(placement: auto,
  image("../fig_kallare.svg", width: 90%),
  caption: [Källaren med väggarna V1–V21 (Kub 350-150, den sammanhängande betongkärnan mörk), rören P1–P19 och fyllningens höjd mot väggarna. Bakom V3 och V20 läggs fyllningen innan mellanbjälklaget gjuts. Mått i mm, samma koordinater som i K-05.],
) <fig-kallare>

- *Grund:* sprängt berg som avjämnas med makadam. Grunden dräneras runt huset, och det finns inget vattentryck mot väggar eller platta. Berget och den dränerade makadamen är inte tjälfarliga.
- *Höjder:* fri höjd #M.H mm från bottenplattans överkant till mellanbjälklagets underkant (rörens längd), alltså tre hela Kub-skift à 600 mm och ett halvt skift, 300 mm. Mellanbjälklaget är 150 mm.
- *Fyllning:* höjden över bottenplattans överkant enligt @fig-kallare[figur]. Den är 2,0 m mot de slutna fasaderna utom mot V1, där den är #D.v1 m. Mot V18 ligger avsatsen utanför sovrummet, #D.v18 m. Mot V14 faller den från 1,8 till 0,8 m och mot V9 från 0,8 m till noll vid öppningen. Mot fasaden med öppningarna är fyllningen #D.fasad.h m (husets Onshape-modell). Bakom V3 och V20 ligger plattan på mark på plan 1 (K-05) på #M.eps_mark mm cellplast. Där går fyllningen till #M.hfm m, och plattan räknas som ytlast, #M.gmark kN/m² permanent och #M.qmark kN/m² nyttig.
- *Jordtryck:* vilojordtryck, eftersom väggarna hålls i topp och botten. $K_0 = 1 - sin phi'$ = #M.K0 med $phi'$ = #M.fi° för dränerande krossmaterial, $gamma$ = #M.gamma kN/m³. Last på marken intill väggarna är #M.q kN/m² (gångyta). Inga fordon får köra närmare än 2 m.
- *Packning* (@jordtryck): fyllningen inom 1 m från väggen läggs i lager om högst #M.lager m och packas med en lätt vibroplatta, högst #M.vp_m kg, centrifugalkraft högst #M.vp_F kN och bredd minst #M.vp_b m. Det ger ett kvarstående horisontaltryck på #M.komp kPa. Längre ut än 1 m får fyllningen packas tyngre.
- *Användning:* källaren är uppvärmd och har golvvärme i bottenplattan.
- *Laster från plan 1 och mellanbjälklaget* enligt K-05: samma punktlaster, väggar, kombinationer och mönster för nyttig last. Laster som står över en vägg går in i väggens kärna och sprids 60° mot horisontalplanet ned till bottenplattan. Nyttig last i källaren är 2,0 + 0,7 kN/m².
- *Kombinationer:* jordtrycket och packningstrycket är permanent last, 6.10a med $0,91 dot 1,35$ och 6.10b med $0,91 dot 1,2$. Last på marken är nyttig last. Kärnans krympning är en påtvingad deformation med faktorn 1,0.

#tab(
  columns: (auto, 1fr, auto, auto),
  align: (left, left, right, right),
  table.header([Material], [], [$f_"ck"$ (MPa)], [$gamma_M$]),
  [Betong i väggarna], [Sundolitts recept B30 (NS-EN 206), räknas som C30/37. Största stenstorlek 16 mm, grov ballast minskad 25 %, sättmått 180–200 mm. Exponeringsklass XC2 mot utsidan (cellplast och jord) och XC1 mot insidan, livslängd 50 år], [#M.fck], [1,5],
  [Betong i plattorna], [C25/30. Bottenplattan XC2 mot cellplasten och XC1 i överkant, mellanbjälklaget XC1 (K-05). Mellanbjälklaget får gjutas med väggarnas recept; ytterväggarnas översta skift gjuts alltid med det], [25], [1,5],
  [Armering], [B500B. I väggarna täckande skikt #M.c_in mm mot insidan och #M.c_ut mm mot utsidan till de vågräta järnen], [500], [1,15],
)
Kärnans $E_"cm"$ = #M.Ecm MPa. Kryptalet är #M.kryp och den slutliga krympningen #M.svinn mm/m (SS-EN 1992-1-1 3.1.4 med RH 80 % och $h_0$ = 150 mm; kärnan är inkapslad i cellplast).

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

== Väggsystemet

Kub 350-150 består av element 1 200 × 600 mm (halva element 300 mm), som staplas i förband och armeras innan kärnan gjuts. Plastbindare håller ihop cellplasten och har fästen för armeringen och för gipsskivorna på insidan. Väggen är #M.H mm hög: de tre hela skiften (#M.gjut1 mm) gjuts först, och i ytterväggarna gjuts det översta halva skiftet tillsammans med mellanbjälklaget. Innerväggarna gjuts i hela höjden före bjälklaget, som vilar på dem med ett glidskikt.

TG 2216 godkänner Kub för väggar mot jord. Ett av de redovisade fallen är vår vägg: den hålls i toppen av ett gjutet bjälklag och i botten av golvet, med fyllning upp till 2,3 m. TG 2216 anger armeringen för det fallet, men den räknar inte med packning intill väggen. Väggarna dimensioneras därför här enligt SS-EN 1992-1-1, och armeringen är minst den som TG 2216 anger:

#tab(
  columns: (auto, 1fr, 1fr),
  align: (left, left, left),
  table.header([Del], [Armering], [Kommentar]),
  [Vågräta järn], [2 Ø10 per skift, ett vid var yta, s600. I de två översta skiften s300], [TG 2216. I V3 s300 i hela höjden (@v3)],
  [Lodräta järn], [#A.txt på insidan i alla ytterväggar, från bottenplattan upp till bjälklagets överkantsnät], [TG 2216 anger Ø10 s300; tätare för packningstrycket (@barformaga) och för lasterna över väggarna (@vert)],
  [Startjärn], [#A.start på utsidan, 500 mm ned i kantbalken (bockade) och 1 200 mm upp i väggen], [TG 2216],
  [Vinkeljärn till bjälklaget], [#A.txt, 650 mm ned i väggen och 500 mm in i bjälklaget under överkantsnätet], [TG 2216 anger Ø10 s300; pos 14 på R-03],
  [Hörn och anslutningar], [Vinkeljärn Ø10, 750 mm åt var håll, vid båda ytorna; skarvar minst #M.skarv mm], [TG 2216 figur 5–7; @fig-lokala[figur] c och d],
  [Öppningar], [2 Ø12 över, under och längs sidorna, förankrade 600 mm förbi öppningen], [TG 2216],
  [Innerväggar], [Vågräta järn och startjärn som ovan], [Inget jordtryck; glidskikt på krönet (R-03)],
)

== Jordtryck och packning <jordtryck>

När fyllningen packas intill en vägg som inte kan röra sig, blir ett horisontaltryck kvar i jorden. Det är större än vilojordtrycket nära markytan (Ingold, Géotechnique 1979). Trycket blir $sigma_"komp" = sqrt(2 P gamma slash pi)$, där $P$ är packningsredskapets linjelast, alltså tyngd och centrifugalkraft per meter bredd. För vibroplattan i avsnitt 2 är $P$ = #M.P kN/m, vilket ger $sigma_"komp"$ = #M.komp kPa. Trycket gäller från djupet där $gamma z slash K_a$ når $sigma_"komp"$ ($K_a$ = #M.KA) ned till djupet där vilojordtrycket blir större, alltså i hela fyllningshöjden här.

#figure(placement: auto,
  image("../fig_jordtryck.svg", width: 92%),
  caption: [Vägg med 2,0 m fyllning (#D.vmax.namn). Vänster: horisontaltrycket. Höger: moment i den lodräta strimlan och bärförmågan med Sundolitts Ø10 s300 och med #A.txt.],
) <fig-jordtryck>

Med 2,0 m fyllning ger vilojordtrycket ensamt #M.M_K0 kNm/m i väggen, och med packningstrycket #M.M_komp kNm/m. Packar man inte inom 1 m från väggen räcker alltså Ø10 s300. Armeringen här tillåter normal packning med lätt vibroplatta, eftersom fyllningen intill väggen annars sätter sig.

== Bärförmåga i färdigt läge <barformaga>

Väggen räknas som en lodrät strimla, fritt upplagd mellan fogen mot bottenplattan och mellanbjälklagets mittplan, $L$ = #M.Ls m. Hörnen och de vinkelräta väggarna hjälper till, men det räknas inte. Ytterväggarna på plan 1 står #M.e mm utanför kärnans mitt (#M.e_ut mm utanför kärnans yta, K-05). Deras last ger ett moment i väggens topp, som avtar linjärt till noll vid bottenplattan. Hela momentet läggs på väggen och inget på bjälklaget, vilket ligger på säker sida. Det ger drag i insidan, liksom jordtrycket.
- *Böjning:* lodräta järn på insidan, $d$ = #A.dv mm. #A.txt ger $M_"Rd"$ = #A.MRd kNm/m (Ø10 s300: #A.MRd300 kNm/m). Största moment är #D.vmax.M kNm/m i #D.vmax.namn, #D.vmax.y m över bottenplattan, varav #D.vmax.Mt kNm/m i toppen från lasterna över väggen. Det är #D.vmax.utn av bärförmågan (Ø10 s300: #D.vmax.utn300).
- *Tvärkraft:* högst #D.vmax.utnV av $V_"Rd,c"$. Ingen tvärkraftsarmering behövs.
- *Minimiarmering och andra ordningens effekter:* minimiarmeringen enligt 9.3.1.1 är uppfylld i båda riktningarna. Slankheten är $lambda$ = #D.vert.lam. För väggarna med fyllning är normalkraften liten och gränsen enligt 5.8.3.1 minst #D.vert.lam_lim, så andra ordningens effekter är försumbara.

#liten(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, right, right, right, right, right, right, left),
  table.header([Vägg], [$L$ (m)], [Fyllning (m)], [$M_"Ed"$ jord + topp], [$M_"Ed"$], [$M_"Rd"$], [Böjning], [$V_"Ed"$ / $V_"Rd,c"$], [$R_"topp"$ / $R_"botten"$], [Minsta]),
  ..D.vagg_fyllda.map(r => ([#r.namn], [#r.L], [#r.fyll], [#r.Mj + #r.Mt], [#r.M], [#r.MRd], [#r.utnM], [#r.V / #r.VRd], [#r.Rt / #r.Rb], [#r.min])).flatten(),
)
#text(size: 8pt)[Moment i kNm/m och krafter i kN/m, dimensionerande. Största fyllning längs väggen. Minsta: den glesaste lodräta armering som räcker för väggen. Övriga väggar (#D.vagg_ovriga) har ingen fyllning.]

== Fasaden med öppningarna <fasad>

Mot fasaden med öppningarna (#D.fasad.namn) är fyllningen #D.fasad.h m. Betongen i öppningarnas underkant ligger #D.fasad.bro m över bottenplattan; smygen och bröstningen isoleras med 100 mm cellplast. Pelarna mellan öppningarna går upp till bjälklaget. De bär jordtrycket från sin egen bredd och halva öppningarna intill, lodrätt mellan plattorna:

#tab(
  columns: (auto, auto, auto, auto),
  align: (left, right, right, right),
  table.header([Pelare], [Bredd (m)], [Lastbredd / bredd], [$M_"Ed"$ (kNm/m)]),
  ..D.fasad.pel.map(r => ([#r.namn], [#r.b], [#r.faktor], [#r.M])).flatten(),
)
Största moment är #D.fasad.Mmax kNm/m, alltså #D.fasad.utn av #A.txt. Bröstningen under öppningarna spänner vågrätt mellan pelarna, högst #D.fasad.oppn m. Med #D.fasad.p kPa ger det #D.fasad.Mb kNm/m mot #D.fasad.MRdb kNm/m med de vågräta järnen och 2 Ø12 under öppningen.

== Vertikal last och lasterna över väggarna <vert>

Lasten i väggens topp är det största av K-05:s värde över 1 m (med det som står direkt på väggen) och väggens last per meter i den samverkande modellen (@botten). Största värde är #D.vert.Nmax kN/m (#D.vert.Nnamn).
- *Ytterväggar:* normalkraften med egentyngd och oavsiktlig excentricitet $l_0 slash 400$, tillsammans med momentet i @barformaga, eller i väggar utan fyllning momentet från lasterna över väggen. Högst #D.vert.yutn (#D.vert.ynamn: $M_"Ed"$ = #D.vert.yM mot $M_"Rd"$ = #D.vert.yMRd kNm/m med normalkraft). Normalkraften ökar momentkapaciteten, så kontrollen i @barformaga utan normalkraft ligger på säker sida. Andra ordningens moment (nominell krökning, 5.8.8) ingår där slankheten överskrider gränsen: #D.vert.M2.
- *Innerväggar:* centrisk last (glidskikt på krönet), oarmerad vägg enligt 12.6.5.2 med $Phi$ = #D.vert.Phi, där slankheten ingår: högst #D.vert.iutn (#D.vert.inamn, #D.vert.iN mot #D.vert.iNRd kN/m).
- *Lasterna över väggarna:* ytterväggarna på plan 1 står på bjälklaget #M.e_ut mm utanför kärnans yta. Det är mindre än halva bjälklagets tjocklek, så lasten går med en tryckstrimla direkt in i kärnan. Bjälklaget och kärnan gjuts samtidigt. Konsolmomentet till kärnans yta blir högst #D.kant.M kNm/m (#D.kant.q kN/m) mot #D.kant.MRd kNm/m för överkantsnätet.
- *LD4_2* (K-05, #D.horn.F kN dimensionerande) står i hörnet V2/V20, #D.horn.ax och #D.horn.ay mm utanför kärnornas ytor. Bjälklaget ($d$ = #D.horn.d mm) räknas längs kärnornas ytor, $u$ = #D.horn.u mm:
  - tryckstrimlan: $V_"Ed"$ / $V_"Rd,max"$ = #D.horn.F / #D.horn.VRdmax kN (#D.horn.utn_max);
  - tvärkraft med $beta = a_v slash 2d$ = #D.horn.beta (6.2.2(6)): #D.horn.utn_c av $V_"Rd,c"$ = #D.horn.VRdc kN;
  - dragband i överkant: $F a_v slash z$ = #D.horn.T kN mot #D.horn.TRd kN för nätet (#D.horn.utn_T).

  Zon Ö1 i K-05 ger dessutom tilläggsjärn i överkant över hörnet.

== Anslutningar och fogar <ansl>

- *Topp:* i ytterväggarna gjuts det översta halva skiftet samtidigt med mellanbjälklaget. Kärnan och bjälklaget blir då en enhet, och bjälklaget vilar på hela kärnan (TG 2216 kräver minst 100 mm). Den yttre cellplasten i det översta skiftet kapas i bjälklagets underkant, och bjälklaget går ut till 30 mm från väggens ytterliv, med 30 mm kantisolering utanför (husets modell). Vinkeljärnen (#A.txt) förankrar väggen i bjälklaget. Största reaktion i toppen är #D.vmax.Rt kN/m.
- *Gjutfogen vid #M.gjut1 mm:* tvärkraften där är högst #D.fog.V18 kN/m. Med de lodräta järnen genom fogen och en uppruggad yta (6.2.5) är utnyttjandet #D.fog.utn18.
- *Botten:* kärnan gjuts direkt på kantbalkens uppruggade överkant, och startjärnen går genom fogen. Bottenplattan är golvet som håller väggens fot, och kärnan står i kontakt med den, som TG 2216 kräver när fyllningen är högre än 1 m. Största reaktion i botten är #D.vmax.Rb kN/m. Fogen har bärförmågan #D.fog.vrb MPa (6.2.5: uppruggad yta, startjärnen, väggens egentyngd). Det ger högst #D.fog.utnb.
- *Hörn och anslutningar:* vågräta järn med vinkeljärn enligt TG 2216 figur 5–7, se @fig-lokala[figur] c och d.
- *Innerväggar:* de gjuts i hela höjden före bjälklaget. Krönet avjämnas och får glidskikt (byggpapp), och bjälklaget vilar på kärnan utan att vara förankrat i innerväggarna (R-03).

== Utförande av väggarna <utf>

- *Montering:* elementen staplas i förband med armeringen i bindarnas hållare. Väggarna riktas och stagas enligt Sundolitts anvisning: stag vid alla hörn och öppningar och annars cirka var 2 m, med skruv minst 140 mm i bindarna. Kapade element och kanter vid öppningar förstärks med plywood eller läkt.
- *Gjutning:* pump med reducerat tryck, och betongen stiger högst 1 m per timme. Börja i ett hörn och gå runt väggarna i varv. Högst 2,4 m per gjutning, ingen vibrator i väggarna (stöt för hand vid behov). Kontrollera sättmåttet på plats. Gjut inte under −5 °C.
- *Första gjutningen* är de tre hela skiften, upp till #M.gjut1 mm, och innerväggarna i hela höjden. Fogen i ytterväggarnas överkant ruggas och rengörs, och elementens knastar täcks. Innerväggarnas krön avjämnas och får glidskikt.
- *Gjutning med bjälklaget:* bjälklagets form och stämp står för sig själva och får inte hänga i Kub-elementen. Ytterväggarnas översta skift fylls först. Efter 30–60 minuter, när betongen har satt sig, fylls de upp igen, och sedan gjuts bjälklaget. Bara bjälklaget vibreras.
- *Insida:* gips 13 mm (typ A) på all cellplast, också i smygar, skruvad i bindarna. Enligt TG 2216 ger det REI 30. Kärnan klarar REI 90 enligt SS-EN 1992-1-2 tabell 5.4 (150 mm ≥ 140 mm, axelavstånd 30 mm ≥ 25 mm). Gipset skyddar cellplasten och får inte vara genombrutet; eldosor enligt TG 2216. Ingen ångspärr behövs, eftersom halva isoleringen ligger utanför kärnan.
- *Utsida under mark:* grundmursskiva med knopparna mot väggen och en avslutningslist upptill. Dränledning runt huset med fall minst 1:200. Ledningens högsta punkt ska ligga minst 200 mm under golvets överkant och under plattans cellplast. Ledningen och väggen omges med dränerande material, med fiberduk mot jorden. Marken ska falla från huset, minst 1:50 över 3 m.
- *Utsida ovan mark:* fasadsten enligt AR-01. Den täcker all cellplast ovan mark, som TG 2216 kräver.

= Byggskedet <bygg>

== Ordningsföljd

+ Gjut bottenplattan (@botten) med startjärnen ingjutna och uppruggad yta under väggarna.
+ Montera Kub-elementen med armering, vinkeljärn i hörnen och staga väggarna.
+ Gjut de tre hela skiften (#M.gjut1 mm) i ytterväggarna och innerväggarna i hela höjden. Lägg glidskikt (byggpapp) på innerväggarnas avjämnade krön.
+ Fyll bakom V3 och V20 till #M.hfm m när betongen har nått $f_"ck" (t)$ ≥ #BY.regel MPa (@hardning). Lagren ska vara högst #M.lager m, packade med lätt vibroplatta inom 1 m från väggen. Lägg sedan 400 mm cellplast för plattan på mark.
+ Montera ytterväggarnas översta halva skift, rören, bjälklagets form och armering samt vinkeljärnen. Gjut det översta skiftet och mellanbjälklaget i samma gjutning.
+ Fyll mot övriga väggar när bjälklaget och det översta skiftet har nått $f_"ck" (t)$ ≥ #BY.regel MPa. Väggarna under har då härdat längre. Bjälklagets stämp får stå kvar; de påverkar inte väggarna.
+ Riv formen under bjälklaget enligt R-03.

Sundolitt rekommenderar minst fyra veckors härdning och torkning innan det fylls mot väggarna. Det är ett allmänt råd som också gäller torkning före puts. TG 2216 kräver att väggar och bjälklag är gjutna och har härdat tillräckligt. Här räknas hur mycket som räcker.

== V3 och V20 innan bjälklaget finns <v3>

Fyllningen bakom V3 och V20 bär plattan på mark på plan 1, som är en del av mellanbjälklaget. Den måste därför ligga på plats innan bjälklaget gjuts. Väggarna har då fri överkant, #M.gjut1 mm. Som fri konsol skulle V3 behöva inspänning i foten, cirka 32 kNm/m, men bottenplattan och kantbalken kan inte ta den. Väggarna räknas i stället med brottlinjeteori: de bär åt två håll, är inspända i hörnen med vinkeljärnen och ledat upplagda i botten. Lasten är fyllningen till #M.hfm m med packningstryck. På fyllningen ligger dessutom cellplasten, #M.gbygg kN/m² permanent, och färsk betong med arbetslast när plattan på mark gjuts, #M.qbygg kN/m² (SS-EN 1991-1-6), som nyttig last.
- *V3* ($L$ = 4,40 m): med Sundolitts vågräta järn (Ø10 s600) blir $lambda$ = #BY.lam3_std. Med #BY.hor3 i båda ytorna i hela höjden ($m_h$ = #BY.mh3 kNm/m i fält och #BY.mhn3 kNm/m vid hörnen, $m_v$ = #BY.mv3 kNm/m) blir $lambda$ = #BY.lam3, och vid återfyllningen (#BY.regel MPa) #BY.lam3_r.
- *V20* ($L$ = 1,66 m) klarar sig med Sundolitts armering, $lambda$ = #BY.lam20.
- *Hörnen:* vinkeljärnen Ø10 (750 + 750) i V3:s hörn får spänningen $f_"yd" slash lambda$ = #BY.sig MPa. Med sämre vidhäftning ($eta_1$ = 0,7) och alla järn skarvade i samma snitt ($alpha_6$ = 1,5) behövs förankringslängden #BY.lb mm mot #BY.l0 mm.
- *Tvärkraft:* #BY.V3 kN/m mot $V_"Rd,c"$ = #BY.VRd3 kN/m.

== Hållfasthet vid återfyllning <hardning>

Betongens hållfasthet efter $t$ dygn följer SS-EN 1992-1-1 3.1.2: $f_"cm" (t) = beta_"cc" (t) f_"cm"$ med $beta_"cc" (t) = exp(s (1 - sqrt(28 slash t)))$, $f_"ck" (t) = f_"cm" (t) - 8$ MPa och $f_"ctm" (t) = beta_"cc" (t) f_"ctm"$. Kontrollerna i byggskedet görs med betongen vid ålder $t$:
- *V3 och V20 innan bjälklaget:* $lambda$ och tvärkraft räcker redan efter tre dygn. Förankringen av vinkeljärnen i hörnen styr och kräver $f_"ck" (t)$ ≥ #BY.fckA MPa.
- *Övriga väggar efter bjälklaget* (mest belastad #BY.vaggB): böjning, tvärkraft och gjutfogen räcker efter tre dygn. Skarven mellan vinkeljärnen och de lodräta järnen i det översta skiftet (#BY.sigB MPa) kräver $f_"ck" (t)$ ≥ #BY.fckB MPa.

*Kravet blir $f_"ck" (t)$ ≥ #BY.regel MPa, två tredjedelar av $f_"ck"$, innan det fylls mot någon vägg* ($f_"cm" (t)$ ≥ #BY.fcm MPa; provkuber ungefär 20 % högre). Det gäller väggarna och, för de övriga väggarna, också bjälklaget och det översta skiftet. Vid lägre temperatur tar det längre tid. Mognadsåldern enligt SS-EN 1992-1-1 (B.10) är $t_T = sum exp(-(4000 slash (273 + T) - 13,65)) Delta t$, där $T$ är dygnets medeltemperatur. Kravet nås vid mognadsåldern #BY.teqN dygn med cement i klass N ($s$ = 0,25) och #BY.teqR dygn med klass R ($s$ = 0,20), alltså:

#figure(placement: auto,
  image("../fig_hardning.svg", width: 88%),
  caption: [$f_"ck" (t)$ för C30/37 mot dygn efter gjutning vid konstant medeltemperatur, med cement i klass N (heldragen) och R (streckad). Kravet för återfyllning och gränsen innan betongen får frysa.],
) <fig-hardning>

#block(breakable: false, tab(
  columns: (auto, auto, auto, auto, auto),
  align: (left, right, right, right, right),
  table.header([Dygnsmedeltemperatur], [Återfyllning, klass N], [Återfyllning, klass R], [Frost, klass N], [Frost, klass R]),
  ..BY.dygn.map(r => ([#r.T °C], [#r.N dygn], [#r.R dygn], [#r.fN], [#r.fR])).flatten(),
))
Dygn efter gjutning, minst 3. Frost: dygn tills $f_"ck" (t)$ = 5 MPa, då betongen tål att frysa. Dessförinnan ska den skyddas mot frost. Kärnan är isolerad av cellplasten och håller värmen, så att räkna med luftens temperatur ligger på säker sida. Bjälklagets ovansida täcks med isolermattor när det är kallt.
- *Kontroll:* temperaturgivare i väggen och i bjälklaget, med mognadsgraden räknad som ovan, eller provkuber som härdar bredvid väggen. Är betongleverantörens cement i klass R gäller den kolumnen.
- *Exempel vid 10 °C med cement i klass N:* V3 och V20 fylls tidigast #BY.d10N dygn efter den första gjutningen, och övriga väggar #BY.d10N dygn efter bjälklaget. Vid 20 °C är tiderna #BY.d20N dygn och vid 5 °C #BY.d5N dygn.

= Bottenplatta <botten>

== Uppbyggnad

#figure(placement: auto,
  image("../fig_detalj.svg", width: 100%),
  caption: [Yttervägg mot jord (Kub 350-150) på kantbalk i L-element (L300), med mellanbjälklaget. Mått i mm.],
) <fig-det>

- *Underlag:* makadam på sprängt berg, avjämnat och packat.
- *Under plattan:* cellplast S100 i två skikt, 200 mm, med åldringsbeständig plastfolie mellan skikten (Plattor.pdf). Bottenplattan är alltså 300 mm hög: 100 mm betong på 200 mm cellplast, samma i hela källaren.
- *Längs ytterkanten:* L-element L300 med 100 mm fot av S200 under kantbalken. Vid källarens #D.horn_s300 yttre hörn är foten S300 1,0 m åt båda håll (@fig-platta[figur]). Kantbalken är 450 mm bred och 200 mm hög inklusive plattan. Väggens kärna står på kantbalken, 100–250 mm från ytterkanten.
- *Under innerväggarna* V4–V6, V15 och V19: balkar 450 mm breda med samma höjd och 100 mm S200 under.
- *Under rören:* kvadratiska plintar med samma höjd, sida #D.plint_bredd mm (@fig-platta[figur]). Storleken är vald så att trycket på cellplasten under plintarna blir ungefär lika stort som under väggarna, så att rören och väggarna sätter sig lika mycket. Röret svetsas på en fotplåt 200 × 200 × 15 S355 med fyra svetsbultar Ø13, L = 75 mm, som gjuts in i plintens överkant. Vid P7 står två rör tätt intill varandra på en gemensam fotplåt 280 × 200 × 15 (K-05). Röret bär bara tryck, och bultarna håller det på plats.
- *Platta:* 100 mm C25/30 med Ø6 s150 i över- och underkant. Golvvärmeslangarna fästs i underkantsnätet.

== Beräkningsmodell

- *Bottenplattan:* plattelement (DKT) med verklig tjocklek, 100 mm i fält och 200 mm i balkar och plintar. Plattan står på en bädd $k = E slash t$, med $E_k$ eller $0,4 E_k$ och olika tjocklek och kvalitet under plattan och under balkar och plintar.
- *Mellanbjälklaget:* K-05:s nät och laster. Plattan på mark (plan 1) ligger på 400 mm S100.
- *Väggarna:* kärnan som fjäder $E t slash h$ med $t$ = 150 mm längs K-05:s upplagslinjer i kärnans mitt.
- *Rören:* fjädrar $E A slash L$ mellan plåtarna i de två plattorna.
- *Styvheter, två omgångar:*
  - kort: $E_k$ för cellplasten och $E_"cm"$ för betongen;
  - lång: $0,4 E_k$ för cellplasten, $E_"cm" slash (1 + 2,8)$ för plattorna, $E_"cm" slash (1 + #M.kryp)$ = #M.Ev_l MPa för kärnan, och kärnans krympning, #M.sv_mm mm över väggens höjd.
- *Laster:* lastfall och kombinationer som i K-05. Väggarnas egentyngd är #M.gkub kN/m² (kärna, cellplast och gips). På ytterväggarna kommer fasadsten till, #M.gsten kN/m² från 50 mm under mark till bjälklagets överkant (AR-01). Bottenplattans egentyngd ingår också. Resultaten är det ogynnsammaste av omgångarna.

== Cellplast och sättningar <cellplast>

#figure(placement: auto,
  image("../fig_tryck.svg", width: 100%),
  caption: [Största tryck mot cellplasten i brottgränstillstånd (omhyllande av omgångarna) och sättning av bottenplattan för kvasipermanent last, långtid. Tunna linjer: balkar och plintar.],
) <fig-tryck>

#tab(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  table.header([Tryck (kPa)], [Värde], [Gräns]),
  [S200 under balkar och plintar, brottgräns (medel inom $r$ = 150 mm vid toppen)], [#P3.eps_b.uls (#P3.eps_b.medel)], [#P3.eps_b.fdM],
  [S200, bara permanent last], [#P3.eps_b.perm], [#P3.eps_b.fdP],
  [S200, kvasipermanent långtid], [#P3.eps_b.qp], [#P3.eps_b.kryp],
  [S300 vid de yttre hörnen: brottgräns / permanent / långtid], [#P3.eps_3.uls / #P3.eps_3.perm / #P3.eps_3.qp], [#P3.eps_3.fdM / #P3.eps_3.fdP / #P3.eps_3.kryp],
  [S100 under plattan, brottgräns], [#P3.eps_f.uls], [#P3.eps_f.fdM],
  [S100 under plattan, kvasipermanent långtid], [#P3.eps_f.qp], [#P3.eps_f.kryp],
  [Sättning av bottenplattan, långtid (mm)], [#P3.w.min–#P3.w.max], [],
)
Betongväggarna med fasadsten väger cirka 8–11 kN/m. De största trycken ligger vid de yttre hörnen, där hörnstolparna på plan 1 och LD4_2 står. Där räcker inte S200, och under kantbalken läggs S300 1,0 m åt båda håll från hörnet. Utanför hörnen räcker S200.

Mellanbjälklagets stöd sätter sig långtid #P3.w.ror mm vid rören och #P3.w.vagg mm vid väggarna. Väggarna sätter sig alltså cirka #P3.w.skillnad mm mer än rören. Kärnans krympning ensam ger högst #P3.svinn kNm/m i mellanbjälklaget. Effekten finns med i kontrollen i @samverkan.

*Plattan på mark på plan 1* (K-05, 400 mm S100): största tryck är #P3.mark.uls kPa mot $f_d$ = #P3.mark.fdM kPa i brottgränstillstånd och #P3.mark.qp kPa långtid mot #P3.mark.kryp kPa, alltså #P3.mark.utn. S100 räcker där. Tjockleken bestäms av värmeisoleringen, inte av tryckklassen.

== Platta, balkar och plintar

#figure(placement: auto,
  image("../fig_bottenplatta.svg", width: 88%),
  caption: [Bottenplattan L300: kantbalkar och balkar under innerväggarna, plintar under rören med sida i mm, S300 vid de yttre hörnen och diagonaljärn vid inåtgående hörn.],
) <fig-platta>

- *Platta 100 mm:* största moment utanför balkar och plintar, minst $d$ = #P3.falt.d mm från dem, är #P3.falt.mu kNm/m i underkant och #P3.falt.mo kNm/m i överkant. Det motsvarar #P3.falt.utn av Ø6 s150 ($M_"Rd"$ = #P3.falt.MRu / #P3.falt.MRo kNm/m). Närmare balkarna är momentet en lokal topp vid den tjocka delens kant, störst i inåtgående hörn mellan balkarna (#P3.falt.topp kNm/m precis vid kanten). Toppen är en singularitet i FE-lösningen och avtar inom några centimeter; nätet går in i balkarna och tar momentet där.
- *Kantbalkar:* balkmoment (plattans moment integrerat över 450 mm) högst #P3.kant.Ms kNm i underkant och #P3.kant.Mh kNm i överkant. 2 Ø10 i under- och överkant ger $M_"Rd"$ = #P3.kant.MRd / #P3.kant.MRo kNm (#P3.kant.utnM).
  - Tvärkraft högst #P3.kant.V kN, #P3.kant.utnV av $V_"Rd,c"$. Ingen tvärkraftsarmering behövs.
  - U-byglar Ø6 s600 håller längsjärnen på plats. Balken är en förtjockning av en platta på bädd, så minimiarmering för byglar behövs inte (6.2.1(4)).
  - Startjärnens fot, 330 mm, läggs längs balken på byglarna, så att 500 mm ligger i balken (@fig-det[figur]).
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
  caption: [Lokal armering, ungefär skala 1:20. Mått i mm. a) Plint under rör. b) Balk under innervägg. c) Yttre hörn i plan. d) V3 mot V19/V20 i plan. Kantbalkens armering och väggens anslutningar visas i @fig-det[figur].],
) <fig-lokala>

== Mellanbjälklaget och rören i samverkan <samverkan>

Med väggarna och rören som fjädrar på en bottenplatta som sätter sig blir K-05:s stödmoment vid väggändarna mindre, eftersom de är toppar från stela upplagslinjer. Lasterna fördelas också om något mellan rör och väggar.
- *Böjning:* moment utjämnat över 250 mm mot K-05:s armering med tilläggsjärn ger #P3.topp.ok i överkant och #P3.topp.uk i underkant. Samma mått med K-05:s egen omhyllning ger #P3.topp.ok5 och #P3.topp.uk5. K-05:s armering räcker alltså även med sättningar och kärnans krympning.
- *Rörlaster:* de blir högst #D.ror.max_kvot större än i K-05 (#D.ror.namn), för de lätt belastade rören #D.ror.okade (kN, samverkan / K-05). Genomstansningen i K-05 har stor marginal vid dessa rör. Största utnyttjande med armeringen 10 mm för lågt blir #D.ror.lag (#D.ror.lag_namn).
- *Väggarna:* lasten fördelas om mellan väggarna. Väggar som får mer last än med K-05:s stela upplagslinjer: #D.vagglast.storre. Kontrollen i @vert använder det största av de två.

== Glidning, tjäle och fukt

- *Glidning:* fasaden med öppningarna har bara #D.fasad.h m fyllning, så jordtrycket på huset är ojämnt. Karakteristiskt blir det netto #D.glid.Fy kN söderut och #D.glid.Fx kN åt höger i @fig-kallare[figur]. Dimensionerande är det #D.glid.Fd kN mot friktionen $mu G$ = #D.glid.my × #D.glid.G = #D.glid.Rd kN i det svagaste skiktet (plastfolien mellan cellplastskikten), alltså #D.glid.utn. Räknas också packningstrycket blir det #D.glid.Fdk kN, #D.glid.utnk. Kraften förs genom mellanbjälklaget och bottenplattan som skivor. TG 2216 kräver att jordtrycket tas med i husets stabilitet när väggarna hålls av bjälklaget.
- *Tjäle:* grundläggning på dränerad makadam på berg och uppvärmd källare. Ingen markisolering behövs mot tjäle, inte heller vid fasaden med öppningarna.
- *Fukt:* dränering och fuktskydd enligt @utf. Den åldringsbeständiga plastfolien mellan cellplastskikten ligger kvar som i Plattor.pdf.

= Utförande och kontroll

1. Spräng och avjämna berget och lägg makadam. Lägg dränledningen runt huset innan cellplasten läggs.
2. Lägg L-element, cellplast S200 under balkar och plintar och S100 under plattan i två skikt med åldringsbeständig plastfolie emellan. Under kantbalken vid källarens yttre hörn ska foten vara S300, 1,0 m åt båda håll. Skär ur cellplasten för balkar och plintar.
3. Armera: nät Ø6 s150 i båda lagren, kantbalkar och balkar 2 Ø10 + 2 Ø10 med U-byglar Ø6 s600, plintar Ø8 s150 i underkant, diagonaljärn och startjärn #A.start till väggarna. Gjut in fotplåtarna för rören i plintarna. Lägg golvvärmeslangarna.
4. Gjut bottenplattan och rugga ytan under väggarna.
5. Bygg och gjut väggarna och mellanbjälklaget i den ordning som anges i @bygg, och fyll mot väggarna först när betongen har nått $f_"ck" (t)$ ≥ #BY.regel MPa.
6. Kontrollera före gjutning: armeringens läge och täckskikt (distanser), plintarnas läge och storlek, startjärnen. Kontrollera före väggarnas gjutning: de lodräta järnen #A.txt, de vågräta järnen i V3 (#BY.hor3), vinkeljärnen i hörnen och stagningen. Under gjutningen: sättmått och stighastighet. Före återfyllning: betongens hållfasthet (temperaturgivare eller provkuber) och vibroplattans vikt.

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
- *Strimlan* ger för jämnt tryck 10 kPa över hela spännvidden $q L^2 slash 8$ = #D.valid.Ms kNm/m.
- *Hållfasthetstillväxten:* $beta_"cc" (7)$ = #D.valid.b7 för cement i klass N, alltså $f_"ck" (7)$ = #D.valid.f7 MPa. Mognadsfaktorn vid 10 °C är #D.valid.m10, alltså ett dygn vid 10 °C motsvarar #D.valid.m10 dygn vid 20 °C.
- *Sättning under balkarna* för hand: $w = sigma t slash E$ = #D.valid.sig kPa × 100 mm / #D.valid.Ed kPa = #D.valid.w_hand mm. FE-modellen ger högst #D.valid.w_fe mm.
- *Jämvikt i den samverkande modellen:* summan av lasten är lika med reaktionen från cellplasten under bottenplattan och plattan på mark (kN): #D.jamvikt.map(r => [#r.namn #r.last = #r.R]).join(", ").
#if D.nat != none [
- *Nätet:* grundnät 140 mm i stället för 200 mm (#D.nat.ne2 mot #D.nat.ne1 element i bottenplattan) ändrar största cellplasttryck (kvasipermanent last) från #D.nat.p1 till #D.nat.p2 kPa, #if D.nat.w1 == D.nat.w2 [sättningen inte alls (#D.nat.w1 mm)] else [sättningen från #D.nat.w1 till #D.nat.w2 mm] och rörlasterna högst #D.nat.dr %.
]
- *Kopplingen till K-05:* mellanbjälklagets nät, laster och lastmönster hämtas direkt från K-05:s program, så nätet är detsamma nod för nod.
