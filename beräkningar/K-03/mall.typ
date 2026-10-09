#let r = json("resultat.json")
#let p = r.projekt

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
#set heading(numbering: "1.1", supplement: [avsnitt])
#show heading.where(level: 1): it => {
  v(4pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => block(above: 8pt, below: 4pt, text(size: 10pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)
#let liten(body) = text(size: 8.5pt, body)
#let rod = rgb("#b5463a")
#let fet(b, s) = if b { strong(s) } else { s }

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Konstruktionsberäkning], [*Upprättad*], p.upprattad,
  [*Underlag*], [F-01, K-01, K-05 och modellen #r.modell.fil], ..if p.granskad != "" { ([*Granskad*], p.granskad) } else { ([], []) },
)

= Konstruktion och omfattning

Taket bärs så här: råspont på takbalkar 45×170 c/c 600 som spänner mellan nock- och dalbalkarna (K-01) eller till ytterväggen vid takfot. Nock- och dalbalkarna vilar på takstolar i gavlarna och i mittre huskroppens mitt och på stolpar ner till bjälklaget (K-05). Handlingen omfattar takbalkarna med takfönstren och deras upplag, de sju takstolarna och alla stolpar under nock- och dalbalkar och takstolar, däribland *huvudstolpen* LN1_3. Väggarnas reglar, hammarband och avväxlingar under takbalkarna vid takfot och den horisontella stabiliseringen redovisas i K-04.

Geometrin är hämtad ur modellen (#r.modell.fil) med `modell_k03.py`. Stolparna har samma beteckningar som lasterna i K-05: LN för nockbalkar, LD för dalbalkar och LA för hörnen under gavlarnas takstolar. Den äldre beräkningens beteckningar (A–H) står inom parentes.

#figure(image("fig_oversikt.svg", width: 100%), caption: [Takets bärande delar i plan, koordinater som i K-05. Röda stolpar räcker inte eller saknas i modellen, se tabellen nedan.])

#table(
  columns: (1.3fr, auto, auto, 1.6fr, auto),
  align: (left, right, left, left, right),
  [Del], [Antal], [Avsnitt], [Dimensionerande fall, som täcker de övriga], [Utnyttjande],
  [Takbalkar 45×170 c/c 600], [#r.tb.antal], [3.1], [Typ #r.tb.dim, #r.tb.dimtext: tvärkraft vid haket], [#r.tb.umax],
  [Upplag och förankring], [#r.tb.antal], [3.2], [Samma typ: hak, säte, skruv och lyft], [#r.tb.umax],
  [Takfönster], [#r.fon.len()], [3.3], [Takbalken bredvid öppningen], [#r.sammanf.at(1).u],
  [Takstolar], [#r.st.len()], [4], [Mittakstolen L2M under nockbalk 3, stöd C], [#r.sammanf.at(2).u],
  [*Huvudstolpen LN1_3*], [1], [5.1], [Stolpe med dubbeltriangel under nockbalk 1], [*#r.hs.u*],
  [Övriga stolpar], [#r.stolpar.len()], [5.2–5.3], [Varje stolpe i tabellen, hörnen LA1–LA10 i en rad], [#r.uS],
)

#block(stroke: 0.8pt + rod, inset: 6pt, radius: 2pt, width: 100%)[
  #text(fill: rod, weight: "bold")[Delar i modellen som inte räcker eller saknas]
  #table(
    columns: (1.25fr, 1.35fr, auto, 1.8fr),
    align: (left, left, right, left),
    [Del], [I modellen], [Utnyttjande], [Krav i denna handling, utnyttjande],
    ..r.brister.map(b => ([#b.del_], [#b.modell], [#text(fill: rod)[#b.utn]], [#b.krav])).flatten(),
  )
]

= Förutsättningar

- *Regler:* SS-EN 1990, SS-EN 1991-1-3, -1-4 och SS-EN 1995-1-1 med EKS 12. Säkerhetsklass 2 ($gamma_d$ = #r.kl.gd), klimatklass 1, $k_"mod"$ = #r.kl.kmod (snö) och #r.kl.kmodw (vind), $k_"def"$ = #r.kl.kdef, $k_"cr"$ = #r.kl.kcr.
- *Material:* konstruktionsvirke C24 ($f_"m,k"$ = #r.mat.C24.fmk, $f_"c,0,k"$ = #r.mat.C24.fc0k, $f_"c,90,k"$ = #r.mat.C24.fc90k, $f_"v,k"$ = #r.mat.C24.fvk MPa, $E_"0,05"$ = #r.mat.C24.E005 MPa, $gamma_M$ = 1,3) och limträ GL30h ($f_"c,0,k"$ = #r.mat.GL30h.fc0k, $f_"m,k"$ = #r.mat.GL30h.fmk MPa, $gamma_M$ = 1,25).
- *Egenvikt:* tak #r.last.g kN/m² takyta, #r.last.gh kN/m² horisontellt (F-01).
- *Snö:* $s_k$ = #r.last.sk kN/m². Takfall mot en dal räknas med $mu$ = #r.last.mud jämnt över hela takfallet (#r.last.sd kN/m²). Det är mer än den ansamlade snön enligt SS-EN 1991-1-3 5.3.4, där $mu_2$ = 1,6 bara nås i dalen. Takfall mot takfot räknas med $mu$ = #r.last.mut (#r.last.st kN/m², standarden ger 0,8).
- *Vind:* vindsug i zon G närmast gaveln, $c_"pe" - c_"pi"$ = #r.last.cpe och $q_p$ = #r.last.qp kN/m² (K-01), ger lyft #r.last.w kN/m². Lastkombination $1,0 G_k + gamma_d 1,5 W_k$.
- *Kombinationer:* 6.10a och 6.10b med $gamma_d$. Snön är huvudlast. Bruksgräns $w_"fin" lt.eq L slash$#r.kl.ned (F-01).
- *Stolparnas laster* kommer från K-05, som bygger på K-01:s stödreaktioner och gavlarnas takremsor. Huvudstolpens krafter är K-01:s, med stolpen 4 st 45×120.

= Takbalkar

== Takbalkarna

Takbalkarna är fritt upplagda mellan balkarnas centrumlinjer eller till ytterväggens centrum, med takutsprånget som konsol vid takfot. Spann och antal är tagna ur modellen. Lasten räknas per horisontell meter. Böjningen kontrolleras i fält (6.11). Tvärkraften kontrolleras vid haket över upplagsregeln (6.5.2), och nedböjningen räknas längs takbalken med $w_"fin" = w_G (1 + k_"def") + w_S (1 + psi_2 k_"def")$. Råsponten stagar den tryckta överkanten.

#table(
  columns: (auto, 1.6fr, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right, right, right, right),
  [Typ], [Läge], [Antal], [$L$ (m)], [Konsol (m)], [$mu$], [$M_d$ (kNm)], [Böjning], [Hak], [Säte], [$w_"fin"$ / krav (mm)],
  ..r.typer.map(t => (fet(t.dim, t.namn), [#t.text], [#t.antal], [#t.L], [#t.a], [#t.mu], [#t.M], [#t.um], fet(t.dim, t.uv), [#t.us], [#t.w (#t.uw)])).flatten(),
)
#liten[Hak: $tau_d = 1,5 V_d slash (k_"cr" b h_"ef") lt.eq k_v f_"v,d"$ med $h_"ef"$ = #r.tb.h_ef mm, $alpha$ = #r.tb.alfa, $x$ = #r.tb.x mm och $k_v$ = #r.tb.kv (6.62, $k_n$ = 5). Säte: lodrät kraft mot sätet med fibrerna 60° mot kraften, $f_"c,60,d"$ = #r.tb.fsate MPa (6.16), yta 45 × 45 mm.]

== Upplag mot nock- och dalbalkarna och förankring

#figure(image("fig_upplag.svg", width: 80%), caption: [Takbalkarnas upplag mot nockbalken, snitt tvärs balken. Vid dalbalken på samma sätt, spegelvänt.])

#[
    Takbalkens överkant ligger i balkens överkant, i isoleringens nivå (K-02). Takbalken är 196 mm hög i lodled, balken 190 mm. Takbalken vilar därför med ett hak på en upplagsregel 45×45 C24 längs balkens sida, ovanför underplåten. Sätet ligger #r.tb.z_sate mm över balkens underkant.

    - *Hak:* dimensionerande för typ #r.tb.dim, #r.tb.umax.
    - *Upplagsregeln:* tryck vinkelrätt fibrerna #r.tb.ureg. Skruv Ø6×100 genom regeln in i limträet bär #r.tb.Fv kN var (8.6, enkelskäriga trä–trä). Det krävs #r.tb.n_skruv skruv per takbalk.
    - *Lyft:* vindsuget ger högst #r.tb.lyft kN uppåt per takbalksände. En skruv Ø6×160 snett genom takbalken, 80 mm in i balken, bär #r.tb.Fax kN ($f_"ax,k"$ = 11 MPa enligt ETA), #r.tb.ulyft.
]

== Takfönster

Takfönstren TF1–TF3 är 1 200 mm breda och ligger mellan två takbalkar med avväxlingar 45×170 överst och nederst. Takbalkarna bredvid öppningen bär sitt eget halva fack och halva öppningen, 0,9 m, fördelat på antalet takbalkar. Avväxlingen bär en kortling c/c 600 som punktlast mitt på.

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, right, right, right, right),
  [Fönster], [y (mm)], [Takbalk], [Takbalkar vid sidorna], [Utnyttjande], [Avväxling], [Kortlingar], [Råspont utan kortlingar, $w$ (mm)],
  ..r.fon.map(f => ([TF#f.nr], [#f.y], [#f.typ], [#f.trim], [#f.utrim], [#f.uavv], [#f.kort], [#text(fill: rod)[#f.w]])).flatten(),
)
#liten[Takbalkar vid sidorna: antal takbalkar som står tätt intill öppningen på var sida i modellen. Råspont 20 mm över 1,2 m utan kortlingar, egenvikt och snö: kravet är #r.fon_wkrav mm ($L$/300). Kortlingar c/c 600 ovanför och nedanför fönstret behövs därför. Med dem räcker även en enkel takbalk vid sidan.]

= Takstolar

Takstolarna är trianglar av två diagonaler och ett dragband med spikplåtar i fötter och topp. Nockbalkens stödreaktion $P_d$ (K-01, via K-05) verkar i toppen, och takremsan (halva facken bredvid, i gaveln plus utsprånget) verkar jämnt på diagonalerna. Med halva spannet $a$ blir fotens reaktion $V = P slash 2 + q a$, dragbandets kraft $H = (P slash 2 + q a slash 2) slash tan 30°$ och diagonalens tryckkraft vid foten $N = H cos 30° + V sin 30°$. Diagonalen kontrolleras för tryck och böjning $M = q a^2 slash 8$ med knäckning i takstolens plan (6.23). Ur planet stagas den av takbalken ovanför innertaket ("extra" i modellen), som skruvas i diagonalen c/c 600. Snön räknas med $mu$ = #r.last.mud på hela takstolen.

#table(
  columns: (auto, 2fr, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, left, right, right, right, right, right, right),
  [Takstol], [Läge], [Bär], [$P_d$ (kN)], [Diagonal], [Utn.], [Dragband], [Utn.], [Spik], [Topp (mm)], [Skruv], [Topp], [Fot (mm)],
  ..r.st.map(t => (fet(t.dim, t.namn), [#t.text], [#t.stod], [#t.P], [#t.diag], [#t.ud], [#t.band], [#t.ub], [#t.spik], [#t.tkrav], [#t.nk], [#t.utopp], [#t.lfot])).flatten(),
)
#liten[Spik: ankarspik 4,0×40 per plåt och stav i foten, spikplåt 100×600×2,0 på båda sidor, #r.sp.Fv kN per spik (8.9, tunn plåt). Topp: tjocklek som krävs under balken, säte 200 mm (balkens bredd) med $f_"c,60,d"$ = #r.sp.ftopp MPa. Toppen har 45 mm och får toppklossar 45 mm på båda sidor, fästa med det antal skruv Ø6×90 som anges (#r.sp.Fvk_kloss kN per skruv). Utnyttjandet gäller 135 mm. Fot: minsta upplag på hammarbandet, $k_"c,90"$ = 1,5.]

#figure(image("fig_takstol.svg", width: 100%), caption: [Mittakstolen L2M i elevation ur modellen, med last och krafter. Gaveltakstolarna har samma form men bär mindre.])

*Mittakstolen L2M* bär nockbalk 3:s stöd C, $P_d$ = #r.L2M.P kN, och en takremsa på #r.L2M.bredd m, $q_d$ = #r.L2M.q kN/m. Med $a$ = #r.L2M.a m blir $V$ = #r.L2M.V kN, $H$ = #r.L2M.H kN och $N$ = #r.L2M.N kN. Diagonalen 45×#r.L2M.hd ($L$ = #r.L2M.Ld mm, $k_c$ = #r.L2M.kc) och $M$ = #r.L2M.M kNm ger #r.L2M.ud. Dragbandet 45×#r.L2M.hb ger #r.L2M.ub. Varje fot har spikplåtar på båda sidor med minst #r.L2M.spik ankarspik per plåt och stav, och plåten #r.L2M.plat. Foten behöver minst #r.L2M.lfot mm upplag på hammarbandet. Toppen behöver #r.L2M.tkrav mm tjocklek under balken. Med toppklossarna, fästa med #r.L2M.nk skruv Ø6×90, blir utnyttjandet #r.L2M.ut.

= Stolpar

== Huvudstolpen LN1_3 (F) <huvud>

#grid(
  columns: (1fr, 1.15fr),
  column-gutter: 10pt,
  figure(image("fig_huvudstolpe.svg", width: 100%), caption: [Huvudstolpen under nockbalk 1, stöd D. Strävor på båda sidor.]),
  [
    Huvudstolpen bär nockbalk 1 vid stöd D, direkt och via två strävor som når balken #r.hs.e mm från stolpen åt båda hållen. Stolpen, topregeln och strävorna bildar en *dubbeltriangel*. Modellen visar strävan bara på den ena sidan, men båda behövs. Stolpen är #r.hs.n st 45×#r.hs.h C24 sida vid sida, med #r.hs.h mm i strävornas plan och #r.hs.b mm i väggens plan, där väggen stagar den.

    - *Krafter (K-01):* $N_d$ = #r.hs.N kN och $M_d$ = #r.hs.M kNm, från gungbrädan mellan strävorna och stolpens böjstyvhet.
    - *Stolpen:* knäcklängd #r.hs.L mm i strävornas plan, $lambda_"rel"$ = #r.hs.lr och $k_c$ = #r.hs.kc. Med $N slash (k_c A f_"c,0,d") + M slash (W f_"m,d")$ blir utnyttjandet *#r.hs.u*.
    - *Strävorna:* 45×120 i fyra lager, #r.hs.Fax kN axiellt på var sida, #r.hs.Ns kN per lager: #r.hs.us.
    - *Topregeln:* den går i ett stycke över stolpen och tar strävornas vågräta kraft #r.hs.F kN i drag, #r.hs.ut. Under strävans topp krävs minst #r.hs.lt mm upplag mot balken.
    - *Knutpunkter:* spikplåt 100×400 på båda sidor med minst #r.hs.spik ankarspik per plåt och stav.
    - *Lyft:* stolpen förankras för #r.hs.lyft kN uppåt i topp och fot.
  ],
)

== Stolpe B (LD4_1)

Stolpe B bär dalbalk 4 vid stöd B och mittakstolens fot, $N_d$ = #r.B.N kN. Dalbalkens centrumlinje ligger #r.B.e mm från stolpens centrum, vilket ger $M_d$ = #r.B.M kNm. Stolpen är fristående. Som 115×115 GL30h, som i modellen, blir utnyttjandet #text(fill: rod)[*#r.B.mod*]. Med GL30h 140×140 på samma plats blir det *#r.B.krav*.

== Alla stolpar

Knäckning räknas med stolpens hela höjd. En vägg stagar stolpen i väggens plan när gipsskivan ligger tätt intill stolpen i modellen. Fristående stolpar av flera reglar skruvas ihop så att de verkar som ett tvärsnitt. Stolpar som står på syll eller under hammarband kontrolleras för tryck vinkelrätt fibrerna med 30 mm lastspridning åt båda håll (6.1.5), $k_"c,90"$ = 1,25 i syllen och 1,5 i hammarbandet.

#table(
  columns: (auto, 1.3fr, 1.2fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, right, right, right, right),
  [Stolpe], [Bär], [Utförande], [$L$ (mm)], [Stagning], [$N_d$ (kN)], [Knäckn.], [Syll], [Ham.band], [Lyft (kN)],
  ..r.stolpar.map(s => ([#s.namn#if s.gamla != "" [ (#s.gamla)]], [#s.bar], [#if s.krav [*#s.utf*] else [#s.utf]], [#s.L], [#s.stag], [#s.Nd], [#s.u], [#s.syll], [#s.ham], [#s.lyft])).flatten(),
)
#liten[Fetstil: utförande som krävs i denna handling, i stället för modellens (se tabellen i avsnitt 1). LA1–LA10: största värde för de tio hörnen. Lyft: dimensionerande dragkraft vid vindlyft (K-05), som stolpen förankras för i topp och fot. Huvudstolpen, se @huvud.]

= Sammanfattning och förutsättningar för utförandet

#table(
  columns: (1.4fr, auto, 1.6fr, auto),
  align: (left, right, left, right),
  [Del], [Antal], [Dimensionerande], [Största utnyttjande],
  ..r.sammanf.map(s => ([#s.del_], [#s.antal], [#s.dim], [#s.u])).flatten(),
)

Alla delar klarar brott- och bruksgränstillståndet med utförandet nedan. Delarna i den röda tabellen i avsnitt 1 klarar det inte som de är i modellen.

+ Takbalkar 45×170 C24 c/c 600 vilar med hak på upplagsregel 45×45 C24 längs nock- och dalbalkarnas sidor, ovanför underplåten. Regeln skruvas med #r.tb.n_skruv skruv Ø6×100 per takbalk. Varje takbalksände förankras med en skruv Ø6×160 snett in i balken.
+ Takfönster: kortlingar 45×170 c/c 600 ovanför och nedanför fönstret, burna av avväxlingar 45×170 mellan takbalkarna vid sidorna.
+ Takstolar: spikplåt 100×600×2,0 på båda sidor i fötterna och 100×400 i toppen, med ankarspik 4,0×40 enligt tabellen i avsnitt 4. Diagonalerna skruvas till takbalken ovanför innertaket c/c 600. Alla takstolar får toppklossar 45 mm, minst 600 mm långa, på båda sidor om toppen, skruvade enligt tabellen. Fötterna har minst det upplag på hammarbandet som tabellen anger.
+ Huvudstolpen LN1_3: 4 st 45×120 C24 med strävor 45×120 på båda sidor (dubbeltriangel) och en hel topregel över stolpen.
+ Stolpe B (LD4_1): GL30h 140×140. LD4_2: 5 st 45×95 C24. Stöd B i nockbalk 1 (LN1_1): ny stolpe 4 st 45×95 C24 i väggen vid y ≈ 2 795. Den sticker ut 25 mm ur den 70 mm tjocka väggen.
+ Stolpar av flera reglar skruvas ihop. Alla stolpar förankras i topp och fot för lyftkraften i tabellen.
