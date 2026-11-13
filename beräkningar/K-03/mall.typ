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

Geometrin är modellens (#r.modell.fil) och är kontrollerad mot den. Stolparna har samma beteckningar som lasterna i K-05: LN för nockbalkar, LD för dalbalkar och LA för hörnen under gavlarnas takstolar. Den äldre beräkningens beteckningar (A–H) står inom parentes.

#figure(image("fig_oversikt.svg", width: 100%), caption: [Takets bärande delar i plan, koordinater som i K-05.#if r.brister.len() > 0 [ Röda stolpar räcker inte eller saknas i modellen, se tabellen nedan.]])

#table(
  columns: (1.3fr, auto, auto, 1.6fr, auto),
  align: (left, right, left, left, right),
  [Del], [Antal], [Avsnitt], [Dimensionerande fall, som täcker de övriga], [Utnyttjande],
  [Takbalkar 45×170 c/c 600], [#r.tb.antal], [3.1], [Typ #r.tb.dim, #r.tb.dimtext: tvärkraft vid haket], [#r.tb.umax],
  [Upplag och förankring], [#r.tb.antal], [3.2], [Samma typ: hak, säte, skruv och lyft], [#r.tb.umax],
  [Takfönster], [#r.fon.len()], [3.3], [Takbalken bredvid öppningen], [#r.sammanf.at(1).u],
  [Takstolar], [#r.st.len()], [4], [Mittakstolen L2M under nockbalk 3, stöd C], [#r.sammanf.at(2).u],
  [*Huvudstolpen LN1_3*], [1], [5.1], [Stolpe med dubbeltriangel under nockbalk 1], [*#r.hs.u*],
  [Övriga stolpar], [#r.sammanf.last().antal], [5.2–5.3], [Varje stolpe i tabellen, hörnen LA1–LA10 i en rad], [#r.uS],
)

#if r.brister.len() > 0 [
#block(stroke: 0.8pt + rod, inset: 6pt, radius: 2pt, width: 100%)[
  #text(fill: rod, weight: "bold")[Delar i modellen som inte räcker eller saknas]
  #table(
    columns: (1.25fr, 1.35fr, auto, 1.8fr),
    align: (left, left, right, left),
    [Del], [I modellen], [Utnyttjande], [Krav i denna handling, utnyttjande],
    ..r.brister.map(b => ([#b.del_], [#b.modell], [#text(fill: rod)[#b.utn]], [#b.krav])).flatten(),
  )
]
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

#figure(image("fig_upplag.svg", width: 80%), caption: [Takbalkarnas upplag mot nockbalken, snitt tvärs balken. Vid dalbalken på samma sätt, spegelvänt, med takbalken och upplagsregeln högre upp på balkens sida.])

#[
    Vid nockbalken ligger takbalkens överkant i balkens överkant, i isoleringens nivå (K-02). Takbalken är #r.tb.h_lod mm hög i lodled, balken #r.tb.balk_h mm. Takbalken vilar med ett hak på en upplagsregel 45×45 C24 längs balkens sida, ovanför underplåten. Sätet ligger #r.tb.z_sate mm över balkens underkant. Vid dalbalken möts takplanen i balkens överkant, så att luftspalten går fri över balken (U-03): takbalken ligger där högre på balkens sida, upplagsregeln sitter så högt att haket får fullt säte, och haket blir grundare än vid nocken. Haket kontrolleras med nockens mått för båda ändarna, på säker sida.

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
  ..r.fon.map(f => ([TF#f.nr], [#f.y], [#f.typ], [#f.trim], [#f.utrim], [#f.uavv], [#f.kort], [#f.w])).flatten(),
)
#liten[Takbalkar vid sidorna: antal takbalkar som står tätt intill öppningen på var sida i modellen. Kortlingar: i modellen, ovanför och nedanför fönstret mitt i öppningen. Utan dem skulle råsponten 20 mm spänna 1,2 m, med nedböjningen i sista kolumnen (egenvikt och snö) mot kravet #r.fon_wkrav mm ($L$/300). Kortlingarna c/c 600 behövs därför. Med dem räcker även en enkel takbalk vid sidan.]

= Takstolar

Takstolarna är trianglar av två diagonaler och ett dragband med spikplåtar i fötter och topp. Nockbalkens stödreaktion $P_d$ (K-01, via K-05) verkar i toppen, och takremsan (halva facken bredvid, i gaveln plus utsprånget) verkar jämnt på diagonalerna. Med halva spannet $a$ blir fotens reaktion $V = P slash 2 + q a$, dragbandets kraft $H = (P slash 2 + q a slash 2) slash tan 30°$ och diagonalens tryckkraft vid foten $N = H cos 30° + V sin 30°$. Diagonalen kontrolleras för tryck och böjning $M = q a^2 slash 8$ med knäckning i takstolens plan (6.23). Ur planet stagas den av takbalken ovanför innertaket ("extra" i modellen), som skruvas i diagonalen c/c 600. Snön räknas med $mu$ = #r.last.mud på hela takstolen.

#table(
  columns: (auto, 2fr, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, left, right, right, right, right, right, right),
  [Takstol], [Läge], [Bär], [$P_d$ (kN)], [Diagonal], [Utn.], [Dragband], [Utn.], [Spik], [Klossar], [Skruv], [Topp], [Fot (mm)],
  ..r.st.map(t => (fet(t.dim, t.namn), [#t.text], [#t.stod], [#t.P], [#t.diag], [#t.ud], [#t.band], [#t.ub], [#t.spik], [#t.kloss], [#t.nk], [#t.utopp], [#t.lfot])).flatten(),
)
#liten[Spik: ankarspik 4,0×40 per plåt och stav i foten, spikplåt 100×600×2,0 på båda sidor, #r.sp.Fv kN per spik (8.9, tunn plåt). Topp: under balken, säte #r.tb.balk_b mm (balkens bredd), bär diagonalernas ändar, 45 mm med fibrerna 30° ($f_"c,60,d"$ = #r.sp.ftopp MPa, 6.16), och toppklossen 45 mm på ena sidan med vågräta fibrer, tryck vinkelrätt fibrerna med $l_"ef"$ = #r.tb.balk_b + 2 × 30 mm och $k_"c,90" f_"c,90,d"$ = #r.sp.fc90 MPa (6.1.5). Klossen för sin del av lasten till takstolen med det antal skruv Ø6×90 som anges (#r.sp.Fvk_kloss kN per skruv). Fot: minsta upplag på hammarbandet, $k_"c,90"$ = 1,5.]

#figure(image("fig_takstol.svg", width: 100%), caption: [Mittakstolen L2M i elevation ur modellen, med last och krafter. Gaveltakstolarna har samma form men bär mindre.])

*Mittakstolen L2M* bär nockbalk 3:s stöd C, $P_d$ = #r.L2M.P kN, och en takremsa på #r.L2M.bredd m, $q_d$ = #r.L2M.q kN/m. Med $a$ = #r.L2M.a m blir $V$ = #r.L2M.V kN, $H$ = #r.L2M.H kN och $N$ = #r.L2M.N kN. Diagonalen 45×#r.L2M.hd ($L$ = #r.L2M.Ld mm, $k_c$ = #r.L2M.kc) och $M$ = #r.L2M.M kNm ger #r.L2M.ud. Dragbandet 45×#r.L2M.hb ger #r.L2M.ub. Varje fot har spikplåtar på båda sidor med minst #r.L2M.spik ankarspik per plåt och stav, och plåten #r.L2M.plat. Foten behöver minst #r.L2M.lfot mm upplag på hammarbandet. Toppen med toppklossen, fäst med #r.L2M.nk skruv Ø6×90, är utnyttjad till #r.L2M.ut.

= Stolpar

== Huvudstolpen LN1_3 (F) <huvud>

#grid(
  columns: (1fr, 1.15fr),
  column-gutter: 10pt,
  figure(image("fig_huvudstolpe.svg", width: 100%), caption: [Huvudstolpen under nockbalk 1, stöd D. Strävor på båda sidor.]),
  [
    Huvudstolpen bär nockbalk 1 vid stöd D, direkt och via två strävor som når balken #r.hs.e mm från stolpen åt båda hållen. Stolpen, topregeln och strävorna bildar en *dubbeltriangel*. Stolpen är #r.hs.n st 45×#r.hs.h C24 sida vid sida, med #r.hs.h mm i strävornas plan och #r.hs.b mm i väggens plan, där väggen stagar den.

    - *Krafter (K-01):* $N_d$ = #r.hs.N kN och $M_d$ = #r.hs.M kNm, från gungbrädan mellan strävorna och stolpens böjstyvhet.
    - *Stolpen:* knäcklängd #r.hs.L mm i strävornas plan, $lambda_"rel"$ = #r.hs.lr och $k_c$ = #r.hs.kc. Med $N slash (k_c A f_"c,0,d") + M slash (W f_"m,d")$ blir utnyttjandet *#r.hs.u*.
    - *Strävorna:* 45×120 i fyra lager, #r.hs.Fax kN axiellt på var sida, #r.hs.Ns kN per lager: #r.hs.us.
    - *Topregeln:* den går i ett stycke över stolpen och tar strävornas vågräta kraft #r.hs.F kN i drag, #r.hs.ut. Under strävans topp krävs minst #r.hs.lt mm upplag mot balken.
    - *Knutpunkter:* spikplåt 100×400 på båda sidor med minst #r.hs.spik ankarspik per plåt och stav.
    - *Lyft:* stolpen förankras för #r.hs.lyft kN uppåt i topp och fot.
    - *Förankringen vid foten:* stolpen står direkt på bjälklaget, mellan den lätta väggens två syllbitar. På var syllbit sitter ett vinkelbeslag #r.hs.beslag (ETA-06/0106) mot stolpens ände, med #r.hs.skruv i stolpen och syllen, och en betongbult #r.hs.bult genom beslaget och syllen, minst #r.hs.bult_djup mm i plattan och borrad efter gjutningen. Två beslag bär $R_"1,k"$ = #r.hs.R1k kN (databladet, søjle på bjælke), $R_"1,d"$ = #r.hs.R1d kN ($k_"mod"$ 0,9, $gamma_M$ 1,35): #r.hs.ufot. Med beslagsöm i stället för skruv blir det bara #r.hs.R1d_spik kN. Bulten får #r.hs.Nb0 kN, #r.hs.Nb kN i drag med beslagets bändning (#r.hs.band).
  ],
)

== Stolpe B (LD4_1)

Stolpe B bär dalbalk 4 vid stöd B och mittakstolens fot, $N_d$ = #r.B.N kN. Dalbalkens centrumlinje ligger #r.B.e mm från stolpens centrum, vilket ger $M_d$ = #r.B.M kNm. Stolpen är fristående, #r.B.utf: utnyttjandet blir *#r.B.u*.

== Alla stolpar

Knäckning räknas med stolpens hela höjd. En vägg stagar stolpen i väggens plan när gipsskivan ligger tätt intill stolpen i modellen. Fristående stolpar av flera reglar skruvas ihop så att de verkar som ett tvärsnitt. LN3_1 och LN5_2 står i väggarnas ände med 83 mm under nockbalken, så att balken ligger mitt i takets spets: lasten verkar excentriskt i väggens plan (LN3_1 fyra reglar, 48,5 mm; LN5_2 fem reglar, 71 mm), och stolpen räknas för tryck med knäckning ut ur väggens plan och böjning i den (6.24), med reglarna skruvade ihop så att lasten fördelas på alla. Stolpar som står på syll eller under hammarband kontrolleras för tryck vinkelrätt fibrerna med 30 mm lastspridning åt båda håll (6.1.5), $k_"c,90"$ = 1,25 i syllen och 1,5 i hammarbandet.

#table(
  columns: (auto, 1.3fr, 1.2fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, right, right, right, right),
  [Stolpe], [Bär], [Utförande], [$L$ (mm)], [Stagning], [$N_d$ (kN)], [Knäckn.], [Syll], [Ham.band], [Lyft (kN)],
  ..r.stolpar.map(s => ([#s.namn#if s.gamla != "" [ (#s.gamla)]], [#s.bar], [#if s.krav [*#s.utf*] else [#s.utf]], [#s.L], [#s.stag], [#s.Nd], [#s.u], [#s.syll], [#s.ham], [#s.lyft])).flatten(),
)
#liten[#if r.stolpar.any(s => s.krav) [Fetstil: utförande som krävs i denna handling, i stället för modellens (se tabellen i avsnitt 1). ]LA1–LA10: största värde för de tio hörnen. Lyft: dimensionerande dragkraft vid vindlyft (K-05), som stolpen förankras för i topp och fot. Huvudstolpen, se @huvud.]

= Sammanfattning och förutsättningar för utförandet

#table(
  columns: (1.4fr, auto, 1.6fr, auto),
  align: (left, right, left, right),
  [Del], [Antal], [Dimensionerande], [Största utnyttjande],
  ..r.sammanf.map(s => ([#s.del_], [#s.antal], [#s.dim], [#s.u])).flatten(),
)

Alla delar klarar brott- och bruksgränstillståndet med utförandet nedan#if r.brister.len() == 0 [, som är modellens].#if r.brister.len() > 0 [ Delarna i den röda tabellen i avsnitt 1 klarar det inte som de är i modellen.]

+ Takbalkar 45×170 C24 c/c 600 vilar med hak på upplagsregel 45×45 C24 längs nock- och dalbalkarnas sidor, ovanför underplåten. Regeln skruvas med #r.tb.n_skruv skruv Ø6×100 per takbalk. Varje takbalksände förankras med en skruv Ø6×160 snett in i balken.
+ Takfönster: kortlingar 45×170 c/c 600 ovanför och nedanför fönstret, burna av avväxlingar 45×170 mellan takbalkarna vid sidorna.
+ Takstolar: spikplåt 100×600×2,0 på båda sidor i fötterna och 100×400 i toppen, med ankarspik 4,0×40 enligt tabellen i avsnitt 4. Diagonalerna skruvas till takbalken ovanför innertaket c/c 600. Varje takstol har en toppkloss 45 mm, 600 mm lång, på ena sidan om toppen (gavelstolarna på insidan, mittakstolen på den nordöstra sidan), skruvad enligt tabellen. Fötterna har minst det upplag på hammarbandet som tabellen anger.
+ Huvudstolpen LN1_3: 4 st 45×120 C24 med strävor 45×120 på båda sidor (dubbeltriangel) och en hel topregel över stolpen.
+ Stolpe B (LD4_1): GL30h 140×140. LD4_2: #r.stolpar.find(s => s.namn == "LD4_2").utf sida vid sida under dalbalk 4:s ände. Närmaste regel bredvid gruppen står tätt intill den eller minst 60 mm ifrån, så att lasten sprids 30 mm åt båda håll i syllen. LN1_1 under nockbalk 1:s stöd B: #r.stolpar.find(s => s.namn == "LN1_1").utf i väggen vid y ≈ 2 795.
+ Stolpar av flera reglar skruvas ihop, LN3_1 och LN5_2 med helgängade skruvar så att balkens excentriska last fördelas på alla reglarna. Alla stolpar förankras i topp och fot för lyftkraften i tabellen. Huvudstolpen förankras vid foten med två vinkelbeslag #r.hs.beslag, fullt utskruvade med skruv (inte spik), och en betongbult #r.hs.bult genom vart (@huvud).
