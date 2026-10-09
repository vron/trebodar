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
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  v(5pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => {
  block(below: 4pt, text(size: 10.5pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)
#let ok(b) = if b [OK] else [*EJ OK*]
#let liten(body) = text(size: 8.5pt, body)

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Konstruktionsberäkning], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Konstruktion

Nock- och dalbalkarna är limträ #r.geo.b × #r.hw mm i hel längd. I fält där limträet inte räcker till förses balken med plattstål #r.geo.b × #r.geo.t_pl i över- och underkant och får samma yttermått som HE 200 A, #r.geo.b × #r.geo.h_tot mm. Där plåt saknas sätts distansreglar #r.distans.tjocklek mm på ovan- och undersidan. Plåtarna tar böjmomentet som tryck- och dragkraft, och limträet för över tvärkraften mellan dem. Plåtarna fästs med lim och skruv. I brottgränstillståndet tillgodoräknas endast skruvarna, i bruksgränstillståndet även limmet.

Plåtarna ligger i de långa fälten och går ut till balkänden där de når den. Övriga fält klarar limträet ensamt.

#grid(
  columns: (auto, 1fr),
  column-gutter: 10pt,
  align(left + horizon, image("fig_sektion.svg")),
  table(
    columns: (auto, 1fr),
    [Del], [Utförande],
    [Plåtar], [Plattstål #r.geo.b×#r.geo.t_pl, #r.stal.kvalitet enligt #r.stal.standard.],
    [Limträ], [#r.tra.kvalitet enligt #r.tra.standard, #r.geo.b×#r.hw i hel längd. Fuktkvot #r.tra.fuktkvot.],
    [Distans], [Reglar #r.geo.b×#r.distans.tjocklek där plåt saknas, inga krav på limning. Glipa #r.distans.glipa mm mot plåtänden.],
    [Lim mot stål], [Tvåkomponents strukturepoxi för limning av stål (t.ex. Sikadur-30). Heltäckande fog mot båda plåtarna i hela plåtlängden.],
    [Skruv], [#r.skruv.produkt (#r.skruv.kod, #r.skruv.eta)#footnote[Finns hos #link(r.skruv.lank)[#r.skruv.leverantor]. Mått och värden ur tillverkarens #link(r.skruv.datablad)[datablad]. En annan skruv kräver ny kontroll av bärförmågan och av hålens diameter.], skruv för stålplåt med ansats under huvudet. Kärndiameter #r.skruv.d1 mm, $M_"y,Rk"$ = #r.skruv.My_Rk Nm. #r.skruv.korrosion. Skruven sätts vinkelrätt mot plåten och går #r.intr mm in i limträet. Gängan börjar #r.ganga_start mm in i limträet.],
    [Hål], [Ø#r.skruv.hal enligt tillverkaren, cylindriska genom hela plåten, utan försänkning. Ansatsen under huvudet (Ø#r.skruv.ansats) fyller hålet. Huvudet (Ø#r.skruv.huvud_d) ligger an mot plåten och sticker ut #r.skruv.huvud mm. Förborrning i limträet genom plåthålen med Ø#r.skruv.forborr, lika djupt som skruven. Skruven dras i ett drag tills huvudet ligger an mot plåten, med högst #r.skruv.moment Nm (momentbegränsare eller momentnyckel), inte med slagskruvdragare.],
    [Placering], [Två rader, #r.skruv.rader2.at(0) och #r.skruv.rader2.at(1) mm från plåtens ena långkant. Där delningen _s_ är under #r.skruv.s_tre_rader mm används tre rader (även #r.skruv.rader3.at(1) mm). Skruvarna fördelas på raderna så att c/c i varje rad blir minst #r.a1ax_min mm. Första skruv #r.skruv.ande mm från balkände och #r.skruv.ande_plat mm från plåtände inne på balken.],
  ),
)

#grid(
  columns: (auto, 1fr),
  column-gutter: 14pt,
  align(horizon, image("fig_plan.svg")),
  align(horizon)[
    *Limning.* #r.lim.forbehandling_stal. Träytan ska vara #lower(r.lim.forbehandling_tra). #r.lim.pressning. Härdning #r.lim.hardning. #r.stal.korrosion
  ],
)

= Förutsättningar och laster

SS-EN 1990, SS-EN 1991-1-3, SS-EN 1991-1-5, SS-EN 1993-1-1 och SS-EN 1995-1-1 med Boverkets tillämpning enligt #p.regelverk. Säkerhetsklass 2 ($gamma_d$ = #r.laster.gamma_d), klimatklass 1, $k_"mod"$ = #r.tra.k_mod (snö, medellång lastvaraktighet), $k_"def"$ = #r.tra.k_def.

Takets egenvikt #r.laster.g_tak kN/m² takyta ger #r.g_tak_h kN/m² horisontellt (division med cos #r.laster.takvinkel°). Grundvärdet för snölast är $s_k$ = #r.laster.s_k kN/m² (Tanum), $C_e$ = $C_t$ = 1,0. Dalbalkarna antas få all snö från avståndet mellan nockarna, #r.last.dal.snobredd m, med formfaktor 1,0. Det är mer än den ansamlade snön enligt SS-EN 1991-1-3 5.3.4 ($mu_2$ = 1,6 över lastbredden ger #r.S_mu2 kN/m). Nockbalkarna räknas med lastbredden #r.last.nock.lastbredd m och formfaktor 1,0 (standarden ger $mu_1$ = 0,8). Temperaturpåverkan behandlas i avsnitt 4.

#table(
  columns: (1fr, auto, auto, auto),
  align: (left, left, right, right),
  [Last per meter balk (kN/m)], [Underlag], [Nockbalk], [Dalbalk],
  [Egenvikt tak], [#r.g_tak_h kN/m² × lastbredd #r.last.nock.lastbredd / #r.last.dal.lastbredd m], [#r.last.nock.g_tak], [#r.last.dal.g_tak],
  [Egenvikt balk med plåt], [#r.m_balk kg/m], [#r.g_balk], [#r.g_balk],
  [Egenvikt balk utan plåt], [#r.m_utan kg/m (limträ och distansreglar)], [#r.g_utan], [#r.g_utan],
  [$G_k$ med plåt / utan plåt], [], [#r.last.nock.G / #r.last.nock.G_utan], [#r.last.dal.G / #r.last.dal.G_utan],
  [$S_k$ snö], [$s_k$ × #r.last.nock.snobredd / #r.last.dal.snobredd m], [#r.last.nock.S], [#r.last.dal.S],
  [$q_d$ ekv. 6.10b], [#r.gG_610b $G_k$ + #r.gQ $S_k$], [*#r.last.nock.q610b*], [*#r.last.dal.q610b*],
  [$q_d$ ekv. 6.10a], [#r.gG_610a $G_k$ + #r.gQ_610a $S_k$], [#r.last.nock.q610a], [#r.last.dal.q610a],
  [$q_d$ egenvikt gynnsam], [1,0 $G_k$ + #r.gQ $S_k$], [#r.last.nock.qgynn], [#r.last.dal.qgynn],
  [$q_k$ karakteristisk], [$G_k + S_k$], [#r.last.nock.qk], [#r.last.dal.qk],
  [$W_k$ vindsug, zon G / H / I], [$q_p (c_"pe" - c_"pi")$ × lastbredd], [#r.vindlast.nock.W.G / #r.vindlast.nock.W.H / #r.vindlast.nock.W.I], [#r.vindlast.dal.W.G / #r.vindlast.dal.W.H / #r.vindlast.dal.W.I],
  [$q_d$ vindlyft, zon G / H / I], [1,0 $G_k$ + #r.vind.gW $W_k$], [#r.vindlast.nock.qW.G / #r.vindlast.nock.qW.H / #r.vindlast.nock.qW.I], [#r.vindlast.dal.qW.G / #r.vindlast.dal.qW.H / #r.vindlast.dal.qW.I],
)
#liten[Lastkombinationer enligt EKS: 6.10a $gamma_d #"1,35" G_k + gamma_d #"1,5" psi_0 S_k$ och 6.10b $gamma_d #"1,2" G_k + gamma_d #"1,5" S_k$ med $psi_0$ = #r.laster.psi0 och $psi_2$ = #r.laster.psi2 (snö, $1 <= s_k < 2$). Där egentyngden verkar gynnsamt (lyft vid stöd) används 1,0 $G_k$. Balkens egenvikt räknas med plåt där plåt finns och utan plåt i övrigt. Negativ last verkar uppåt.]

*Vind.* Vindlyft på taket räknas enligt SS-EN 1991-1-4 med referensvindhastigheten $v_b$ = #r.vind.vb m/s (Tanum), terrängtyp #r.vind.terrang och referenshöjden #r.vind.z m. Det ger $q_b$ = #r.vind.qb kN/m² och $q_p$ = #r.vind.qp kN/m² ($c_e$ = #r.vind.ce). Störst lyft ger vind längs nocken (tabell 7.4b, takvinkel 30°): $c_"pe"$ = #r.vind.cpe.G i zon G närmast gaveln (#r.vind.e10 m), #r.vind.cpe.H i zon H (till #r.vind.e2 m) och #r.vind.cpe.I i zon I, med $e$ = #r.vind.e m. Invändigt övertryck $c_"pi"$ = +#r.vind.cpi ger netto #r.vind.cnet.G / #r.vind.cnet.H / #r.vind.cnet.I. Zonerna räknas från båda balkändarna. Lastkombinationen är 1,0 $G_k$ + $gamma_d$ 1,5 $W_k$ utan snö. Vindens tryck på taket ger nedåtriktad last som är liten jämfört med snön och styr inte.

*Snöns placering.* Snön kan ligga ojämnt längs balken, till exempel efter snöras, ensidig avsmältning eller skottning. Varje lastkombination prövas därför med snö på alla kombinationer av belastade och obelastade fält, medan egentyngden alltid verkar på hela balken.

= Beräkningsmodell

*Statiskt system.* Balkarna går kontinuerligt över flera stöd. Varje balk räknas med tre modeller, och skruv, plåt och limträ dimensioneras för det ogynnsammaste resultatet i varje snitt:

#pad(left: 10pt)[
  (a) kontinuerlig balk med förankrade stöd och fältvis snö enligt avsnitt 2, samt vindlyft, \
  (b) som (a), men stöden tar bara tryck: balken får lyfta från ett stöd som annars skulle få dragkraft, \
  (c) varje fält fritt upplagt med full last. Det ger största möjliga fältmoment oberoende av kontinuiteten.
]

#for b in r.balkar.filter(b => b.vagg) [#b.namn vilar på en innervägg över #b.vagg_txt mm. ]Väggen modelleras som ett styvt underlag som bara tar tryck (#r.modell.k_vagg N/mm per mm). Snön i det fria fältet böjer ned balken över väggens ände. Balken trycks då hårt mot själva väggänden och vill lyfta en bit in på väggen, där bara lasten ovanpå håller den ned. Modellen låter balken lyfta där. Därför tar väggänden mindre moment än en fast inspänning, och fältmomentet blir större. Vid vindlyft är balken förankrad i väggen, se avsnitt 6.

*Tvärsnitt längs balken.* Modellen har olika tvärsnitt där plåt finns och där den saknas. Med plåt är balken sammansatt av två plåtar och #r.geo.b×#r.hw limträ. Utan plåt är den limträ #r.geo.b×#r.hw med $E I$ = #r.EI_tra190 × 10#super[12] Nmm² (med $E_"0,mean"$). Plåtens ände är fri: plåtkraften är noll där och byggs upp av skruvarna (och limmet) inåt längs plåten. Varje plåt går över stöden intill, så att stödmomenten tas av plåtarna och plåtänden hamnar en bit in i nästa fält. Med nästan stel fog ger modellen samma stödreaktioner som en vanlig balk med stegvis varierande $E I$, vilket är kontrollerat.

#for b in r.balkar.filter(b => b.stolpe != none) [*Stolpe med dubbeltriangel i #lower(b.namn).* Stolpen D (#b.stolpe.text, #b.stolpe.L mm från triangelns underkant till golvet, ledad i golvet) bär balken direkt och via två strävor som når balken #b.stolpe.e mm från stolpen åt båda hållen. Triangeln är styv och kan bara vrida sig kring stolpens topp, och det hindras av stolpens böjstyvhet, $k_theta = 3 E I slash L dot (1 + d slash L)$ = #b.stolpe.kth kNm/mrad ($d$ = triangelns höjd). Strävorna arbetar därför som en gungbräda: den ena kan bara trycka upp balken om den andra gör det lika mycket på andra sidan om stolpen. Strävornas vertikala kraft på balken är högst #b.stolpe.FE kN (axialkraft #b.stolpe.Fax kN i strävan), och strävornas toppar behöver minst #b.stolpe.l_strava mm upplag. Stolpen får högst $N_d$ = #b.stolpe.Nd kN och momentet $M_d$ = #b.stolpe.Md kNm. Vid vindlyft drar balken upp stolpen med #b.stolpe.Nmin kN.]

*Samverkan.* Balken analyseras med finita element som en mekaniskt sammanfogad balk med linjärt samband mellan kraft och glidning (9.1.3), med verkliga stöd, laster, plåtbitar och skruvdelning. Fogens styvhet per längdenhet påverkar kraftfördelningen, så tre fall räknas:

#pad(left: 10pt)[
  (1) enbart skruv, övre värde $K_u = 2/3 dot #"2,0" dot K_"ser"$ = #r.K_up kN/mm (2.2.2(2) och 7.1(3), stål–trä), för skruvkrafter, \
  (2) enbart skruv, undre värde $K_"u,fin" = 2/3 dot K_"ser" slash (1 + psi_2 k_"def")$ = #r.K_low kN/mm (2.3.2.2(2), utan faktorn 2,0), för spänningar, \
  (3) limfog, $k$ = #r.k_lim N/mm per mm balk (avsnitt 5), i praktiken full samverkan, för spänningar och stödreaktioner,
]

med $K_"ser" = rho_m^#"1,5" d slash 23$ = #r.Kser kN/mm (tabell 7.1). Limträets elasticitetsmodul $E_"0,mean" slash (1 + psi_2 k_"def")$ = #r.E2fin MPa. Krafterna i varje modell och lastfall ger skruvkraft $F = K delta$ ($delta$ = glidningen i fogen), normalkraft och krökning i plåtarna samt böj- och skjuvspänning i limträet. I brottgränstillståndet tillgodoräknas bara skruvarna: skruvarna dimensioneras med fall (1) och (2), där limmet inte finns. Med fungerande lim (fall 3) avlastas skruvarna, men balken blir styvare och får större stödmoment. Plåt och limträ kontrolleras för alla tre fallen. Stödreaktioner och omhyllande snittkrafter i avsnitt 6 omfattar alla tre fallen.

#grid(
  columns: (1fr, 1fr),
  column-gutter: 10pt,
  table(
    columns: (1fr, auto),
    align: (left, right),
    [Skruv Ø#r.skruv.d, tjock plåt (8.2.3)], [Värde],
    [$d_"ef" = #"1,1" d_1$ (8.7.1(3)); $d_"ef" > 6$ mm ger bultregler], [#r.d_ef mm],
    [$f_"h,0,k" = #"0,082" (1 - #"0,01" d_"ef") rho_k$ (8.32)], [#r.f_h MPa],
    [$f_"ax,k"$ = #r.skruv.fax_k MPa vid $rho_a$ = #r.skruv.rho_a enligt ETA, $times (rho_k slash rho_a)^#"0,8"$], [#r.f_axk MPa],
    [$F_"ax,Rk" = f_"ax,k" d l_"ef"$, gängan i limträet $l_"ef"$ = #r.l_ef mm, $alpha$ = 90°], [#r.F_ax kN],
    [Brottmod (c), (d), (e) enligt (8.10), $t_1$ = #r.t_ef mm, lindragseffekt $F_"ax,Rk" slash 4$], [#r.jc / #r.jd / #r.je kN],
    [$F_"v,Rk"$ (mod #r.mod)], [#r.FvRk kN],
    [$F_"v,Rd" = k_"mod" F_"v,Rk" slash gamma_M$, $gamma_M$ = #r.skruv.gamma_M], [*#r.FRd kN*],
    [Jämförelse: tillverkarens $F_"v,k"$, tjock plåt, utan förborrning, $rho_k$ = 385], [#r.skruv.R_tjock_k kN],
  ),
  table(
    columns: (1fr, auto),
    align: (left, right),
    [Kontroll i varje snitt], [Bärförmåga],
    [Skruv, $F = K delta$, inklusive temperatur (avsnitt 4)], [$F_"v,Rd"$ = #r.FRd kN],
    [Plåt, $N slash A + E kappa t slash 2$ (EC3 6.2.1)], [$f_"yd"$ = #r.fyd MPa],
    [Tryckt plåt, knäckning mellan skruvar i samma rad, $l_"cr"$ = c/c i raden enligt verkliga skruvlägen, kurva c (EC3 6.3.1)], [#r.Nb_400 kN vid c/c #r.cc_max],
    [Dragen plåt, $#"0,9" A_"net" f_u slash gamma_"M2"$, två respektive tre hål i snittet (EC3 6.2.3)], [#r.NuRd / #r.NuRd3 kN],
    [Limträ, böjspänning, $k_h$ = 1 (EC5 6.1.6)], [$f_"m,d"$ = #r.fmd MPa],
    [Limträ, skjuvspänning i tvärsnittets mitt (EC5 6.1.7)], [$k_"cr" f_"v,d"$ = #r.tauRd MPa],
  ),
)

*Tjock plåt.* Plåten är lika tjock som skruvens diameter ($t >= d$). Hålet Ø#r.skruv.hal är tillverkarens mått för skruven. Ansatsen under huvudet, Ø#r.skruv.ansats, fyller hålet med #r.glapp mm spel, och huvudet dras fast mot plåten. Skruven blir då inspänd i plåten. Tillverkaren och #r.skruv.eta räknar plåt med $t >= d$ som tjock plåt, och bärförmågan räknas så (8.2.3). Förborrningen ger högre hålkanthållfasthet i limträet än tillverkarens tabellvärde, som gäller utan förborrning.

*Skruvdelning.* Delningen _s_ längs plåten varierar. Med två rader är c/c i varje rad $2 s$, med tre rader $3 s$. Den glesaste delningen begränsas till c/c #r.cc_max för att plåten ska hållas mot limträet när limmet härdar. Avstånden uppfyller både 8.5.1.1 (bultregler, förborrat: $a_1 >= 5d$, $a_2 >= 4d$, $a_3 >=$ #r.a3_min mm, $a_4 >= 3d$) och tabell 8.6 för axiellt belastad skruv, som krävs för lindragseffekten: $a_1 >= 7d$ = #r.a1ax_min mm i raden, $a_2 >= 5d$ = #r.a2ax_min mm mellan raderna, $a_"1,CG" >= 10d$ = #r.a1cg_min mm från balkände och $a_"2,CG" >= 4d$ = #r.a2cg_min mm från kant. Minsta c/c i en rad i schemana är #r.cc_rad_min mm. Vid en plåtände inne på balken sitter första skruven #r.skruv.ande_plat mm från plåtens ände (kantavstånd i stål, $>= #"1,2" d_0$ = #r.e1_min mm). I stålet är c/c i en rad minst $#"2,2" d_0$ = #r.p1_min mm och mellan raderna minst $#"2,4" d_0$ = #r.p2_min mm (EC3 tabell 3.3). Skruvar från över- och underplåten står förskjutna i ytterraderna. I mittraden är det #r.gap_spets mm mellan spetsarna. Skruvschemat är kontrollerat med de verkliga skruvlägena och knäcklängderna.

Tvärsnittet är lika brett som högt, så vippning är inte aktuell.

*Bruksgränstillstånd.* Fält med plåt räknas som fritt upplagda, vilket ger en övre gräns för nedböjningen. Med plåt räknas limfogen med styvheten i avsnitt 5 och skruvarna med $2 K_"ser"$. Krypning räknas endast i trädelen, och skjuvdeformationen i limträet ingår:

$ w_"fin" = w(G_k; E_0 slash (1 + k_"def")) + w(S_k; E_0 slash (1 + psi_2 k_"def")) + psi_(0,T) w_T <= L slash #r.laster.nedbojning_krav $

där $w_T$ är nedböjningen från temperaturskillnaden mellan plåtarna (avsnitt 4). Fält utan plåt räknas i stället som del av den kontinuerliga balken, med fältvis snö och stöd som både förankrade och bara tar tryck. Hela lasten räknas där med $E_0 slash (1 + k_"def")$. Fritt upplagt klarar enbart limträ #r.geo.b×#r.hw kravet upp till cirka #r.lmax_nock m för nockbalkarna och #r.lmax_dal m för dalbalkarna. Med kontinuiteten klarar även nockbalk 3:s fält B–C, 3,8 m, kravet utan plåt.

= Temperaturpåverkan

Stål utvidgas mer än trä: $alpha_s$ = #r.alfa_s × 10#super[−6] /K och längs fibrerna $alpha_t$ = #r.alfa_t × 10#super[−6] /K (SS-EN 1991-1-5 tabell C.1). Plåtarna limmas och skruvas vid cirka +20 °C. När temperaturen sedan ändras vill plåten ändra längd mer än limträet, och limmet och skruvarna hindrar det. Balken ligger i takets isolering med överplåten mot den kalla sidan, så över- och underplåt får dessutom olika temperatur. Vinterfallet med uppvärmt hus kommer från K-02, som räknar temperaturfältet kring nocken. Vid −20 °C ute och +25 °C inne blir plåtarna där −16,5 °C och +14,8 °C, och skillnaden mellan dem är 24–33 K med rimliga variationer av ytövergångarna. Följande fall räknas, med linjär temperaturfördelning över höjden:

#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  [Fall], [Överplåt], [Underplåt],
  ..r.temperatur.map(T => ([#T.namn], [#T.To °C], [#T.Tu °C])).flatten(),
)

Påverkan delas upp i två delar som räknas var för sig och adderas för varje fall:

*Lika temperaturändring i plåtarna* (medelvärdet av över- och underplåt). När det blir kallt vill stålet krympa mer än limträet. Mitt på plåten hindrar fogen det helt: plåten blir sträckt med en jämn kraft $N_oo$, #r.Ninf kN per grad, och limträet lika mycket tryckt. Kraften är lika stor längs hela mittpartiet, så där går ingen kraft genom fogen. Vid plåtänden måste plåtkraften vara noll. Hela $N_oo$ förs därför över till limträet på en kort sträcka vid varje ände, och där får fogen en spets (figuren). Ju styvare fog, desto kortare sträcka och högre spets: med lim är sträckan några decimeter, med enbart skruv en till två meter. Samma sak gäller lasten vid en plåtände där momentet inte är noll.

#figure(image("fig_temp.svg", width: 82%), caption: [Plåtkraft och skjuvkraft per längdenhet i fogen längs en 4 m lång plåt när plåtarna kyls lika mycket.])

*Olika temperatur i över- och underplåt.* Balken vill kröka sig. Ett fritt upplagt fält får böja ut fritt, medan en kontinuerlig balk hålls kvar av stöden och får tvångsmoment. Detta räknas med finita element som i avsnitt 3, med en initialtöjning $plus.minus alpha_s (Delta T_ö - Delta T_u) slash 2$ i plåtarna och motsvarande fri krökning i limträet, både med förankrade stöd och med varje fält fritt upplagt.

Temperatur i byggnader har kombinationsfaktorn $psi_0$ = #r.laster.psi0_T (SS-EN 1990 tabell A1.1, samma i EKS). $psi_0$ är ingen materialfaktor. Den tar hänsyn till att full temperaturskillnad och full snölast sällan inträffar samtidigt: i varje kombination räknas en av dem fullt, som huvudlast, och den andra med $psi_0$. Båda kombinationerna prövas. I brottgränstillstånd prövas både snö som huvudlast med temperatur som följdlast och tvärtom: $F_d = max(F_S + #r.cT1 F_T; thick F_(S,psi_0) + #r.cT2 F_T)$, där $F_S$ är kraften från 6.10a/b och $F_(S,psi_0)$ samma med snön som följdlast. Skruvkraften från temperaturen räknas med skruvarnas styvhet $K_u$, utan lim, som lasten i övrigt.

#table(
  columns: (1fr, auto, auto, auto, auto),
  align: (left, right, right, right, right),
  [Karakteristiska värden], [Skruvkraft (kN)], [Skjuvspänning i limfog (MPa)], [Spänning i plåt (MPa)], [Nedböjning $w_T$ (mm)],
  ..r.temp.map(t => ([#t.namn], [#t.F], [#t.q], [#t.sig], [#t.w])).flatten(),
)
#liten[Största värde längs balken och över fallen. Skruvkraften gäller enbart skruv, skjuvspänningen i limfogen fungerande lim. Nedböjningen är den största i något fritt upplagt fält med plåt (kall överplåt ger nedböjning).]

Spänningen i plåten är liten. Skruvkraften från temperaturen uppträder nära plåtänderna och är där en betydande del av skruvens bärförmåga, #r.FRd kN per skruv. Nedböjningen från temperaturen ingår i bruksgränskontrollen med $psi_0 w_T$.

= Limfogen

Limmet behövs för styvheten. I brottgränstillståndet räknas inte limmet, och skruvarna är dimensionerade för hela skjuvkraften i fogen inklusive temperaturen.

Limfogen räknas som en fog med skjuvstyvheten $k$ = #r.k_lim N/mm per mm balk. Det motsvarar limträets skjuvdeformation inom cirka 30 mm från fogen ($G b slash 30$). Limskiktet självt är mycket styvare. Sikadur-30 har deklarerad E-modul minst 2 000 MPa (SS-EN 1504-4), alltså $G$ ≈ 0,8 GPa. Med 3 mm fog ger det 51 000 N/mm per mm, tolv gånger mer. Fogens styvhet bestäms alltså av träet närmast fogen och beror i praktiken inte på limtypen. Spänningen i fogen är störst vid plåtänderna, där plåtkraften förs in. Tabellen visar de största karakteristiska värdena, för snö som huvudlast med $psi_0$ för temperaturen eller tvärtom.

#table(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Balk], [Last $tau_S$ (MPa)], [Temperatur $tau_T$ (MPa)], [Kombinerat $tau$ (MPa)], [_x_ (mm)], [$tau slash k_"cr" f_"v,k"$],
  ..r.lim_tab.map(l => ([#l.namn], [#l.tauL], [#l.tauT], [#l.tau], [#l.x], [#l.u %])).flatten(),
)
#liten[Skjuvspänning i fogen, karakteristiska värden, $k_"cr" f_"v,k"$ = #r.fvk_cr MPa. _x_: läge längs balken. Värdena är lokala toppar i en linjär modell och gäller limträet närmast fogen.]

Lasten ensam ger måttliga värden. Temperaturen, främst vinterfallet med uppvärmt hus, ger toppar i samma storlek som limträets skjuvhållfasthet. Nedböjningen är kontrollerad även med limmet släppt de första #r.L_slapp mm från varje plåtände, med enbart skruv där (kolumnen _släppt_ i bruksgränstabellerna). Nedböjningskravet $L$/300 uppfylls då med högst #r.us_max_all % utnyttjande.

= Resultat per balk

Stöden betecknas A, B, … från vänster och _x_ räknas från vänster balkände, med samma orientering som i balkskisserna.

#for b in r.balkar [
  #pagebreak(weak: true)
  == #b.namn

  Längd #b.total mm, spann #b.spann mm#if b.utstick != "0" [ med #b.utstick mm utstick i båda ändar]. #if b.vagg [Balken vilar på innervägg över #b.vagg_txt mm; väggens ände är stöd A.] #if b.stolpe != none [Stöd D är en stolpe med dubbeltriangel, se avsnitt 3; reaktionen avser stolpens hela kraft.] Last: $G_k$ = #b.G kN/m, $S_k$ = #b.S kN/m, $q_d$ = #b.qd kN/m (6.10b). Största dimensionerande moment #b.Mmax kNm i fält och #b.Mmin kNm över stöd, största tvärkraft #b.V kN. Plåt: #b.bitar.len() #if b.bitar.len() == 1 [bit] else [bitar] i över- och underkant, sammanlagt #b.stal_txt m (#b.stal_kg kg).#if b.over_stod.len() > 0 [ Plåten går över stöd #b.over_stod.join(", ", last: " och ").]

  #figure(image(b.fig, width: 90%), caption: [#b.namn. Stöd, plåtbitar, omhyllande moment (ritat på dragen sida) och tvärkraft i brottgränstillstånd för samtliga modeller och lastfall, med och utan limverkan, samt skruvdelning _s_ längs plåten (mm).])

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 12pt,
    row-gutter: 8pt,
    [
      *Brottgränstillstånd*
      #table(
        columns: (1fr, auto, auto, auto),
        align: (left, right, right, center),
        [Kontroll], [Utn.], [_x_ (mm)], [],
        ..b.kontroller.map(k => ([#k.namn], [#k.u %], [#k.x], ok(k.ok))).flatten(),
        [Med lim: plåt, limträ], [#b.u_full %], [], ok(b.u_full_ok),
      )
      #liten[Enbart skruv (limmet oräknat), största värde ur modell (a)–(c) med båda förbindningsstyvheterna och de verkliga skruvlägena. Skruvraden inkluderar temperatur. Sista raden: samma kontroller med fungerande limfog. _x_ anger snittet med störst utnyttjande.]
    ],
    [
      *Stödreaktioner, dimensionerande*
      #table(
        columns: (auto, 1fr, auto, auto, auto),
        align: (center, left, right, right, right),
        [Stöd], [_x_ (mm)], [$R_"max"$ (kN)], [$R_"min"$ (kN)], [$l_"min"$ (mm)],
        ..b.stod.map(s => ([#s.bok], [#s.x#if s.vagg [ (vägg)]#if s.plat [ (plåt)]], [#s.Rmax], if s.lyft [*#s.Rmin*] else [#s.Rmin], [#s.l])).flatten(),
      )
      #liten[
        $R_"min"$ gäller förankrat stöd med 1,0 $G_k$ och fältvis snö eller vindlyft. #if b.ankare.len() > 0 [Negativt värde är dragkraft.] $l_"min"$ är minsta upplagslängd för tryck vinkelrätt fibrerna, $k_"c,90" f_"c,90,d"$ = #r.kfc90d MPa, där upplagslängden på varje sida ökas med högst 30 mm, högst $l$ och högst avståndet till balkänden (6.1.5(1)). Lastspridning genom plåten är inte medräknad.
        #if b.vagg [För väggen avser $R_"max"$ reaktionen inom 0,5 m från väggens ände; väggens hela last är högst #b.stod.first().Rvagg kN. Vid vindlyft drar balken upp väggen med sammanlagt #b.stod.first().Rvagg_lyft kN. Balken lyfter högst #b.lyft_vagg mm från väggen i brottgränstillstånd.]
      ]
    ],
    [
      *Plåtbitar och skruv* (lika i över- och underplåt)
      #table(
        columns: (auto, 1fr, auto, auto, auto),
        align: (center, left, right, right, right),
        [Bit], [_x_ (mm)], [Längd], [kg/st], [Skruv/st],
        ..b.bitar.map(t => ([#t.nr], [#t.fran–#t.till], [#t.L], [#t.massa], [#t.n])).flatten(),
      )
      #v(2pt)
      #table(
        columns: (auto, 1fr, auto, auto, auto),
        align: (center, left, center, right, right),
        [Bit], [Zon, _x_ (mm)], [Rader], [c/c i rad], [Antal],
        ..b.zoner.map(z => ([#z.bit], [#z.x], [#z.rader], [#z.cc], [#z.n])).flatten(),
        [], [*Summa plåt / balk*], [], [], [*#b.n_plat / #b.n_balk*],
      )
    ],
    [
      *Bruksgränstillstånd*
      #table(
        columns: (auto, auto, auto, auto, auto, auto, auto),
        align: (center, right, right, right, right, right, right),
        [Fält], [_L_], [$w_"fin"$], [_L_/#r.laster.nedbojning_krav], [Utn.], [Släppt], [Utan lim],
        ..b.brg.map(f => ([#f.fran–#f.till], [#f.L], [#f.wtot], [#f.wgr], [#f.u %], [#f.ws], [#f.wsk])).flatten(),
      )
      #liten[mm, fält med plåt fritt upplagda, $w_"fin"$ inklusive $psi_0 w_T$. _Släppt_: limmet släppt de första #r.L_slapp mm från varje plåtände. _Utan lim_: enbart skruv. Fält utan plåt är limträ #r.geo.b×#r.hw och räknas som del av den kontinuerliga balken. c/c i rad i skruvtabellen = antal rader × _s_; exakta hållägen i balkens hålbildsfil.]
    ],
  )
]

#pagebreak()
= Sammanfattning

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto),
  align: (left, right, left, right, right, right, right),
  [Balk], [Längd (mm)], [Plåtbitar (mm)], [Stål (kg)], [Max utn. brottgräns], [Max utn. bruksgräns], [Skruv],
  ..r.balkar.map(b => ([#b.namn], [#b.total], [#b.bitar.map(t => t.L).join(", ")], [#b.stal_kg], [#b.umax %], [#b.wmax_u %], [#b.n_balk])).flatten(),
  [*Summa*], [], [#r.n_bitar plåtar], [*#r.stal_kg*], [], [], [*#r.n_tot*],
)
#liten[Plåtbitarna finns i över- och underkant, dvs. två av varje längd. Stålvikten avser båda plåtarna.]

#if r.ok [Samtliga balkar uppfyller kraven i brottgränstillstånd (endast skruv, med temperatur) och bruksgränstillstånd (lim och skruv).] else [*Alla krav är inte uppfyllda, se tabellerna i avsnitt 6.*] Förutsättningar:

+ Skruv #r.skruv.produkt (#r.skruv.kod, #r.skruv.eta), #r.skruv.korrosion. Hål i plåten Ø#r.skruv.hal, cylindriska, utan försänkning. Förborrning Ø#r.skruv.forborr i limträet. Antal och lägen enligt hålbilden för respektive balk. En annan skruv kräver ny kontroll av bärförmågan och av hålens diameter.
+ Plåtbitarna tillverkas i hela längder utan skarv.
+ Limträet levereras #r.geo.b×#r.hw, #r.tra.kvalitet, i hel längd. Där plåt saknas sätts distansreglar #r.distans.tjocklek mm i över- och underkant, så att balken är #r.geo.h_tot mm hög i hela längden. Reglarna är inte bärande och kräver ingen särskild limning. De kan spricka eller släppa utan att det påverkar balken.
+ Stöd med negativ $R_"min"$ förankras för angiven dragkraft (dimensionerande värde). Vindlyft ger dragkraft vid samtliga stöd.

