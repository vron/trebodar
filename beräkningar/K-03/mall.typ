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
  [*Underlag*], [F-01, K-01, K-05],   // geometrin är modellens (r.modell.fil), kontrollerad med kontroll_k03.py
  ..if p.granskad != "" { ([*Granskad*], p.granskad) } else { ([], []) },
)

= Konstruktion och omfattning

Taket bärs så här: råspont på ströläkt på takbalkar 45×170 c/c 600 som spänner mellan nock- och dalbalkarna eller till ytterväggen vid takfot. Nock- och dalbalkarna vilar på takstolar i gavlarna och i mittre huskroppens mitt och på stolpar ner till bjälklaget (K-05). Handlingen omfattar takbalkarna med takfönstren och deras upplag, yttertakets infästning mot vindsug, de sju takstolarna och alla stolpar under nock- och dalbalkar och takstolar. Väggarnas reglar, hammarband och avväxlingar under takbalkarna vid takfot och den horisontella stabiliseringen redovisas i K-04.

Stolparna har samma beteckningar som lasterna i K-05: LN för nockbalkar, LD för dalbalkar och LA för hörnen under gavlarnas takstolar.

#figure(image("fig_oversikt.svg", width: 100%), caption: [Takets bärande delar i plan.#if r.brister.len() > 0 [ Röda stolpar räcker inte eller saknas i modellen, se tabellen nedan.]])

#table(
  columns: (1.3fr, auto, 1.6fr, auto),
  align: (left, left, left, right),
  [Del], [Avsnitt], [Dimensionerande fall, som täcker de övriga], [Utnyttjande],
  [Takbalkar 45×170 c/c 600], [3.1], [Typ #r.tb.dim, #r.tb.dimtext: tvärkraft vid haket], [#r.tb.umax],
  [Upplag och förankring], [3.2], [Samma typ: hak, säte, skruv och lyft], [#r.tb.umax],
  [Takfönster], [3.3], [Takbalken bredvid öppningen], [#r.sammanf.at(1).u],
  [Yttertakets infästning], [3.4], [#r.sammanf.at(2).dim], [#r.sammanf.at(2).u],
  [Takstolar], [4], [Mittakstolen L2M under nockbalk 3, stöd C], [#r.sammanf.at(3).u],
  [Huvudstolpen LN1_3], [5.1], [Stolpe med dubbeltriangel under nockbalk 1], [#r.hs.u],
  [Övriga stolpar], [5.2–5.3], [Varje stolpe i tabellen, hörnen LA1–LA10 i en rad], [#r.uS],
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
- *Vind:* $q_p$ = #r.last.qp kN/m² (F-01, K-01). Vindsuget räknas med formfaktorerna för sadeltak 30° och lastytans storlek (SS-EN 1991-1-4 7.2.5 och figur 7.2), se @vindsug. Lastkombination $1,0 G_k + gamma_d 1,5 W_k$.
- *Kombinationer:* 6.10a och 6.10b med $gamma_d$. Snön är huvudlast. Bruksgräns $w_"fin" lt.eq L slash$#r.kl.ned (F-01).
- *Stolparnas laster* kommer från K-05.
// K-05 bygger på K-01:s stödreaktioner och gavlarnas takremsor. Huvudstolpens krafter är K-01:s, med stolpen 4 st 45×120.

= Takbalkar

== Takbalkarna

Takbalkarna är fritt upplagda mellan balkarnas centrumlinjer eller till ytterväggens centrum, med takutsprånget som konsol vid takfot. Lasten räknas per horisontell meter. Böjningen kontrolleras i fält (6.11). Tvärkraften kontrolleras vid haket över upplagsregeln (6.5.2), och nedböjningen räknas längs takbalken med $w_"fin" = w_G (1 + k_"def") + w_S (1 + psi_2 k_"def")$.
// Spann och antal ur modellen. Råsponten stagar den tryckta överkanten.

#table(
  columns: (auto, 1.6fr, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right, right, right),
  [Typ], [Läge], [$L$ (m)], [Konsol (m)], [$mu$], [$M_d$ (kNm)], [Böjning], [Hak], [Säte], [$w_"fin"$ / krav (mm)],
  ..r.typer.map(t => (fet(t.dim, t.namn), [#t.text], [#t.L], [#t.a], [#t.mu], [#t.M], [#t.um], fet(t.dim, t.uv), [#t.us], [#t.w (#t.uw)])).flatten(),
)
#liten[Haket är urtaget i takbalkens underkant vid änden, som takbalken vilar med på upplagsregeln (figur 2). Tvärkraften kontrolleras i takbalkens kvarvarande höjd ovanför urtaget, med hänsyn till att träet kan spricka från urtagets hörn. Sätet är hakets yta som ligger an mot regeln, där trycket mot träet kontrolleras.]
// Hak: τ_d = 1,5 V_d/(k_cr b h_ef) ≤ k_v f_v,d med h_ef = r.tb.h_ef mm, α = r.tb.alfa, x = r.tb.x mm, k_v = r.tb.kv (6.62, k_n = 5).
// Säte: lodrät kraft mot sätet med fibrerna 60° mot kraften, f_c,60,d = r.tb.fsate MPa (6.16), yta 45 × 45 mm.

== Upplag mot nock- och dalbalkarna och förankring

#figure(image("fig_upplag.svg", width: 80%), caption: [Takbalkarnas upplag mot nockbalken, snitt tvärs balken.]) <upplag>
// Vid dalbalken på samma sätt, spegelvänt, med takbalken och upplagsregeln högre upp på balkens sida.

#[
    Vid nockbalken ligger takbalkens överkant i balkens överkant, i isoleringens nivå. Takbalken är #r.tb.h_lod mm hög i lodled, balken #r.tb.balk_h mm. Takbalken vilar med ett hak på en upplagsregel 45×45 C24 längs balkens sida, ovanför underplåten. Sätet ligger #r.tb.z_sate mm över balkens underkant. Vid dalbalken möts takplanen i balkens överkant, så att luftspalten går fri över balken: takbalken ligger där högre på balkens sida, och upplagsregeln sitter så högt att haket får fullt säte.
    // Haket blir grundare vid dalbalken än vid nocken; det kontrolleras med nockens mått för båda ändarna, på säker sida.

    - *Hak:* dimensionerande för typ #r.tb.dim, #r.tb.umax.
    - *Upplagsregeln:* tryck vinkelrätt fibrerna #r.tb.ureg. Skruv Ø6×100 genom regeln in i limträet bär #r.tb.Fv kN var (8.6, enkelskäriga trä–trä). Det krävs #r.tb.n_skruv skruv per takbalk.
    - *Lyft:* vindsuget i gavelzonen ger högst #r.tb.lyft kN uppåt per takbalksände (typ #r.tb.lyft_typ: lastytan #r.tb.lyft_A m² ger $c_"pe"$ = #r.tb.lyft_cpe och med det inre trycket #r.tb.lyft_w kN/m², @vindsug). En skruv Ø6×160 snett genom takbalken, 80 mm in i balken, bär #r.tb.Fax kN ($f_"ax,k"$ = 11 MPa enligt ETA), #r.tb.ulyft.
]

== Takfönster

Takfönstren TF1–TF3 är 1 200 mm breda och ligger mellan två takbalkar med avväxlingar 45×170 överst och nederst. Takbalkarna bredvid öppningen bär sitt eget halva fack och halva öppningen, 0,9 m, fördelat på antalet takbalkar. Avväxlingen bär en kortling c/c 600 som punktlast mitt på.

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, right, right, right, right),
  [Fönster], [y (mm)], [Takbalk], [Takbalkar vid sidorna], [Utnyttjande], [Avväxling], [Kortlingar], [Råspont utan kortlingar, $w$ (mm)],
  ..r.fon.map(f => ([TF#f.nr], [#f.y], [#f.typ], [#f.trim], [#f.utrim], [#f.uavv], [#f.kort], [#f.w])).flatten(),
)
#liten[Takbalkar vid sidorna: antal takbalkar som står tätt intill öppningen på var sida. Kortlingar: ovanför och nedanför fönstret mitt i öppningen. Kortlingarna c/c 600 behövs ($L$/300 = #r.fon_wkrav mm).]
// Utan kortlingarna skulle råsponten 20 mm spänna 1,2 m, med nedböjningen i sista kolumnen (egenvikt och snö). Med dem
// räcker även en enkel takbalk vid sidan.

== Yttertakets infästning mot vindsug <vindsug>

Yttertaket hålls mot vindsuget i tre led. Plåten sitter med klammer i råsponten. Råsponten är spikad i ströläkten på takbalkarna och takstolarna. Läkten är skruvad genom hårdboarden i takbalken. De två mellanläkten i varje fack bär ingenting.

#grid(
  columns: (7.6cm, 1fr),
  column-gutter: 10pt,
  figure(image("fig_vindsug.svg", width: 100%), caption: [Röda delar ligger i randzonerna.]),   // ströläktens linjer i plan
  [
    *Vindsug.* Infästningar räknas med de lokala formfaktorerna $c_"pe,1"$ (lastyta högst 1 m²), och trycket under den lastade delen läggs till suget. Zonerna är $e slash 10$ = #r.yt.e10 m djupa i plan, #r.yt.e10s m längs takytan, med $e = 2 h$ = #r.yt.e m. Hela djupet från gavelkanten räknas med zon G:s värde. Huset har flera sadeltak i bredd, och randzonen gäller bara takfötter mot det fria (7.2.7).

    *Randzonen* är #r.yt.rand m från gavelkanter och fria takfötter.   // längs takytan; R-02 ritar den

    *Laster.* På plåten $w_d = gamma_d dot 1,5 dot w_k$. Läkten och spiken får $w_d$ minus egentyngden ovanför läkten, #r.yt.gn kN/m² vinkelrätt takytan, från en remsa på #r.yt.cc_lakt mm.
  ],
)

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right, right, right),
  [Zon], [$c_"pe,1"$], [Under], [$w_k$], [$w_d$], [Läkt], [c/c högst], [Vald c/c], [Skruv], [Spik], [Spik],
  [], [], [], [kN/m²], [kN/m²], [kN/m], [mm], [mm], [utn.], [N], [utn.],
  ..r.yt.zoner.map(z => ([*#z.namn.* #z.text], [#z.cpe1], [+#z.under], [#z.wk], [#z.wd], [#z.q], [#z.cc_max], [*#z.cc*], [#z.us], [#z.F], [#z.usp])).flatten(),
)
#liten[Randzonen räknas med det största av suget vid gavlarna och vid takfötterna. Under: trycket under den lastade delen, det inre trycket $c_"pi"$ = +0,2 eller vid takfötterna vindens tryck in i luftspaltens mynning, +0,8 (7.2.1). Läkt: lasten per meter läkt på takbalk. Spik: kraften per spik i råsponten.]

- *Ströläkten* #r.yt.lakt skruvas i varje takbalk och takstol med #r.yt.skruv (försänkt, C4), c/c #r.yt.cc_rand i randzonerna och c/c #r.yt.cc_ovrigt i övrigt. Huvudets genomdragning i läkten styr: $f_"head,k" d_h^2$ = #r.yt.Rhead kN ($f_"head,k"$ = #r.yt.fhead MPa, $d_h$ = #r.yt.dh mm). Gängans utdrag ur takbalken är #r.yt.Rax kN (#r.yt.lef mm gänga, $f_"ax,k"$ = #r.yt.fax MPa). $R_d$ = #r.yt.Rd kN med $k_"mod"$ = #r.kl.kmodw och $gamma_M$ = 1,3. Skruven sätts mitt i läkten och takbalken.   // r.yt.a2 mm från takbalkens kant, minst 4d = r.yt.a2krav mm (8.7.2)
- *Råsponten* spikas, eller skruvas med minst samma utdragsbärförmåga, med #r.yt.spik_n spik per bräda (#r.yt.spik) i varje läkt som ligger på en takbalk eller takstol (K-04). Spetsen sitter #r.yt.tpen mm i läkten, #r.yt.tpen_d $d$ (minst 12 $d$ för fullt värde, 8.3.2): $F_"ax,Rk"$ = #r.yt.Rspik_k N och $F_"ax,Rd"$ = #r.yt.Rspik_d N per spik. Släta spik får bara bära kortvarig last i utdrag, som vinden. Spiken räcker också med två tredjedelar av värdet, som gäller virke som torkar efter montaget (8.3.2): då är den utnyttjad till högst #r.yt.u_spik23.
- *Mellanläkten* bär ingenting och räknas inte i bärförmågan. Råsponten spikas i dem bara så att de ligger kvar, med kortare spik som inte går igenom läkten.
// Samma spik som på takbalkarna skulle sticka ut r.yt.ut_mellan mm under mellanläkten och gå igenom hårdboarden; där
// används r.yt.spik_mellan (står på R-02).
- *Plåten:* plåtslagaren dimensionerar klammerns delning för $w_d$ i tabellen.

= Takstolar

Takstolarna är trianglar av två diagonaler och ett dragband, prefabricerade med inpressade spikplåtar i fötter och topp (@spikplatar). Nockbalkens stödreaktion $P_d$ (K-01, via K-05) verkar i toppen, och takremsan (halva facken bredvid, i gaveln plus utsprånget) verkar jämnt på diagonalerna. Med halva spannet $a$ blir fotens reaktion $V = P slash 2 + q a$, dragbandets kraft $H = (P slash 2 + q a slash 2) slash tan 30°$ och diagonalens tryckkraft vid foten $N = H cos 30° + V sin 30°$. Diagonalen kontrolleras för tryck och böjning $M = q a^2 slash 8$ med knäckning i takstolens plan (6.23). Ur planet stagas den av takbalken ovanför innertaket, som skruvas i diagonalen c/c 600. Snön räknas med $mu$ = #r.last.mud på hela takstolen.

#table(
  columns: (auto, 2fr, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, left, right, right, right, right, right, right),
  [Takstol], [Läge], [Bär], [$P_d$ (kN)], [Diagonal], [Utn.], [Dragband], [Utn.], [Plåt fot], [Klossar], [Skruv], [Topp], [Fot (mm)],
  ..r.st.map(t => (fet(t.dim, t.namn), [#t.text], [#t.stod], [#t.P], [#t.diag], [#t.ud], [#t.band], [#t.ub], [#t.platfot], [#t.kloss], [#t.nk], [#t.utopp], [#t.lfot])).flatten(),
)
#liten[Plåt fot: spikplåtens bredd × längd (mm) i fötterna, på båda sidor (@spikplatar). Topp: under balken, säte #r.tb.balk_b mm (balkens bredd), bär diagonalernas ändar, 45 mm med fibrerna 30° ($f_"c,60,d"$ = #r.sp.ftopp MPa, 6.16), och toppklossen 45 mm på ena sidan med vågräta fibrer, tryck vinkelrätt fibrerna med $l_"ef"$ = #r.tb.balk_b + 2 × 30 mm och $k_"c,90" f_"c,90,d"$ = #r.sp.fc90 MPa (6.1.5). Klossen för sin del av lasten till takstolen med det antal skruv Ø6×90 som anges (#r.sp.Fvk_kloss kN per skruv). Fot: minsta upplag på hammarbandet, $k_"c,90"$ = 1,5.]

#figure(image("fig_takstol.svg", width: 100%), caption: [Mittakstolen L2M i elevation ur modellen, med last och krafter. Gaveltakstolarna har samma form men bär mindre.])

*Mittakstolen L2M* bär nockbalk 3:s stöd C, $P_d$ = #r.L2M.P kN, och en takremsa på #r.L2M.bredd m, $q_d$ = #r.L2M.q kN/m. Med $a$ = #r.L2M.a m blir $V$ = #r.L2M.V kN, $H$ = #r.L2M.H kN och $N$ = #r.L2M.N kN. Diagonalen 45×#r.L2M.hd ($L$ = #r.L2M.Ld mm, $k_c$ = #r.L2M.kc) och $M$ = #r.L2M.M kNm ger #r.L2M.ud. Dragbandet 45×#r.L2M.hb räknas för #r.L2M.Hdim kN: #r.L2M.ub. Varje fot har en spikplåt #r.L2M.platfot på båda sidor: #r.L2M.ufot. Foten behöver minst #r.L2M.lfot mm upplag på hammarbandet. Toppen med toppklossen, fäst med #r.L2M.nk skruv Ø6×90, är utnyttjad till #r.L2M.ut.
// Dragbandets kraft ur K-04:s balkmodell, där takbalkarna bär som sparrar mot dalbalkarna.

== Spikplåtar <spikplatar>

Takstolarna och huvudstolpens fyra lager är prefabricerade med hydrauliskt inpressade spikplåtar, #r.sp.produkt #r.sp.t mm eller likvärdiga, på båda sidor av varje knutpunkt. Plåtarna räknas enligt SS-EN 1995-1-1 8.8 med plåtens deklarerade värden (SS-EN 14545): förankringen $f_"a,0,0,k"$ = #r.sp.fa00 och $f_"a,90,90,k"$ = #r.sp.fa9090 N/mm², plåtens bärförmåga per mm $f_"t,0,k"$ = #r.sp.ft0, $f_"c,0,k"$ = #r.sp.fc0, $f_"v,0,k"$ = #r.sp.fv0 och $f_"v,90,k"$ = #r.sp.fv90 N/mm, $gamma_M$ = #r.sp.gM. Varje knutpunkt räknas med stavarnas konturer och plåten i modellens läge:

- *förankringen* i varje stav: kraften genom den effektiva kontaktytan $A_"ef"$ (5 mm från kanterna och 6 mm från ändarna bortom), med hållfastheten för kraftens vinkel mot plåten och mot fibrerna (8.8.4);
- *plåten* längs fogen mellan stavarna (8.8.5.2), och minsta överlapp på varje stav, 40 mm eller en tredjedel av stavens höjd.

Tryck går genom kontakt mellan stavarnas ändar, drag och skjuvning genom plåtarna: i takstolarnas fötter dragbandets kraft, i toppen lyftet vid vindsug och skjuvningen vid snö på ena takfallet, i huvudstolpen strävans lodräta kraft vid foten, dess vågräta kraft i toppen och lyftet över stolpens topp. Storlekarna är tillverkarens standardmått, grupperade så att få storlekar behövs: #r.sp.storlekar.join(", ", last: " och ") mm.

#table(
  columns: (1.2fr, 1fr, auto, auto, 1.8fr, auto),
  align: (left, left, left, right, left, right),
  [Knutpunkt], [], [Plåt (mm)], [Utn.], [$A_"ef"$ per stav (cm²)], [Fog (mm)],
  ..r.sp.knutar.map(k => ([#k.grupp], [#k.namn], [#k.storlek], [#k.u], [#k.A], [#k.l])).flatten(),
)
#liten[Plåt: bredd × längd. Fötterna: den ena foten (V); den andra är lika. Fog: fogens längd under plåten.]

= Stolpar

== Huvudstolpen LN1_3 <huvud>

#grid(
  columns: (1fr, 1.15fr),
  column-gutter: 10pt,
  figure(image("fig_huvudstolpe.svg", width: 100%), caption: [Huvudstolpen under nockbalk 1, stöd D. Strävor på båda sidor.]),
  [
    Huvudstolpen bär nockbalk 1 vid stöd D, direkt och via två strävor som når balken #r.hs.e mm från stolpen åt båda hållen. Stolpen, topregeln och strävorna bildar en *dubbeltriangel*. Stolpen är #r.hs.n st 45×#r.hs.h C24 sida vid sida, med #r.hs.h mm i strävornas plan och #r.hs.b mm i väggens plan, där väggen stagar den.

    - *Krafter (K-01):* $N_d$ = #r.hs.N kN och $M_d$ = #r.hs.M kNm, från gungbrädan mellan strävorna och stolpens böjstyvhet.
    - *Stolpen:* knäcklängd #r.hs.L mm i strävornas plan, $lambda_"rel"$ = #r.hs.lr och $k_c$ = #r.hs.kc. Med $N slash (k_c A f_"c,0,d") + M slash (W f_"m,d")$ blir utnyttjandet *#r.hs.u*.
    - *Strävorna:* 45×#r.hs.bs i fyra lager, #r.hs.Fax kN axiellt på var sida, #r.hs.Ns kN per lager: #r.hs.us.
    - *Topregeln:* den går i ett stycke över stolpen och tar strävornas vågräta kraft #r.hs.F kN i drag, #r.hs.ut. Under strävans topp krävs minst #r.hs.lt mm upplag mot balken.
    - *Knutpunkter:* lagren är prefabricerade som takstolarna, med inpressade spikplåtar på båda sidor av varje lager: #r.hs.plat_fot vid strävans fot, från stolpens mitt in på strävan (#r.hs.u_plat_fot), #r.hs.plat_topp längs strävan i dess topp (#r.hs.u_plat_topp) och #r.hs.plat_stolpe över stolpens topp (#r.hs.u_plat_stolpe), se @spikplatar.
    - *Lyft:* stolpen förankras för #r.hs.lyft kN uppåt i topp och fot.
    - *Förankringen vid foten:* stolpen står direkt på bjälklaget, mellan den lätta väggens två syllbitar. På var syllbit sitter ett vinkelbeslag mot stolpens ände, skruvat i stolpen och syllen, och en betongbult #r.hs.bult genom beslaget och syllen, minst #r.hs.bult_djup mm i plattan och borrad efter gjutningen. Två beslag bär $R_"1,k"$ = #r.hs.R1k kN (databladet, søjle på bjælke), $R_"1,d"$ = #r.hs.R1d kN ($k_"mod"$ 0,9, $gamma_M$ 1,35): #r.hs.ufot. Bulten får #r.hs.Nb kN i drag med beslagets bändning.
    // Beslaget: r.hs.beslag (ETA-06/0106) med r.hs.skruv per beslag; med beslagsöm i stället för skruv bara r.hs.R1d_spik kN.
    // Bulten r.hs.Nb0 kN utan bändning, faktor r.hs.band.
  ],
)

== LD4_1

LD4_1 bär dalbalk 4 och mittakstolens fot, $N_d$ = #r.B.N kN. Dalbalkens centrumlinje ligger #r.B.e mm från stolpens centrum, vilket ger $M_d$ = #r.B.M kNm. Stolpen är fristående, #r.B.utf: utnyttjandet blir *#r.B.u*.

== Andra stolpar

Knäckning räknas med stolpens hela höjd. En vägg stagar stolpen i väggens plan. Fristående stolpar av flera reglar skruvas ihop så att de verkar som ett tvärsnitt. LN3_1 och LN5_2 står i väggarnas ände med 83 mm under nockbalken, så att balken ligger mitt i takets spets: lasten verkar excentriskt i väggens plan (LN3_1 fyra reglar, 48,5 mm; LN5_2 fem reglar, 71 mm), och stolpen räknas för tryck med knäckning ut ur väggens plan, med reglarna skruvade ihop så att lasten fördelas på alla. Stolpar som står på syll eller under hammarband kontrolleras för tryck vinkelrätt fibrerna med 30 mm lastspridning åt båda håll (6.1.5), $k_"c,90"$ = 1,25 i syllen och 1,5 i hammarbandet.

#table(
  columns: (auto, 1.3fr, 1.2fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, left, right, left, right, right, right, right, right),
  [Stolpe], [Bär], [Utförande], [$L$ (mm)], [Stagning], [$N_d$ (kN)], [Knäckn.], [Syll], [Ham.band], [Lyft (kN)],
  ..r.stolpar.map(s => ([#s.namn], [#s.bar], [#if s.krav [*#s.utf*] else [#s.utf]], [#s.L], [#s.stag], [#s.Nd], [#s.u], [#s.syll], [#s.ham], [#s.lyft])).flatten(),
)
#liten[#if r.stolpar.any(s => s.krav) [Fetstil: utförande som krävs i denna handling, i stället för modellens (se tabellen i avsnitt 1). ]LA1–LA10: största värde för de tio hörnen. Lyft: dimensionerande dragkraft, som stolpen förankras för i topp och fot.]
// Lyftet är K-01:s minsta stödreaktion (vindlyft eller snö fält för fält längs balken, K-05). Förankringen vid foten är
// prövad för den i K-04; förbandet i toppen, mellan stolpen och balken, är inte utformat (#129).

= Sammanfattning

#table(
  columns: (1.4fr, 1.6fr, auto),
  align: (left, left, right),
  [Del], [Dimensionerande], [Största utnyttjande],
  ..r.sammanf.map(s => ([#s.del_], [#s.dim], [#s.u])).flatten(),
)

#if r.brister.len() > 0 [Delarna i den röda tabellen i avsnitt 1 klarar inte kraven som de är i modellen.]

// Förutsättningar för utförandet (står på R-01, R-02 och i tabellerna ovan): takbalkarna med hak på upplagsregel 45×45
// längs nock- och dalbalkarnas sidor, regeln med r.tb.n_skruv skruv Ø6×100 per takbalk, varje takbalksände förankrad med
// en skruv Ø6×160 snett in i balken; takfönstren med kortlingar 45×170 c/c 600 på avväxlingar; ströläkten skruvad c/c
// 300 i randzonerna och 600 i övrigt, råsponten med 2 spik per bräda i varje läkt på takbalk eller takstol; takstolarna
// med spikplåtar och toppkloss enligt avsnitt 4; huvudstolpen 4 st 45×120 med strävor och hel topregel; LD4_1 GL30h
// 140×140, LD4_2 5 st 45×145 med närmaste regel tätt intill eller minst 60 mm ifrån; stolpar av flera reglar
// ihopskruvade, LN3_1 och LN5_2 med helgängade skruvar; alla stolpar förankrade för lyftet i tabellen.
